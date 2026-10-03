#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Checks the size of what Mac loads, in tokens, and recommends maintenance.

What it measures:
  - MEMORY.md against a token budget, plus packed lines (single lines long
    enough to hide a whole session narrative). A line count would miss both.
  - The whole always-loaded spine (the seven files read on every wake).
  - patterns.md / chronology.md: organic reference files, not loaded on wake,
    flagged only on runaway growth (generous character ceilings).
  - The two owner companion files that load on every wake — the voice file(s)
    `docs/voice-context-*.md` and `docs/mac-preferences.md` — against a token
    budget. Over budget means "offer the owner a compaction pass"; they are
    never digested or split by a script.
  - INDEX.md coverage: organic sanctum files that INDEX.md does not mention.
  - sessions/ files are raw logs, counted but never flagged.

Token figures are estimates (characters / 4), good enough to spot bloat.

Usage:
    uv run scripts/check-memory-health.py <sanctum-path> [--project-root DIR]
                                          [--sanctum-dir PATH] [-o OUTPUT]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SPINE = [
    "access-boundaries.md",
    "INDEX.md",
    "MEMORY.md",
    "CREED.md",
    "PERSONA.md",
    "BOND.md",
    "CAPABILITIES.md",
]

# name: (metric, limit). MEMORY.md is the always-loaded curated file: the BMB
# guardrail is ~1,500 tokens; a catalog-heavy owner may earn more, so the flag
# fires at 3,000. patterns/chronology are not loaded on wake.
THRESHOLDS = {
    "MEMORY.md": ("tokens", 3000),
    "patterns.md": ("chars", 60000),
    "chronology.md": ("chars", 120000),
}
SPINE_TOKEN_BUDGET = 12000       # all seven always-loaded files together
COMPANION_TOKEN_BUDGET = 20000   # each companion file that loads every wake
PACKED_LINE_CHARS = 600          # a MEMORY.md line longer than this is packed
SANCTUM_REL = ("_bmad", "_memory", "band-manager-sidecar")


def tokens_est(text: str) -> int:
    return round(len(text) / 4)


def measure(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "size_chars": len(text),
        "size_lines": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        "tokens_est": tokens_est(text),
    }


def infer_project_root(sanctum: Path) -> Path | None:
    parts = sanctum.resolve().parts
    if len(parts) > 3 and tuple(parts[-3:]) == SANCTUM_REL:
        return Path(*parts[:-3])
    return None


def packed_lines(path: Path) -> list[dict]:
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if len(line) > PACKED_LINE_CHARS:
            out.append({"line": n, "chars": len(line)})
    return out


def index_unlisted(sanctum: Path) -> list[str]:
    """Organic top-level files INDEX.md does not mention (an unlisted file is lost)."""
    index = sanctum / "INDEX.md"
    if not index.is_file():
        return []
    text = index.read_text(encoding="utf-8", errors="replace")
    skip = set(SPINE) | {"PULSE.md"}
    out = []
    for path in sorted(sanctum.iterdir()):
        if path.name.startswith(".") or path.name in skip:
            continue
        if path.is_dir():
            if path.name in ("sessions", "capabilities"):
                continue
            name = path.name + "/"
        else:
            name = path.name
        stem = name.rstrip("/")
        # `_collection_*.txt` style wildcards in INDEX count as a mention.
        prefix = stem.split("_")[1] if stem.startswith("_") and "_" in stem[1:] else None
        if stem in text or (prefix and f"_{prefix}_" in text):
            continue
        out.append(name)
    return out


def check_companions(project_root: Path) -> dict:
    docs = project_root / "docs"
    files = sorted(docs.glob("voice-context-*.md")) if docs.is_dir() else []
    prefs = docs / "mac-preferences.md"
    if prefs.is_file():
        files.append(prefs)
    result = {}
    for path in files:
        facts = measure(path)
        facts["threshold_tokens"] = COMPANION_TOKEN_BUDGET
        facts["over_threshold"] = facts["tokens_est"] > COMPANION_TOKEN_BUDGET
        result[str(path.relative_to(project_root))] = facts
    return result


def check_health(sanctum_path: Path, project_root: Path | None = None) -> dict:
    files: dict = {}
    needs_pruning: list[str] = []
    for name, (metric, threshold) in THRESHOLDS.items():
        path = sanctum_path / name
        if not path.exists():
            files[name] = {"exists": False}
            continue
        facts = measure(path)
        measured = facts["tokens_est"] if metric == "tokens" else facts["size_chars"]
        facts.update({"metric": metric, "threshold": threshold, "over_threshold": measured > threshold})
        if name == "MEMORY.md":
            facts["packed_lines"] = packed_lines(path)
        files[name] = facts
        if facts["over_threshold"] or facts.get("packed_lines"):
            needs_pruning.append(name)

    spine_tokens = {n: measure(sanctum_path / n)["tokens_est"] for n in SPINE if (sanctum_path / n).is_file()}
    spine_total = sum(spine_tokens.values())

    sessions_dir = sanctum_path / "sessions"
    session_count = len(list(sessions_dir.glob("*.md"))) if sessions_dir.is_dir() else 0

    root = project_root or infer_project_root(sanctum_path)
    companions = check_companions(root) if root else None
    companions_over = [p for p, f in (companions or {}).items() if f["over_threshold"]]
    unlisted = index_unlisted(sanctum_path)

    recs = []
    if needs_pruning:
        recs.append(
            f"Curate {', '.join(needs_pruning)}: push narrative detail down to sessions/, "
            "split packed lines, keep the live state."
        )
    if spine_total > SPINE_TOKEN_BUDGET:
        recs.append(f"The always-loaded spine is ~{spine_total} tokens (budget {SPINE_TOKEN_BUDGET}).")
    if companions_over:
        recs.append(
            f"Offer the owner a compaction pass on {', '.join(companions_over)} "
            "(summarize older history, merge duplicates, keep personal sections whole)."
        )
    if unlisted:
        recs.append(f"Add INDEX.md rows for: {', '.join(unlisted)}.")

    return {
        "sanctum_path": str(sanctum_path),
        "files": files,
        "spine_tokens_est": spine_tokens,
        "spine_total_tokens_est": spine_total,
        "spine_over_budget": spine_total > SPINE_TOKEN_BUDGET,
        "companions": companions,
        "companions_over_budget": companions_over,
        "index_unlisted": unlisted,
        "session_files": session_count,
        "needs_pruning": needs_pruning,
        "maintenance_recommended": bool(recs),
        "recommendation": " ".join(recs) if recs else "Memory files are within healthy size limits.",
    }


def main():
    parser = argparse.ArgumentParser(description="Check sanctum memory size and coverage")
    parser.add_argument("sanctum_path", help="Path to the sanctum (band-manager-sidecar) directory")
    parser.add_argument(
        "--sanctum-dir",
        default=None,
        help="Override the sanctum directory (wins over the positional path).",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root for the companion files. Default: inferred from the sanctum path.",
    )
    parser.add_argument("-o", "--output", help="Output file path")
    args = parser.parse_args()

    sanctum = Path(args.sanctum_dir) if args.sanctum_dir else Path(args.sanctum_path)
    if not sanctum.exists():
        result = {"error": True, "message": f"Sanctum directory not found: {sanctum}"}
    else:
        root = Path(args.project_root) if args.project_root else None
        result = check_health(sanctum, root)

    output = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
    sys.exit(0)
