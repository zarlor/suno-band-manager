#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for upgrade-sanctum.py — v2 -> v2 template upgrades, owner content kept."""

import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))


def _load(name, filename):
    spec = spec_from_file_location(name, SCRIPTS_DIR / filename)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load("upgrade_sanctum", "upgrade-sanctum.py")
init = _load("init_sanctum", "init-sanctum.py")


@pytest.fixture
def born(tmp_path):
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "config.yaml").write_text("user_name: Sam\ncommunication_language: English\n")
    init.scaffold(tmp_path, SKILL_DIR)
    return tmp_path, bmad / "_memory" / "band-manager-sidecar"


def snapshot(sanctum):
    return {p.name: p.read_bytes() for p in sanctum.iterdir() if p.is_file()}


def test_fresh_sanctum_needs_nothing(born):
    root, sanctum = born
    report = mod.plan(root, sanctum, SKILL_DIR)
    assert report["status"] == "dry-run"
    assert report["changes"] == []


def test_dry_run_writes_nothing(born):
    root, sanctum = born
    creed = sanctum / "CREED.md"
    creed.write_text(creed.read_text().replace("You wake.", "A fresh start is always valid."))
    before = snapshot(sanctum)
    report = mod.plan(root, sanctum, SKILL_DIR)
    assert any(c["kind"] == "replace-section" for c in report["changes"])
    assert snapshot(sanctum) == before


def test_missing_section_is_safe_add_and_applies(born):
    root, sanctum = born
    creed = sanctum / "CREED.md"
    text = creed.read_text()
    start = text.index("## Standing Orders")
    end = text.index("## Package Assembly Rule")
    creed.write_text(text[:start] + text[end:])
    report = mod.plan(root, sanctum, SKILL_DIR)
    adds = [c for c in report["changes"] if c["kind"] == "add-section"]
    assert adds and adds[0]["heading"] == "## Standing Orders" and adds[0]["safe"]
    result = mod.apply_changes(sanctum, report, {"safe"})
    assert result["status"] == "applied"
    new = creed.read_text()
    assert new.index("## Standing Orders") < new.index("## Package Assembly Rule")
    assert result["backup_path"] and Path(result["backup_path"], "CREED.md").is_file()
    assert mod.plan(root, sanctum, SKILL_DIR)["changes"] == []


def test_replacement_needs_its_id(born):
    root, sanctum = born
    persona = sanctum / "PERSONA.md"
    persona.write_text(persona.read_text().replace("SUNO-REFERENCE.md", "v5.5 (paid)"))
    report = mod.plan(root, sanctum, SKILL_DIR)
    (change,) = [c for c in report["changes"] if c["file"] == "PERSONA.md"]
    assert change["kind"] == "replace-section" and change["safe"] is False
    # 'safe' alone does not touch it.
    mod.apply_changes(sanctum, report, {"safe"})
    assert "v5.5 (paid)" in persona.read_text()
    # Naming the id applies it.
    mod.apply_changes(sanctum, report, {change["id"]})
    assert "v5.5 (paid)" not in persona.read_text()
    assert "SUNO-REFERENCE.md" in persona.read_text()


def test_owner_sections_are_never_proposed(born):
    root, sanctum = born
    persona = sanctum / "PERSONA.md"
    persona.write_text(persona.read_text() + "- **2026-10-01** — Learned to hold the bridge back.\n")
    creed = sanctum / "CREED.md"
    creed.write_text(creed.read_text().replace("Discovered during First Breath", "For Sam: a personal catalog"))
    memory = sanctum / "MEMORY.md"
    memory.write_text(memory.read_text().replace("_(empty — first session)_", "Working on a song", 1))
    report = mod.plan(root, sanctum, SKILL_DIR)
    assert report["changes"] == []
    kept = " ".join(report["owner_sections_kept"])
    assert "PERSONA.md ## Evolution Log" in kept
    assert "CREED.md ## Mission" in kept
    assert "MEMORY.md ## Current Work" in kept


def test_memory_only_gains_sections(born):
    root, sanctum = born
    memory = sanctum / "MEMORY.md"
    text = memory.read_text()
    start = text.index("## Downloads")
    end = text.index("## Default Exclusions")
    memory.write_text(text[:start] + text[end:])
    report = mod.plan(root, sanctum, SKILL_DIR)
    (change,) = report["changes"]
    assert change["kind"] == "add-section" and change["heading"] == "## Downloads"
    mod.apply_changes(sanctum, report, {"safe"})
    new = memory.read_text()
    assert new.index("## User Preferences") < new.index("## Downloads") < new.index("## Default Exclusions")


def test_index_rows_merge_and_heading_rename(born):
    root, sanctum = born
    index = sanctum / "INDEX.md"
    text = index.read_text().replace("## Loaded on Waking (always)", "## Loaded on Rebirth (always)")
    text = text.replace(
        "| `PULSE.md` | The maintenance-wake routine and the owner's Pulse preferences | Pulse wakes (`--pulse`), or when the owner asks about Pulse |\n",
        "",
    )
    text = text.replace("## Growth Rule", "| `extra.md` | owner row | x |\n\n## Growth Rule")
    index.write_text(text)
    report = mod.plan(root, sanctum, SKILL_DIR)
    kinds = sorted(c["kind"] for c in report["changes"])
    assert kinds == ["add-rows", "rename-heading"]
    mod.apply_changes(sanctum, report, {"safe"})
    new = index.read_text()
    assert "## Loaded on Waking (always)" in new and "Rebirth" not in new
    assert "| `PULSE.md` |" in new
    assert "| `extra.md` | owner row | x |" in new  # owner row kept


def test_missing_shard_is_created(born):
    root, sanctum = born
    (sanctum / "creed-package-assembly.md").unlink()
    report = mod.plan(root, sanctum, SKILL_DIR)
    (change,) = report["changes"]
    assert change["kind"] == "create-file" and change["safe"]
    assert report["sidecar_format"] == "v2"
    mod.apply_changes(sanctum, report, {"safe"})
    assert (sanctum / "creed-package-assembly.md").is_file()


def test_damaged_spine_restores_only_missing_files(born):
    root, sanctum = born
    (sanctum / "BOND.md").unlink()
    report = mod.plan(root, sanctum, SKILL_DIR)
    assert report["sidecar_format"] == "damaged"
    assert [c["file"] for c in report["changes"]] == ["BOND.md"]


def test_incident_log_is_create_only(born):
    root, sanctum = born
    log = sanctum / "creed-incident-log.md"
    log.write_text("# owner incident archive\n")
    report = mod.plan(root, sanctum, SKILL_DIR)
    assert report["changes"] == []


def test_v1_store_is_not_applicable(tmp_path):
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    (sanctum / "index.md").write_text("# v1\n")
    report = mod.plan(tmp_path, sanctum, SKILL_DIR)
    assert report["status"] == "not-applicable"
    assert "migrate" in report["message"]


def test_cli_json_dry_run(born, monkeypatch, capsys):
    root, sanctum = born
    monkeypatch.setattr(sys, "argv", ["upgrade-sanctum.py", "--project-root", str(root), "--format", "json"])
    assert mod.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "dry-run"
    assert payload["changes"] == []
