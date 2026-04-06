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


def test_check_first_run_true(tmp_path):
    """First run when sidecar doesn't exist."""
    assert mod.check_first_run(tmp_path) is True


def test_check_first_run_false(tmp_path):
    """Not first run when sidecar exists."""
    sidecar = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    sidecar.mkdir(parents=True)
    assert mod.check_first_run(tmp_path) is False


def test_scaffold_sidecar(tmp_path):
    """Scaffold creates all expected files."""
    result = mod.scaffold_sidecar(tmp_path)
    assert result["scaffolded"] is True
    assert "access-boundaries.md" in result["files_created"]
    assert "patterns.md" in result["files_created"]
    assert "chronology.md" in result["files_created"]

    sidecar = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    assert (sidecar / "access-boundaries.md").exists()
    assert (sidecar / "patterns.md").exists()
    assert (sidecar / "chronology.md").exists()


def test_scaffold_idempotent(tmp_path):
    """Scaffold doesn't overwrite existing files."""
    mod.scaffold_sidecar(tmp_path)
    sidecar = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"

    # Write custom content
    (sidecar / "patterns.md").write_text("custom content")

    result = mod.scaffold_sidecar(tmp_path)
    assert "patterns.md" not in result["files_created"]
    assert (sidecar / "patterns.md").read_text() == "custom content"


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
