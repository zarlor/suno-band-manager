#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Smoke test for batch-full-analysis.py.

The catalog-wide deeper-analysis layer of the suno-playlist-sequencer workflow
(extracted from suno-feedback-elicitor; see ../../../.decision-log.md). This
minimal smoke test pins the exit-code contract — a missing audio dir yields a
non-zero exit, not a crash. Invoked via `uv run` to provision librosa; skips
without uv.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).parent.parent / "batch-full-analysis.py")
UV = shutil.which("uv")
TIMEOUT = 600

pytestmark = pytest.mark.skipif(UV is None, reason="uv not available to provision librosa deps")


def run_uv(args: list[str]) -> int:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT).returncode


def test_missing_dir_exits_nonzero():
    assert run_uv(["--audio-dir", "/nonexistent-audio-dir-xyz"]) != 0


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
