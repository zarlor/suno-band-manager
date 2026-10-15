#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Run every test suite in the module with unittest and print one line per suite.

Suites: src/_shared/tests and src/skills/*/scripts/tests. Each runs as
`python -m unittest discover -s <tests> -t <parent>` under `uv run` with the
packages the scripts under test import, so no virtualenv is needed.

Usage: uv run dev-tools/run-tests.py [--verbose] [SUITE_SUBSTRING ...]
Exit 0 when every suite passed, 1 otherwise.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPS = ["pyyaml", "ruamel.yaml", "numpy", "librosa"]


def suites() -> list[Path]:
    found = [ROOT / "src" / "_shared" / "tests"]
    found += sorted((ROOT / "src" / "skills").glob("*/scripts/tests"))
    return [p for p in found if p.is_dir()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("only", nargs="*", help="run only suites whose path contains one of these")
    parser.add_argument("--verbose", action="store_true", help="print each suite's full output")
    args = parser.parse_args()
    cmd_deps = [arg for dep in DEPS for arg in ("--with", dep)]
    failed, total = 0, 0
    for tests in suites():
        rel = tests.relative_to(ROOT)
        if args.only and not any(s in str(rel) for s in args.only):
            continue
        cmd = ["uv", "run", "-q", *cmd_deps, "python", "-m", "unittest", "discover",
               "-s", str(tests), "-t", str(tests.parent)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=tests.parent)
        out = proc.stdout + proc.stderr
        ran = re.search(r"Ran (\d+) tests?", out)
        count = int(ran.group(1)) if ran else 0
        total += count
        status = "ok" if proc.returncode == 0 else "FAILED"
        failed += proc.returncode != 0
        print(f"{status:6} {count:5} tests  {rel}")
        if args.verbose or proc.returncode != 0:
            print(out.rstrip())
    print(f"{'ok' if not failed else 'FAILED':6} {total:5} tests  total")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
