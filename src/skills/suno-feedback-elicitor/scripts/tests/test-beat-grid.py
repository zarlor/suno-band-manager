#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for beat-grid.py (Beat This! beat tracking).

The model needs PyTorch, which is too heavy to provision in the suite, so these
pin the pure logic (tempo and bar grouping from beat times, the librosa
relation labels, input discovery) and the exit-code contract. The path guard
runs before the dependency check, so a missing input exits 1 under any Python.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "beat-grid.py"
spec = importlib.util.spec_from_file_location("beat_grid", SCRIPT)
bg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bg)


def grid(bpm, beats_per_bar, bars):
    ibi = 60.0 / bpm
    beats = [i * ibi for i in range(beats_per_bar * bars)]
    return beats, beats[::beats_per_bar]


def test_beat_stats_four_four():
    beats, downbeats = grid(120, 4, 16)
    s = bg.beat_stats(beats, downbeats)
    assert s["bpm"] == 120.0
    assert s["beats_per_bar"] == 4
    assert s["beats_per_bar_hist"] == {"4": 15}
    assert s["bars_per_minute"] == 30.0


def test_beat_stats_three_four():
    beats, downbeats = grid(90, 3, 12)
    s = bg.beat_stats(beats, downbeats)
    assert s["bpm"] == 90.0 and s["beats_per_bar"] == 3


def test_beat_stats_too_few_beats():
    s = bg.beat_stats([0.0, 0.5], [0.0])
    assert s["bpm"] is None and s["beats_per_bar"] is None


def test_tempo_relation_labels():
    assert bg.tempo_relation(76.9, 152.0) == "librosa_double"
    assert bg.tempo_relation(200.0, 99.4) == "librosa_half"
    assert bg.tempo_relation(96.8, 97.5) == "agree"
    assert bg.tempo_relation(80.0, 120.0) == "librosa_1.5x"
    assert bg.tempo_relation(120.0, 80.0) == "librosa_2/3x"
    assert bg.tempo_relation(100.0, 130.0) == "disagree"
    assert bg.tempo_relation(None, 120.0) is None


def test_collect_inputs_recurses_and_filters(tmp_path):
    (tmp_path / "band-a").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "band-a" / "Song.mp3").write_bytes(b"")
    (tmp_path / "Root.WAV").write_bytes(b"")
    (tmp_path / "notes.txt").write_text("x")
    (tmp_path / ".hidden" / "Skip.mp3").write_bytes(b"")
    found = bg.collect_inputs(str(tmp_path))
    assert [bg.rel_label(f, str(tmp_path)) for f in found] == ["Root.WAV", "band-a/Song.mp3"]


def test_missing_input_exits_1():
    proc = subprocess.run([sys.executable, str(SCRIPT), "/nonexistent-audio-xyz", "--no-archive"],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 1


def test_empty_dir_exits_1(tmp_path):
    proc = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path), "--no-archive"],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 1


def test_format_text_handles_errors_and_missing_values():
    text = bg.format_text([
        {"file": "a.mp3", "duration_s": 200.0, "bpm": 76.9, "beats_per_bar": 4, "librosa_bpm": 152.0,
         "tempo_relation": "librosa_double"},
        {"file": "b.mp3", "duration_s": 5.0, "bpm": None, "beats_per_bar": None},
        {"file": "c.mp3", "error": "RuntimeError: bad file"},
    ])
    assert "double-time read" in text and "ERROR: RuntimeError" in text
