#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Regenerate Mac's derived catalog files from the songbook (BMad v7 sanctum).

Writes the two files under `memory/catalog/` of the sanctum
(`{project-root}/_bmad/memory/suno-agent-band-manager/`):

    memory/catalog/recently-published.md   <!-- derived:recently-published:start/end -->
    memory/catalog/status.md               <!-- derived:catalog-status:start/end -->

Their content is derived from songbook frontmatter + body Status markers +
playlist YAMLs, and only the text between each file's marker pair is rewritten.
They are never hand-edited. A missing file is created with its heading and an
empty marker pair, then filled.

The songbook and band-profiles folders are the module's `songbook_folder` and
`band_profiles_folder` answers (`modules.suno.*`), `docs/songbook` and
`docs/band-profiles` by default.

A songbook entry that cannot be read (no frontmatter, a YAML error) or whose
`band_profile` names no band profile is left out of the catalog and listed in
`skipped[]`; the run then reports `regenerated_with_skips` (or
`unchanged_with_skips`) and exits 1, so a dropped song is never silent.

If a catalog file exists but has no marker pair, the script reports it and
exits non-zero without modifying it. Pass --migrate to wrap the file's existing
body (everything under its `# ` heading) with the markers, then regenerate.

Cross-platform: pure Python stdlib + PyYAML.

Usage:
    uv run {skill-root}/scripts/regenerate_index_sections.py [project_root]
    uv run {skill-root}/scripts/regenerate_index_sections.py --dry-run  # print the content only
    uv run {skill-root}/scripts/regenerate_index_sections.py --migrate  # add missing markers
    uv run {skill-root}/scripts/regenerate_index_sections.py --sanctum-dir PATH  # override sanctum
    uv run {skill-root}/scripts/regenerate_index_sections.py --format json
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "ERROR: PyYAML required. Run via `uv run` so the PEP 723 inline "
        "dependency block installs it automatically.",
        file=sys.stderr,
    )
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
import bmad_config  # noqa: E402  (vendored from src/_shared/ by dev-tools/sync-shared.py)


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
STATUS_MARKER_RE = re.compile(
    r"\*\*Status:\s*(LOCKED|PUBLISHED|WIP)"
    r"(?:\s*[—-]\s*(?:v\d+\s+)?Published\s+(\d{4}-\d{2}-\d{2}))?"
    r"(?:\s*\((\d{4}-\d{2}-\d{2})\))?"
    r"\.?\s*(.*?)\*\*",
    re.DOTALL,
)

# How many entries to include in Recently Published
RECENT_LIMIT = 7

def _load_sanctum_seed():
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("_sanctum_seed", Path(__file__).resolve().parent / "_sanctum_seed.py")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_seed = _load_sanctum_seed()

# The derived catalog files: (sanctum-relative path, marker name, heading).
CATALOG_FILES = (
    (_seed.MEMORY_SECTION_FILES["recently published"], "recently-published", "Recently Published"),
    (_seed.MEMORY_SECTION_FILES["catalog status"], "catalog-status", "Catalog Status"),
)


def resolve_sanctum_dir(project_root: Path, sanctum_dir: str | None) -> Path:
    """The v7 sanctum, or the --sanctum-dir override (a staging copy, tests)."""
    return _seed.sanctum_dir(project_root, sanctum_dir).resolve()


def new_catalog_file(heading: str, marker_name: str) -> str:
    return (
        f"# {heading}\n\n"
        f"<!-- derived:{marker_name}:start -->\n\n"
        f"<!-- derived:{marker_name}:end -->\n"
    )


