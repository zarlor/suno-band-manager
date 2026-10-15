#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for _sanctum_seed.py — the shared seeding logic.

This is the single source of the creed-sharding + access-boundaries seeding that
BOTH init-sanctum.py and migrate-sidecar-to-v2.py depend on, so it is tested
directly here.
"""

import json
import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_resolver import install_resolver  # noqa: E402
from helpers import TempDirMixin  # noqa: E402

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

spec = spec_from_file_location("_sanctum_seed", SCRIPTS_DIR / "_sanctum_seed.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

ASSETS = SKILL_DIR / "assets"
REFERENCES = SKILL_DIR / "references"


class TestSanctumSeed(TempDirMixin, unittest.TestCase):
    def test_shard_routing_covers_three_shards_plus_incident_log(self):
        creed_text = (REFERENCES / "creed.md").read_text(encoding="utf-8")
        shards = mod.shard_creed(creed_text)
        # Every routed shard + the incident log.
        assert "creed-disciplines.md" in shards
        assert "creed-workshop-capture.md" in shards
        assert "creed-package-assembly.md" in shards
        assert "creed-incident-log.md" in shards
        for name, text in shards.items():
            assert text.strip(), f"empty shard: {name}"

    def test_shard_creed_lifts_package_assembly_rule(self):
        creed_text = (REFERENCES / "creed.md").read_text(encoding="utf-8")
        shards = mod.shard_creed(creed_text)
        assert "Package Assembly Rule" in shards["creed-package-assembly.md"]

    def test_render_access_boundaries_substitutes_project_root(self):
        body = mod.render_access_boundaries(ASSETS, {"project_root": "/tmp/proj", "project-root": "/tmp/proj"})
        assert body is not None
        assert "Access Boundaries for Mac" in body
        assert "{project_root}" not in body
        assert "{project-root}" not in body
        assert "/tmp/proj" in body

    def test_render_access_boundaries_missing_template_returns_none(self):
        assert mod.render_access_boundaries(self.tmp_path, {"project_root": "x"}) is None

    def test_write_access_boundaries_writes_file(self):
        name = mod.write_access_boundaries(self.tmp_path, ASSETS, {"project_root": str(self.tmp_path)})
        assert name == "access-boundaries.md"
        written = (self.tmp_path / "access-boundaries.md").read_text(encoding="utf-8")
        assert "Deny Zones" in written

    def test_write_creed_shards_writes_all(self):
        written = mod.write_creed_shards(self.tmp_path, REFERENCES)
        assert "creed-disciplines.md" in written
        assert "creed-package-assembly.md" in written
        assert "creed-incident-log.md" in written
        for name in written:
            assert (self.tmp_path / name).read_text(encoding="utf-8").strip()

    def test_write_creed_shards_missing_creed_returns_empty(self):
        assert mod.write_creed_shards(self.tmp_path, self.tmp_path) == []

    def test_cli_seeds_into_out_dir(self):
        with patch.object(
            sys, "argv",
            ["_sanctum_seed.py", "--out", str(self.tmp_path), "--skill-path", str(SKILL_DIR), "--format", "json"],
        ), self.capsys():
            rc = mod.main()
        assert rc == 0
        out = json.loads(self.capsys.readouterr().out)
        assert out["status"] == "seeded"
        assert "memory/disciplines/package-assembly.md" in out["written"]
        assert (self.tmp_path / "memory" / "disciplines" / "package-assembly.md").exists()
        assert not (self.tmp_path / "access-boundaries.md").exists()

    def test_render_access_boundaries_substitutes_hyphenated_root(self):
        body = mod.render_access_boundaries(ASSETS, {"project-root": "/tmp/proj"})
        assert "{project-root}" not in body
        assert "/tmp/proj/_bmad/memory/suno-agent-band-manager/" in body
        # {skill-root} stays a runtime placeholder (the bundle carve-out).
        assert "{skill-root}/" in body

    def test_render_dominion_demotes_sections_for_the_creed(self):
        body = mod.render_dominion(ASSETS, {"project-root": "/tmp/proj"})
        for sub in ("### Read Access", "### Write Access", "### The Write Rule", "### Deny Zones"):
            assert sub in body
        assert "\n## " not in "\n" + body
        assert "Access Boundaries for Mac" not in body

    def test_discipline_files_one_per_discipline_with_incidents(self):
        files = mod.discipline_files((REFERENCES / "creed.md").read_text(encoding="utf-8"))
        names = {k.split("/", 2)[2] for k in files if k.startswith("memory/disciplines/")}
        assert {"package-assembly.md", "workshop-capture.md", "research-discipline.md",
                "thematic-discipline.md", "milestone-auto-save.md"} <= names
        assert any(k.startswith("memory/incidents/") for k in files)
        assert mod.discipline_file("Thematic Discipline — Read the Songbook") == "thematic-discipline.md"

    def test_discipline_files_split_rule_from_story(self):
        files = mod.discipline_files((REFERENCES / "creed.md").read_text(encoding="utf-8"))
        incidents = {k.split("/", 2)[2] for k in files if k.startswith("memory/incidents/")}
        assert {"workshop-capture.md", "catalog-verification-discipline.md", "thematic-discipline.md",
                "document-state-marker-discipline.md", "hedge-preservation-discipline.md"} <= incidents
        for name in incidents:
            rule = files[f"memory/disciplines/{name}"]
            story = files[f"memory/incidents/{name}"]
            assert "### Why — the incident" not in rule and "### Why — the incident" not in story
            assert rule.rstrip().endswith(f"`memory/incidents/{name}` (read it only when auditing or questioning the rule)._")
            assert story.startswith("# ") and "— the incident" in story.splitlines()[0]
        workshop = files["memory/disciplines/workshop-capture.md"]
        assert "Append the text verbatim" in workshop and "fourth-instance" not in workshop
        assert "fourth-instance" in files["memory/incidents/workshop-capture.md"]
        # A discipline with no story gets no incident file and no pointer.
        assert "memory/incidents/research-discipline.md" not in files
        assert "memory/incidents/" not in files["memory/disciplines/research-discipline.md"]

    def test_split_rule_and_story_without_marker_keeps_everything_as_rule(self):
        assert mod.split_rule_and_story("rule\n\n### Steps\n1. x") == ("rule\n\n### Steps\n1. x", "")
        assert mod.split_rule_and_story("rule\n\n### Why — the incident\n\nstory") == ("rule", "story")

    def test_shard_creed_warns_on_unrouted_heading(self):
        creed = (
            "## Mission\nm\n\n## Principles\np\n\n"
            "## Research Discipline\nr\n\n## Brand New Discipline\nn\n"
        )
        with self.assertWarnsRegex(UserWarning, "Brand New Discipline"):
            mod.shard_creed(creed)
        assert mod.unrouted_headings(creed) == ["Brand New Discipline"]

    def test_shipped_creed_has_no_unrouted_headings(self):
        creed_text = (REFERENCES / "creed.md").read_text(encoding="utf-8")
        assert mod.unrouted_headings(creed_text) == []

    def test_cli_writes_only_missing_without_force(self):
        disciplines = self.tmp_path / "memory" / "disciplines"
        disciplines.mkdir(parents=True)
        (disciplines / "research-discipline.md").write_text("owner learnings\n")
        with patch.object(
            sys, "argv",
            ["_sanctum_seed.py", "--out", str(self.tmp_path), "--skill-path", str(SKILL_DIR), "--format", "json"],
        ), self.capsys():
            assert mod.main() == 0
        out = json.loads(self.capsys.readouterr().out)
        assert "memory/disciplines/research-discipline.md" in out["skipped_existing"]
        assert "memory/disciplines/package-assembly.md" in out["written"]
        assert (disciplines / "research-discipline.md").read_text() == "owner learnings\n"

    def test_cli_force_overwrites(self):
        disciplines = self.tmp_path / "memory" / "disciplines"
        disciplines.mkdir(parents=True)
        (disciplines / "research-discipline.md").write_text("owner learnings\n")
        with patch.object(
            sys, "argv",
            ["_sanctum_seed.py", "--out", str(self.tmp_path), "--skill-path", str(SKILL_DIR), "--force", "--format", "json"],
        ), self.capsys():
            assert mod.main() == 0
        out = json.loads(self.capsys.readouterr().out)
        assert "memory/disciplines/research-discipline.md" in out["written"]
        assert (disciplines / "research-discipline.md").read_text() != "owner learnings\n"

    # --- classification -------------------------------------------------------

    def test_classify_absent_v7_v2_v1_damaged(self):
        sanctum = self.tmp_path / "s"
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

        v7 = self.tmp_path / "v7"
        v7.mkdir()
        for name in mod.IDENTITY_FILES:
            (v7 / name).write_text(name)
        assert mod.classify_sanctum(v7) == {"sidecar_format": "v7", "needs_migration": False, "missing_spine": []}
        (v7 / "BOND.md").unlink()
        state = mod.classify_sanctum(v7)
        assert state["sidecar_format"] == "damaged" and state["missing_spine"] == ["BOND.md"]

    def test_locate_prefers_v7_and_falls_back_to_a_legacy_store(self):
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        assert state["sidecar_format"] == "absent" and sanctum == mod.sanctum_dir(self.tmp_path)
        legacy = mod.legacy_sanctum_dir(self.tmp_path)
        legacy.mkdir(parents=True)
        for name in mod.V2_SPINE:
            (legacy / name).write_text(name)
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        assert sanctum == legacy and state["sidecar_format"] == "v2"
        v7 = mod.sanctum_dir(self.tmp_path)
        v7.mkdir(parents=True)
        for name in mod.IDENTITY_FILES:
            (v7 / name).write_text(name)
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        assert sanctum == v7 and state["sidecar_format"] == "v7"

    def test_memory_map_counts_dates_tending_and_raw(self):
        (self.tmp_path / "memory" / "sessions").mkdir(parents=True)
        (self.tmp_path / "memory" / "work").mkdir()
        (self.tmp_path / "memory" / "work" / "current.md").write_text("x")
        (self.tmp_path / "memory" / "sessions" / "2026-10-01-a.md").write_text("x")
        (self.tmp_path / "memory" / "sessions" / "2026-10-09-b.md").write_text("x")
        (self.tmp_path / "memory" / ".tended").write_text("2026-10-05\n")
        (self.tmp_path / "raw").mkdir()
        (self.tmp_path / "raw" / "2026-10-02-notes.md").write_text("---\nstatus: raw\n---\nbody")
        (self.tmp_path / "raw" / "2026-10-03-old.md").write_text("---\nstatus: distilled\n---\nbody")
        text = mod.memory_map(self.tmp_path)
        assert "memory/sessions/ (2 files)" in text and "memory/work/ (1 files)" in text
        assert "Tended: 2026-10-05; session notes since: 1" in text
        assert "raw/2026-10-02-notes.md" in text and "2026-10-03-old.md" not in text.split("Undistilled")[1]
        assert mod.memory_map(self.tmp_path / "nothing") .startswith("(empty")

    # --- config -------------------------------------------------------------

    def test_resolve_config_from_toml_layers_and_bond(self):
        bmad = self.tmp_path / "_bmad"
        bmad.mkdir()
        (bmad / "config.toml").write_text('[core]\noutput_folder = "{project-root}/out"\n[modules.suno]\nsuno_tier = "pro"\n')
        (bmad / "custom").mkdir()
        (bmad / "custom" / "config.user.toml").write_text('[modules.suno]\nsuno_tier = "free"\nsongbook_folder = "{project-root}/book"\n')
        (bmad / "config.yaml").write_text("user_name: Yaml\nsuno:\n  default_mode: jam\n")
        install_resolver(self.tmp_path)
        sanctum = mod.sanctum_dir(self.tmp_path)
        sanctum.mkdir(parents=True)
        (sanctum / "BOND.md").write_text("# Bond\n\n- **Name:** Robin\n- **Language:** French\n")
        cfg = mod.resolve_config(self.tmp_path)
        assert cfg["values"]["user_name"] == "Robin"
        assert cfg["values"]["communication_language"] == "French"
        assert cfg["values"]["document_output_language"] == "French"
        assert cfg["values"]["output_folder"] == "{project-root}/out"
        assert cfg["values"]["suno_tier"] == "free"
        assert cfg["values"]["default_mode"] == "demo"  # legacy YAML is not read
        assert cfg["values"]["songbook_folder"] == "{project-root}/book"
        assert cfg["warnings"] == []

    def test_owner_from_lone_voice_file_before_bond(self):
        docs = self.tmp_path / "docs"
        docs.mkdir()
        (docs / "voice-context-mary-jane.md").write_text("# voice\n")
        cfg = mod.resolve_config(self.tmp_path)
        assert cfg["values"]["user_name"] == "Mary Jane"
        assert mod.normalize_username(cfg["values"]["user_name"]) == "mary-jane"
        (docs / "voice-context-other.md").write_text("# voice\n")
        assert mod.resolve_config(self.tmp_path)["values"]["user_name"] is None

    def test_broken_config_is_reported_not_called_unset(self):
        (self.tmp_path / "_bmad").mkdir()
        (self.tmp_path / "_bmad" / "config.toml").write_text("[modules.suno\nbad")
        install_resolver(self.tmp_path)
        cfg = mod.resolve_config(self.tmp_path)
        assert any("broken" in w for w in cfg["warnings"])
        assert not any("bmad setup suno` asks" in w for w in cfg["warnings"])
        assert cfg["values"]["songbook_folder"] == "{project-root}/docs/songbook"

    def test_not_yet_known_marker_is_not_a_name(self):
        sanctum = mod.sanctum_dir(self.tmp_path)
        sanctum.mkdir(parents=True)
        (sanctum / "BOND.md").write_text("- **Name:** _(not yet known)_\n")
        assert mod.resolve_config(self.tmp_path)["values"]["user_name"] is None

    def test_template_token_in_bond_is_not_a_name(self):
        sanctum = mod.sanctum_dir(self.tmp_path)
        sanctum.mkdir(parents=True)
        (sanctum / "BOND.md").write_text("- **Name:** {user_name}\n")
        cfg = mod.resolve_config(self.tmp_path)
        assert cfg["values"]["user_name"] is None
        assert any("user_name" in w for w in cfg["warnings"])

    # --- roster -------------------------------------------------------------

    def test_menu_rows_route_and_fold_feedback_loop(self):
        csv_path = mod.find_menu_csv(SKILL_DIR)
        assert csv_path is not None
        rows = mod.menu_rows(csv_path)
        codes = [r["code"] for r in rows]
        assert codes[0] == "CS" and "FL" not in codes and "AA" in codes
        assert set(rows[0]) == {"code", "name", "description", "skill", "action"}
        assert mod.route_for(rows[0]) == {"name": "create-song", "type": "prompt", "target": "references/create-song.md"}
        mb = next(r for r in rows if r["code"] == "MB")
        assert mod.route_for(mb) == {"name": "manage-profiles", "type": "skill", "target": "suno-band-profile-manager"}

    def test_capabilities_md_points_to_the_menu_and_keeps_learned(self):
        rows = mod.menu_rows(mod.find_menu_csv(SKILL_DIR))
        text = mod.generate_capabilities_md(rows)
        builtin = text.split("## Learned")[0]
        assert "The menu the wake prints" in builtin and "Create Song" not in builtin
        assert "## Learned" in text
        assert "references/capability-authoring.md" in text
        assert "assets/menu.csv was not found" in mod.generate_capabilities_md([])


if __name__ == "__main__":
    unittest.main()
