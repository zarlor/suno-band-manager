#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Update one song's entry in the sanctum's `memory/work/current.md`, in place.

`current.md` is a standing file: one bullet per thread in progress, each opening
`- **<song title>**`. A checkpoint changes the bullet for the song it is about and
leaves every other byte as it was, so a brief or an open thread for another song is
never dropped by a rewrite of the whole file. Dated event lines don't belong here
(they go to the session log), so the entry text may not open with a date.

  - replaces the bullet whose bold title matches --song (case-insensitive), with its
    indented continuation lines, by `- **<song>** <text>`;
  - appends that bullet when the song has none yet (creating the file with a
    `# Current Work` heading when it doesn't exist);
  - --remove drops the song's bullet (the thread is done or parked elsewhere).

Usage:
    update-current.py <project-root> --song "Low Tide Ledger" --text "(Tidewater Rail) — verse 2 swing 3 captured; next: owner's pick."
    update-current.py <project-root> --song "Low Tide Ledger" < entry.txt
    update-current.py <project-root> --song "Low Tide Ledger" --remove

Prints JSON. Exit 0 written, 1 refused (with a reason), 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REL_PATH = Path("_bmad") / "memory" / "suno-agent-band-manager" / "memory" / "work" / "current.md"
HEADING = "# Current Work"
DATED = re.compile(r"^\s*(?:\*\*)?\[?\d{4}-\d{2}-\d{2}")


def entry_span(lines: list[str], song: str) -> tuple[int, int] | None:
    """[start, end) of the song's bullet and its indented continuation lines."""
    opener = re.compile(r"^- \*\*" + re.escape(song.strip()) + r"\*\*", re.IGNORECASE)
    for i, line in enumerate(lines):
        if opener.match(line):
            end = i + 1
            while end < len(lines) and lines[end].startswith((" ", "\t")) and lines[end].strip():
                end += 1
            return i, end
    return None


def update(text: str, song: str, entry: str | None) -> tuple[str, str]:
    """The new file text and the action taken (replaced, added, removed, absent)."""
    lines = text.splitlines(keepends=True)
    span = entry_span(lines, song)
    new = None if entry is None else f"- **{song.strip()}** {entry.strip()}\n"
    if span:
        start, end = span
        replacement = [] if new is None else [new]
        return "".join(lines[:start] + replacement + lines[end:]), ("removed" if new is None else "replaced")
    if new is None:
        return text, "absent"
    if not text.strip():
        return f"{HEADING}\n\n{new}", "added"
    sep = "" if text.endswith("\n") else "\n"
    return text + sep + new, "added"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project_root")
    parser.add_argument("--song", required=True, help="the song's title, as bolded in its bullet")
    parser.add_argument("--text", help="the entry after the title (else stdin)")
    parser.add_argument("--remove", action="store_true", help="drop the song's bullet")
    args = parser.parse_args()

    root = Path(args.project_root)
    if not (root / "_bmad").is_dir():
        print(json.dumps({"status": "error", "reason": f"no _bmad/ under {root}"}))
        return 2
    path = root / REL_PATH
    entry = None
    if not args.remove:
        entry = args.text if args.text is not None else sys.stdin.read()
        entry = " ".join(entry.split())
        if not entry:
            print(json.dumps({"status": "error", "reason": "empty entry: give --text or stdin"}))
            return 2
        if DATED.match(entry):
            print(json.dumps({"status": "refused", "path": str(path),
                              "reason": "current.md is standing state: say where the song is, not a dated event (that goes to the session log)"}))
            return 1

    before = path.read_text(encoding="utf-8") if path.exists() else ""
    after, action = update(before, args.song, entry)
    if action != "absent":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after, encoding="utf-8")
    print(json.dumps({"status": "ok", "path": str(path), "action": action, "song": args.song.strip()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
