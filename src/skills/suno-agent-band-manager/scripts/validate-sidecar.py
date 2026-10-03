#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate the Mac sanctum against songbook + band-profile ground truth.

Reads every songbook entry and band profile, derives the ground-truth catalog
state, and compares it against the derived-section claims in the v2 sanctum's
MEMORY.md. Reports drift as structured findings. Exits 0 on clean, 1 on drift
(CI-friendly).

(In the pre-v2 layout the derived Recently Published / Catalog Status sections
lived in `index.md`; the v2 sanctum carries them in the curated `MEMORY.md`.
INDEX.md in the v2 sanctum is a thin map and carries no derived claims, so the
catalog cross-checks read MEMORY.md.)

Cross-platform: pure Python stdlib + PyYAML (already a module dependency).

Usage:
    uv run scripts/validate-sidecar.py [project_root]
    uv run scripts/validate-sidecar.py --format json
    uv run scripts/validate-sidecar.py --warn-only  # exit 0 even with findings
    uv run scripts/validate-sidecar.py --sanctum-dir PATH  # test a staging copy
    uv run scripts/validate-sidecar.py --since 2026-10-01  # + untracked companion files

Checks performed:
    1. Songbook internal consistency — frontmatter status/date vs. body status marker
    2. Audio file existence for published songs
    3. Sanctum Recently Published list (MEMORY.md) matches songbook ground truth
    4. Sanctum Catalog Status counts (MEMORY.md) match actual songbook counts
    5. Playlist YAML track set matches the band's songbook titles (both sides
       listed: tracks with no songbook entry, published songs not in the playlist)
    6. Markdown cross-references in docs/ resolve to existing files
    7. Voice-file catalog counts ("N published tracks" in a band's section or
       songbook row) match the songbook's published count for that band
    8. MEMORY.md Pending / Parked Work lists no COMPLETED WIP as active, and
       every active docs/wip-*.md is listed there
    9. Voice-file Companion Files table entries exist on disk; with --since,
       docs/ files changed since that date that the table doesn't list

Called by:
    - pack-portable.{sh,ps1} before packing (gates sync)
    - save-memory workflow after MEMORY.md writes (validates derivation)
    - Standalone by user any time for a consistency check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print(
        json.dumps(
            {
                "status": "error",
                "message": (
                    "PyYAML required. Run via `uv run` so the PEP 723 inline "
                    "dependency block installs it automatically."
                ),
            }
        )
    )
    sys.exit(2)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Song:
    path: Path
    band: str
    title: str
    frontmatter_status: str | None
    frontmatter_date: str | None
    body_status: str | None  # "LOCKED", "PUBLISHED", "WIP", or None
    body_date: str | None
    body_description: str | None
    audio_references: list[str] = field(default_factory=list)
    # Optional `published:` frontmatter date. Entries that keep `date:` as the
    # day work started record the publish day here; when present it is the
    # date the body's "Published YYYY-MM-DD" marker must agree with.
    frontmatter_published: str | None = None
    # Optional `source_wip:` frontmatter — the docs/wip-*.md file the song was
    # developed from, recorded at publish. scan-wip-status.py correlates on it.
    source_wip: str | None = None
    # Optional `short_title:` — the display name a playlist may use instead.
    short_title: str | None = None

    @property
    def is_published(self) -> bool:
        """Single source of truth: requires frontmatter + body to agree on published."""
        frontmatter_published = self.frontmatter_status == "published"
        body_published = self.body_status in ("LOCKED", "PUBLISHED")
        return frontmatter_published and body_published


@dataclass
class Finding:
    category: str  # songbook_drift | audio_missing | index_drift | playlist_drift | cross_reference_missing | voice_catalog_drift | pending_drift | companion_missing | companion_untracked
    severity: str  # "error" | "warning"
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "category": self.category,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
STATUS_MARKER_RE = re.compile(
    r"\*\*Status:\s*(LOCKED|PUBLISHED|WIP)"
    r"(?:\s*[—-]\s*(?:v\d+\s+)?Published\s+(\d{4}-\d{2}-\d{2}))?"
    r"(?:\s*\((\d{4}-\d{2}-\d{2})\))?"
    r"\.?\s*(.*?)\*\*",
    re.DOTALL,
)
AUDIO_REF_RE = re.compile(r"`(docs/audio/[^`]+\.(?:mp3|wav|flac|m4a))`")

# Default sanctum location (preserved bespoke divergence: double-underscore parent,
# fixed dir name). The derived catalog sections live in MEMORY.md in the v2 sanctum.
DEFAULT_SANCTUM_REL = ("_bmad", "_memory", "band-manager-sidecar")
MEMORY_FILENAME = "MEMORY.md"


