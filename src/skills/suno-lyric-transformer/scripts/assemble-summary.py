#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Assemble the Transformation Summary from the validator, syllable and cliche reports.

Every figure (sections, character budget, syllable range, duration, cliche count)
is read from the JSON of validate-lyrics.py, syllable-counter.py and, when CD ran,
cliche-detector.py; nothing is computed by hand. The JSON on stdout carries
`transformation_summary`, shaped exactly like the headless contract's field, so a
headless run copies it as is; `markdown` is the block an interactive run pastes.

Usage:
    uv run assemble-summary.py --validation val.json --syllables syl.json [--cliches cli.json] [options]

    # JSON report (default)
    uv run assemble-summary.py --validation val.json --syllables syl.json --cliches cli.json --transformations "ST,CC,RA,CD"

    # Just the markdown block
    uv run assemble-summary.py --validation val.json --syllables syl.json --markdown
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from suno_constants import SUNO_LYRICS_HARD_LIMIT, SUNO_LYRICS_QUALITY_BUDGET
from option_codes import CODE_NAMES

SCRIPT_NAME = "assemble-summary"
VERSION = "2.0.0"

# The metrics each input report must carry (all three scripts always emit them).
REQUIRED = {
    "validate-lyrics": ["section_count", "sections", "lyric_lines", "total_lines", "character_count",
                        "lyric_character_count", "metatag_character_count"],
    "syllable-counter": ["min_syllables", "max_syllables", "average_syllables_per_line",
                         "total_syllables", "estimated_duration"],
    "cliche-detector": ["total_cliches_found", "categories"],
}


class InputError(Exception):
    """An input report that is missing, unreadable, or not the expected script's output."""


def load_report(path: str, script: str) -> dict:
    """Load one script's JSON report; raise InputError naming what is wrong."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError(f"cannot read {script} report {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"{script} report {path} is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise InputError(f"{script} report {path} is not a JSON object")
    if data.get("script", script) != script:
        raise InputError(f"{path} is {data.get('script')!r} output, expected {script}")
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        raise InputError(f"{script} report {path} has no metrics object")
    missing = [key for key in REQUIRED[script] if key not in metrics]
    if missing:
        raise InputError(f"{script} report {path} lacks metrics: {', '.join(missing)}")
    return data


def overall_status(statuses: dict) -> str:
    """fail when the validator failed; warning when any input warned or failed; else pass."""
    if statuses["validation"] == "fail":
        return "fail"
    if any(st in ("fail", "warning") for st in statuses.values()):
        return "warning"
    return "pass"


def section_type(tag: str) -> str:
    """The section's kind without its number or cue: "Verse 1 - riff" -> "Verse", "Final Verse" -> "Final Verse"."""
    base = re.split(r"\s*(?::|\||\s[-–—]\s?|[–—])", tag, maxsplit=1)[0].strip()
    return re.sub(r"\s+\d+$", "", base) or tag


def assemble_summary(validation: dict, syllables: dict, cliches: dict | None,
                     transformations: list[str]) -> dict:
    """Assemble summary data from the reports; cliches is None when CD did not run."""
    val = validation["metrics"]
    syl = syllables["metrics"]
    char_count = val["character_count"]
    budget_pct = round(100 * char_count / SUNO_LYRICS_QUALITY_BUDGET)
    duration = syl["estimated_duration"] or {}
    statuses = {
        "validation": validation.get("status", "unknown"),
        "syllables": syllables.get("status", "unknown"),
        "cliches": cliches.get("status", "unknown") if cliches is not None else "not run",
    }
    cli = cliches["metrics"] if cliches is not None else None

    return {
        "section_count": val["section_count"],
        "sections": val["sections"],
        "unique_section_types": sorted({section_type(s) for s in val["sections"]}),
        "lyric_lines": val["lyric_lines"],
        "total_lines": val["total_lines"],
        "character_count": char_count,
        "lyric_character_count": val["lyric_character_count"],
        "metatag_character_count": val["metatag_character_count"],
        "character_budget": f"{char_count}/{SUNO_LYRICS_QUALITY_BUDGET} ({budget_pct}%)",
        "character_budget_pct": budget_pct,
        "over_quality_budget": char_count > SUNO_LYRICS_QUALITY_BUDGET,
        "over_hard_limit": char_count > SUNO_LYRICS_HARD_LIMIT,
        "syllable_range": f"{syl['min_syllables']}-{syl['max_syllables']}",
        "average_syllables": syl["average_syllables_per_line"],
        "total_syllables": syl["total_syllables"],
        "syllables_latin_only": syl.get("latin_only", False),
        "syllable_skipped_lines": syl.get("skipped_line_count", 0),
        "estimated_duration": duration.get("formatted"),
        "estimated_duration_sec": duration.get("max_seconds"),
        "cliche_detection_ran": cli is not None,
        "total_cliches": cli["total_cliches_found"] if cli is not None else None,
        "cliche_categories": cli["categories"] if cli is not None else {},
        "input_status": statuses,
        "validation_status": statuses["validation"],
        "cliche_status": statuses["cliches"],
        "transformations_applied": transformations,
        "transformation_descriptions": [f"- {code}: {CODE_NAMES[code]}" for code in transformations],
    }


