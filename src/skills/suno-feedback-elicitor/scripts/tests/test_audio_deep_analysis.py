#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for audio_deep_analysis.py.

The missing-file and unreadable-file contract goes through `uv run`, so librosa
is provisioned from the script's PEP 723 header. The rest runs in-process on
synthesized signals with real librosa: the energy arc and its shifts, the
windows that cover a short track and a tail, and main() itself (the per-band
archive, the text report with -o, a run from another directory).
"""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_synth import SR, click_triad, write_wav  # noqa: E402

SCRIPT = str(Path(__file__).parent.parent / "audio_deep_analysis.py")
UV = shutil.which("uv")
TIMEOUT = 600


def run_uv(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT)


def load(name="audio_deep_analysis"):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@unittest.skipIf(UV is None, "uv not available to provision librosa deps")
class AudioDeepAnalysisExitTest(unittest.TestCase):
    def test_missing_file_exits_1_with_a_reason(self):
        proc = run_uv(["/nonexistent-track-xyz.mp3"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Audio file not found", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "fail")

    def test_unreadable_audio_is_a_json_failure_and_archives_nothing(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        bad = Path(tmp.name) / "Broken.mp3"
        bad.write_bytes(b"not audio at all")
        proc = subprocess.run([UV, "run", SCRIPT, str(bad)], capture_output=True, text=True, timeout=TIMEOUT,
                              cwd=tmp.name)
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "fail")
        self.assertEqual(sorted(p.name for p in Path(tmp.name).iterdir()), ["Broken.mp3"])


class AudioDeepAnalysisTest(unittest.TestCase):
    def setUp(self):
        import librosa

        self.m = load()
        self.m.librosa = librosa

    def test_band_folder_for_detects_per_band_layout(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        tmp_path = Path(td.name)
        audio = tmp_path / "docs" / "audio"
        self.assertEqual(self.m.band_folder_for(audio / "band-a" / "Night Shift.mp3"), "band-a")
        self.assertIsNone(self.m.band_folder_for(audio / "Night Shift.mp3"))          # legacy flat layout
        self.assertIsNone(self.m.band_folder_for(tmp_path / "Downloads" / "x.mp3"))  # not an audio folder

    def test_energy_arc_rises_and_the_shift_is_up_at_the_right_time(self):
        rng = np.random.default_rng(7)
        quiet = rng.uniform(-0.05, 0.05, 20 * SR)
        loud = rng.uniform(-1.0, 1.0, 20 * SR)
        energy = self.m.analyze_energy(np.concatenate([quiet, loud]), SR, collect=True)
        self.assertEqual([w["time"] for w in energy["windows"]], [0, 5, 10, 15, 20, 25, 30, 35])
        pcts = [w["energy_pct"] for w in energy["windows"]]
        self.assertTrue(all(p < 10 for p in pcts[:4]), pcts)
        self.assertTrue(all(p > 90 for p in pcts[4:]), pcts)
        self.assertEqual(len(energy["shifts"]), 1)
        shift = energy["shifts"][0]
        self.assertEqual((shift["direction"], shift["time"]), ("UP", 20))
        self.assertGreater(shift["to_pct"], shift["from_pct"])
        self.assertEqual(shift["change_pct"], shift["to_pct"] - shift["from_pct"])

    def test_a_drop_is_down(self):
        rng = np.random.default_rng(7)
        y = np.concatenate([rng.uniform(-1.0, 1.0, 10 * SR), rng.uniform(-0.05, 0.05, 10 * SR)])
        shifts = self.m.analyze_energy(y, SR, collect=True)["shifts"]
        self.assertEqual([(s["direction"], s["time"]) for s in shifts], [("DOWN", 10)])

    def test_windows_cover_a_short_track_and_a_tail(self):
        bounds = self.m.window_bounds
        self.assertEqual(bounds(0, 100), [])
        self.assertEqual(bounds(30, 100), [(0, 30)])                        # shorter than one window: one window
        self.assertEqual(bounds(200, 100), [(0, 100), (100, 200)])
        self.assertEqual(bounds(260, 100), [(0, 100), (100, 200), (200, 260)])  # a long tail is its own window
        self.assertEqual(bounds(230, 100), [(0, 100), (100, 230)])          # a short tail joins the last window

    def test_a_track_shorter_than_one_window_still_gets_readings(self):
        y = click_triad(3.0)
        self.assertEqual(self.m.analyze_energy(y, SR, collect=True)["windows"][0]["time"], 0)
        chords = self.m.analyze_chords(y, SR, collect=True)
        self.assertEqual([(c["time_start"], c["key"]) for c in chords], [(0, "A minor")])
        self.assertAlmostEqual(chords[0]["time_end"], 3.0, delta=0.1)
        spectral = self.m.analyze_spectral_balance(y, SR, collect=True)
        self.assertEqual(len(spectral), 1)
        self.assertGreater(spectral[0]["low_pct"], spectral[0]["high_pct"])  # 220-330 Hz tones sit low


class MainTest(unittest.TestCase):
    """main() in-process on a synthesized render: where the archive lands, and what -o gets."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name).resolve()
        self.root = base / "project"
        (self.root / "_bmad").mkdir(parents=True)
        self.song = self.root / "docs" / "audio" / "band-a" / "Song.wav"
        self.song.parent.mkdir(parents=True)
        write_wav(self.song, click_triad(6.0))
        self.elsewhere = base / "elsewhere"
        self.elsewhere.mkdir()
        self.archive = self.root / "docs" / "audio-analysis" / "songs" / "band-a" / "song.json"
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.elsewhere)  # not the project root: the archive must still land in the project
        self.m = load("audio_deep_analysis_main")

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["audio_deep_analysis.py", *argv]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as exit_:
                self.m.main()
        return exit_.exception.code, out.getvalue(), err.getvalue()

    def test_json_run_archives_under_the_band_folder_of_the_audios_project(self):
        code, out, err = self.run_main([str(self.song)])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["status"], "pass")
        self.assertEqual(json.loads(self.archive.read_text(encoding="utf-8")), data)
        self.assertIn(f"ARCHIVED: {self.archive}", err)
        self.assertEqual(list(self.elsewhere.iterdir()), [])
        metrics = data["metrics"]
        self.assertEqual(metrics["file"], "Song.wav")
        self.assertTrue(metrics["energy_arc"]["windows"])
        self.assertTrue(metrics["chord_progression"])
        self.assertTrue(metrics["spectral_balance"])

    def test_text_run_writes_the_report_to_the_output_file_and_still_archives(self):
        target = self.elsewhere / "reports" / "deep.txt"
        code, out, _ = self.run_main([str(self.song), "--format", "text", "-o", str(target)])
        self.assertEqual((code, out), (0, ""))
        report = target.read_text(encoding="utf-8")
        for heading in ("=== ENERGY / LOUDNESS ARC ===", "=== KEY/CHORD PROGRESSION ===",
                        "=== SECTION BOUNDARIES (spectral novelty) ===", "=== SPECTRAL BALANCE (low/mid/high) ==="):
            self.assertIn(heading, report)
        archived = json.loads(self.archive.read_text(encoding="utf-8"))
        self.assertEqual(archived["metrics"]["chord_progression"][0]["key"], "A minor")

    def test_no_archive_writes_nothing(self):
        code, _, err = self.run_main([str(self.song), "--no-archive"])
        self.assertEqual(code, 0)
        self.assertFalse((self.root / "docs" / "audio-analysis").exists())
        self.assertNotIn("ARCHIVED", err)

    def test_usage_error_exits_1_not_the_missing_dependency_code(self):
        code, out, _ = self.run_main([str(self.song), "--format", "yaml"])
        self.assertEqual(code, 1)
        self.assertIn("usage:", json.loads(out)["error"])


if __name__ == "__main__":
    unittest.main()
