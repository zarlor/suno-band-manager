#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Exit-code contract test for audio-deep-analysis.py.

audio-deep-analysis.py is the single-track deep analyzer Step 2 invokes. A full
analysis needs real audio and a heavy librosa provision, so this test pins the
deterministic contract: a missing input file yields a non-zero exit (1) rather
than a traceback. Invoked via `uv run` so librosa is provisioned (the file guard
fires after the dep check). Skips when uv is unavailable.
"""

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "audio-deep-analysis.py")
UV = shutil.which("uv")
TIMEOUT = 600


def run_uv(args: list[str]) -> int:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT).returncode


@unittest.skipIf(UV is None, "uv not available to provision librosa deps")
class AudioDeepAnalysisTest(unittest.TestCase):
    def test_missing_file_exits_1(self):
        self.assertEqual(run_uv(["/nonexistent-track-xyz.mp3"]), 1)

    def test_band_folder_for_detects_per_band_layout(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        tmp_path = Path(td.name)
        spec = importlib.util.spec_from_file_location("audio_deep_analysis", SCRIPT)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        audio = tmp_path / "docs" / "audio"
        self.assertEqual(m.band_folder_for(audio / "band-a" / "Night Shift.mp3"), "band-a")
        self.assertIsNone(m.band_folder_for(audio / "Night Shift.mp3"))          # legacy flat layout
        self.assertIsNone(m.band_folder_for(tmp_path / "Downloads" / "x.mp3"))  # not an audio folder


if __name__ == "__main__":
    unittest.main()
