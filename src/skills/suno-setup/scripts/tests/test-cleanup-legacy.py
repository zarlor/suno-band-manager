#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for cleanup-legacy.py — install-verification gating, config.yaml
preservation, no-skill direct removal, idempotency, and exit codes."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "cleanup-legacy.py"


def run(args: list[str]) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, data


def make_skill(base: Path, name: str):
    skill = base / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n")
    return skill


def test_verified_removal_with_skills_installed():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bmad = tmp / "_bmad"
        skills_dir = tmp / ".claude" / "skills"
        # legacy suno/ holds a skill that is installed
        make_skill(bmad / "suno", "suno-agent-band-manager")
        (bmad / "suno" / "extra.txt").write_text("x")
        make_skill(skills_dir, "suno-agent-band-manager")
        # core/ with config.yaml to preserve
        (bmad / "core").mkdir(parents=True)
        (bmad / "core" / "config.yaml").write_text("user_name: Lenny\n")
        (bmad / "core" / "junk.txt").write_text("junk")

        code, data = run([
            "--bmad-dir", str(bmad), "--module-code", "suno",
            "--skills-dir", str(skills_dir),
        ])
        assert code == 0, data
        assert "suno" in data["directories_removed"]
        # config.yaml preserved in core/
        assert (bmad / "core" / "config.yaml").exists()
        # non-config files gone
        assert not (bmad / "core" / "junk.txt").exists()
        assert not (bmad / "suno" / "extra.txt").exists()
        # installed skill untouched
        assert (skills_dir / "suno-agent-band-manager" / "SKILL.md").exists()


def test_missing_skill_blocks_removal_exit_1():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bmad = tmp / "_bmad"
        skills_dir = tmp / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        make_skill(bmad / "suno", "suno-agent-band-manager")  # NOT installed

        code, data = run([
            "--bmad-dir", str(bmad), "--module-code", "suno",
            "--skills-dir", str(skills_dir),
        ])
        assert code == 1, (code, data)
        assert data["status"] == "error"
        assert "suno-agent-band-manager" in data["missing_skills"]
        # nothing removed
        assert (bmad / "suno").exists()


def test_no_skill_dir_removed_directly():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bmad = tmp / "_bmad"
        (bmad / "_config").mkdir(parents=True)
        (bmad / "_config" / "stuff.txt").write_text("x")
        skills_dir = tmp / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        code, data = run([
            "--bmad-dir", str(bmad), "--module-code", "suno",
            "--also-remove", "_config", "--skills-dir", str(skills_dir),
        ])
        assert code == 0, data
        assert "_config" in data["directories_removed"]
        assert not (bmad / "_config").exists()


def test_idempotent_missing_dirs_not_error():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bmad = tmp / "_bmad"
        bmad.mkdir()
        code, data = run([
            "--bmad-dir", str(bmad), "--module-code", "suno", "--also-remove", "_config",
        ])
        assert code == 0, data
        assert set(data["directories_not_found"]) >= {"suno", "core", "_config"}
        assert data["directories_removed"] == []


if __name__ == "__main__":
    tests = [
        test_verified_removal_with_skills_installed,
        test_missing_skill_blocks_removal_exit_1,
        test_no_skill_dir_removed_directly,
        test_idempotent_missing_dirs_not_error,
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
