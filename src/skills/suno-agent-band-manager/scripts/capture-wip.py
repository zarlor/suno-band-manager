#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Capture creative material verbatim into a song's WIP file, attributed and dated.

The Workshop Capture discipline: a lyric swing, sketch or pasted external text
goes into the song's WIP file before anyone discusses it, because the
conversation does not survive. This script makes that one step mechanical:

  - finds `docs/wip-<slug>-fragments.md` for the working title, or the file
    given with --file (a songbook entry being workshopped), and creates the WIP
    file when there is none;
  - appends the material byte for byte in a fenced block under `## Swings tried`
    (created when missing; a lone `_(none yet)_` placeholder is replaced), headed
    with the label, the source and the date;
  - leaves every other byte of the file as it was, and checks that it did;
  - reports each captured line's syllable count (`line_syllables`), the shared
    heuristic the lyric transformer uses, so line-length judgments rest on a count.

`--critique` adds the critique to an entry captured earlier (matched by its
label), so a rejected swing keeps its text and the reason together.

Usage:
    capture-wip.py <project-root> --title "Low Tide Ledger" --source "ChatGPT" \
        --label "Swing 3 — verse 2 turn" [--framing "..."] [--date YYYY-MM-DD] < swing.txt
    capture-wip.py <project-root> --file docs/songbook/band/song.md --source "owner" --label "Bridge draft" --text "..."
    capture-wip.py <project-root> --title "Low Tide Ledger" --label "Swing 3 — verse 2 turn" --critique "Too on the nose."

Prints JSON. Exit 0 written, 1 refused (with a reason), 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
from syllables import count_line_syllables

SECTION = "## Swings tried"
PLACEHOLDER = "_(none yet)_"


def slugify(title: str) -> str:
    text = re.sub(r"[`*_\[\]()\"'’“”]", "", title.lower())
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "untitled"


def fence_for(text: str) -> str:
    """A backtick fence longer than any backtick run inside the material."""
    longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def wip_path(root: Path, title: str | None, file: str | None) -> Path:
    if file:
        path = Path(file)
        return path if path.is_absolute() else root / path
    return root / "docs" / f"wip-{slugify(title or '')}-fragments.md"


def new_wip(title: str) -> str:
    return f"# {title} — workshop fragments\n\n> **Status:** workshopping.\n\n{SECTION}\n"


def section_bounds(text: str) -> tuple[int, int] | None:
    """(start of the line after the section heading, end of the section) or None."""
    lines = text.splitlines(keepends=True)
    offset, start = 0, None
    for line in lines:
        if start is None and line.rstrip("\n") == SECTION:
            start = offset + len(line)
        elif start is not None and line.startswith("## "):
            return start, offset
        offset += len(line)
    return (start, len(text)) if start is not None else None


def entry_block(label: str, source: str, day: str, framing: str | None, material: str) -> str:
    fence = fence_for(material)
    body = material if material.endswith("\n") else material + "\n"
    parts = [f"### {label} — {source}, {day}\n\n"]
    if framing:
        parts.append(f"{framing.strip()}\n\n")
    parts.append(f"{fence}\n{body}{fence}\n")
    return "".join(parts)


def insert_entry(text: str, block: str) -> str:
    bounds = section_bounds(text)
    if bounds is None:
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        return f"{text}{sep}{SECTION}\n\n{block}"
    start, end = bounds
    section = text[start:end]
    if section.strip() == PLACEHOLDER:
        trailing = "\n" if end < len(text) else ""
        return text[:start] + "\n" + block + trailing + text[end:]
    head = section.rstrip("\n")
    rest = text[end:]
    return text[:start] + head + "\n\n" + block + ("\n" if rest else "") + rest


def add_critique(text: str, label: str, critique: str, day: str) -> str | None:
    """Append a critique paragraph to the entry headed with `label`; None if not found."""
    pattern = re.compile(rf"^### {re.escape(label)} — .*$", re.M)
    match = pattern.search(text)
    if not match:
        return None
    nxt = re.compile(r"^(### |## )", re.M).search(text, match.end())
    end = nxt.start() if nxt else len(text)
    entry = text[match.start():end].rstrip("\n")
    addition = f"\n\n**Critique ({day}):** {critique.strip()}\n"
    return text[:match.start()] + entry + addition + ("\n" if nxt else "") + text[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project_root")
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--title", help="working title; the WIP file is docs/wip-<slug>-fragments.md")
    where.add_argument("--file", help="an explicit file to capture into (e.g. a songbook entry)")
    parser.add_argument("--label", help='entry label, e.g. "Swing 4 — anchor X" (not needed with --dry-run)')
    parser.add_argument("--source", help='who wrote it: "Mac", "ChatGPT", "owner", ...')
    parser.add_argument("--framing", help="what prompted it / which iteration it came from")
    parser.add_argument("--text", help="the material (default: read stdin)")
    parser.add_argument("--critique", help="add this critique to the entry with --label instead of capturing")
    parser.add_argument("--dry-run", action="store_true",
                        help="count the material's line syllables and write nothing (check your own swing before capturing it)")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    path = wip_path(root, args.title, args.file)
    try:
        path.resolve().relative_to(root)
    except ValueError:
        print(json.dumps({"status": "refused", "reason": f"{path} is outside the project"}))
        return 1

    if not args.label and not args.dry_run:
        parser.error("--label is required unless --dry-run")
    if args.critique:
        if not path.is_file():
            print(json.dumps({"status": "refused", "reason": f"no file at {path}"}))
            return 1
        before = path.read_text(encoding="utf-8")
        after = add_critique(before, args.label, args.critique, args.date)
        if after is None:
            print(json.dumps({"status": "refused", "reason": f"no entry labelled '{args.label}' in {path.name}"}))
            return 1
        path.write_text(after, encoding="utf-8")
        print(json.dumps({"status": "written", "path": str(path.relative_to(root)), "critique_added": args.label}))
        return 0

    if not args.source and not args.dry_run:
        parser.error("--source is required when capturing")
    material = args.text if args.text is not None else sys.stdin.read()
    if not material.strip():
        print(json.dumps({"status": "refused", "reason": "no material to capture (empty --text and stdin)"}))
        return 2

    lines = [{"line": line.strip(), "syllables": count_line_syllables(line)}
             for line in material.splitlines() if line.strip() and not line.strip().startswith("[")]
    if args.dry_run:
        # Count only: a swing you drafted is checked against the band's line rule before it is captured.
        print(json.dumps({"status": "counted", "line_syllables": lines}))
        return 0

    created = not path.is_file()
    if created and args.file:
        print(json.dumps({"status": "refused", "reason": f"--file {args.file} does not exist"}))
        return 1
    before = new_wip(args.title) if created else path.read_text(encoding="utf-8")
    block = entry_block(args.label, args.source, args.date, args.framing, material)
    after = insert_entry(before, block)

    # Everything that was there stays (apart from a replaced placeholder), and the material lands whole.
    kept = before.replace(PLACEHOLDER, "", 1) if before.count(PLACEHOLDER) and PLACEHOLDER not in after else before
    if material not in after or any(line not in after for line in kept.splitlines() if line.strip()):
        print(json.dumps({"status": "refused", "reason": "verification failed; file left unchanged"}))
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(after, encoding="utf-8")
    print(json.dumps({
        "status": "written",
        "path": str(path.relative_to(root)),
        "created": created,
        "entry": f"{args.label} — {args.source}, {args.date}",
        "chars": len(material),
        # Per sung line, so a critique or a counter-swing measures line length the same way.
        "line_syllables": lines,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
