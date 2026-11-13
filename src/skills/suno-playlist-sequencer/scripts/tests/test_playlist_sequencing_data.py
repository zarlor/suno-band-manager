#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for playlist_sequencing_data.py, the data layer of the suno-playlist-sequencer workflow.

Three groups:
  - the exit-code contract of the real script, run with `uv run` so its own
    dependencies are provisioned (skipped without uv): each failure exits 1 with
    a JSON `error` on stdout, never a crash and never the dependency exit 2;
  - the seam math, the report and the compare, on dicts in analyze_track's shape;
  - main() end to end: with analyze_track stood in for the guards and artifacts,
    and once with the real analyze_track on synthesized audio, so its return
    shape is checked against the report builder (skipped without librosa).
"""

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

SCRIPT = str(Path(__file__).parent.parent / "playlist_sequencing_data.py")
UV = shutil.which("uv")
TIMEOUT = 600
HAVE_AUDIO_LIBS = all(importlib.util.find_spec(n) for n in ("librosa", "numpy"))
HAVE_PYLOUDNORM = importlib.util.find_spec("pyloudnorm") is not None


def run_uv(args: list[str], cwd=None):
    """(exit code, stdout) of the real script under `uv run`."""
    proc = subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT, cwd=cwd)
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


def load_module():
    spec = importlib.util.spec_from_file_location("playlist_sequencing_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_module():
    spec = importlib.util.spec_from_file_location("playlist_sequencing_data", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _track(name, bpm, entry, exit_, thirds):
    return {"name": name, "duration": 200.0, "bpm": bpm, "overall_key": "A minor", "overall_conf": 0.8,
            "overall_camelot": "8A", "entry_key": "A minor", "entry_conf": 0.8, "entry_camelot": entry,
            "exit_key": "A minor", "exit_conf": 0.8, "exit_camelot": exit_, "energy_level": 6,
            "intro_energy_pct": 40, "outro_energy_pct": 70,
            "loudness": {"integrated_lufs": -13.2, "lra_lu": 5.1, "thirds_lufs": thirds, "build_lu": 2.0}}


def _report(m, tracks):
    m.compute_transitions(tracks)
    return m.build_report("Album", tracks)


@unittest.skipIf(UV is None, "uv not available to provision librosa deps")
class TestPlaylistSequencingData(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def test_missing_dir_exits_1_with_the_reason(self):
        code, out = run_uv(["--audio-dir", "/nonexistent-audio-dir-xyz"])
        self.assertEqual(code, 1)  # not 2 (dependencies missing), and not a crash without JSON
        report = json.loads(out)
        self.assertEqual((report["script"], report["status"]), ("playlist-sequencing-data", "fail"))
        self.assertIn("Audio directory not found: /nonexistent-audio-dir-xyz", report["error"])

    def test_folder_without_audio_exits_1_with_the_reason(self):
        (self.tmp_path / "notes.txt").write_text("x", encoding="utf-8")
        code, out = run_uv(["--audio-dir", str(self.tmp_path)])
        self.assertEqual(code, 1)
        report = json.loads(out)
        self.assertEqual(report["status"], "fail")
        self.assertIn("No tracks found", report["error"])

    def test_missing_playlist_exits_1_with_the_reason(self):
        code, out = run_uv(["--playlist", str(self.tmp_path / "nope-playlist.yaml")])
        self.assertEqual(code, 1)
        self.assertIn("Playlist config not found", json.loads(out)["error"])

    def test_usage_error_exits_1_with_the_error_object_not_2(self):
        # Exit 2 means the audio dependencies are missing; a mistyped flag must not read as that.
        for args in (["--no-such-flag"], ["--format", "yaml"]):
            code, out = run_uv(args)
            self.assertEqual(code, 1, args)
            report = json.loads(out)
            self.assertEqual(report["status"], "fail")
            self.assertTrue(report["error"].startswith("usage: "), report["error"])
        self.assertEqual(run_uv(["--help"])[0], 0)

    def test_resolve_audio_dir_precedence(self):
        m = load_module()
        self.enterContext(contextlib.chdir(self.tmp_path))
        playlist = "docs/band-a-playlist.yaml"
        self.assertEqual(m.resolve_audio_dir("cli/dir", playlist, "yaml/dir"), "cli/dir")
        self.assertEqual(m.resolve_audio_dir(None, playlist, "docs/audio/custom"), "docs/audio/custom")
        # No band folder on disk yet: fall back to the legacy flat docs/audio.
        self.assertEqual(m.resolve_audio_dir(None, playlist), "docs/audio")
        (self.tmp_path / "docs" / "audio" / "band-a").mkdir(parents=True)
        self.assertEqual(m.resolve_audio_dir(None, playlist), os.path.join("docs/audio", "band-a"))
        self.assertEqual(m.resolve_audio_dir(None), "docs/audio")

    def test_relative_yaml_audio_dir_resolves_from_the_project_root(self):
        m = load_module()
        playlist = "docs/band-a-playlist.yaml"
        self.assertEqual(m.resolve_audio_dir(None, playlist, "docs/audio/custom", "/proj"),
                         os.path.join("/proj", "docs/audio/custom"))
        self.assertEqual(m.resolve_audio_dir(None, playlist, "/abs/audio", "/proj"), "/abs/audio")
        self.assertEqual(m.resolve_audio_dir(None, playlist, "docs/audio/custom", "."), "docs/audio/custom")
        self.assertEqual(m.resolve_audio_dir("cli/dir", playlist, "docs/audio/custom", "/proj"), "cli/dir")
        self.assertEqual(m.resolve_audio_dir(None, project_root="/proj"), os.path.join("/proj", "docs", "audio"))

    def test_data_root_follows_the_audio_not_the_working_directory(self):
        m = load_module()
        j = os.path.join
        self.assertEqual(m.data_root("music/band-a-playlist.yaml", "anything"), "music")
        self.assertEqual(m.data_root(None, j("proj", "docs", "audio")), j("proj", "docs"))
        self.assertEqual(m.data_root(None, j("proj", "docs", "audio", "band-a")), j("proj", "docs"))
        self.assertEqual(m.data_root(None, j("proj", "docs", "audio", "band-a", "album-1")), j("proj", "docs"))
        self.assertEqual(m.data_root(None, j("elsewhere", "renders")), "elsewhere")

    def test_load_playlist_names_the_album_after_the_file_when_album_is_missing(self):
        m = load_module()
        p = self.tmp_path / "band-b-playlist.yaml"
        p.write_text('tracks:\n  - name: "A"\n    file: "A.mp3"\n', encoding="utf-8")
        self.assertEqual(m.load_playlist(str(p))[0], "band-b")
        self.assertEqual(m.archive_default("band-b", "docs"), os.path.join("docs", "audio-analysis", "playlists", "band-b.json"))

    def test_duplicate_track_names_are_refused(self):
        m = load_module()
        p = self.tmp_path / "x-playlist.yaml"
        p.write_text('album: X\ntracks:\n  - name: A\n    file: A.mp3\n  - name: B\n    file: B.mp3\n'
                     '  - name: "A "\n    file: A2.mp3\n', encoding="utf-8")
        with self.assertRaises(m.PlaylistError) as caught:
            m.read_playlist(str(p))
        self.assertIn("duplicate track name", str(caught.exception))
        self.assertIn("'A' (tracks 1 and 3)", str(caught.exception))

    def test_load_playlist_returns_yaml_audio_dir(self):
        m = load_module()
        p = self.tmp_path / "x-playlist.yaml"
        p.write_text('album: "X"\naudio_dir: "docs/audio/x"\ntracks:\n  - name: "A"\n    file: "A.mp3"\n')
        album, tracks, audio_dir = m.load_playlist(str(p))
        self.assertEqual((album, tracks, audio_dir), ("X", [("A", "A.mp3")], "docs/audio/x"))

    def test_discover_tracks_recurses_band_folders(self):
        m = load_module()
        (self.tmp_path / "band-a").mkdir()
        (self.tmp_path / "band-a" / "Song.mp3").write_bytes(b"x")
        (self.tmp_path / "Loose.mp3").write_bytes(b"x")
        (self.tmp_path / "notes.txt").write_text("x")
        _, tracks = m.discover_tracks(str(self.tmp_path))
        self.assertEqual(tracks, [("Loose", "Loose.mp3"), ("Song", "band-a/Song.mp3")])

    def test_discover_tracks_takes_every_audio_type_in_any_case(self):
        m = load_module()
        for name in ("Render.wav", "LOUD.MP3", "Master.FLAC", "demo.ogg", "phone.m4a", "cover.jpg", "notes.mp3.txt"):
            (self.tmp_path / name).write_bytes(b"x")
        _, tracks = m.discover_tracks(str(self.tmp_path))
        self.assertEqual(tracks, [("LOUD", "LOUD.MP3"), ("Master", "Master.FLAC"), ("Render", "Render.wav"),
                                  ("demo", "demo.ogg"), ("phone", "phone.m4a")])

    def test_discovered_names_stay_unique(self):
        m = load_module()
        for rel in ("band-a/Song.mp3", "band-b/Song.mp3", "Twice.mp3", "Twice.wav", "Solo.mp3"):
            (self.tmp_path / rel).parent.mkdir(exist_ok=True)
            (self.tmp_path / rel).write_bytes(b"x")
        _, tracks = m.discover_tracks(str(self.tmp_path))
        self.assertEqual(tracks, [("Solo", "Solo.mp3"), ("Twice.mp3", "Twice.mp3"), ("Twice.wav", "Twice.wav"),
                                  ("band-a/Song", "band-a/Song.mp3"), ("band-b/Song", "band-b/Song.mp3")])
        self.assertEqual(len({name for name, _ in tracks}), len(tracks))

    def test_transitions_carry_loudness_seam(self):
        m = _load_module()
        results = [_track("Loud End", 120.0, "8A", "8A", [-15.0, -13.0, -10.0]),
                   _track("Quiet Open", 122.0, "8A", "9A", [-19.0, -14.0, -12.0]),
                   {"name": "Missing", "error": "file not found"}]
        m.compute_transitions(results)
        t = results[0]["transition"]
        self.assertEqual(t["loudness_step_lu"], -9.0)
        self.assertEqual(t["loudness_quality"], "big jump (quieter)")
        self.assertEqual(t["key_compat"], "compatible")
        self.assertEqual(t["key_relation"], "same")
        self.assertEqual(t["bpm_quality"], "smooth")
        self.assertNotIn("key_quality", t)  # no single-variable field reads as the seam's verdict
        self.assertNotIn("transition", results[1])  # successor errored
        text = m.format_text("Album", results)
        self.assertIn("| LUFS | LUFS in→out | LRA |", text)
        self.assertIn("-9.0 LU (big jump (quieter))", text)
        data = __import__("json").loads(m.format_json("Album", results))
        self.assertEqual(data["tracks"][0]["loudness"]["thirds_lufs"], [-15.0, -13.0, -10.0])
        self.assertEqual(data["tracks"][0]["transition_to_next"]["loudness_step_lu"], -9.0)

    def test_transition_without_loudness_data_is_tolerated(self):
        m = _load_module()
        a, b = _track("A", 100.0, "8A", "8A", [-14, -14, -14]), _track("B", 100.0, "8A", "8A", [-14, -14, -14])
        a.pop("loudness")
        t = m.transition_between(a, b)
        self.assertIsNone(t["loudness_step_lu"])
        self.assertIsNone(t["loudness_quality"])

    def test_transition_uses_exit_entry_tempo_and_loudness(self):
        m = _load_module()
        a = _track("Fast Out", 120.0, "8A", "8A", [-15.0, -13.0, -10.0])
        b = _track("Slow In", 118.0, "8A", "8A", [-19.0, -14.0, -12.0])
        a.update(entry_bpm=118.0, exit_bpm=150.0); b.update(entry_bpm=75.0, exit_bpm=118.0)
        a["loudness"]["exit_lufs"] = -9.0; b["loudness"]["entry_lufs"] = -24.0
        t = m.transition_between(a, b)
        self.assertEqual(t["bpm_basis"], "exit/entry")
        self.assertEqual(t["bpm_from"], 150.0)
        self.assertEqual(t["bpm_to"], 75.0)
        self.assertEqual(t["bpm_change"], 75.0)
        self.assertTrue(t["bpm_quality"].startswith("jump"))
        self.assertEqual(t["loudness_step_lu"], -15.0)
        text = m.format_text("Album", [a, b])
        self.assertIn("BPM in→out", text)
        self.assertIn("118.0→150.0", text)
        self.assertIn("LUFS in→out", text)

    def test_tempo_labels_change_at_3_and_6_percent(self):
        m = _load_module()

        def label(exit_bpm, entry_bpm):
            a, b = _track("A", exit_bpm, "8A", "8A", [-14] * 3), _track("B", entry_bpm, "8A", "8A", [-14] * 3)
            a.update(entry_bpm=exit_bpm, exit_bpm=exit_bpm); b.update(entry_bpm=entry_bpm, exit_bpm=entry_bpm)
            return m.transition_between(a, b)["bpm_quality"]

        self.assertEqual([label(100.0, to) for to in (102.9, 103.1, 105.9, 106.1)],
                         ["smooth", "ok", "ok", "jump (6%)"])
        self.assertEqual(label(121.0, 72.0), "jump (40%)")
        self.assertEqual(label(100.0, 97.1), "smooth")  # the change is measured either way
        self.assertEqual(label(100.0, 93.9), "jump (6%)")

    def test_a_tempo_that_read_zero_is_unknown_never_smooth(self):
        m = _load_module()
        a, b = _track("Drone", 0.0, "8A", "8A", [-14] * 3), _track("Next", 150.0, "8A", "8A", [-14] * 3)
        a.update(entry_bpm=0.0, exit_bpm=0.0); b.update(entry_bpm=150.0, exit_bpm=150.0)
        t = m.transition_between(a, b)
        self.assertEqual((t["bpm_quality"], t["pulse_pair"]), ("unknown", False))
        self.assertEqual(m.transition_between(b, a)["bpm_quality"], "unknown")
        self.assertIn("(unknown)", m.format_text("Album", [a, b]))
        # compare treats the label as neither better nor worse than a measured one
        self.assertEqual(m._seam_labels(t)["bpm_quality"], "unknown")

    def test_camelot_wheel_wraps_from_12_to_1(self):
        m = _load_module()
        d = m.camelot_distance
        self.assertEqual(d("12A", "1A"), 1)
        self.assertEqual(d("1B", "12B"), 1)
        self.assertEqual(d("11A", "1A"), 2)
        self.assertEqual(d("12B", "1A"), 1.5)
        self.assertEqual(d("12A", "12B"), 0.5)
        self.assertEqual(d("7A", "1A"), 6.5)  # opposite side: the farthest two keys can be
        self.assertEqual(m.key_relation("C# minor", "G# minor", d("12A", "1A")), "adjacent")
        self.assertEqual(m.key_relation("E major", "B major", d(m.get_camelot("E major"), m.get_camelot("B major"))),
                         "adjacent")
        self.assertEqual(m.key_compat(d("12B", "1B")), "compatible")
        self.assertEqual(d("??", "1A"), -1)

    def test_camelot_table_is_the_circle_of_fifths(self):
        m = _load_module()
        pcs = m.PITCH_CLASSES
        self.assertEqual(m.get_camelot("C major"), "8B")  # the anchor every other code is checked from
        self.assertEqual(m.get_camelot("H major"), "??")
        codes = set()
        for i, tonic in enumerate(pcs):
            major, minor = m.get_camelot(f"{tonic} major"), m.get_camelot(f"{pcs[(i + 9) % 12]} minor")
            self.assertRegex(major, r"^(1[0-2]|[1-9])B$", tonic)
            self.assertEqual(minor, major[:-1] + "A", f"{tonic} major and its relative minor share a number")
            fifth_up = m.get_camelot(f"{pcs[(i + 7) % 12]} major")
            self.assertEqual(int(fifth_up[:-1]), int(major[:-1]) % 12 + 1, f"a fifth above {tonic} major is one step on")
            codes.update((major, minor))
        self.assertEqual(len(codes), 24)  # every key has its own code
        for flat, sharp in m.FLAT_TO_SHARP.items():
            for mode in ("major", "minor"):
                if f"{flat} {mode}" in m.CAMELOT:
                    self.assertEqual(m.get_camelot(f"{flat} {mode}"), m.get_camelot(f"{sharp} {mode}"), f"{flat} {mode}")

    def test_tempo_source_reported_in_json_and_text(self):
        import json
        m = _load_module()
        a = _track("A", 76.9, "8A", "8A", [-14, -14, -14])
        b = _track("B", 96.8, "8A", "8A", [-14, -14, -14])
        a["tempo_source"] = b["tempo_source"] = "beat-this"
        data = json.loads(m.format_json("Album", [a, b]))
        self.assertEqual(data["tempo_source"], "beat-this")
        self.assertEqual(data["tracks"][0]["tempo_source"], "beat-this")
        self.assertIn("Tempo: Beat This!", m.format_text("Album", [a, b]))
        b["tempo_source"] = "librosa"
        self.assertEqual(json.loads(m.format_json("Album", [a, b]))["tempo_source"], "mixed")
        a.pop("tempo_source"); b.pop("tempo_source")
        self.assertIn("Tempo: librosa.", m.format_text("Album", [a, b]))

    def test_key_relation_names_parallel_and_relative(self):
        m = _load_module()
        d = m.camelot_distance
        self.assertEqual(m.key_relation("A minor", "A major", d("8A", "11B")), "parallel")
        self.assertEqual(m.key_compat(d("8A", "11B")), "distant")  # the wheel alone would hide the pivot
        self.assertEqual(m.key_relation("Eb minor", "D# major", d("2A", "5B")), "parallel")  # enharmonic tonic
        self.assertEqual(m.key_relation("A minor", "C major", d("8A", "8B")), "relative")
        self.assertEqual(m.key_relation("A minor", "E minor", d("8A", "9A")), "adjacent")
        self.assertEqual(m.key_relation("A minor", "B minor", d("8A", "10A")), "two-step")
        self.assertEqual(m.key_relation("A minor", "F# major", d("8A", "2B")), "distant")
        self.assertEqual(m.key_relation("Unknown", "A minor", -1), "unknown")
        self.assertEqual(m.key_compat(-1), "unknown")

    def test_dropped_tracks_reported_and_not_counted_as_analyzed(self):
        m = _load_module()
        tracks = [_track("A", 100.0, "8A", "8A", [-14] * 3),
                  {"name": "Gone", "file": "Gone.mp3", "error": "missing audio file"},
                  _track("B", 100.0, "8A", "8A", [-14] * 3),
                  {"name": "Bad", "file": "Bad.mp3", "error": "analysis error: boom"}]
        data = _report(m, tracks)
        self.assertEqual(data["track_count"], 4)
        self.assertEqual(data["analyzed_count"], 2)
        self.assertEqual(data["dropped"], [
            {"position": 2, "name": "Gone", "file": "Gone.mp3", "reason": "missing audio file"},
            {"position": 4, "name": "Bad", "file": "Bad.mp3", "reason": "analysis error: boom"}])

    def test_felt_bpm_folds_half_time_read_and_flags(self):
        m = _load_module()
        a = _track("Doom", 144.0, "8A", "8A", [-14] * 3)
        b = _track("Ballad", 74.0, "8A", "8A", [-14] * 3)
        a.update(entry_bpm=144.0, exit_bpm=146.0); b.update(entry_bpm=74.0, exit_bpm=74.0)
        t = m.transition_between(a, b)
        self.assertIs(t["pulse_pair"], True)
        self.assertTrue(t["bpm_quality"].startswith("jump"))
        a["felt_bpm"] = 72.0
        t = m.transition_between(a, b)
        self.assertEqual(t["bpm_from"], 73.0)
        self.assertEqual(t["bpm_basis"], "exit/entry+felt")
        self.assertEqual(t["bpm_quality"], "smooth")
        self.assertIs(t["pulse_pair"], False)
        data = _report(m, [a, b])
        self.assertIs(data["tracks"][0]["felt_bpm_check"], False)  # ear verdict recorded
        self.assertIs(data["tracks"][1]["felt_bpm_check"], True)  # 74 is in the 70-100 danger range

    def test_librosa_slow_prior_reported_and_feeds_felt_check(self):
        import json
        m = _load_module()
        a = _track("Slow Burn", 117.5, "8A", "8A", [-14] * 3)    # 117.5 is outside both danger ranges
        b = _track("Mid", 110.0, "8A", "8A", [-14] * 3)
        c = _track("Agreed", 110.0, "8A", "8A", [-14] * 3)
        a.update(tempo_source="librosa", bpm_librosa_slow_prior=60.1, librosa_prior_relation="double")
        c.update(tempo_source="librosa", bpm_librosa_slow_prior=110.0, librosa_prior_relation="agree")
        data = json.loads(m.format_json("Album", [a, b, c]))
        t0, t1, t2 = data["tracks"]
        self.assertEqual(t0["bpm"], 117.5)
        self.assertEqual(t0["bpm_librosa_slow_prior"], 60.1)
        self.assertEqual(t0["librosa_prior_relation"], "double")
        self.assertIs(t0["felt_bpm_check"], True)  # the double flags it even outside the danger ranges
        self.assertIsNone(t1["bpm_librosa_slow_prior"])
        self.assertIs(t1["felt_bpm_check"], False)
        self.assertIs(t2["felt_bpm_check"], False)
        self.assertIs(m.needs_felt_check(117.5, 60.0, "double"), False)  # the ear's verdict settles it
        self.assertIs(m.needs_felt_check(117.5, None), False)
        self.assertIs(m.needs_felt_check(74.0, None), True)
        text = m.format_text("Album", [a, b, c])
        self.assertIn("| 117.5 / 60.1 (halftime?) |", text)
        self.assertIn("| 110.0 |", text)
        self.assertIn("start_bpm=80", text)
        self.assertNotIn("start_bpm=80", m.format_text("Album", [b, c]))  # no footnote when nothing differs

    def test_load_felt_bpm(self):
        m = _load_module()
        p = self.tmp_path / "x-playlist.yaml"
        p.write_text('album: X\ntracks:\n  - name: A\n    file: A.mp3\n    felt_bpm: 72\n  - name: B\n    file: B.mp3\n')
        self.assertEqual(m.load_felt_bpm(str(p)), {"A": 72.0})

    def test_a_felt_bpm_that_is_not_a_positive_number_is_named_not_dropped_silently(self):
        m = _load_module()
        tracks = [{"name": "A", "felt_bpm": 72}, {"name": "B", "felt_bpm": "84"}, {"name": "C", "felt_bpm": 0},
                  {"name": "D", "felt_bpm": -90}, {"name": "E", "felt_bpm": True}, {"name": "F"},
                  {"name": "G", "felt_bpm": 66.5}]
        felt, ignored = m.split_felt_bpm(tracks)
        self.assertEqual(felt, {"A": 72.0, "G": 66.5})
        self.assertEqual(ignored, [{"name": n, "value": v, "reason": "not a positive number"}
                                   for n, v in (("B", "84"), ("C", 0), ("D", -90), ("E", True))])
        self.assertIsNone(m.octave_correct(None, 72.0))

    def test_runs_same_key_and_tempo_buckets(self):
        m = _load_module()
        tracks = [_track(n, bpm, "8A", "8A", [-14] * 3) for n, bpm in
                  (("A", 80.0), ("B", 82.0), ("C", 130.0), ("D", 131.0), ("E", 132.0))]
        tracks[4]["overall_camelot"] = "9A"
        runs = m.find_runs(tracks)
        self.assertIn({"kind": "same-key", "value": "8A", "tracks": ["A", "B", "C", "D"]}, runs)
        self.assertIn({"kind": "tempo", "value": "slow", "tracks": ["A", "B"], "felt_verified": False}, runs)
        self.assertIn({"kind": "tempo", "value": "up", "tracks": ["C", "D", "E"], "felt_verified": False}, runs)
        tracks[2] = {"name": "C", "error": "missing audio file"}  # a drop breaks a run
        self.assertFalse([r for r in m.find_runs(tracks) if r["kind"] == "same-key"])

    def test_compare_reports_what_moved(self):
        import copy
        m = _load_module()
        before = [_track("A", 100.0, "8A", "8A", [-14] * 3), _track("B", 100.0, "8A", "8A", [-14] * 3),
                  _track("C", 100.0, "8A", "8A", [-14] * 3)]
        after = copy.deepcopy(before)
        after[1].update(bpm=140.0, exit_camelot="3B", exit_key="C# major")  # regen moved B
        prior, current = _report(m, before), _report(m, after)
        diff = m.compare_runs(prior, current)
        self.assertEqual(diff["track_changes"], [{"name": "B", "changes": {"bpm": [100.0, 140.0], "exit_camelot": ["8A", "3B"]}}])
        self.assertEqual(diff["unchanged_tracks"], 2)
        self.assertFalse(diff["reordered"])
        seams = {(s["from"], s["to"]): s for s in diff["seam_changes"]}
        self.assertEqual(seams[("A", "B")]["direction"], "worse")
        self.assertIn("bpm_quality", seams[("A", "B")]["changes"])
        self.assertEqual(seams[("B", "C")]["direction"], "worse")
        self.assertEqual(seams[("B", "C")]["changes"]["key_compat"], ["compatible", "distant"])
        same = m.compare_runs(current, current)
        self.assertEqual(same["track_changes"], [])
        self.assertEqual(same["seam_changes"], [])

    def test_compare_reads_legacy_key_quality_and_reorders(self):
        m = _load_module()
        prior = {"tracks": [
            {"name": "A", "position": 1, "bpm": 100.0, "transition_to_next": {"to": "B", "key_quality": "PERFECT",
                                                                               "bpm_quality": "smooth"}},
            {"name": "B", "position": 2, "bpm": 100.0}]}
        current = _report(m, [_track("B", 100.0, "8A", "8A", [-14] * 3), _track("A", 100.0, "8A", "8A", [-14] * 3),
                              _track("New", 100.0, "8A", "8A", [-14] * 3)])
        diff = m.compare_runs(prior, current)
        self.assertTrue(diff["reordered"])
        self.assertEqual(diff["added_tracks"], ["New"])
        self.assertEqual(diff["removed_tracks"], [])
        self.assertIn({"from": "B", "to": "A"}, diff["new_seams"])
        self.assertEqual(m._seam_labels(prior["tracks"][0]["transition_to_next"])["key_compat"], "compatible")

    def test_compare_reads_prior_before_archive_overwrite(self):
        """Re-eval regression: the run must compare against the PRIOR archive, not itself."""
        import json
        m = _load_module()
        self.enterContext(contextlib.chdir(self.tmp_path))
        audio = self.tmp_path / "docs" / "audio" / "band-a"
        audio.mkdir(parents=True)
        for n in ("A", "B"):
            (audio / f"{n}.mp3").write_bytes(b"x")
        (self.tmp_path / "docs" / "band-a-playlist.yaml").write_text(
            'album: "Band A"\ntracks:\n  - name: A\n    file: A.mp3\n  - name: B\n    file: B.mp3\n')
        bpms = iter([100.0, 100.0, 120.0, 100.0])  # run 1: A=100, B=100; run 2: A=120
        self.enterContext(mock.patch.object(
            m, "analyze_track", lambda path, reading=None: _track("x", next(bpms), "8A", "8A", [-14] * 3)))
        self.enterContext(mock.patch.object(m, "require_audio_deps", lambda **kw: None))
        self.enterContext(mock.patch.dict(sys.modules, {"librosa": type(sys)("librosa"),
                                                        "numpy": type(sys)("numpy")}))
        argv = ["x", "--playlist", "docs/band-a-playlist.yaml", "--no-companion", "--tempo-source", "librosa",
                "-o", "out.json"]
        self.enterContext(mock.patch.object(sys, "argv", argv))
        m.main()
        first = json.loads((self.tmp_path / "out.json").read_text())
        self.assertEqual(first["compare"]["status"], "no-prior")
        m.main()
        second = json.loads((self.tmp_path / "out.json").read_text())
        self.assertEqual(second["compare"]["track_changes"], [{"name": "A", "changes": {"bpm": [100.0, 120.0]}}])
        archived = json.loads((self.tmp_path / "docs/audio-analysis/playlists/band-a.json").read_text())
        self.assertEqual(archived["tracks"][0]["bpm"], 120.0)
        self.assertNotIn("compare", archived)


class TestRunGuardsAndArtifacts(unittest.TestCase):
    """main(): the archive is the re-eval baseline, so a run never erases it by accident."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.m = _load_module()
        self.enterContext(contextlib.chdir(self.root))
        self.audio = self.root / "docs" / "audio" / "band-a"
        self.audio.mkdir(parents=True)
        for n in ("A", "B", "C"):
            (self.audio / f"{n}.mp3").write_bytes(b"x")
        self.playlist = self.root / "docs" / "band-a-playlist.yaml"
        self.write_playlist("A", "B", "C")
        self.enterContext(mock.patch.object(
            self.m, "analyze_track",
            lambda path, reading=None: _track("x", 100.0, "8A", "8A", [-14] * 3) | {"tempo_source": "librosa"}))
        self.enterContext(mock.patch.object(self.m, "require_audio_deps", lambda **kw: None))
        self.enterContext(mock.patch.dict(sys.modules, {"librosa": type(sys)("librosa"),
                                                        "numpy": type(sys)("numpy")}))
        self.archive = self.root / "docs/audio-analysis/playlists/band-a.json"
        self.companion = self.root / "docs/band-a-playlist-sequencing.md"

    def write_playlist(self, *names, path=None, extra=""):
        body = "".join(f'  - name: "{n}"\n    file: "{n}.mp3"\n' for n in names)
        (path or self.playlist).write_text(f'album: "Band A"\n{extra}tracks:\n{body}')

    def run_main(self, *extra, playlist="docs/band-a-playlist.yaml", parse=True):
        """(exit code, stdout JSON) for one run; stderr is kept on self.stderr. parse=False returns stdout as text.
        playlist=None runs without --playlist."""
        argv = ["x", *(["--playlist", playlist] if playlist else []), "--tempo-source", "librosa", *extra]
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
            try:
                self.m.main()
            except SystemExit as exc:
                code = exc.code or 0
        self.stderr = err.getvalue()
        return code, (json.loads(out.getvalue()) if parse else out.getvalue())

    def test_nothing_analyzed_writes_nothing_and_exits_1(self):
        code, _ = self.run_main()
        self.assertEqual(code, 0)
        archived, companion = self.archive.read_text(), self.companion.read_text()
        for n in ("A", "B", "C"):
            (self.audio / f"{n}.mp3").unlink()
        code, out = self.run_main("--force-archive")
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "fail")
        self.assertEqual([d["name"] for d in out["dropped"]], ["A", "B", "C"])
        self.assertEqual(out["artifacts"]["archive"]["status"], "skipped")
        self.assertEqual(self.archive.read_text(), archived)  # the baseline survives
        self.assertEqual(self.companion.read_text(), companion)

    def test_dropping_an_analyzed_track_keeps_the_prior_archive(self):
        self.run_main()
        archived = self.archive.read_text()
        (self.audio / "B.mp3").unlink()
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual(out["artifacts"]["archive"]["status"], "kept-prior")
        self.assertIn("B", out["artifacts"]["archive"]["reason"])
        self.assertEqual(out["artifacts"]["companion"]["status"], "kept-prior")
        self.assertEqual(self.archive.read_text(), archived)
        code, out = self.run_main("--force-archive")
        self.assertEqual(out["artifacts"]["archive"]["status"], "written")
        self.assertNotEqual(self.archive.read_text(), archived)

    def test_removing_a_track_from_the_playlist_is_not_a_loss(self):
        self.run_main()
        self.write_playlist("A", "C")
        code, out = self.run_main()
        self.assertEqual(out["artifacts"]["archive"]["status"], "written")
        self.assertEqual(out["compare"]["removed_tracks"], ["B"])

    def test_artifacts_name_the_written_paths(self):
        code, out = self.run_main()
        self.assertEqual(out["artifacts"]["archive"], {"path": os.path.join("docs", "audio-analysis", "playlists",
                                                                            "band-a.json"), "status": "written"})
        self.assertEqual(out["artifacts"]["companion"]["path"], os.path.join("docs", "band-a-playlist-sequencing.md"))
        self.assertIsNone(out["tempo_source_note"])
        self.assertEqual(out["audio_dir"], os.path.join("docs", "audio", "band-a"))  # the folder a catalog pass scans
        code, out = self.run_main("--no-archive", "--no-companion")
        self.assertEqual(out["artifacts"]["archive"], {"path": None, "status": "skipped"})

    def test_outputs_land_beside_a_relocated_playlist(self):
        data = self.root / "music"
        (data / "audio" / "band-b").mkdir(parents=True)
        (data / "audio" / "band-b" / "A.mp3").write_bytes(b"x")
        self.write_playlist("A", path=data / "band-b-playlist.yaml")
        (self.root / "elsewhere").mkdir()
        os.chdir(self.root / "elsewhere")
        code, out = self.run_main(playlist=str(data / "band-b-playlist.yaml"))
        self.assertEqual(code, 0)
        self.assertEqual(out["analyzed_count"], 1)  # audio/band-b/ beside the playlist
        self.assertTrue((data / "audio-analysis" / "playlists" / "band-a.json").is_file())  # slug from album:
        self.assertTrue((data / "band-a-playlist-sequencing.md").is_file())
        self.assertFalse((self.root / "elsewhere" / "docs").exists())

    def test_playlist_parse_errors_exit_1_with_a_reason(self):
        self.playlist.write_text("album: [unclosed\n")
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("not valid YAML", out["error"])
        self.playlist.write_text('album: X\ntracks:\n  - file: "A.mp3"\n')
        code, out = self.run_main()
        self.assertEqual((code, out["error"]), (1, "track 1 in docs/band-a-playlist.yaml has no `name:`"))
        self.playlist.write_text("- just a list\n")
        self.assertEqual(self.run_main()[0], 1)

    def test_empty_file_entry_is_a_named_drop(self):
        self.playlist.write_text('album: "Band A"\ntracks:\n  - name: A\n    file: A.mp3\n  - name: New\n    file: ""\n')
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual(out["dropped"], [{"position": 2, "name": "New", "file": None,
                                           "reason": "no file: set in the playlist entry"}])

    def test_felt_bpm_in_the_playlist_reaches_the_seam_math(self):
        # analyze_track reads 100 for every track; A's ear-verified 50 folds its reading to half time.
        self.write_playlist("A", "B", "C")
        self.playlist.write_text(self.playlist.read_text().replace('    file: "A.mp3"\n', '    file: "A.mp3"\n    felt_bpm: 50\n'))
        code, out = self.run_main()
        self.assertEqual(code, 0)
        first, second = out["tracks"][0], out["tracks"][1]
        self.assertEqual(first["felt_bpm"], 50.0)
        self.assertIs(first["felt_bpm_check"], False)  # the ear has spoken
        self.assertIs(second["felt_bpm_check"], True)  # 100 is in a danger range and nothing is recorded
        seam = first["transition_to_next"]
        self.assertTrue(seam["bpm_basis"].endswith("+felt"), seam["bpm_basis"])
        self.assertEqual((seam["bpm_from"], seam["bpm_to"], seam["bpm_quality"]), (50.0, 100.0, "jump (100%)"))
        self.assertEqual(second["transition_to_next"]["bpm_basis"], "overall")
        self.assertEqual(out["felt_bpm_ignored"], [])

    def test_ignored_felt_bpm_is_reported_in_json_text_and_companion(self):
        self.playlist.write_text(self.playlist.read_text().replace('    file: "A.mp3"\n', '    file: "A.mp3"\n    felt_bpm: "50"\n'))
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual(out["felt_bpm_ignored"], [{"name": "A", "value": "50", "reason": "not a positive number"}])
        self.assertIsNone(out["tracks"][0]["felt_bpm"])
        self.assertEqual(out["tracks"][0]["transition_to_next"]["bpm_basis"], "overall")  # the measured tempo stood
        self.assertIn("FELT_BPM IGNORED: A", self.stderr)
        self.assertIn("`felt_bpm:` ignored", self.companion.read_text(encoding="utf-8"))
        self.assertIn("A ('50')", self.run_main("--format", "text", "--no-archive", "--no-companion", parse=False)[1])

    def test_playlist_without_album_gets_its_own_archive(self):
        for slug in ("band-a", "band-b"):
            path = self.root / "docs" / f"{slug}-playlist.yaml"
            path.write_text('tracks:\n  - name: "A"\n    file: "A.mp3"\n', encoding="utf-8")
            (self.root / "docs" / "audio" / slug).mkdir(parents=True, exist_ok=True)
            (self.root / "docs" / "audio" / slug / "A.mp3").write_bytes(b"x")
            code, out = self.run_main(playlist=f"docs/{slug}-playlist.yaml")
            self.assertEqual((code, out["album"]), (0, slug))
            self.assertEqual(out["artifacts"]["archive"]["path"],
                             os.path.join("docs", "audio-analysis", "playlists", f"{slug}.json"))
            self.assertEqual(out["artifacts"]["companion"]["path"], os.path.join("docs", f"{slug}-playlist-sequencing.md"))
            self.assertEqual(out["compare"]["status"], "no-prior")  # the other band's archive is not this one's baseline
        self.assertFalse((self.root / "docs/audio-analysis/playlists/audio-analysis.json").exists())

    def test_duplicate_track_names_exit_1(self):
        self.write_playlist("A", "B", "A")
        code, out = self.run_main()
        self.assertEqual((code, out["status"]), (1, "fail"))
        self.assertIn("duplicate track name", out["error"])
        self.assertFalse(self.archive.exists())

    def test_prior_archive_of_another_shape_is_unreadable_not_a_crash(self):
        self.archive.parent.mkdir(parents=True)
        for body in ("[1, 2, 3]", '{"script": "batch-full-analysis", "tracks": [{"file": "A.mp3"}]}',
                     '{"tracks": [{"name": "A", "transition_to_next": "B"}]}', '{"tracks": {"A": 1}}'):
            self.archive.write_text(body, encoding="utf-8")
            code, out = self.run_main("--no-archive", "--no-companion")
            self.assertEqual(code, 0, body)
            self.assertEqual(out["compare"]["status"], "unreadable: not a playlist-sequencing-data report", body)
            self.assertEqual(out["analyzed_count"], 3)
        other = self.root / "other.json"
        other.write_text('{"tracks": [{"file": "A.mp3"}]}', encoding="utf-8")
        code, out = self.run_main("--compare-to", str(other))
        self.assertEqual((code, out["compare"]["status"]), (0, "unreadable: not a playlist-sequencing-data report"))
        self.assertEqual(out["artifacts"]["archive"]["status"], "written")  # nothing usable to protect

    def test_no_archive_run_still_guards_the_companion(self):
        self.run_main()
        companion = self.companion.read_text(encoding="utf-8")
        (self.audio / "B.mp3").unlink()
        code, out = self.run_main("--no-archive")
        self.assertEqual(code, 0)
        self.assertEqual(out["artifacts"]["archive"], {"path": None, "status": "skipped"})
        self.assertEqual(out["artifacts"]["companion"]["status"], "kept-prior")
        self.assertIn("B", out["artifacts"]["companion"]["reason"])
        self.assertEqual(self.companion.read_text(encoding="utf-8"), companion)  # B's row is still there
        code, out = self.run_main("--no-archive", "--force-archive")
        self.assertEqual(out["artifacts"]["companion"]["status"], "written")
        self.assertNotEqual(self.companion.read_text(encoding="utf-8"), companion)

    def test_dropped_tracks_are_named_in_the_markdown(self):
        (self.audio / "B.mp3").unlink()
        code, text = self.run_main("--format", "text", "--no-archive", parse=False)
        self.assertEqual(code, 0)
        self.assertIn("_Not analyzed (1 of 3): B (missing audio file)._", text)
        self.assertIn("_Not analyzed (1 of 3): B (missing audio file)._", self.companion.read_text(encoding="utf-8"))
        self.assertNotIn("Not analyzed", self.m.format_text("Album", [_track("A", 100.0, "8A", "8A", [-14] * 3)]))

    def test_a_failed_write_is_said_and_exits_3(self):
        (self.root / "docs" / "audio-analysis").write_text("a file where the archive folder goes", encoding="utf-8")
        code, out = self.run_main()
        self.assertEqual(code, 3)
        self.assertEqual(out["status"], "ok")  # the analysis itself is whole and on stdout
        self.assertEqual(out["analyzed_count"], 3)
        self.assertEqual(out["artifacts"]["archive"]["status"], "error")
        self.assertTrue(out["artifacts"]["archive"]["reason"])
        self.assertEqual(out["artifacts"]["companion"]["status"], "written")
        self.assertIn("ARCHIVE WRITE FAILED", self.stderr)
        # --format text carries no artifacts block: stderr and the exit code are all the caller gets.
        code, text = self.run_main("--format", "text", parse=False)
        self.assertEqual(code, 3)
        self.assertIn("## Track Data", text)
        self.assertIn("ARCHIVE WRITE FAILED", self.stderr)

    def test_output_folder_is_created_before_anything_is_written(self):
        code, _ = self.run_main("-o", "reports/new/out.json", parse=False)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((self.root / "reports/new/out.json").read_text(encoding="utf-8"))["analyzed_count"], 3)

    def test_unusable_output_path_fails_before_the_archive_is_touched(self):
        (self.root / "blocker").write_text("a file", encoding="utf-8")
        for bad in ("blocker/sub/out.json", "docs"):  # a file where a folder is needed; a folder as the file
            code, out = self.run_main("-o", bad)
            self.assertEqual((code, out["status"]), (1, "fail"), bad)
            self.assertIn("-o", out["error"])
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.companion.exists())

    def test_usage_error_is_the_json_failure_and_exit_1(self):
        code, out = self.run_main("--format", "yaml")
        self.assertEqual((code, out["status"]), (1, "fail"))
        self.assertTrue(out["error"].startswith("usage: "))
        self.assertIn("usage:", self.stderr)

    def test_without_a_playlist_outputs_sit_beside_the_audio_folder(self):
        music = self.root / "music"
        (music / "audio" / "band-b").mkdir(parents=True)
        (music / "audio" / "band-b" / "A.MP3").write_bytes(b"x")
        (music / "audio" / "band-b" / "B.wav").write_bytes(b"x")
        (self.root / "elsewhere").mkdir()
        os.chdir(self.root / "elsewhere")
        code, out = self.run_main("--audio-dir", str(music / "audio" / "band-b"), playlist=None)
        self.assertEqual((code, out["analyzed_count"]), (0, 2))  # .MP3 and .wav are both audio
        self.assertEqual([t["name"] for t in out["tracks"]], ["A", "B"])
        self.assertEqual(out["artifacts"]["archive"]["path"],
                         str(music / "audio-analysis" / "playlists" / "audio-analysis.json"))
        self.assertTrue((music / "audio-analysis-playlist-sequencing.md").is_file())
        self.assertFalse((self.root / "elsewhere" / "docs").exists())

    def test_project_root_replaces_the_working_directory(self):
        # audio_dir: in the YAML is written from the project root; the run starts somewhere else.
        self.write_playlist("A", "B", "C", extra='audio_dir: "docs/audio/band-a"\n')
        (self.root / "elsewhere").mkdir()
        os.chdir(self.root / "elsewhere")
        code, out = self.run_main(playlist=str(self.playlist))
        self.assertEqual(code, 1)  # no --project-root and no _bmad/ above the playlist: the path means nothing here
        self.assertIn("Audio directory not found", out["error"])
        code, out = self.run_main("--project-root", str(self.root), playlist=str(self.playlist))
        self.assertEqual((code, out["analyzed_count"]), (0, 3))
        (self.root / "_bmad").mkdir()  # the project root is also found from the playlist
        code, out = self.run_main(playlist=str(self.playlist))
        self.assertEqual((code, out["analyzed_count"]), (0, 3))

    def test_tempo_source_note_says_why_beat_this_was_not_used(self):
        def unavailable(paths, include_beats=False):
            raise self.m.BeatThisUnavailable("PyTorch / Beat This! not installed")
        self.enterContext(mock.patch.object(self.m, "run_beat_grid", unavailable))
        code, out = self.run_main("--tempo-source", "beat-this")
        self.assertIn("PyTorch / Beat This! not installed", out["tempo_source_note"])
        self.enterContext(mock.patch.object(
            self.m, "run_beat_grid", lambda paths, include_beats=False: [{"bpm": 100.0}, {"error": "too short"},
                                                                        {"bpm": 100.0}]))
        code, out = self.run_main("--tempo-source", "beat-this")
        self.assertIn("B (too short)", out["tempo_source_note"])