def transformation_summary(data: dict) -> dict:
    """The headless contract's transformation_summary, field for field."""
    return {
        "sections": data["sections"],
        "section_count": data["section_count"],
        "estimated_duration": data["estimated_duration"],
        "transformations_applied": data["transformations_applied"],
        "syllable_range": data["syllable_range"],
        "character_count": data["character_count"],
        "lyric_character_count": data["lyric_character_count"],
        "metatag_character_count": data["metatag_character_count"],
        "character_budget": data["character_budget"],
    }


def format_markdown(data: dict) -> str:
    """Format the summary data as a markdown block."""
    lines = [
        "## Transformation Summary",
        "",
        f"**Validation Status:** {data['validation_status'].upper()}",
        f"**Sections:** {data['section_count']} ({', '.join(data['unique_section_types'])})",
        f"**Lyric Lines:** {data['lyric_lines']}",
        f"**Syllable Range:** {data['syllable_range']} (avg {data['average_syllables']})",
        f"**Estimated Duration:** ~{data['estimated_duration'] or 'unknown'}",
    ]

    if data['syllable_skipped_lines']:
        lines.append(f"**Syllables:** Latin lines only ({data['syllable_skipped_lines']} non-Latin lines not counted)")

    if data['character_count'] > 0:
        lines.append(
            f"**Character Budget:** Lyrics {data['lyric_character_count']} + Metatags "
            f"{data['metatag_character_count']} = {data['character_budget']} of the quality "
            f"budget ({SUNO_LYRICS_HARD_LIMIT} hard limit)"
        )

    lines.append("")
    if not data['cliche_detection_ran']:
        lines.append("**Cliche Detection:** not run")
    else:
        lines.append(f"**Cliche Detection:** {data['total_cliches']} found ({data['cliche_status']})")
    if data['cliche_categories']:
        for cat, count in sorted(data['cliche_categories'].items()):
            lines.append(f"  - {cat}: {count}")

    if data['transformations_applied']:
        lines.append("")
        lines.append("**Transformations Applied:**")
        for desc in data['transformation_descriptions']:
            lines.append(desc)

    lines.append("")
    return "\n".join(lines)


def build_report(data: dict, markdown: str, skill_path: str = "") -> dict:
    """Build the standard output report; status follows the inputs."""
    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "skill_path": skill_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": overall_status(data["input_status"]),
        "transformation_summary": transformation_summary(data),
        "metrics": data,
        "markdown": markdown,
    }


def parse_codes(raw: str) -> list[str]:
    codes = [c.strip().upper() for c in raw.split(",") if c.strip()]
    unknown = [c for c in codes if c not in CODE_NAMES]
    if unknown:
        raise InputError(f"unknown transformation codes: {', '.join(unknown)} (valid: {', '.join(CODE_NAMES)})")
    return codes


def main():
    parser = argparse.ArgumentParser(
        description="Assemble the Transformation Summary from validator, syllable and cliche reports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --validation val.json --syllables syl.json --cliches cli.json --transformations "ST,CC,RA,CD"
  %(prog)s --validation val.json --syllables syl.json --markdown

Omit --cliches when CD did not run: the summary says "not run" rather than 0.
Status: fail when the validator failed, warning when any input warned, else pass.
Exit codes: 0 = summary assembled (read status), 2 = an input is missing,
unreadable, not that script's JSON, or lacks a metric; or an unknown code
        """
    )
    parser.add_argument("--validation", required=True, help="validate-lyrics.py JSON report")
    parser.add_argument("--syllables", required=True, help="syllable-counter.py JSON report")
    parser.add_argument("--cliches", help="cliche-detector.py JSON report (omit when CD did not run)")
    parser.add_argument("--transformations", default="", help="Comma-separated codes applied")
    parser.add_argument("--markdown", action="store_true", help="Output only the markdown block")
    parser.add_argument("-o", "--output", help="Write the output here instead of stdout")
    parser.add_argument("--skill-path", default="", help="Skill path for report context")

    args = parser.parse_args()

    try:
        validation = load_report(args.validation, "validate-lyrics")
        syllables = load_report(args.syllables, "syllable-counter")
        cliches = load_report(args.cliches, "cliche-detector") if args.cliches else None
        transformations = parse_codes(args.transformations)
    except InputError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    data = assemble_summary(validation, syllables, cliches, transformations)
    markdown = format_markdown(data)
    out = markdown if args.markdown else json.dumps(build_report(data, markdown, args.skill_path), indent=2)

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        print(out)
    sys.exit(0)


if __name__ == "__main__":
    main()
