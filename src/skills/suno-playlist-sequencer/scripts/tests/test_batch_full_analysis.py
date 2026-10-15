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

import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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


def _load():
    spec = importlib.util.spec_from_file_location("batch_full_analysis_main", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class TestBatchOutputs(unittest.TestCase):
    """A band-folder pass never overwrites the catalog-wide report; a run with nothing analyzed writes nothing."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.enterContext(contextlib.chdir(self.root))
        self.m = _load()
        for rel in ("docs/audio/band-a/Song.mp3", "docs/audio/band-b/Other.mp3"):
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_bytes(b"x")
        self.enterContext(mock.patch.object(self.m, "require_audio_deps", lambda **kw: None))
        self.enterContext(mock.patch.dict(sys.modules, {"librosa": type(sys)("librosa"),
                                                        "numpy": type(sys)("numpy")}))

    def run_main(self, *args, analyze=None):
        analyze = analyze or (lambda path, reading=None: _result(Path(path).stem, 100.0))
        out, code = io.StringIO(), 0
        with mock.patch.object(self.m, "analyze_track", analyze), \
                mock.patch.object(sys, "argv", ["x", "--tempo-source", "librosa", *args]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            try:
                self.m.main()
            except SystemExit as exc:
                code = exc.code
        return code, json.loads(out.getvalue())

    def test_default_targets_scope_by_folder(self):
        j = os.path.join
        self.assertEqual(self.m.default_targets("docs/audio", "2026-10-15"),
                         (j("docs", "audio-analysis", "catalog", "2026-10-15-deep.json"),
                          j("docs", "catalog-analysis-report.md")))
        self.assertEqual(self.m.default_targets("docs/audio/Band A/", "2026-10-15"),
                         (j("docs", "audio-analysis", "catalog", "2026-10-15-deep-band-a.json"),
                          j("docs", "band-a-catalog-analysis-report.md")))
        self.assertEqual(self.m.default_targets("music/audio", "2026-10-15")[1], j("music", "catalog-analysis-report.md"))

    def test_band_pass_leaves_the_catalog_report_alone(self):
        code, out = self.run_main()
        self.assertEqual(code, 0)
        catalog = (self.root / "docs/catalog-analysis-report.md").read_text()
        code, out = self.run_main("--audio-dir", "docs/audio/band-a")
        self.assertEqual(code, 0)
        self.assertEqual(out["artifacts"]["companion"], {"path": os.path.join("docs", "band-a-catalog-analysis-report.md"),
                                                         "status": "written"})
        self.assertIn("-deep-band-a.json", out["artifacts"]["archive"]["path"])
        self.assertEqual((self.root / "docs/catalog-analysis-report.md").read_text(), catalog)

    def test_every_track_failing_exits_1_and_writes_nothing(self):
        code, out = self.run_main(analyze=lambda path, reading=None: {"file": "x", "error": "boom"})
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "fail")
        self.assertEqual(len(out["failed"]), 2)
        self.assertFalse((self.root / "docs/catalog-analysis-report.md").exists())
        self.assertFalse((self.root / "docs/audio-analysis").exists())

    def test_partial_failure_is_reported(self):
        def analyze(path, reading=None):
            return {"file": "x", "error": "boom"} if "Other" in path else _result("Song", 100.0)
        code, out = self.run_main(analyze=analyze)
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "partial")
        self.assertEqual(out["failed"], [{"file": "band-b/Other.mp3", "error": "boom"}])
        self.assertEqual(out["analyzed_count"], 1)

    def test_tempo_source_note_on_fallback(self):
        def unavailable(paths, include_beats=False):
            raise self.m.BeatThisUnavailable("beat-grid.py not found")
        with mock.patch.object(self.m, "run_beat_grid", unavailable):
            code, out = self.run_main("--tempo-source", "beat-this")
        self.assertIn("beat-grid.py not found", out["tempo_source_note"])


if __name__ == "__main__":
    unittest.main()