@unittest.skipUnless(HAVE_AUDIO_LIBS, "librosa and numpy are needed to analyze real audio")
class TestRealAnalysis(unittest.TestCase):
    """main() with the real analyze_track on synthesized audio: its return shape must fit build_report
    and format_text. Only what can't run here is stood in (loudness, when pyloudnorm isn't installed)."""

    LOUDNESS = {"integrated_lufs": -14.0, "lra_lu": 3.0, "thirds_lufs": [-15.0, -14.0, -13.0], "build_lu": 2.0,
                "entry_lufs": -15.0, "exit_lufs": -13.0}

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.m = _load_module()
        audio = self.root / "docs" / "audio" / "band-a"
        audio.mkdir(parents=True)
        write_wav(audio / "One.wav", bpm=120.0, freqs=(220.0, 261.63, 329.63))   # an A minor chord
        write_wav(audio / "Two.wav", bpm=90.0, freqs=(261.63, 329.63, 392.0))    # a C major chord
        self.playlist = self.root / "docs" / "band-a-playlist.yaml"
        self.playlist.write_text('album: "Band A"\ntracks:\n  - name: One\n    file: One.wav\n'
                                 '  - name: Two\n    file: Two.wav\n    felt_bpm: 90\n', encoding="utf-8")
        if not HAVE_PYLOUDNORM:
            self.enterContext(mock.patch.object(self.m, "require_audio_deps", lambda **kw: None))
            self.enterContext(mock.patch.object(self.m, "loudness_summary", lambda samples, sr: dict(self.LOUDNESS)))

    def run_main(self, *extra):
        argv = ["x", "--playlist", str(self.playlist), "--tempo-source", "librosa", "--no-archive", "--no-companion",
                *extra]
        out = io.StringIO()
        code = 0
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            try:
                self.m.main()
            except SystemExit as exc:
                code = exc.code or 0
        return code, out.getvalue()

    def test_real_tracks_come_through_the_report(self):
        code, out = self.run_main()
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual((report["status"], report["track_count"], report["analyzed_count"]), ("ok", 2, 2))
        self.assertEqual(report["dropped"], [])
        self.assertEqual(report["tempo_source"], "librosa")
        for t in report["tracks"]:
            self.assertNotIn("error", t)
            self.assertAlmostEqual(t["duration"], 8.0, delta=0.2)
            for field in ("bpm", "entry_bpm", "exit_bpm"):
                self.assertIsInstance(t[field], float, field)
            self.assertEqual(t["tempo_source"], "librosa")
            self.assertIn(t["librosa_prior_relation"], ("agree", "double", "other"))
            for which in ("overall", "entry", "exit"):
                self.assertRegex(t["key"][which], r"^[A-G]#? (major|minor)$")
                self.assertRegex(t["key"][f"{which}_camelot"], r"^(1[0-2]|[1-9])[AB]$")
                self.assertIsInstance(t["key"][f"{which}_confidence"], float)
            self.assertIn(t["energy"]["level"], range(1, 11))
            self.assertIsInstance(t["loudness"]["integrated_lufs"], float)
            self.assertEqual(len(t["loudness"]["thirds_lufs"]), 3)
            for field in ("entry_lufs", "exit_lufs"):
                self.assertIn(field, t["loudness"])
        one, two = report["tracks"]
        # The numbers are measurements of the signal, not placeholders: the click rate and the chord.
        self.assertAlmostEqual(one["bpm"], 120.0, delta=6.0)
        self.assertAlmostEqual(two["bpm"], 90.0, delta=5.0)
        self.assertEqual((one["key"]["overall"], one["key"]["overall_camelot"]), ("A minor", "8A"))
        self.assertEqual((two["key"]["overall"], two["key"]["overall_camelot"]), ("C major", "8B"))
        self.assertEqual(two["felt_bpm"], 90.0)
        self.assertIs(two["felt_bpm_check"], False)
        seam = one["transition_to_next"]
        self.assertEqual(seam["to"], "Two")
        self.assertRegex(seam["bpm_quality"], r"^jump \(\d+%\)$")  # about 120 into about 90
        self.assertEqual(seam["bpm_basis"], "exit/entry+felt")
        self.assertEqual((seam["key_relation"], seam["key_compat"]), ("relative", "compatible"))
        self.assertIsInstance(seam["loudness_step_lu"], float)
        self.assertNotIn("transition_to_next", two)

    def test_real_tracks_come_through_the_text_report(self):
        code, text = self.run_main("--format", "text")
        self.assertEqual(code, 0)
        self.assertRegex(text, r"\| 1 \| One \| [\d.]+")
        self.assertRegex(text, r"\| One \| Two \| ")


if __name__ == "__main__":
    unittest.main()
