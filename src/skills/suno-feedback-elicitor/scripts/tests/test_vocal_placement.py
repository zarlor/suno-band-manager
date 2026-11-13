#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for vocal_placement.py (Demucs stems + BS.1770 loudness).

Demucs needs PyTorch, which is too heavy to provision in the suite, so these pin
the placement arithmetic, the no-vocal flagging, text output, and the
exit-code contract (the path guard runs before the dependency check). main()
runs in-process with the model, the loudness meter and the per-file separation
stood in, to pin what a run archives.
"""

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parent.parent / "vocal_placement.py"
spec = importlib.util.spec_from_file_location("vocal_placement", SCRIPT)
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)


class VocalPlacementTest(unittest.TestCase):
    def test_placement_overall_thirds_and_drift(self):
        p = vp.placement(-15.0, -14.0, [-16.0, -15.0, -14.0], [-16.5, -14.0, -12.0])
        self.assertEqual(p["vocal_minus_band_lu"], -1.0)
        self.assertEqual(p["vocal_minus_band_thirds_lu"], [0.5, -1.0, -2.0])
        self.assertEqual(p["vocal_drift_lu"], -2.5)
        self.assertEqual(p["vocal_present_thirds"], [True, True, True])

    def test_instrumental_ending_is_flagged_and_drift_withheld(self):
        p = vp.placement(-18.0, -13.0, [-15.0, -15.0, -40.0], [-14.0, -13.0, -12.0])
        self.assertEqual(p["vocal_present_thirds"], [True, True, False])
        self.assertIsNone(p["vocal_drift_lu"])

    def test_silent_stem_gives_none(self):
        p = vp.placement(None, -13.0, [None, None, None], [-14.0, -13.0, -12.0])
        self.assertIsNone(p["vocal_minus_band_lu"])
        self.assertEqual(p["vocal_present_thirds"], [False, False, False])

    def test_format_text_marks_absent_thirds(self):
        r = {"file": "x.mp3", **vp.placement(-18.0, -13.0, [-15.0, -15.0, -40.0], [-14.0, -13.0, -12.0])}
        text = vp.format_text([r, {"file": "y.mp3", "error": "boom"}])
        self.assertEqual(vp.format_json([r], "cuda", 5)["metrics"]["shifts"], 5)
        self.assertIn("-28.0*", text)
        self.assertIn("ERROR: boom", text)

    def test_missing_input_exits_1(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), "/nonexistent-audio-xyz", "--no-archive"],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Not found", proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "fail")

    def test_usage_errors_exit_1_not_the_missing_dependency_code(self):
        for argv in (["--shifts", "0"], ["--shifts", "-2"], ["--format", "yaml"], ["--bogus"]):
            proc = subprocess.run([sys.executable, str(SCRIPT), "/nonexistent-audio-xyz", *argv],
                                  capture_output=True, text=True, timeout=60)
            self.assertEqual(proc.returncode, 1, argv)  # 2 is read as "audio dependencies missing"
            self.assertIn("usage:", json.loads(proc.stdout)["error"], argv)
        proc = subprocess.run([sys.executable, str(SCRIPT), "/nonexistent-audio-xyz", "--shifts", "0"],
                              capture_output=True, text=True, timeout=60)
        self.assertIn("--shifts must be 1 or more", proc.stderr)


GOOD = {"duration_s": 180.0, "vocals_lufs": -15.0, "band_lufs": -14.0,
        **vp.placement(-15.0, -14.0, [-16.0, -15.0, -14.0], [-16.5, -14.0, -12.0]), "stems_lufs": {}}


class MainArchiveTest(unittest.TestCase):
    """main() with Demucs, pyloudnorm and the separation stood in: what a run leaves on disk."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name).resolve()
        self.root = base / "project"
        (self.root / "_bmad").mkdir(parents=True)
        self.band = self.root / "docs" / "audio" / "band-a"
        self.band.mkdir(parents=True)
        for name in ("Song.mp3", "Other.mp3"):
            (self.band / name).write_bytes(b"")
        self.song_archive = self.root / "docs" / "audio-analysis" / "songs" / "band-a" / "song-vocal-placement.json"
        self.elsewhere = base / "elsewhere"
        self.elsewhere.mkdir()
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.elsewhere)  # not the project root: the archive must still land in the project

    def run_main(self, argv, analyze):
        model = mock.MagicMock(samplerate=44100)
        fakes = {
            "pyloudnorm": types.SimpleNamespace(Meter=lambda sr: object()),
            "demucs": types.ModuleType("demucs"),
            "demucs.pretrained": types.SimpleNamespace(get_model=lambda name: model),
        }
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(sys.modules, fakes), mock.patch.object(vp, "require_modules"), \
                mock.patch.object(vp, "resolve_device", return_value="cpu"), \
                mock.patch.object(vp, "analyze_file", side_effect=analyze), \
                mock.patch.object(sys, "argv", ["vocal_placement.py", *argv]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as exit_:
                vp.main()
        return exit_.exception.code, out.getvalue(), err.getvalue()

    @staticmethod
    def failing(*args, **kwargs):
        raise RuntimeError("CUDA out of memory")

    def test_good_run_archives_under_the_audios_project(self):
        code, out, err = self.run_main([str(self.band / "Song.mp3")], lambda *a, **k: dict(GOOD))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(self.song_archive.read_text(encoding="utf-8")), json.loads(out))
        self.assertIn(f"ARCHIVED: {self.song_archive}", err)
        self.assertEqual(list(self.elsewhere.iterdir()), [])

    def test_a_run_where_every_file_fails_leaves_the_good_archive_untouched(self):
        self.run_main([str(self.band / "Song.mp3")], lambda *a, **k: dict(GOOD))
        before = self.song_archive.read_bytes()
        code, out, err = self.run_main([str(self.band / "Song.mp3")], self.failing)
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["status"], "fail")
        self.assertEqual(data["findings"][0]["message"], "RuntimeError: CUDA out of memory")
        self.assertEqual(self.song_archive.read_bytes(), before)
        self.assertIn("nothing archived", err)
        self.assertNotIn("ARCHIVED:", err)

    def test_a_failed_first_run_writes_no_archive_at_all(self):
        code, _, _ = self.run_main([str(self.band)], self.failing)
        self.assertEqual(code, 1)
        self.assertFalse((self.root / "docs" / "audio-analysis").exists())

    def test_a_partial_run_exits_0_and_archives_with_the_folder_slug(self):
        def analyze(path, *args, **kwargs):
            if path.endswith("Other.mp3"):
                raise RuntimeError("could not decode")
            return dict(GOOD)

        code, out, _ = self.run_main([str(self.band)], analyze)
        self.assertEqual((code, json.loads(out)["status"]), (0, "partial"))
        names = [p.name for p in (self.root / "docs" / "audio-analysis" / "catalog").iterdir()]
        self.assertEqual(len(names), 1)
        self.assertRegex(names[0], r"^\d{4}-\d\d-\d\d-vocal-placement-band-a\.json$")


if __name__ == "__main__":
    unittest.main()
