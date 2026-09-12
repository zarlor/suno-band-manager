#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Verify Audio Files — compare local audio files against the canonical
audio-files-manifest.yaml and report mismatches.

Companion to audio-files-manifest.py. The manifest is generated on the
canonical machine (whichever has the latest published audio) and travels
in the portable sync archive. This script runs on a non-canonical machine
after unpack to detect which audio files need to be re-downloaded from Suno.

Three failure modes are detected:
- MISSING: no local file matches the manifest entry, even under fuzzy
  filename normalization (no audio for this song at all)
- SIZE_MISMATCH: a local file matches by song identity but bytes differ
  beyond the size tolerance (likely a different gen — re-download from
  Suno if the gen matters)
- EXTRA: local file with no manifest entry under any normalization
  (orphan / abandoned gen)

Filename matching is normalization-aware (since v1.1.0): variations like
`Foo.mp3` vs `Foo-Redux.mp3` vs `Foo (NSFW).mp3`, em-dash vs ascii hyphen,
equals-sign-as-separator, repeated underscore-hyphen runs are all treated
as the same song. Band suffixes (e.g. `-Acoustic`, `-Duo`, or whatever
convention the project uses) are NOT normalized away, because they
distinguish different bands' generations of the same poem. When a
fuzzy match is used, the entry includes `filename_variant: true` and a
`local_filename` field showing the actual on-disk name.

Size matching is tolerance-aware (since v1.2.0). Suno's MP3 downloads
carry per-download ID3 metadata variance (timestamps, cover art presence,
encoded-by strings) that produces small byte differences across machines
and download events even for the SAME audio gen. Default tolerance of
1024 bytes absorbs this metadata noise so the script doesn't false-
positive identical audio as "different gen." Real gen differences are
typically tens of KB or larger. Override with `--tolerance-bytes`.

Output is JSON, structured so Mac can present a download list to the user
or auto-fix orphans on confirmation.

The audio dir is scanned recursively (since v1.3.0) to match the per-band
layout docs/audio/{band-slug}/Song.mp3. A band sub-folder is part of a
file's identity — "solitary-fire/For Now.mp3" never matches
"lennys-voice/For Now.mp3" — and only the filename part is normalized. A
legacy flat manifest (bare filenames) still verifies against a per-band
local layout by falling back to filename-only matching.

Optional --playlist-context flag enriches mismatch entries with playlist
position info so the report can be presented in playlist order rather
than alphabetical filename order.

Usage:
  # Default: read docs/audio-files-manifest.yaml, scan docs/audio/
  verify-audio-files.py PROJECT_ROOT

  # Use a custom manifest path
  verify-audio-files.py PROJECT_ROOT --manifest docs/custom-manifest.yaml

  # Use a custom audio dir
  verify-audio-files.py PROJECT_ROOT --audio-dir docs/audio

  # Enrich with playlist position from per-band playlist YAMLs
  verify-audio-files.py PROJECT_ROOT --playlist-context

Exit codes:
  0 = no mismatches detected (all files match manifest)
  1 = mismatches detected (see JSON output for details)
  2 = invalid arguments, manifest not found, or missing dependencies
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_NAME = "verify-audio-files"
SCRIPT_VERSION = "1.3.0"

DEFAULT_AUDIO_DIR = "docs/audio"
DEFAULT_MANIFEST_PATH = "docs/audio-files-manifest.yaml"
DEFAULT_SIZE_TOLERANCE_BYTES = 1024  # absorbs ID3 metadata variance from Suno re-downloads

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".opus"}


