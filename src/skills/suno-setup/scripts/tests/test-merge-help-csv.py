#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for merge-help-csv.py — anti-zombie row replacement, header handling
(including the after,before → preceded-by,followed-by rewrite), no file
deletion, the unresolved-token guard, and error paths."""

import csv
import json
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "merge-help-csv.py"

HEADER = ("module,skill,display-name,menu-code,description,action,args,phase,"
          "preceded-by,followed-by,required,output-location,outputs\n")
OLD_HEADER = HEADER.replace("preceded-by,followed-by", "after,before")


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


def test_old_header_in_target_is_rewritten():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        target = write(tmp / "module-help.csv",
                       OLD_HEADER + "Other,other-skill,Keep,KP,keep,run,,anytime,a:b,,false,,\n")
        source = write(tmp / "src.csv", HEADER + "Suno,suno-setup,S,SU,d,run,,anytime,,,false,,\n")
        code, data = run(["--target", str(target), "--source", str(source)])
        assert code == 0, data
        assert data["header_migrated"] is True
        rows = read_rows(target)
        assert rows[0][8:10] == ["preceded-by", "followed-by"]
        # Row data is positional and unchanged.
        assert ["Other", "other-skill", "Keep", "KP", "keep", "run", "", "anytime", "a:b", "", "false", "", ""] in rows


def test_old_header_in_source_is_canonicalized():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        source = write(tmp / "src.csv", OLD_HEADER + "Suno,suno-setup,S,SU,d,run,,anytime,,,false,,\n")
        target = tmp / "module-help.csv"
        code, data = run(["--target", str(target), "--source", str(source)])
        assert code == 0, data
        assert read_rows(target)[0][8:10] == ["preceded-by", "followed-by"]


def test_no_files_deleted():
    """Per-module CSVs (core/, suno/) are installer sources — never deleted."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        core_csv = write(tmp / "core" / "module-help.csv", HEADER)
        suno_csv = write(tmp / "suno" / "module-help.csv", HEADER)
        source = write(tmp / "src.csv", HEADER + "Suno,suno-setup,S,SU,d,run,,anytime,,,false,,\n")
        code, data = run(["--target", str(tmp / "module-help.csv"), "--source", str(source)])
        assert code == 0, data
        assert core_csv.exists() and suno_csv.exists()


def test_legacy_dir_option_is_gone():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        source = write(tmp / "src.csv", HEADER + "Suno,suno-setup,S,SU,d,run,,anytime,,,false,,\n")
        code, _ = run(["--target", str(tmp / "out.csv"), "--source", str(source), "--legacy-dir", str(tmp)])
        assert code != 0


def test_unresolved_project_root_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        source = write(tmp / "src.csv", HEADER + "Suno,suno-setup,S,SU,d,run,,anytime,,,false,,\n")
        code, data = run(["--target", "{project-root}/_bmad/module-help.csv", "--source", str(source)])
        assert code == 1, data
        assert "{project-root}" in data["error"]
        assert not Path("{project-root}").exists()


if __name__ == "__main__":
    tests = [
        test_fresh_target_created,
        test_anti_zombie_replaces_same_module,
        test_empty_source_errors,
        test_old_header_in_target_is_rewritten,
        test_old_header_in_source_is_canonicalized,
        test_no_files_deleted,
        test_legacy_dir_option_is_gone,
        test_unresolved_project_root_rejected,
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
