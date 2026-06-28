#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Checks sanctum memory file sizes and recommends maintenance.

Tuned for the v2 sanctum model:
  - MEMORY.md is CURATED and bounded — it should stay small (the raw per-session
    narrative lives in sessions/, not here). A tight threshold flags it the
    moment curation slips.
  - patterns.md / chronology.md are organic append-only files — keep their
    existing, more-generous thresholds.
  - sessions/YYYY-MM-DD.md are RAW per-date logs — intentionally large and never
    loaded on rebirth, so they are NOT size-checked (a big session file is
    healthy, not a problem).

Usage:
    uv run scripts/check-memory-health.py <sanctum-path> [--sanctum-dir PATH] [-o OUTPUT]
    uv run scripts/check-memory-health.py --help

Arguments:
    sanctum-path    Path to the sanctum (band-manager-sidecar) directory

Options:
    --sanctum-dir   Override the sanctum directory (takes precedence over the
                    positional sanctum-path). Use to test a staging copy.
    -o, --output    Write JSON output to file instead of stdout
"""

import argparse
import json
import sys
from pathlib import Path

# Per-file thresholds tuned for the v2 sanctum.
#
# MEMORY.md is the always-loaded CURATED file. Its meaningful bound is LINE
# count — it's distilled "what the owner is doing/prefers" state, kept tight
# (its own header targets <~200 lines). The derived catalog sections are
# legitimately long single-line bullets, so a tight CHARACTER cap would false-
# alarm on a perfectly-curated file; the ~200-line cap is the honest bound.
#
# patterns.md / chronology.md are organic, append-only REFERENCE files that are
# NOT loaded on rebirth, so their size has little runtime cost. They are kept in
# the check (to catch genuine runaway growth) with generous character ceilings
# sized to the real preserved files — a healthy post-migration store is GREEN.
#
# sessions/YYYY-MM-DD.md are raw per-date logs — intentionally large, never
# loaded on rebirth, and deliberately NOT size-checked.
THRESHOLDS = {
    # name: (metric, limit) where metric is "lines" or "chars"
    "MEMORY.md": ("lines", 200),
    "patterns.md": ("chars", 60000),
    "chronology.md": ("chars", 120000),
}


def check_health(sanctum_path: Path) -> dict:
    """Check sanctum memory file sizes and flag maintenance needs."""
    files = {}
    needs_pruning = []

    for name, (metric, threshold) in THRESHOLDS.items():
        file_path = sanctum_path / name
        if file_path.exists():
            text = file_path.read_text()
            size_chars = len(text)
            size_lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
            measured = size_lines if metric == "lines" else size_chars
            over = measured > threshold
            files[name] = {
                "metric": metric,
                "size_chars": size_chars,
                "size_lines": size_lines,
                "threshold": threshold,
                "over_threshold": over,
            }
            if over:
                needs_pruning.append(name)
        else:
            files[name] = {"exists": False}

    # sessions/ files are raw per-date logs — report their count for visibility
    # but never flag them for pruning (they're not loaded on rebirth).
    sessions_dir = sanctum_path / "sessions"
    session_count = (
        len(list(sessions_dir.glob("*.md"))) if sessions_dir.is_dir() else 0
    )

    return {
        "sanctum_path": str(sanctum_path),
        "files": files,
        "session_files": session_count,
        "needs_pruning": needs_pruning,
        "maintenance_recommended": len(needs_pruning) > 0,
        "recommendation": (
            f"Files exceeding size thresholds: {', '.join(needs_pruning)}. "
            "Consider condensing verbose entries and archiving old content."
            if needs_pruning
            else "Memory files are within healthy size limits."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description="Check sanctum memory file health")
    parser.add_argument("sanctum_path", help="Path to sanctum (band-manager-sidecar) directory")
    parser.add_argument(
        "--sanctum-dir",
        default=None,
        help=(
            "Override the sanctum directory (takes precedence over the positional "
            "sanctum-path). Use to test a staging copy without touching live data."
        ),
    )
    parser.add_argument("-o", "--output", help="Output file path")
    args = parser.parse_args()

    sanctum = Path(args.sanctum_dir) if args.sanctum_dir else Path(args.sanctum_path)
    if not sanctum.exists():
        result = {"error": True, "message": f"Sanctum directory not found: {sanctum}"}
    else:
        result = check_health(sanctum)

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
    sys.exit(0)
