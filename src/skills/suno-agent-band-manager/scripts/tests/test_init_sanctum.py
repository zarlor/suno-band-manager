#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for init_sanctum.py — fresh BMad v7 sanctum scaffolding for Mac.

The scaffold is run against a small synthetic skill (helpers.make_skill), so
the tests assert what the script produced from inputs they own. One smoke test
runs it against the shipped skill and checks shape only.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_resolver import install_resolver  # noqa: E402
from helpers import SKILL_ASSETS, TempDirMixin, creed_source, load_script, make_skill, snapshot  # noqa: E402

mod = load_script("init_sanctum", "init_sanctum.py")


def make_project(tmp_path):
    """A minimal project: BMad config and a lone voice file (it suggests a name; the scaffold must not take it)."""
    project = tmp_path / "project"
    bmad = project / "_bmad"
    bmad.mkdir(parents=True)
    (bmad / "config.toml").write_text('[modules.suno]\nsuno_tier = "pro"\n', encoding="utf-8")
    (project / "docs").mkdir()
    (project / "docs" / "voice-context-testuser.md").write_text("# voice\n", encoding="utf-8")
    return project


def sanctum_of(project):
    return project / "_bmad" / "memory" / "suno-agent-band-manager"


def legacy_of(project):
    return project / "_bmad" / "_memory" / "band-manager-sidecar"


IDENTITY = ["PERSONA.md", "CREED.md", "BOND.md", "HOW-I-REMEMBER.md", "CAPABILITIES.md"]
# The tokens the scaffold fills in; none may survive in what it writes.
TOKENS = ("{user_name}", "{user_slug}", "{communication_language}", "{birth_date}", "{project_root}",
          "{project-root}", "{dominion}", "{songbook_folder}", "{band_profiles_folder}")