def normalize_for_match(name: str) -> str:
    """Normalize a filename for fuzzy song-identity matching.

    Strips/normalizes filename variations that don't change song identity:
    - File extension (.mp3, .wav, etc.)
    - Version qualifiers (-Redux, -v2, -alt — common Suno post-publish naming)
    - Parenthetical annotations ((NSFW), (clean), (explicit), etc.)
    - Em-dash (—) / en-dash (–) collapsed to ascii hyphen
    - Equals sign (=, occasionally used as separator in mangled Suno-default names) → hyphen
    - Repeated separator runs (-_, _-, --, __) collapsed to single hyphen
    - Whitespace + leading/trailing hyphens trimmed, lowercase

    NOT stripped (preserved as meaningful):
    - Band-suffix patterns. The band suffix distinguishes different bands'
      generations of the same poem (e.g. `Song Title.mp3` for the first band
      and `Song Title-Acoustic.mp3` for the second — these are different audio
      files of the same lyrics, not duplicates).

    The goal: recognize that filenames like `Foo.mp3`, `Foo-Redux.mp3`,
    `Foo (NSFW).mp3` all refer to the same song; while `Foo.mp3` and
    `Foo-Acoustic.mp3` are different songs by band-suffix convention.
    """
    s = name.lower()
    # Strip audio extension
    s = re.sub(r"\.(mp3|wav|flac|m4a|ogg|opus)$", "", s)
    # Strip version qualifiers (must come before separator collapse)
    s = re.sub(r"-(redux|v\d+|alt|alternate)\b", "", s)
    # Strip parentheticals (e.g., "(NSFW)", "(clean)", "(explicit)")
    s = re.sub(r"\s*\([^)]*\)\s*", " ", s)
    # Normalize unicode dashes
    s = s.replace("—", "-").replace("–", "-")
    # Equals sign as separator → hyphen
    s = s.replace("=", "-")
    # Collapse repeated separators (-_, _-, --, __) to single hyphen
    s = re.sub(r"[-_]+", "-", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    # Strip leading/trailing hyphens
    s = s.strip("-")
    return s


def display_path(path: Path, root: Path) -> str:
    """Path relative to the project root when inside it, else the absolute path
    (a --manifest outside the project must not crash the report)."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def match_key(name: str) -> str:
    """Song-identity key for a name that may carry a band sub-folder.

    The folder ("solitary-fire/For Now.mp3") is part of the identity, so two
    bands' renderings of the same title never cross-match; only the filename
    part goes through normalize_for_match().
    """
    folder, _, base = name.rpartition("/")
    key = normalize_for_match(base)
    return f"{folder.lower()}/{key}" if folder else key


def require_yaml():
    try:
        import yaml  # noqa: F401
        return yaml
    except ImportError:
        print(
            json.dumps({
                "script": SCRIPT_NAME,
                "version": SCRIPT_VERSION,
                "status": "error",
                "error": "missing-dependency",
                "message": "pyyaml is required. Run this script via 'uv run scripts/verify-audio-files.py ...' — uv reads the PEP 723 metadata block and provisions pyyaml automatically.",
            }),
            file=sys.stdout,
        )
        sys.exit(2)


def load_playlist_context(project_root: Path, yaml_module) -> dict[str, dict]:
    """Map filename -> {band, position, track_name} from per-band playlist YAMLs."""
    context = {}
    docs = project_root / "docs"
    if not docs.is_dir():
        return context
    for yaml_path in sorted(docs.glob("*-playlist.yaml")):
        try:
            data = yaml_module.safe_load(yaml_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        album = data.get("album", yaml_path.stem.replace("-playlist", ""))
        # band slug = the filename stem minus -playlist suffix
        band_slug = yaml_path.stem
        if band_slug.endswith("-playlist"):
            band_slug = band_slug[:-len("-playlist")]
        for idx, track in enumerate(data.get("tracks") or [], start=1):
            if not isinstance(track, dict):
                continue
            file = track.get("file")
            name = track.get("name")
            if not file:
                continue
            context[file] = {
                "band": album,
                "band_slug": band_slug,
                "position": idx,
                "track_name": name,
            }
    return context


def main():
    parser = argparse.ArgumentParser(description="Verify local audio files against canonical manifest")
    parser.add_argument("project_root", help="Project root directory")
    parser.add_argument(
        "--manifest",
        default=DEFAULT_MANIFEST_PATH,
        help=f"Manifest path relative to project root (default: {DEFAULT_MANIFEST_PATH})",
    )
    parser.add_argument(
        "--audio-dir",
        default=DEFAULT_AUDIO_DIR,
        help=f"Audio directory relative to project root (default: {DEFAULT_AUDIO_DIR})",
    )
    parser.add_argument(
        "--playlist-context",
        action="store_true",
        help="Enrich mismatch entries with playlist position from per-band playlist YAMLs",
    )
    parser.add_argument(
        "--tolerance-bytes",
        type=int,
        default=DEFAULT_SIZE_TOLERANCE_BYTES,
        help=(
            f"Size-difference tolerance in bytes (default: {DEFAULT_SIZE_TOLERANCE_BYTES}). "
            f"Files differing by less than this are treated as matched. Suno's per-download "
            f"ID3 metadata variance (timestamps, cover art) produces small byte differences "
            f"even for the same audio gen; this absorbs that noise. Set to 0 for strict "
            f"byte-exact matching."
        ),
    )
    args = parser.parse_args()

    yaml = require_yaml()

    project_root = Path(args.project_root).resolve()
    manifest_path = project_root / args.manifest
    audio_dir = project_root / args.audio_dir

    if not manifest_path.is_file():
        print(
            json.dumps({
                "script": SCRIPT_NAME,
                "version": SCRIPT_VERSION,
                "status": "error",
                "error": "manifest-not-found",
                "manifest_path": str(manifest_path),
                "hint": "Generate the manifest on the canonical machine first via audio-files-manifest.py, then sync.",
            })
        )
        sys.exit(2)

    if not audio_dir.is_dir():
        print(
            json.dumps({
                "script": SCRIPT_NAME,
                "version": SCRIPT_VERSION,
                "status": "error",
                "error": "audio-dir-not-found",
                "audio_dir": str(audio_dir),
            })
        )
        sys.exit(2)

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    expected = {entry["name"]: entry for entry in (manifest.get("files") or [])}

    # Walk local audio dir recursively (per-band sub-folders included). Keys are
    # POSIX paths relative to the audio dir, matching the manifest's names.
    local = {}
    for path in sorted(audio_dir.rglob("*")):
        rel = path.relative_to(audio_dir)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        if ":" in path.name:
            continue
        local[rel.as_posix()] = path.stat().st_size

    playlist_ctx = load_playlist_context(project_root, yaml) if args.playlist_context else {}

    # Augment playlist_ctx with normalized-key lookup so fuzzy-matched local
    # filenames can still find their playlist context (since the playlist YAML
    # has the canonical filename and the local file may differ).
    playlist_ctx_by_norm: dict[str, dict] = {}
    for fname, ctx in playlist_ctx.items():
        playlist_ctx_by_norm[normalize_for_match(fname)] = ctx

    # Build normalized → list of (name, size) maps for both sides. Multiple
    # entries can collide on a single normalized key when a manifest carries
    # both `Foo.mp3` and `Foo-Redux.mp3` — both legitimate gens, distinguished
    # by size.
    local_by_norm: dict[str, list[tuple[str, int]]] = {}
    # Filename-only index, used when a legacy flat manifest (bare filenames) is
    # verified against a per-band local layout.
    local_by_base: dict[str, list[tuple[str, int]]] = {}
    for name, size in local.items():
        local_by_norm.setdefault(match_key(name), []).append((name, size))
        local_by_base.setdefault(normalize_for_match(name.rpartition("/")[2]), []).append((name, size))

    missing = []
    size_mismatch = []
    extra = []
    matched = []

    # Track which local files have been claimed by a manifest entry so we don't
    # double-match and can detect orphans afterward.
    claimed_local: set[str] = set()

    def lookup_playlist_ctx(canonical_name: str, local_name: str | None) -> dict | None:
        """Find playlist context by exact name, then bare filename, then normalized.

        Playlist YAML `file:` entries are bare filenames relative to the band's
        audio_dir, so a band-folder path is also tried by its filename part.
        """
        for candidate in (canonical_name, local_name):
            if not candidate:
                continue
            if candidate in playlist_ctx:
                return playlist_ctx[candidate]
            base = candidate.rpartition("/")[2]
            if base in playlist_ctx:
                return playlist_ctx[base]
        norm = normalize_for_match(canonical_name.rpartition("/")[2])
        return playlist_ctx_by_norm.get(norm)

    for name, entry in expected.items():
        expected_size = entry.get("size_bytes")
        norm = match_key(name)
        legacy_flat = "/" not in name

        # Find a local match. Prefer exact filename match, then best size match
        # among normalized-key candidates that haven't already been claimed. A
        # bare manifest name also considers the filename-only index (legacy
        # flat manifest vs per-band local layout).
        candidates = list(local_by_norm.get(norm, []))
        if legacy_flat:
            # Same-folder candidates first, then the same filename in any band
            # folder — a root-level variant must not block the band-folder file.
            candidates += [c for c in local_by_base.get(norm, []) if c not in candidates]
        best: tuple[str, int] | None = None
        best_score: float = float("inf")
        for local_name, local_size in candidates:
            if local_name in claimed_local:
                continue
            if local_name == name or (legacy_flat and local_name.rpartition("/")[2] == name):
                # Exact name match always wins
                best = (local_name, local_size)
                best_score = -1
                break
            # Otherwise pick the closest size match
            score = abs(local_size - (expected_size or 0))
            if score < best_score:
                best = (local_name, local_size)
                best_score = score

        if best is None:
            # No local file under the canonical name OR any fuzzy variant
            item = {"name": name, "expected_size_bytes": expected_size}
            ctx = lookup_playlist_ctx(name, None)
            if ctx:
                item["playlist_context"] = ctx
            missing.append(item)
            continue

        local_name, local_size = best
        claimed_local.add(local_name)
        is_variant = local_name != name

        delta = local_size - (expected_size or 0)
        within_tolerance = abs(delta) <= args.tolerance_bytes

        if local_size == expected_size or within_tolerance:
            entry_out: dict = {"name": name}
            if is_variant:
                entry_out["filename_variant"] = True
                entry_out["local_filename"] = local_name
            if delta != 0 and within_tolerance:
                entry_out["delta_bytes"] = delta
                entry_out["within_tolerance"] = True
                entry_out["note"] = (
                    f"Local size differs by {delta:+d} bytes (within {args.tolerance_bytes}-byte "
                    f"tolerance — likely ID3 metadata variance, not a different audio gen)"
                )
            matched.append(entry_out)
        else:
            item = {
                "name": name,
                "expected_size_bytes": expected_size,
                "local_size_bytes": local_size,
                "delta_bytes": delta,
            }
            if is_variant:
                item["filename_variant"] = True
                item["local_filename"] = local_name
            ctx = lookup_playlist_ctx(name, local_name)
            if ctx:
                item["playlist_context"] = ctx
            size_mismatch.append(item)

    # Anything not claimed is an orphan
    for name, size in local.items():
        if name not in claimed_local:
            item = {"name": name, "local_size_bytes": size}
            ctx = lookup_playlist_ctx(name, name)
            if ctx:
                item["playlist_context"] = ctx
            extra.append(item)

    has_mismatches = bool(missing or size_mismatch or extra)

    result = {
        "script": SCRIPT_NAME,
        "version": SCRIPT_VERSION,
        "status": "mismatch" if has_mismatches else "ok",
        "manifest_path": display_path(manifest_path, project_root),
        "audio_dir": args.audio_dir,
        "manifest_generated_at": manifest.get("generated_at"),
        "summary": {
            "expected": len(expected),
            "local": len(local),
            "matched": len(matched),
            "matched_byte_exact": sum(1 for m in matched if isinstance(m, dict) and not m.get("within_tolerance")),
            "matched_within_tolerance": sum(1 for m in matched if isinstance(m, dict) and m.get("within_tolerance")),
            "matched_filename_variants": sum(1 for m in matched if isinstance(m, dict) and m.get("filename_variant")),
            "missing": len(missing),
            "size_mismatch": len(size_mismatch),
            "size_mismatch_filename_variants": sum(1 for m in size_mismatch if m.get("filename_variant")),
            "extra": len(extra),
            "tolerance_bytes": args.tolerance_bytes,
        },
        "missing": missing,
        "size_mismatch": size_mismatch,
        "extra": extra,
    }

    print(json.dumps(result, indent=2))
    sys.exit(1 if has_mismatches else 0)


if __name__ == "__main__":
    main()