def resolve_sanctum_dir(project_root: Path, sanctum_dir: str | None) -> Path:
    """Resolve the sanctum directory, honoring a --sanctum-dir override.

    Default is the real bespoke sanctum under the project root. The override
    exists so the memory scripts can be tested against a staging copy without
    touching live data.
    """
    if sanctum_dir:
        return Path(sanctum_dir).resolve()
    return project_root.joinpath(*DEFAULT_SANCTUM_REL)


def parse_song(path: Path, project_root: Path) -> tuple[Song | None, str | None]:
    """Parse a songbook markdown file.

    Returns a (song, error) pair:
      - (Song, None)       when parsing succeeds
      - (None, None)       when the file has no frontmatter (likely not a song)
      - (None, error_msg)  when YAML frontmatter fails to parse
    """
    text = path.read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        return None, None

    try:
        frontmatter = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError as exc:
        return None, f"YAML frontmatter parse error: {exc}"

    body = text[fm_match.end() :]

    # Body status marker: walk matches and pick the last one (body markers
    # appear after Generation Log notes that may reference earlier WIP states).
    body_status = body_date = body_description = None
    for m in STATUS_MARKER_RE.finditer(body):
        body_status = m.group(1)
        body_date = m.group(2) or m.group(3)
        body_description = (m.group(4) or "").strip()

    audio_refs = AUDIO_REF_RE.findall(body)

    band = frontmatter.get("band_profile", "")
    title = frontmatter.get("title", path.stem)

    return (
        Song(
            path=path.relative_to(project_root),
            band=band,
            title=str(title),
            frontmatter_status=frontmatter.get("status"),
            frontmatter_date=str(frontmatter.get("date")) if frontmatter.get("date") else None,
            body_status=body_status,
            body_date=body_date,
            body_description=body_description,
            audio_references=audio_refs,
            frontmatter_published=(
                str(frontmatter.get("published")) if frontmatter.get("published") else None
            ),
            short_title=(
                str(frontmatter.get("short_title")).strip() if frontmatter.get("short_title") else None
            ),
            source_wip=(
                str(frontmatter.get("source_wip")).strip() if frontmatter.get("source_wip") else None
            ),
        ),
        None,
    )


def load_all_songs(project_root: Path) -> tuple[list[Song], list[Finding]]:
    """Load every songbook entry plus any parse-failure findings.

    Songs whose YAML frontmatter fails to parse used to be silently dropped,
    which hid songs from derived sections without surfacing any error (issue #29).
    Each parse failure now becomes a songbook_drift error so sync can't pass
    while a song is invisible to the index generator.
    """
    songbook_root = project_root / "docs" / "songbook"
    if not songbook_root.is_dir():
        return [], []
    songs: list[Song] = []
    parse_findings: list[Finding] = []
    for path in sorted(songbook_root.rglob("*.md")):
        song, error = parse_song(path, project_root)
        if song is not None:
            songs.append(song)
        elif error is not None:
            parse_findings.append(
                Finding(
                    category="songbook_drift",
                    severity="error",
                    path=str(path.relative_to(project_root)),
                    message=(
                        f"{error} — song will be skipped by derived-section "
                        "generators. Fix by quoting values containing "
                        "special YAML characters (e.g. inner brackets)."
                    ),
                )
            )
    return songs, parse_findings


# ---------------------------------------------------------------------------
# Check implementations
# ---------------------------------------------------------------------------


def check_songbook_consistency(song: Song) -> list[Finding]:
    """Frontmatter and body must agree on status + date."""
    findings: list[Finding] = []
    path = str(song.path)

    frontmatter_published = song.frontmatter_status == "published"
    body_published = song.body_status in ("LOCKED", "PUBLISHED")

    if song.body_status is None and frontmatter_published:
        # Missing marker is data incompleteness, not contradiction.
        # Warning keeps pre-existing songbook gaps from blocking sync.
        findings.append(
            Finding(
                category="songbook_drift",
                severity="warning",
                path=path,
                message="frontmatter status=published but no body Status marker found",
            )
        )
    elif frontmatter_published != body_published and song.body_status is not None:
        findings.append(
            Finding(
                category="songbook_drift",
                severity="error",
                path=path,
                message=(
                    f"frontmatter status={song.frontmatter_status!r} disagrees with "
                    f"body Status: {song.body_status}"
                ),
            )
        )

    # A separate `published:` field (start date kept in `date:`) is the one the
    # body marker must match; otherwise `date:` is the publish date.
    fm_field, fm_publish_date = (
        ("published", song.frontmatter_published)
        if song.frontmatter_published
        else ("date", song.frontmatter_date)
    )
    if (
        frontmatter_published
        and body_published
        and fm_publish_date
        and song.body_date
        and fm_publish_date != song.body_date
    ):
        findings.append(
            Finding(
                category="songbook_drift",
                severity="error",
                path=path,
                message=(
                    f"frontmatter {fm_field}={fm_publish_date} disagrees with "
                    f"body Published {song.body_date}"
                ),
            )
        )

    return findings


