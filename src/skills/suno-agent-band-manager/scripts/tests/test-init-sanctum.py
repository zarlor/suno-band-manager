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


# ---------------------------------------------------------------------------
# Fresh-birth ≠ migrated-birth ACCEPTANCE TEST (Theme 1)
# A freshly-born sanctum must contain the SAME file set the migration produces:
# all 7 always-loaded files + the 3 on-demand creed shards + the incident log.
# ---------------------------------------------------------------------------

ALWAYS_LOADED_SEVEN = [
    "access-boundaries.md",
    "INDEX.md",
    "MEMORY.md",
    "CREED.md",
    "PERSONA.md",
    "BOND.md",
    "CAPABILITIES.md",
]

CREED_SHARDS = [
    "creed-disciplines.md",
    "creed-workshop-capture.md",
    "creed-package-assembly.md",
]


def test_fresh_birth_has_all_seven_always_loaded_files(project):
    """All 7 always-loaded files exist and are non-empty after a fresh birth."""
    mod.scaffold(project, SKILL_DIR)
    sanctum = project / "_bmad" / "_memory" / "band-manager-sidecar"
    for name in ALWAYS_LOADED_SEVEN:
        path = sanctum / name
        assert path.exists(), f"missing always-loaded file: {name}"
        assert path.read_text(encoding="utf-8").strip(), f"empty always-loaded file: {name}"


def test_fresh_birth_has_creed_shards_and_incident_log(project):
    """The 3 on-demand creed shards + the non-loaded incident log exist, non-empty."""
    mod.scaffold(project, SKILL_DIR)
    sanctum = project / "_bmad" / "_memory" / "band-manager-sidecar"
    for name in CREED_SHARDS + ["creed-incident-log.md"]:
        path = sanctum / name
        assert path.exists(), f"missing creed shard: {name}"
        assert path.read_text(encoding="utf-8").strip(), f"empty creed shard: {name}"


def test_fresh_birth_access_boundaries_loads_first_and_substitutes(project):
    """access-boundaries.md is the loaded-first Dominion contract, no raw placeholders."""
    mod.scaffold(project, SKILL_DIR)
    sanctum = project / "_bmad" / "_memory" / "band-manager-sidecar"
    text = (sanctum / "access-boundaries.md").read_text(encoding="utf-8")
    assert "Access Boundaries for Mac" in text
    assert "Deny Zones" in text
    # {project_root} placeholder must have been substituted.
    assert "{project_root}" not in text
    assert str(project) in text


def test_fresh_birth_history_is_honest_no_migration_fiction(project):
    """A fresh birth must NOT claim migrated memories (none existed)."""
    mod.scaffold(project, SKILL_DIR)
    sanctum = project / "_bmad" / "_memory" / "band-manager-sidecar"
    memory = (sanctum / "MEMORY.md").read_text(encoding="utf-8")
    persona = (sanctum / "PERSONA.md").read_text(encoding="utf-8")
    # The seeded "sanctum migration" / "memories migrated" framing is removed.
    assert "sanctum migration" not in memory
    assert "memories migrated" not in persona
    assert "Reborn into the v2 sanctum" not in persona
    # The honest first-session markers are present instead.
    assert "First Breath" in memory
    assert "First Breath" in persona


def test_fresh_birth_matches_migration_file_set(project):
    """The fresh-born file set is a superset of the migration's seeded sanctum files.

    The migration tool produces the same always-loaded skeleton, access-boundaries,
    creed shards, and incident log (plus migrated session/preserved files). A fresh
    birth must produce that core seeded set so the activation contract — which is
    written against the migrated shape — holds for a born sanctum too.
    """
    mod.scaffold(project, SKILL_DIR)
    sanctum = project / "_bmad" / "_memory" / "band-manager-sidecar"
    born = {p.name for p in sanctum.iterdir() if p.is_file()}
    expected = set(ALWAYS_LOADED_SEVEN) | set(CREED_SHARDS) | {
        "creed-incident-log.md", "INDEX.md", "PULSE.md",
    }
    missing = expected - born
    assert not missing, f"fresh birth missing seeded files: {sorted(missing)}"
