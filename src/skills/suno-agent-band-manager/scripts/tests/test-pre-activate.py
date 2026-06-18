#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for pre-activate.py"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

# Load module
spec = spec_from_file_location(
    "pre_activate",
    Path(__file__).parent.parent / "pre-activate.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE_CSV = (
    "module,skill,display-name,menu-code,description,action,args,phase,after,before,required,output-location,outputs\n"
    'Suno Band Manager,suno-setup,Setup Suno Module,SU,"Install or update config.",configure,,anytime,,,false,,\n'
    'Suno Band Manager,suno-agent-band-manager,Create Song,CS,"Create a song package.",create-song,,anytime,,,false,,song package\n'
    'Suno Band Manager,suno-agent-band-manager,Refine Song,RS,"Refine a song.",refine-song,,anytime,,,false,,\n'
    'Suno Band Manager,suno-band-profile-manager,Manage Bands,MB,"Manage band profiles.",manage-profiles,,anytime,,,false,,\n'
)


# The real skill directory — init-sanctum.py reads its assets/ templates from here.
SKILL_DIR = Path(__file__).parent.parent.parent


def test_check_first_run_true(tmp_path):
    """First run when sanctum doesn't exist."""
    assert mod.check_first_run(tmp_path) is True


def test_check_first_run_false(tmp_path):
    """Not first run when sanctum exists."""
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    assert mod.check_first_run(tmp_path) is False


def test_check_first_run_honors_sanctum_dir_override(tmp_path):
    """--sanctum-dir override controls first-run detection."""
    staging = tmp_path / "staging"
    # Override points at a non-existent dir → first run.
    assert mod.check_first_run(tmp_path, sanctum_dir=str(staging)) is True
    staging.mkdir()
    assert mod.check_first_run(tmp_path, sanctum_dir=str(staging)) is False


def test_scaffold_delegates_to_init_sanctum(tmp_path):
    """Scaffold builds the v2 sanctum via init-sanctum.py (not the old stubs)."""
    (tmp_path / "_bmad").mkdir()
    result = mod.scaffold_sidecar(tmp_path, SKILL_DIR)
    assert result["scaffolded"] is True
    assert result["via"] == "init-sanctum.py"

    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    # v2 sanctum skeleton files (from assets/ templates), not the old 3 stubs.
    assert (sanctum / "INDEX.md").exists()
    assert (sanctum / "MEMORY.md").exists()
    assert (sanctum / "CREED.md").exists()
    assert (sanctum / "PERSONA.md").exists()
    assert (sanctum / "sessions").is_dir()


def test_scaffold_idempotent(tmp_path):
    """Scaffold is a no-op when the sanctum already exists (init-sanctum guards)."""
    (tmp_path / "_bmad").mkdir()
    mod.scaffold_sidecar(tmp_path, SKILL_DIR)
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    (sanctum / "MEMORY.md").write_text("custom content")

    # Second scaffold: init-sanctum.py reports "exists" and creates nothing.
    result = mod.scaffold_sidecar(tmp_path, SKILL_DIR)
    assert result["init_result"].get("status") == "exists"
    assert (sanctum / "MEMORY.md").read_text() == "custom content"


def _write_csv(tmp_path, content=SAMPLE_CSV):
    """Helper to write a test CSV file."""
    csv_path = tmp_path / "module-help.csv"
    csv_path.write_text(content)
    return csv_path


def test_render_menu(tmp_path):
    """Menu renders correctly from module-help.csv."""
    csv_path = _write_csv(tmp_path)

    menu = mod.render_menu(csv_path)
    # Setup skill entry should be excluded
    assert "Setup" not in menu
    # Agent and external skill entries should appear
    assert "[CS]" in menu
    assert "[RS]" in menu
    assert "[MB]" in menu
    assert "Create Song" in menu


def test_render_menu_excludes_setup(tmp_path):
    """Menu does not include the setup skill entry."""
    csv_path = _write_csv(tmp_path)
    menu = mod.render_menu(csv_path)
    assert "[SU]" not in menu