@functools.lru_cache(maxsize=None)
def content_dirs(project_root: Path) -> tuple[Path, Path]:
    """(songbook folder, band-profiles folder).

    The module's `songbook_folder` and `band_profiles_folder` answers, read
    through BMad's resolver (`modules.suno.*`); `docs/songbook` and
    `docs/band-profiles` when there is no answer or no BMad config. A config
    that exists and cannot be read exits 2 with the reason. A band's playlist
    YAML sits in the folder that holds the band-profiles folder.
    """
    root = Path(project_root)
    try:
        cfg = bmad_config.module_config(root)
    except bmad_config.ConfigError as exc:
        print(f"ERROR: module config unreadable: {exc}", file=sys.stderr)
        sys.exit(2)

    def folder(key: str, default: str) -> Path:
        path = Path(cfg.get(key) or default)
        return path if path.is_absolute() else root / path

    return folder("songbook_folder", "docs/songbook"), folder("band_profiles_folder", "docs/band-profiles")


def display_path(path: Path, project_root: Path) -> str:
    """Project-root-relative display when possible, else the absolute path.

    An overridden --sanctum-dir may live outside the project root (e.g. a
    staging copy), so relative_to can fail — fall back to the absolute path.
    """
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)

# Display name lookups are derived dynamically from band profile YAMLs at
# runtime (see `band_display_map()` below) so this script works for any
# project's bands, not just one specific project's hardcoded list.


_RAW_TITLE_RE = re.compile(r"^title:[ \t]*(.+?)[ \t]*$", re.MULTILINE)


def song_title(frontmatter: dict, block: str, fallback: str) -> str:
    """The entry's title as text. An empty `title:` falls back to the file name.
    YAML reads `title: No` as a boolean and `title: 1999` as a number; the title
    is then the text as written, so every script names the song the same way."""
    title = frontmatter.get("title")
    if title is None or not str(title).strip():
        return fallback
    if isinstance(title, str):
        return title
    raw = _RAW_TITLE_RE.search(block)
    written = re.sub(r"\s+#.*$", "", raw.group(1)) if raw else ""
    return written or str(title)


def parse_song(path: Path) -> dict | None:
    """The parsed song, or None when it cannot be read (see read_song for why)."""
    return read_song(path)[0]


def read_song(path: Path) -> tuple[dict | None, str | None]:
    """(song, None) on success, (None, reason) when the entry cannot be read."""
    try:
        # utf-8-sig: an entry saved with a byte-order mark is still an entry.
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"unreadable: {exc}"
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        return None, "no YAML frontmatter (the file must open with a --- block)"
    try:
        frontmatter = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError as exc:
        # Common cause: flow-sequence values containing inner brackets
        # (e.g., transformations_applied: [... [Spoken] ...]) — use a quoted
        # string or a flat list without brackets inside items. See issue #29.
        return None, "frontmatter YAML error: " + " ".join(str(exc).split())
    if not isinstance(frontmatter, dict):
        return None, "frontmatter is not a mapping"

    body = text[fm_match.end() :]
    body_status = body_date = body_desc = None
    for m in STATUS_MARKER_RE.finditer(body):
        body_status = m.group(1)
        body_date = m.group(2) or m.group(3)
        body_desc = (m.group(4) or "").strip()

    # Truncate body_desc at the "Audio at" marker to get the short description.
    # Preserve the trailing period — the description ends on a natural sentence boundary,
    # and the caller appends " Songbook: ..." which needs the period for readability.
    if body_desc:
        audio_cut = re.search(r"\s*Audio at\b", body_desc)
        if audio_cut:
            body_desc = body_desc[: audio_cut.start()].rstrip()
        if body_desc and not body_desc.endswith((".", "!", "?")):
            body_desc += "."

    return {
        "path": path,
        "title": song_title(frontmatter, fm_match.group(1), path.stem),
        "band": str(frontmatter.get("band_profile") or ""),
        "frontmatter_status": frontmatter.get("status"),
        "frontmatter_date": str(frontmatter.get("date"))
        if frontmatter.get("date")
        else None,
        "frontmatter_published": str(frontmatter.get("published"))
        if frontmatter.get("published")
        else None,
        "body_status": body_status,
        "body_date": body_date,
        "body_desc": body_desc,
    }, None


