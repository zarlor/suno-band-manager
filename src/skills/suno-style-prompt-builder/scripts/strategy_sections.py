#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""List or print sections of references/model-prompt-strategies.md by heading.

The catalog is too large to read whole on every run. `--list` gives its headings
as JSON; `--section NAME` (repeatable) prints those sections' markdown verbatim,
each with its subsections, in file order.

A NAME matches a heading exactly (case-insensitive, without the leading #s);
failing that, it matches every heading that starts with NAME, so
"Slider Guidelines" returns "Slider Guidelines (counter-genre, uploaded audio,
Extend)". A section already inside another printed section is not printed twice.

Usage:
    uv run strategy_sections.py --list
    uv run strategy_sections.py --section "How to Load This File"
    uv run strategy_sections.py --section "Counter-Genre Prompting" --section "Slider Guidelines"
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_NAME = "strategy-sections"
VERSION = "1.0.0"

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "references" / "model-prompt-strategies.md"
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def parse_headings(lines: list[str]) -> list[dict]:
    """Headings with level and 1-based line span (a section runs to the next heading
    at its own level or higher). Fenced code blocks are skipped."""
    heads = []
    in_fence = False
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if m:
            heads.append({"heading": m.group(2), "level": len(m.group(1)), "start_line": n})
    for i, h in enumerate(heads):
        end = len(lines)
        for later in heads[i + 1:]:
            if later["level"] <= h["level"]:
                end = later["start_line"] - 1
                break
        h["end_line"] = end
    return heads


def match(heads: list[dict], name: str) -> list[dict]:
    key = name.strip().lstrip("#").strip().lower()
    exact = [h for h in heads if h["heading"].lower() == key]
    return exact or [h for h in heads if h["heading"].lower().startswith(key)]


def main():
    parser = argparse.ArgumentParser(
        description="List or print sections of the model prompt strategies reference by heading.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output: --list prints JSON {"file", "headings": [{heading, level, start_line, end_line}]};
--section prints the matched sections' markdown, separated by blank lines.
Exit codes: 0 = printed, 2 = unreadable file, no mode given, or a NAME matched
no heading (stderr names it and lists the top-level headings)
        """,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="List headings as JSON")
    mode.add_argument("--section", action="append", metavar="NAME", help="Print the section(s) with this heading")
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="Catalog to read (default: the skill's model prompt strategies)")
    args = parser.parse_args()

    # The catalog is UTF-8 (dashes, arrows); print it as UTF-8 whatever the locale says.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        lines = Path(args.file).read_text(encoding="utf-8").split("\n")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Error: cannot read {args.file}: {exc}", file=sys.stderr)
        sys.exit(2)
    heads = parse_headings(lines)

    if args.list:
        print(json.dumps({"script": SCRIPT_NAME, "version": VERSION, "file": args.file, "headings": heads}, indent=2))
        sys.exit(0)

    chosen, unmatched = [], []
    for name in args.section:
        found = match(heads, name)
        if not found:
            unmatched.append(name)
        chosen.extend(h for h in found if h not in chosen)
    if unmatched:
        tops = [h["heading"] for h in heads if h["level"] == 2]
        print(f"Error: no heading matches {', '.join(repr(u) for u in unmatched)}. "
              f"Top-level headings: {'; '.join(tops)}. Run --list for all.", file=sys.stderr)
        sys.exit(2)

    chosen.sort(key=lambda h: h["start_line"])
    spans = []
    for h in chosen:
        if spans and h["start_line"] <= spans[-1][1]:
            continue  # inside a section already printed
        spans.append((h["start_line"], h["end_line"]))
    print("\n\n".join("\n".join(lines[s - 1:e]).rstrip() for s, e in spans))
    sys.exit(0)


if __name__ == "__main__":
    main()
