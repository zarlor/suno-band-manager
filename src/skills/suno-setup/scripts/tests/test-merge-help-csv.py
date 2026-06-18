#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for merge-help-csv.py — anti-zombie row replacement, header handling,
legacy CSV cleanup, and error paths."""

import csv
import json
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "merge-help-csv.py"

HEADER = ("module,skill,display-name,menu-code,description,action,args,phase,"
          "after,before,required,output-location,outputs\n")


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run(args: list[str]) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, data


def read_rows(path: Path) -> list[list[str]]:
    return list(csv.reader(StringIO(path.read_text())))


def test_fresh_target_created():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        source = write(tmp / "src.csv", HEADER + "Suno,suno-setup,Setup,SU,desc,configure,,anytime,,,false,out,cfg\n")
        target = tmp / "module-help.csv"
        code, data = run(["--target", str(target), "--source", str(source)])
        assert code == 0, data
        assert data["target_existed"] is False
        rows = read_rows(target)
        assert rows[0][0] == "module"  # header
        assert any(r and r[0] == "Suno" for r in rows[1:])


def test_anti_zombie_replaces_same_module():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        target = write(tmp / "module-help.csv",
                       HEADER + "Suno,suno-old,Old,OL,olddesc,run,,anytime,,,false,,\n"
                       + "Other,other-skill,Keep,KP,keep,run,,anytime,,,false,,\n")
        source = write(tmp / "src.csv",
                       HEADER + "Suno,suno-setup,Setup,SU,newdesc,configure,,anytime,,,false,,\n")
        code, data = run(["--target", str(target), "--source", str(source)])
        assert code == 0, data
        rows = [r for r in read_rows(target) if r]
        modules = [r[0] for r in rows[1:]]
        # Old Suno row gone, Other preserved, new Suno present
        assert "Other" in modules
        skills = [r[1] for r in rows[1:]]
        assert "suno-old" not in skills
        assert "suno-setup" in skills
        assert data["rows_removed"] == 1


def test_empty_source_errors():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        source = write(tmp / "src.csv", HEADER)  # header only, no rows
        code, _ = run(["--target", str(tmp / "out.csv"), "--source", str(source)])
        assert code == 1


def test_legacy_csv_cleanup_requires_module_code():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        source = write(tmp / "src.csv", HEADER + "Suno,suno-setup,S,SU,d,run,,anytime,,,false,,\n")
        code, _ = run([
            "--target", str(tmp / "out.csv"), "--source", str(source),
            "--legacy-dir", str(tmp),
        ])
        assert code == 1


def test_legacy_csv_deleted():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        legacy = write(tmp / "suno" / "module-help.csv", HEADER)
        source = write(tmp / "src.csv", HEADER + "Suno,suno-setup,S,SU,d,run,,anytime,,,false,,\n")
        code, data = run([
            "--target", str(tmp / "out.csv"), "--source", str(source),
            "--legacy-dir", str(tmp), "--module-code", "suno",
        ])
        assert code == 0, data
        assert not legacy.exists()
        assert str(legacy) in data["legacy_csvs_deleted"]


if __name__ == "__main__":
    tests = [
        test_fresh_target_created,
        test_anti_zombie_replaces_same_module,
        test_empty_source_errors,
        test_legacy_csv_cleanup_requires_module_code,
        test_legacy_csv_deleted,
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
