#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Exit-code contract test for analyze-audio.py.

analyze-audio.py is one of the single-song intake scripts Step 2 invokes. A full
analysis test needs real audio fixtures and a heavy librosa provision, so this
test pins the deterministic contract the skill relies on: the script returns a
meaningful non-zero exit code when its audio directory is missing or empty,
rather than crashing with a traceback. It invokes via `uv run` so the librosa
PEP 723 deps are provisioned (the directory guard fires after the dep check).
Skips when uv is unavailable.
"""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).parent.parent / "analyze-audio.py")
UV = shutil.which("uv")
TIMEOUT = 600

pytestmark = pytest.mark.skipif(UV is None, reason="uv not available to provision librosa deps")


def run_uv(args: list[str]) -> int:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT).returncode


def test_missing_dir_exits_1():
    assert run_uv(["/nonexistent-audio-dir-xyz"]) == 1


def test_empty_dir_exits_1():
    assert run_uv([tempfile.mkdtemp()]) == 1


def test_find_mp3s_recurses_and_labels_band_folders(tmp_path):
    spec = importlib.util.spec_from_file_location("analyze_audio", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    (tmp_path / "band-a").mkdir()
    (tmp_path / ".hidden").mkdir()
    for rel in ("band-a/Song.mp3", "Loose.mp3", ".hidden/Skip.mp3", "notes.txt"):
        (tmp_path / rel).write_bytes(b"x")
    found = m.find_mp3s(str(tmp_path))
    assert [m.rel_label(p, str(tmp_path)) for p in found] == ["Loose.mp3", "band-a/Song.mp3"]


def test_text_and_json_report_loudness():
    spec = importlib.util.spec_from_file_location("analyze_audio_fmt", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    results = [
        {"file": "band-a/One.mp3", "duration": "3:10", "bpm_librosa": 152.0, "key": "F major", "key_confidence": 0.81,
         "loudness": {"integrated_lufs": -14.02, "lra_lu": 7.44, "thirds_lufs": [-16, -14, -13], "build_lu": 3.0}},
        {"file": "band-a/Two.mp3", "duration": "0:04", "bpm_librosa": 95.7, "key": "C minor", "key_confidence": 0.69,
         "loudness": {"integrated_lufs": -20.5, "lra_lu": None, "thirds_lufs": [None, None, None], "build_lu": None}},
    ]
    text = m.format_text_output(results, 2)
    assert "LUFS" in text and "aub" not in text
    assert "-14.02" in text and "Loudness range (integrated): -20.5 to -14.0 LUFS" in text
    data = m.format_json_output(results, 2)
    assert data["metrics"]["integrated_lufs_range"] == {"min": -20.5, "max": -14.02}


def test_beat_this_tempo_preferred_with_librosa_kept():
    spec = importlib.util.spec_from_file_location("analyze_audio_bt", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    loud = {"integrated_lufs": -14.0, "lra_lu": 6.0, "thirds_lufs": [-15, -14, -13], "build_lu": 2.0}
    results = [
        {"file": "a.mp3", "duration": "2:37", "bpm": 76.9, "bpm_beat_this": 76.9, "tempo_relation": "librosa_double",
         "tempo_source": "beat-this", "bpm_librosa": 152.0, "key": "F major", "key_confidence": 0.8, "loudness": loud},
        {"file": "b.mp3", "duration": "3:11", "bpm": 96.8, "bpm_beat_this": 96.8, "tempo_relation": "agree",
         "tempo_source": "beat-this", "bpm_librosa": 95.7, "key": "C minor", "key_confidence": 0.7, "loudness": loud},
    ]
    text = m.format_text_output(results, 2)
    assert "BPM range (Beat This!): 77 - 97" in text and "different pulse on 1 track" in text
    metrics = m.format_json_output(results, 2)["metrics"]
    assert metrics["tempo_source"] == "beat-this"
    assert metrics["bpm_range"] == {"min": 76.9, "max": 96.8}
    assert metrics["bpm_range_librosa"] == {"min": 95.7, "max": 152.0}


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
