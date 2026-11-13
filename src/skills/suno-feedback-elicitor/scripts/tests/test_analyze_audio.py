#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for analyze_audio.py.

Three layers. The exit-code contract runs the script via `uv run`, so its
PEP 723 deps (librosa, pyloudnorm) are provisioned and a failure is a reason,
not a traceback; one such run measures a synthesized render end to end. The
routing of main() (which archive, which companion, what -o and the flags do)
runs in-process with the per-file measurement stood in. analyze_file itself runs
in-process on a synthesized render with real librosa; only the BS.1770 summary
is stood in there, because pyloudnorm is not in the test runner.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_synth import click_triad, write_wav  # noqa: E402

SCRIPT = str(Path(__file__).parent.parent / "analyze_audio.py")
UV = shutil.which("uv")
TIMEOUT = 600


def run_uv(args: list[str], cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT, cwd=cwd)


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@unittest.skipIf(UV is None, "uv not available to provision librosa deps")
class AnalyzeAudioTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp_path = Path(td.name)

    def test_missing_dir_exits_1_with_a_reason(self):
        proc = run_uv(["/nonexistent-audio-dir-xyz"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Audio file or directory not found", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "fail")

    def test_empty_dir_exits_1(self):
        proc = run_uv([str(self.tmp_path)])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("No audio files", proc.stderr)

    def test_usage_error_exits_1_not_the_missing_dependency_code(self):
        proc = run_uv([str(self.tmp_path), "--format", "yaml"])
        self.assertEqual(proc.returncode, 1)  # 2 is read as "audio dependencies missing"
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "fail")
        self.assertIn("usage:", out["error"])

    def test_synthesized_render_is_measured_end_to_end(self):
        audio = self.tmp_path / "audio"
        audio.mkdir()
        write_wav(audio / "Take.wav", click_triad(8.0))
        proc = run_uv([str(audio), "--no-archive", "--no-companion", "--tempo-source", "librosa"],
                      cwd=self.tmp_path)
        if proc.returncode == 2:
            self.skipTest("pyloudnorm could not be provisioned for the script")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "pass")
        track = data["metrics"]["tracks"][0]
        self.assertEqual(track["file"], "Take.wav")
        for field in ("bpm", "bpm_librosa", "key_confidence"):
            self.assertIsInstance(track[field], (int, float), field)
        self.assertRegex(track["key"], r" (major|minor)$")
        self.assertRegex(track["duration"], r"^\d+:\d\d$")
        self.assertIsInstance(track["loudness"]["integrated_lufs"], float)
        self.assertEqual(sorted(p.name for p in self.tmp_path.iterdir()), ["audio"])  # the flags wrote nothing

    def test_every_file_failing_exits_1_and_writes_nothing(self):
        audio = self.tmp_path / "docs" / "audio" / "band-a"
        audio.mkdir(parents=True)
        (audio / "Broken.mp3").write_bytes(b"not audio at all")
        code = run_uv([str(audio), "--tempo-source", "librosa"], cwd=self.tmp_path).returncode
        self.assertEqual(code, 1)
        self.assertFalse((self.tmp_path / "docs" / "audio-analysis").exists())
        self.assertFalse((self.tmp_path / "docs" / "audio-analysis-reference.md").exists())

    def test_single_file_that_is_not_mp3_exits_1(self):
        f = self.tmp_path / "notes.txt"
        f.write_text("x")
        self.assertEqual(run_uv([str(f)]).returncode, 1)


class AnalyzeAudioFunctionsTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp_path = Path(td.name)

    def test_find_audio_files_recurses_and_labels_band_folders(self):
        m = load("analyze_audio")
        tmp_path = self.tmp_path
        (tmp_path / "band-a").mkdir()
        (tmp_path / ".hidden").mkdir()
        for rel in ("band-a/Song.mp3", "Loose.mp3", ".hidden/Skip.mp3", "notes.txt"):
            (tmp_path / rel).write_bytes(b"x")
        found = m.find_audio_files(str(tmp_path))
        self.assertEqual([m.rel_label(p, str(tmp_path)) for p in found], ["Loose.mp3", "band-a/Song.mp3"])

    def test_find_audio_files_takes_wav_flac_and_upper_case_extensions(self):
        m = load("analyze_audio_exts")
        for name in ("a.wav", "b.flac", "C.MP3", "d.Ogg", "e.m4a", "f.txt", "g.mp3.bak"):
            (self.tmp_path / name).write_bytes(b"x")
        found = [os.path.basename(p) for p in m.find_audio_files(str(self.tmp_path))]
        self.assertEqual(found, ["C.MP3", "a.wav", "b.flac", "d.Ogg", "e.m4a"])

    def test_analyze_file_measures_a_synthesized_render(self):
        """Real librosa on a click-plus-triad signal; only the pyloudnorm summary is stood in."""
        import librosa

        m = load("analyze_audio_real")
        m.librosa = librosa
        wav = write_wav(self.tmp_path / "Take.wav", click_triad(8.0))
        loud = {"integrated_lufs": -14.6, "lra_lu": 0.1}
        with mock.patch.object(m, "loudness_summary", return_value=loud) as summary:
            result = m.analyze_file(str(wav))
        self.assertNotIn("error", result)
        self.assertEqual(result["file"], "Take.wav")
        self.assertEqual(result["duration"], "0:08")
        self.assertEqual(result["tempo_source"], "librosa")
        self.assertEqual(result["bpm"], result["bpm_librosa"])
        self.assertTrue(110 <= result["bpm"] <= 125 or 55 <= result["bpm"] <= 62, result["bpm"])  # 120, or its half
        self.assertIsInstance(result["bpm_librosa_slow_prior"], float)
        self.assertEqual(result["key"], "A minor")
        self.assertGreater(result["key_confidence"], 0.5)
        self.assertEqual(result["loudness"], loud)
        samples, native_sr = summary.call_args.args  # loudness is read at the file's own rate
        self.assertEqual((native_sr, len(samples)), (22050, 8 * 22050))

    def test_analyze_file_reports_an_unreadable_file_as_an_error_entry(self):
        import librosa

        m = load("analyze_audio_bad")
        m.librosa = librosa
        bad = self.tmp_path / "Broken.mp3"
        bad.write_bytes(b"not audio at all")
        with contextlib.redirect_stderr(io.StringIO()):
            result = m.analyze_file(str(bad))
        self.assertEqual(sorted(result), ["error", "file"])
        self.assertEqual(result["file"], "Broken.mp3")

    def test_mixed_run_is_partial_with_the_failed_file_listed(self):
        m = load("analyze_audio_partial")
        good = {"file": "good.mp3", "duration": "3:10", "bpm": 120.0, "bpm_librosa": 120.0, "key": "F major",
                "key_confidence": 0.8, "loudness": {"integrated_lufs": -14.0, "lra_lu": 6.0}}
        data = m.format_json_output([good, {"file": "bad.mp3", "error": "boom"}], 2)
        self.assertEqual(data["status"], "partial")
        self.assertEqual(data["metrics"]["tracks_analyzed"], 1)
        self.assertEqual(data["metrics"]["tracks_errored"], 1)
        self.assertEqual(data["findings"], [{"file": "bad.mp3", "level": "error", "message": "boom"}])
        self.assertEqual(m.format_json_output([{"file": "bad.mp3", "error": "boom"}], 1)["status"], "fail")

    def test_text_and_json_report_loudness(self):
        m = load("analyze_audio_fmt")
        results = [
            {"file": "band-a/One.mp3", "duration": "3:10", "bpm_librosa": 152.0, "key": "F major", "key_confidence": 0.81,
             "loudness": {"integrated_lufs": -14.02, "lra_lu": 7.44, "thirds_lufs": [-16, -14, -13], "build_lu": 3.0}},
            {"file": "band-a/Two.mp3", "duration": "0:04", "bpm_librosa": 95.7, "key": "C minor", "key_confidence": 0.69,
             "loudness": {"integrated_lufs": -20.5, "lra_lu": None, "thirds_lufs": [None, None, None], "build_lu": None}},
        ]
        text = m.format_text_output(results, 2)
        self.assertIn("LUFS", text.splitlines()[2])  # the column sits in the header row
        self.assertIn("-14.02", text)
        self.assertIn("Loudness range (integrated): -20.5 to -14.0 LUFS", text)
        data = m.format_json_output(results, 2)
        self.assertEqual(data["metrics"]["integrated_lufs_range"], {"min": -20.5, "max": -14.02})

    def test_beat_this_tempo_preferred_with_librosa_kept(self):
        m = load("analyze_audio_bt")
        loud = {"integrated_lufs": -14.0, "lra_lu": 6.0, "thirds_lufs": [-15, -14, -13], "build_lu": 2.0}
        results = [
            {"file": "a.mp3", "duration": "2:37", "bpm": 76.9, "bpm_beat_this": 76.9, "tempo_relation": "librosa_double",
             "tempo_source": "beat-this", "bpm_librosa": 152.0, "key": "F major", "key_confidence": 0.8, "loudness": loud},
            {"file": "b.mp3", "duration": "3:11", "bpm": 96.8, "bpm_beat_this": 96.8, "tempo_relation": "agree",
             "tempo_source": "beat-this", "bpm_librosa": 95.7, "key": "C minor", "key_confidence": 0.7, "loudness": loud},
        ]
        text = m.format_text_output(results, 2)
        self.assertIn("BPM range (Beat This!): 77 - 97", text)
        self.assertIn("different pulse on 1 track", text)
        metrics = m.format_json_output(results, 2)["metrics"]
        self.assertEqual(metrics["tempo_source"], "beat-this")
        self.assertEqual(metrics["bpm_range"], {"min": 76.9, "max": 96.8})
        self.assertEqual(metrics["bpm_range_librosa"], {"min": 95.7, "max": 152.0})

    def test_slow_prior_reading_and_halftime_note(self):
        m = load("analyze_audio_slow")
        loud = {"integrated_lufs": -15.9, "lra_lu": 5.5, "thirds_lufs": [-17, -16, -15], "build_lu": 2.0}
        slow = {"file": "slow.mp3", "duration": "3:59", "bpm": 117.5, "tempo_source": "librosa", "bpm_librosa": 117.5,
                "bpm_librosa_slow_prior": 60.1, "librosa_prior_relation": "double", "key": "G# major",
                "key_confidence": 0.85, "loudness": loud}
        agree = {**slow, "file": "agree.mp3", "bpm": 95.7, "bpm_librosa": 95.7, "bpm_librosa_slow_prior": 95.7,
                 "librosa_prior_relation": "agree"}
        text = m.format_text_output([slow, agree], 2)
        self.assertIn("Slow80", text)
        self.assertIn("60.1 (x2)", text)
        self.assertIn("     95.7      95.7 ", text)
        self.assertIn("Likely halftime ambiguity: librosa reads 117.5 BPM at its default and 60.1", text)
        two = m.format_text_output([slow, {**slow, "file": "slow2.mp3"}], 2)
        self.assertIn("Likely halftime ambiguity on 2 tracks", two)
        metrics = m.format_json_output([slow, agree], 2)["metrics"]
        self.assertEqual(metrics["librosa_prior_doubles"], 1)
        self.assertEqual(metrics["bpm_range_librosa"], {"min": 95.7, "max": 117.5})
        self.assertEqual(metrics["tracks"][0]["bpm_librosa"], 117.5)  # the default reading keeps its field and value


