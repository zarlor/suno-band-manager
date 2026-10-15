#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for init-sanctum.py — fresh BMad v7 sanctum scaffolding for Mac."""

import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402

spec = spec_from_file_location("init_sanctum", SCRIPTS_DIR / "init-sanctum.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def make_project(tmp_path):
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


class InitSanctumTests(TempDirMixin, unittest.TestCase):
    def test_scaffold_creates_sanctum_at_the_v7_path(self):
        project = make_project(self.tmp_path)
        result = mod.scaffold(project, SKILL_DIR)
        self.assertEqual(result["status"], "created")
        self.assertTrue(sanctum_of(project).is_dir())
        self.assertFalse((project / "_bmad" / "_memory").exists())

    def test_fresh_birth_has_identity_files_and_folders(self):
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        sanctum = sanctum_of(project)
        for name in [*IDENTITY, "PULSE.md"]:
            self.assertTrue((sanctum / name).read_text(encoding="utf-8").strip(), f"missing or empty: {name}")
        for folder in ("raw", "capabilities", "memory/work", "memory/catalog", "memory/disciplines", "memory/sessions"):
            self.assertTrue((sanctum / folder).is_dir(), folder)
        for old in ("INDEX.md", "MEMORY.md", "access-boundaries.md", "sessions"):
            self.assertFalse((sanctum / old).exists(), f"v2 leftover: {old}")

    def test_scaffold_substitutes_variables(self):
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        persona = (sanctum_of(project) / "PERSONA.md").read_text()
        self.assertIn("Testuser", persona)
        self.assertNotIn("{user_name}", persona)

    def test_standing_files_seeded_from_memory_template(self):
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        sanctum = sanctum_of(project)
        self.assertNotIn("## ", (sanctum / "memory/work/downloads.md").read_text().split("\n", 1)[1])
        self.assertTrue((sanctum / "memory/work/downloads.md").read_text().startswith("# Downloads"))
        self.assertTrue((sanctum / "memory/owner/preferences.md").is_file())
        published = (sanctum / "memory/catalog/recently-published.md").read_text()
        status = (sanctum / "memory/catalog/status.md").read_text()
        self.assertIn("<!-- derived:recently-published:start -->", published)
        self.assertIn("<!-- derived:recently-published:end -->", published)
        self.assertIn("<!-- derived:catalog-status:start -->", status)
        self.assertIn("<!-- derived:catalog-status:end -->", status)
        self.assertFalse((sanctum / "memory/pending.md").exists())  # nothing to raise yet
        self.assertFalse((sanctum / "memory/work/session-history.md").exists())  # session notes live in memory/sessions/

    def test_scaffold_is_idempotent_no_clobber(self):
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        second = mod.scaffold(project, SKILL_DIR)
        self.assertEqual(second["status"], "exists")

    def test_default_user_name_when_no_config(self):
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        result = mod.scaffold(tmp_path, SKILL_DIR)
        self.assertEqual(result["status"], "created")
        bond = (sanctum_of(tmp_path) / "BOND.md").read_text()
        self.assertIn("_(not yet known)_", bond)
        self.assertNotIn("friend", bond)
        self.assertIn("docs/voice-context-<owner>.md", bond)

    def test_fresh_birth_has_disciplines_and_incidents(self):
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        sanctum = sanctum_of(project)
        for name in ("package-assembly.md", "workshop-capture.md", "research-discipline.md",
                     "catalog-verification-discipline.md", "hedge-preservation-discipline.md"):
            self.assertTrue((sanctum / "memory/disciplines" / name).read_text(encoding="utf-8").strip(), name)
        self.assertTrue(any((sanctum / "memory/incidents").iterdir()))

    def test_creed_carries_the_dominion_with_substituted_paths(self):
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        creed = (sanctum_of(project) / "CREED.md").read_text(encoding="utf-8")
        dominion = creed.split("## Dominion (Access Boundaries)", 1)[1].split("\n## ", 1)[0]
        for sub in ("### Read Access", "### Write Access", "### The Write Rule", "### Deny Zones"):
            self.assertIn(sub, dominion)
        self.assertNotIn("{dominion}", creed)
        self.assertNotIn("{project_root}", creed)
        self.assertIn(str(project), dominion)
        self.assertIn("_bmad/memory/suno-agent-band-manager/", dominion)
        self.assertIn("memory/disciplines/package-assembly.md", creed)

    def test_fresh_birth_history_is_honest_no_migration_fiction(self):
        """A fresh birth must NOT claim migrated memories (none existed)."""
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        sanctum = sanctum_of(project)
        persona = (sanctum / "PERSONA.md").read_text(encoding="utf-8")
        self.assertNotIn("memories migrated", persona)
        self.assertNotIn("Reborn into the v2 sanctum", persona)
        self.assertIn("First Breath", persona)

    def test_fresh_birth_matches_conversion_file_set(self):
        """A fresh birth has the identity set and memory kinds a converted sanctum has."""
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        sanctum = sanctum_of(project)
        born = {p.name for p in sanctum.iterdir()}
        self.assertLessEqual(set(IDENTITY) | {"PULSE.md", "memory", "raw", "capabilities"}, born)

    def test_capabilities_md_points_to_the_menu(self):
        """CAPABILITIES.md doesn't copy the menu: one line points to it, then the Learned table."""
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        caps = (sanctum_of(project) / "CAPABILITIES.md").read_text()
        builtin = caps.split("## Built-in", 1)[1].split("## Learned", 1)[0]
        self.assertIn("The menu the wake prints", builtin)
        self.assertIn("[RS] Refine Song", builtin)
        self.assertNotIn("Create Song", caps)
        self.assertIn("## Learned", caps)

    def test_fresh_birth_templates_carry_no_install_history(self):
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        sanctum = sanctum_of(project)
        bond = (sanctum / "BOND.md").read_text()
        self.assertNotIn("patterns.md", bond)
        persona = (sanctum / "PERSONA.md").read_text()
        self.assertNotIn("v4.5", persona)
        self.assertNotIn("v5.5", persona)
        self.assertIn("SUNO-REFERENCE.md", persona)

    def test_fresh_birth_creed_has_standing_orders_and_mission_placeholder(self):
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        creed = (sanctum_of(project) / "CREED.md").read_text()
        self.assertIn("## Standing Orders", creed)
        self.assertIn("references/prompt-quality-canon.md", creed)
        self.assertIn("Discovered during First Breath", creed)
        # The Three Laws and Sacred Truth live once, in SKILL.md; the creed names them.
        self.assertNotIn("You wake.", creed)
        self.assertIn("Sacred Truth live in my SKILL.md", creed)
        self.assertIn("Is the package in the Create-screen order that create-song Step 5 gives?", creed)

    def test_how_i_remember_and_pulse_describe_the_v7_layout(self):
        project = make_project(self.tmp_path)
        mod.scaffold(project, SKILL_DIR)
        sanctum = sanctum_of(project)
        how = (sanctum / "HOW-I-REMEMBER.md").read_text()
        self.assertIn("memory/work/current.md", how)
        self.assertIn("raw/", how)
        self.assertIn("memory/.tended", how)
        pulse = (sanctum / "PULSE.md").read_text()
        self.assertIn("memory/pending.md", pulse)
        self.assertNotIn("MEMORY.md", pulse)
        self.assertIn("_bmad/memory/suno-agent-band-manager/", pulse)

    def test_bundle_ships_what_the_canon_order_points_to(self):
        """The CREED's Author-to-the-standard order points at files the skill ships."""
        self.assertTrue((SKILL_DIR / "references" / "prompt-quality-canon.md").is_file())
        self.assertTrue((SKILL_DIR / "references" / "capability-authoring.md").is_file())


if __name__ == "__main__":
    unittest.main()
