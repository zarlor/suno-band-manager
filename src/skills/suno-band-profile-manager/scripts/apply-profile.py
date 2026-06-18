#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///

"""Deterministic write owner for band profile YAML.

Headless create/edit/duplicate flows must NOT hand-serialize profile YAML —
that loses comments, reorders keys unpredictably, and is easy to get subtly
wrong. This script owns the three deterministic operations:

  --save        Write a full profile YAML (from stdin or --in) to the
                profiles directory under the derived/given slug.
  --set         Merge field overrides (dot-notation, from stdin or --set-json)
                into an existing profile and save. Reports which fields changed.
  --duplicate   Copy an existing profile to a new slug, optionally bumping the
                version field.

All operations emit structured JSON to stdout. The save/merge is a YAML
round-trip via PyYAML; nested keys use dot notation (e.g. vocal.tone).

Exit codes: 0=success, 1=fail (bad args, profile missing, etc.), 2=error.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Graceful degradation: pyyaml is the one hard dependency. If it is missing
# (e.g. claude.ai web with no uv), emit a clear JSON error so the calling LLM
# can fall back to performing the YAML write by hand rather than crashing on an
# uncaught ImportError.
try:
    import yaml
except ImportError:
    print(json.dumps({
        "script": "apply-profile",
        "status": "error",
        "error": (
            "pyyaml is not installed and could not be imported. Run this script "
            "with `uv run` (which installs it automatically), or perform the "
            "profile YAML save/merge by hand following profile-schema.md."
        ),
    }))
    sys.exit(2)


SCRIPT_NAME = "apply-profile"


def _derive_slug(band_name: str) -> str:
    """Convert a band name to a kebab-case slug (no extension)."""
    import re
    name = band_name.strip().lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def _read_yaml(path: Path):
    with open(path) as f:
        return yaml.safe_load(f)


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, default_flow_style=False)


def _set_nested(data: dict, dotted_key: str, value) -> bool:
    """Set a dot-notation key in a nested dict. Returns True if the value changed."""
    parts = dotted_key.split(".")
    cursor = data
    for part in parts[:-1]:
        nxt = cursor.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cursor[part] = nxt
        cursor = nxt
    leaf = parts[-1]
    old = cursor.get(leaf)
    cursor[leaf] = value
    return old != value


def _flatten(d: dict, prefix: str = "") -> dict:
    """Flatten a nested dict into dot-notation keys (for --set merge sources)."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


def _resolve_profiles_dir(args) -> Path:
    if args.profiles_dir:
        return Path(args.profiles_dir)
    return Path(args.project_root) / "docs" / "band-profiles"


def _load_input_data(args) -> dict:
    """Load YAML from --in file or stdin."""
    if args.input:
        raw = Path(args.input).read_text()
    else:
        raw = sys.stdin.read()
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("Input is not a YAML mapping")
    return data


