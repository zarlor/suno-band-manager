#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Copy the canonical src/_shared/*.py helpers into each skill that imports them.

BMad installers copy each skill folder on its own, so a skill can't import from a
sibling folder at install time. Each skill whose scripts import a helper carries a
copy in scripts/_shared/: exactly the helpers its scripts import, plus the helpers
those import, plus __init__.py. src/_shared/ is the single place to edit them. Run
this after editing a helper or changing a script's imports; with --check it only
reports, and src/_shared/tests/test-vendored-copies.py fails on drift.

Usage: uv run dev-tools/sync-shared.py [--check]
"""

import argparse
import ast
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "src" / "_shared"
SKILLS = ROOT / "src" / "skills"


def shared_modules() -> dict[str, Path]:
    return {p.stem: p for p in sorted(SHARED.glob("*.py")) if p.stem != "__init__"}


def imports_of(path: Path, names: set[str]) -> set[str]:
    """The shared module names a Python file imports (`import x`, `from x import`)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found & names


def needed(skill: Path, modules: dict[str, Path]) -> set[str]:
    """Shared modules a skill's scripts import, closed over the helpers' own imports."""
    names = set(modules)
    want = set()
    for script in (skill / "scripts").glob("*.py"):
        want |= imports_of(script, names)
    queue = list(want)
    while queue:
        for dep in imports_of(modules[queue.pop()], names) - want:
            want.add(dep)
            queue.append(dep)
    return want


def plan() -> dict[Path, set[str]]:
    modules = shared_modules()
    return {skill: needed(skill, modules) for skill in sorted(SKILLS.glob("suno-*")) if (skill / "scripts").is_dir()}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift without copying; exit 1 if any")
    args = parser.parse_args()
    modules = shared_modules()
    drift = []
    for skill, want in plan().items():
        dest = skill / "scripts" / "_shared"
        files = {f"{name}.py" for name in want} | ({"__init__.py"} if want else set())
        for name in sorted(files):
            src, target = SHARED / name, dest / name
            if not target.is_file() or target.read_bytes() != src.read_bytes():
                drift.append(f"stale or missing: {target.relative_to(ROOT)}")
                if not args.check:
                    dest.mkdir(exist_ok=True)
                    shutil.copy2(src, target)
        if dest.is_dir():
            for extra in sorted(p for p in dest.glob("*.py") if p.name not in files):
                drift.append(f"not imported, removed: {extra.relative_to(ROOT)}")
                if not args.check:
                    extra.unlink()
            if not args.check and not any(dest.glob("*.py")):
                shutil.rmtree(dest)
    for line in drift:
        print(("drift — " if args.check else "") + line)
    if not drift:
        print("all vendored _shared copies match")
    return 1 if (args.check and drift) else 0


if __name__ == "__main__":
    sys.exit(main())
