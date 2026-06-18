#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Exit-code contract test for analyze-audio.py.

analyze-audio.py is one of the single-song intake scripts Step 2 invokes. A full
analysis test needs real audio fixtures and a heavy librosa provision, so this
test pins the deterministic contract the skill relies on: the script returns a
meaningful non-zero exit code when its audio directory is missing or empty,
rather than crashing with a traceback. It invokes via `uv run` so the librosa
PEP 723 deps are provisioned (the directory guard fires after the dep check).
Skips when uv is unavailable.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).parent.parent / "analyze-audio.py")
UV = shutil.which("uv")
TIMEOUT = 600

pytestmark = pytest.mark.skipif(UV is None, reason="uv not available to provision librosa deps")


def run_uv(args: list[str]) -> int:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT).returncode


def test_missing_dir_exits_1():
    assert run_uv(["/nonexistent-audio-dir-xyz"]) == 1


def test_empty_dir_exits_1():
    assert run_uv([tempfile.mkdtemp()]) == 1


if __name__ == "__main__":
    if UV is None:
        print("SKIP: uv not available")
        sys.exit(0)
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS: {test.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {test.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
    sys.exit(1 if failed else 0)
