#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Measures what Mac loads and how well his memory is tended (BMad v7 sanctum).

The sanctum is `{project-root}/_bmad/memory/suno-agent-band-manager/`. There is
no token budget on memory itself: v7 memory is many small files found with ls
and grep, and it stays good by being tended, not by being trimmed. What this
script measures instead:

  - The identity set: the files loaded whole at every waking (PERSONA, CREED,
    BOND, HOW-I-REMEMBER, CAPABILITIES), together. Flagged past ~12,000 tokens.
  - The two companion files that also load every waking: the owner's voice
    file `docs/voice-context-<owner>.md` and `docs/mac-preferences.md`. Each is
    flagged past ~20,000 tokens: offer the owner a compaction pass; a script
    never digests or splits them.
  - Standing files under `memory/` longer than a screen (~60 lines or ~4,000
    characters): a section is being appended to instead of replaced. Not
    standing, so never measured: the dated `chronology/` and `sessions/`, the
    `incidents/` stories, the generated `catalog/`, and `disciplines/` (rule
    text sliced from the skill creed, long by design; HOW-I-REMEMBER.md does
    not count it among the standing kinds).
  - Undistilled raw files: `raw/` files whose frontmatter still says
    `status: raw`.
  - Tending staleness: session notes in `memory/sessions/` written since the
    date in `memory/.tended`; flagged at 3 or more, or when memory was never
    tended.

Token figures are estimates (characters / 4), good enough to spot bloat.

Usage:
    uv run scripts/check-memory-health.py <project-root> [--sanctum-dir PATH]
                                          [--format json|text] [-o OUTPUT]