CANNED = {"duration": "3:10", "bpm": 120.0, "tempo_source": "librosa", "bpm_librosa": 120.0,
          "bpm_librosa_slow_prior": 120.0, "librosa_prior_relation": "agree", "key": "F major",
          "key_confidence": 0.8, "loudness": {"integrated_lufs": -14.0, "lra_lu": 6.0}}


class MainRoutingTest(unittest.TestCase):
    """main() to a successful end, with the measurement stood in: what gets written, and where."""

    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root = Path(td.name).resolve() / "project"
        (self.root / "_bmad").mkdir(parents=True)
        self.audio = self.root / "docs" / "audio"
        for rel in ("band-a/Song.mp3", "band-b/Other.wav"):
            (self.audio / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.audio / rel).write_bytes(b"")
        self.archive = self.root / "docs" / "audio-analysis"
        self.companion = self.root / "docs" / "audio-analysis-reference.md"
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.root)
        self.m = load("analyze_audio_main")

    def run_main(self, argv, analyze=None):
        """(exit code, stdout, stderr) of main() with dependencies and the per-file measurement stood in."""
        analyze = analyze or (lambda path, reading=None: {"file": os.path.basename(path), **CANNED})
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(self.m, "require_audio_deps"), \
                mock.patch.object(self.m, "analyze_file", side_effect=analyze), \
                mock.patch.object(sys, "argv", ["analyze_audio.py", *argv, "--tempo-source", "librosa"]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as exit_:
                self.m.main()
        return exit_.exception.code, out.getvalue(), err.getvalue()

    def test_single_file_archives_per_song_and_leaves_the_catalog_companion_alone(self):
        code, out, err = self.run_main(["docs/audio/band-a/Song.mp3"])
        self.assertEqual(code, 0)
        archive = self.archive / "songs" / "band-a" / "song-summary.json"
        self.assertEqual(json.loads(archive.read_text(encoding="utf-8")), json.loads(out))
        self.assertFalse(self.companion.exists())
        self.assertIn("ARCHIVED: ", err)
        self.assertNotIn("COMPANION: ", err)

    def test_catalog_root_run_writes_the_dated_archive_and_the_catalog_companion(self):
        code, out, err = self.run_main(["docs/audio"])
        self.assertEqual(code, 0)
        archives = sorted(p.name for p in (self.archive / "catalog").iterdir())
        self.assertEqual(len(archives), 1)
        self.assertRegex(archives[0], r"^\d{4}-\d\d-\d\d-summary\.json$")
        self.assertIn("band-a/Song.mp3", self.companion.read_text(encoding="utf-8"))
        self.assertIn("band-b/Other.wav", self.companion.read_text(encoding="utf-8"))  # .wav is measured too
        self.assertIn("ARCHIVED: ", err)
        self.assertIn("COMPANION: ", err)

    def test_band_folder_run_keeps_its_own_archive_and_companion(self):
        self.companion.write_text("catalog-wide summary\n", encoding="utf-8")
        code, _, err = self.run_main(["docs/audio/band-a"])
        self.assertEqual(code, 0)
        self.assertEqual(self.companion.read_text(encoding="utf-8"), "catalog-wide summary\n")
        own = self.root / "docs" / "audio-analysis-reference-band-a.md"
        self.assertIn("Song.mp3", own.read_text(encoding="utf-8"))
        archives = sorted(p.name for p in (self.archive / "catalog").iterdir())
        self.assertRegex(archives[0], r"^\d{4}-\d\d-\d\d-summary-band-a\.json$")
        self.assertIn(str(own.name), err)

    def test_no_archive_no_companion_writes_nothing(self):
        code, out, err = self.run_main(["docs/audio", "--no-archive", "--no-companion"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["status"], "pass")
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.companion.exists())
        self.assertNotIn("ARCHIVED", err)
        self.assertNotIn("COMPANION", err)

    def test_run_from_another_directory_writes_under_the_audios_project(self):
        elsewhere = self.root.parent / "elsewhere"
        elsewhere.mkdir()
        os.chdir(elsewhere)
        code, _, _ = self.run_main([str(self.audio)])
        self.assertEqual(code, 0)
        self.assertTrue(self.companion.exists())
        self.assertEqual(len(list((self.archive / "catalog").iterdir())), 1)
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_partial_run_exits_0_and_archives(self):
        def analyze(path, reading=None):
            if path.endswith("Other.wav"):
                return {"file": "Other.wav", "error": "boom"}
            return {"file": os.path.basename(path), **CANNED}

        code, out, _ = self.run_main(["docs/audio"], analyze)
        self.assertEqual((code, json.loads(out)["status"]), (0, "partial"))
        self.assertEqual(len(list((self.archive / "catalog").iterdir())), 1)

    def test_text_format_goes_to_the_output_file_in_a_new_folder(self):
        target = self.root / "reports" / "today" / "summary.txt"
        code, out, _ = self.run_main(["docs/audio", "--format", "text", "-o", str(target), "--no-archive",
                                      "--no-companion"])
        self.assertEqual((code, out), (0, ""))
        self.assertIn("Tracks analyzed: 2/2", target.read_text(encoding="utf-8"))

    def test_unwritable_output_fails_with_a_reason_and_archives_nothing(self):
        blocker = self.root / "blocker"
        blocker.write_text("a file, not a folder", encoding="utf-8")
        code, out, err = self.run_main(["docs/audio", "-o", str(blocker / "summary.json")])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["status"], "fail")
        self.assertIn("Cannot write", err)
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.companion.exists())


if __name__ == "__main__":
    unittest.main()
