#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for _shared/tempo_source.py: Beat This! when opted in, librosa otherwise.

Pins the opt-in reading (per-module and shared BMad config, walked up from the
working directory), the --tempo-source override, and the beat-grid.py hand-off
and its fallbacks. A stand-in script plays beat-grid.py, so no PyTorch is needed.
"""

import argparse
import importlib.util
import io
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "tempo_source.py"
spec = importlib.util.spec_from_file_location("tempo_source", SCRIPT)
ts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ts)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def fake_beat_grid(monkeypatch, tmp_path, body):
    script = tmp_path / "fake-beat-grid.py"
    script.write_text("import json, sys\n" + body)
    monkeypatch.setattr(ts, "BEAT_GRID", script)
    monkeypatch.setattr(ts.shutil, "which", lambda _name: None)  # run with sys.executable, not uv


def test_flag_from_per_module_config(tmp_path):
    write(tmp_path / "_bmad/suno/config.yaml", "user_name: X\npytorch_audio_tools: 'on'\n")
    assert ts.read_config_flag(tmp_path) == "on"
    assert ts.opted_in(tmp_path)


def test_flag_from_shared_config_reads_only_the_suno_section(tmp_path):
    write(tmp_path / "_bmad/config.yaml",
          "core:\n  pytorch_audio_tools: true\nsuno:\n  suno_tier: pro\n  pytorch_audio_tools: off  # comment\n")
    assert ts.read_config_flag(tmp_path) == "off"
    assert not ts.opted_in(tmp_path)


def test_per_module_config_wins_over_shared(tmp_path):
    write(tmp_path / "_bmad/suno/config.yaml", "pytorch_audio_tools: true\n")
    write(tmp_path / "_bmad/config.yaml", "suno:\n  pytorch_audio_tools: 'off'\n")
    assert ts.opted_in(tmp_path)


def test_opt_in_found_from_a_subdirectory(tmp_path):
    write(tmp_path / "_bmad/suno/config.yaml", "pytorch_audio_tools: yes\n")
    sub = tmp_path / "docs" / "audio"
    sub.mkdir(parents=True)
    assert ts.resolve_tempo_source("auto", sub) == "beat-this"


def test_no_config_means_librosa(tmp_path):
    assert ts.find_config_flag(tmp_path) is None or not ts.opted_in(tmp_path)
    write(tmp_path / "_bmad/suno/config.yaml", "user_name: X\n")
    write(tmp_path / "_bmad/config.yaml", "suno:\n  suno_tier: pro\n")
    assert ts.read_config_flag(tmp_path) is None


def test_explicit_source_overrides_config(tmp_path):
    write(tmp_path / "_bmad/suno/config.yaml", "pytorch_audio_tools: 'on'\n")
    assert ts.resolve_tempo_source("librosa", tmp_path) == "librosa"
    write(tmp_path / "_bmad/suno/config.yaml", "pytorch_audio_tools: 'off'\n")
    assert ts.resolve_tempo_source("auto", tmp_path) == "librosa"
    assert ts.resolve_tempo_source("beat-this", tmp_path) == "beat-this"


def test_tempo_source_arg_defaults_to_auto():
    parser = argparse.ArgumentParser()
    ts.add_tempo_source_arg(parser)
    assert parser.parse_args([]).tempo_source == "auto"
    assert parser.parse_args(["--tempo-source", "librosa"]).tempo_source == "librosa"


def test_run_beat_grid_passes_paths_in_order(monkeypatch, tmp_path):
    fake_beat_grid(monkeypatch, tmp_path, (
        "paths = sys.argv[1:sys.argv.index('--no-librosa')]\n"
        "beats = '--include-beats' in sys.argv\n"
        "print(json.dumps({'metrics': {'tracks': [{'file': p, 'bpm': 100.0 + i, 'beats': beats}"
        " for i, p in enumerate(paths)]}}))\n"))
    tracks = ts.run_beat_grid(["a.mp3", "b.mp3"], include_beats=True)
    assert [t["file"] for t in tracks] == ["a.mp3", "b.mp3"]
    assert tracks[1]["bpm"] == 101.0 and tracks[0]["beats"] is True


def test_run_beat_grid_missing_dependencies_is_unavailable(monkeypatch, tmp_path):
    fake_beat_grid(monkeypatch, tmp_path, "sys.exit(2)\n")
    with pytest.raises(ts.BeatThisUnavailable, match="not installed"):
        ts.run_beat_grid(["a.mp3"])


def test_run_beat_grid_track_count_mismatch_is_unavailable(monkeypatch, tmp_path):
    fake_beat_grid(monkeypatch, tmp_path, "print(json.dumps({'metrics': {'tracks': []}}))\n")
    with pytest.raises(ts.BeatThisUnavailable):
        ts.run_beat_grid(["a.mp3"])


def test_run_beat_grid_missing_script(monkeypatch, tmp_path):
    monkeypatch.setattr(ts, "BEAT_GRID", tmp_path / "nope.py")
    with pytest.raises(ts.BeatThisUnavailable):
        ts.run_beat_grid(["a.mp3"])
    assert ts.run_beat_grid([]) == []


def test_readings_fall_back_to_librosa_with_a_note(monkeypatch, tmp_path):
    fake_beat_grid(monkeypatch, tmp_path, "sys.exit(1)\n")
    log = io.StringIO()
    assert ts.beat_this_readings(["a.mp3"], log=log) is None
    assert "using librosa" in log.getvalue()


def test_beat_grid_path_points_at_the_real_script():
    assert ts.BEAT_GRID.is_file() and ts.BEAT_GRID.name == "beat-grid.py"


def test_usable_and_source_summary():
    assert ts.usable({"bpm": 90.0})
    assert not ts.usable({"bpm": None}) and not ts.usable({"error": "x"}) and not ts.usable(None)
    assert ts.source_summary([{"tempo_source": "beat-this"}, {"tempo_source": "beat-this"}]) == "beat-this"
    assert ts.source_summary([{"tempo_source": "beat-this"}, {}]) == "mixed"
    assert ts.source_summary([{"tempo_source": "beat-this"}, {"error": "missing"}]) == "beat-this"
    assert ts.source_summary([]) == "librosa"
    assert set(ts.SOURCE_LABELS) == {"beat-this", "librosa", "mixed"}


def test_tempo_relation_labels():
    assert ts.tempo_relation(76.9, 152.0) == "librosa_double"
    assert ts.tempo_relation(96.8, 97.5) == "agree"
    assert ts.tempo_relation(None, 120.0) is None


def steady_beats(bpm, start, end):
    ibi = 60.0 / bpm
    n = int((end - start) / ibi)
    return [start + i * ibi for i in range(n)]


def test_window_tempos_ignore_a_stray_beat():
    beats = steady_beats(120, 0, 30)
    beats.insert(10, beats[9] + 0.1)  # one stray detection
    windows = ts.window_tempos(beats)
    assert [w["bpm"] for w in windows] == [120.0, 120.0]
    assert windows[0]["start"] == 0.0 and windows[1]["end"] <= 30.0


def test_windowed_stability_labels():
    steady = [{"start": 0, "end": 15, "bpm": 200.0}, {"start": 15, "end": 30, "bpm": 201.0}]
    assert ts.windowed_stability(steady) == ("steady", (200, 201))
    slight = steady + [{"start": 30, "end": 45, "bpm": 212.0}]
    assert ts.windowed_stability(slight)[0] == "slight variation"
    halftime = steady + [{"start": 30, "end": 45, "bpm": 100.0}]
    assert ts.windowed_stability(halftime) == ("TEMPO CHANGES", (100, 201))
    assert ts.windowed_stability([]) == ("too few beats", (0, 0))


def test_feel_sections_name_and_merge_runs():
    beats = steady_beats(125, 0, 120) + steady_beats(64, 120, 150) + steady_beats(125, 150, 195)
    windows = ts.window_tempos(beats)
    sections = ts.feel_sections(windows, 125.0)
    assert len(sections) == 1
    f = sections[0]
    assert f["feel"] == "half-time" and f["start"] == 120.0 and f["end"] == 150.0 and abs(f["bpm"] - 64) < 1


def test_feel_sections_labels():
    windows = [{"start": 0.0, "end": 15.0, "bpm": 231.0}, {"start": 15.0, "end": 30.0, "bpm": 115.0},
               {"start": 30.0, "end": 45.0, "bpm": 172.0}, {"start": 45.0, "end": 60.0, "bpm": 150.0}]
    feels = [f["feel"] for f in ts.feel_sections(windows, 115.0)]
    assert feels == ["double-time", "triplet grid", "shift"]
    assert ts.feel_sections(windows, None) == []
