#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for _sanctum_seed.py — the shared seeding logic.

This is the single source of the creed-sharding, Dominion rendering, sanctum
classification, config and roster logic that the waking, birth, migration and
upgrade scripts depend on, so it is tested directly here. The inputs are
synthetic (helpers.make_skill and inline text); one smoke test runs the
slicing on the shipped creed and checks shape only.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_resolver import install_resolver  # noqa: E402
from helpers import SKILL_CREED, TempDirMixin, creed_source, load_script, make_skill  # noqa: E402

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

mod = load_script("_sanctum_seed", "_sanctum_seed.py")

VARS = {"project_root": "/tmp/proj", "project-root": "/tmp/proj"}


class TestSanctumSeed(TempDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.skill = make_skill(self.tmp_path)
        self.assets = self.skill / "assets"
        self.out = self.tmp_path / "out"
        self.out.mkdir()

    def run_cli(self, *argv):
        with patch.object(sys, "argv", ["_sanctum_seed.py", *argv]), self.capsys():
            code = mod.main()
        return code, self.capsys.readouterr()

    # --- the creed source ---------------------------------------------------

    def test_creed_source_is_defined_once_and_followed(self):
        """Every seeding entry point reads the creed at CREED_SOURCE_REL under the skill."""
        self.assertEqual(mod.creed_source(self.skill), self.skill.joinpath(*mod.CREED_SOURCE_REL))
        self.assertEqual(mod.CREED_SOURCE_LABEL, "/".join(mod.CREED_SOURCE_REL))
        moved = self.tmp_path / "moved-skill"
        with patch.object(mod, "CREED_SOURCE_REL", ("assets", "creed-source.md")):
            target = mod.creed_source(moved)
            self.assertEqual(target, moved / "assets" / "creed-source.md")
            target.parent.mkdir(parents=True)
            target.write_text(SKILL_CREED, encoding="utf-8")
            written = mod.write_disciplines(self.out, moved)
        self.assertIn("memory/disciplines/research-discipline.md", written)

    # --- v2 shards ----------------------------------------------------------

    def test_shard_creed_routes_sections_and_gathers_incidents(self):
        shards = mod.shard_creed(SKILL_CREED)
        self.assertEqual(sorted(shards), ["creed-disciplines.md", "creed-incident-log.md",
                                          "creed-package-assembly.md", "creed-workshop-capture.md"])
        self.assertIn("## Research Discipline", shards["creed-disciplines.md"])
        self.assertIn("## Thematic Discipline", shards["creed-disciplines.md"])
        self.assertNotIn("## Workshop Capture Discipline", shards["creed-disciplines.md"])
        self.assertIn("Invoke the builder and the transformer.", shards["creed-package-assembly.md"])
        # Mission and Principles belong to the core, not to a shard.
        self.assertFalse(any("The species mission." in text for text in shards.values()))
        log = shards["creed-incident-log.md"]
        self.assertIn("A swing was lost before it was written down.", log)
        self.assertNotIn("## Research Discipline", log)  # no story, so not in the log

    def test_shard_creed_without_stories_writes_a_placeholder_log(self):
        shards = mod.shard_creed("## Research Discipline\n\nLook it up.\n")
        self.assertIn("_No verbose incident narratives extracted._", shards["creed-incident-log.md"])

    def test_write_creed_shards_writes_all_and_respects_only_missing(self):
        written = mod.write_creed_shards(self.out, self.skill)
        self.assertEqual(sorted(written), sorted(mod.shard_creed(SKILL_CREED)))
        for name in written:
            self.assertTrue((self.out / name).read_text(encoding="utf-8").strip())
        (self.out / "creed-disciplines.md").write_text("grown\n", encoding="utf-8")
        (self.out / "creed-workshop-capture.md").unlink()
        self.assertEqual(mod.write_creed_shards(self.out, self.skill, only_missing=True), ["creed-workshop-capture.md"])
        self.assertEqual((self.out / "creed-disciplines.md").read_text(encoding="utf-8"), "grown\n")

    def test_write_creed_shards_missing_creed_returns_empty(self):
        self.assertEqual(mod.write_creed_shards(self.out, self.tmp_path / "no-skill"), [])
        self.assertEqual(mod.write_disciplines(self.out, self.tmp_path / "no-skill"), [])

    # --- access boundaries and the Dominion ---------------------------------

    def test_render_access_boundaries_substitutes_both_root_tokens(self):
        body = mod.render_access_boundaries(self.assets, VARS)
        self.assertNotIn("{project_root}", body)
        self.assertNotIn("{project-root}", body)
        self.assertIn("`/tmp/proj/_bmad/memory/suno-agent-band-manager/` — own memory", body)
        # {skill-root} stays a runtime placeholder (the bundle carve-out).
        self.assertIn("{skill-root}/", body)

    def test_render_access_boundaries_missing_template_returns_none(self):
        self.assertIsNone(mod.render_access_boundaries(self.out, {"project_root": "x"}))
        self.assertIsNone(mod.write_access_boundaries(self.out, self.out, {"project_root": "x"}))
        self.assertFalse((self.out / "access-boundaries.md").exists())

    def test_write_access_boundaries_writes_the_rendered_body(self):
        name = mod.write_access_boundaries(self.out, self.assets, VARS)
        self.assertEqual(name, "access-boundaries.md")
        self.assertEqual((self.out / "access-boundaries.md").read_text(encoding="utf-8"),
                         mod.render_access_boundaries(self.assets, VARS))

    def test_dominion_names_the_configured_songbook_and_profile_folders(self):
        """The module's folder answers are rendered into the Dominion, so a songbook the owner
        moved is inside the write list instead of under 'Anything not listed above'."""
        root = self.tmp_path / "proj"
        (root / "_bmad").mkdir(parents=True)
        (root / "_bmad" / "config.toml").write_text(
            '[modules.suno]\nsongbook_folder = "{project-root}/music/book"\n'
            f'band_profiles_folder = "{(self.tmp_path / "shared" / "bands").as_posix()}"\n', encoding="utf-8")
        install_resolver(root)
        variables = mod.template_variables(root)
        self.assertEqual(variables["songbook_folder"], "music/book")  # inside the project: relative
        self.assertEqual(variables["band_profiles_folder"], (self.tmp_path / "shared" / "bands").as_posix())
        # Playlist YAMLs sit beside the band-profiles folder, so their Dominion entry moves with it.
        self.assertEqual(variables["playlists_folder"], (self.tmp_path / "shared").as_posix())
        body = mod.render_dominion(self.assets, variables)
        self.assertIn("- `music/book/` — written by the song flows", body)
        self.assertIn(f"- `{(self.tmp_path / 'shared' / 'bands').as_posix()}/` — band profiles", body)
        self.assertNotIn("{songbook_folder}", body)
        self.assertNotIn("{band_profiles_folder}", body)

    def test_dominion_folders_default_to_the_docs_paths(self):
        """No answers (or no BMad at all): today's docs/ folders, written project-relative."""
        variables = mod.template_variables(self.tmp_path)
        self.assertEqual((variables["songbook_folder"], variables["band_profiles_folder"]),
                         ("docs/songbook", "docs/band-profiles"))
        self.assertEqual(variables["playlists_folder"], "docs")
        body = mod.render_dominion(self.assets, variables)
        self.assertIn("- `docs/songbook/` — the songbook", body)
        self.assertIn("- `docs/band-profiles/` — band profiles", body)

    def test_folder_entry_forms(self):
        root = self.tmp_path
        default = "{project-root}/docs/songbook"
        self.assertEqual(mod.folder_entry(None, default, root), "docs/songbook")
        self.assertEqual(mod.folder_entry("", default, root), "docs/songbook")
        self.assertEqual(mod.folder_entry("music/book/", default, root), "music/book")       # relative: from the root
        self.assertEqual(mod.folder_entry(str(root / "a" / ".." / "b"), default, root), "b")  # collapsed
        self.assertEqual(mod.folder_entry("{project_root}/x", default, root), "x")
        outside = (root.parent / "elsewhere").as_posix()
        self.assertEqual(mod.folder_entry(outside, default, root), outside)

    def test_render_dominion_demotes_sections_for_the_creed(self):
        body = mod.render_dominion(self.assets, VARS)
        for sub in ("### Read Access", "### Write Access", "### The Write Rule", "### Deny Zones", "### Notes"):
            self.assertIn(sub, body)
        self.assertNotIn("\n## ", "\n" + body)
        self.assertNotIn("# Synthetic Boundaries", body)  # the template's own title stays out
        self.assertIn("reinstall", mod.render_dominion(self.out, VARS))  # no template: says so

    # --- v7 disciplines and incidents ---------------------------------------

    def test_discipline_files_one_per_routed_section(self):
        files = mod.discipline_files(SKILL_CREED)
        self.assertEqual(sorted(files), [
            "memory/disciplines/package-assembly.md",
            "memory/disciplines/research-discipline.md",
            "memory/disciplines/thematic-discipline.md",
            "memory/disciplines/workshop-capture.md",
            "memory/incidents/thematic-discipline.md",
            "memory/incidents/workshop-capture.md",
        ])
        self.assertEqual(files["memory/disciplines/research-discipline.md"],
                         "# Research Discipline\n\nLook it up before you claim it.\n")
        self.assertEqual(mod.discipline_file("Thematic Discipline — Read the Songbook"), "thematic-discipline.md")
        self.assertEqual(mod.discipline_file("Package Assembly Rule — anything"), "package-assembly.md")

    def test_discipline_files_split_rule_from_story(self):
        files = mod.discipline_files(SKILL_CREED)
        rule = files["memory/disciplines/thematic-discipline.md"]
        story = files["memory/incidents/thematic-discipline.md"]
        self.assertNotIn("### Why — the incident", rule)
        self.assertNotIn("### Why — the incident", story)
        self.assertIn("### Steps\n\n1. Open the songbook.", rule)
        self.assertNotIn("Once, a theme was claimed unread.", rule)
        self.assertTrue(rule.rstrip().endswith(
            "`memory/incidents/thematic-discipline.md` (read it only when auditing or questioning the rule)._"))
        self.assertEqual(story, "# Thematic Discipline — Read the Songbook Before Making Thematic Claims — the incident"
                                "\n\nOnce, a theme was claimed unread.\n")
        # A discipline with no story gets no incident file and no pointer.
        self.assertNotIn("memory/incidents/", files["memory/disciplines/research-discipline.md"])

    def test_split_rule_and_story_without_marker_keeps_everything_as_rule(self):
        self.assertEqual(mod.split_rule_and_story("rule\n\n### Steps\n1. x"), ("rule\n\n### Steps\n1. x", ""))
        self.assertEqual(mod.split_rule_and_story("rule\n\n### Why — the incident\n\nstory"), ("rule", "story"))

    def test_unrouted_heading_warns_in_both_slicers(self):
        creed = (
            "## Mission\nm\n\n## Principles\np\n\n"
            "## Research Discipline\nr\n\n## Brand New Discipline\nn\n"
        )
        with self.assertWarnsRegex(UserWarning, "Brand New Discipline"):
            mod.shard_creed(creed)
        with self.assertWarnsRegex(UserWarning, "Brand New Discipline"):
            files = mod.discipline_files(creed)
        self.assertEqual(sorted(files), ["memory/disciplines/research-discipline.md"])
        self.assertEqual(mod.unrouted_headings(creed), ["Brand New Discipline"])
        self.assertEqual(mod.unrouted_headings(SKILL_CREED), [])
        # A section merged into another discipline is no longer a route of its own.
        self.assertEqual(mod.unrouted_headings("## Pre-Presentation Review\nr\n"), ["Pre-Presentation Review"])
        self.assertEqual(mod.unrouted_headings("## Package Assembly Rule\nr\n\n## Milestone Auto-Save\nm\n"), [])

    def test_shipped_creed_slices_into_discipline_files(self):
        """Smoke check on the shipped creed source: shape only."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            files = mod.discipline_files(mod.creed_source(SKILL_DIR).read_text(encoding="utf-8"))
        self.assertTrue(files)
        for rel, text in files.items():
            self.assertTrue(rel.startswith(("memory/disciplines/", "memory/incidents/")) and rel.endswith(".md"), rel)
            self.assertTrue(text.startswith("# ") and text.strip(), rel)

    # --- recovery CLI -------------------------------------------------------

    def test_cli_seeds_into_out_dir(self):
        code, captured = self.run_cli("--out", str(self.out), "--skill-path", str(self.skill), "--format", "json")
        self.assertEqual(code, 0)
        out = json.loads(captured.out)
        self.assertEqual(out["status"], "seeded")
        self.assertEqual(sorted(out["written"]), sorted(mod.discipline_files(SKILL_CREED)))
        self.assertEqual(out["skipped_existing"], [])
        for rel in out["written"]:
            self.assertTrue((self.out / rel).is_file(), rel)
        self.assertFalse((self.out / "access-boundaries.md").exists())

    def test_cli_writes_only_missing_without_force(self):
        disciplines = self.out / "memory" / "disciplines"
        disciplines.mkdir(parents=True)
        (disciplines / "research-discipline.md").write_text("owner learnings\n", encoding="utf-8")
        code, captured = self.run_cli("--out", str(self.out), "--skill-path", str(self.skill), "--format", "json")
        self.assertEqual(code, 0)
        out = json.loads(captured.out)
        self.assertIn("memory/disciplines/research-discipline.md", out["skipped_existing"])
        self.assertIn("memory/disciplines/package-assembly.md", out["written"])
        self.assertEqual((disciplines / "research-discipline.md").read_text(encoding="utf-8"), "owner learnings\n")

    def test_cli_force_overwrites(self):
        disciplines = self.out / "memory" / "disciplines"
        disciplines.mkdir(parents=True)
        (disciplines / "research-discipline.md").write_text("owner learnings\n", encoding="utf-8")
        code, captured = self.run_cli("--out", str(self.out), "--skill-path", str(self.skill), "--force",
                                      "--format", "json")
        self.assertEqual(code, 0)
        self.assertIn("memory/disciplines/research-discipline.md", json.loads(captured.out)["written"])
        self.assertEqual((disciplines / "research-discipline.md").read_text(encoding="utf-8"),
                         "# Research Discipline\n\nLook it up before you claim it.\n")

    def test_cli_without_a_creed_source_is_an_error_not_seeded(self):
        """No creed to slice: exit 2 with the path, never `status: seeded` with nothing written."""
        creed_source(self.skill).unlink()
        code, captured = self.run_cli("--out", str(self.out), "--skill-path", str(self.skill), "--format", "json")
        self.assertEqual(code, 2)
        self.assertEqual(captured.out, "")
        self.assertIn(str(creed_source(self.skill)), captured.err)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_cli_missing_out_dir_is_an_error(self):
        code, captured = self.run_cli("--out", str(self.tmp_path / "nowhere"), "--skill-path", str(self.skill))
        self.assertEqual(code, 2)
        self.assertIn("--out dir not found", captured.err)

    # --- classification -------------------------------------------------------

    def test_classify_absent_v7_v2_v1_damaged(self):
        sanctum = self.tmp_path / "s"
        self.assertEqual(mod.classify_sanctum(sanctum)["sidecar_format"], "absent")
        sanctum.mkdir()
        self.assertEqual(mod.classify_sanctum(sanctum)["sidecar_format"], "absent")  # empty dir
        (sanctum / "index.md").write_text("v1")
        (sanctum / "access-boundaries.md").write_text("v1 stores carried this")
        self.assertEqual(mod.classify_sanctum(sanctum)["sidecar_format"], "v1")
        for name in mod.V2_SPINE:
            (sanctum / name).write_text(name)
        state = mod.classify_sanctum(sanctum)
        self.assertEqual(state["sidecar_format"], "v2")
        self.assertTrue(state["needs_migration"])
        (sanctum / "BOND.md").unlink()
        self.assertEqual(mod.classify_sanctum(sanctum)["sidecar_format"], "damaged")

        v7 = self.tmp_path / "v7"
        v7.mkdir()
        for name in mod.IDENTITY_FILES:
            (v7 / name).write_text(name)
        self.assertEqual(mod.classify_sanctum(v7), {"sidecar_format": "v7", "needs_migration": False, "missing_spine": []})
        (v7 / "BOND.md").unlink()
        state = mod.classify_sanctum(v7)
        self.assertEqual(state["sidecar_format"], "damaged")
        self.assertEqual(state["missing_spine"], ["BOND.md"])

    def test_locate_prefers_v7_and_falls_back_to_a_legacy_store(self):
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        self.assertEqual(state["sidecar_format"], "absent")
        self.assertEqual(sanctum, mod.sanctum_dir(self.tmp_path))
        legacy = mod.legacy_sanctum_dir(self.tmp_path)
        legacy.mkdir(parents=True)
        for name in mod.V2_SPINE:
            (legacy / name).write_text(name)
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        self.assertEqual(sanctum, legacy)
        self.assertEqual(state["sidecar_format"], "v2")
        v7 = mod.sanctum_dir(self.tmp_path)
        v7.mkdir(parents=True)
        for name in mod.IDENTITY_FILES:
            (v7 / name).write_text(name)
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        self.assertEqual(sanctum, v7)
        self.assertEqual(state["sidecar_format"], "v7")

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
        self.assertIn("memory/sessions/ (2 files)", text)
        self.assertIn("memory/work/ (1 files)", text)
        self.assertIn("Tended: 2026-10-05; session notes since: 1", text)
        self.assertIn("raw/2026-10-02-notes.md", text)
        self.assertNotIn("2026-10-03-old.md", text.split("Undistilled")[1])
        self.assertTrue(mod.memory_map(self.tmp_path / "nothing") .startswith("(empty"))

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
        self.assertEqual(cfg["values"]["user_name"], "Robin")
        self.assertEqual(cfg["values"]["communication_language"], "French")
        self.assertEqual(cfg["values"]["document_output_language"], "French")
        self.assertEqual(cfg["values"]["output_folder"], "{project-root}/out")
        self.assertEqual(cfg["values"]["suno_tier"], "free")
        self.assertEqual(cfg["values"]["default_mode"], "demo")  # legacy YAML is not read
        self.assertEqual(cfg["values"]["songbook_folder"], "{project-root}/book")
        self.assertEqual(cfg["warnings"], [])

    def test_lone_voice_file_is_a_candidate_until_the_owner_is_met(self):
        """A name read off a file name is never `user_name` before First Breath has asked."""
        docs = self.tmp_path / "docs"
        docs.mkdir()
        (docs / "voice-context-mary-jane.md").write_text("# voice\n")
        cfg = mod.resolve_config(self.tmp_path)
        self.assertIsNone(cfg["values"]["user_name"])
        self.assertEqual(cfg["owner_candidate"], "Mary Jane")
        self.assertEqual(mod.normalize_username(cfg["owner_candidate"]), "mary-jane")
        self.assertTrue(any("Mary Jane" in w and "Ask the owner" in w for w in cfg["warnings"]))
        self.assertNotIn("voice file", cfg["sources"])
        # The newborn sanctum's templates stay unset rather than taking the guess.
        variables = mod.template_variables(self.tmp_path, cfg)
        self.assertEqual((variables["user_name"], variables["user_slug"]), (mod.OWNER_UNSET, "<owner>"))

        # A scaffolded bond that has not been filled in: still a candidate.
        sanctum = mod.sanctum_dir(self.tmp_path)
        sanctum.mkdir(parents=True)
        (sanctum / "BOND.md").write_text(f"# Bond\n\n- **Name:** {mod.OWNER_UNSET}\n", encoding="utf-8")
        cfg = mod.resolve_config(self.tmp_path)
        self.assertEqual((cfg["values"]["user_name"], cfg["owner_candidate"]), (None, "Mary Jane"))

        # Once BOND.md names the owner there is no candidate.
        (sanctum / "BOND.md").write_text("# Bond\n\n- **Name:** Robin\n", encoding="utf-8")
        cfg = mod.resolve_config(self.tmp_path)
        self.assertEqual((cfg["values"]["user_name"], cfg["owner_candidate"]), ("Robin", None))

        # Two voice files suggest nobody.
        (sanctum / "BOND.md").unlink()
        (docs / "voice-context-other.md").write_text("# voice\n")
        cfg = mod.resolve_config(self.tmp_path)
        self.assertEqual((cfg["values"]["user_name"], cfg["owner_candidate"]), (None, None))
        self.assertTrue(any("ask what to call the owner" in w for w in cfg["warnings"]))

    def test_lone_voice_file_still_names_an_owner_memory_has_met(self):
        """Memory that met its owner but has no readable name line keeps the voice-file name, so
        an upgrade or a restore never renders a known owner as unknown."""
        docs = self.tmp_path / "docs"
        docs.mkdir()
        (docs / "voice-context-mary-jane.md").write_text("# voice\n")
        sanctum = mod.sanctum_dir(self.tmp_path)
        sanctum.mkdir(parents=True)

        # A hand-edited bond: filled in, no `- **Name:**` line.
        (sanctum / "BOND.md").write_text("# Bond — MJ\n\nWe go back years.\n", encoding="utf-8")
        cfg = mod.resolve_config(self.tmp_path)
        self.assertEqual((cfg["values"]["user_name"], cfg["owner_candidate"]), ("Mary Jane", None))
        self.assertIn("voice file", cfg["sources"])

        # A born sanctum that lost BOND.md.
        (sanctum / "BOND.md").unlink()
        self.assertEqual(mod.resolve_config(self.tmp_path)["owner_candidate"], "Mary Jane")
        (sanctum / "memory").mkdir()
        (sanctum / "memory" / ".born").write_text("2026-06-18\n", encoding="utf-8")
        cfg = mod.resolve_config(self.tmp_path)
        self.assertEqual((cfg["values"]["user_name"], cfg["owner_candidate"]), ("Mary Jane", None))

    def test_lone_voice_file_names_the_owner_of_an_old_store(self):
        """A v1 store has no BOND.md; its owner was met long ago, so the conversion keeps the name."""
        docs = self.tmp_path / "docs"
        docs.mkdir()
        (docs / "voice-context-mary-jane.md").write_text("# voice\n")
        legacy = mod.legacy_sanctum_dir(self.tmp_path)
        legacy.mkdir(parents=True)
        (legacy / "index.md").write_text("# v1\n", encoding="utf-8")
        cfg = mod.resolve_config(self.tmp_path)
        self.assertEqual((cfg["values"]["user_name"], cfg["owner_candidate"]), ("Mary Jane", None))

    def test_broken_config_is_reported_not_called_unset(self):
        (self.tmp_path / "_bmad").mkdir()
        (self.tmp_path / "_bmad" / "config.toml").write_text("[modules.suno\nbad")
        install_resolver(self.tmp_path)
        cfg = mod.resolve_config(self.tmp_path)
        self.assertTrue(any("broken" in w for w in cfg["warnings"]))
        self.assertFalse(any("bmad setup suno` asks" in w for w in cfg["warnings"]))
        self.assertEqual(cfg["values"]["songbook_folder"], "{project-root}/docs/songbook")

    def test_not_yet_known_marker_is_not_a_name(self):
        sanctum = mod.sanctum_dir(self.tmp_path)
        sanctum.mkdir(parents=True)
        (sanctum / "BOND.md").write_text("- **Name:** _(not yet known)_\n")
        self.assertIsNone(mod.resolve_config(self.tmp_path)["values"]["user_name"])

    def test_template_token_in_bond_is_not_a_name(self):
        sanctum = mod.sanctum_dir(self.tmp_path)
        sanctum.mkdir(parents=True)
        (sanctum / "BOND.md").write_text("- **Name:** {user_name}\n")
        cfg = mod.resolve_config(self.tmp_path)
        self.assertIsNone(cfg["values"]["user_name"])
        self.assertTrue(any("user_name" in w for w in cfg["warnings"]))

    # --- roster -------------------------------------------------------------

    def test_menu_rows_route_by_their_one_skill_or_prompt(self):
        csv_path = mod.find_menu_csv(self.skill)
        self.assertEqual(csv_path, self.assets / "menu.csv")
        rows = mod.menu_rows(csv_path)
        self.assertEqual([r["code"] for r in rows], ["CS", "RS", "MB", "AA"])
        self.assertEqual(set(rows[0]), {"code", "name", "description", "action", "skill", "prompt"})
        for row in rows:
            self.assertEqual(bool(row["skill"]) + bool(row["prompt"]), 1, row["code"])
        self.assertEqual(mod.menu_problems(csv_path), [])
        self.assertEqual(mod.route_for(rows[0]), {"name": "create-song", "type": "prompt", "target": "references/create-song.md"})
        mb = next(r for r in rows if r["code"] == "MB")
        self.assertEqual(mod.route_for(mb), {"name": "manage-profiles", "type": "skill", "target": "suno-band-profile-manager"})
        # A prompt row without an action is named after its file.
        self.assertEqual(mod.route_for({"prompt": "references/liner-notes.md"}),
                         {"name": "liner-notes", "type": "prompt", "target": "references/liner-notes.md"})
        self.assertIsNone(mod.find_menu_csv(self.tmp_path / "no-skill"))

    def test_menu_rows_without_exactly_one_route_are_left_out_and_reported(self):
        csv_path = self.tmp_path / "menu.csv"
        csv_path.write_text(
            "code,name,description,action,skill,prompt\n"
            'CS,Create Song,"Create.",create-song,,references/create-song.md\n'
            'BO,Both,"Both routes.",both,some-skill,references/both.md\n'
            'NO,Neither,"No route.",neither,,\n'
            ',Nameless,"No code.",x,some-skill,\n'
            'FL,Feedback Loop,"The alias as a row.",elicit-feedback,suno-feedback-elicitor,\n'
            'CS,Again,"A repeated code.",again,,references/again.md\n', encoding="utf-8")
        self.assertEqual([r["code"] for r in mod.menu_rows(csv_path)], ["CS"])
        problems = mod.menu_problems(csv_path)
        self.assertEqual(len(problems), 5)
        self.assertIn("line 3 [BO] must name exactly one of skill or prompt", problems[0])
        self.assertIn("line 4 [NO] must name exactly one of skill or prompt", problems[1])
        self.assertIn("line 5 [?] has no code or name", problems[2])
        self.assertIn("line 6 [FL] uses a code that is an alias for [RS]", problems[3])
        self.assertIn("line 7 [CS] repeats a code", problems[4])

    def test_shipped_menu_has_one_route_per_row_and_no_alias_row(self):
        """Smoke check on the shipped assets/menu.csv: every row parses to a route, none is left out."""
        csv_path = mod.find_menu_csv(SKILL_DIR)
        self.assertEqual(mod.menu_problems(csv_path), [])
        rows = mod.menu_rows(csv_path)
        self.assertTrue(rows)
        codes = [r["code"] for r in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertFalse(set(codes) & set(mod.MENU_ALIASES))
        for alias, code in mod.MENU_ALIASES.items():
            self.assertIn(code, codes, alias)  # every alias points at a row that exists
        for row in rows:
            route = mod.route_for(row)
            self.assertTrue(route["name"] and route["target"], row["code"])
            if route["type"] == "prompt":
                self.assertTrue((SKILL_DIR / route["target"]).is_file(), route["target"])

    def test_capabilities_md_takes_its_alias_line_from_menu_aliases(self):
        """The alias sentence is built from MENU_ALIASES and the rows, the alias's one definition."""
        rows = mod.menu_rows(mod.find_menu_csv(self.skill))
        self.assertEqual(mod.alias_sentence(rows), "FL routes to [RS] Refine Song.")
        self.assertIn("FL routes to [RS] Refine Song.", mod.generate_capabilities_md(rows).split("## Learned")[0])
        without_rs = [r for r in rows if r["code"] != "RS"]
        self.assertEqual(mod.alias_sentence(without_rs), "")
        self.assertNotIn("FL", mod.generate_capabilities_md(without_rs).split("## Learned")[0])
        with patch.object(mod, "MENU_ALIASES", {"XX": "CS"}):
            self.assertEqual(mod.alias_sentence(rows), "XX routes to [CS] Create Song.")

    def test_capabilities_md_points_to_the_menu_and_keeps_learned(self):
        rows = mod.menu_rows(mod.find_menu_csv(self.skill))
        text = mod.generate_capabilities_md(rows)
        builtin = text.split("## Learned")[0]
        self.assertNotIn("Create Song", builtin)  # the wake prints the roster; it is not copied here
        self.assertNotIn("was not found", builtin)
        self.assertIn("| Code | Name | Description | Source | Added |", text.split("## Learned")[1])
        self.assertIn("assets/menu.csv was not found", mod.generate_capabilities_md([]))

    # --- old stores beside the v7 path --------------------------------------

    def _legacy(self, names):
        legacy = mod.legacy_sanctum_dir(self.tmp_path)
        legacy.mkdir(parents=True)
        for name in names:
            (legacy / name).write_text(name, encoding="utf-8")
        return legacy

    def test_locate_reports_a_partial_legacy_store_instead_of_first_breath(self):
        """One v2 spine file missing: the store is damaged, never 'absent' (a birth beside old memory)."""
        legacy = self._legacy([n for n in mod.V2_SPINE if n != "BOND.md"])
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        self.assertEqual(sanctum, legacy)
        self.assertEqual(state["sidecar_format"], "damaged")
        self.assertEqual(state["missing_spine"], ["BOND.md"])
        self.assertEqual((state["legacy_store"], state["legacy_format"]), (str(legacy), "damaged"))
        self.assertFalse(state["needs_migration"])

    def test_locate_reports_an_unrecognised_legacy_store(self):
        legacy = self._legacy(["patterns.md"])
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        self.assertEqual((sanctum, state["sidecar_format"], state["legacy_format"]), (legacy, "damaged", "damaged"))
        self.assertEqual(state["missing_spine"], mod.V2_SPINE)

    def test_locate_names_the_legacy_store_on_a_v1_or_v2_route(self):
        legacy = self._legacy(["index.md"])
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        self.assertEqual((sanctum, state["sidecar_format"]), (legacy, "v1"))
        self.assertEqual((state["legacy_store"], state["legacy_format"]), (str(legacy), "v1"))

    def test_locate_surfaces_an_unconverted_store_beside_an_unfinished_v7_path(self):
        """A stub at the v7 path must not hide the old store: the state names it."""
        legacy = self._legacy(mod.V2_SPINE)
        v7 = mod.sanctum_dir(self.tmp_path)
        (v7 / "memory" / "work").mkdir(parents=True)
        (v7 / "memory" / "work" / "current.md").write_text("# Current Work\n", encoding="utf-8")
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        self.assertEqual((sanctum, state["sidecar_format"]), (v7, "damaged"))
        self.assertEqual((state["legacy_store"], state["legacy_format"]), (str(legacy), "v2"))
        self.assertEqual(state["missing_spine"], mod.IDENTITY_FILES)

    def test_locate_ignores_the_kept_rollback_beside_a_sanctum_that_was_born(self):
        """A sanctum that was whole once (memory/.born) and lost a file: the old store is the
        owner's kept rollback, already converted, so it is not reported."""
        self._legacy(mod.V2_SPINE)
        v7 = mod.sanctum_dir(self.tmp_path)
        (v7 / "memory").mkdir(parents=True)
        (v7 / "memory" / ".born").write_text("2026-06-18\n", encoding="utf-8")
        for name in mod.IDENTITY_FILES[1:]:
            (v7 / name).write_text(name, encoding="utf-8")
        sanctum, state = mod.locate_sanctum(self.tmp_path)
        self.assertEqual((sanctum, state["sidecar_format"]), (v7, "damaged"))
        self.assertNotIn("legacy_store", state)
        # And a complete v7 sanctum never looks at the legacy path.
        (v7 / mod.IDENTITY_FILES[0]).write_text("x", encoding="utf-8")
        (v7 / "memory" / ".born").unlink()
        self.assertEqual(mod.locate_sanctum(self.tmp_path)[1],
                         {"sidecar_format": "v7", "needs_migration": False, "missing_spine": []})

    def test_locate_with_an_override_never_looks_at_the_legacy_path(self):
        self._legacy(mod.V2_SPINE)
        staging = self.tmp_path / "staging"
        sanctum, state = mod.locate_sanctum(self.tmp_path, str(staging))
        self.assertEqual((sanctum, state["sidecar_format"]), (staging, "absent"))
        self.assertNotIn("legacy_store", state)

    def test_is_legacy_path(self):
        self.assertTrue(mod.is_legacy_path(mod.legacy_sanctum_dir(self.tmp_path)))
        self.assertFalse(mod.is_legacy_path(mod.sanctum_dir(self.tmp_path)))

    # --- files that are not valid UTF-8 -------------------------------------

    def test_non_utf8_sanctum_files_are_read_with_replacement(self):
        sanctum = mod.sanctum_dir(self.tmp_path)
        (sanctum / "memory").mkdir(parents=True)
        (sanctum / "BOND.md").write_bytes(b"# Bond \xff\n\n- **Name:** Robin\n- **Language:** French\n")
        (sanctum / "memory" / "pending.md").write_bytes(b"Raise the \xff playlist.\n")
        (sanctum / "memory" / ".tended").write_bytes(b"2026-10-05\xff\n")
        self.assertEqual(mod.owner_from_bond(sanctum), {"user_name": "Robin", "communication_language": "French"})
        self.assertEqual(mod.pending_text(sanctum), "Raise the \ufffd playlist.")
        self.assertEqual(mod.tending_state(sanctum)["tended"], "2026-10-05")
        self.assertIn("Tended: 2026-10-05", mod.memory_map(sanctum))
        self.assertEqual(mod.resolve_config(self.tmp_path)["values"]["user_name"], "Robin")


if __name__ == "__main__":
    unittest.main()
