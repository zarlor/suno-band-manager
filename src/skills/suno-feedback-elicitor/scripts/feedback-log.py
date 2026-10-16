#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Locate a song's feedback iteration log, and append rounds and notes to it.

The iteration log is one markdown file per song:
  {history-dir}/{band-slug or "no-band"}/{song-slug}.md
with one heading per round:
  ## Round {n} — YYYY-MM-DD

`locate` derives the slugs (kebab-case), checks whether the log exists, and
returns the last round number and date, the next round number, and, when the
exact file is missing, near-match candidates in the band's folder (the song
title may be fuzzy). Picking among candidates is left to the caller.

`append` writes to the same path. By default it opens the next round: a
`## Round {n} — YYYY-MM-DD` heading, the prose entry, and the per-round JSON
snapshot in a fenced block with its `round` set to n. `--round last` instead
adds the text under the current round (mid-elicitation anchors as they land),
opening round 1 when the log has none. A missing log is created with a
`# {title}` heading.

Exit codes:
  0 = located / appended
  1 = invalid input (snapshot isn't a JSON object, nothing to append)
  2 = usage error or file error
"""

import argparse
import difflib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_NAME = "feedback-log"
NO_BAND = "no-band"
VERSION = "1.1.0"
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
    # A stable folder without a profile, so a later session finds the same song's log.
    band_or_session = slugify(band) if band and slugify(band) else NO_BAND
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
        "stamp": stamp,
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


def _error(message: str, code: int) -> None:
    print(json.dumps({"script": SCRIPT_NAME, "version": VERSION, "status": "error", "error": message}))
    sys.exit(code)


def append(history_dir: Path, band: str, title: str, stamp: str, date: str,
           text: str, snapshot: dict | None, which: str) -> dict:
    loc = locate(history_dir, band, title, stamp)
    path = Path(loc["path"])
    created = not path.is_file()
    existing = "" if created else path.read_text(encoding="utf-8")
    last_n = loc["last_round"]

    if which == "last" and last_n is not None:
        n, heading = last_n, None
    else:
        n = loc["next_round"]
        heading = f"## Round {n} — {date}"

    parts = []
    if created:
        parts.append(f"# {title.strip() or loc['song_slug']}\n")
    if heading:
        parts.append(heading + "\n")
    if text.strip():
        parts.append(text.strip() + "\n")
    if snapshot is not None:
        # session_id names the session the snapshot belongs to: always the stamp, so every
        # round in every log uses one format (a hand-typed id is replaced).
        snapshot = {"session_id": stamp,
                    **{k: v for k, v in snapshot.items() if k not in ("session_id", "round")}, "round": n}
        parts.append("```json\n" + json.dumps(snapshot, ensure_ascii=False) + "\n```\n")

    lead = ""
    if existing:
        lead = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    chunk = lead + "\n".join(parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(chunk)

    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "status": "ok",
        "path": str(path),
        "created": created,
        "round": n,
        "new_round": heading is not None,
        "snapshot_written": snapshot is not None,
        "bytes_appended": len(chunk.encode("utf-8")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Locate a song's feedback iteration log and its last round.",
        epilog="""
Example:
  uv run feedback-log.py locate --band "My Band" --title "Song Title" --project-root .
  uv run feedback-log.py locate --title "Song Title"     # no band profile: session-stamped folder
  uv run feedback-log.py append --band "My Band" --title "Song Title" --text "Tried: ...  Reaction: ..." \\
      --snapshot '{"feedback_type": "vague", "dimensions_adjusted": ["vocals"]}'
  uv run feedback-log.py append --band "My Band" --title "Song Title" --round last --text "Anchor: keep the bass tone"
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

    app = sub.add_parser("append", help="Append a round (or a note to the current round) to the log")
    app.add_argument("--band", default="", help="Band profile name (omit when no profile is in play)")
    app.add_argument("--title", default="", help="Song title (omit when the song is untitled)")
    app.add_argument("--project-root", default=".", help="Project root (default: current directory)")
    app.add_argument("--history-dir", help="Log root (default: {project-root}/docs/feedback-history)")
    app.add_argument("--stamp", help="Session timestamp YYYYMMDD-HHMM used when band or title is missing "
                                     "(default: now; pass the one locate returned to hit the same file)")
    app.add_argument("--date", help="Round date YYYY-MM-DD (default: today)")
    app.add_argument("--round", dest="which", choices=["next", "last"], default="next",
                     help="next: open a new round (default); last: add to the current round")
    app.add_argument("--text", default="", help="The prose entry (what was tried and the reaction, or a note)")
    app.add_argument("--stdin", action="store_true", help="Read the prose entry from stdin instead of --text")
    app.add_argument("--snapshot", help="The per-round JSON snapshot (an object; its round is set for you)")
    app.add_argument("--stdin-json", action="store_true",
                     help='Read {"text": ..., "snapshot": {...}} from stdin (a quoted heredoc), so quotes and '
                          "apostrophes in the user's words need no shell escaping")
    app.add_argument("-o", "--output", help="Write JSON to a file instead of stdout")
    args = parser.parse_args()

    if args.stamp and not re.fullmatch(r"\d{8}-\d{4}", args.stamp):
        parser.error("--stamp must look like YYYYMMDD-HHMM")
    stamp = args.stamp or datetime.now().strftime("%Y%m%d-%H%M")
    history_dir = Path(args.history_dir) if args.history_dir else Path(args.project_root) / "docs" / "feedback-history"

    try:
        if args.command == "locate":
            result = locate(history_dir, args.band, args.title, stamp)
        else:
            if args.date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
                parser.error("--date must look like YYYY-MM-DD")
            date = args.date or datetime.now().strftime("%Y-%m-%d")
            text = sys.stdin.read() if args.stdin else args.text
            snapshot = None
            if args.stdin_json:
                try:
                    payload = json.loads(sys.stdin.read())
                except json.JSONDecodeError as e:
                    _error(f"--stdin-json input is not valid JSON: {e}", 1)
                if not isinstance(payload, dict) or not isinstance(payload.get("snapshot", {}), dict):
                    _error('--stdin-json takes an object {"text": ..., "snapshot": {...}}', 1)
                text = str(payload.get("text") or "")
                snapshot = payload.get("snapshot")
            elif args.snapshot is not None:
                try:
                    snapshot = json.loads(args.snapshot)
                except json.JSONDecodeError as e:
                    _error(f"--snapshot is not valid JSON: {e}", 1)
                if not isinstance(snapshot, dict):
                    _error("--snapshot must be a JSON object", 1)
            if not text.strip() and snapshot is None:
                _error("nothing to append: give --text, --stdin or --snapshot", 1)
            result = append(history_dir, args.band, args.title, stamp, date, text, snapshot, args.which)
    except OSError as e:
        _error(str(e), 2)

    out = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        print(out)


if __name__ == "__main__":
    main()
