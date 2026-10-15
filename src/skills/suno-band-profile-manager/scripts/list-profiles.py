#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///

"""List the band profiles in the profiles folder, or find one by name or slug.

Scans {profiles}/*.yaml (drafts/ and archive/ are subfolders, so skipped) and
returns a JSON summary. A file that can't be read or isn't a profile mapping
is reported under `skipped` with its reason, and the status turns `warning`;
nothing is dropped silently.

--check NAME resolves a band name or slug to one profile, the same way every
time: an exact slug or filename first, then the slug derived from NAME
(profile_paths.derive_slug), then profiles whose `name` field derives to that
slug. One hit -> `exists: true` with its `slug`; several -> `ambiguous: true`
with the `matches`; none -> `exists: false` with any near `suggestions`.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print(json.dumps({
        "script": "list-profiles",
        "status": "error",
        "error": "pyyaml is not installed. Run this script with `uv run`, which installs it.",
    }))
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_paths import derive_slug, resolve_dirs  # noqa: E402

SCRIPT_NAME = "list-profiles"
VERSION = "2.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _profile_files(profiles_dir: Path) -> list[Path]:
    return sorted(profiles_dir.glob("*.yaml")) + sorted(profiles_dir.glob("*.yml"))


def _read(path: Path):
    """(mapping, None) for a readable profile, else (None, reason)."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError, UnicodeDecodeError) as e:
        return None, f"unreadable: {e}"
    if not isinstance(data, dict):
        return None, "not a YAML mapping (no profile fields)"
    return data, None


def _summary(path: Path, data: dict) -> dict:
    writer_voice = data.get("writer_voice")
    return {
        "file": path.name,
        "slug": path.stem,
        "name": data.get("name", path.stem),
        "genre": data.get("genre", "unknown"),
        "mood": data.get("mood", ""),
        "model_preference": data.get("model_preference", "unknown"),
        "tier": data.get("tier", "unknown"),
        "instrumental": data.get("instrumental", False),
        "language": data.get("language", "English"),
        "creativity_default": data.get("creativity_default", "balanced"),
        "has_writer_voice": bool(isinstance(writer_voice, dict) and writer_voice.get("vocabulary")),
        "has_generation_history": bool(data.get("generation_history")),
        "version": data.get("version", 1),
    }


def _hit(path: Path, data: dict | None, matched_by: str) -> dict:
    stat = path.stat()
    name = data.get("name", path.stem) if isinstance(data, dict) else path.stem
    return {
        "file": path.name,
        "slug": path.stem,
        "path": str(path),
        "name": name,
        "matched_by": matched_by,
        "size_bytes": stat.st_size,
        "last_modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def check_profile(profiles_dir: Path, profile_name: str) -> dict:
    """Resolve a band name or slug to one profile (see the module docstring)."""
    base = {"script": SCRIPT_NAME, "version": VERSION, "timestamp": _now(),
            "status": "pass", "query": profile_name, "profiles_dir": str(profiles_dir)}
    query = profile_name.strip()
    stem = Path(query).stem if query.endswith((".yaml", ".yml")) else query
    wanted = derive_slug(stem)

    # 1. Exact slug / filename, then 2. the slug derived from the query.
    for candidate, how in ((profiles_dir / query, "filename"),
                           (profiles_dir / f"{stem}.yaml", "slug"),
                           (profiles_dir / f"{stem}.yml", "slug"),
                           (profiles_dir / f"{wanted}.yaml", "derived_slug"),
                           (profiles_dir / f"{wanted}.yml", "derived_slug")):
        if wanted and candidate.is_file() and candidate.parent == profiles_dir:
            data, _ = _read(candidate)
            return {**base, "exists": True, **_hit(candidate, data, how)}

    # 3. Profiles whose `name` derives to the same slug (a renamed band's file).
    matches, suggestions = [], []
    if profiles_dir.is_dir() and wanted:
        for path in _profile_files(profiles_dir):
            data, _ = _read(path)
            name = str(data.get("name", "")) if data else ""
            if name and derive_slug(name) == wanted:
                matches.append(_hit(path, data, "name"))
            elif wanted in path.stem or (name and wanted in derive_slug(name)):
                suggestions.append({"slug": path.stem, "name": name or path.stem})
    if len(matches) == 1:
        return {**base, "exists": True, **matches[0]}
    if matches:
        return {**base, "exists": False, "ambiguous": True, "matches": matches}
    return {**base, "exists": False, "suggestions": suggestions}


def list_profiles(profiles_dir: Path) -> dict:
    """Scan the profiles folder and return a summary of each profile."""
    base = {"script": SCRIPT_NAME, "version": VERSION, "profiles_dir": str(profiles_dir),
            "timestamp": _now()}
    if not profiles_dir.exists():
        return {**base, "status": "pass", "profiles": [], "count": 0, "skipped": [],
                "message": "No profiles directory found. No band profiles have been created yet."}

    profiles, skipped = [], []
    for path in _profile_files(profiles_dir):
        data, reason = _read(path)
        if data is None:
            skipped.append({"file": path.name, "reason": reason})
            continue
        profiles.append(_summary(path, data))

    return {**base, "status": "warning" if skipped else "pass",
            "profiles": profiles, "count": len(profiles), "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(
        description="List the band profiles, or resolve one band name or slug to its profile (--check).",
        epilog="Exit codes: 0=success, 2=error"
    )
    parser.add_argument(
        "profiles_dir",
        nargs="?",
        help="Path to band profiles directory (same as --profiles-dir)."
    )
    parser.add_argument(
        "--profiles-dir",
        dest="profiles_dir_opt",
        help=(
            "Band profiles directory (wins over the positional). Default: "
            "band_profiles_folder from BMad's config (modules.suno), else "
            "{project-root}/docs/band-profiles."
        ),
    )
    parser.add_argument("--project-root", default=".", help="Project root (default: cwd).")
    parser.add_argument("-o", "--output", help="Output file (defaults to stdout)")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostics to stderr")
    parser.add_argument(
        "--check",
        metavar="PROFILE_NAME",
        help="Resolve a band name or slug to its profile (exact slug, derived slug, then `name` fields)"
    )
    args = parser.parse_args()

    profiles_dir = resolve_dirs(
        args.project_root, profiles_dir=args.profiles_dir_opt or args.profiles_dir
    )["profiles_dir"]

    if args.verbose:
        print(f"Scanning: {profiles_dir}", file=sys.stderr)

    if args.check:
        result = check_profile(profiles_dir, args.check)
    else:
        result = list_profiles(profiles_dir)

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output)
        if args.verbose:
            print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
