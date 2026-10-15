#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for init-sanctum.py — fresh BMad v7 sanctum scaffolding for Mac."""

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
    """A minimal project: BMad config and the owner's voice file (which names them before BOND.md exists)."""
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "config.toml").write_text('[modules.suno]\nsuno_tier = "pro"\n')
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "voice-context-testuser.md").write_text("# voice\n")
    return tmp_path


def sanctum_of(project):
    return project / "_bmad" / "memory" / "suno-agent-band-manager"


IDENTITY = ["PERSONA.md", "CREED.md", "BOND.md", "HOW-I-REMEMBER.md", "CAPABILITIES.md"]


def test_scaffold_creates_sanctum_at_the_v7_path(project):
    result = mod.scaffold(project, SKILL_DIR)
    assert result["status"] == "created"
    assert sanctum_of(project).is_dir()
    assert not (project / "_bmad" / "_memory").exists()


def test_fresh_birth_has_identity_files_and_folders(project):
    mod.scaffold(project, SKILL_DIR)
    sanctum = sanctum_of(project)
    for name in [*IDENTITY, "PULSE.md"]:
        assert (sanctum / name).read_text(encoding="utf-8").strip(), f"missing or empty: {name}"
    for folder in ("raw", "capabilities", "memory/work", "memory/catalog", "memory/disciplines", "memory/sessions"):
        assert (sanctum / folder).is_dir(), folder
    for old in ("INDEX.md", "MEMORY.md", "access-boundaries.md", "sessions"):
        assert not (sanctum / old).exists(), f"v2 leftover: {old}"


def test_scaffold_substitutes_variables(project):
    mod.scaffold(project, SKILL_DIR)
    persona = (sanctum_of(project) / "PERSONA.md").read_text()
    assert "Testuser" in persona
    assert "{user_name}" not in persona


def test_standing_files_seeded_from_memory_template(project):
    mod.scaffold(project, SKILL_DIR)
    sanctum = sanctum_of(project)
    assert "## " not in (sanctum / "memory/work/downloads.md").read_text().split("\n", 1)[1]
    assert (sanctum / "memory/work/downloads.md").read_text().startswith("# Downloads")
    assert (sanctum / "memory/owner/preferences.md").is_file()
    published = (sanctum / "memory/catalog/recently-published.md").read_text()
    status = (sanctum / "memory/catalog/status.md").read_text()
    assert "<!-- derived:recently-published:start -->" in published and "<!-- derived:recently-published:end -->" in published
    assert "<!-- derived:catalog-status:start -->" in status and "<!-- derived:catalog-status:end -->" in status
    assert not (sanctum / "memory/pending.md").exists()  # nothing to raise yet
    assert not (sanctum / "memory/work/session-history.md").exists()  # session notes live in memory/sessions/


def test_scaffold_is_idempotent_no_clobber(project):
    mod.scaffold(project, SKILL_DIR)
    second = mod.scaffold(project, SKILL_DIR)
    assert second["status"] == "exists"


def test_default_user_name_when_no_config(tmp_path):
    (tmp_path / "_bmad").mkdir()
    result = mod.scaffold(tmp_path, SKILL_DIR)
    assert result["status"] == "created"
    bond = (sanctum_of(tmp_path) / "BOND.md").read_text()
    assert "_(not yet known)_" in bond and "friend" not in bond
    assert "docs/voice-context-<owner>.md" in bond


def test_fresh_birth_has_disciplines_and_incidents(project):
    mod.scaffold(project, SKILL_DIR)
    sanctum = sanctum_of(project)
    for name in ("package-assembly.md", "workshop-capture.md", "research-discipline.md",
                 "catalog-verification-discipline.md", "hedge-preservation-discipline.md"):
        assert (sanctum / "memory/disciplines" / name).read_text(encoding="utf-8").strip(), name
    assert any((sanctum / "memory/incidents").iterdir())


def test_creed_carries_the_dominion_with_substituted_paths(project):
    mod.scaffold(project, SKILL_DIR)
    creed = (sanctum_of(project) / "CREED.md").read_text(encoding="utf-8")
    dominion = creed.split("## Dominion (Access Boundaries)", 1)[1].split("\n## ", 1)[0]
    for sub in ("### Read Access", "### Write Access", "### The Write Rule", "### Deny Zones"):
        assert sub in dominion
    assert "{dominion}" not in creed and "{project_root}" not in creed
    assert str(project) in dominion
    assert "_bmad/memory/suno-agent-band-manager/" in dominion
    assert "memory/disciplines/package-assembly.md" in creed


def test_fresh_birth_history_is_honest_no_migration_fiction(project):
    """A fresh birth must NOT claim migrated memories (none existed)."""
    mod.scaffold(project, SKILL_DIR)
    sanctum = sanctum_of(project)
    persona = (sanctum / "PERSONA.md").read_text(encoding="utf-8")
    assert "memories migrated" not in persona
    assert "Reborn into the v2 sanctum" not in persona
    assert "First Breath" in persona


def test_fresh_birth_matches_conversion_file_set(project):
    """A fresh birth has the identity set and memory kinds a converted sanctum has."""
    mod.scaffold(project, SKILL_DIR)
    sanctum = sanctum_of(project)
    born = {p.name for p in sanctum.iterdir()}
    assert set(IDENTITY) | {"PULSE.md", "memory", "raw", "capabilities"} <= born


def test_capabilities_md_carries_builtin_roster(project):
    """CAPABILITIES.md lists Mac's real capabilities from assets/menu.csv."""
    mod.scaffold(project, SKILL_DIR)
    caps = (sanctum_of(project) / "CAPABILITIES.md").read_text()
    assert "| [CS] | Create Song |" in caps
    assert "| [RS] | Refine Song |" in caps
    assert "| [FL] |" not in caps
    assert "## Learned" in caps


def test_fresh_birth_templates_carry_no_install_history(project):
    mod.scaffold(project, SKILL_DIR)
    sanctum = sanctum_of(project)
    bond = (sanctum / "BOND.md").read_text()
    assert "patterns.md" not in bond
    persona = (sanctum / "PERSONA.md").read_text()
    assert "v4.5" not in persona and "v5.5" not in persona
    assert "SUNO-REFERENCE.md" in persona


def test_fresh_birth_creed_has_standing_orders_and_mission_placeholder(project):
    mod.scaffold(project, SKILL_DIR)
    creed = (sanctum_of(project) / "CREED.md").read_text()
    assert "## Standing Orders" in creed
    assert "references/prompt-quality-canon.md" in creed
    assert "Discovered during First Breath" in creed
    assert "You wake." in creed
    assert "Settings in Controls panel order" in creed


def test_how_i_remember_and_pulse_describe_the_v7_layout(project):
    mod.scaffold(project, SKILL_DIR)
    sanctum = sanctum_of(project)
    how = (sanctum / "HOW-I-REMEMBER.md").read_text()
    assert "memory/work/current.md" in how and "raw/" in how and "memory/.tended" in how
    pulse = (sanctum / "PULSE.md").read_text()
    assert "memory/pending.md" in pulse and "MEMORY.md" not in pulse
    assert "_bmad/memory/suno-agent-band-manager/" in pulse


def test_bundle_ships_what_the_canon_order_points_to():
    """The CREED's Author-to-the-standard order points at files the skill ships."""
    assert (SKILL_DIR / "references" / "prompt-quality-canon.md").is_file()
    assert (SKILL_DIR / "references" / "capability-authoring.md").is_file()
