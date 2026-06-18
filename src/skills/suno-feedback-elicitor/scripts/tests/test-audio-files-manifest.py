#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Tests for audio-files-manifest.py.

The manifest script captures size_bytes (+ mtime) per audio file on the
canonical machine so the small, machine-readable manifest can travel in the
portable-sync archive instead of the large MP3s. These tests pin the generation
output (file count, on-disk manifest) and the exit-code contract (0 = written,
1 = audio dir not found). The verify half is tested in test-verify-audio-files.py.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

SCRIPT = str(Path(__file__).parent.parent / "audio-files-manifest.py")


def run(args: list[str]) -> tuple[int, dict]:
    result = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    try:
        out = json.loads(result.stdout)
    except json.JSONDecodeError:
        out = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, out


def make_project(files: dict[str, int]) -> Path:
    root = Path(tempfile.mkdtemp())
    audio = root / "docs" / "audio"
    audio.mkdir(parents=True)
    for name, size in files.items():
        (audio / name).write_bytes(b"x" * size)
    return root


def test_manifest_generation_and_exit_code():
    root = make_project({"Song A.mp3": 1000, "Song B.mp3": 2000})
    code, out = run([str(root)])
    assert code == 0
    assert out["status"] == "ok"
    assert out["file_count"] == 2
    manifest_path = root / "docs" / "audio-files-manifest.yaml"
    assert manifest_path.is_file()
    data = yaml.safe_load(manifest_path.read_text())
    assert {f["name"] for f in data["files"]} == {"Song A.mp3", "Song B.mp3"}


def test_manifest_missing_audio_dir_exits_1():
    root = Path(tempfile.mkdtemp())
    code, out = run([str(root)])
    assert code == 1
    assert out["status"] == "error"
    assert out["error"] == "audio-dir-not-found"


def test_manifest_skips_non_audio_files():
    root = make_project({"Song A.mp3": 1000})
    (root / "docs" / "audio" / "notes.txt").write_text("not audio")
    code, out = run([str(root)])
    assert code == 0
    assert out["file_count"] == 1


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS: {test.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL: {test.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR: {test.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
    sys.exit(1 if failed else 0)
