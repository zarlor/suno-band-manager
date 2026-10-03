#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Resolve the band-profile, docs and songbook folders from module config.

Imported by this skill's scripts (not run on its own). Resolution order for
each folder:

  profiles dir  --profiles-dir flag > suno.band_profiles_folder in
                {project-root}/_bmad/config.yaml > {project-root}/docs/band-profiles
  docs dir      --docs-dir flag > parent of the resolved profiles dir
                (holds {slug}-playlist.yaml, the sequencer's module-wide contract)
  songbook dir  --songbook-dir flag > suno.songbook_folder > {docs dir}/songbook

Stdlib only: the config read is a narrow parse of the `suno:` section's flat
`key: value` lines, so scripts without a YAML dependency can use it too.
"""

from __future__ import annotations

from pathlib import Path

CONFIG_REL = Path("_bmad") / "config.yaml"


def read_module_config(project_root: Path | str, section: str = "suno") -> dict:
    """Return the flat `key: value` pairs of one top-level section of
    {project-root}/_bmad/config.yaml, with `{project-root}` substituted.
    Missing file or section returns {}."""
    root = Path(project_root)
    path = root / CONFIG_REL
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    out: dict = {}
    inside = False
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            inside = line.split("#", 1)[0].strip() == f"{section}:"
            continue
        if not inside or ":" not in line:
            continue
        key, _, value = line.strip().partition(":")
        value = value.strip()
        quote = value[:1]
        if quote in ("'", '"') and quote in value[1:]:
            value = value[1:value.index(quote, 1)]
        elif " #" in value:
            value = value.split(" #", 1)[0].strip()
        out[key.strip()] = value.replace("{project-root}", str(root))
    return out


def resolve_dirs(project_root: Path | str = ".", profiles_dir=None,
                 docs_dir=None, songbook_dir=None) -> dict:
    """Resolve profiles/docs/songbook folders. Flags win, then config, then defaults."""
    root = Path(project_root)
    cfg = read_module_config(root)
    profiles = Path(profiles_dir) if profiles_dir else (
        Path(cfg["band_profiles_folder"]) if cfg.get("band_profiles_folder")
        else root / "docs" / "band-profiles")
    docs = Path(docs_dir) if docs_dir else profiles.parent
    songbook = Path(songbook_dir) if songbook_dir else (
        Path(cfg["songbook_folder"]) if cfg.get("songbook_folder") else docs / "songbook")
    return {"profiles_dir": profiles, "docs_dir": docs, "songbook_dir": songbook}
