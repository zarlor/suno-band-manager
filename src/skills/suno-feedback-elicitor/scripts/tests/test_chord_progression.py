#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for chord_progression.py.

The exit-code contract goes through `uv run`, so librosa is provisioned from the
script's PEP 723 header: a missing or unreadable file is exit 1 with a reason
(never a traceback), and a track with too few beats says so. Chord matching is
pure numpy and runs in-process.
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

SCRIPT = str(Path(__file__).parent.parent / "chord_progression.py")
UV = shutil.which("uv")
TIMEOUT = 600

spec = importlib.util.spec_from_file_location("chord_progression", SCRIPT)
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)


def run_uv(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT)


def chroma(*notes):
    """A chroma vector with equal energy on the named pitch classes."""
    v = np.zeros(12)
    for note in notes:
        v[cp.PITCH_CLASSES.index(note)] = 1.0
    return v


@unittest.skipIf(UV is None, "uv not available to provision librosa deps")
class ChordProgressionExitTest(unittest.TestCase):
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
        bad = self.tmp_path / "Broken.mp3"
        bad.write_bytes(b"not audio at all")
        proc = run_uv([str(bad), "--tempo-source", "librosa"])
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn("Traceback", proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual((out["script"], out["status"]), ("chord-progression", "fail"))

    def test_too_few_beats_is_said_not_reported_as_zero_measures(self):
        silent = write_wav(self.tmp_path / "Silent.wav", np.zeros(22050))
        proc = run_uv([str(silent), "--tempo-source", "librosa"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        metrics = json.loads(proc.stdout)["metrics"]
        self.assertEqual(metrics["measures"], [])
        self.assertEqual(metrics["note"], "Too few beats for measure analysis")

    def test_a_track_with_measures_carries_no_note_and_text_honours_the_output_file(self):
        wav = write_wav(self.tmp_path / "Take.wav", click_triad(12.0))
        proc = run_uv([str(wav), "--tempo-source", "librosa"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        metrics = json.loads(proc.stdout)["metrics"]
        self.assertGreater(metrics["total_measures_analyzed"], 0)
        self.assertNotIn("note", metrics)
        self.assertEqual({m["chord"] for m in metrics["measures"]}, {"Am"})
        target = self.tmp_path / "reports" / "chords.txt"
        proc = run_uv([str(wav), "--tempo-source", "librosa", "--format", "text", "-o", str(target)])
        self.assertEqual((proc.returncode, proc.stdout), (0, ""), proc.stderr)
        self.assertIn("CHORD CHANGE SUMMARY", target.read_text(encoding="utf-8"))


class MatchChordTest(unittest.TestCase):
    def setUp(self):
        self.templates = cp._build_chord_templates()

    def test_minor_major_and_power_chords_are_told_apart(self):
        self.assertEqual(cp.match_chord(chroma("A", "C", "E"), self.templates)[0], "Am")
        self.assertEqual(cp.match_chord(chroma("A", "C#", "E"), self.templates)[0], "A")
        self.assertEqual(cp.match_chord(chroma("A", "E"), self.templates)[0], "A5")
        self.assertEqual(cp.match_chord(chroma("C", "E", "G"), self.templates)[0], "C")
        self.assertEqual(cp.match_chord(chroma("B", "D", "F#"), self.templates)[0], "Bm")  # wraps past B

    def test_a_perfect_match_scores_one(self):
        chord, score = cp.match_chord(self.templates["Em"], self.templates)
        self.assertEqual(chord, "Em")
        self.assertAlmostEqual(score, 1.0)

    def test_silence_is_named_not_matched(self):
        self.assertEqual(cp.match_chord(np.zeros(12), self.templates), ("silence", 0.0))


if __name__ == "__main__":
    unittest.main()
