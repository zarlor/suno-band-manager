#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for _sanctum_seed.py — the shared seeding logic.

This is the single source of the creed-sharding + access-boundaries seeding that
BOTH init-sanctum.py and migrate-sidecar-to-v2.py depend on, so it is tested
directly here.
"""

import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

spec = spec_from_file_location("_sanctum_seed", SCRIPTS_DIR / "_sanctum_seed.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

ASSETS = SKILL_DIR / "assets"
REFERENCES = SKILL_DIR / "references"


def test_shard_routing_covers_three_shards_plus_incident_log():
    creed_text = (REFERENCES / "creed.md").read_text(encoding="utf-8")
    shards = mod.shard_creed(creed_text)
    # Every routed shard + the incident log.
    assert "creed-disciplines.md" in shards
    assert "creed-workshop-capture.md" in shards
    assert "creed-package-assembly.md" in shards
    assert "creed-incident-log.md" in shards
    for name, text in shards.items():
        assert text.strip(), f"empty shard: {name}"


def test_shard_creed_lifts_package_assembly_rule():
    creed_text = (REFERENCES / "creed.md").read_text(encoding="utf-8")
    shards = mod.shard_creed(creed_text)
    assert "Package Assembly Rule" in shards["creed-package-assembly.md"]


def test_render_access_boundaries_substitutes_project_root():
    body = mod.render_access_boundaries(ASSETS, {"project_root": "/tmp/proj", "project-root": "/tmp/proj"})
    assert body is not None
    assert "Access Boundaries for Mac" in body
    assert "{project_root}" not in body
    assert "{project-root}" not in body
    assert "/tmp/proj" in body


def test_render_access_boundaries_missing_template_returns_none(tmp_path):
    assert mod.render_access_boundaries(tmp_path, {"project_root": "x"}) is None


def test_write_access_boundaries_writes_file(tmp_path):
    name = mod.write_access_boundaries(tmp_path, ASSETS, {"project_root": str(tmp_path)})
    assert name == "access-boundaries.md"
    written = (tmp_path / "access-boundaries.md").read_text(encoding="utf-8")
    assert "Deny Zones" in written


def test_write_creed_shards_writes_all(tmp_path):
    written = mod.write_creed_shards(tmp_path, REFERENCES)
    assert "creed-disciplines.md" in written
    assert "creed-package-assembly.md" in written
    assert "creed-incident-log.md" in written
    for name in written:
        assert (tmp_path / name).read_text(encoding="utf-8").strip()


def test_write_creed_shards_missing_creed_returns_empty(tmp_path):
    assert mod.write_creed_shards(tmp_path, tmp_path) == []


def test_cli_seeds_into_out_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv",
        ["_sanctum_seed.py", "--out", str(tmp_path), "--skill-path", str(SKILL_DIR), "--format", "json"],
    )
    rc = mod.main()
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "seeded"
    assert "memory/disciplines/package-assembly.md" in out["written"]
    assert (tmp_path / "memory" / "disciplines" / "package-assembly.md").exists()
    assert not (tmp_path / "access-boundaries.md").exists()


def test_render_access_boundaries_substitutes_hyphenated_root():
    body = mod.render_access_boundaries(ASSETS, {"project-root": "/tmp/proj"})
    assert "{project-root}" not in body
    assert "/tmp/proj/_bmad/memory/suno-agent-band-manager/" in body
    # {skill-root} stays a runtime placeholder (the bundle carve-out).
    assert "{skill-root}/" in body


def test_render_dominion_demotes_sections_for_the_creed():
    body = mod.render_dominion(ASSETS, {"project-root": "/tmp/proj"})
    for sub in ("### Read Access", "### Write Access", "### The Write Rule", "### Deny Zones"):
        assert sub in body
    assert "\n## " not in "\n" + body
    assert "Access Boundaries for Mac" not in body


def test_discipline_files_one_per_discipline_with_incidents():
    files = mod.discipline_files((REFERENCES / "creed.md").read_text(encoding="utf-8"))
    names = {k.split("/", 2)[2] for k in files if k.startswith("memory/disciplines/")}
    assert {"package-assembly.md", "workshop-capture.md", "research-discipline.md",
            "thematic-discipline.md", "milestone-auto-save.md"} <= names
    assert any(k.startswith("memory/incidents/") for k in files)
    assert mod.discipline_file("Thematic Discipline — Read the Songbook") == "thematic-discipline.md"


def test_shard_creed_warns_on_unrouted_heading():
    creed = (
        "## Mission\nm\n\n## Principles\np\n\n"
        "## Research Discipline\nr\n\n## Brand New Discipline\nn\n"
    )
    with pytest.warns(UserWarning, match="Brand New Discipline"):
        mod.shard_creed(creed)
    assert mod.unrouted_headings(creed) == ["Brand New Discipline"]


def test_shipped_creed_has_no_unrouted_headings():
    creed_text = (REFERENCES / "creed.md").read_text(encoding="utf-8")
    assert mod.unrouted_headings(creed_text) == []


def test_cli_writes_only_missing_without_force(tmp_path, monkeypatch, capsys):
    disciplines = tmp_path / "memory" / "disciplines"
    disciplines.mkdir(parents=True)
    (disciplines / "research-discipline.md").write_text("owner learnings\n")
    monkeypatch.setattr(
        sys, "argv",
        ["_sanctum_seed.py", "--out", str(tmp_path), "--skill-path", str(SKILL_DIR), "--format", "json"],
    )
    assert mod.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert "memory/disciplines/research-discipline.md" in out["skipped_existing"]
    assert "memory/disciplines/package-assembly.md" in out["written"]
    assert (disciplines / "research-discipline.md").read_text() == "owner learnings\n"


def test_cli_force_overwrites(tmp_path, monkeypatch, capsys):
    disciplines = tmp_path / "memory" / "disciplines"
    disciplines.mkdir(parents=True)
    (disciplines / "research-discipline.md").write_text("owner learnings\n")
    monkeypatch.setattr(
        sys, "argv",
        ["_sanctum_seed.py", "--out", str(tmp_path), "--skill-path", str(SKILL_DIR), "--force", "--format", "json"],
    )
    assert mod.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert "memory/disciplines/research-discipline.md" in out["written"]
    assert (disciplines / "research-discipline.md").read_text() != "owner learnings\n"


# --- classification -------------------------------------------------------


def test_classify_absent_v7_v2_v1_damaged(tmp_path):
    sanctum = tmp_path / "s"
    assert mod.classify_sanctum(sanctum)["sidecar_format"] == "absent"
    sanctum.mkdir()
    assert mod.classify_sanctum(sanctum)["sidecar_format"] == "absent"  # empty dir
    (sanctum / "index.md").write_text("v1")
    (sanctum / "access-boundaries.md").write_text("v1 stores carried this")
    assert mod.classify_sanctum(sanctum)["sidecar_format"] == "v1"
    for name in mod.V2_SPINE:
        (sanctum / name).write_text(name)
    state = mod.classify_sanctum(sanctum)
    assert state["sidecar_format"] == "v2" and state["needs_migration"]
    (sanctum / "BOND.md").unlink()
    assert mod.classify_sanctum(sanctum)["sidecar_format"] == "damaged"

    v7 = tmp_path / "v7"
    v7.mkdir()
    for name in mod.IDENTITY_FILES:
        (v7 / name).write_text(name)
    assert mod.classify_sanctum(v7) == {"sidecar_format": "v7", "needs_migration": False, "missing_spine": []}
    (v7 / "BOND.md").unlink()
    state = mod.classify_sanctum(v7)
    assert state["sidecar_format"] == "damaged" and state["missing_spine"] == ["BOND.md"]


def test_locate_prefers_v7_and_falls_back_to_a_legacy_store(tmp_path):
    sanctum, state = mod.locate_sanctum(tmp_path)
    assert state["sidecar_format"] == "absent" and sanctum == mod.sanctum_dir(tmp_path)
    legacy = mod.legacy_sanctum_dir(tmp_path)
    legacy.mkdir(parents=True)
    for name in mod.V2_SPINE:
        (legacy / name).write_text(name)
    sanctum, state = mod.locate_sanctum(tmp_path)
    assert sanctum == legacy and state["sidecar_format"] == "v2"
    v7 = mod.sanctum_dir(tmp_path)
    v7.mkdir(parents=True)
    for name in mod.IDENTITY_FILES:
        (v7 / name).write_text(name)
    sanctum, state = mod.locate_sanctum(tmp_path)
    assert sanctum == v7 and state["sidecar_format"] == "v7"


def test_memory_map_counts_dates_tending_and_raw(tmp_path):
    (tmp_path / "memory" / "sessions").mkdir(parents=True)
    (tmp_path / "memory" / "work").mkdir()
    (tmp_path / "memory" / "work" / "current.md").write_text("x")
    (tmp_path / "memory" / "sessions" / "2026-10-01-a.md").write_text("x")
    (tmp_path / "memory" / "sessions" / "2026-10-09-b.md").write_text("x")
    (tmp_path / "memory" / ".tended").write_text("2026-10-05\n")
    (tmp_path / "raw").mkdir()
    (tmp_path / "raw" / "2026-10-02-notes.md").write_text("---\nstatus: raw\n---\nbody")
    (tmp_path / "raw" / "2026-10-03-old.md").write_text("---\nstatus: distilled\n---\nbody")
    text = mod.memory_map(tmp_path)
    assert "memory/sessions/ (2 files)" in text and "memory/work/ (1 files)" in text
    assert "Tended: 2026-10-05; session notes since: 1" in text
    assert "raw/2026-10-02-notes.md" in text and "2026-10-03-old.md" not in text.split("Undistilled")[1]
    assert mod.memory_map(tmp_path / "nothing") .startswith("(empty")


# --- config -----------------------------------------------------------------


def test_resolve_config_from_toml_layers_and_bond(tmp_path):
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "config.toml").write_text('[core]\noutput_folder = "{project-root}/out"\n[modules.suno]\nsuno_tier = "pro"\n')
    (bmad / "custom").mkdir()
    (bmad / "custom" / "config.user.toml").write_text('[modules.suno]\nsuno_tier = "free"\nsongbook_folder = "{project-root}/book"\n')
    (bmad / "config.yaml").write_text("user_name: Yaml\nsuno:\n  default_mode: jam\n")
    sanctum = mod.sanctum_dir(tmp_path)
    sanctum.mkdir(parents=True)
    (sanctum / "BOND.md").write_text("# Bond\n\n- **Name:** Robin\n- **Language:** French\n")
    cfg = mod.resolve_config(tmp_path)
    assert cfg["values"]["user_name"] == "Robin"
    assert cfg["values"]["communication_language"] == "French"
    assert cfg["values"]["document_output_language"] == "French"
    assert cfg["values"]["output_folder"] == "{project-root}/out"
    assert cfg["values"]["suno_tier"] == "free"
    assert cfg["values"]["default_mode"] == "demo"  # legacy YAML is not read
    assert cfg["values"]["songbook_folder"] == "book"
    assert cfg["warnings"] == []


def test_owner_from_lone_voice_file_before_bond(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "voice-context-mary-jane.md").write_text("# voice\n")
    cfg = mod.resolve_config(tmp_path)
    assert cfg["values"]["user_name"] == "Mary Jane"
    assert mod.normalize_username(cfg["values"]["user_name"]) == "mary-jane"
    (docs / "voice-context-other.md").write_text("# voice\n")
    assert mod.resolve_config(tmp_path)["values"]["user_name"] is None


def test_template_token_in_bond_is_not_a_name(tmp_path):
    sanctum = mod.sanctum_dir(tmp_path)
    sanctum.mkdir(parents=True)
    (sanctum / "BOND.md").write_text("- **Name:** {user_name}\n")
    cfg = mod.resolve_config(tmp_path)
    assert cfg["values"]["user_name"] is None
    assert any("user_name" in w for w in cfg["warnings"])


# --- roster -----------------------------------------------------------------


def test_capabilities_roster_from_menu_csv():
    csv_path = mod.find_menu_csv(SKILL_DIR)
    assert csv_path is not None
    rows = mod.menu_rows(csv_path, [mod.MODULE_CODE])
    text = mod.generate_capabilities_md(rows)
    assert "| [CS] | Create Song |" in text
    assert "`references/create-song.md`" in text
    assert "[FL]" not in text.split("## Learned")[0].split("Typing FL")[0]
    assert "## Learned" in text
    assert "references/capability-authoring.md" in text