def test_build_routing_table_agent_capabilities(tmp_path):
    """Agent's own capabilities route to prompt references."""
    csv_path = _write_csv(tmp_path)

    table = mod.build_routing_table(csv_path)
    assert table["CS"]["type"] == "prompt"
    assert table["CS"]["target"] == "./references/create-song.md"
    assert table["RS"]["type"] == "prompt"
    assert table["RS"]["target"] == "./references/refine-song.md"


def test_build_routing_table_external_skills(tmp_path):
    """External skill capabilities route to skill invocation."""
    csv_path = _write_csv(tmp_path)

    table = mod.build_routing_table(csv_path)
    assert table["MB"]["type"] == "skill"
    assert table["MB"]["target"] == "suno-band-profile-manager"


def test_build_routing_table_numeric_keys(tmp_path):
    """Routing table includes numeric keys for positional access."""
    csv_path = _write_csv(tmp_path)

    table = mod.build_routing_table(csv_path)
    # First non-setup entry is CS at position 1
    assert table["1"]["name"] == "create-song"
    assert table["2"]["name"] == "refine-song"
    assert table["3"]["name"] == "manage-profiles"


def test_find_module_csv_installed(tmp_path):
    """Finds CSV at installed location."""
    bmad_dir = tmp_path / "_bmad"
    bmad_dir.mkdir()
    csv_file = bmad_dir / "module-help.csv"
    csv_file.write_text(SAMPLE_CSV)

    skill_dir = tmp_path / "skills" / "suno-agent-band-manager"
    skill_dir.mkdir(parents=True)

    result = mod.find_module_csv(tmp_path, skill_dir)
    assert result == csv_file


def test_find_module_csv_setup_assets(tmp_path):
    """Falls back to setup skill assets when not installed."""
    skills_dir = tmp_path / "skills"
    setup_assets = skills_dir / "suno-setup" / "assets"
    setup_assets.mkdir(parents=True)
    csv_file = setup_assets / "module-help.csv"
    csv_file.write_text(SAMPLE_CSV)

    skill_dir = skills_dir / "suno-agent-band-manager"
    skill_dir.mkdir(parents=True)

    result = mod.find_module_csv(tmp_path, skill_dir)
    assert result == csv_file


def test_find_module_csv_not_found(tmp_path):
    """Returns None when CSV is not found."""
    skill_dir = tmp_path / "skills" / "suno-agent-band-manager"
    skill_dir.mkdir(parents=True)

    result = mod.find_module_csv(tmp_path, skill_dir)
    assert result is None


def test_sanctum_load_order_is_the_canonical_seven(tmp_path):
    """The always-loaded rebirth set is exactly the canonical 7 files, in order."""
    assert mod.SANCTUM_LOAD_ORDER == [
        "access-boundaries.md",
        "INDEX.md",
        "MEMORY.md",
        "CREED.md",
        "PERSONA.md",
        "BOND.md",
        "CAPABILITIES.md",
    ]
    # access-boundaries.md must load FIRST (Dominion contract before any file op).
    assert mod.SANCTUM_LOAD_ORDER[0] == "access-boundaries.md"


def test_main_emits_menu_text_key(tmp_path, monkeypatch, capsys):
    """The pre-activate JSON output uses the `menu_text` key (not `menu`)."""
    bmad_dir = tmp_path / "_bmad"
    bmad_dir.mkdir()
    (bmad_dir / "module-help.csv").write_text(SAMPLE_CSV)

    monkeypatch.setattr(sys, "argv", ["pre-activate.py", str(tmp_path)])
    mod.main()
    payload = json.loads(capsys.readouterr().out)

    assert "menu_text" in payload
    assert "menu" not in payload
    assert "[CS]" in payload["menu_text"]
    # The load order is surfaced as the canonical 7.
    assert payload["sanctum_load_order"] == mod.SANCTUM_LOAD_ORDER
    assert len(payload["sanctum_load_order"]) == 7
