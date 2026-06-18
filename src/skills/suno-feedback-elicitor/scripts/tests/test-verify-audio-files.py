#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Tests for verify-audio-files.py.

verify-audio-files.py is the receiving-machine half of the multi-machine
audio-drift pair: it compares local audio files against a canonical
audio-files-manifest.yaml and classifies each as matched / missing /
size_mismatch / extra. These tests round-trip with the manifest generator and
pin the three mismatch classes, the size-tolerance behavior, and the exit-code
contract (0 = clean, 1 = mismatches, 2 = error).
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
MANIFEST_SCRIPT = str(SCRIPTS / "audio-files-manifest.py")
VERIFY_SCRIPT = str(SCRIPTS / "verify-audio-files.py")


def run(script: str, args: list[str]) -> tuple[int, dict]:
    result = subprocess.run([sys.executable, script, *args], capture_output=True, text=True)
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


def test_verify_clean_round_trip_exits_0():
    root = make_project({"Song A.mp3": 1000, "Song B.mp3": 2000})
    run(MANIFEST_SCRIPT, [str(root)])
    code, out = run(VERIFY_SCRIPT, [str(root)])
    assert code == 0
    assert out["status"] == "ok"
    assert out["summary"]["missing"] == 0
    assert out["summary"]["size_mismatch"] == 0
    assert out["summary"]["extra"] == 0


def test_verify_detects_missing_and_extra_and_mismatch():
    root = make_project({"Song A.mp3": 1000, "Song B.mp3": 2000})
    run(MANIFEST_SCRIPT, [str(root)])
    audio = root / "docs" / "audio"
    (audio / "Song B.mp3").unlink()              # missing
    (audio / "Song A.mp3").write_bytes(b"x" * 50000)  # size_mismatch
    (audio / "Song C.mp3").write_bytes(b"x" * 3000)   # extra
    code, out = run(VERIFY_SCRIPT, [str(root)])
    assert code == 1
    assert out["status"] == "mismatch"
    assert out["summary"]["missing"] == 1
    assert out["summary"]["size_mismatch"] == 1
    assert out["summary"]["extra"] == 1


def test_verify_missing_manifest_exits_2():
    root = make_project({"Song A.mp3": 1000})
    code, out = run(VERIFY_SCRIPT, [str(root)])
    assert code == 2
    assert out["status"] == "error"
    assert out["error"] == "manifest-not-found"


def test_verify_size_tolerance_absorbs_id3_variance():
    root = make_project({"Song A.mp3": 100000})
    run(MANIFEST_SCRIPT, [str(root)])
    (root / "docs" / "audio" / "Song A.mp3").write_bytes(b"x" * 100512)  # +512, within 1024
    code, out = run(VERIFY_SCRIPT, [str(root)])
    assert code == 0
    assert out["summary"]["size_mismatch"] == 0


def test_verify_filename_variant_matches():
    """A -Redux variant of the canonical name still matches by normalized identity."""
    root = make_project({"Song A.mp3": 100000})
    run(MANIFEST_SCRIPT, [str(root)])
    audio = root / "docs" / "audio"
    (audio / "Song A.mp3").rename(audio / "Song A-Redux.mp3")
    code, out = run(VERIFY_SCRIPT, [str(root)])
    assert code == 0
    assert out["summary"]["matched"] == 1


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
