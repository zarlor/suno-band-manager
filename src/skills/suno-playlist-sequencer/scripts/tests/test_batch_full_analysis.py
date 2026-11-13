#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for batch_full_analysis.py, the catalog-wide deeper-analysis layer of the suno-playlist-sequencer workflow.

Three groups:
  - the exit-code contract of the real script, run with `uv run` so its own
    dependencies are provisioned (skipped without uv): each failure exits 1 with
    a JSON `error` on stdout, never a crash and never the dependency exit 2;
  - file discovery, output scoping and the report formats, on dicts in
    analyze_track's shape;
  - main() end to end: with analyze_track stood in for the artifact rules, and
    once with the real analyze_track on synthesized audio, so its return shape
    is checked against the report builder (skipped without librosa).
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
import wave
from pathlib import Path
from unittest import mock

SCRIPT = str(Path(__file__).parent.parent / "batch_full_analysis.py")
UV = shutil.which("uv")
TIMEOUT = 600
HAVE_AUDIO_LIBS = all(importlib.util.find_spec(n) for n in ("librosa", "numpy"))


def run_uv(args: list[str]):
    """(exit code, stdout) of the real script under `uv run`."""
    proc = subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT)
    return proc.returncode, proc.stdout


def write_wav(path, seconds=8.0, bpm=120.0, freqs=(220.0, 261.63, 329.63), level=0.15):
    """A short mono 16-bit WAV: a held chord with a decaying noise burst on every beat."""
    import numpy as np

    sr = 22050
    t = np.arange(int(seconds * sr)) / sr
    y = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs) * level
    n = int(0.05 * sr)
    burst = np.random.default_rng(7).uniform(-1, 1, n) * np.exp(-np.arange(n) / (0.01 * sr)) * 0.8
    for beat in np.arange(0, seconds - 0.1, 60.0 / bpm):
        i = int(beat * sr)
        y[i:i + n] += burst
    pcm = (np.clip(y, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


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

    def test_missing_dir_exits_1_with_the_reason(self):
        code, out = run_uv(["--audio-dir", "/nonexistent-audio-dir-xyz"])
        self.assertEqual(code, 1)  # not 2 (dependencies missing), and not a crash without JSON
        report = json.loads(out)
        self.assertEqual((report["script"], report["status"]), ("batch-full-analysis", "fail"))
        self.assertIn("Audio directory not found: /nonexistent-audio-dir-xyz", report["error"])

    def test_folder_without_audio_exits_1_with_the_reason(self):
        (self.tmp_path / "notes.txt").write_text("x", encoding="utf-8")
        code, out = run_uv(["--audio-dir", str(self.tmp_path)])
        self.assertEqual(code, 1)
        report = json.loads(out)
        self.assertEqual(report["status"], "fail")
        self.assertIn("No audio files found", report["error"])

    def test_usage_error_exits_1_with_the_error_object_not_2(self):
        # Exit 2 means the audio dependencies are missing; a mistyped flag must not read as that.
        for args in (["--no-such-flag"], ["--format", "yaml"]):
            code, out = run_uv(args)
            self.assertEqual(code, 1, args)
            report = json.loads(out)
            self.assertEqual(report["status"], "fail")
            self.assertTrue(report["error"].startswith("usage: "), report["error"])
        self.assertEqual(run_uv(["--help"])[0], 0)

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

    def test_every_audio_type_is_found_in_any_case(self):
        m = _load()
        for name in ("Render.wav", "LOUD.MP3", "Master.FLAC", "demo.ogg", "phone.m4a", "cover.jpg", "notes.mp3.txt"):
            (self.tmp_path / name).write_bytes(b"x")
        found = m.find_mp3s(str(self.tmp_path))
        self.assertEqual([m.rel_label(p, str(self.tmp_path)) for p in found],
                         ["LOUD.MP3", "Master.FLAC", "Render.wav", "demo.ogg", "phone.m4a"])
        self.assertEqual([m.track_label(n) for n in ("LOUD.MP3", "band-a/Render.wav", "Mr. Blue", "notes.txt")],
                         ["LOUD", "band-a/Render", "Mr. Blue", "notes.txt"])

    def test_failed_tracks_are_named_in_the_markdown(self):
        m = _load()
        text = m.format_text([_result("Song", 100.0), {"file": "band-b/Other.wav", "error": "boom"}])
        self.assertIn("_Not analyzed (1 of 2): band-b/Other.wav (boom)._", text)
        self.assertNotIn("Not analyzed", m.format_text([_result("Song", 100.0)]))

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

    def run_main(self, *args, analyze=None, parse=True):
        """(exit code, stdout JSON) for one run; stderr is kept on self.stderr. parse=False returns stdout as text."""
        analyze = analyze or (lambda path, reading=None: _result(Path(path).stem, 100.0))
        out, err, code = io.StringIO(), io.StringIO(), 0
        with mock.patch.object(self.m, "analyze_track", analyze), \
                mock.patch.object(sys, "argv", ["x", "--tempo-source", "librosa", *args]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                self.m.main()
            except SystemExit as exc:
                code = exc.code or 0
        self.stderr = err.getvalue()
        return code, (json.loads(out.getvalue()) if parse else out.getvalue())

    def test_default_targets_scope_by_folder(self):
        j = os.path.join
        self.assertEqual(self.m.default_targets("docs/audio", "2026-10-15"),
                         (j("docs", "audio-analysis", "catalog", "2026-10-15-deep.json"),
                          j("docs", "catalog-analysis-report.md")))
        self.assertEqual(self.m.default_targets("docs/audio/Band A/", "2026-10-15"),
                         (j("docs", "audio-analysis", "catalog", "2026-10-15-deep-band-a.json"),
                          j("docs", "band-a-catalog-analysis-report.md")))
        self.assertEqual(self.m.default_targets("music/audio", "2026-10-15")[1], j("music", "catalog-analysis-report.md"))

    def test_outputs_follow_the_scanned_folder_never_the_working_directory(self):
        j = os.path.join
        scope = self.m.output_scope
        self.assertEqual(scope(j("proj", "docs", "audio")), (j("proj", "docs"), None))
        self.assertEqual(scope(j("proj", "docs", "audio", "band-a")), (j("proj", "docs"), "band-a"))
        # Nested under an audio/ folder: still beside that audio/ folder, scoped by the folder scanned.
        self.assertEqual(scope(j("proj", "docs", "audio", "band-a", "Album One")), (j("proj", "docs"), "album-one"))
        # No audio/ folder above it: beside the scanned folder itself.
        self.assertEqual(scope(j("/mnt", "renders", "Tuesday")), (j("/mnt", "renders"), "tuesday"))
        self.assertEqual(self.m.default_targets(j("/mnt", "renders", "Tuesday"), "2026-10-15"),
                         (j("/mnt", "renders", "audio-analysis", "catalog", "2026-10-15-deep-tuesday.json"),
                          j("/mnt", "renders", "tuesday-catalog-analysis-report.md")))

    def test_external_folder_run_writes_beside_it_not_under_cwd(self):
        renders = self.root / "renders" / "tuesday"
        renders.mkdir(parents=True)
        (renders / "Take.WAV").write_bytes(b"x")
        (self.root / "elsewhere").mkdir()
        os.chdir(self.root / "elsewhere")
        code, out = self.run_main("--audio-dir", str(renders))
        self.assertEqual((code, out["analyzed_count"]), (0, 1))
        self.assertEqual(out["artifacts"]["companion"]["path"], str(self.root / "renders" / "tuesday-catalog-analysis-report.md"))
        self.assertTrue((self.root / "renders" / "tuesday-catalog-analysis-report.md").is_file())
        self.assertTrue(list((self.root / "renders" / "audio-analysis" / "catalog").glob("*-deep-tuesday.json")))
        self.assertFalse((self.root / "elsewhere" / "docs").exists())

    def test_default_audio_folder_comes_from_the_project_root(self):
        (self.root / "elsewhere").mkdir()
        os.chdir(self.root / "elsewhere")
        code, out = self.run_main()
        self.assertEqual(code, 1)  # no docs/audio under this folder, and no project above it
        self.assertIn("Audio directory not found", out["error"])
        code, out = self.run_main("--project-root", str(self.root))
        self.assertEqual((code, out["analyzed_count"]), (0, 2))
        self.assertTrue((self.root / "docs" / "catalog-analysis-report.md").is_file())
        (self.root / "_bmad").mkdir()  # found from the working directory when it sits inside the project
        code, out = self.run_main("--no-archive", "--no-companion")
        self.assertEqual((code, out["analyzed_count"]), (0, 2))

    def test_a_failed_write_is_said_and_exits_3(self):
        (self.root / "docs" / "audio-analysis").write_text("a file where the archive folder goes", encoding="utf-8")
        code, out = self.run_main()
        self.assertEqual(code, 3)
        self.assertEqual((out["status"], out["analyzed_count"]), ("ok", 2))  # the analysis is whole and on stdout
        self.assertEqual(out["artifacts"]["archive"]["status"], "error")
        self.assertTrue(out["artifacts"]["archive"]["reason"])
        self.assertEqual(out["artifacts"]["companion"]["status"], "written")
        self.assertIn("ARCHIVE WRITE FAILED", self.stderr)
        code, text = self.run_main("--format", "text", parse=False)  # no artifacts block in text
        self.assertEqual(code, 3)
        self.assertIn("## Summary Table", text)
        self.assertIn("ARCHIVE WRITE FAILED", self.stderr)

    def test_output_folder_is_created_and_a_bad_one_fails_before_any_write(self):
        code, _ = self.run_main("-o", "reports/new/out.json", "--no-archive", "--no-companion", parse=False)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((self.root / "reports/new/out.json").read_text(encoding="utf-8"))["analyzed_count"], 2)
        (self.root / "blocker").write_text("a file", encoding="utf-8")
        for bad in ("blocker/sub/out.json", "docs"):  # a file where a folder is needed; a folder as the file
            code, out = self.run_main("-o", bad)
            self.assertEqual((code, out["status"]), (1, "fail"), bad)
            self.assertIn("-o", out["error"])
        self.assertFalse((self.root / "docs/catalog-analysis-report.md").exists())
        self.assertFalse((self.root / "docs/audio-analysis").exists())

    def test_usage_error_is_the_json_failure_and_exit_1(self):
        code, out = self.run_main("--format", "yaml")
        self.assertEqual((code, out["status"]), (1, "fail"))
        self.assertTrue(out["error"].startswith("usage: "))

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
            raise self.m.BeatThisUnavailable("beat_grid.py not found")
        with mock.patch.object(self.m, "run_beat_grid", unavailable):
            code, out = self.run_main("--tempo-source", "beat-this")
        self.assertIn("beat_grid.py not found", out["tempo_source_note"])


@unittest.skipUnless(HAVE_AUDIO_LIBS, "librosa and numpy are needed to analyze real audio")
class TestRealAnalysis(unittest.TestCase):
    """main() with the real analyze_track on synthesized audio: its return shape must fit build_report
    and format_text. Nothing is stood in: this script needs only librosa and numpy."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.m = _load()
        self.audio = self.root / "docs" / "audio" / "band-a"
        self.audio.mkdir(parents=True)
        write_wav(self.audio / "One.wav", bpm=120.0, freqs=(220.0, 261.63, 329.63))   # an A minor chord
        write_wav(self.audio / "Two.WAV", bpm=90.0, freqs=(261.63, 329.63, 392.0))    # a C major chord

    def run_main(self, *extra):
        argv = ["x", "--audio-dir", str(self.audio), "--tempo-source", "librosa", *extra]
        out = io.StringIO()
        code = 0
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            try:
                self.m.main()
            except SystemExit as exc:
                code = exc.code or 0
        return code, out.getvalue()

    def test_real_tracks_come_through_the_report_and_the_files(self):
        code, out = self.run_main()
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual((report["status"], report["track_count"], report["analyzed_count"]), ("ok", 2, 2))
        self.assertEqual(report["failed"], [])
        self.assertEqual([t["file"] for t in report["tracks"]], ["One.wav", "Two.WAV"])
        one, two = report["tracks"]
        # Measurements of the signal: the click rate and the chord.
        self.assertAlmostEqual(one["bpm"], 120.0, delta=6.0)
        self.assertAlmostEqual(two["bpm"], 90.0, delta=5.0)
        self.assertEqual((one["key"], two["key"]), ("A minor", "C major"))
        for t in report["tracks"]:
            self.assertNotIn("error", t)
            self.assertAlmostEqual(t["duration"], 8.0, delta=0.2)
            self.assertEqual(t["duration_display"], "0:08")
            self.assertEqual(t["tempo_source"], "librosa")
            self.assertIn(t["bpm_stability"], ("steady", "slight variation", "TEMPO CHANGES", "too few beats"))
            self.assertEqual(len(t["bpm_range"]), 2)
            self.assertIn(t["librosa_prior_relation"], ("agree", "double", "other"))
            self.assertIsInstance(t["key_confidence"], float)
            self.assertRegex(t["dynamic_character"], r"^(FLAT|MODERATE|DYNAMIC|HIGHLY DYNAMIC) ")
            self.assertEqual(sorted(t["energy"]), ["max", "min", "profile", "range", "shifts"])
            self.assertEqual(t["energy"]["range"], t["energy"]["max"] - t["energy"]["min"])
            balance = t["spectral_balance"]
            self.assertTrue(97 <= balance["low_pct"] + balance["mid_pct"] + balance["high_pct"] <= 100, balance)
            self.assertIsInstance(t["sections"], list)
        archive = report["artifacts"]["archive"]
        self.assertEqual(archive["status"], "written")
        self.assertEqual(json.loads(Path(archive["path"]).read_text(encoding="utf-8"))["tracks"], report["tracks"])
        companion = (self.root / "docs" / "band-a-catalog-analysis-report.md").read_text(encoding="utf-8")
        self.assertRegex(companion, r"\| One \| 0:08 \| [\d.]+")
        self.assertRegex(companion, r"\| Two \| 0:08 \| [\d.]+")  # the label drops .WAV as it drops .mp3

    def test_real_tracks_come_through_the_text_report(self):
        code, text = self.run_main("--format", "text", "--no-archive", "--no-companion")
        self.assertEqual(code, 0)
        self.assertIn("## Spectral Balance", text)
        self.assertRegex(text, r"\| One \| \d+% \| \d+% \| \d+% \|")


if __name__ == "__main__":
    unittest.main()
