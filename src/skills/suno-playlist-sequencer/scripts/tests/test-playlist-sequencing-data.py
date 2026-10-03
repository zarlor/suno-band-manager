#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Smoke test for playlist-sequencing-data.py.

The data layer of the suno-playlist-sequencer workflow (extracted from
suno-feedback-elicitor; see dev-docs/decision-logs/suno-playlist-sequencer.md). This minimal smoke test
pins the exit-code contract — a missing audio dir yields a non-zero exit, not a
crash. Invoked via `uv run` to provision librosa; skips without uv.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).parent.parent / "playlist-sequencing-data.py")
UV = shutil.which("uv")
TIMEOUT = 600

pytestmark = pytest.mark.skipif(UV is None, reason="uv not available to provision librosa deps")


def run_uv(args: list[str]) -> int:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT).returncode


def test_missing_dir_exits_nonzero():
    assert run_uv(["--audio-dir", "/nonexistent-audio-dir-xyz"]) != 0


def load_module():
    spec = importlib.util.spec_from_file_location("playlist_sequencing_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_audio_dir_precedence(tmp_path, monkeypatch):
    m = load_module()
    monkeypatch.chdir(tmp_path)
    playlist = "docs/band-a-playlist.yaml"
    assert m.resolve_audio_dir("cli/dir", playlist, "yaml/dir") == "cli/dir"
    assert m.resolve_audio_dir(None, playlist, "docs/audio/custom") == "docs/audio/custom"
    # No band folder on disk yet: fall back to the legacy flat docs/audio.
    assert m.resolve_audio_dir(None, playlist) == "docs/audio"
    (tmp_path / "docs" / "audio" / "band-a").mkdir(parents=True)
    assert m.resolve_audio_dir(None, playlist) == os.path.join("docs/audio", "band-a")
    assert m.resolve_audio_dir(None) == "docs/audio"


def test_load_playlist_returns_yaml_audio_dir(tmp_path):
    m = load_module()
    p = tmp_path / "x-playlist.yaml"
    p.write_text('album: "X"\naudio_dir: "docs/audio/x"\ntracks:\n  - name: "A"\n    file: "A.mp3"\n')
    album, tracks, audio_dir = m.load_playlist(str(p))
    assert (album, tracks, audio_dir) == ("X", [("A", "A.mp3")], "docs/audio/x")


def test_discover_tracks_recurses_band_folders(tmp_path):
    m = load_module()
    (tmp_path / "band-a").mkdir()
    (tmp_path / "band-a" / "Song.mp3").write_bytes(b"x")
    (tmp_path / "Loose.mp3").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("x")
    _, tracks = m.discover_tracks(str(tmp_path))
    assert tracks == [("Loose", "Loose.mp3"), ("Song", "band-a/Song.mp3")]


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


def test_transitions_carry_loudness_seam():
    m = _load_module()
    results = [_track("Loud End", 120.0, "8A", "8A", [-15.0, -13.0, -10.0]),
               _track("Quiet Open", 122.0, "8A", "9A", [-19.0, -14.0, -12.0]),
               {"name": "Missing", "error": "file not found"}]
    m.compute_transitions(results)
    t = results[0]["transition"]
    assert t["loudness_step_lu"] == -9.0 and t["loudness_quality"] == "big jump (quieter)"
    assert t["key_compat"] == "compatible" and t["key_relation"] == "same" and t["bpm_quality"] == "smooth"
    assert "key_quality" not in t  # no single-variable field reads as the seam's verdict
    assert "transition" not in results[1]  # successor errored
    text = m.format_text("Album", results)
    assert "| LUFS | LUFS in→out | LRA |" in text and "-9.0 LU (big jump (quieter))" in text
    data = __import__("json").loads(m.format_json("Album", results))
    assert data["tracks"][0]["loudness"]["thirds_lufs"] == [-15.0, -13.0, -10.0]
    assert data["tracks"][0]["transition_to_next"]["loudness_step_lu"] == -9.0


def test_transition_without_loudness_data_is_tolerated():
    m = _load_module()
    a, b = _track("A", 100.0, "8A", "8A", [-14, -14, -14]), _track("B", 100.0, "8A", "8A", [-14, -14, -14])
    a.pop("loudness")
    t = m.transition_between(a, b)
    assert t["loudness_step_lu"] is None and t["loudness_quality"] is None


def test_transition_uses_exit_entry_tempo_and_loudness():
    m = _load_module()
    a = _track("Fast Out", 120.0, "8A", "8A", [-15.0, -13.0, -10.0])
    b = _track("Slow In", 118.0, "8A", "8A", [-19.0, -14.0, -12.0])
    a.update(entry_bpm=118.0, exit_bpm=150.0); b.update(entry_bpm=75.0, exit_bpm=118.0)
    a["loudness"]["exit_lufs"] = -9.0; b["loudness"]["entry_lufs"] = -24.0
    t = m.transition_between(a, b)
    assert t["bpm_basis"] == "exit/entry" and t["bpm_from"] == 150.0 and t["bpm_to"] == 75.0
    assert t["bpm_change"] == 75.0 and t["bpm_quality"].startswith("jump")
    assert t["loudness_step_lu"] == -15.0
    text = m.format_text("Album", [a, b])
    assert "BPM in→out" in text and "118.0→150.0" in text and "LUFS in→out" in text


def test_tempo_source_reported_in_json_and_text():
    import json
    m = _load_module()
    a = _track("A", 76.9, "8A", "8A", [-14, -14, -14])
    b = _track("B", 96.8, "8A", "8A", [-14, -14, -14])
    a["tempo_source"] = b["tempo_source"] = "beat-this"
    data = json.loads(m.format_json("Album", [a, b]))
    assert data["tempo_source"] == "beat-this" and data["tracks"][0]["tempo_source"] == "beat-this"
    assert "Tempo: Beat This!" in m.format_text("Album", [a, b])
    b["tempo_source"] = "librosa"
    assert json.loads(m.format_json("Album", [a, b]))["tempo_source"] == "mixed"
    a.pop("tempo_source"); b.pop("tempo_source")
    assert "Tempo: librosa." in m.format_text("Album", [a, b])


def _report(m, tracks):
    m.compute_transitions(tracks)
    return m.build_report("Album", tracks)


def test_key_relation_names_parallel_and_relative():
    m = _load_module()
    d = m.camelot_distance
    assert m.key_relation("A minor", "A major", d("8A", "11B")) == "parallel"
    assert m.key_compat(d("8A", "11B")) == "distant"  # the wheel alone would hide the pivot
    assert m.key_relation("Eb minor", "D# major", d("2A", "5B")) == "parallel"  # enharmonic tonic
    assert m.key_relation("A minor", "C major", d("8A", "8B")) == "relative"
    assert m.key_relation("A minor", "E minor", d("8A", "9A")) == "adjacent"
    assert m.key_relation("A minor", "B minor", d("8A", "10A")) == "two-step"
    assert m.key_relation("A minor", "F# major", d("8A", "2B")) == "distant"
    assert m.key_relation("Unknown", "A minor", -1) == "unknown" and m.key_compat(-1) == "unknown"


def test_dropped_tracks_reported_and_not_counted_as_analyzed():
    m = _load_module()
    tracks = [_track("A", 100.0, "8A", "8A", [-14] * 3),
              {"name": "Gone", "file": "Gone.mp3", "error": "missing audio file"},
              _track("B", 100.0, "8A", "8A", [-14] * 3),
              {"name": "Bad", "file": "Bad.mp3", "error": "analysis error: boom"}]
    data = _report(m, tracks)
    assert data["track_count"] == 4 and data["analyzed_count"] == 2
    assert data["dropped"] == [
        {"position": 2, "name": "Gone", "file": "Gone.mp3", "reason": "missing audio file"},
        {"position": 4, "name": "Bad", "file": "Bad.mp3", "reason": "analysis error: boom"}]


def test_felt_bpm_folds_half_time_read_and_flags():
    m = _load_module()
    a = _track("Doom", 144.0, "8A", "8A", [-14] * 3)
    b = _track("Ballad", 74.0, "8A", "8A", [-14] * 3)
    a.update(entry_bpm=144.0, exit_bpm=146.0); b.update(entry_bpm=74.0, exit_bpm=74.0)
    t = m.transition_between(a, b)
    assert t["pulse_pair"] is True and t["bpm_quality"].startswith("jump")
    a["felt_bpm"] = 72.0
    t = m.transition_between(a, b)
    assert t["bpm_from"] == 73.0 and t["bpm_basis"] == "exit/entry+felt" and t["bpm_quality"] == "smooth"
    assert t["pulse_pair"] is False
    data = _report(m, [a, b])
    assert data["tracks"][0]["felt_bpm_check"] is False  # ear verdict recorded
    assert data["tracks"][1]["felt_bpm_check"] is True   # 74 is in the 70-100 danger range


def test_librosa_slow_prior_reported_and_feeds_felt_check():
    import json
    m = _load_module()
    a = _track("Slow Burn", 117.5, "8A", "8A", [-14] * 3)    # 117.5 is outside both danger ranges
    b = _track("Mid", 110.0, "8A", "8A", [-14] * 3)
    c = _track("Agreed", 110.0, "8A", "8A", [-14] * 3)
    a.update(tempo_source="librosa", bpm_librosa_slow_prior=60.1, librosa_prior_relation="double")
    c.update(tempo_source="librosa", bpm_librosa_slow_prior=110.0, librosa_prior_relation="agree")
    data = json.loads(m.format_json("Album", [a, b, c]))
    t0, t1, t2 = data["tracks"]
    assert t0["bpm"] == 117.5 and t0["bpm_librosa_slow_prior"] == 60.1 and t0["librosa_prior_relation"] == "double"
    assert t0["felt_bpm_check"] is True           # the double flags it even outside the danger ranges
    assert t1["bpm_librosa_slow_prior"] is None and t1["felt_bpm_check"] is False
    assert t2["felt_bpm_check"] is False
    assert m.needs_felt_check(117.5, 60.0, "double") is False  # the ear's verdict settles it
    assert m.needs_felt_check(117.5, None) is False and m.needs_felt_check(74.0, None) is True
    text = m.format_text("Album", [a, b, c])
    assert "| 117.5 / 60.1 (halftime?) |" in text and "| 110.0 |" in text and "start_bpm=80" in text
    assert "start_bpm=80" not in m.format_text("Album", [b, c])  # no footnote when nothing differs


def test_load_felt_bpm(tmp_path):
    m = _load_module()
    p = tmp_path / "x-playlist.yaml"
    p.write_text('album: X\ntracks:\n  - name: A\n    file: A.mp3\n    felt_bpm: 72\n  - name: B\n    file: B.mp3\n')
    assert m.load_felt_bpm(str(p)) == {"A": 72.0}


def test_runs_same_key_and_tempo_buckets():
    m = _load_module()
    tracks = [_track(n, bpm, "8A", "8A", [-14] * 3) for n, bpm in
              (("A", 80.0), ("B", 82.0), ("C", 130.0), ("D", 131.0), ("E", 132.0))]
    tracks[4]["overall_camelot"] = "9A"
    runs = m.find_runs(tracks)
    assert {"kind": "same-key", "value": "8A", "tracks": ["A", "B", "C", "D"]} in runs
    assert {"kind": "tempo", "value": "slow", "tracks": ["A", "B"], "felt_verified": False} in runs
    assert {"kind": "tempo", "value": "up", "tracks": ["C", "D", "E"], "felt_verified": False} in runs
    tracks[2] = {"name": "C", "error": "missing audio file"}  # a drop breaks a run
    assert not [r for r in m.find_runs(tracks) if r["kind"] == "same-key"]


def test_compare_reports_what_moved():
    import copy
    m = _load_module()
    before = [_track("A", 100.0, "8A", "8A", [-14] * 3), _track("B", 100.0, "8A", "8A", [-14] * 3),
              _track("C", 100.0, "8A", "8A", [-14] * 3)]
    after = copy.deepcopy(before)
    after[1].update(bpm=140.0, exit_camelot="3B", exit_key="C# major")  # regen moved B
    prior, current = _report(m, before), _report(m, after)
    diff = m.compare_runs(prior, current)
    assert diff["track_changes"] == [{"name": "B", "changes": {"bpm": [100.0, 140.0], "exit_camelot": ["8A", "3B"]}}]
    assert diff["unchanged_tracks"] == 2 and not diff["reordered"]
    seams = {(s["from"], s["to"]): s for s in diff["seam_changes"]}
    assert seams[("A", "B")]["direction"] == "worse" and "bpm_quality" in seams[("A", "B")]["changes"]
    assert seams[("B", "C")]["direction"] == "worse"
    assert seams[("B", "C")]["changes"]["key_compat"] == ["compatible", "distant"]
    same = m.compare_runs(current, current)
    assert same["track_changes"] == [] and same["seam_changes"] == []


def test_compare_reads_legacy_key_quality_and_reorders():
    m = _load_module()
    prior = {"tracks": [
        {"name": "A", "position": 1, "bpm": 100.0, "transition_to_next": {"to": "B", "key_quality": "PERFECT",
                                                                           "bpm_quality": "smooth"}},
        {"name": "B", "position": 2, "bpm": 100.0}]}
    current = _report(m, [_track("B", 100.0, "8A", "8A", [-14] * 3), _track("A", 100.0, "8A", "8A", [-14] * 3),
                          _track("New", 100.0, "8A", "8A", [-14] * 3)])
    diff = m.compare_runs(prior, current)
    assert diff["reordered"] and diff["added_tracks"] == ["New"] and diff["removed_tracks"] == []
    assert {"from": "B", "to": "A"} in diff["new_seams"]
    assert m._seam_labels(prior["tracks"][0]["transition_to_next"])["key_compat"] == "compatible"


def test_compare_reads_prior_before_archive_overwrite(tmp_path, monkeypatch):
    """Re-eval regression: the run must compare against the PRIOR archive, not itself."""
    import json
    m = _load_module()
    monkeypatch.chdir(tmp_path)
    audio = tmp_path / "docs" / "audio" / "band-a"
    audio.mkdir(parents=True)
    for n in ("A", "B"):
        (audio / f"{n}.mp3").write_bytes(b"x")
    (tmp_path / "docs" / "band-a-playlist.yaml").write_text(
        'album: "Band A"\ntracks:\n  - name: A\n    file: A.mp3\n  - name: B\n    file: B.mp3\n')
    bpms = iter([100.0, 100.0, 120.0, 100.0])  # run 1: A=100, B=100; run 2: A=120
    monkeypatch.setattr(m, "analyze_track", lambda path, reading=None: _track("x", next(bpms), "8A", "8A", [-14] * 3))
    monkeypatch.setattr(m, "require_audio_deps", lambda **kw: None)
    monkeypatch.setitem(sys.modules, "librosa", type(sys)("librosa"))
    monkeypatch.setitem(sys.modules, "numpy", type(sys)("numpy"))
    argv = ["x", "--playlist", "docs/band-a-playlist.yaml", "--no-companion", "--tempo-source", "librosa",
            "-o", "out.json"]
    monkeypatch.setattr(sys, "argv", argv)
    m.main()
    first = json.loads((tmp_path / "out.json").read_text())
    assert first["compare"]["status"] == "no-prior"
    m.main()
    second = json.loads((tmp_path / "out.json").read_text())
    assert second["compare"]["track_changes"] == [{"name": "A", "changes": {"bpm": [100.0, 120.0]}}]
    archived = json.loads((tmp_path / "docs/audio-analysis/playlists/band-a.json").read_text())
    assert archived["tracks"][0]["bpm"] == 120.0 and "compare" not in archived


if __name__ == "__main__":
    if UV is None:
        print("SKIP: uv not available")
        sys.exit(0)
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS: {test.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {test.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
    sys.exit(1 if failed else 0)
