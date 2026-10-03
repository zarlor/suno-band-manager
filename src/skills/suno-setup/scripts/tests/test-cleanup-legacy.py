#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for cleanup-legacy.py — scope (only suno-* skill copies under
_bmad/suno/), install verification, installer-managed skips, dry run,
idempotency, the unresolved-token guard and exit codes."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "cleanup-legacy.py"


def run(args: list[str]) -> tuple[int, dict]:
    result = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, data


def make_skill(base: Path, name: str) -> Path:
    skill = base / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n")
    return skill


def layout(tmp: Path) -> tuple[Path, Path]:
    bmad = tmp / "_bmad"
    skills_dir = tmp / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    return bmad, skills_dir


def test_removes_only_verified_suno_skill_copies():
    with tempfile.TemporaryDirectory() as tmp:
        bmad, skills_dir = layout(Path(tmp))
        make_skill(bmad / "suno", "suno-agent-band-manager")
        make_skill(bmad / "suno" / "skills", "suno-lyric-transformer")
        make_skill(skills_dir, "suno-agent-band-manager")
        make_skill(skills_dir, "suno-lyric-transformer")
        (bmad / "suno" / "config.yaml").write_text("suno_tier: pro\n")
        (bmad / "suno" / "module-help.csv").write_text("module\n")
        (bmad / "suno" / "extra.txt").write_text("x")
        make_skill(bmad / "suno", "other-skill")  # not named suno-*
        (bmad / "core").mkdir()
        (bmad / "core" / "junk.txt").write_text("junk")
        (bmad / "_config").mkdir()
        (bmad / "_config" / "stuff.txt").write_text("x")

        code, data = run(["--bmad-dir", str(bmad), "--module-code", "suno", "--skills-dir", str(skills_dir)])
        assert code == 0, data
        assert sorted(r["path"] for r in data["removed"]) == [
            "suno/skills/suno-lyric-transformer", "suno/suno-agent-band-manager"]
        assert data["files_removed_count"] == 2
        assert not (bmad / "suno" / "skills").exists()  # emptied container removed
        for kept in ("suno/config.yaml", "suno/module-help.csv", "suno/extra.txt",
                     "suno/other-skill/SKILL.md", "core/junk.txt", "_config/stuff.txt"):
            assert (bmad / kept).exists(), kept
        assert (skills_dir / "suno-agent-band-manager" / "SKILL.md").exists()


def test_unverified_copy_is_kept_not_error():
    with tempfile.TemporaryDirectory() as tmp:
        bmad, skills_dir = layout(Path(tmp))
        make_skill(bmad / "suno", "suno-agent-band-manager")  # NOT installed
        code, data = run(["--bmad-dir", str(bmad), "--module-code", "suno", "--skills-dir", str(skills_dir)])
        assert code == 0, data
        assert data["removed"] == []
        assert data["unverified"] == ["suno/suno-agent-band-manager"]
        assert (bmad / "suno" / "suno-agent-band-manager").exists()


def test_second_skills_dir_verifies():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bmad, claude_skills = layout(tmp)
        agents_skills = tmp / ".agents" / "skills"
        make_skill(agents_skills, "suno-setup")
        make_skill(bmad / "suno", "suno-setup")
        code, data = run(["--bmad-dir", str(bmad), "--module-code", "suno",
                          "--skills-dir", str(claude_skills), "--skills-dir", str(agents_skills)])
        assert code == 0, data
        assert [r["path"] for r in data["removed"]] == ["suno/suno-setup"]


def test_no_skills_dir_skips_with_reason():
    with tempfile.TemporaryDirectory() as tmp:
        bmad = Path(tmp) / "_bmad"
        make_skill(bmad / "suno", "suno-setup")
        code, data = run(["--bmad-dir", str(bmad), "--module-code", "suno",
                          "--skills-dir", str(Path(tmp) / "missing")])
        assert code == 0, data
        assert "skipped_reason" in data
        assert (bmad / "suno" / "suno-setup").exists()


def test_dry_run_deletes_nothing():
    with tempfile.TemporaryDirectory() as tmp:
        bmad, skills_dir = layout(Path(tmp))
        make_skill(bmad / "suno", "suno-setup")
        make_skill(skills_dir, "suno-setup")
        code, data = run(["--bmad-dir", str(bmad), "--module-code", "suno",
                          "--skills-dir", str(skills_dir), "--dry-run"])
        assert code == 0, data
        assert data["dry_run"] is True
        assert data["would_remove"] == [{"path": "suno/suno-setup", "file_count": 1}]
        assert (bmad / "suno" / "suno-setup" / "SKILL.md").exists()


def test_installer_tracked_copy_is_skipped():
    with tempfile.TemporaryDirectory() as tmp:
        bmad, skills_dir = layout(Path(tmp))
        make_skill(bmad / "suno", "suno-setup")
        make_skill(skills_dir, "suno-setup")
        (bmad / "_config").mkdir()
        (bmad / "_config" / "manifest.yaml").write_text("modules:\n  - name: core\n")
        (bmad / "_config" / "files-manifest.csv").write_text(
            'type,name,module,path,hash\n"md","skill","suno","suno/suno-setup/SKILL.md","x"\n')
        code, data = run(["--bmad-dir", str(bmad), "--module-code", "suno", "--skills-dir", str(skills_dir)])
        assert code == 0, data
        assert data["removed"] == []
        assert data["skipped_installer_managed"] == ["suno/suno-setup"]
        assert (bmad / "suno" / "suno-setup").exists()


def test_installer_listed_module_is_left_alone():
    with tempfile.TemporaryDirectory() as tmp:
        bmad, skills_dir = layout(Path(tmp))
        make_skill(bmad / "suno", "suno-setup")
        make_skill(skills_dir, "suno-setup")
        (bmad / "_config").mkdir()
        (bmad / "_config" / "manifest.yaml").write_text("modules:\n  - name: core\n  - name: suno\n")
        code, data = run(["--bmad-dir", str(bmad), "--module-code", "suno", "--skills-dir", str(skills_dir)])
        assert code == 0, data
        assert data["removed"] == []
        assert "installer" in data["skipped_reason"]


def test_protected_module_codes_refused():
    with tempfile.TemporaryDirectory() as tmp:
        bmad = Path(tmp) / "_bmad"
        (bmad / "core").mkdir(parents=True)
        for code_name in ("core", "_config", "../x", "scripts"):
            code, data = run(["--bmad-dir", str(bmad), "--module-code", code_name])
            assert code == 1, (code_name, data)
        assert (bmad / "core").exists()


def test_also_remove_option_is_gone():
    with tempfile.TemporaryDirectory() as tmp:
        bmad = Path(tmp) / "_bmad"
        (bmad / "_config").mkdir(parents=True)
        result = subprocess.run([sys.executable, str(SCRIPT), "--bmad-dir", str(bmad), "--module-code", "suno",
                                 "--also-remove", "_config"], capture_output=True, text=True)
        assert result.returncode != 0
        assert (bmad / "_config").exists()


def test_idempotent_missing_module_dir():
    with tempfile.TemporaryDirectory() as tmp:
        bmad = Path(tmp) / "_bmad"
        bmad.mkdir()
        code, data = run(["--bmad-dir", str(bmad), "--module-code", "suno"])
        assert code == 0, data
        assert data["removed"] == []


def test_unresolved_project_root_rejected():
    code, data = run(["--bmad-dir", "{project-root}/_bmad", "--module-code", "suno"])
    assert code == 1, data
    assert "{project-root}" in data["error"]
