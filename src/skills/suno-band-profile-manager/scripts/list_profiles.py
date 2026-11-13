#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///

"""List the band profiles in the profiles folder, or find one by name or slug.

Scans {profiles}/*.yaml (drafts/ and archive/ are subfolders, so skipped) and
returns a JSON summary. A file that can't be read or isn't a profile mapping
is reported under `skipped` with its reason, and the status turns `warning`;
nothing is dropped silently. A *.yml file is skipped the same way, with the
rename it needs: the scripts that load, edit, validate and delete a profile
read {slug}.yaml only, so listing it as a profile would promise what they
cannot do.

--check NAME resolves a band name or slug to one profile, the same way every
time: an exact slug or filename first, then the slug derived from NAME
(profile_paths.derive_slug), then profiles whose `name` field derives to that
slug or equals NAME. One hit -> `exists: true` with its `slug` (plus
`unreadable` and status `warning` when the file is there but cannot be read as
a profile); several -> `ambiguous: true` with the `matches`; none ->
`exists: false` with any near `suggestions`, and a `message` when the only
match is a .yml file.

The positional argument is a profiles folder, never a band name: a value that
is not a folder exits 2 and points at --check.
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
    return sorted(profiles_dir.glob("*.yaml"))


def _yml_reason(path: Path) -> str:
    return (f"uses the .yml extension; rename it to {path.stem}.yaml "
            "(the profile scripts read .yaml only)")


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
    wanted = derive_slug(stem)  # "" for a name with no ASCII letters or digits

    # 1. Exact slug / filename, then 2. the slug derived from the query.
    for name_part, how in ((stem if query.endswith(".yaml") else "", "filename"),
                           (stem, "slug"), (wanted, "derived_slug")):
        candidate = profiles_dir / f"{name_part}.yaml"
        if name_part and candidate.is_file() and candidate.parent == profiles_dir:
            data, reason = _read(candidate)
            hit = {**base, "exists": True, **_hit(candidate, data, how)}
            if reason:
                # The file is there, but nothing can load it: say so rather than a clean pass.
                hit.update({"status": "warning", "unreadable": reason})
            return hit

    # 3. Profiles whose `name` derives to the same slug (a renamed band's file),
    #    or equals the query (a name no slug can be derived from).
    matches, suggestions = [], []
    if profiles_dir.is_dir() and stem:
        for path in _profile_files(profiles_dir):
            data, _ = _read(path)
            name = str(data.get("name", "")) if data else ""
            if name and ((wanted and derive_slug(name) == wanted)
                         or name.strip().casefold() == stem.casefold()):
                matches.append(_hit(path, data, "name"))
            elif wanted and (wanted in path.stem or (name and wanted in derive_slug(name))):
                suggestions.append({"slug": path.stem, "name": name or path.stem})
    if len(matches) == 1:
        return {**base, "exists": True, **matches[0]}
    if matches:
        return {**base, "exists": False, "ambiguous": True, "matches": matches}
    result = {**base, "exists": False, "suggestions": suggestions}
    for name_part in (stem, wanted):
        yml = profiles_dir / f"{name_part}.yml"
        if name_part and yml.is_file() and yml.parent == profiles_dir:
            result.update({"status": "warning", "yml_file": yml.name,
                           "message": f"{yml.name} {_yml_reason(yml)}."})
            break
    return result


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
    for path in sorted(profiles_dir.glob("*.yml")):
        skipped.append({"file": path.name, "reason": _yml_reason(path)})

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
        help="Path to band profiles directory (same as --profiles-dir). Not a band name: use --check for that."
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

    if args.profiles_dir and not args.profiles_dir_opt and not Path(args.profiles_dir).is_dir():
        # A band name passed here would read as an empty folder: "no profiles yet", status pass.
        print(json.dumps({
            "script": SCRIPT_NAME, "version": VERSION, "status": "error",
            "error": (f"'{args.profiles_dir}' is not a folder. The positional argument is the "
                      f"profiles folder; to look up a band by name or slug, use "
                      f"--check \"{args.profiles_dir}\"."),
        }, indent=2))
        sys.exit(2)

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
        Path(args.output).write_text(output, encoding="utf-8")
        if args.verbose:
            print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