class InitSanctumTests(TempDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.skill = make_skill(self.tmp_path)
        self.project = make_project(self.tmp_path)

    def run_main(self, *argv):
        with patch.object(sys, "argv", ["init_sanctum.py", *argv]), self.capsys():
            code = mod.main()
        return code, self.capsys.readouterr()

    def test_scaffold_creates_sanctum_at_the_v7_path(self):
        result = mod.scaffold(self.project, self.skill)
        self.assertEqual(result["status"], "created")
        self.assertTrue(sanctum_of(self.project).is_dir())
        self.assertFalse((self.project / "_bmad" / "_memory").exists())
        self.assertEqual(mod._seed.classify_sanctum(sanctum_of(self.project))["sidecar_format"], "v7")

    def test_fresh_birth_has_identity_files_and_folders(self):
        result = mod.scaffold(self.project, self.skill)
        sanctum = sanctum_of(self.project)
        for name in [*IDENTITY, "PULSE.md"]:
            self.assertTrue((sanctum / name).read_text(encoding="utf-8").strip(), f"missing or empty: {name}")
            self.assertIn(name, result["created"])
        for folder in ("raw", "capabilities", *(f"memory/{kind}" for kind in mod._seed.MEMORY_KINDS)):
            self.assertTrue((sanctum / folder).is_dir(), folder)
        for old in ("INDEX.md", "MEMORY.md", "access-boundaries.md", "sessions"):
            self.assertFalse((sanctum / old).exists(), f"v2 leftover: {old}")

    def test_scaffold_fills_every_token(self):
        mod.scaffold(self.project, self.skill)
        sanctum = sanctum_of(self.project)
        for rel, data in snapshot(sanctum).items():
            if rel == "memory/.template-base.json":
                continue
            text = data.decode("utf-8")
            for token in TOKENS:
                self.assertNotIn(token, text, f"{token} left in {rel}")
        self.assertIn(str(self.project), (sanctum / "HOW-I-REMEMBER.md").read_text(encoding="utf-8"))
        creed = (sanctum / "CREED.md").read_text(encoding="utf-8")
        self.assertIn("- `docs/songbook/` — written by the song flows", creed)
        self.assertIn("- `docs/band-profiles/` — band profiles", creed)

    def test_dominion_takes_the_configured_folders(self):
        """`bmad setup suno` answers reach the newborn Dominion."""
        (self.project / "_bmad" / "config.toml").write_text(
            '[modules.suno]\nsongbook_folder = "{project-root}/music/book"\n'
            'band_profiles_folder = "{project-root}/music/bands"\n', encoding="utf-8")
        install_resolver(self.project)
        mod.scaffold(self.project, self.skill)
        creed = (sanctum_of(self.project) / "CREED.md").read_text(encoding="utf-8")
        self.assertIn("- `music/book/` — written by the song flows", creed)
        self.assertIn("- `music/bands/` — band profiles", creed)
        self.assertNotIn("docs/songbook", creed)

    def test_standing_files_split_from_memory_template_sections(self):
        mod.scaffold(self.project, self.skill)
        sanctum = sanctum_of(self.project)
        downloads = (sanctum / "memory/work/downloads.md").read_text(encoding="utf-8")
        self.assertEqual(downloads, "# Downloads\n\n- **Cap:** unknown\n")
        self.assertEqual((sanctum / "memory/owner/preferences.md").read_text(encoding="utf-8"),
                         "# User Preferences\n\n- **Tier:** unknown\n")
        published = (sanctum / "memory/catalog/recently-published.md").read_text(encoding="utf-8")
        status = (sanctum / "memory/catalog/status.md").read_text(encoding="utf-8")
        self.assertIn("<!-- derived:recently-published:start -->", published)
        self.assertIn("<!-- derived:recently-published:end -->", published)
        self.assertIn("<!-- derived:catalog-status:start -->", status)
        self.assertIn("<!-- derived:catalog-status:end -->", status)
        # The Pulse Report section is never seeded, and an empty section makes no file.
        self.assertFalse((sanctum / "memory/pending.md").exists())
        self.assertFalse((sanctum / "memory/work/session-history.md").exists())

    def test_rerun_on_a_complete_sanctum_writes_nothing(self):
        mod.scaffold(self.project, self.skill)
        before = snapshot(sanctum_of(self.project))
        second = mod.scaffold(self.project, self.skill)
        self.assertEqual(second["status"], "exists")
        self.assertEqual(second["created"], [])
        self.assertEqual(snapshot(sanctum_of(self.project)), before)

    def test_unknown_owner_is_marked_not_guessed(self):
        """With or without a lone voice file, the newborn sanctum does not name its owner:
        a name read off a file name is for Mac to confirm, not for the scaffold to write."""
        for label, keep_voice_file in (("voice file", True), ("no voice file", False)):
            with self.subTest(label):
                project = make_project(self.tmp_path / label.replace(" ", "-"))
                if not keep_voice_file:
                    (project / "docs" / "voice-context-testuser.md").unlink()
                result = mod.scaffold(project, self.skill)
                self.assertEqual(result["status"], "created")
                sanctum = sanctum_of(project)
                bond = (sanctum / "BOND.md").read_text(encoding="utf-8")
                self.assertIn(f"- **Name:** {mod._seed.OWNER_UNSET}", bond)
                self.assertIn(f"- **Language:** {mod._seed.OWNER_UNSET}", bond)
                self.assertIn("docs/voice-context-<owner>.md", bond)
                for rel, data in snapshot(sanctum).items():
                    self.assertNotIn("Testuser", data.decode("utf-8"), rel)

    def test_disciplines_and_incidents_sliced_from_the_creed_source(self):
        result = mod.scaffold(self.project, self.skill)
        sanctum = sanctum_of(self.project)
        disciplines = sorted(p.name for p in (sanctum / "memory/disciplines").iterdir())
        self.assertEqual(disciplines, ["package-assembly.md", "research-discipline.md", "thematic-discipline.md",
                                       "workshop-capture.md"])
        incidents = sorted(p.name for p in (sanctum / "memory/incidents").iterdir())
        self.assertEqual(incidents, ["thematic-discipline.md", "workshop-capture.md"])
        self.assertIn("Once, a theme was claimed unread.",
                      (sanctum / "memory/incidents/thematic-discipline.md").read_text(encoding="utf-8"))
        self.assertNotIn("Once, a theme was claimed unread.",
                         (sanctum / "memory/disciplines/thematic-discipline.md").read_text(encoding="utf-8"))
        self.assertEqual(result["warnings"], [])

    def test_unrouted_creed_heading_is_reported_in_warnings(self):
        creed = creed_source(self.skill)
        creed.write_text(creed.read_text(encoding="utf-8") + "\n## Brand New Discipline\n\nNew.\n", encoding="utf-8")
        result = mod.scaffold(self.project, self.skill)
        self.assertEqual(result["status"], "created")
        self.assertTrue(any("Brand New Discipline" in w for w in result["warnings"]), result["warnings"])

    def test_creed_carries_the_dominion_with_substituted_paths(self):
        mod.scaffold(self.project, self.skill)
        creed = (sanctum_of(self.project) / "CREED.md").read_text(encoding="utf-8")
        dominion = creed.split("## Dominion (Access Boundaries)", 1)[1].split("\n## ", 1)[0]
        for sub in ("### Read Access", "### Write Access", "### The Write Rule", "### Deny Zones", "### Notes"):
            self.assertIn(sub, dominion)
        self.assertIn(f"`{self.project}/_bmad/memory/suno-agent-band-manager/` — own memory", dominion)
        # The template's own `# ` title is not part of the Dominion.
        self.assertNotIn("# Synthetic Boundaries", creed)

    def test_capabilities_md_points_to_the_menu_and_keeps_an_empty_learned_table(self):
        result = mod.scaffold(self.project, self.skill)
        caps = (sanctum_of(self.project) / "CAPABILITIES.md").read_text(encoding="utf-8")
        self.assertEqual(caps, mod._seed.generate_capabilities_md(mod._seed.menu_rows(self.skill / "assets" / "menu.csv")))
        self.assertNotIn("Create Song", caps)  # the roster is the menu, not a copy of it
        self.assertIn("4 built-in capabilities", result["message"])  # one per row of the synthetic menu

    def test_template_base_records_what_was_seeded(self):
        result = mod.scaffold(self.project, self.skill)
        sanctum = sanctum_of(self.project)
        self.assertIn("memory/.template-base.json", result["created"])
        units = json.loads((sanctum / "memory/.template-base.json").read_text(encoding="utf-8"))["units"]
        self.assertIn("PERSONA.md ## Model Awareness", units)
        self.assertIn("CREED.md ## Dominion (Access Boundaries)", units)
        self.assertIn("memory/disciplines/research-discipline.md", units)
        self.assertEqual(units["memory/disciplines/research-discipline.md"]["text"],
                         (sanctum / "memory/disciplines/research-discipline.md").read_text(encoding="utf-8"))
        self.assertFalse(any(key.startswith("memory/incidents/") for key in units))

    # --- states that must not be scaffolded over -----------------------------

    def test_incomplete_sanctum_is_reported_not_called_existing(self):
        """A re-run on a sanctum that lost identity files restores nothing, and says so."""
        mod.scaffold(self.project, self.skill)
        sanctum = sanctum_of(self.project)
        (sanctum / "CREED.md").unlink()
        (sanctum / "BOND.md").unlink()
        before = snapshot(sanctum)
        result = mod.scaffold(self.project, self.skill)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["missing"], ["CREED.md", "BOND.md"])
        self.assertIn("upgrade_sanctum.py", result["message"])
        self.assertEqual(result["created"], [])
        self.assertEqual(snapshot(sanctum), before)
        code, captured = self.run_main(str(self.project), str(self.skill), "--format", "json")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(captured.out)["status"], "incomplete")

    def test_missing_template_is_an_error_and_nothing_is_created(self):
        for victim in ("assets/PERSONA-template.md", "assets/MEMORY-template.md",
                       "assets/ACCESS-BOUNDARIES-template.md", mod._seed.CREED_SOURCE_LABEL):
            with self.subTest(missing=victim):
                skill = make_skill(self.tmp_path, name="skill-" + victim.replace("/", "-"))
                (skill / victim).unlink()
                result = mod.scaffold(self.project, skill)
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["missing"], [victim])
                self.assertEqual(result["created"], [])
                self.assertFalse(sanctum_of(self.project).exists())
                code, captured = self.run_main(str(self.project), str(skill), "--format", "json")
                self.assertEqual(code, 1)
                self.assertIn(victim, json.loads(captured.out)["message"])

    def test_legacy_store_blocks_a_fresh_scaffold(self):
        """A fresh sanctum beside an old store would hide that store from every later wake."""
        cases = {
            "v1": ["index.md"],
            "v2": mod._seed.V2_SPINE,
            "damaged": ["MEMORY.md", "CREED.md"],  # a partial v2 spine
        }
        for fmt, names in cases.items():
            with self.subTest(fmt=fmt):
                project = make_project(self.tmp_path / fmt)
                legacy = legacy_of(project)
                legacy.mkdir(parents=True)
                for name in names:
                    (legacy / name).write_text("# old\n", encoding="utf-8")
                result = mod.scaffold(project, self.skill)
                self.assertEqual(result["status"], "refused")
                self.assertEqual(result["legacy_store"], str(legacy))
                self.assertEqual(result["legacy_format"], fmt)
                self.assertEqual(result["created"], [])
                self.assertFalse(sanctum_of(project).exists())
                code, _ = self.run_main(str(project), str(self.skill), "--format", "json")
                self.assertEqual(code, 1)

    def test_old_store_at_the_scaffold_path_is_refused(self):
        staging = self.tmp_path / "staging"
        staging.mkdir()
        (staging / "index.md").write_text("# v1\n", encoding="utf-8")
        result = mod.scaffold(self.project, self.skill, str(staging))
        self.assertEqual((result["status"], result["legacy_format"]), ("refused", "v1"))
        self.assertEqual(sorted(p.name for p in staging.iterdir()), ["index.md"])

    def test_sanctum_dir_scaffolds_there_and_leaves_the_project_sanctum_alone(self):
        staging = self.tmp_path / "staging"
        code, captured = self.run_main(str(self.project), str(self.skill), "--sanctum-dir", str(staging),
                                       "--format", "json")
        self.assertEqual(code, 0)
        payload = json.loads(captured.out)
        self.assertEqual((payload["status"], payload["sanctum_path"]), ("created", str(staging)))
        self.assertEqual(mod._seed.classify_sanctum(staging)["sidecar_format"], "v7")
        self.assertFalse(sanctum_of(self.project).exists())

    def test_cli_exit_codes_and_bad_paths(self):
        code, captured = self.run_main(str(self.project), str(self.skill), "--format", "json")
        self.assertEqual((code, json.loads(captured.out)["status"]), (0, "created"))
        code, captured = self.run_main(str(self.project), str(self.skill), "--format", "json")
        self.assertEqual((code, json.loads(captured.out)["status"]), (0, "exists"))
        code, captured = self.run_main(str(self.tmp_path / "nowhere"), str(self.skill))
        self.assertEqual(code, 2)
        self.assertIn("project root not found", captured.err)
        code, captured = self.run_main(str(self.project), str(self.tmp_path / "no-skill"))
        self.assertEqual(code, 2)
        self.assertIn("skill path not found", captured.err)

    def test_write_failure_is_reported_not_raised(self):
        def boom(*args, **kwargs):
            raise PermissionError("read-only file system")

        with patch.object(mod._seed, "record_seeded_base", boom):
            code, captured = self.run_main(str(self.project), str(self.skill), "--format", "json")
        payload = json.loads(captured.out)
        self.assertEqual((code, payload["status"]), (1, "error"))
        self.assertIn("read-only file system", payload["message"])

    # --- the shipped skill: shape only --------------------------------------

    def test_shipped_skill_scaffolds_a_complete_sanctum(self):
        result = mod.scaffold(self.project, SKILL_DIR)
        self.assertEqual(result["status"], "created")
        sanctum = sanctum_of(self.project)
        self.assertEqual(mod._seed.classify_sanctum(sanctum)["sidecar_format"], "v7")
        for name in (n.replace("-template.md", ".md") for n in SKILL_ASSETS if n.endswith("-template.md")
                     and n not in ("MEMORY-template.md", "ACCESS-BOUNDARIES-template.md")):
            text = (sanctum / name).read_text(encoding="utf-8")
            self.assertTrue(text.strip(), name)
            for token in TOKENS:
                self.assertNotIn(token, text, f"{token} left in {name}")
        self.assertTrue(any((sanctum / "memory" / "disciplines").iterdir()))


if __name__ == "__main__":
    unittest.main()
