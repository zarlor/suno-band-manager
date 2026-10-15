#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for _shared/tempo_source.py: Beat This! when opted in, librosa otherwise.

Pins the opt-in reading (BMad's TOML config layers, walked up from the
working directory), the --tempo-source override, and the beat-grid.py hand-off
and its fallbacks. A stand-in script plays beat-grid.py, so no PyTorch is needed.
"""

import argparse
import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parent.parent / "tempo_source.py"
sys.path.insert(0, str(SCRIPT.parent))  # tempo_source imports its sibling bmad_config
sys.path.insert(0, str(Path(__file__).parent))
from fake_resolver import install_resolver  # noqa: E402
spec = importlib.util.spec_from_file_location("tempo_source", SCRIPT)
ts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ts)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if path.suffix == ".toml" and "_bmad" in path.parts:
        install_resolver(path.parents[len(path.parts) - 1 - path.parts.index("_bmad")])


def patch_attr(case, target, name, value):
    """Patch target.name for the rest of the test (monkeypatch.setattr)."""
    patcher = mock.patch.object(target, name, value)
    patcher.start()
    case.addCleanup(patcher.stop)


def fake_beat_grid(case, tmp_path, body):
    script = tmp_path / "fake-beat-grid.py"
    script.write_text("import json, sys\n" + body)
    patch_attr(case, ts, "BEAT_GRID", script)
    patch_attr(case, ts.shutil, "which", lambda _name: None)  # run with sys.executable, not uv


class TmpPathTestCase(unittest.TestCase):
    """Gives each test a fresh temporary directory as self.tmp_path."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name).resolve()


