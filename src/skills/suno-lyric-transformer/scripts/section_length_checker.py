#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check section content lengths against expected ranges from the section-jobs framework.

Parses lyrics by metatag headers and validates that each section falls within
recommended line count ranges for Suno compatibility.

Usage:
    uv run section_length_checker.py <lyrics-file> [options]

    # Check section lengths in a file
    uv run section_length_checker.py lyrics.txt

    # Check from text argument
    uv run section_length_checker.py --text "[Verse 1]\\nLine one\\nLine two"

    # Output to file
    uv run section_length_checker.py lyrics.txt -o results.json
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from script_io import read_text_input, write_output
from tag_vocab import SOLO_INSTRUMENTS, is_tag_line, section_base, section_opener

SCRIPT_NAME = "section-length-checker"
VERSION = "1.1.0"

# Expected line count ranges per section type (min, max)
SECTION_RANGES = {
    "intro": (0, 4),
    "verse": (4, 8),
    "pre-chorus": (2, 4),
    "chorus": (2, 6),
    "bridge": (2, 6),
    "breakdown": (2, 4),
    "build-up": (2, 4),
    "buildup": (2, 4),
    "outro": (1, 6),  # a one-line outro is a short-poem strategy (thesis isolation)
    "hook": (1, 4),
    "refrain": (2, 6),
    "interlude": (0, 4),
    "post-chorus": (2, 4),
    "solo": (0, 2),
    **{f"{instrument} solo": (0, 2) for instrument in SOLO_INSTRUMENTS},
    "instrumental": (0, 4),
    "instrumental break": (0, 4),
    "instrumental intro": (0, 4),
    "instrumental outro": (0, 4),
    "drum break": (0, 4),
    "percussion break": (0, 4),
    "bass drop": (0, 4),
    "strings rise": (0, 4),
    "big finish": (0, 6),
    "reprise": (1, 6),
    "coda": (0, 6),
    "build": (2, 4),
    "drop": (0, 4),
    "break": (0, 4),
    "fade out": (0, 4),
    "fade in": (0, 4),
}


def normalize_section_name(tag: str) -> str:
    """Normalize section tag to base name: 'Verse 1' -> 'verse', 'Final Chorus' -> 'chorus',
    'Verse 1 - half-spoken' -> 'verse'."""
    return section_base(tag) or tag.lower().strip()


def parse_sections(text: str) -> list[dict]:
    """Parse lyrics into sections with line counts.

    Only a section tag (tag_vocab.py) opens a section. Every other tag-only
    line ([Energy: slow], [Harmonized], [End], an unrecognized tag) is a cue,
    not lyric content, and leaves the lines after it in the current section.
    """
    sections = []
    current_section = None

    for line in text.split('\n'):
        opener = section_opener(line)
        if opener:
            current_section = {
                "tag": opener,
                "base_name": normalize_section_name(opener),
                "lyric_lines": []
            }
            sections.append(current_section)
            continue

        if is_tag_line(line):
            continue

        stripped = line.strip()
        if stripped and current_section is not None:
            current_section["lyric_lines"].append(stripped)

    return sections


# Genres that get relaxed section length constraints. A genre matches when any
# of its words does ("prog metal", "progressive-rock").
PROG_GENRES = {"prog", "metal", "progressive", "experimental"}


def is_prog_genre(genre: str) -> bool:
    return bool(set(re.split(r'[\s,/-]+', genre.lower())) & PROG_GENRES)


