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
        [
            "_sanctum_seed.py",
            "--out", str(tmp_path),
            "--skill-path", str(SKILL_DIR),
            "--project-root", str(tmp_path),
            "--format", "json",
        ],
    )
    rc = mod.main()
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "seeded"
    assert "access-boundaries.md" in out["written"]
    assert "creed-package-assembly.md" in out["written"]
    assert (tmp_path / "access-boundaries.md").exists()


def test_render_access_boundaries_substitutes_hyphenated_root():
    body = mod.render_access_boundaries(ASSETS, {"project-root": "/tmp/proj"})
    assert "{project-root}" not in body
    assert "/tmp/proj/_bmad/_memory/band-manager-sidecar/" in body
    # {skill-root} stays a runtime placeholder (the bundle carve-out).
    assert "{skill-root}/" in body


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
    (tmp_path / "creed-disciplines.md").write_text("owner learnings\n")
    (tmp_path / "access-boundaries.md").write_text("owner boundaries\n")
    monkeypatch.setattr(
        sys, "argv",
        ["_sanctum_seed.py", "--out", str(tmp_path), "--skill-path", str(SKILL_DIR), "--format", "json"],
    )
    assert mod.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert "creed-disciplines.md" in out["skipped_existing"]
    assert "access-boundaries.md" in out["skipped_existing"]
    assert "creed-package-assembly.md" in out["written"]
    assert (tmp_path / "creed-disciplines.md").read_text() == "owner learnings\n"
    assert (tmp_path / "access-boundaries.md").read_text() == "owner boundaries\n"


def test_cli_force_overwrites(tmp_path, monkeypatch, capsys):
    (tmp_path / "creed-disciplines.md").write_text("owner learnings\n")
    monkeypatch.setattr(
        sys, "argv",
        ["_sanctum_seed.py", "--out", str(tmp_path), "--skill-path", str(SKILL_DIR), "--force", "--format", "json"],
    )
    assert mod.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert "creed-disciplines.md" in out["written"]
    assert (tmp_path / "creed-disciplines.md").read_text() != "owner learnings\n"


# --- classification -------------------------------------------------------


def test_classify_absent_v1_v2_damaged(tmp_path):
    sanctum = tmp_path / "s"
    assert mod.classify_sanctum(sanctum)["sidecar_format"] == "absent"
    sanctum.mkdir()
    assert mod.classify_sanctum(sanctum)["sidecar_format"] == "damaged"
    (sanctum / "index.md").write_text("v1")
    (sanctum / "access-boundaries.md").write_text("v1 stores carried this")
    assert mod.classify_sanctum(sanctum)["sidecar_format"] == "v1"
    for name in mod.SANCTUM_LOAD_ORDER:
        (sanctum / name).write_text(name)
    state = mod.classify_sanctum(sanctum)
    assert state["sidecar_format"] == "v2" and state["missing_spine"] == []
    (sanctum / "BOND.md").unlink()
    state = mod.classify_sanctum(sanctum)
    assert state["sidecar_format"] == "damaged" and state["missing_spine"] == ["BOND.md"]


# --- config -----------------------------------------------------------------


def test_resolve_config_from_toml_layers(tmp_path):
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "config.toml").write_text('[core]\ndocument_output_language = "German"\n')
    (bmad / "config.user.toml").write_text('[core]\nuser_name = "Robin"\ncommunication_language = "French"\n')
    (bmad / "config.yaml").write_text("suno:\n  suno_tier: free\n")
    cfg = mod.resolve_config(tmp_path)
    assert cfg["values"]["user_name"] == "Robin"
    assert cfg["values"]["communication_language"] == "French"
    assert cfg["values"]["document_output_language"] == "German"
    assert cfg["values"]["suno_tier"] == "free"
    assert cfg["values"]["songbook_folder"] == "{project-root}/docs/songbook"
    assert cfg["warnings"] == []


def test_parse_simple_yaml_nested_section(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text(
        "user_name: Lee\nsuno:\n  description: one\n    two: not a key\n  suno_tier: 'pro'\nother: x\n"
    )
    data = mod.parse_simple_yaml(path)
    assert data["user_name"] == "Lee"
    assert data["suno"] == {"description": "one", "suno_tier": "pro"}
    assert data["other"] == "x"


# --- roster -----------------------------------------------------------------


def test_capabilities_roster_from_module_csv():
    csv_path = mod.find_module_csv(SKILL_DIR.parent.parent.parent, SKILL_DIR)
    assert csv_path is not None
    rows = mod.menu_rows(csv_path, [mod.MODULE_CODE])
    text = mod.generate_capabilities_md(rows)
    assert "| [CS] | Create Song |" in text
    assert "`references/create-song.md`" in text
    assert "[FL]" not in text.split("## Learned")[0].split("Typing FL")[0]
    assert "## Learned" in text
    assert "references/capability-authoring.md" in text