class TestTempoSource(TmpPathTestCase):
    def test_flag_from_module_config(self):
        tmp_path = self.tmp_path
        write(tmp_path / "_bmad/config.toml", "[core]\noutput_folder = 'x'\n[modules.suno]\npytorch_audio_tools = 'on'\n")
        self.assertEqual(ts.read_config_flag(tmp_path), "on")
        self.assertTrue(ts.opted_in(tmp_path))

    def test_flag_reads_only_the_suno_table(self):
        tmp_path = self.tmp_path
        write(tmp_path / "_bmad/config.toml",
              "[core]\npytorch_audio_tools = 'on'\n[modules.other]\npytorch_audio_tools = 'on'\n"
              "[modules.suno]\nsuno_tier = 'pro'\npytorch_audio_tools = 'off'  # comment\n")
        self.assertEqual(ts.read_config_flag(tmp_path), "off")
        self.assertFalse(ts.opted_in(tmp_path))

    def test_custom_override_wins_and_toml_booleans_count(self):
        tmp_path = self.tmp_path
        write(tmp_path / "_bmad/config.toml", "[modules.suno]\npytorch_audio_tools = 'off'\n")
        write(tmp_path / "_bmad/custom/config.user.toml", "[modules.suno]\npytorch_audio_tools = true\n")
        self.assertTrue(ts.opted_in(tmp_path))

    def test_opt_in_found_from_a_subdirectory(self):
        tmp_path = self.tmp_path
        write(tmp_path / "_bmad/config.toml", "[modules.suno]\npytorch_audio_tools = 'yes'\n")
        sub = tmp_path / "docs" / "audio"
        sub.mkdir(parents=True)
        self.assertEqual(ts.resolve_tempo_source("auto", sub), "beat-this")

    def test_no_config_means_librosa(self):
        tmp_path = self.tmp_path
        self.assertTrue(ts.find_config_flag(tmp_path) is None or not ts.opted_in(tmp_path))
        write(tmp_path / "_bmad/config.toml", "[modules.suno]\nsuno_tier = 'pro'\n")
        self.assertIsNone(ts.read_config_flag(tmp_path))

    def test_broken_config_warns_and_uses_librosa(self):
        tmp_path = self.tmp_path
        write(tmp_path / "_bmad/config.toml", "[modules.suno\nbad")
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(ts.read_config_flag(tmp_path), "off")
        self.assertIn("unreadable", err.getvalue())

    def test_no_resolver_is_a_reasoned_warning(self):
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(ts.read_config_flag(tmp_path), "off")
        self.assertIn("bmad setup suno", err.getvalue())

    def test_legacy_yaml_config_is_not_read(self):
        tmp_path = self.tmp_path
        write(tmp_path / "_bmad/suno/config.yaml", "pytorch_audio_tools: 'on'\n")
        write(tmp_path / "_bmad/config.yaml", "suno:\n  pytorch_audio_tools: 'on'\n")
        install_resolver(tmp_path)
        self.assertIsNone(ts.read_config_flag(tmp_path))

    def test_explicit_source_overrides_config(self):
        tmp_path = self.tmp_path
        write(tmp_path / "_bmad/config.toml", "[modules.suno]\npytorch_audio_tools = 'on'\n")
        self.assertEqual(ts.resolve_tempo_source("librosa", tmp_path), "librosa")
        write(tmp_path / "_bmad/config.toml", "[modules.suno]\npytorch_audio_tools = 'off'\n")
        self.assertEqual(ts.resolve_tempo_source("auto", tmp_path), "librosa")
        self.assertEqual(ts.resolve_tempo_source("beat-this", tmp_path), "beat-this")

    def test_tempo_source_arg_defaults_to_auto(self):
        parser = argparse.ArgumentParser()
        ts.add_tempo_source_arg(parser)
        self.assertEqual(parser.parse_args([]).tempo_source, "auto")
        self.assertEqual(parser.parse_args(["--tempo-source", "librosa"]).tempo_source, "librosa")

    def test_run_beat_grid_passes_paths_in_order(self):
        tmp_path = self.tmp_path
        fake_beat_grid(self, tmp_path, (
            "paths = sys.argv[1:sys.argv.index('--no-librosa')]\n"
            "beats = '--include-beats' in sys.argv\n"
            "print(json.dumps({'metrics': {'tracks': [{'file': p, 'bpm': 100.0 + i, 'beats': beats}"
            " for i, p in enumerate(paths)]}}))\n"))
        tracks = ts.run_beat_grid(["a.mp3", "b.mp3"], include_beats=True)
        self.assertEqual([t["file"] for t in tracks], ["a.mp3", "b.mp3"])
        self.assertEqual(tracks[1]["bpm"], 101.0)
        self.assertIs(tracks[0]["beats"], True)

    def test_run_beat_grid_missing_dependencies_is_unavailable(self):
        tmp_path = self.tmp_path
        fake_beat_grid(self, tmp_path, "sys.exit(2)\n")
        with self.assertRaisesRegex(ts.BeatThisUnavailable, "not installed"):
            ts.run_beat_grid(["a.mp3"])

    def test_run_beat_grid_track_count_mismatch_is_unavailable(self):
        tmp_path = self.tmp_path
        fake_beat_grid(self, tmp_path, "print(json.dumps({'metrics': {'tracks': []}}))\n")
        with self.assertRaises(ts.BeatThisUnavailable):
            ts.run_beat_grid(["a.mp3"])

    def test_run_beat_grid_missing_script(self):
        tmp_path = self.tmp_path
        patch_attr(self, ts, "BEAT_GRID", tmp_path / "nope.py")
        with self.assertRaises(ts.BeatThisUnavailable):
            ts.run_beat_grid(["a.mp3"])
        self.assertEqual(ts.run_beat_grid([]), [])

    def test_readings_fall_back_to_librosa_with_a_note(self):
        tmp_path = self.tmp_path
        fake_beat_grid(self, tmp_path, "sys.exit(1)\n")
        log = io.StringIO()
        self.assertIsNone(ts.beat_this_readings(["a.mp3"], log=log))
        self.assertIn("using librosa", log.getvalue())

    def test_beat_grid_path_points_at_the_real_script(self):
        self.assertTrue(ts.BEAT_GRID.is_file())
        self.assertEqual(ts.BEAT_GRID.name, "beat-grid.py")

    def test_usable_and_source_summary(self):
        self.assertTrue(ts.usable({"bpm": 90.0}))
        self.assertFalse(ts.usable({"bpm": None}))
        self.assertFalse(ts.usable({"error": "x"}))
        self.assertFalse(ts.usable(None))
        self.assertEqual(ts.source_summary([{"tempo_source": "beat-this"}, {"tempo_source": "beat-this"}]), "beat-this")
        self.assertEqual(ts.source_summary([{"tempo_source": "beat-this"}, {}]), "mixed")
        self.assertEqual(ts.source_summary([{"tempo_source": "beat-this"}, {"error": "missing"}]), "beat-this")
        self.assertEqual(ts.source_summary([]), "librosa")
        self.assertEqual(set(ts.SOURCE_LABELS), {"beat-this", "librosa", "mixed"})

    def test_tempo_relation_labels(self):
        self.assertEqual(ts.tempo_relation(76.9, 152.0), "librosa_double")
        self.assertEqual(ts.tempo_relation(96.8, 97.5), "agree")
        self.assertIsNone(ts.tempo_relation(None, 120.0))

    def test_librosa_prior_relation_labels(self):
        # default ~2x slow: the halftime double-read the slow prior exists to expose
        self.assertEqual(ts.librosa_prior_relation(117.5, 60.1), "double")
        self.assertEqual(ts.librosa_prior_relation(152.0, 76.0), "double")
        self.assertEqual(ts.librosa_prior_relation(95.7, 95.7), "agree")
        self.assertEqual(ts.librosa_prior_relation(99.0, 96.0), "agree")       # within 5%
        self.assertEqual(ts.librosa_prior_relation(129.2, 89.1), "other")      # 1.45x: neither
        self.assertEqual(ts.librosa_prior_relation(107.7, 55.0), "double")     # a fast song halved by the prior still reads double
        self.assertEqual(ts.librosa_prior_relation(130.0, 60.0), "other")      # 2.17x: outside the 5% band
        self.assertEqual(ts.librosa_prior_relation(60.0, 120.0), "other")      # slow above default isn't 'double'
        self.assertIsNone(ts.librosa_prior_relation(None, 60.0))
        self.assertIsNone(ts.librosa_prior_relation(120.0, 0))
        self.assertEqual(ts.librosa_prior_relation(130.0, 60.0, tolerance=0.1), "double")

    def test_librosa_tempo_pair_reuses_the_default_and_runs_the_slow_prior(self):
        calls = []

        def fake_bpm(y, sr, **kwargs):
            calls.append(kwargs)
            return 60.1 if kwargs.get("start_bpm") == ts.SLOW_PRIOR_BPM else 117.5

        patch_attr(self, ts, "_librosa_bpm", fake_bpm)
        self.assertEqual(ts.librosa_tempo_pair(None, 22050), {
            "bpm_librosa": 117.5, "bpm_librosa_slow_prior": 60.1, "librosa_prior_relation": "double"})
        self.assertEqual(calls, [{}, {"start_bpm": 80}])
        calls.clear()
        pair = ts.librosa_tempo_pair(None, 22050, default_bpm=117.4876)
        self.assertEqual(pair["bpm_librosa"], 117.5)
        self.assertEqual(calls, [{"start_bpm": 80}])

    def test_halftime_note_and_slow_prior_fields(self):
        double = {"bpm_librosa": 117.5, "bpm_librosa_slow_prior": 60.1, "librosa_prior_relation": "double"}
        note = ts.halftime_note(double)
        self.assertIn("117.5", note)
        self.assertIn("60.1", note)
        self.assertIn("halftime", note)
        self.assertIsNone(ts.halftime_note({**double, "librosa_prior_relation": "agree"}))
        self.assertIsNone(ts.halftime_note(None))
        patch_attr(self, ts, "_librosa_bpm", lambda y, sr, **kw: 60.1)
        fields = ts.slow_prior_fields(None, 22050, 117.5)
        self.assertEqual(fields, {"bpm_librosa_slow_prior": 60.1, "librosa_prior_relation": "double", "tempo_note": note})
        self.assertNotIn("tempo_note", ts.slow_prior_fields(None, 22050, 60.0))

    def test_bpm_cell(self):
        self.assertEqual(ts.bpm_cell(117.5, 60.1, "double"), "117.5 / 60.1 (halftime?)")
        self.assertEqual(ts.bpm_cell(129.2, 89.1, "other"), "129.2 / 89.1")
        self.assertEqual(ts.bpm_cell(95.7, 95.7, "agree"), "95.7")
        self.assertEqual(ts.bpm_cell(76.9), "76.9")