def check_sections(text: str, genre: str = "") -> dict:
    """Check section lengths against expected ranges."""
    sections = parse_sections(text)
    findings = []
    section_results = []
    is_prog = is_prog_genre(genre)

    if not sections:
        findings.append({
            "severity": "high",
            "category": "section-length",
            "location": {"file": "lyrics"},
            "issue": "No section tags found, so no section length was checked.",
            "fix": "Add section tags ([Verse 1], [Chorus]) before checking section lengths."
        })

    for section in sections:
        line_count = len(section["lyric_lines"])
        base = section["base_name"]
        expected = SECTION_RANGES.get(base)
        # In prog/metal mode, double the max for all sections
        if expected and is_prog:
            expected = (expected[0], expected[1] * 2)

        result = {
            "tag": section["tag"],
            "base_name": base,
            "line_count": line_count,
            "expected_range": list(expected) if expected else None,
            "status": "unknown"
        }

        if expected is None:
            result["status"] = "unknown"
            findings.append({
                "severity": "info",
                "category": "section-length",
                "location": {"section": section["tag"]},
                "issue": f"Section [{section['tag']}] has no defined expected range.",
                "fix": "This section type is not in the standard range database."
            })
        elif line_count < expected[0]:
            result["status"] = "short"
            findings.append({
                "severity": "medium",
                "category": "section-length",
                "location": {"section": section["tag"]},
                "issue": f"Section [{section['tag']}] is too short: {line_count} lines (expected {expected[0]}-{expected[1]}).",
                "fix": f"Add {expected[0] - line_count} more line(s) to reach the minimum of {expected[0]}."
            })
        elif line_count > expected[1]:
            result["status"] = "long"
            findings.append({
                "severity": "medium",
                "category": "section-length",
                "location": {"section": section["tag"]},
                "issue": f"Section [{section['tag']}] is too long: {line_count} lines (expected {expected[0]}-{expected[1]}).",
                "fix": f"Remove {line_count - expected[1]} line(s) to reach the maximum of {expected[1]}."
            })
        else:
            result["status"] = "pass"

        section_results.append(result)

    return {
        "sections": section_results,
        "findings": findings
    }


def build_report(result: dict, text: str, skill_path: str = "") -> dict:
    """Build the standard output report."""
    findings = result["findings"]

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1

    passed = sum(1 for s in result["sections"] if s["status"] == "pass")
    failed = sum(1 for s in result["sections"] if s["status"] in ("short", "long"))

    status = "pass"
    if failed > 0 or severity_counts["high"] > 0:
        status = "warning"

    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "skill_path": skill_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "metrics": {
            "total_sections": len(result["sections"]),
            "sections_pass": passed,
            "sections_fail": failed,
        },
        "sections": result["sections"],
        "findings": findings,
        "summary": {
            "total": len(findings),
            **severity_counts
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Check section content lengths against expected ranges.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s lyrics.txt
  %(prog)s --text "[Verse 1]\\nLine 1\\nLine 2\\nLine 3\\nLine 4"
  %(prog)s --stdin < lyrics.txt
  %(prog)s lyrics.txt -o results.json --verbose

Expected ranges (lines):
  Intro=0-4, Verse=4-8, Pre-Chorus=2-4, Chorus=2-6,
  Bridge=2-6, Breakdown=2-4, Build-Up=2-4, Outro=1-6,
  Hook=1-4, Refrain=2-6

Status: warning when a section is out of range or the text has no section
tags (nothing was checked), else pass.
Exit codes: 0 = check ran (read status and sections), 2 = bad input
        """
    )
    parser.add_argument("file", nargs="?", help="Path to lyrics text file")
    parser.add_argument("--text", help="Lyrics text to check directly")
    parser.add_argument("--stdin", action="store_true", help="Read lyrics from stdin")
    parser.add_argument("-o", "--output", help="Output file path (defaults to stdout)")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostics to stderr")
    parser.add_argument("--skill-path", default="", help="Skill path for report context")
    parser.add_argument("--genre", default="",
                        help="Genre hint; one holding the word prog, metal, progressive or experimental "
                             "(\"prog metal\") doubles each section's maximum")

    args = parser.parse_args()

    text = read_text_input(args, parser)

    if args.verbose:
        print(f"Checking section lengths ({len(text.splitlines())} lines)...", file=sys.stderr)

    result = check_sections(text, genre=args.genre)
    report = build_report(result, text, args.skill_path)

    output_json = json.dumps(report, indent=2)

    write_output(output_json, args.output)
    if args.output and args.verbose:
        print(f"Report written to {args.output}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