def band_display_map(project_root: Path) -> dict[str, str]:
    """Build {slug: display_name} from band profile YAMLs.

    Falls back to a Title-Cased version of the slug when a profile is missing
    or doesn't carry a `name:` field. Generic across projects — does not
    hardcode any specific band names.
    """
    out: dict[str, str] = {}
    profiles_dir = content_dirs(project_root)[1]
    if not profiles_dir.is_dir():
        return out
    for profile_path in sorted(profiles_dir.glob("*.yaml")):
        slug = profile_path.stem
        try:
            profile = yaml.safe_load(profile_path.read_text(encoding="utf-8-sig"))
        except (yaml.YAMLError, OSError, UnicodeDecodeError):
            profile = None
        display = ""
        if isinstance(profile, dict):
            display = str(profile.get("name") or "").strip()
        if not display:
            display = " ".join(w.capitalize() for w in slug.replace("_", "-").split("-") if w)
        out[slug] = display
    return out


def known_band_slugs(project_root: Path) -> set[str]:
    """Band profile YAML filenames (without extension) define valid band slugs."""
    profiles_dir = content_dirs(project_root)[1]
    if not profiles_dir.is_dir():
        return set()
    return {p.stem for p in profiles_dir.glob("*.yaml")}


def load_all_songs(project_root: Path) -> tuple[list[dict], list[dict]]:
    """(songs, skipped). Each skipped entry is {"path", "reason"}; nothing is dropped silently."""
    songbook_root, profiles_dir = content_dirs(project_root)
    songs: list[dict] = []
    skipped: list[dict] = []
    if not songbook_root.is_dir():
        return songs, skipped
    valid_bands = known_band_slugs(project_root)
    for path in sorted(songbook_root.rglob("*.md")):
        shown = display_path(path, project_root)
        song, reason = read_song(path)
        if song is None:
            skipped.append({"path": shown, "reason": reason})
            continue
        # A band_profile that names no band profile YAML (a legacy entry, a
        # typo) stays out of the catalog, and is reported so it can be fixed.
        if valid_bands and song["band"] not in valid_bands:
            skipped.append({
                "path": shown,
                "reason": f"band_profile '{song['band']}' matches no "
                          f"{Path(display_path(profiles_dir, project_root)).as_posix()}/*.yaml",
            })
            continue
        songs.append(song)
    return songs, skipped


def is_published(song: dict) -> bool:
    return song["frontmatter_status"] == "published" and song["body_status"] in (
        "LOCKED",
        "PUBLISHED",
    )


def publish_date(song: dict) -> str:
    """Authoritative publish date: body marker wins; frontmatter `published:`
    (when the entry keeps its start date in `date:`), then `date:`, are fallbacks."""
    return song["body_date"] or song.get("frontmatter_published") or song["frontmatter_date"] or ""


def generate_recently_published(songs: list[dict], project_root: Path) -> str:
    band_display = band_display_map(project_root)
    published = [s for s in songs if is_published(s)]
    published.sort(key=publish_date, reverse=True)
    published = published[:RECENT_LIMIT]

    lines = []
    for s in published:
        title = s["title"]
        date = publish_date(s)
        band_display_name = band_display.get(s["band"], s["band"])
        desc = s["body_desc"] or f"{band_display_name}."
        path_display = Path(display_path(s["path"], project_root)).as_posix()
        lines.append(
            f"- **{title}** ({date}, PUBLISHED) — {desc} Songbook: "
            f"`{path_display}`."
        )
    return "\n".join(lines)


