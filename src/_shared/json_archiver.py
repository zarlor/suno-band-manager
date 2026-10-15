#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""JSON archive writer: persist full analysis output per song / playlist.

Audio analysis scripts produce rich JSON output that's typically used
once and discarded (it goes to stdout, gets parsed for the immediate
question, then the next session has to re-run the whole analysis to ask
a different question of the same audio).

This helper writes the full JSON output to a canonical archive path so
the data is preserved indefinitely. Future sessions can read the archive
directly instead of re-running the script.

Archive layout:

    docs/audio-analysis/
      songs/[<band-slug>/]<song-slug>.json  (per-song scripts: audio-deep-analysis; band
                                       sub-folder when the audio lives in docs/audio/<band-slug>/)
      playlists/<album-slug>.json      (playlist-sequencing-data per album)
      catalog/<YYYY-MM-DD>.json        (batch-full-analysis snapshots, dated)

The archive is the durable raw-data layer; the companion `.md` files
(see companion_writer.py) are the human-readable summaries derived from
the same data.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


ARCHIVE_ROOT = "docs/audio-analysis"


def _slugify(name: str) -> str:
    """Lowercase, drop apostrophes (so "Rider's Hymn" → "riders-hymn"), replace
    remaining non-alphanumeric with hyphens, collapse repeats."""
    s = name.lower()
    s = s.replace("'", "").replace("’", "")  # drop straight + curly apostrophes
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"


def archive_path(category: str, identifier: str, project_root: str = ".") -> str:
    """Resolve the canonical archive path for a category + identifier.

    Args:
        category: One of "songs", "playlists", "catalog".
        identifier: Song name, album name, or date string (e.g., "2026-04-29").
            May carry a band sub-folder as "band-slug/song-name"; each segment
            is slugified independently and the folder becomes a sub-directory.
        project_root: Repo root (default cwd).

    Returns:
        Absolute or repo-relative path to the .json archive file.
    """
    if category == "catalog" and identifier == "":
        # Default to today's date for catalog snapshots
        identifier = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    parts = [_slugify(p) for p in identifier.split("/") if p.strip()] or [_slugify(identifier)]
    *dirs, slug = parts
    return os.path.join(project_root, ARCHIVE_ROOT, category, *dirs, f"{slug}.json")


def input_archive_identifier(input_path: str, suffix: str) -> tuple:
    """(category, identifier) for archiving a script run over a file or a directory.

    A directory run archives to catalog/<YYYY-MM-DD>-<suffix>. A single-file run
    archives to songs/, keeping the band folder when the file sits in the
    per-band layout (docs/audio/{band-slug}/Song.mp3 -> songs/{band-slug}/song-<suffix>).
    """
    p = Path(input_path)
    if p.is_dir():
        return "catalog", datetime.now(timezone.utc).strftime("%Y-%m-%d") + f"-{suffix}"
    stem = f"{p.stem}-{suffix}"
    if p.parent.parent.name == "audio":
        return "songs", f"{p.parent.name}/{stem}"
    return "songs", stem


def write_archive(target_path: str, data: dict, indent: int = 2) -> dict:
    """Write `data` as JSON to `target_path`, creating parent dirs as needed.

    Returns a dict with status, path, bytes_written.
    """
    parent = Path(target_path).parent
    parent.mkdir(parents=True, exist_ok=True)

    body = json.dumps(data, indent=indent)
    with open(target_path, "w") as f:
        f.write(body)
        if not body.endswith("\n"):
            f.write("\n")

    return {
        "status": "archived",
        "path": target_path,
        "bytes_written": len(body) + 1,
    }


def resolve_archive_arg(
    category: str,
    identifier: str,
    arg_value: Optional[str],
    project_root: str = ".",
) -> Optional[str]:
    """Resolve --archive arg value into an actual path.

    `arg_value` semantics (matches argparse `nargs="?", const=""`):
        None       -> archive mode not requested
        ""         -> use canonical archive path (archive_path(category, identifier))
        "<path>"   -> use the user-supplied path verbatim
    """
    if arg_value is None:
        return None
    if arg_value == "":
        return archive_path(category, identifier, project_root)
    return arg_value
