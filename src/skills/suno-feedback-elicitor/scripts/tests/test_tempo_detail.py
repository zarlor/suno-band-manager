#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Exit-code contract test for tempo-detail.py.

Pins the deterministic contract: a missing input file yields a non-zero exit (1)
rather than a traceback. Invoked via `uv run` so librosa is provisioned (the
file guard fires after the dep check). Skips when uv is unavailable.
"""

import shutil
import subprocess
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "tempo-detail.py")
UV = shutil.which("uv")
TIMEOUT = 600


def run_uv(args: list[str]) -> int:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT).returncode


@unittest.skipIf(UV is None, "uv not available to provision librosa deps")
class TempoDetailTest(unittest.TestCase):
    def test_missing_file_exits_1(self):
        self.assertEqual(run_uv(["/nonexistent-track-xyz.mp3"]), 1)


if __name__ == "__main__":
    unittest.main()
