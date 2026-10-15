#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Resolve the band-profile, docs and songbook folders from module config.

Imported by this skill's scripts (not run on its own). Resolution order for
each folder:

  profiles dir  --profiles-dir flag > modules.suno.band_profiles_folder in
                BMad's config > {project-root}/docs/band-profiles
  docs dir      --docs-dir flag > parent of the resolved profiles dir
                (holds {slug}-playlist.yaml, the sequencer's module-wide contract)
  songbook dir  --songbook-dir flag > modules.suno.songbook_folder > {docs dir}/songbook

The config read goes through BMad's resolve_config.py (via `_shared/bmad_config.py`).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
import bmad_config  # noqa: E402


def read_module_config(project_root: Path | str) -> dict:
    """This module's answers from BMad's resolver, `{project-root}` filled in.
    No _bmad/ returns {}; a broken config exits 2 with the resolver's reason."""
    try:
        return bmad_config.module_config(project_root)
    except bmad_config.ConfigError as exc:
        print(f"ERROR: module config unreadable: {exc}", file=sys.stderr)
        sys.exit(2)


def under_root(root: Path, value: str) -> Path:
    """A folder answer: relative to the project root unless already absolute."""
    path = Path(value)
    return path if path.is_absolute() else root / path


def resolve_dirs(project_root: Path | str = ".", profiles_dir=None,
                 docs_dir=None, songbook_dir=None) -> dict:
    """Resolve profiles/docs/songbook folders. Flags win, then config, then defaults."""
    root = Path(project_root)
    cfg = read_module_config(root)
    profiles = Path(profiles_dir) if profiles_dir else (
        under_root(root, cfg["band_profiles_folder"]) if cfg.get("band_profiles_folder")
        else root / "docs" / "band-profiles")
    docs = Path(docs_dir) if docs_dir else profiles.parent
    songbook = Path(songbook_dir) if songbook_dir else (
        under_root(root, cfg["songbook_folder"]) if cfg.get("songbook_folder") else docs / "songbook")
    return {"profiles_dir": profiles, "docs_dir": docs, "songbook_dir": songbook}
