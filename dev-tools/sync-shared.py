#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Copy the canonical src/skills/_shared/*.py helpers into every skill that vendors them.

BMad installers copy each skill folder on its own, so a skill can't import from a
sibling folder at install time. Each skill that needs the helpers carries a copy in
scripts/_shared/; src/skills/_shared/ is the single place to edit them. Run this after
editing a helper; src/skills/_shared/tests/test-vendored-copies.py fails on drift.

Usage: uv run dev-tools/sync-shared.py [--check]
"""

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "src" / "skills" / "_shared"


def vendored_dirs():
    return sorted(p for p in (ROOT / "src" / "skills").glob("suno-*/scripts/_shared") if p.is_dir())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift without copying; exit 1 if any")
    args = parser.parse_args()
    drift = []
    for dest in vendored_dirs():
        for src in sorted(SHARED.glob("*.py")):
            target = dest / src.name
            if not target.is_file() or target.read_bytes() != src.read_bytes():
                drift.append(str(target.relative_to(ROOT)))
                if not args.check:
                    shutil.copy2(src, target)
    verb = "drifted" if args.check else "updated"
    for path in drift:
        print(f"{verb}: {path}")
    if not drift:
        print("all vendored _shared copies match")
    return 1 if (args.check and drift) else 0


if __name__ == "__main__":
    sys.exit(main())