def generate_catalog_status(songs: list[dict], project_root: Path) -> str:
    profiles_dir = content_dirs(project_root)[1]
    band_display = band_display_map(project_root)
    # Per-band published counts
    per_band: dict[str, list[dict]] = {}
    for s in songs:
        per_band.setdefault(s["band"], []).append(s)

    lines = []
    for band_slug in sorted(per_band.keys()):
        band_display_name = band_display.get(band_slug, band_slug)
        band_songs = per_band[band_slug]
        published = [s for s in band_songs if is_published(s)]
        published.sort(key=publish_date, reverse=True)

        # Check for a playlist YAML for this band
        playlist_path = profiles_dir.parent / f"{band_slug}-playlist.yaml"
        playlist_count = None
        if playlist_path.exists():
            try:
                playlist = yaml.safe_load(playlist_path.read_text(encoding="utf-8-sig"))
                tracks = playlist.get("tracks") if isinstance(playlist, dict) else None
                if isinstance(tracks, list):
                    playlist_count = len(tracks)
            except (yaml.YAMLError, OSError, UnicodeDecodeError):
                pass

        # Line format depends on whether there's a playlist
        if playlist_count is not None and playlist_count > len(published):
            # Catalog with a full-album playlist that's longer than the published list
            lines.append(
                f"- **{band_display_name}:** {playlist_count}-track playlist "
                f"(songbook: {len(band_songs)} entries, {len(published)} with "
                f"complete LOCKED markers). See playlist YAML at "
                f"`{Path(display_path(playlist_path, project_root)).as_posix()}`."
            )
        else:
            # Catalog is the published list (no extended playlist beyond it)
            titles = ", ".join(s["title"] for s in published)
            lines.append(
                f"- **{band_display_name}:** **{len(published)} published tracks** — {titles}."
            )
    return "\n".join(lines)


