#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Scan docs/wip-*.md for COMPLETED markers and correlate against the songbook.

The `## STATUS: COMPLETED` marker is described across the prompts as
"machine-readable … that pending/parked listings should grep for" — yet nothing
grepped it; the LLM hand-scanned every WIP file at every save-memory, every
reconcile, and every post-publish. This script makes the marker actually
machine-read.

For each `docs/wip-*.md` file it emits:

  - status:               "completed" if the file carries a
                          `## STATUS: COMPLETED` marker, else "active"
  - completed_as:         the published title quoted in the marker (or null)
  - published_date:       the date in the marker (or null)
  - songbook_ref:         the songbook path the marker points at (or null)
  - correlation_warning:  for an *active* (unmarked) WIP whose working title
                          collides with a *published* songbook entry — i.e. it
                          "looks like the source of a just-published song but
                          isn't marked." null when no collision.

The LLM keeps only the genuinely judgmental part: confirming the match and
authorizing the marker write. This script does the scan + match + correlate.

Songbook parsing reuses `validate-sidecar.py`'s helpers (load_all_songs / Song)
so there is one songbook parser, not two.

Usage:
    scan-wip-status.py [project_root]
    scan-wip-status.py --format json
    scan-wip-status.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_validate_sidecar():
    """Import validate-sidecar.py by path to reuse its songbook parser.

    Registered in sys.modules before exec so its @dataclass definitions resolve
    (dataclasses looks the module up by name in sys.modules during class build).
    """
    mod_path = Path(__file__).resolve().parent / "validate-sidecar.py"
    spec = spec_from_file_location("validate_sidecar", mod_path)
    mod = module_from_spec(spec)
    sys.modules["validate_sidecar"] = mod
    spec.loader.exec_module(mod)
    return mod


_vs = _load_validate_sidecar()

# `## STATUS: COMPLETED as "<title>" — published <YYYY-MM-DD>` — the canonical
# marker from reconcile.md "The COMPLETED WIP convention". COMPLETED_RE matches
# the marker *line* (its presence is what flips status → completed); title and
# date are pulled from that line with separate, eager sub-patterns so quoting /
# separator variants don't swallow the captures.
COMPLETED_RE = re.compile(r"^##\s*STATUS:\s*COMPLETED\b.*$", re.IGNORECASE | re.MULTILINE)
COMPLETED_TITLE_RE = re.compile(r'\bas\s+["“]([^"”\n]+)["”]', re.IGNORECASE)
COMPLETED_DATE_RE = re.compile(r"published\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)

# A songbook-path pointer inside the WIP's completion block, e.g.
# `docs/songbook/<band>/<slug>.md`.
SONGBOOK_REF_RE = re.compile(r"`(docs/songbook/[^`]+\.md)`")


def _normalize_title(title: str) -> str:
    """Lowercase + collapse whitespace + drop a trailing version suffix.

    So "The Slide", "the slide", and "The Slide v2" all compare equal enough to
    flag a correlation. Matching here is intentionally loose — it only raises a
    *warning* for the LLM to confirm, never an automatic state change.
    """
    t = title.strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+v\d+$", "", t)  # strip trailing "v2"/"v3"
    return t


def _wip_working_title(path: Path, text: str) -> str:
    """Best-effort working title for an active WIP.

    Prefer the first `# ` heading; fall back to the filename between the
    `wip-` prefix and a trailing `-fragments` suffix.
    """
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    stem = path.stem
    stem = re.sub(r"^wip-", "", stem)
    stem = re.sub(r"-fragments?$", "", stem)
    return stem.replace("-", " ").strip()


def scan_wip_files(project_root: Path) -> list[dict]:
    """Scan docs/wip-*.md and correlate against published songbook titles."""
    docs_dir = project_root / "docs"
    results: list[dict] = []
    if not docs_dir.is_dir():
        return results

    # Published songbook titles (normalized) → for the correlation warning.
    songs, _ = _vs.load_all_songs(project_root)
    published_titles = {
        _normalize_title(s.title): str(s.path) for s in songs if s.is_published
    }

    for wip_path in sorted(docs_dir.glob("wip-*.md")):
        try:
            text = wip_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        rel = str(wip_path.relative_to(project_root))
        marker = COMPLETED_RE.search(text)

        if marker:
            marker_line = marker.group(0)
            title_m = COMPLETED_TITLE_RE.search(marker_line)
            date_m = COMPLETED_DATE_RE.search(marker_line)
            ref_match = SONGBOOK_REF_RE.search(text)
            results.append(
                {
                    "path": rel,
                    "status": "completed",
                    "completed_as": title_m.group(1).strip() if title_m else None,
                    "published_date": date_m.group(1) if date_m else None,
                    "songbook_ref": ref_match.group(1) if ref_match else None,
                    "correlation_warning": None,
                }
            )
            continue

        # Active (unmarked) WIP — correlate its working title against published songs.
        working_title = _wip_working_title(wip_path, text)
        norm = _normalize_title(working_title)
        warning = None
        if norm and norm in published_titles:
            warning = (
                f"working title {working_title!r} matches published songbook entry "
                f"{published_titles[norm]} but this WIP carries no "
                f"'## STATUS: COMPLETED' marker — looks like the source of a "
                f"published song. Confirm and mark COMPLETED if so."
            )
        results.append(
            {
                "path": rel,
                "status": "active",
                "completed_as": None,
                "published_date": None,
                "songbook_ref": published_titles.get(norm),
                "correlation_warning": warning,
            }
        )

    return results


def build_report(project_root: Path) -> dict:
    files = scan_wip_files(project_root)
    return {
        "status": "ok",
        "wip_count": len(files),
        "completed": sum(1 for f in files if f["status"] == "completed"),
        "active": sum(1 for f in files if f["status"] == "active"),
        "correlation_warnings": sum(
            1 for f in files if f["correlation_warning"]
        ),
        "files": files,
    }


def format_text(report: dict) -> str:
    lines = [
        "WIP Status Scan",
        "=" * 15,
        f"{report['wip_count']} WIP file(s): "
        f"{report['completed']} completed, {report['active']} active "
        f"({report['correlation_warnings']} correlation warning(s))",
        "",
    ]
    if not report["files"]:
        lines.append("No docs/wip-*.md files found.")
        return "\n".join(lines)
    for f in report["files"]:
        lines.append(f"[{f['status'].upper()}] {f['path']}")
        if f["completed_as"]:
            date = f["published_date"] or "?"
            lines.append(f'    completed as "{f["completed_as"]}" — published {date}')
        if f["songbook_ref"]:
            lines.append(f"    songbook: {f['songbook_ref']}")
        if f["correlation_warning"]:
            lines.append(f"    ! {f['correlation_warning']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan docs/wip-*.md for COMPLETED markers and correlate unmarked "
            "WIPs against published songbook titles. The scan/match/correlate is "
            "deterministic; the LLM keeps the judgment (confirm the match, "
            "authorize the state change)."
        )
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(f"ERROR: project root not found: {project_root}", file=sys.stderr)
        return 2

    report = build_report(project_root)
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