def check_audio_exists(song: Song, project_root: Path) -> list[Finding]:
    """Every audio reference in a published song must exist on disk."""
    if not song.is_published:
        return []
    findings: list[Finding] = []
    for rel in song.audio_references:
        audio_path = project_root / rel
        if not audio_path.exists():
            findings.append(
                Finding(
                    category="audio_missing",
                    severity="warning",
                    path=str(song.path),
                    message=f"referenced audio file not found: {rel}",
                )
            )
    return findings


def check_index_recently_published(
    memory_text: str, songs: list[Song], memory_display: str
) -> list[Finding]:
    """Every song listed in Recently Published must match songbook ground truth."""
    findings: list[Finding] = []
    index_path = memory_display

    # Extract the Recently Published block (from that heading until the next ## heading)
    recent_match = re.search(
        r"^##\s+Recently Published\s*\n(.*?)(?=\n##\s)",
        memory_text,
        re.MULTILINE | re.DOTALL,
    )
    if not recent_match:
        return []

    block = recent_match.group(1)

    # Each entry looks like: - **Title** (YYYY-MM-DD, STATUS) — ...
    entry_re = re.compile(
        r"-\s+\*\*(?P<title>[^*]+?)\*\*\s*"
        r"\((?P<date>\d{4}-\d{2}-\d{2}),\s*(?P<status>[A-Za-z]+)",
    )

    for match in entry_re.finditer(block):
        title = match.group("title").strip()
        claimed_date = match.group("date")
        claimed_status = match.group("status").upper()

        # Match title allowing for minor suffix (e.g., "Harbor Lights v2" matches "Harbor Lights").
        # Multiple songs can share a title across bands (same poem, different interpretations),
        # so disambiguate by date: prefer the song whose body or frontmatter date matches
        # what the index claims.
        candidates = [
            s for s in songs if s.title == title or title.startswith(s.title)
        ]
        matched = None
        for c in candidates:
            if claimed_date in (c.body_date, c.frontmatter_published, c.frontmatter_date):
                matched = c
                break
        if matched is None and candidates:
            matched = candidates[0]
        if matched is None:
            findings.append(
                Finding(
                    category="index_drift",
                    severity="error",
                    path=index_path,
                    message=(
                        f"Recently Published lists {title!r} but no songbook entry "
                        f"has that title"
                    ),
                )
            )
            continue

        # Status must agree — index claims vs. songbook ground truth
        song_published = matched.is_published
        index_claims_published = claimed_status in ("PUBLISHED", "LOCKED")
        if song_published != index_claims_published:
            findings.append(
                Finding(
                    category="index_drift",
                    severity="error",
                    path=index_path,
                    message=(
                        f"{title!r} listed as {claimed_status} but songbook shows "
                        f"frontmatter={matched.frontmatter_status!r} "
                        f"body_marker={matched.body_status!r}"
                    ),
                )
            )

        # Date must agree with body_date (authoritative) if published
        if song_published and matched.body_date and claimed_date != matched.body_date:
            findings.append(
                Finding(
                    category="index_drift",
                    severity="error",
                    path=index_path,
                    message=(
                        f"{title!r} listed with date {claimed_date} but "
                        f"songbook Status marker says Published {matched.body_date}"
                    ),
                )
            )

    return findings


