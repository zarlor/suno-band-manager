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
AGENTS.md. Idempotent: anything already configured is left as it is. A guard
hook left from an older location (its command differs) is pointed at the
current one, and the result names the command it replaced (`replaced_command`).

Both hooks run pipeline_guard.py on bare `python3` (stdlib-only) so a hook that
fires on every turn or write stays fast; they fail open when the sanctum,
validate_path.py or the transcript is missing.

Usage:
    uv run {skill-root}/scripts/configure_guard.py --settings-path PATH --guard-script-path PATH [--dominion-hook]
    uv run {skill-root}/scripts/configure_guard.py --agents-md-path PATH
    uv run {skill-root}/scripts/configure_guard.py --settings-path PATH --guard-script-path PATH --agents-md-path PATH

Options:
    --settings-path     Path to .claude/settings.local.json
    --guard-script-path Path to pipeline_guard.py: relative to the project root (the
                        folder holding the settings file's .claude/), or absolute.
                        The file must exist; a guard outside the project is run
                        by its absolute path.
    --dominion-hook     Also install the PreToolUse Dominion hook (needs the two above)
    --agents-md-path    Path to AGENTS.md (or CLAUDE.md / GEMINI.md)
    -o, --output        Write JSON output to file instead of stdout

Path arguments must be real paths: a literal {project-root} token is rejected.

Exit codes: 0=success, 1=validation error (no targets, unresolved path token,
    only one of --settings-path / --guard-script-path, --dominion-hook without
    both),
    2=runtime error (malformed settings JSON, a `hooks` value of the wrong
    shape, guard script not found); the settings file is left untouched
"""

import argparse
import json
import re
import os
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


def guard_command(settings_path: Path, guard_script_path: str) -> tuple[str | None, str | None]:
    """(hook command, None), or (None, reason) when the guard script is not there.

    The project is the folder holding the settings file's `.claude/`. A path
    inside it becomes `"$CLAUDE_PROJECT_DIR"/<relative>`, which survives a moved
    project; a guard outside it (a plugin or global install) is run by its
    absolute path. Symlinks are kept as given.
    """
    project_dir = Path(os.path.abspath(settings_path)).parent.parent
    given = Path(guard_script_path)
    script = given if given.is_absolute() else project_dir / given
    if not script.is_file():
        return None, (
            f"Guard script not found: {script}. Give --guard-script-path the real location of "
            "pipeline_guard.py (relative to the project root, or absolute). No hook was installed: "
            "a hook pointing at a missing script blocks every turn."
        )
    if not given.is_absolute():
        return f'python3 "$CLAUDE_PROJECT_DIR"/{guard_script_path}', None
    try:
        relative = Path(os.path.normpath(given)).relative_to(project_dir)
    except ValueError:
        return f'python3 "{given}"', None
    return f'python3 "$CLAUDE_PROJECT_DIR"/{relative.as_posix()}', None


def _guard_hooks(entries: list, dominion: bool) -> list[dict]:
    """The pipeline-guard hooks among a hook event's entries: the ones run with
    --dominion, or the ones run without it."""
    found = []
    for entry in entries:
        hooks = entry.get("hooks") if isinstance(entry, dict) else None
        for hook in hooks if isinstance(hooks, list) else []:
            command = str(hook.get("command") or "") if isinstance(hook, dict) else ""
            # Either spelling: installs before the script was renamed wrote pipeline-guard.py,
            # and such a hook must be found so it is repointed, not doubled.
            if re.search(r"pipeline[-_]guard", command) and ("--dominion" in command) == dominion:
                found.append(hook)
    return found


def _install(entries: list, command: str, dominion: bool, new_entry: dict) -> dict:
    """Install one guard hook. A hook already there counts only when it runs this
    exact command; one left from an older location is pointed at the new one."""
    present = _guard_hooks(entries, dominion)
    if not present:
        entries.append(new_entry)
        return {"status": "configured"}
    stale = [hook for hook in present if hook.get("command") != command]
    if not stale:
        return {"status": "already_configured"}
    replaced = [hook["command"] for hook in stale]
    for hook in stale:
        hook["command"] = command
    return {"status": "configured", "replaced_command": replaced[0] if len(replaced) == 1 else replaced}


def configure_hooks(settings_path: Path, guard_script_path: str, dominion: bool) -> list[dict]:
    """Merge the Stop hook (and, with ``dominion``, the PreToolUse hook) into the settings."""
    targets = ["claude_hook"] + (["dominion_hook"] if dominion else [])

    def refuse(message: str) -> list[dict]:
        return [{"target": t, "path": str(settings_path), "status": "error", "message": message} for t in targets]

    existing = _load_settings(settings_path)
    if existing is None:
        return refuse("Malformed JSON in settings file. Fix manually or delete to recreate.")
    hooks = existing.get("hooks", {})
    if not isinstance(hooks, dict):
        return refuse('"hooks" in the settings file is not an object. Fix it by hand; nothing was changed.')
    for event in ("Stop", "PreToolUse"):
        if not isinstance(hooks.get(event, []), list):
            return refuse(f'"hooks.{event}" in the settings file is not a list. Fix it by hand; nothing was changed.')
    command, problem = guard_command(settings_path, guard_script_path)
    if command is None:
        return refuse(problem)

    existing["hooks"] = hooks
    results = []
    # The Stop guard is the pipeline-guard command without --dominion.
    outcome = _install(
        hooks.setdefault("Stop", []), command, False,
        {"hooks": [{"type": "command", "command": command, "timeout": 10}]},
    )
    results.append({"target": "claude_hook", "path": str(settings_path), **outcome})
    if dominion:
        outcome = _install(
            hooks.setdefault("PreToolUse", []), f"{command} --dominion", True,
            {"matcher": DOMINION_MATCHER, "hooks": [{"type": "command", "command": f"{command} --dominion", "timeout": 10}]},
        )
        results.append({"target": "dominion_hook", "path": str(settings_path), **outcome})

    if any(r["status"] == "configured" for r in results):
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
    parser.add_argument(
        "--guard-script-path",
        help="Path to pipeline_guard.py, relative to the project root or absolute; the file must exist",
    )
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
    if bool(args.settings_path) != bool(args.guard_script_path):
        # Half a hook request would install nothing and still report success for the rest.
        message = "Give both --settings-path and --guard-script-path to install the Claude Code hook; nothing was changed."
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
