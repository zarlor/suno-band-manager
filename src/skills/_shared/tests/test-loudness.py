#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for _shared/loudness.py.

The gating, percentile, and seam logic is pure Python and runs anywhere. The
BS.1770 measurement itself is checked against a known reference (a 997 Hz sine
at 0.1 peak in mono reads -23.0 LUFS) via `uv run --with numpy --with
pyloudnorm`, so it skips when uv is unavailable.
"""

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("loudness", SHARED / "loudness.py")
loudness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loudness)
UV = shutil.which("uv")


def test_percentile_matches_linear_interpolation():
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert loudness._percentile(vals, 0) == 1.0
    assert loudness._percentile(vals, 100) == 5.0
    assert loudness._percentile(vals, 50) == 3.0
    assert loudness._percentile(vals, 95) == pytest.approx(4.8)


def test_loudness_range_constant_curve_is_zero():
    assert loudness.loudness_range([-14.0] * 20) == 0.0


def test_loudness_range_gates_silence_and_quiet_outliers():
    curve = [None, -90.0] + [-20.0] * 10 + [-10.0] * 10 + [-45.0]  # -45 is > 20 LU below the power mean
    assert loudness.loudness_range(curve) == 10.0


def test_loudness_range_needs_five_values():
    assert loudness.loudness_range([-14.0, -13.0, None]) is None


def test_seam_step_and_quality():
    loud_end = {"thirds_lufs": [-16.0, -13.0, -10.0]}
    quiet_open = {"thirds_lufs": [-19.0, -14.0, -12.0]}
    assert loudness.seam_step(loud_end, quiet_open) == -9.0
    assert loudness.seam_quality(-9.0) == "big jump (quieter)"
    assert loudness.seam_quality(4.2) == "noticeable (louder)"
    assert loudness.seam_quality(-2.9) == "smooth"
    assert loudness.seam_quality(None) is None


def test_seam_step_tolerates_missing_data():
    assert loudness.seam_step(None, {"thirds_lufs": [-10, -10, -10]}) is None
    assert loudness.seam_step({"thirds_lufs": [-10, -10, None]}, {"thirds_lufs": [-10, -10, -10]}) is None


@pytest.mark.skipif(UV is None, reason="uv not available to provision numpy/pyloudnorm")
def test_bs1770_reference_sine_and_build():
    code = f"""
import sys, numpy as np
sys.path.insert(0, {str(SHARED)!r})
import loudness
sr = 48000
t = np.arange(sr * 12) / sr
sine = 0.1 * np.sin(2 * np.pi * 997 * t)
s = loudness.summarize(sine, sr)
assert abs(s["integrated_lufs"] - (-23.0)) < 0.2, s
assert s["lra_lu"] is not None and s["lra_lu"] < 0.5, s
ramp = sine * np.repeat([0.5, 1.0, 2.0], sr * 4)
b = loudness.summarize(ramp, sr)["build_lu"]
assert abs(b - 12.04) < 0.3, b  # x4 amplitude from first third to last = +12 dB
print("ok")
"""
    proc = subprocess.run([UV, "run", "--quiet", "--no-project", "--with", "numpy", "--with", "pyloudnorm",
                           "python", "-c", code], capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "ok"