def check_index_catalog_counts(
    memory_text: str, songs: list[Song], project_root: Path, memory_display: str
) -> list[Finding]:
    """Catalog Status counts must match actual songbook + playlist ground truth."""
    findings: list[Finding] = []
    index_path = memory_display

    # Extract the Catalog Status block
    catalog_match = re.search(
        r"^##\s+Catalog Status\s*\n(.*?)(?=\n##\s)",
        memory_text,
        re.MULTILINE | re.DOTALL,
    )
    if not catalog_match:
        return findings

    block = catalog_match.group(1)

    # Check claims of the form: "**Band Name:** **N published tracks**" or "**Band:** N-track playlist"
    per_band_claims = re.finditer(
        r"\*\*(?P<band>[^:*]+):\*\*\s*"
        r"(?:\*\*)?(?P<count>\d+)[-\s](?:published\s+tracks|track\s+playlist)",
        block,
        re.IGNORECASE,
    )

    # Build ground-truth counts per band (from songbook status + playlist files)
    published_per_band: dict[str, int] = {}
    all_per_band: dict[str, int] = {}
    for song in songs:
        all_per_band[song.band] = all_per_band.get(song.band, 0) + 1
        if song.is_published:
            published_per_band[song.band] = published_per_band.get(song.band, 0) + 1

    # Band name in index → band slug mapping. Derived dynamically from
    # band profile YAMLs at runtime so this works for any project's bands,
    # not just one specific project's hardcoded list.
    band_slugs: dict[str, str] = {}
    profiles_dir = project_root / "docs" / "band-profiles"
    if profiles_dir.is_dir():
        for profile_path in sorted(profiles_dir.glob("*.yaml")):
            try:
                profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                continue
            if isinstance(profile, dict):
                display_name = (profile.get("name") or "").strip()
                if display_name:
                    band_slugs[display_name] = profile_path.stem

    for match in per_band_claims:
        band_display = match.group("band").strip()
        claimed = int(match.group("count"))
        slug = band_slugs.get(band_display)
        if slug is None:
            continue

        # Figure out whether this is a "published tracks" claim or "playlist" claim
        is_playlist_claim = "playlist" in match.group(0).lower()

        if is_playlist_claim:
            # Cross-check against the playlist YAML if it exists
            playlist_path = project_root / "docs" / f"{slug}-playlist.yaml"
            if playlist_path.exists():
                try:
                    playlist = yaml.safe_load(playlist_path.read_text(encoding="utf-8"))
                    actual_tracks = len(playlist.get("tracks", []) or [])
                    if actual_tracks != claimed:
                        findings.append(
                            Finding(
                                category="index_drift",
                                severity="warning",
                                path=index_path,
                                message=(
                                    f"{band_display!r} claimed {claimed}-track playlist "
                                    f"but {playlist_path.name} has {actual_tracks} tracks"
                                ),
                            )
                        )
                except yaml.YAMLError:
                    pass
        else:
            actual_published = published_per_band.get(slug, 0)
            if actual_published != claimed:
                findings.append(
                    Finding(
                        category="index_drift",
                        severity="error",
                        path=index_path,
                        message=(
                            f"{band_display!r} claimed {claimed} published tracks "
                            f"but songbook has {actual_published} with status=published + body marker"
                        ),
                    )
                )

    return findings


_VERSION_SUFFIX_RE = re.compile(r"\s*\((?:version\s*\d+|v\d+|reprise|encore)\)\s*$", re.IGNORECASE)


def normalize_title(title: str) -> str:
    """Comparable form of a song title: version suffix dropped, curly quotes
    straightened, whitespace collapsed, casefolded."""
    t = _VERSION_SUFFIX_RE.sub("", str(title))
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", t).strip().casefold()


def title_keys(song: Song) -> set[str]:
    """Every normalized name a song answers to: its title, each '|'-separated
    form of a stylized title ("gnoS rorriM|Mirror Song"), and short_title."""
    names = [song.title, *song.title.split("|")]
    if song.short_title:
        names.append(song.short_title)
    return {normalize_title(n) for n in names if n.strip()}


def _band_display_names(project_root: Path) -> dict[str, str]:
    """band slug -> display `name:` from docs/band-profiles/*.yaml."""
    names: dict[str, str] = {}
    profiles_dir = project_root / "docs" / "band-profiles"
    if not profiles_dir.is_dir():
        return names
    for profile_path in sorted(profiles_dir.glob("*.yaml")):
        try:
            profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError, UnicodeDecodeError):
            continue
        if isinstance(profile, dict) and str(profile.get("name") or "").strip():
            names[profile_path.stem] = str(profile["name"]).strip()
    return names