def replace_section(
    text: str, marker_name: str, new_content: str
) -> tuple[str, bool]:
    """Replace content between <!-- derived:NAME:start --> and :end markers.

    Returns (new_text, replaced). If markers aren't found, returns (text, False)
    so the caller can report what to add.
    """
    pattern = re.compile(
        rf"(<!--\s*derived:{re.escape(marker_name)}:start\s*-->)(.*?)"
        rf"(<!--\s*derived:{re.escape(marker_name)}:end\s*-->)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return text, False
    replacement = f"{match.group(1)}\n\n{new_content}\n\n{match.group(3)}"
    return text[: match.start()] + replacement + text[match.end() :], True


def migrate_section(text: str, heading: str, marker_name: str) -> tuple[str, bool]:
    """Wrap an existing "## Heading" section's body with derived-section markers.

    Finds a line like "## Recently Published", locates the end of the section
    (next "## " heading at the same level, or EOF), and wraps the body content
    with <!-- derived:NAME:start --> / <!-- derived:NAME:end --> markers.

    Returns (new_text, migrated). migrated=False means the markers already
    existed or the heading wasn't found.
    """
    existing_marker = re.compile(
        rf"<!--\s*derived:{re.escape(marker_name)}:start\s*-->"
    )
    if existing_marker.search(text):
        return text, False

    heading_pattern = re.compile(rf"^{re.escape(heading)}\s*$", re.MULTILINE)
    heading_match = heading_pattern.search(text)
    if not heading_match:
        return text, False

    body_start = heading_match.end()
    next_heading = re.compile(r"^##\s+", re.MULTILINE)
    next_match = next_heading.search(text, pos=body_start)
    body_end = next_match.start() if next_match else len(text)

    body = text[body_start:body_end].strip("\n")
    wrapped = (
        f"\n\n<!-- derived:{marker_name}:start -->\n\n"
        f"{body}\n\n"
        f"<!-- derived:{marker_name}:end -->\n\n"
    )
    return text[:body_start] + wrapped + text[body_end:], True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate Mac's derived catalog files (memory/catalog/recently-published.md "
            "and memory/catalog/status.md) from the songbook."
        )
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the regenerated content without writing",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help=(
            "If a catalog file has no derived-section markers, wrap its existing "
            "body with them before regenerating."
        ),
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the run result (default: text)",
    )
    parser.add_argument(
        "--sanctum-dir",
        default=None,
        help=(
            "Override the sanctum directory (default: "
            "<project_root>/_bmad/memory/suno-agent-band-manager). Use to test "
            "against a staging copy without touching live data."
        ),
    )
    args = parser.parse_args()

    def emit(result: dict, stream=sys.stdout) -> None:
        """Print the run result as JSON or human text per --format."""
        if args.format == "json":
            print(json.dumps(result, indent=2), file=stream)
        elif result.get("message"):
            print(result["message"], file=stream)

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(f"ERROR: project root not found: {project_root}", file=sys.stderr)
        return 2

    sanctum_dir = resolve_sanctum_dir(project_root, args.sanctum_dir)
    if not sanctum_dir.is_dir():
        print(
            f"ERROR: no sanctum at {sanctum_dir}. First Breath scaffolds one; an old "
            "store converts with `uv run {skill-root}/scripts/migrate_sanctum_to_v7.py`.",
            file=sys.stderr,
        )
        return 2

    songs, skipped = load_all_songs(project_root)

    def report_skips() -> None:
        if skipped and args.format == "text":
            print(f"WARNING: {len(skipped)} songbook entr{'y' if len(skipped) == 1 else 'ies'} "
                  "left out of the catalog:", file=sys.stderr)
            for item in skipped:
                print(f"  {item['path']}: {item['reason']}", file=sys.stderr)

    content = {
        "recently-published": generate_recently_published(songs, project_root),
        "catalog-status": generate_catalog_status(songs, project_root),
    }

    if args.dry_run:
        if args.format == "json":
            emit({
                "status": "dry_run",
                "recently_published": content["recently-published"],
                "catalog_status": content["catalog-status"],
                "skipped": skipped,
            })
        else:
            print("=== Recently Published ===\n")
            print(content["recently-published"])
            print("\n=== Catalog Status ===\n")
            print(content["catalog-status"])
            report_skips()
        return 1 if skipped else 0

    # Plan every file first; write nothing unless every file can be regenerated.
    planned: list[tuple[Path, str, str, str]] = []  # (path, old, new, action)
    missing_markers: list[tuple[str, str]] = []
    for rel, marker, heading in CATALOG_FILES:
        path = sanctum_dir / rel
        if path.is_file():
            old = path.read_text(encoding="utf-8")
            action = "regenerated"
        else:
            old = ""
            action = "created"
        text = old or new_catalog_file(heading, marker)
        if args.migrate and old:
            text, migrated = migrate_section(text, f"# {heading}", marker)
            if migrated:
                action = "migrated"
        new, ok = replace_section(text, marker, content[marker])
        if not ok:
            missing_markers.append((display_path(path, project_root), marker))
            continue
        planned.append((path, old, new, action))

    if missing_markers:
        print("ERROR: catalog file(s) missing their derived-section markers:", file=sys.stderr)
        for shown, marker in missing_markers:
            print(
                f"  {shown}: <!-- derived:{marker}:start --> ... <!-- derived:{marker}:end -->",
                file=sys.stderr,
            )
        print(
            "\nRerun with --migrate to wrap each file's existing body with the "
            "markers (the file is derived; its body is replaced on regeneration).",
            file=sys.stderr,
        )
        return 1

    files = []
    for path, old, new, action in planned:
        shown = display_path(path, project_root)
        if new == old:
            files.append({"path": shown, "status": "unchanged"})
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new, encoding="utf-8")
        files.append({"path": shown, "status": action})

    changed = [f["path"] for f in files if f["status"] != "unchanged"]
    suffix = "_with_skips" if skipped else ""
    if not changed:
        emit({
            "status": "unchanged" + suffix,
            "message": "No changes needed — the catalog files are already up to date.",
            "files": files,
            "skipped": skipped,
        })
    else:
        emit({
            "status": "regenerated" + suffix,
            "message": f"Regenerated {', '.join(changed)}",
            "files": files,
            "skipped": skipped,
        })
    report_skips()
    return 1 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
