#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for tempo_detail.py.

The exit-code contract and one real run go through `uv run`, so librosa is
provisioned from the script's PEP 723 header: a missing or unreadable file is
exit 1 with a reason (never a traceback), and the text report honours -o. The
window and tempo-event maths is pure numpy and runs in-process.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_synth import click_triad, write_wav  # noqa: E402

SCRIPT = str(Path(__file__).parent.parent / "tempo_detail.py")
UV = shutil.which("uv")
TIMEOUT = 600

spec = importlib.util.spec_from_file_location("tempo_detail", SCRIPT)
td = importlib.util.module_from_spec(spec)
spec.loader.exec_module(td)


def run_uv(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT)


def beats_at(bpm, start, seconds):
    return start + np.arange(int(round(seconds * bpm / 60.0))) * 60.0 / bpm


@unittest.skipIf(UV is None, "uv not available to provision librosa deps")
class TempoDetailExitTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def test_missing_file_exits_1_with_a_reason(self):
        proc = run_uv(["/nonexistent-track-xyz.mp3"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Audio file not found", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "fail")

    def test_unreadable_audio_is_a_json_failure_not_a_traceback(self):
        for name, body in (("Broken.mp3", b"not audio at all"), ("Empty.wav", b"")):
            bad = self.tmp_path / name
            bad.write_bytes(body)
            proc = run_uv([str(bad), "--tempo-source", "librosa"])
            self.assertEqual(proc.returncode, 1, name)
            self.assertNotIn("Traceback", proc.stderr, name)
            out = json.loads(proc.stdout)
            self.assertEqual((out["script"], out["status"]), ("tempo-detail", "fail"))
            self.assertIn("Could not analyze", out["error"])

    def test_usage_error_exits_1_not_the_missing_dependency_code(self):
        proc = run_uv(["track.mp3", "--tempo-source", "metronome"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("usage:", json.loads(proc.stdout)["error"])

    def test_text_format_is_written_to_the_output_file(self):
        wav = write_wav(self.tmp_path / "Take.wav", click_triad(8.0))
        target = self.tmp_path / "reports" / "tempo.txt"
        proc = run_uv([str(wav), "--tempo-source", "librosa", "--format", "text", "-o", str(target)])
        self.assertEqual((proc.returncode, proc.stdout), (0, ""), proc.stderr)
        report = target.read_text(encoding="utf-8")
        self.assertIn("Overall BPM:", report)
        self.assertIn("--- Beat Regularity ---", report)

    def test_unwritable_output_is_a_json_failure(self):
        wav = write_wav(self.tmp_path / "Take.wav", click_triad(4.0))
        blocker = self.tmp_path / "blocker"
        blocker.write_text("a file, not a folder", encoding="utf-8")
        proc = run_uv([str(wav), "--tempo-source", "librosa", "-o", str(blocker / "tempo.json")])
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("Cannot write", json.loads(proc.stdout)["error"])


class TempoWindowsTest(unittest.TestCase):
    def test_one_stray_beat_does_not_read_as_a_tempo_change(self):
        """Beat This! beats: window medians, so a single extra detection changes nothing."""
        beats = np.sort(np.append(beats_at(120.0, 0.0, 30.0), 7.3))  # one stray beat between two real ones
        local = 60.0 / np.diff(beats)
        rows = td.window_stats(beats, local, 30.0, robust=True)
        self.assertEqual([r["stability"] for r in rows], ["steady", "steady"])
        self.assertEqual([r["median_bpm"] for r in rows], [120.0, 120.0])
        self.assertEqual([(r["time_start"], r["time_end"]) for r in rows], [(0, 15), (15, 30.0)])
        self.assertEqual(td.find_tempo_events(beats, local, rows, robust=True), [])

    def test_the_same_stray_beat_is_an_event_without_the_robust_reading(self):
        """librosa beats: mean and beat-to-beat jumps, so the stray beat shows (this is why robust exists)."""
        beats = np.sort(np.append(beats_at(120.0, 0.0, 30.0), 7.3))
        local = 60.0 / np.diff(beats)
        rows = td.window_stats(beats, local, 30.0, robust=False)
        self.assertIn("avg_bpm", rows[0])
        self.assertEqual(rows[0]["stability"], "tempo_change")
        self.assertTrue(td.find_tempo_events(beats, local, rows, robust=False))

    def test_a_real_tempo_change_is_one_event_at_its_window(self):
        beats = np.concatenate([beats_at(120.0, 0.0, 60.0), beats_at(90.0, 60.0, 60.0)])
        local = 60.0 / np.diff(beats)
        rows = td.window_stats(beats, local, 120.0, robust=True)
        events = td.find_tempo_events(beats, local, rows, robust=True)
        self.assertEqual(events, [{"time": 60, "from_bpm": 120.0, "to_bpm": 90.0, "delta": 30.0}])


if __name__ == "__main__":
    unittest.main()
