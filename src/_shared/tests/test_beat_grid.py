#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for the shared beat_grid helper: its JSON hand-off to tempo_source, and what a run archives.

PyTorch and the Beat This! model are too heavy to provision in the suite, so a
stand-in tracker returns a known beat grid and a stand-in `librosa.load` returns
silence of a known length. Everything from there on is the real code: main(),
analyze_file, format_json, and tempo_source.run_beat_grid reading what main printed.
The pure beat maths (beat_stats, edge_bpms, format_text) is pinned in the feedback
elicitor's test_beat_grid.py.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent))
import beat_grid as bg  # noqa: E402
import json_archiver  # noqa: E402
import tempo_source as ts  # noqa: E402

SR = 22050
DURATION_S = 70
# A child Python whose default text encoding is ASCII, standing in for a platform
# whose default is not UTF-8 (Windows cp1252).
ASCII_LOCALE = {**os.environ, "LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}


def steady_grid(bpm=120.0, beats_per_bar=4, seconds=DURATION_S):
    """Stand-in for a loaded Beat This! model: a steady grid, whatever the audio."""
    step = 60.0 / bpm
    beats = [i * step for i in range(int(seconds / step))]
    return lambda y, sr: (beats, beats[::beats_per_bar])


def unreadable(y, sr):
    raise RuntimeError("could not decode audio")


FAKE_LIBROSA = types.SimpleNamespace(load=lambda path, sr=None, mono=True: (bytes(SR * DURATION_S), SR))
# Stand-in for the librosa comparison reading (tempo_source.librosa_tempo_pair needs real audio).
LIBROSA_PAIR = {"bpm_librosa": 240.0, "bpm_librosa_slow_prior": 120.0, "librosa_prior_relation": "double"}


class BeatGridCase(unittest.TestCase):
    """A temp project (a folder holding _bmad/) with one band's audio, and main() run in-process."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "project"
        (self.root / "_bmad").mkdir(parents=True)
        self.band = self.root / "docs" / "audio" / "my-band"
        self.band.mkdir(parents=True)
        self.song = self.band / "Song.mp3"
        self.song.write_bytes(b"")
        self.archive_root = self.root / "docs" / "audio-analysis"
        self.song_archive = self.archive_root / "songs" / "my-band" / "song-beat-grid.json"
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.root)
        patcher = mock.patch.object(json_archiver, "datetime")
        patcher.start().now.return_value = datetime(2026, 9, 12, tzinfo=timezone.utc)
        self.addCleanup(patcher.stop)

    def run_main(self, argv, tracker=None):
        """(exit code, stdout, stderr) of beat_grid.main() with the model and the audio decoder stood in."""
        tracker = tracker or steady_grid()
        inference = types.ModuleType("beat_this.inference")
        inference.Audio2Beats = lambda **kwargs: tracker
        package = types.ModuleType("beat_this")
        package.inference = inference
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(sys.modules, {"beat_this": package, "beat_this.inference": inference,
                                           "librosa": FAKE_LIBROSA}), \
                mock.patch.object(bg, "require_modules", lambda *a, **k: None), \
                mock.patch.object(bg, "resolve_device", lambda requested: "cpu"), \
                mock.patch.object(bg, "librosa_tempo_pair", lambda y, sr: dict(LIBROSA_PAIR)), \
                mock.patch.object(sys, "argv", ["beat_grid.py", *[str(a) for a in argv]]), \
                redirect_stdout(out), redirect_stderr(err), \
                self.assertRaises(SystemExit) as cm:
            bg.main()
        return cm.exception.code, out.getvalue(), err.getvalue()


class TestHandOffToTempoSource(BeatGridCase):
    """What beat_grid prints is what tempo_source.run_beat_grid (and six scripts through it) reads."""

    def test_analyze_file_reports_tempo_edges_and_beat_times(self):
        with mock.patch.dict(sys.modules, {"librosa": FAKE_LIBROSA}):
            r = bg.analyze_file(str(self.song), steady_grid(), with_librosa=False, include_beats=True)
        self.assertEqual(r["duration_s"], 70.0)
        self.assertEqual(r["bpm"], 120.0)
        self.assertEqual(r["entry_bpm"], 120.0)
        self.assertEqual(r["exit_bpm"], 120.0)
        self.assertEqual(r["beats_per_bar"], 4)
        self.assertEqual(r["bars_per_minute"], 30.0)
        self.assertEqual(r["n_beats"], 140)
        self.assertEqual(r["beats_s"][:3], [0.0, 0.5, 1.0])
        self.assertEqual(len(r["beats_s"]), 140)
        self.assertEqual(r["downbeats_s"][:3], [0.0, 2.0, 4.0])
        self.assertNotIn("librosa_bpm", r)

    def test_beat_times_are_left_out_unless_asked_for(self):
        with mock.patch.dict(sys.modules, {"librosa": FAKE_LIBROSA}):
            r = bg.analyze_file(str(self.song), steady_grid(), with_librosa=False)
        self.assertNotIn("beats_s", r)
        self.assertNotIn("downbeats_s", r)

    def test_format_json_carries_the_tracks_under_metrics(self):
        report = json.loads(json.dumps(bg.format_json([{"file": "a", "bpm": 120.0}], "cpu")))
        self.assertEqual(report["script"], "beat-grid")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["metrics"]["tracks"][0]["bpm"], 120.0)
        self.assertEqual(report["metrics"]["tracks_analyzed"], 1)
        self.assertEqual(report["metrics"]["device"], "cpu")

    def test_format_json_status_and_findings_follow_the_errors(self):
        good, bad = {"file": "a", "bpm": 120.0}, {"file": "b", "error": "RuntimeError: boom"}
        self.assertEqual(bg.format_json([good, bad], "cpu")["status"], "partial")
        failed = bg.format_json([bad], "cpu")
        self.assertEqual(failed["status"], "fail")
        self.assertEqual(failed["findings"], [{"file": "b", "level": "error", "message": "RuntimeError: boom"}])
        self.assertEqual(failed["metrics"]["tracks_errored"], 1)

    def run_beat_grid_against_main(self, paths, include_beats, tracker=None):
        """tempo_source.run_beat_grid, with beat_grid.main() run in-process in place of the `uv run` child."""
        calls = []

        def child(cmd, **kwargs):
            calls.append(cmd)
            code, out, _ = self.run_main(cmd[cmd.index(str(ts.BEAT_GRID)) + 1:], tracker)
            return subprocess.CompletedProcess(cmd, code, stdout=out)

        with mock.patch.object(ts.subprocess, "run", child):
            tracks = ts.run_beat_grid(paths, include_beats=include_beats)
        self.assertEqual(len(calls), 1)
        return tracks

    def test_run_beat_grid_reads_what_main_prints(self):
        tracks = self.run_beat_grid_against_main([self.song], include_beats=True)
        self.assertEqual(len(tracks), 1)
        reading = tracks[0]
        self.assertTrue(ts.usable(reading))
        self.assertEqual(reading["file"], "Song.mp3")
        self.assertEqual(reading["bpm"], 120.0)
        self.assertEqual(reading["entry_bpm"], 120.0)
        self.assertEqual(reading["exit_bpm"], 120.0)
        self.assertEqual(reading["beats_per_bar"], 4)
        self.assertEqual(reading["beats_s"][:3], [0.0, 0.5, 1.0])
        self.assertEqual(reading["downbeats_s"][:3], [0.0, 2.0, 4.0])
        self.assertNotIn("librosa_bpm", reading)

    def test_run_beat_grid_keeps_the_order_and_count_of_several_files(self):
        other = self.band / "Another.mp3"
        other.write_bytes(b"")
        tracks = self.run_beat_grid_against_main([self.song, other], include_beats=False)
        self.assertEqual([t["file"] for t in tracks], ["Song.mp3", "Another.mp3"])
        self.assertTrue(all(ts.usable(t) for t in tracks))
        self.assertNotIn("beats_s", tracks[0])

    def test_run_beat_grid_gets_error_rows_when_every_track_fails(self):
        tracks = self.run_beat_grid_against_main([self.song], include_beats=True, tracker=unreadable)
        self.assertEqual(len(tracks), 1)
        self.assertIn("could not decode audio", tracks[0]["error"])
        self.assertFalse(ts.usable(tracks[0]))

    def test_the_hand_off_never_writes_an_archive(self):
        self.run_beat_grid_against_main([self.song], include_beats=True)
        self.assertFalse(self.archive_root.exists())


class TestArchive(BeatGridCase):
    def test_single_file_archives_under_its_band(self):
        code, out, err = self.run_main([self.song])
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(json.loads(self.song_archive.read_text(encoding="utf-8")), report)
        self.assertIn("ARCHIVED", err)
        track = report["metrics"]["tracks"][0]
        self.assertEqual((track["bpm"], track["librosa_bpm"], track["tempo_relation"]), (120.0, 240.0, "librosa_double"))
        self.assertEqual((track["librosa_bpm_slow_prior"], track["librosa_prior_relation"]), (120.0, "double"))

    def test_all_failed_run_exits_1_and_leaves_a_good_archive_untouched(self):
        self.assertEqual(self.run_main([self.song])[0], 0)
        good = self.song_archive.read_bytes()
        code, out, err = self.run_main([self.song], unreadable)
        self.assertEqual(code, 1)
        self.assertEqual(self.song_archive.read_bytes(), good)
        report = json.loads(out)
        self.assertEqual(report["status"], "fail")
        self.assertIn("could not decode audio", report["metrics"]["tracks"][0]["error"])
        self.assertIn("nothing archived", err)
        self.assertNotIn("ARCHIVED", err)

    def test_all_failed_run_creates_no_archive(self):
        code, _, _ = self.run_main([self.song], unreadable)
        self.assertEqual(code, 1)
        self.assertFalse(self.archive_root.exists())

    def test_partial_run_still_archives_and_exits_0(self):
        (self.band / "Another.mp3").write_bytes(b"")
        seen = []

        def second_fails(y, sr):
            seen.append(1)
            if len(seen) == 2:
                raise RuntimeError("could not decode audio")
            return steady_grid()(y, sr)

        code, out, _ = self.run_main([self.band], second_fails)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["status"], "partial")
        archive = self.archive_root / "catalog" / "2026-09-12-beat-grid-my-band.json"
        self.assertEqual(json.loads(archive.read_text(encoding="utf-8"))["status"], "partial")

    def test_no_archive_flag_writes_nothing(self):
        code, _, err = self.run_main([self.song, "--no-archive"])
        self.assertEqual(code, 0)
        self.assertFalse(self.archive_root.exists())
        self.assertNotIn("ARCHIVED", err)

    def test_explicit_archive_path_is_used_as_given(self):
        target = self.root / "out" / "mine.json"
        code, out, _ = self.run_main([self.song, "--archive", target])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), json.loads(out))
        self.assertFalse(self.archive_root.exists())

    def test_band_folders_and_the_catalog_root_get_separate_dated_archives(self):
        other = self.root / "docs" / "audio" / "Other Band"
        other.mkdir()
        (other / "Tune.mp3").write_bytes(b"")
        for folder in (self.band, other, self.root / "docs" / "audio"):
            self.assertEqual(self.run_main([folder])[0], 0)
        catalog = self.archive_root / "catalog"
        self.assertEqual(sorted(p.name for p in catalog.iterdir()), [
            "2026-09-12-beat-grid-my-band.json",
            "2026-09-12-beat-grid-other-band.json",
            "2026-09-12-beat-grid.json",
        ])
        tracks = json.loads((catalog / "2026-09-12-beat-grid-my-band.json").read_text(encoding="utf-8"))["metrics"]["tracks"]
        self.assertEqual([t["file"] for t in tracks], ["Song.mp3"])

    def test_several_inputs_archive_as_one_dated_catalog_run(self):
        other = self.band / "Another.mp3"
        other.write_bytes(b"")
        self.assertEqual(self.run_main([self.song, other])[0], 0)
        self.assertEqual([p.name for p in (self.archive_root / "catalog").iterdir()], ["2026-09-12-beat-grid.json"])

    def test_run_from_another_directory_archives_under_the_audio_project(self):
        elsewhere = self.root.parent / "elsewhere"
        elsewhere.mkdir()
        os.chdir(elsewhere)
        code, _, err = self.run_main([self.song])
        self.assertEqual(code, 0)
        self.assertTrue(self.song_archive.is_file())
        self.assertIn(str(self.song_archive), err)
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_audio_outside_any_project_archives_under_the_working_directory(self):
        loose_dir = self.root.parent / "loose"
        loose_dir.mkdir()
        loose = loose_dir / "Loose.mp3"
        loose.write_bytes(b"")
        os.chdir(loose_dir)
        self.assertEqual(self.run_main([loose])[0], 0)
        self.assertTrue((loose_dir / "docs" / "audio-analysis" / "songs" / "loose-beat-grid.json").is_file())


class TestOutputFile(BeatGridCase):
    def test_input_and_usage_failures_print_the_failure_object_and_exit_1(self):
        # Exit 2 means "dependencies missing" to the prompts and to tempo_source, so a
        # bad flag or a missing input must not use it.
        for argv, reason in (
            (["--no-such-flag"], "usage:"),
            ([self.root / "docs" / "audio" / "absent.mp3"], "Not found:"),
            ([self.root / "_bmad"], "No audio files in"),
        ):
            with self.subTest(argv=argv):
                code, out, err = self.run_main(argv)
                self.assertEqual(code, 1)
                report = json.loads(out)
                self.assertEqual((report["script"], report["status"]), ("beat-grid", "fail"))
                self.assertIn(reason, report["error"])
                self.assertIn(reason, err)

    def test_text_output_file_holds_the_table(self):
        out_file = Path(os.environ.get("BEAT_GRID_TEST_OUT") or self.root / "table.txt")
        code, out, _ = self.run_main([self.song, "--format", "text", "-o", out_file, "--no-archive"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        table = out_file.read_bytes().decode("utf-8")
        self.assertIn("Song.mp3", table)
        self.assertIn("120.0→120.0", table)

    def test_text_output_file_is_utf8_whatever_the_platform_default(self):
        # The table holds an arrow; rerun the test above where the default text encoding is ASCII.
        out_file = self.root / "ascii-locale-table.txt"
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "test_beat_grid.TestOutputFile.test_text_output_file_holds_the_table"],
            cwd=TESTS, capture_output=True, text=True, env={**ASCII_LOCALE, "BEAT_GRID_TEST_OUT": str(out_file)},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("120.0→120.0", out_file.read_bytes().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