A sanctum path given in place of the project root is accepted too (the project
root is then inferred). Exit 0 with a report, 1 when there is no v7 sanctum to
measure (absent, or an old store that converts with migrate-sanctum-to-v7.py).
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_sanctum_seed():
    seed_path = Path(__file__).resolve().parent / "_sanctum_seed.py"
    spec = spec_from_file_location("_sanctum_seed", seed_path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_seed = _load_sanctum_seed()

IDENTITY_TOKEN_BUDGET = 12000    # the identity files together
COMPANION_TOKEN_BUDGET = 20000   # each companion file that loads every waking
STANDING_MAX_LINES = 60          # "longer than a screen"
STANDING_MAX_CHARS = 4000
TENDING_NOTES_THRESHOLD = 3      # session notes since the last tending
# memory/ kinds that are not standing files: dated records, stories, the generated
# catalog, and the disciplines (rule text from the skill creed, long by design).
NOT_STANDING = ("chronology", "sessions", "incidents", "catalog", "disciplines")
PREFERENCES_FILE = "docs/mac-preferences.md"


def tokens_est(text: str) -> int:
    return round(len(text) / 4)


def measure(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "size_chars": len(text),
        "size_lines": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        "tokens_est": tokens_est(text),
    }


def project_root_for(path: Path) -> Path:
    """The project root for a positional path: a sanctum path maps to its project."""
    parts = path.resolve().parts
    for rel in (_seed.SANCTUM_REL, _seed.LEGACY_SANCTUM_REL):
        if len(parts) > len(rel) and tuple(parts[-len(rel):]) == rel:
            return Path(*parts[: -len(rel)])
    return path.resolve()


def check_identity(sanctum: Path) -> dict:
    files = {n: measure(sanctum / n)["tokens_est"] for n in _seed.IDENTITY_FILES if (sanctum / n).is_file()}
    total = sum(files.values())
    return {
        "files_tokens_est": files,
        "missing": [n for n in _seed.IDENTITY_FILES if n not in files],
        "total_tokens_est": total,
        "threshold_tokens": IDENTITY_TOKEN_BUDGET,
        "over_threshold": total > IDENTITY_TOKEN_BUDGET,
    }


def companion_files(project_root: Path, sanctum: Path) -> list[Path]:
    """The owner's voice file and mac-preferences.md.

    The owner comes from BOND.md (or a lone voice file); when no file matches a
    known owner, every voice file in docs/ is measured.
    """
    docs = project_root / "docs"
    files: list[Path] = []
    owner = _seed.resolve_config(project_root, sanctum)["values"].get("user_name")
    if owner:
        voice = docs / f"voice-context-{_seed.normalize_username(owner)}.md"
        if voice.is_file():
            files.append(voice)
    if not files and docs.is_dir():
        files = sorted(docs.glob(_seed.VOICE_GLOB))
    prefs = project_root / PREFERENCES_FILE
    if prefs.is_file():
        files.append(prefs)
    return files


def check_companions(project_root: Path, sanctum: Path) -> dict:
    result = {}
    for path in companion_files(project_root, sanctum):
        facts = measure(path)
        facts["threshold_tokens"] = COMPANION_TOKEN_BUDGET
        facts["over_threshold"] = facts["tokens_est"] > COMPANION_TOKEN_BUDGET
        result[path.relative_to(project_root).as_posix()] = facts
    return result


def standing_files(sanctum: Path) -> list[Path]:
    memory = sanctum / "memory"
    if not memory.is_dir():
        return []
    out = []
    for path in sorted(memory.rglob("*.md")):
        rel = path.relative_to(memory)
        if len(rel.parts) > 1 and rel.parts[0] in NOT_STANDING:
            continue
        out.append(path)
    return out


def check_standing(sanctum: Path) -> list[dict]:
    """Standing files longer than a screen."""
    long = []
    for path in standing_files(sanctum):
        facts = measure(path)
        if facts["size_lines"] > STANDING_MAX_LINES or facts["size_chars"] > STANDING_MAX_CHARS:
            long.append({"file": path.relative_to(sanctum).as_posix(), **facts})
    return long


def check_tending(sanctum: Path) -> dict:
    state = _seed.tending_state(sanctum)
    stale = state["tended"] is None or state["session_notes_since"] >= TENDING_NOTES_THRESHOLD
    return {**state, "threshold_notes": TENDING_NOTES_THRESHOLD, "tending_due": stale}


def check_health(sanctum: Path, project_root: Path) -> dict:
    identity = check_identity(sanctum)
    companions = check_companions(project_root, sanctum)
    companions_over = [p for p, f in companions.items() if f["over_threshold"]]
    long_standing = check_standing(sanctum)
    raw = _seed.undistilled_raw(sanctum)
    tending = check_tending(sanctum)

    recs = []
    if identity["over_threshold"]:
        recs.append(
            f"The identity set is ~{identity['total_tokens_est']} tokens (flag at {IDENTITY_TOKEN_BUDGET}): "
            "move detail out of the identity files into memory/ (a discipline, a standing file)."
        )
    if identity["missing"]:
        recs.append(
            f"Identity files missing: {', '.join(identity['missing'])} "
            "(upgrade-sanctum.py restores them from the templates)."
        )
    if companions_over:
        recs.append(
            f"Offer the owner a compaction pass on {', '.join(companions_over)} "
            "(summarize older history, merge duplicates, keep personal sections whole)."
        )
    if long_standing:
        recs.append(
            "Longer than a screen, a section is being appended to: "
            f"{', '.join(f['file'] for f in long_standing)}. Replace what changed; move what happened "
            "to a session note or a chronology file."
        )
    if raw:
        recs.append(f"Distill {len(raw)} raw file(s) still marked status: raw.")
    if tending["tending_due"]:
        recs.append(
            "Memory has never been tended." if tending["tended"] is None else
            f"{tending['session_notes_since']} session notes since the last tending ({tending['tended']}): tend memory."
        )

    return {
        "sanctum_path": str(sanctum),
        "identity": identity,
        "companions": companions,
        "companions_over_budget": companions_over,
        "standing_files_checked": len(standing_files(sanctum)),
        "standing_too_long": long_standing,
        "undistilled_raw": raw,
        "tending": tending,
        "maintenance_recommended": bool(recs),
        "recommendations": recs,
        "recommendation": " ".join(recs) if recs else "Memory is tended and within healthy size limits.",
    }


def render_text(result: dict) -> str:
    if result.get("error"):
        return f"ERROR: {result['message']}\n"
    ident = result["identity"]
    out = [
        f"Sanctum: {result['sanctum_path']}",
        f"Identity set: ~{ident['total_tokens_est']} tokens (flag at {ident['threshold_tokens']})"
        + (" — OVER" if ident["over_threshold"] else ""),
    ]
    for name, tokens in ident["files_tokens_est"].items():
        out.append(f"  {name}: ~{tokens}")
    for name in ident["missing"]:
        out.append(f"  {name}: MISSING")
    out.append("Companion files:")
    for rel, facts in result["companions"].items():
        flag = " — OVER" if facts["over_threshold"] else ""
        out.append(f"  {rel}: ~{facts['tokens_est']} tokens (flag at {facts['threshold_tokens']}){flag}")
    if not result["companions"]:
        out.append("  (none found)")
    out.append(
        f"Standing files: {result['standing_files_checked']} checked, "
        f"{len(result['standing_too_long'])} longer than a screen"
    )
    for f in result["standing_too_long"]:
        out.append(f"  {f['file']}: {f['size_lines']} lines, {f['size_chars']} chars")
    out.append(f"Undistilled raw: {len(result['undistilled_raw'])}")
    for name in result["undistilled_raw"]:
        out.append(f"  raw/{name}")
    t = result["tending"]
    out.append(
        f"Tended: {t['tended']}; session notes since: {t['session_notes_since']}" if t["tended"]
        else f"Never tended; session notes: {t['session_notes_since']}"
    )
    out.append("")
    if result["recommendations"]:
        out.append("Recommended:")
        out += [f"  - {r}" for r in result["recommendations"]]
    else:
        out.append(result["recommendation"])
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Measure Mac's v7 sanctum: the identity set, the companion files, standing "
            "files longer than a screen, undistilled raw files and tending staleness."
        )
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root (where _bmad/ and docs/ live). A sanctum path is accepted too.",
    )
    parser.add_argument(
        "--sanctum-dir",
        default=None,
        help="Override the sanctum directory (staging copies, tests).",
    )
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format (default: json).")
    parser.add_argument("-o", "--output", help="Write the report to a file instead of stdout.")
    args = parser.parse_args()

    given = Path(args.project_root)
    project_root = project_root_for(given)
    override = args.sanctum_dir
    if override is None and project_root != given.resolve():
        override = str(given.resolve())  # a sanctum path was given positionally

    sanctum, state = _seed.locate_sanctum(project_root, override)
    fmt = state["sidecar_format"]
    if fmt in ("v1", "v2"):
        result = {
            "error": True,
            "sidecar_format": fmt,
            "sanctum_path": str(sanctum),
            "message": (
                f"{sanctum} is a {fmt} store. Convert it first: "
                + ("migrate-sidecar-to-v2.py --in-place, then " if fmt == "v1" else "")
                + "migrate-sanctum-to-v7.py."
            ),
        }
    elif fmt == "absent":
        result = {"error": True, "sidecar_format": fmt, "sanctum_path": str(sanctum),
                  "message": f"No sanctum at {sanctum} (First Breath scaffolds one)."}
    else:
        result = {"sidecar_format": fmt, **check_health(sanctum, project_root)}

    output = json.dumps(result, indent=2) if args.format == "json" else render_text(result)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output if args.format == "json" else output.rstrip("\n"))
    return 1 if result.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())
