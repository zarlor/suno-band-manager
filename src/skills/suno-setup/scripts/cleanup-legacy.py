#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Remove leftover copies of this module's skills from _bmad/{module}/.

An earlier, pre-consolidation installer copied the module's skills into
_bmad/{module}/. Once those skills are installed in a platform skills folder
(.claude/skills/ or similar), the copies under _bmad/ are dead weight.

Scope is deliberately narrow. The script only ever removes a directory that it
can positively identify as this module's own leftover:
  - it sits at _bmad/{module}/{name}/ or _bmad/{module}/skills/{name}/,
  - it holds a SKILL.md and {name} starts with "{module}-",
  - a copy of {name} exists in at least one --skills-dir,
  - no BMad installer tracks it (_config/files-manifest.csv, skill-manifest.csv),
    and the installer manifest does not list {module} as an installed module.
Everything else is kept: _config/, core/, other modules, scripts/, _memory/,
and inside _bmad/{module}/ the config.yaml, module-help.csv and any unknown file.

--dry-run reports what would be removed and deletes nothing.

Exit codes: 0=success (including nothing to remove), 1=validation error, 2=runtime error
"""

import argparse
import csv
import json
import re
import shutil
import sys
from pathlib import Path

# Names under _bmad/ that are never a module's own folder.
PROTECTED_NAMES = frozenset({"_config", "_memory", "memory", "core", "scripts", "custom", "render", "docs"})


def parse_args():
    parser = argparse.ArgumentParser(
        description="Remove leftover copies of this module's skills from _bmad/{module}/."
    )
    parser.add_argument("--bmad-dir", required=True, help="Path to the _bmad/ directory")
    parser.add_argument("--module-code", required=True, help="Module code (e.g. 'suno')")
    parser.add_argument(
        "--skills-dir",
        action="append",
        default=[],
        help="Platform skills folder where the module's skills are installed "
        "(e.g. .claude/skills). Repeatable. A copy is removed only if the skill "
        "exists in one of these.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report what would be removed; delete nothing")
    parser.add_argument("--verbose", action="store_true", help="Print detailed progress to stderr")
    return parser.parse_args()


def reject_unresolved_paths(named_paths: list[tuple[str, str | None]]) -> None:
    """Exit with a clear error if any path argument still contains the literal
    ``{project-root}`` token. That token is meaningful only inside config
    values; filesystem path arguments must be resolved by the caller. Failing
    loudly here prevents silently operating on a junk ``{project-root}/`` directory.
    """
    for name, value in named_paths:
        if value and "{project-root}" in value:
            fail(
                f"Unresolved '{{project-root}}' token in {name} path: {value!r}. "
                "Resolve '{project-root}' to the actual project root before running "
                "this script — it is a filesystem path, not a config value."
            )


def fail(message: str, code: int = 1, **extra) -> None:
    print(json.dumps({"status": "error", "error": message, **extra}, indent=2))
    sys.exit(code)


def installer_tracked_paths(bmad_dir: Path) -> set[str]:
    """Paths (relative to _bmad/) that a BMad installer tracks in its manifests."""
    tracked: set[str] = set()
    for name in ("files-manifest.csv", "skill-manifest.csv"):
        manifest = bmad_dir / "_config" / name
        if not manifest.is_file():
            continue
        with open(manifest, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                path = (row.get("path") or "").strip().replace("\\", "/")
                if path.startswith("_bmad/"):
                    path = path[len("_bmad/"):]
                if path:
                    tracked.add(path)
    return tracked


def installer_lists_module(bmad_dir: Path, module_code: str) -> bool:
    """True when _config/manifest.yaml lists the module as installed (line scan, no yaml dep)."""
    manifest = bmad_dir / "_config" / "manifest.yaml"
    if not manifest.is_file():
        return False
    pattern = re.compile(rf"^\s*-\s*name:\s*['\"]?{re.escape(module_code)}['\"]?\s*$")
    return any(pattern.match(line) for line in manifest.read_text(encoding="utf-8").splitlines())


def find_candidates(module_dir: Path, module_code: str) -> list[Path]:
    """Skill directories under _bmad/{module}/ named {module}-* (flat or skills/ layout)."""
    candidates = []
    for parent in (module_dir, module_dir / "skills"):
        if not parent.is_dir():
            continue
        for child in sorted(parent.iterdir()):
            if child.is_dir() and not child.is_symlink() and child.name.startswith(f"{module_code}-") and (child / "SKILL.md").is_file():
                candidates.append(child)
    return candidates


def count_files(path: Path) -> int:
    return sum(1 for item in path.rglob("*") if item.is_file())


def main():
    args = parse_args()
    reject_unresolved_paths([("--bmad-dir", args.bmad_dir), *(("--skills-dir", s) for s in args.skills_dir)])

    code = args.module_code
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", code) or code in PROTECTED_NAMES:
        fail(f"Refusing module code {code!r}: cleanup only works on a module's own _bmad/{{module}}/ folder.")

    bmad_dir = Path(args.bmad_dir)
    module_dir = bmad_dir / code
    result = {
        "status": "success",
        "dry_run": args.dry_run,
        "bmad_dir": str(bmad_dir.resolve()),
        "module_dir": str(module_dir.resolve()),
        "installer_managed": (bmad_dir / "_config" / "manifest.yaml").is_file(),
        "would_remove" if args.dry_run else "removed": [],
        "files_removed_count": 0,
        "skipped_installer_managed": [],
        "unverified": [],
        "skills_dirs": [str(Path(s).resolve()) for s in args.skills_dir],
    }
    listing = result["would_remove" if args.dry_run else "removed"]

    if not module_dir.is_dir():
        result["skipped_reason"] = "module folder not found"
        print(json.dumps(result, indent=2))
        return
    if installer_lists_module(bmad_dir, code):
        result["skipped_reason"] = f"the BMad installer manages _bmad/{code}/"
        print(json.dumps(result, indent=2))
        return

    candidates = find_candidates(module_dir, code)
    existing_skills_dirs = [Path(s) for s in args.skills_dir if Path(s).is_dir()]
    if candidates and not existing_skills_dirs:
        result["skipped_reason"] = "no --skills-dir found to verify the installed skills against"
        result["unverified"] = [str(c.relative_to(bmad_dir)) for c in candidates]
        print(json.dumps(result, indent=2))
        return

    tracked = installer_tracked_paths(bmad_dir)
    to_remove: list[tuple[Path, int]] = []
    for cand in candidates:
        rel = cand.relative_to(bmad_dir).as_posix()
        if any(t == rel or t.startswith(rel + "/") for t in tracked):
            result["skipped_installer_managed"].append(rel)
            continue
        if not any((sd / cand.name / "SKILL.md").is_file() for sd in existing_skills_dirs):
            result["unverified"].append(rel)
            continue
        to_remove.append((cand, count_files(cand)))

    for cand, file_count in to_remove:
        rel = cand.relative_to(bmad_dir).as_posix()
        if not args.dry_run:
            if args.verbose:
                print(f"Removing {cand} ({file_count} files)", file=sys.stderr)
            try:
                shutil.rmtree(cand)
            except OSError as e:
                fail(f"Failed to remove {cand}: {e}", code=2, removed=listing)
        listing.append({"path": rel, "file_count": file_count})
        result["files_removed_count"] += file_count

    skills_sub = module_dir / "skills"
    if not args.dry_run and to_remove and skills_sub.is_dir() and not any(skills_sub.iterdir()):
        skills_sub.rmdir()

    if args.dry_run:
        result["would_remove_count"] = result.pop("files_removed_count")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
