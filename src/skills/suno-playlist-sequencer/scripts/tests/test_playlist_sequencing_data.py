#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Smoke test for playlist-sequencing-data.py.

The data layer of the suno-playlist-sequencer workflow (extracted from
suno-feedback-elicitor; see dev-docs/decision-logs/suno-playlist-sequencer.md). This minimal smoke test
pins the exit-code contract — a missing audio dir yields a non-zero exit, not a
crash. Invoked via `uv run` to provision librosa; skips without uv.
"""

import contextlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = str(Path(__file__).parent.parent / "playlist-sequencing-data.py")
UV = shutil.which("uv")
TIMEOUT = 600


def run_uv(args: list[str]) -> int:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT).returncode


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

    def test_missing_dir_exits_nonzero(self):
        self.assertNotEqual(run_uv(["--audio-dir", "/nonexistent-audio-dir-xyz"]), 0)

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

    def run_main(self, *extra, playlist="docs/band-a-playlist.yaml"):
        """(exit code, stdout JSON) for one run."""
        import io
        import json
        argv = ["x", "--playlist", playlist, "--tempo-source", "librosa", *extra]
        out = io.StringIO()
        code = 0
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            try:
                self.m.main()
            except SystemExit as exc:
                code = exc.code
        return code, json.loads(out.getvalue())

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


if __name__ == "__main__":
    unittest.main()