def cmd_save(args) -> dict:
    data = _load_input_data(args)
    slug = args.slug or _derive_slug(str(data.get("name", "")))
    if not slug:
        return {"script": SCRIPT_NAME, "status": "fail",
                "error": "No slug provided and profile has no 'name' to derive one from."}
    profiles_dir = _resolve_profiles_dir(args)
    target = profiles_dir / f"{slug}.yaml"
    _write_yaml(target, data)
    return {
        "script": SCRIPT_NAME,
        "status": "complete",
        "operation": "save",
        "slug": slug,
        "profile_path": str(target),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def cmd_set(args) -> dict:
    profiles_dir = _resolve_profiles_dir(args)
    target = profiles_dir / f"{args.slug}.yaml"
    if not target.exists():
        return {"script": SCRIPT_NAME, "status": "fail",
                "error": f"Profile not found: {target}"}
    data = _read_yaml(target)
    if not isinstance(data, dict):
        return {"script": SCRIPT_NAME, "status": "fail",
                "error": f"Existing profile is not a YAML mapping: {target}"}

    # Overrides come from --set-json (inline) or stdin/--in (YAML mapping).
    if args.set_json:
        overrides = json.loads(args.set_json)
    else:
        overrides = _load_input_data(args)
    if not isinstance(overrides, dict):
        return {"script": SCRIPT_NAME, "status": "fail",
                "error": "Override input is not a mapping."}

    flat = _flatten(overrides)
    changed = []
    for dotted, value in flat.items():
        if _set_nested(data, dotted, value):
            changed.append(dotted)

    _write_yaml(target, data)
    return {
        "script": SCRIPT_NAME,
        "status": "complete",
        "operation": "set",
        "slug": args.slug,
        "profile_path": str(target),
        "fields_changed": changed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def cmd_duplicate(args) -> dict:
    profiles_dir = _resolve_profiles_dir(args)
    source = profiles_dir / f"{args.slug}.yaml"
    if not source.exists():
        return {"script": SCRIPT_NAME, "status": "fail",
                "error": f"Source profile not found: {source}"}
    new_slug = _derive_slug(args.duplicate)
    if not new_slug:
        return {"script": SCRIPT_NAME, "status": "fail",
                "error": f"Could not derive a slug from new name {args.duplicate!r}."}
    target = profiles_dir / f"{new_slug}.yaml"
    if target.exists() and not args.force:
        return {"script": SCRIPT_NAME, "status": "fail",
                "error": f"Target already exists: {target}. Pass --force to overwrite."}
    data = _read_yaml(source)
    if not isinstance(data, dict):
        return {"script": SCRIPT_NAME, "status": "fail",
                "error": f"Source profile is not a YAML mapping: {source}"}
    # Update the display name to the new slug's title-case unless caller keeps it.
    if args.bump_version:
        data["version"] = (data.get("version") or 1) + 1
    _write_yaml(target, data)
    return {
        "script": SCRIPT_NAME,
        "status": "complete",
        "operation": "duplicate",
        "source": str(source),
        "slug": new_slug,
        "profile_path": str(target),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic save/field-merge/duplicate owner for band profile YAML.",
        epilog="Exit codes: 0=success, 1=fail, 2=error",
    )
    parser.add_argument("slug", nargs="?",
                        help="Band slug (kebab-case, no extension). Required for --set and --duplicate; "
                             "optional for --save (derived from profile 'name' if omitted).")
    parser.add_argument("--save", action="store_true",
                        help="Save a full profile YAML (from stdin or --in).")
    parser.add_argument("--set", dest="do_set", action="store_true",
                        help="Merge field overrides into an existing profile and save.")
    parser.add_argument("--set-json", metavar="JSON",
                        help="Inline JSON object of field overrides for --set (alternative to stdin).")
    parser.add_argument("--duplicate", metavar="NEW_NAME",
                        help="Duplicate the profile at <slug> to a new name/slug.")
    parser.add_argument("--bump-version", action="store_true",
                        help="Increment the version field on --duplicate.")
    parser.add_argument("--in", dest="input", metavar="PATH",
                        help="Read input YAML from a file instead of stdin.")
    parser.add_argument("--project-root", default=".",
                        help="Project root (default: current directory).")
    parser.add_argument("--profiles-dir",
                        help="Override the profiles directory (default: {project-root}/docs/band-profiles).")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite an existing target on --duplicate.")
    parser.add_argument("-o", "--output", help="Write JSON result to a file instead of stdout.")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostics to stderr.")
    args = parser.parse_args()

    selected = [bool(args.save), bool(args.do_set), bool(args.duplicate)]
    if sum(selected) != 1:
        parser.error("Exactly one of --save, --set, or --duplicate is required.")

    try:
        if args.save:
            result = cmd_save(args)
        elif args.do_set:
            if not args.slug:
                parser.error("--set requires a <slug> positional argument.")
            result = cmd_set(args)
        else:  # duplicate
            if not args.slug:
                parser.error("--duplicate requires a <slug> positional argument.")
            result = cmd_duplicate(args)
    except (ValueError, yaml.YAMLError, json.JSONDecodeError, OSError) as e:
        result = {"script": SCRIPT_NAME, "status": "error", "error": str(e)}

    output = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output)
        if args.verbose:
            print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)

    status = result.get("status")
    if status == "complete":
        sys.exit(0)
    if status == "fail":
        sys.exit(1)
    sys.exit(2)


if __name__ == "__main__":
    main()
