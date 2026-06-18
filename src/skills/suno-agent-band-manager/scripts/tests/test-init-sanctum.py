#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for init-sanctum.py — fresh v2 sanctum scaffolding for Mac."""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

spec = spec_from_file_location("init_sanctum", SCRIPTS_DIR / "init-sanctum.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


@pytest.fixture
def project(tmp_path):
    """A minimal project with a _bmad/config.yaml."""
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "config.yaml").write_text(
        "user_name: TestUser\ncommunication_language: English\n"
    )
    return tmp_path


def test_scaffold_creates_sanctum_at_bespoke_path(project):
    result = mod.scaffold(project, SKILL_DIR)
    assert result["status"] == "created"
    sanctum = project / "_bmad" / "_memory" / "band-manager-sidecar"
    assert sanctum.is_dir()
    # Preserved divergence: double-underscore _memory, not _bmad/memory.
    assert not (project / "_bmad" / "memory").exists()


def test_scaffold_creates_allcaps_files_and_dirs(project):
    mod.scaffold(project, SKILL_DIR)
    sanctum = project / "_bmad" / "_memory" / "band-manager-sidecar"
    for name in ("INDEX.md", "PERSONA.md", "CREED.md", "BOND.md", "MEMORY.md", "PULSE.md"):
        assert (sanctum / name).exists(), f"missing {name}"
    assert (sanctum / "CAPABILITIES.md").exists()
    assert (sanctum / "sessions").is_dir()
    assert (sanctum / "capabilities").is_dir()


def test_scaffold_substitutes_variables(project):
    mod.scaffold(project, SKILL_DIR)
    sanctum = project / "_bmad" / "_memory" / "band-manager-sidecar"
    persona = (sanctum / "PERSONA.md").read_text()
    assert "TestUser" in persona
    assert "{user_name}" not in persona


def test_memory_template_carries_derived_markers(project):
    mod.scaffold(project, SKILL_DIR)
    sanctum = project / "_bmad" / "_memory" / "band-manager-sidecar"
    memory = (sanctum / "MEMORY.md").read_text()
    assert "<!-- derived:recently-published:start -->" in memory
    assert "<!-- derived:recently-published:end -->" in memory
    assert "<!-- derived:catalog-status:start -->" in memory
    assert "<!-- derived:catalog-status:end -->" in memory


def test_scaffold_is_idempotent_no_clobber(project):
    mod.scaffold(project, SKILL_DIR)
    second = mod.scaffold(project, SKILL_DIR)
    assert second["status"] == "exists"


def test_default_user_name_when_no_config(tmp_path):
    (tmp_path / "_bmad").mkdir()
    result = mod.scaffold(tmp_path, SKILL_DIR)
    assert result["status"] == "created"
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    assert "friend" in (sanctum / "BOND.md").read_text()
