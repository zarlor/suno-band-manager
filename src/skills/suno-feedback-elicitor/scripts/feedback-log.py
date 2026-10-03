#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Locate a song's feedback iteration log and report where the last round left off.

The iteration log is one markdown file per song:
  {history-dir}/{band-or-session}/{song-slug}.md
with one heading per round:
  ## Round {n} — YYYY-MM-DD

`locate` derives the slugs (kebab-case), checks whether the log exists, and
returns the last round number and date, the next round number, and, when the
exact file is missing, near-match candidates in the band's folder (the song
title may be fuzzy). Picking among candidates is left to the caller.

Exit codes:
  0 = located (whether or not the file exists)
  1 = invalid arguments
  2 = runtime error
"""

import argparse
import difflib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_NAME = "feedback-log"
VERSION = "1.0.0"
ROUND_RE = re.compile(r"^##\s+Round\s+(\d+)\b(.*)$", re.MULTILINE)
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
CANDIDATE_RATIO = 0.6


def slugify(text: str) -> str:
    """Kebab-case: lowercase, drop punctuation, spaces/underscores to hyphens."""
    name = text.strip().lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def last_round(text: str) -> tuple[int | None, str | None]:
    """The highest `## Round {n}` heading and the date on it, if any."""
    best_n, best_date = None, None
    for m in ROUND_RE.finditer(text):
        n = int(m.group(1))
        if best_n is None or n > best_n:
            date = DATE_RE.search(m.group(2))
            best_n, best_date = n, date.group(0) if date else None
    return best_n, best_date


def candidates(band_dir: Path, song_slug: str) -> list[str]:
    """Other logs in the band folder whose names are close to the song slug."""
    if not band_dir.is_dir():
        return []
    out = []
    for p in sorted(band_dir.glob("*.md")):
        stem = p.stem
        if stem == song_slug:
            continue
        if song_slug and (song_slug in stem or stem in song_slug
                          or difflib.SequenceMatcher(None, song_slug, stem).ratio() >= CANDIDATE_RATIO):
            out.append(str(p))
    return out


def locate(history_dir: Path, band: str, title: str, stamp: str) -> dict:
    band_or_session = slugify(band) if band and slugify(band) else stamp
    song_slug = slugify(title) if title and slugify(title) else stamp
    band_dir = history_dir / band_or_session
    path = band_dir / f"{song_slug}.md"
    result = {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "status": "ok",
        "path": str(path),
        "exists": path.is_file(),
        "band_or_session": band_or_session,
        "song_slug": song_slug,
        "last_round": None,
        "last_date": None,
        "next_round": 1,
        "candidates": [],
    }
    if result["exists"]:
        n, date = last_round(path.read_text(encoding="utf-8"))
        result["last_round"], result["last_date"] = n, date
        result["next_round"] = (n or 0) + 1
    else:
        result["candidates"] = candidates(band_dir, song_slug)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Locate a song's feedback iteration log and its last round.",
        epilog="""
Example:
  uv run feedback-log.py locate --band "My Band" --title "Song Title" --project-root .
  uv run feedback-log.py locate --title "Song Title"     # no band profile: session-stamped folder
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    loc = sub.add_parser("locate", help="Find the log path, whether it exists, and the last round")
    loc.add_argument("--band", default="", help="Band profile name (omit when no profile is in play)")
    loc.add_argument("--title", default="", help="Song title (omit when the song is untitled)")
    loc.add_argument("--project-root", default=".", help="Project root (default: current directory)")
    loc.add_argument("--history-dir", help="Log root (default: {project-root}/docs/feedback-history)")
    loc.add_argument("--stamp", help="Session timestamp YYYYMMDD-HHMM used when band or title is missing "
                                     "(default: now)")
    loc.add_argument("-o", "--output", help="Write JSON to a file instead of stdout")
    args = parser.parse_args()

    if args.stamp and not re.fullmatch(r"\d{8}-\d{4}", args.stamp):
        parser.error("--stamp must look like YYYYMMDD-HHMM")
    stamp = args.stamp or datetime.now().strftime("%Y%m%d-%H%M")
    history_dir = Path(args.history_dir) if args.history_dir else Path(args.project_root) / "docs" / "feedback-history"

    try:
        result = locate(history_dir, args.band, args.title, stamp)
    except OSError as e:
        print(json.dumps({"script": SCRIPT_NAME, "version": VERSION, "status": "error", "error": str(e)}))
        sys.exit(2)

    out = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        print(out)


if __name__ == "__main__":
    main()