def check_playlist_songbook_parity(
    songs: list[Song], project_root: Path
) -> list[Finding]:
    """A band's playlist YAML and its songbook should name the same songs.

    Compares title sets, not counts, so a rename (same count, stale title) is
    caught. Reports both sides: playlist tracks with no songbook entry for the
    band, and published songbook entries missing from the playlist.
    """
    findings: list[Finding] = []
    playlist_dir = project_root / "docs"
    if not playlist_dir.is_dir():
        return findings

    profiles_dir = playlist_dir / "band-profiles"
    for playlist_path in sorted(playlist_dir.glob("*-playlist.yaml")):
        slug = playlist_path.name.replace("-playlist.yaml", "")
        # Only a band's own playlist has a songbook to match. A thematic or
        # cross-cutting playlist (no docs/band-profiles/{slug}.yaml) draws on a
        # band's songs under its own name and has no songbook of its own.
        if profiles_dir.is_dir() and not (profiles_dir / f"{slug}.yaml").exists():
            continue
        try:
            playlist = yaml.safe_load(playlist_path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(playlist, dict):
            continue
        # A song placed twice as versions of itself ("Song (Version 1)" and
        # "(Version 2)", an encore reprise) shares one songbook entry.
        tracks = {
            normalize_title(t.get("name", "")): str(t.get("name", ""))
            for t in (playlist.get("tracks", []) or [])
            if isinstance(t, dict) and str(t.get("name", "")).strip()
        }
        band_songs = [s for s in songs if s.band == slug]
        all_keys = set().union(*(title_keys(s) for s in band_songs)) if band_songs else set()
        rel = str(playlist_path.relative_to(project_root))

        no_entry = sorted(name for key, name in tracks.items() if key not in all_keys)
        not_placed = sorted(
            s.title for s in band_songs if s.is_published and not (title_keys(s) & tracks.keys())
        )
        if no_entry:
            findings.append(
                Finding(
                    category="playlist_drift",
                    severity="warning",
                    path=rel,
                    message=(
                        f"playlist tracks with no songbook entry for band {slug!r}: "
                        + ", ".join(repr(n) for n in no_entry)
                    ),
                )
            )
        if not_placed:
            findings.append(
                Finding(
                    category="playlist_drift",
                    severity="warning",
                    path=rel,
                    message=(
                        f"published songbook entries for band {slug!r} missing from the "
                        "playlist: " + ", ".join(repr(t) for t in not_placed)
                    ),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Voice-file parity checks (catalog counts, Companion Files table)
# ---------------------------------------------------------------------------


_PUBLISHED_COUNT_RE = re.compile(r"\*{0,2}(\d+)\*{0,2}\s+published(?:\s+tracks?)?\b", re.IGNORECASE)
_SECTION_SPLIT_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def _voice_files(project_root: Path) -> list[Path]:
    docs = project_root / "docs"
    return sorted(docs.glob("voice-context-*.md")) if docs.is_dir() else []


def _band_for_text(text: str, display_names: dict[str, str]) -> str | None:
    """The band whose display name (longest match wins) appears in `text`."""
    lowered = text.casefold()
    best: tuple[int, str] | None = None
    for slug, name in display_names.items():
        if name.casefold() in lowered and (best is None or len(name) > best[0]):
            best = (len(name), slug)
    return best[1] if best else None


def check_voice_catalog_counts(songs: list[Song], project_root: Path) -> list[Finding]:
    """'N published tracks' claims in voice files must match the songbook.

    A claim is tied to a band when it sits in a `## ...` section whose heading
    names the band, or on a line pointing at `docs/songbook/{slug}/` (the
    Companion Files row). The first claim per section or line is checked.
    """
    findings: list[Finding] = []
    display = _band_display_names(project_root)
    published: dict[str, int] = {}
    for s in songs:
        if s.is_published:
            published[s.band] = published.get(s.band, 0) + 1

    for vf in _voice_files(project_root):
        try:
            text = vf.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = str(vf.relative_to(project_root))
        claims: list[tuple[str, int, str]] = []  # (slug, claimed, where)

        # Songbook-folder rows: `docs/songbook/{slug}/` ... "N published"
        for line in text.splitlines():
            m_dir = re.search(r"docs/songbook/([\w.-]+)/", line)
            m_cnt = _PUBLISHED_COUNT_RE.search(line)
            if m_dir and m_cnt and line.lstrip().startswith("|"):
                claims.append((m_dir.group(1), int(m_cnt.group(1)), "songbook row"))

        # Band sections: heading names the band, body claims "N published tracks"
        parts = _SECTION_SPLIT_RE.split(text)
        for i in range(1, len(parts) - 1, 2):
            heading, body = parts[i], parts[i + 1]
            slug = _band_for_text(heading, display)
            if slug is None:
                continue
            body_lines = [ln for ln in body.splitlines() if not ln.lstrip().startswith("|")]
            m_cnt = _PUBLISHED_COUNT_RE.search("\n".join(body_lines))
            if m_cnt:
                claims.append((slug, int(m_cnt.group(1)), f"section {heading.strip()!r}"))

        for slug, claimed, where in claims:
            actual = published.get(slug, 0)
            if slug in display or actual:
                if claimed != actual:
                    findings.append(
                        Finding(
                            category="voice_catalog_drift",
                            severity="warning",
                            path=rel,
                            message=(
                                f"{where} claims {claimed} published for band {slug!r} "
                                f"but the songbook has {actual}"
                            ),
                        )
                    )
    return findings


_COMPANION_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|", re.MULTILINE)


def companion_table_paths(voice_text: str) -> list[str]:
    """Paths in the first column of a voice file's Companion Files table."""
    m = re.search(r"^##\s+Companion Files.*?$(.*?)(?=^##\s)", voice_text + "\n## ", re.MULTILINE | re.DOTALL)
    if not m:
        return []
    return [p.strip() for p in _COMPANION_ROW_RE.findall(m.group(1))]


def check_companion_files(project_root: Path, since: str | None = None) -> list[Finding]:
    """Companion Files table entries must exist; optionally list new docs/ files
    (changed on or after `since`, YYYY-MM-DD) that no table lists."""
    import datetime as _dt

    findings: list[Finding] = []
    listed: set[str] = set()
    for vf in _voice_files(project_root):
        try:
            text = vf.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = str(vf.relative_to(project_root))
        for ref in companion_table_paths(text):
            if any(c in ref for c in "*?{}"):
                continue
            listed.add(ref.rstrip("/"))
            if not (project_root / ref).exists():
                findings.append(
                    Finding(
                        category="companion_missing",
                        severity="warning",
                        path=rel,
                        message=f"Companion Files table lists {ref!r}, which is not on disk",
                    )
                )

    if since:
        try:
            cutoff = _dt.datetime.fromisoformat(since).timestamp()
        except ValueError:
            return findings
        docs = project_root / "docs"
        voice_names = {vf.name for vf in _voice_files(project_root)}
        for path in sorted(docs.glob("*")) if docs.is_dir() else []:
            if not path.is_file() or path.suffix not in (".md", ".yaml", ".yml"):
                continue
            if path.name.startswith("wip-") or path.name in voice_names:
                continue  # WIPs are tracked in MEMORY.md Pending / Parked Work
            rel = path.relative_to(project_root).as_posix()
            if rel in listed or path.stat().st_mtime < cutoff:
                continue
            findings.append(
                Finding(
                    category="companion_untracked",
                    severity="warning",
                    path=rel,
                    message=f"changed since {since} but not in any voice file's Companion Files table",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# MEMORY.md Pending / Parked Work vs WIP COMPLETED markers
# ---------------------------------------------------------------------------


# The canonical marker from reconcile.md "The COMPLETED WIP convention".
# scan-wip-status.py imports this so there is one marker definition.
COMPLETED_RE = re.compile(r"^##\s*STATUS:\s*COMPLETED\b.*$", re.IGNORECASE | re.MULTILINE)
_WIP_REF_RE = re.compile(r"docs/wip-[\w.-]+\.md")


def wip_marker_status(project_root: Path) -> dict[str, str]:
    """docs/wip-*.md relative path -> 'completed' | 'active'."""
    docs = project_root / "docs"
    out: dict[str, str] = {}
    for wip in sorted(docs.glob("wip-*.md")) if docs.is_dir() else []:
        try:
            text = wip.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        out[wip.relative_to(project_root).as_posix()] = (
            "completed" if COMPLETED_RE.search(text) else "active"
        )
    return out


def check_pending_vs_wip(
    memory_text: str, project_root: Path, memory_display: str
) -> list[Finding]:
    """Pending / Parked Work must not list a COMPLETED WIP as active work, and
    should list every active docs/wip-*.md. A '### Resolved ...' or
    '... historical ...' subsection is the place for completed ones."""
    m = re.search(
        r"^##\s+Pending\s*/\s*Parked Work\s*$(.*?)(?=^##\s|\Z)",
        memory_text,
        re.MULTILINE | re.DOTALL,
    )
    if not m:
        return []
    section = m.group(1)
    resolved = re.search(r"^###\s+.*(?:resolved|historical).*$", section, re.IGNORECASE | re.MULTILINE)
    active_part = section[: resolved.start()] if resolved else section
    statuses = wip_marker_status(project_root)
    findings: list[Finding] = []
    for ref in sorted(set(_WIP_REF_RE.findall(active_part))):
        if statuses.get(ref) == "completed":
            findings.append(
                Finding(
                    category="pending_drift",
                    severity="warning",
                    path=memory_display,
                    message=f"Pending / Parked Work lists {ref} as active, but it carries a COMPLETED marker",
                )
            )
    mentioned = set(_WIP_REF_RE.findall(section))
    for ref, status in statuses.items():
        if status == "active" and ref not in mentioned:
            findings.append(
                Finding(
                    category="pending_drift",
                    severity="warning",
                    path=memory_display,
                    message=f"active WIP {ref} is not listed in Pending / Parked Work",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Cross-reference check
# ---------------------------------------------------------------------------


# Inline-code reference: `path/to/file.md` or `path/to/file.md#anchor`
# We require at least one slash or dot-segment so bare `README.md` in running
# prose still matches but single-word code spans like `status` don't.
INLINE_CODE_REF_RE = re.compile(r"`([^`\s]+\.md(?:#[^`]*)?)`")

# Markdown link reference: [text](path.md) or [text](path.md#anchor)
# Negative lookbehind on ! avoids matching image syntax ![alt](...).
MARKDOWN_LINK_REF_RE = re.compile(
    r"(?<!!)\[[^\]]*\]\(([^)\s]+?\.md(?:#[^)\s]*)?)\)"
)


def _is_external_or_anchor(ref: str) -> bool:
    """Skip external URLs, mail links, and bare anchor references."""
    lowered = ref.strip().lower()
    if lowered.startswith(("http://", "https://", "mailto:", "ftp://", "//")):
        return True
    if lowered.startswith("#"):
        return True
    return False


def _strip_code_fences(text: str) -> str:
    """Remove fenced code blocks so references inside them are not checked.

    References inside inline backticks (single backtick spans) are still checked,
    since those are the canonical form for pointing at a file in prose. But
    multi-line ``` fences often contain examples, templates, or diffs that
    shouldn't be validated against the real filesystem.
    """
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


IGNORE_FILENAME = "validate-ignore.txt"
_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}


def load_ignore_globs(sanctum_dir: Path | None) -> list[str]:
    """Glob patterns (project-root-relative) whose files the cross-reference scan skips.

    Read from `{sanctum}/validate-ignore.txt`, one pattern per line, `#` comments.
    For documents another agent or process owns, whose references point outside
    this project by design.
    """
    if sanctum_dir is None:
        return []
    ignore_file = Path(sanctum_dir) / IGNORE_FILENAME
    if not ignore_file.is_file():
        return []
    return [
        line.strip()
        for line in ignore_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _project_file_index(project_root: Path) -> set[str]:
    """POSIX paths of every file in the project, for suffix-matching bare references."""
    index: set[str] = set()
    for path in project_root.rglob("*"):
        rel = path.relative_to(project_root)
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        if path.is_file():
            index.add(rel.as_posix())
    return index


def _resolves_by_suffix(ref: str, index: set[str]) -> bool:
    """A bare or partial reference (`creed.md`, `references/USAGE.md`) names a file
    that exists somewhere in the project."""
    ref = ref.lstrip("./")
    return any(p == ref or p.endswith("/" + ref) for p in index)


def check_markdown_cross_references(
    project_root: Path, sanctum_dir: Path | None = None
) -> list[Finding]:
    """Scan every markdown file under docs/ for broken cross-references.

    Catches forward-intent references (`docs/X.md` mentioned declaratively but
    never actually created) and stale references that slipped past the delete
    reconciliation protocol.

    Scope: `docs/` only — module source references (`src/skills/...`) are out
    of scope because they follow different drift semantics (tracked in git, not
    synced machine-to-machine).

    Matches:
      - Inline code: `path/to/file.md` (single backtick spans)
      - Markdown links: [text](path/to/file.md) including relative `../` paths

    Skips:
      - External URLs (http/https/mailto/ftp)
      - Anchor-only refs (#section)
      - Self-references
      - Anything inside fenced code blocks (``` ... ```)
      - Template placeholders (`docs/{band-slug}-playlist.yaml`)
      - Files matching a pattern in the sanctum's validate-ignore.txt

    Resolves a reference that names an existing file anywhere in the project by
    its tail (a bare `creed.md`, a partial `references/USAGE.md`) — prose often
    names module files that way.
    """
    import fnmatch

    findings: list[Finding] = []
    docs_root = project_root / "docs"
    if not docs_root.is_dir():
        return findings
    ignore_globs = load_ignore_globs(sanctum_dir)
    file_index: set[str] | None = None

    for md_path in sorted(docs_root.rglob("*.md")):
        rel_path = md_path.relative_to(project_root).as_posix()
        if any(fnmatch.fnmatch(rel_path, pattern) for pattern in ignore_globs):
            continue
        try:
            text = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        scannable = _strip_code_fences(text)
        rel_referrer = str(md_path.relative_to(project_root))
        seen: set[str] = set()

        for pattern in (INLINE_CODE_REF_RE, MARKDOWN_LINK_REF_RE):
            for match in pattern.finditer(scannable):
                raw_ref = match.group(1).strip()
                if _is_external_or_anchor(raw_ref):
                    continue

                # Strip URL-style anchor suffix for file existence check
                ref_path_part = raw_ref.split("#", 1)[0]
                if not ref_path_part:
                    continue

                # Deduplicate per-file so one broken reference reported once
                if ref_path_part in seen:
                    continue
                seen.add(ref_path_part)

                # Absolute-ish refs (starting with /) are machine paths — skip.
                if ref_path_part.startswith("/"):
                    continue

                # Glob/wildcard patterns (e.g. `per-candidate/*.md`) describe
                # a directory of files, not a single target — skip them. So do
                # template placeholders like `docs/wip-{slug}.md`.
                if any(c in ref_path_part for c in "*?[{}"):
                    continue

                # References can be either parent-relative (`../foo.md`) or
                # project-root-relative (`docs/foo.md` written from inside
                # `docs/` — the user convention in this codebase). Try both
                # anchors; if either target exists, the reference is valid.
                project_abs = project_root.resolve()
                parent_resolved = (md_path.parent / ref_path_part).resolve()
                root_resolved = (project_root / ref_path_part).resolve()
                referrer_abs = md_path.resolve()

                # Self-reference check against either resolution
                if parent_resolved == referrer_abs or root_resolved == referrer_abs:
                    continue

                # Does either candidate exist under the project root?
                candidates = []
                for cand in (parent_resolved, root_resolved):
                    try:
                        cand.relative_to(project_abs)
                    except ValueError:
                        continue
                    candidates.append(cand)

                if not candidates:
                    # Both candidates escape the project root — out of scope
                    continue

                if any(c.exists() for c in candidates):
                    continue

                if file_index is None:
                    file_index = _project_file_index(project_root)
                if _resolves_by_suffix(ref_path_part, file_index):
                    continue

                # Neither exists — report using the more informative target
                # (prefer project-root-relative when the reference looked like
                # one, else the parent-relative form).
                display_target = candidates[-1] if len(candidates) > 1 else candidates[0]
                try:
                    target_display = str(display_target.relative_to(project_abs))
                except ValueError:
                    target_display = str(display_target)
                findings.append(
                    Finding(
                        category="cross_reference_missing",
                        severity="warning",
                        path=rel_referrer,
                        message=(
                            f"reference to {raw_ref!r} → target not found: "
                            f"{target_display}"
                        ),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_checks(
    project_root: Path, sanctum_dir: str | None = None, since: str | None = None
) -> tuple[list[Finding], dict[str, int]]:
    songs, parse_findings = load_all_songs(project_root)

    findings: list[Finding] = list(parse_findings)
    for song in songs:
        findings.extend(check_songbook_consistency(song))
        findings.extend(check_audio_exists(song, project_root))

    sanctum = resolve_sanctum_dir(project_root, sanctum_dir)
    memory_path = sanctum / MEMORY_FILENAME
    try:
        memory_display = str(memory_path.relative_to(project_root))
    except ValueError:
        memory_display = str(memory_path)
    if memory_path.exists():
        memory_text = memory_path.read_text(encoding="utf-8")
        findings.extend(
            check_index_recently_published(memory_text, songs, memory_display)
        )
        findings.extend(
            check_index_catalog_counts(
                memory_text, songs, project_root, memory_display
            )
        )
        findings.extend(check_pending_vs_wip(memory_text, project_root, memory_display))

    findings.extend(check_playlist_songbook_parity(songs, project_root))
    findings.extend(check_voice_catalog_counts(songs, project_root))
    findings.extend(check_companion_files(project_root, since))
    findings.extend(check_markdown_cross_references(project_root, resolve_sanctum_dir(project_root, sanctum_dir)))

    stats = {
        "songs_scanned": len(songs),
        "songs_published": sum(1 for s in songs if s.is_published),
        "findings_total": len(findings),
        "findings_error": sum(1 for f in findings if f.severity == "error"),
        "findings_warning": sum(1 for f in findings if f.severity == "warning"),
    }
    return findings, stats


def format_text(findings: list[Finding], stats: dict[str, int]) -> str:
    lines = [
        "Sidecar Validation Report",
        "=" * 25,
        f"Songs scanned: {stats['songs_scanned']} "
        f"({stats['songs_published']} published)",
        f"Findings: {stats['findings_total']} "
        f"({stats['findings_error']} errors, {stats['findings_warning']} warnings)",
        "",
    ]
    if not findings:
        lines.append("PASS — no drift detected.")
        return "\n".join(lines)

    # Group by category for readable output
    by_category: dict[str, list[Finding]] = {}
    for f in findings:
        by_category.setdefault(f.category, []).append(f)

    for category, items in sorted(by_category.items()):
        lines.append(f"[{category.upper()}]")
        for f in items:
            lines.append(f"  ({f.severity}) {f.path}")
            lines.append(f"      {f.message}")
        lines.append("")

    if stats["findings_error"] > 0:
        lines.append(
            f"FAIL — {stats['findings_error']} error(s) block sidecar sync."
        )
    else:
        lines.append(
            f"PASS (with {stats['findings_warning']} warning(s)) — no blocking errors."
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Mac sanctum (MEMORY.md) against songbook ground truth."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit 0 even when errors are found (for advisory runs)",
    )
    parser.add_argument(
        "--sanctum-dir",
        default=None,
        help=(
            "Override the sanctum directory (default: "
            "<project_root>/_bmad/_memory/band-manager-sidecar). Use to test "
            "against a staging copy without touching live data."
        ),
    )
    parser.add_argument(
        "--since",
        default=None,
        metavar="YYYY-MM-DD",
        help=(
            "Also list top-level docs/ files changed on or after this date that "
            "no voice file's Companion Files table lists (e.g. the last save date)"
        ),
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(f"ERROR: project root not found: {project_root}", file=sys.stderr)
        return 2

    findings, stats = run_checks(project_root, args.sanctum_dir, args.since)

    if args.format == "json":
        payload: dict[str, Any] = {
            "status": "pass" if stats["findings_error"] == 0 else "fail",
            "stats": stats,
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(findings, stats))

    if args.warn_only:
        return 0
    return 0 if stats["findings_error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
