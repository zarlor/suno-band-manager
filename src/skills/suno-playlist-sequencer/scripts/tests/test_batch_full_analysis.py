#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Smoke test for batch-full-analysis.py.

The catalog-wide deeper-analysis layer of the suno-playlist-sequencer workflow
(extracted from suno-feedback-elicitor; see dev-docs/decision-logs/suno-playlist-sequencer.md). This
minimal smoke test pins the exit-code contract — a missing audio dir yields a
non-zero exit, not a crash. Invoked via `uv run` to provision librosa; skips
without uv.
"""

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "batch-full-analysis.py")
UV = shutil.which("uv")
TIMEOUT = 600


def run_uv(args: list[str]) -> int:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT).returncode


def _result(name, bpm, **extra):
    return {"file": f"{name}.mp3", "duration": 200.0, "bpm": bpm, "bpm_stability": "steady", "bpm_range": (bpm, bpm),
            "tempo_source": "librosa", "key": "A minor", "key_conf": 0.8, "dynamic_character": "MODERATE",
            "energy_min": 20, "energy_max": 60, "energy_range": 40, "energy_shifts": [], "energy_profile": [20, 60],
            "spectral_low": 30, "spectral_mid": 50, "spectral_high": 20, "sections": [], **extra}


@unittest.skipIf(UV is None, "uv not available to provision librosa deps")
class TestBatchFullAnalysis(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def test_missing_dir_exits_nonzero(self):
        self.assertNotEqual(run_uv(["--audio-dir", "/nonexistent-audio-dir-xyz"]), 0)

    def test_find_mp3s_recurses_and_labels_band_folders(self):
        spec = importlib.util.spec_from_file_location("batch_full_analysis", SCRIPT)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        (self.tmp_path / "band-a").mkdir()
        (self.tmp_path / ".hidden").mkdir()
        for rel in ("band-a/Song.mp3", "Loose.mp3", ".hidden/Skip.mp3", "notes.txt"):
            (self.tmp_path / rel).write_bytes(b"x")
        found = m.find_mp3s(str(self.tmp_path))
        self.assertEqual([m.rel_label(p, str(self.tmp_path)) for p in found], ["Loose.mp3", "band-a/Song.mp3"])

    def test_slow_prior_reading_in_json_and_summary_table(self):
        import json
        spec = importlib.util.spec_from_file_location("batch_full_analysis_fmt", SCRIPT)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        slow = _result("Slow", 117.5, bpm_librosa_slow_prior=60.1, librosa_prior_relation="double")
        plain = _result("Plain", 96.0)
        tracks = json.loads(m.format_json([slow, plain]))["tracks"]
        self.assertEqual(tracks[0]["bpm"], 117.5)
        self.assertEqual(tracks[0]["bpm_librosa_slow_prior"], 60.1)
        self.assertEqual(tracks[0]["librosa_prior_relation"], "double")
        self.assertNotIn("librosa_prior_relation", tracks[1])
        text = m.format_text([slow, plain])
        self.assertIn("| Slow | 3:20 | 117.5 / 60.1 (halftime?) |", text)
        self.assertIn("| Plain | 3:20 | 96.0 |", text)
        self.assertIn("start_bpm=80", text)
        self.assertNotIn("start_bpm=80", m.format_text([plain]))


if __name__ == "__main__":
    unittest.main()
