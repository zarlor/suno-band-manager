#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Smoke test for playlist-sequencing-data.py.

The data layer of the suno-playlist-sequencer workflow (extracted from
suno-feedback-elicitor; see ../../../.decision-log.md). This minimal smoke test
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
    assert t["key_quality"] == "PERFECT" and t["bpm_quality"] == "smooth"
    assert "transition" not in results[1]  # successor errored
    text = m.format_text("Album", results)
    assert "| LUFS | LRA |" in text and "-9.0 LU (big jump (quieter))" in text
    data = __import__("json").loads(m.format_json("Album", results))
    assert data["tracks"][0]["loudness"]["thirds_lufs"] == [-15.0, -13.0, -10.0]
    assert data["tracks"][0]["transition_to_next"]["loudness_step_lu"] == -9.0


def test_transition_without_loudness_data_is_tolerated():
    m = _load_module()
    a, b = _track("A", 100.0, "8A", "8A", [-14, -14, -14]), _track("B", 100.0, "8A", "8A", [-14, -14, -14])
    a.pop("loudness")
    t = m.transition_between(a, b)
    assert t["loudness_step_lu"] is None and t["loudness_quality"] is None


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
