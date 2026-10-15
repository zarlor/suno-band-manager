#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Scaffold a band's canonical playlist YAML, {docs}/{band-slug}-playlist.yaml.

That file is the single source of truth for the band's track order; the
suno-playlist-sequencer skill reads and reorders it. This script writes it
for a band that doesn't have one yet:

  (default)        a template with no tracks; tracks are added as songs publish.
  --from-songbook  tracks seeded from the band's published songbook entries
                   ({songbook}/{band-slug}/*.md with `status: published`), in
                   filename order, each with an empty `file:` to fill in from
                   the band's audio folder (songbook frontmatter doesn't
                   reliably carry the audio filename).

The album name is the band profile's `name` ({profiles}/{band-slug}.yaml),
else --album-name, else the slug title-cased. Every string is written as a
quoted YAML scalar, so titles with quotes, colons or backslashes stay valid.

Folders: --profiles-dir / --docs-dir / --songbook-dir, else module config,
else {project-root}/docs/... (see profile_paths.py).

Output: JSON on stdout. Exit codes: 0 = written, or already present (status
`exists`, nothing changed without --force); 1 = invalid slug or project root.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # optional: frontmatter and profile names fall back to a line parser
    yaml = None


def _q(value: str) -> str:
    """A string as a double-quoted YAML scalar (JSON's escaping is valid YAML)."""
    return json.dumps(str(value), ensure_ascii=False)


def _parse_mapping(text: str) -> dict:
    """A YAML mapping's top-level keys ({} when it isn't one). Without pyyaml,
    a line parser reads unindented `key: value` lines."""
    if yaml is not None:
        try:
            data = yaml.safe_load(text)
            return data if isinstance(data, dict) else {}
        except yaml.YAMLError:
            return {}
    data = {}
    for line in text.splitlines():
        m = re.match(r"""^([A-Za-z_][\w-]*)\s*:\s*(.*?)\s*$""", line)
        if m and m.group(1) not in data:
            val = m.group(2)
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            data[m.group(1)] = val
    return data


def _frontmatter(content: str) -> dict:
    """The leading `---` block of a Markdown file as a dict ({} when absent)."""
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    return _parse_mapping(content[3:end]) if end >= 0 else {}


def _profile_name(profiles_dir: Path, slug: str) -> str | None:
    """The band profile's `name`, when the profile exists and has one."""
    try:
        text = (profiles_dir / f"{slug}.yaml").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    name = _parse_mapping(text).get("name")
    return str(name).strip() if name is not None and str(name).strip() else None


def _band_name_from_slug(slug: str) -> str:
    """Convert kebab-case slug to a Title-Cased album name as a default.
    Users typically edit this after scaffolding."""
    parts = slug.replace("_", "-").split("-")
    return " ".join(p.capitalize() for p in parts if p)


def _read_frontmatter(md_path: Path) -> dict:
    try:
        return _frontmatter(md_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def _extract_title_from_songbook(md_path: Path) -> str | None:
    """A songbook entry's frontmatter `title`, or None."""
    title = _read_frontmatter(md_path).get("title")
    return str(title).strip() if title and str(title).strip() else None


def _is_published(md_path: Path) -> bool:
    """True when the entry's frontmatter says `status: published`."""
    return str(_read_frontmatter(md_path).get("status", "")).strip().lower() == "published"


def discover_songbook_tracks(
    project_root: Path, band_slug: str, docs_dir: Path | None = None,
    songbook_dir: Path | None = None,
) -> list[dict]:
    """Find published songbook entries for the band and return their titles.

    songbook_dir: the songbook root holding `{band_slug}/`. Defaults to
    `{docs_dir}/songbook`, and docs_dir to `{project_root}/docs`.
    """
    base_docs = docs_dir if docs_dir is not None else project_root / "docs"
    root = songbook_dir if songbook_dir is not None else base_docs / "songbook"
    band_dir = root / band_slug
    if not band_dir.is_dir():
        return []
    tracks = []
    for md_path in sorted(band_dir.glob("*.md")):
        if not _is_published(md_path):
            continue
        title = _extract_title_from_songbook(md_path)
        if title:
            # Report relative to project_root when possible; otherwise the
            # absolute path (a --docs-dir outside the project root).
            try:
                songbook_path = str(md_path.relative_to(project_root))
            except ValueError:
                songbook_path = str(md_path)
            tracks.append({"name": title, "songbook_path": songbook_path})
    return tracks


def render_playlist_yaml(
    album_name: str, tracks: list[dict], from_songbook: bool, band_slug: str | None = None
) -> str:
    """Render the playlist YAML content as a string.

    With band_slug, the YAML carries `audio_dir: "docs/audio/{band_slug}"` —
    the band's audio folder that every track's `file:` is relative to.
    """
    lines = []
    lines.append(f"# Playlist order for {' '.join(album_name.splitlines())} — authoritative source.")
    lines.append("# This file is the SINGLE source of truth for the band's track sequence.")
    lines.append("# Do NOT duplicate this list in other files (band profile YAML, ordering doc,")
    lines.append("# voice context). Those files derive from or reference this YAML.")
    lines.append("#")
    lines.append("# When a song is published, add it to this file in the same write batch as")
    lines.append("# the songbook entry. When the order changes, update this file first; the")
    lines.append("# sequencing script's per-album companion .md is auto-refreshed from this.")
    lines.append("#")
    lines.append("# Optional: a track's `felt_bpm: 72` records the tempo you hear when the measured")
    lines.append("# BPM reads half/double time; a top-level `locked_arcs:` list (each item a list of")
    lines.append('# track names, or a "A > B > C" string) keeps those runs together and in order.')
    lines.append(f"album: {_q(album_name)}")
    if band_slug:
        lines.append(f"audio_dir: {_q('docs/audio/' + band_slug)}  # this band's audio folder; each file: is relative to it")
    lines.append("tracks:")
    if not tracks:
        lines.append("  # Add tracks below as they are published. Each track needs:")
        lines.append('  #   - name: "<song title as it appears in the songbook>"')
        lines.append('  #     file: "<exact filename in the band\'s audio folder, e.g. My Song.mp3>"')
        lines.append("  # Order in this list = playlist order.")
    else:
        for t in tracks:
            lines.append(f"  - name: {_q(t['name'])}")
            if from_songbook:
                # We discovered the song from songbook but don't know the audio filename.
                # User must fill this in.
                lines.append("    file: \"\"  # TODO: set to the actual filename in the band's audio folder")
                if t.get("songbook_path"):
                    lines.append(f"    # songbook: {' '.join(str(t['songbook_path']).splitlines())}")
            else:
                lines.append('    file: ""')
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a per-band playlist YAML at docs/{band-slug}-playlist.yaml.",
    )
    parser.add_argument(
        "band_slug",
        help="The band's filename slug (kebab-case). Matches the band profile filename: docs/band-profiles/{band-slug}.yaml.",
    )
    parser.add_argument(
        "--from-songbook",
        action="store_true",
        help="Pre-populate tracks from existing songbook entries at docs/songbook/{band-slug}/.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root (default: current directory).",
    )
    parser.add_argument(
        "--profiles-dir",
        help=("Band profiles folder (default: band_profiles_folder from "
              "BMad's config (modules.suno), else {project-root}/docs/band-profiles). "
              "The playlist YAML is written to its parent folder."),
    )
    parser.add_argument(
        "--docs-dir",
        help="Folder for {slug}-playlist.yaml (default: the profiles folder's parent).",
    )
    parser.add_argument(
        "--songbook-dir",
        help=("Songbook root read by --from-songbook (default: songbook_folder from "
              "config, else {docs-dir}/songbook)."),
    )
    parser.add_argument(
        "--album-name",
        help="Album name for the YAML (default: the band profile's `name`, else the slug title-cased).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing playlist YAML if present.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(json.dumps({"status": "error", "message": f"Project root not found: {project_root}"}))
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from profile_paths import resolve_dirs
    dirs = resolve_dirs(project_root, profiles_dir=args.profiles_dir,
                        docs_dir=args.docs_dir, songbook_dir=args.songbook_dir)
    docs_dir = dirs["docs_dir"].resolve()
    songbook_dir = dirs["songbook_dir"].resolve()

    def _report_path(p: Path) -> str:
        """Path relative to project_root when possible; absolute otherwise
        (e.g. a --docs-dir pointing outside the project)."""
        try:
            return str(p.relative_to(project_root))
        except ValueError:
            return str(p)

    slug = args.band_slug.strip()
    if not re.match(r"^[a-z0-9][a-z0-9_-]*$", slug):
        print(json.dumps({
            "status": "error",
            "message": (
                f"Invalid band slug {slug!r}. Use lowercase kebab-case "
                f"(letters, digits, hyphens, underscores; must start with letter/digit)."
            ),
        }))
        sys.exit(1)

    target = docs_dir / f"{slug}-playlist.yaml"
    existed = target.exists()
    if existed and not args.force:
        print(json.dumps({
            "status": "exists",
            "message": f"Playlist YAML already exists at {target}. Use --force to overwrite.",
            "path": _report_path(target),
        }))
        sys.exit(0)

    album_name = (args.album_name or _profile_name(dirs["profiles_dir"], slug)
                  or _band_name_from_slug(slug))
    tracks: list[dict] = []
    if args.from_songbook:
        tracks = discover_songbook_tracks(project_root, slug, docs_dir=docs_dir,
                                          songbook_dir=songbook_dir)

    body = render_playlist_yaml(album_name, tracks, from_songbook=args.from_songbook, band_slug=slug)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w") as f:
        f.write(body)

    print(json.dumps({
        "status": "overwritten" if existed else "created",
        "path": _report_path(target),
        "album": album_name,
        "tracks_seeded": len(tracks),
        "from_songbook": args.from_songbook,
        "note": (
            "Audio filenames left as empty strings — fill in from the band's audio folder (docs/audio/<band-slug>/) before "
            "running the sequencing script."
        ) if tracks else (
            "Empty template written. Add tracks as you publish them."
        ),
    }))


if __name__ == "__main__":
    main()
