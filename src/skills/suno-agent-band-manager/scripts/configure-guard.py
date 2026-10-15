#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Configure Mac's guards: the Claude Code hooks and the cross-platform standing order.

Merges into .claude/settings.local.json the pipeline guard Stop hook and, with
--dominion-hook, a PreToolUse hook on Write/Edit that checks writes outside the
sanctum against the CREED.md Dominion (it asks the owner about a write the
Dominion doesn't allow, while Mac is awake). Appends the standing order to
AGENTS.md. Idempotent: anything already configured is left as it is.

Both hooks run pipeline-guard.py on bare `python3` (stdlib-only) so a hook that
fires on every turn or write stays fast; they fail open when the sanctum,
validate-path.py or the transcript is missing.

Usage:
    uv run scripts/configure-guard.py --settings-path PATH --guard-script-path PATH [--dominion-hook]
    uv run scripts/configure-guard.py --agents-md-path PATH
    uv run scripts/configure-guard.py --settings-path PATH --guard-script-path PATH --agents-md-path PATH

Options:
    --settings-path     Path to .claude/settings.local.json
    --guard-script-path Relative path from project root to pipeline-guard.py
    --dominion-hook     Also install the PreToolUse Dominion hook (needs the two above)
    --agents-md-path    Path to AGENTS.md (or CLAUDE.md / GEMINI.md)
    -o, --output        Write JSON output to file instead of stdout

Path arguments must be real paths: a literal {project-root} token is rejected.

Exit codes: 0=success, 1=validation error (no targets, unresolved path token,
    --dominion-hook without the settings and guard paths),
    2=runtime error (e.g. malformed settings JSON)
"""

import argparse
import json
import sys
from pathlib import Path

STANDING_ORDER = """
## Suno Pipeline Rule (MANDATORY)

When the suno-agent-band-manager skill is active, NEVER hand-build a Suno package from conversation memory. ALWAYS invoke suno-style-prompt-builder and suno-lyric-transformer before presenting any style prompt + lyrics + settings package. This rule exists because those skills carry critical guardrails (artist name detection, production descriptor checks, character budget validation, section tag validation) that cannot be replicated from conversation memory.

The Package Assembly Rule core (marked INVARIANT, with its pre-output self-check) lives in the agent's sanctum creed (_bmad/memory/suno-agent-band-manager/CREED.md), which the wake prints on every activation — so whenever a package is assembled, the rule is loaded. The rest (running the pipeline through Agent, signs it was skipped, presenting a refinement) lives in the sanctum's on-demand memory/disciplines/package-assembly.md. The skill's references/creed.md is authored source that seeds the sanctum at install — it is NOT loaded on every activation.
""".strip()

STANDING_ORDER_MARKER = "## Suno Pipeline Rule"


def reject_unresolved_paths(named_paths: list[tuple[str, str | None]]) -> None:
    """Exit with a clear error if any path argument still contains the literal
    ``{project-root}`` token. That token is meaningful only inside config
    values; filesystem path arguments must be resolved by the caller. Failing
    loudly here prevents silently creating a junk ``{project-root}/`` directory.
    """
    for name, value in named_paths:
        if value and "{project-root}" in value:
            message = (
                f"Unresolved '{{project-root}}' token in {name} path: {value!r}. "
                "Resolve '{project-root}' to the actual project root before running "
                "this script — it is a filesystem path, not a config value."
            )
            print(json.dumps({"results": [{"status": "error", "message": message}]}, indent=2))
            sys.exit(1)


DOMINION_MATCHER = "Write|Edit|MultiEdit|NotebookEdit"


def _load_settings(settings_path: Path) -> dict | None:
    """The settings dict; {} when the file is absent; None when it is malformed."""
    if not settings_path.is_file():
        return {}
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _has_hook(entries: list, *needles: str) -> bool:
    return any(
        all(n in hook.get("command", "") for n in needles)
        for entry in entries if isinstance(entry, dict)
        for hook in entry.get("hooks", []) if isinstance(hook, dict)
    )


def configure_hooks(settings_path: Path, guard_script_path: str, dominion: bool) -> list[dict]:
    """Merge the Stop hook (and, with ``dominion``, the PreToolUse hook) into the settings."""
    targets = ["claude_hook"] + (["dominion_hook"] if dominion else [])
    existing = _load_settings(settings_path)
    if existing is None:
        message = "Malformed JSON in settings file. Fix manually or delete to recreate."
        return [{"target": t, "path": str(settings_path), "status": "error", "message": message} for t in targets]

    hooks = existing.setdefault("hooks", {})
    command = f'python3 "$CLAUDE_PROJECT_DIR"/{guard_script_path}'
    results, changed = [], False

    stop_hooks = hooks.setdefault("Stop", [])
    # The Stop guard is the pipeline-guard command without --dominion.
    if any(
        "pipeline-guard" in hook.get("command", "") and "--dominion" not in hook.get("command", "")
        for entry in stop_hooks if isinstance(entry, dict)
        for hook in entry.get("hooks", []) if isinstance(hook, dict)
    ):
        results.append({"target": "claude_hook", "path": str(settings_path), "status": "already_configured"})
    else:
        stop_hooks.append({"hooks": [{"type": "command", "command": command, "timeout": 10}]})
        results.append({"target": "claude_hook", "path": str(settings_path), "status": "configured"})
        changed = True

    if dominion:
        pre_hooks = hooks.setdefault("PreToolUse", [])
        if _has_hook(pre_hooks, "pipeline-guard", "--dominion"):
            results.append({"target": "dominion_hook", "path": str(settings_path), "status": "already_configured"})
        else:
            pre_hooks.append({
                "matcher": DOMINION_MATCHER,
                "hooks": [{"type": "command", "command": f"{command} --dominion", "timeout": 10}],
            })
            results.append({"target": "dominion_hook", "path": str(settings_path), "status": "configured"})
            changed = True

    if changed:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return results


def configure_standing_order(md_path: Path) -> dict:
    """Append standing order to a markdown instruction file."""
    result = {"target": "standing_order", "path": str(md_path)}

    # Check if already present
    if md_path.is_file():
        content = md_path.read_text(encoding="utf-8")
        if STANDING_ORDER_MARKER in content:
            return {**result, "status": "already_configured"}
        # Append with separator
        if content and not content.endswith("\n\n"):
            content = content.rstrip("\n") + "\n\n"
        content += STANDING_ORDER + "\n"
    else:
        content = STANDING_ORDER + "\n"

    md_path.write_text(content, encoding="utf-8")
    return {**result, "status": "configured"}


def main():
    parser = argparse.ArgumentParser(
        description="Configure Mac's guards: the pipeline Stop hook, the optional Dominion PreToolUse hook, and the AGENTS.md standing order"
    )
    parser.add_argument("--settings-path", help="Path to .claude/settings.local.json")
    parser.add_argument("--guard-script-path", help="Relative path to pipeline-guard.py from project root")
    parser.add_argument(
        "--dominion-hook",
        action="store_true",
        help="Also install the PreToolUse hook that checks Write/Edit outside the sanctum against the CREED.md Dominion",
    )
    parser.add_argument("--agents-md-path", help="Path to AGENTS.md (or CLAUDE.md / GEMINI.md)")
    parser.add_argument("-o", "--output", help="Output file path")
    args = parser.parse_args()
    reject_unresolved_paths([
        ("--settings-path", args.settings_path),
        ("--guard-script-path", args.guard_script_path),
        ("--agents-md-path", args.agents_md_path),
        ("--output", args.output),
    ])

    if args.dominion_hook and not (args.settings_path and args.guard_script_path):
        message = "--dominion-hook needs --settings-path and --guard-script-path."
        print(json.dumps({"results": [{"status": "error", "message": message}]}, indent=2))
        sys.exit(1)

    results = []

    if args.settings_path and args.guard_script_path:
        results.extend(configure_hooks(Path(args.settings_path), args.guard_script_path, args.dominion_hook))

    if args.agents_md_path:
        results.append(configure_standing_order(Path(args.agents_md_path)))

    no_targets = not results
    if no_targets:
        results.append({"status": "error", "message": "No configuration targets specified. Use --settings-path and/or --agents-md-path."})

    output = json.dumps({"results": results}, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)

    # Exit codes: 0=success, 1=validation error (no targets), 2=runtime error
    if no_targets:
        sys.exit(1)
    if any(r.get("status") == "error" for r in results):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
