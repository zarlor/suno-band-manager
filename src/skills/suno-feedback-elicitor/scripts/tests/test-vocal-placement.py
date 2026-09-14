#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for vocal-placement.py (Demucs stems + BS.1770 loudness).

Demucs needs PyTorch, which is too heavy to provision in the suite, so these pin
the placement arithmetic, the no-vocal flagging, text output, and the
exit-code contract (the path guard runs before the dependency check).
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "vocal-placement.py"
spec = importlib.util.spec_from_file_location("vocal_placement", SCRIPT)
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)


def test_placement_overall_thirds_and_drift():
    p = vp.placement(-15.0, -14.0, [-16.0, -15.0, -14.0], [-16.5, -14.0, -12.0])
    assert p["vocal_minus_band_lu"] == -1.0
    assert p["vocal_minus_band_thirds_lu"] == [0.5, -1.0, -2.0]
    assert p["vocal_drift_lu"] == -2.5
    assert p["vocal_present_thirds"] == [True, True, True]


def test_instrumental_ending_is_flagged_and_drift_withheld():
    p = vp.placement(-18.0, -13.0, [-15.0, -15.0, -40.0], [-14.0, -13.0, -12.0])
    assert p["vocal_present_thirds"] == [True, True, False]
    assert p["vocal_drift_lu"] is None


def test_silent_stem_gives_none():
    p = vp.placement(None, -13.0, [None, None, None], [-14.0, -13.0, -12.0])
    assert p["vocal_minus_band_lu"] is None
    assert p["vocal_present_thirds"] == [False, False, False]


def test_format_text_marks_absent_thirds():
    r = {"file": "x.mp3", **vp.placement(-18.0, -13.0, [-15.0, -15.0, -40.0], [-14.0, -13.0, -12.0])}
    text = vp.format_text([r, {"file": "y.mp3", "error": "boom"}])
    assert vp.format_json([r], "cuda", 5)["metrics"]["shifts"] == 5
    assert "-28.0*" in text and "ERROR: boom" in text


def test_missing_input_exits_1():
    proc = subprocess.run([sys.executable, str(SCRIPT), "/nonexistent-audio-xyz", "--no-archive"],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 1