def steady_beats(bpm, start, end):
    ibi = 60.0 / bpm
    n = int((end - start) / ibi)
    return [start + i * ibi for i in range(n)]


class TestWindowedTempo(unittest.TestCase):
    def test_window_tempos_ignore_a_stray_beat(self):
        beats = steady_beats(120, 0, 30)
        beats.insert(10, beats[9] + 0.1)  # one stray detection
        windows = ts.window_tempos(beats)
        self.assertEqual([w["bpm"] for w in windows], [120.0, 120.0])
        self.assertEqual(windows[0]["start"], 0.0)
        self.assertLessEqual(windows[1]["end"], 30.0)

    def test_windowed_stability_labels(self):
        steady = [{"start": 0, "end": 15, "bpm": 200.0}, {"start": 15, "end": 30, "bpm": 201.0}]
        self.assertEqual(ts.windowed_stability(steady), ("steady", (200, 201)))
        slight = steady + [{"start": 30, "end": 45, "bpm": 212.0}]
        self.assertEqual(ts.windowed_stability(slight)[0], "slight variation")
        halftime = steady + [{"start": 30, "end": 45, "bpm": 100.0}]
        self.assertEqual(ts.windowed_stability(halftime), ("TEMPO CHANGES", (100, 201)))
        self.assertEqual(ts.windowed_stability([]), ("too few beats", (0, 0)))

    def test_feel_sections_name_and_merge_runs(self):
        beats = steady_beats(125, 0, 120) + steady_beats(64, 120, 150) + steady_beats(125, 150, 195)
        windows = ts.window_tempos(beats)
        sections = ts.feel_sections(windows, 125.0)
        self.assertEqual(len(sections), 1)
        f = sections[0]
        self.assertEqual(f["feel"], "half-time")
        self.assertEqual(f["start"], 120.0)
        self.assertEqual(f["end"], 150.0)
        self.assertLess(abs(f["bpm"] - 64), 1)

    def test_feel_sections_labels(self):
        windows = [{"start": 0.0, "end": 15.0, "bpm": 231.0}, {"start": 15.0, "end": 30.0, "bpm": 115.0},
                   {"start": 30.0, "end": 45.0, "bpm": 172.0}, {"start": 45.0, "end": 60.0, "bpm": 150.0}]
        feels = [f["feel"] for f in ts.feel_sections(windows, 115.0)]
        self.assertEqual(feels, ["double-time", "triplet grid", "shift"])
        self.assertEqual(ts.feel_sections(windows, None), [])


if __name__ == "__main__":
    unittest.main()
