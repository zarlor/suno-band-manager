#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for pre_activate.py

The menu the wake renders comes from a CSV the tests write (SAMPLE_CSV), so no
test depends on the rows the shipped assets/menu.csv happens to hold. The
scaffold tests run the real init_sanctum.py against the shipped skill and check
shape only (mode, file names, block markers).
"""

import argparse
import io
import json
import shutil
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_resolver import install_resolver  # noqa: E402
from helpers import TempDirMixin, make_skill  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

# Load module
spec = spec_from_file_location(
    "pre_activate",
    Path(__file__).parent.parent / "pre_activate.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE_CSV = (
    "code,name,description,action,skill,prompt\n"
    'CS,Create Song,"Create a song package.",create-song,,references/create-song.md\n'
    'RS,Refine Song,"Refine a song.",refine-song,,references/refine-song.md\n'
    'MB,Manage Bands,"Manage band profiles.",manage-profiles,suno-band-profile-manager,\n'
    'AA,Analyze Audio,"Measure a render.",analyze-audio,suno-feedback-elicitor,\n'
)

SPINE = ["PERSONA.md", "CREED.md", "BOND.md", "HOW-I-REMEMBER.md", "CAPABILITIES.md"]
V2_SPINE = [
    "access-boundaries.md",
    "INDEX.md",
    "MEMORY.md",
    "CREED.md",
    "PERSONA.md",
    "BOND.md",
    "CAPABILITIES.md",
]


def _full_spine(sanctum, names=SPINE):
    for name in names:
        (sanctum / name).write_text(f"# {name}\n")
    if names is SPINE:  # a born v7 sanctum
        (sanctum / "memory").mkdir(exist_ok=True)
        (sanctum / "memory" / ".born").write_text("2026-06-18\n")


# The real skill directory — init_sanctum.py reads its assets/ templates from here.
SKILL_DIR = Path(__file__).parent.parent.parent


# --- three-way (four-state) sidecar-format detection ---


def _make_sanctum(tmp_path):
    sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
    sanctum.mkdir(parents=True)
    return sanctum


def _make_legacy(tmp_path):
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    return sanctum


def _write_csv(tmp_path, content=SAMPLE_CSV):
    """Helper to write a test CSV file."""
    csv_path = tmp_path / "menu.csv"
    csv_path.write_text(content)
    return csv_path


def _run_main_rc(argv):
    """Run main() with argv patched; return (exit code, what it printed to stdout)."""
    out = io.StringIO()
    with mock.patch.object(sys, "argv", ["pre_activate.py", *argv]), \
            redirect_stdout(out), redirect_stderr(io.StringIO()):
        code = mod.main()
    return code, out.getvalue()


def _run_main(argv):
    """Run main() with argv patched; return what it printed to stdout."""
    return _run_main_rc(argv)[1]


def _state_of(wake_output):
    """The compact state JSON a --wake output carries."""
    return json.loads(wake_output.split("===== STATE =====\n", 1)[1].split("\n", 1)[0])


def _args(**overrides):
    """Parsed arguments for build_state(), as main() would pass them."""
    values = {"wake": True, "pulse": False, "scaffold": False, "sanctum_dir": None, "user_name": None, "output": None}
    return argparse.Namespace(**{**values, **overrides})


def _skill_with_scripts(tmp_path, name="skill"):
    """The synthetic skill plus the two scripts a scaffold runs, so --scaffold works against it."""
    skill = make_skill(tmp_path, name=name)
    (skill / "scripts").mkdir()
    for script in ("init_sanctum.py", "_sanctum_seed.py"):
        shutil.copy2(Path(mod.__file__).parent / script, skill / "scripts" / script)
    return skill


class PreActivateTests(TempDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        # The wake's menu comes from this CSV, not from the shipped assets/menu.csv.
        self.menu_csv = self.tmp_path / "wake-menu.csv"
        self.menu_csv.write_text(SAMPLE_CSV, encoding="utf-8")
        self.enterContext(mock.patch.object(mod, "find_menu_csv", lambda *_: self.menu_csv))

    def test_check_first_run_true(self):
        """First run when sanctum doesn't exist."""
        tmp_path = self.tmp_path
        self.assertIs(mod.check_first_run(tmp_path), True)

    def test_check_first_run_false(self):
        """Not first run when the sanctum holds anything."""
        tmp_path = self.tmp_path
        sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
        sanctum.mkdir(parents=True)
        self.assertIs(mod.check_first_run(tmp_path), True)  # an empty dir is not a sanctum
        (sanctum / "PERSONA.md").write_text("x")
        self.assertIs(mod.check_first_run(tmp_path), False)

    def test_check_first_run_honors_sanctum_dir_override(self):
        """--sanctum-dir override controls first-run detection."""
        tmp_path = self.tmp_path
        staging = tmp_path / "staging"
        # Override points at a non-existent dir → first run.
        self.assertIs(mod.check_first_run(tmp_path, sanctum_dir=str(staging)), True)
        staging.mkdir()
        self.assertIs(mod.check_first_run(tmp_path, sanctum_dir=str(staging)), True)  # empty
        (staging / "PERSONA.md").write_text("x")
        self.assertIs(mod.check_first_run(tmp_path, sanctum_dir=str(staging)), False)

    def test_detect_format_absent(self):
        """No sanctum dir → 'absent', no migration → genuine first run."""
        tmp_path = self.tmp_path
        state = mod.detect_sidecar_format(tmp_path)
        self.assertEqual(state["sidecar_format"], "absent")
        self.assertIs(state["needs_migration"], False)
        # first_run is the 'absent' case.
        self.assertIs(mod.check_first_run(tmp_path), True)

    def test_detect_format_v1_needs_migration(self):
        """Old v1 layout at the legacy path (index.md, no v2 markers) → 'v1', needs migration."""
        tmp_path = self.tmp_path
        sanctum = _make_legacy(tmp_path)
        (sanctum / "index.md").write_text("# old content store\n")
        (sanctum / "patterns.md").write_text("# patterns\n")
        state = mod.detect_sidecar_format(tmp_path)
        self.assertEqual(state["sidecar_format"], "v1")
        self.assertIs(state["needs_migration"], True)
        # Critically: NOT first_run (the dir exists), so the old code path would have
        # tried to load v2 files and fallen into the damaged fallback.
        self.assertIs(mod.check_first_run(tmp_path), False)

    def test_detect_format_v7_loads_normally(self):
        """The identity set present → 'v7', no migration → normal load."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        state = mod.detect_sidecar_format(tmp_path)
        self.assertEqual(state["sidecar_format"], "v7")
        self.assertIs(state["needs_migration"], False)
        self.assertEqual(state["missing_spine"], [])

    def test_detect_format_legacy_v2_needs_conversion(self):
        """The old seven-file spine at the legacy path → 'v2', converted, never woken."""
        tmp_path = self.tmp_path
        _full_spine(_make_legacy(tmp_path), V2_SPINE)
        state = mod.detect_sidecar_format(tmp_path)
        self.assertEqual(state["sidecar_format"], "v2")
        self.assertIs(state["needs_migration"], True)

    def test_detect_format_partial_spine_is_damaged(self):
        """A half-built v7 sanctum is damaged, never loaded as if whole."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        (sanctum / "HOW-I-REMEMBER.md").write_text("# layout\n")
        state = mod.detect_sidecar_format(tmp_path)
        self.assertEqual(state["sidecar_format"], "damaged")
        self.assertIs(state["needs_migration"], False)
        self.assertIn("PERSONA.md", state["missing_spine"])

    def test_detect_format_v2_wins_even_with_legacy_index(self):
        """A full v2 spine plus a stray legacy index.md is still v2."""
        tmp_path = self.tmp_path
        sanctum = _make_legacy(tmp_path)
        _full_spine(sanctum, V2_SPINE)
        (sanctum / "index.md").write_text("# stray legacy index\n")
        state = mod.detect_sidecar_format(tmp_path)
        self.assertEqual(state["sidecar_format"], "v2")

    def test_detect_format_v1_on_case_insensitive_filesystem(self):
        """On APFS/NTFS, is_file('INDEX.md') is true for a v1 index.md. Detection must
        compare real directory entries, so the store is still v1."""
        tmp_path = self.tmp_path
        sanctum = _make_legacy(tmp_path)
        (sanctum / "index.md").write_text("# v1 store\n")
        real_is_file = Path.is_file

        def insensitive_is_file(self):
            if self.parent == sanctum:
                return any(p.name.lower() == self.name.lower() for p in sanctum.iterdir())
            return real_is_file(self)

        self.enterContext(mock.patch.object(Path, "is_file", insensitive_is_file))
        state = mod.detect_sidecar_format(tmp_path)
        self.assertEqual(state["sidecar_format"], "v1")
        self.assertIs(state["needs_migration"], True)

    def test_detect_format_damaged(self):
        """A non-empty v7 dir with no identity file → 'damaged'."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        (sanctum / "stray.txt").write_text("junk\n")
        state = mod.detect_sidecar_format(tmp_path)
        self.assertEqual(state["sidecar_format"], "damaged")
        self.assertIs(state["needs_migration"], False)

    def test_detect_format_honors_sanctum_dir_override(self):
        """--sanctum-dir override drives format detection too."""
        tmp_path = self.tmp_path
        staging = tmp_path / "staging"
        staging.mkdir()
        (staging / "index.md").write_text("# v1\n")
        state = mod.detect_sidecar_format(tmp_path, sanctum_dir=str(staging))
        self.assertEqual(state["sidecar_format"], "v1")
        self.assertIs(state["needs_migration"], True)

    def test_main_emits_sidecar_format_and_needs_migration(self):
        """pre-activate JSON output carries sidecar_format + needs_migration, and the v1 mode."""
        tmp_path = self.tmp_path
        bmad_dir = tmp_path / "_bmad"
        bmad_dir.mkdir()
        sanctum = bmad_dir / "_memory" / "band-manager-sidecar"
        sanctum.mkdir(parents=True)
        (sanctum / "index.md").write_text("# old store\n")
        # A v1 store is found at the legacy path.

        payload = json.loads(_run_main([str(tmp_path)]))

        self.assertEqual(payload["sidecar_format"], "v1")
        self.assertIs(payload["needs_migration"], True)
        # first_run stays back-compatible: only true for the absent case.
        self.assertIs(payload["first_run"], False)
        # SKILL.md routes on the mode: a v1 store is never sent down the v2 route.
        self.assertEqual(payload["mode"], "UPGRADE_V1")
        self.assertEqual(payload["legacy_store"], {"path": str(sanctum.resolve()), "sidecar_format": "v1"})

    def test_wake_on_a_v1_store_routes_to_its_migration_and_prints_no_files(self):
        """A v1 store has no spine to become: MODE: UPGRADE_V1, the v1 route, nothing printed."""
        tmp_path = self.tmp_path
        legacy = _make_legacy(tmp_path)
        (legacy / "index.md").write_text("# old content store\n\n## User Preferences\n\n- secret\n")
        (legacy / "PULSE.md").write_text("# not a spine file\n")
        out = _run_main([str(tmp_path), "--wake"])
        self.assertTrue(out.startswith("MODE: UPGRADE_V1\n"))
        self.assertIn("references/upgrade-v1.md", out)
        self.assertNotIn("references/upgrade-v2.md", out)
        self.assertNotIn("===== PERSONA.md =====", out)
        self.assertNotIn("===== MENU =====", out)
        self.assertNotIn("===== memory map =====", out)
        self.assertNotIn("- secret", out)
        self.assertEqual(_state_of(out)["mode"], "UPGRADE_V1")

    def test_scaffold_delegates_to_init_sanctum(self):
        """Scaffold builds the v7 sanctum via init_sanctum.py."""
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        result = mod.scaffold_sidecar(tmp_path, SKILL_DIR)
        self.assertIs(result["scaffolded"], True)
        self.assertEqual(result["via"], "init_sanctum.py")

        sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
        for name in SPINE:
            self.assertTrue((sanctum / name).exists(), name)
        self.assertTrue((sanctum / "memory" / "work").is_dir())
        self.assertTrue((sanctum / "raw").is_dir())

    def test_scaffold_idempotent(self):
        """Scaffold is a no-op when the sanctum already exists (init-sanctum guards)."""
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        mod.scaffold_sidecar(tmp_path, SKILL_DIR)
        sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
        (sanctum / "BOND.md").write_text("custom content")

        # Second scaffold: init_sanctum.py reports "exists" and creates nothing.
        result = mod.scaffold_sidecar(tmp_path, SKILL_DIR)
        self.assertEqual(result["init_result"].get("status"), "exists")
        self.assertEqual((sanctum / "BOND.md").read_text(), "custom content")

    def test_render_menu(self):
        """Menu renders correctly from assets/menu.csv."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)

        menu = mod.render_menu(csv_path)
        # Agent and external skill entries should appear
        self.assertIn("[CS]", menu)
        self.assertIn("[RS]", menu)
        self.assertIn("[MB]", menu)
        self.assertIn("Create Song", menu)

    def test_shipped_menu_renders_and_routes(self):
        """Smoke check on the shipped assets/menu.csv: shape only."""
        csv_path = mod._seed.find_menu_csv(SKILL_DIR)
        self.assertIsNotNone(csv_path)
        lines = mod.render_menu(csv_path).splitlines()[2:]
        self.assertTrue(lines)
        for number, line in enumerate(lines, 1):
            self.assertRegex(line, rf"^{number}\. \[[A-Z0-9]+\] .+ — .+")
        table = mod.build_routing_table(csv_path)
        self.assertEqual(len([v for v in table.values() if isinstance(v, dict)]), len(lines))
        for route in table.values():
            if isinstance(route, dict):
                self.assertIn(route["type"], ("prompt", "skill"))
                self.assertTrue(route["target"])

    def test_build_routing_table_agent_capabilities(self):
        """Agent's own capabilities route to prompt references."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)

        table = mod.build_routing_table(csv_path)
        self.assertEqual(table["CS"]["type"], "prompt")
        self.assertEqual(table["CS"]["target"], "references/create-song.md")
        self.assertEqual(table["RS"]["type"], "prompt")
        self.assertEqual(table["RS"]["target"], "references/refine-song.md")

    def test_build_routing_table_external_skills(self):
        """External skill capabilities route to skill invocation."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)

        table = mod.build_routing_table(csv_path)
        self.assertEqual(table["MB"]["type"], "skill")
        self.assertEqual(table["MB"]["target"], "suno-band-profile-manager")

    def test_routing_table_is_keyed_by_code_in_menu_order(self):
        """Codes only; their order is the menu's line order, so a number maps to a printed line."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)

        table = mod.build_routing_table(csv_path)
        self.assertFalse(any(key.isdigit() for key in table))
        # CS is line 1, AA follows MB; the alias has no line and comes last.
        self.assertEqual(list(table), ["CS", "RS", "MB", "AA", "FL"])
        lines = mod.render_menu(csv_path).splitlines()
        self.assertTrue(lines[2].startswith("1. [CS]"))
        self.assertTrue(lines[5].startswith("4. [AA]"))

    def test_menu_folds_feedback_loop_into_refine_song(self):
        """FL has no menu line; typing FL routes to RS (the alias, defined once in the seed). AA stays."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)
        menu = mod.render_menu(csv_path)
        self.assertNotIn("[FL]", menu)
        self.assertIn("[AA]", menu)
        table = mod.build_routing_table(csv_path)
        self.assertEqual(table["FL"], "RS")
        self.assertEqual(mod.MENU_ALIASES, mod._seed.MENU_ALIASES)

    def test_menu_rows_without_exactly_one_route_are_left_off_and_warned(self):
        """A row naming both a skill and a prompt, neither, or an alias code has no route:
        it leaves the menu and the routing table, and the wake says which line."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        self.menu_csv.write_text(
            "code,name,description,action,skill,prompt\n"
            'CS,Create Song,"Create.",create-song,,references/create-song.md\n'
            'BO,Both,"Both routes.",both,some-skill,references/both.md\n'
            'NO,Neither,"No route.",neither,,\n'
            'FL,Feedback Loop,"An alias code as a row.",elicit-feedback,suno-feedback-elicitor,\n'
            'CS,Create Again,"Repeated code.",create-again,,references/create-again.md\n'
            'MB,Manage Bands,"Manage.",manage-profiles,suno-band-profile-manager,\n', encoding="utf-8")
        payload = json.loads(_run_main([str(tmp_path)]))
        # No RS row here, so the FL alias has nothing to point at and is not routed either.
        self.assertEqual(list(payload["routing_table"]), ["CS", "MB"])
        self.assertEqual(payload["routing_table"]["CS"],
                         {"name": "create-song", "type": "prompt", "target": "references/create-song.md"})
        self.assertEqual(payload["routing_table"]["MB"],
                         {"name": "manage-profiles", "type": "skill", "target": "suno-band-profile-manager"})
        for gone in ("[BO]", "[NO]", "[FL]", "Create Again"):
            self.assertNotIn(gone, payload["menu_text"])
        left_out = [w for w in payload["warnings"] if "left off the menu" in w and "menu.csv" in w]
        self.assertEqual(len(left_out), 4)
        self.assertTrue(any("line 3 [BO]" in w and "exactly one of skill or prompt" in w for w in left_out))
        self.assertTrue(any("line 4 [NO]" in w for w in left_out))
        self.assertTrue(any("line 5 [FL]" in w and "alias" in w for w in left_out))
        self.assertTrue(any("line 6 [CS]" in w and "repeats" in w for w in left_out))

    def test_learned_capabilities_reach_the_menu(self):
        """Rows in the sanctum CAPABILITIES.md Learned table appear on the menu."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)
        sanctum = _make_sanctum(tmp_path)
        (sanctum / "CAPABILITIES.md").write_text(
            "# Capabilities\n\n## Built-in\n\n| Code | Name |\n\n## Learned\n\n"
            "| Code | Name | Description | Source | Added |\n"
            "|------|------|-------------|--------|-------|\n"
            "| [LX] | Liner Notes | Draft liner notes. | `capabilities/liner-notes.md` | 2026-10-01 |\n"
        )
        learned = mod.learned_capabilities(sanctum)
        self.assertEqual(learned[0]["code"], "LX")
        menu = mod.render_menu(csv_path, learned=learned)
        self.assertIn("[LX] Liner Notes", menu)
        table = mod.build_routing_table(csv_path, learned=learned)
        self.assertEqual(table["LX"]["type"], "learned")
        self.assertTrue(table["LX"]["target"].endswith("capabilities/liner-notes.md"))

    def test_find_menu_csv_in_skill_assets(self):
        """Finds the menu in the skill's own assets."""
        tmp_path = self.tmp_path
        skill_dir = tmp_path / "skills" / "suno-agent-band-manager"
        (skill_dir / "assets").mkdir(parents=True)
        csv_file = skill_dir / "assets" / "menu.csv"
        csv_file.write_text(SAMPLE_CSV)
        self.assertEqual(mod._seed.find_menu_csv(skill_dir), csv_file)

    def test_find_menu_csv_not_found(self):
        """Returns None when the menu file is missing; a v6 module-help.csv is not read."""
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        (tmp_path / "_bmad" / "module-help.csv").write_text(SAMPLE_CSV)
        skill_dir = tmp_path / "skills" / "suno-agent-band-manager"
        skill_dir.mkdir(parents=True)
        self.assertIsNone(mod._seed.find_menu_csv(skill_dir))

    def test_sanctum_load_order_is_the_v7_identity_set(self):
        """The always-loaded waking set is the five identity files, in order; Pulse adds PULSE.md."""
        self.assertEqual(mod.SANCTUM_LOAD_ORDER, ["PERSONA.md", "CREED.md", "BOND.md", "HOW-I-REMEMBER.md", "CAPABILITIES.md"])
        self.assertEqual(mod.PULSE_LOAD_ORDER, [*mod.SANCTUM_LOAD_ORDER, "PULSE.md"])

    def test_missing_csv_still_wakes(self):
        """No assets/menu.csv: menu is null with a warning, the sanctum still wakes."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        self.enterContext(mock.patch.object(mod, "find_menu_csv", lambda *_: None))
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertEqual(payload["sidecar_format"], "v7")
        self.assertEqual(payload["mode"], "WAKING")
        self.assertIsNone(payload["menu_text"])
        self.assertIsNone(payload["routing_table"])
        self.assertTrue(any("menu.csv" in w for w in payload["warnings"]))
        self.assertEqual(payload["sanctum_load_order"][0], "PERSONA.md")

    def test_config_resolved_from_v7_config_and_bond(self):
        """pre-activate resolves the suno answers from BMad v7 config and the owner
        from BOND.md; the voice file matches with no --user-name."""
        tmp_path = self.tmp_path
        bmad = tmp_path / "_bmad"
        bmad.mkdir()
        (bmad / "config.toml").write_text(
            '[core]\noutput_folder = "{project-root}/out"\n'
            '[modules.suno]\nsuno_tier = "premier"\ndefault_mode = "studio"\n'
        )
        install_resolver(tmp_path)
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        (sanctum / "BOND.md").write_text("# Bond\n\n- **Name:** Alex Smith\n- **Language:** English\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "voice-context-alex-smith.md").write_text("# voice\n")
        (docs / "voice-context-someone-else.md").write_text("# voice\n")
        (docs / "mac-preferences.md").write_text("# prefs\n")
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertEqual(payload["config"]["user_name"], "Alex Smith")
        self.assertEqual(payload["config"]["suno_tier"], "premier")
        self.assertEqual(payload["config"]["default_mode"], "studio")
        self.assertEqual(payload["config"]["output_folder"], "{project-root}/out")
        vc = payload["voice_context"]
        self.assertEqual(vc["matched_file"], "docs/voice-context-alex-smith.md")
        self.assertEqual(vc["mac_preferences"], "docs/mac-preferences.md")
        self.assertGreaterEqual(vc["sizes"]["docs/mac-preferences.md"]["tokens_est"], 1)

    def test_lone_voice_file_is_reported_as_a_candidate_not_the_owner(self):
        """Before the owner is met, a lone voice file's name is `voice_context.owner_candidate`;
        `config.user_name` stays null, so nothing is matched or loaded on a guess."""
        tmp_path = self.tmp_path
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "voice-context-mary-jane.md").write_text("# voice\n")
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertIsNone(payload["config"]["user_name"])
        vc = payload["voice_context"]
        self.assertEqual(vc["owner_candidate"], "Mary Jane")
        self.assertIsNone(vc["matched_file"])
        self.assertEqual(vc["voice_files"], ["docs/voice-context-mary-jane.md"])
        self.assertTrue(any("Mary Jane" in w for w in payload["warnings"]))

        # Named by BOND.md: no candidate, and the file matches.
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        (sanctum / "BOND.md").write_text("# Bond\n\n- **Name:** Mary Jane\n- **Language:** English\n")
        vc = json.loads(_run_main([str(tmp_path)]))["voice_context"]
        self.assertIsNone(vc["owner_candidate"])
        self.assertEqual(vc["matched_file"], "docs/voice-context-mary-jane.md")

        # Named on the command line: the override wins and the guess is dropped.
        (sanctum / "BOND.md").write_text("# Bond\n\n- **Name:** _(not yet known)_\n")
        payload = json.loads(_run_main([str(tmp_path), "--user-name", "Robin"]))
        self.assertEqual(payload["config"]["user_name"], "Robin")
        self.assertIsNone(payload["voice_context"]["owner_candidate"])

    def test_config_defaults_when_missing(self):
        """No config at all: English defaults, a warning, no crash."""
        tmp_path = self.tmp_path
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertEqual(payload["config"]["communication_language"], "English")
        self.assertIsNone(payload["config"]["user_name"])
        self.assertTrue(any(w.startswith("user_name") for w in payload["warnings"]))

    def test_wake_prints_spine_in_load_order(self):
        """--wake prints MODE, state, the identity files in order, then the memory map."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        (sanctum / "PULSE.md").write_text("# PULSE.md\n")
        (sanctum / "memory" / "work").mkdir(parents=True)
        (sanctum / "memory" / "work" / "current.md").write_text("pick up here")
        (sanctum / "memory" / "pending.md").write_text("Raise the Redux playlist.\n")
        out = _run_main([str(tmp_path), "--wake"])
        self.assertTrue(out.startswith("MODE: WAKING"))
        positions = [out.index(f"===== {name} =====") for name in [*SPINE, "memory map", "memory/pending.md"]]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("memory/work/ (1 files)", out)
        self.assertIn("Raise the Redux playlist.", out)
        self.assertNotIn("pick up here", out)  # memory is mapped, not printed
        self.assertNotIn("===== PULSE.md =====", out)

    def test_pulse_prints_maintenance_set(self):
        """--pulse prints the identity files, then PULSE.md, then the map."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        (sanctum / "PULSE.md").write_text("# PULSE.md\n")
        out = _run_main([str(tmp_path), "--pulse"])
        self.assertTrue(out.startswith("MODE: PULSE"))
        names = [*SPINE, "PULSE.md", "memory map"]
        positions = [out.index(f"===== {n} =====") for n in names]
        self.assertEqual(positions, sorted(positions))

    def test_wake_on_a_legacy_v2_store_routes_to_conversion(self):
        """A v2 store wakes as itself (old spine printed) and is told to convert."""
        tmp_path = self.tmp_path
        legacy = _make_legacy(tmp_path)
        _full_spine(legacy, V2_SPINE)
        (legacy / "BOND.md").write_text("- **Name:** Robin\n")
        out = _run_main([str(tmp_path), "--wake"])
        self.assertTrue(out.startswith("MODE: UPGRADE_V2"))
        self.assertIn("references/upgrade-v2.md", out)
        self.assertIn("===== MEMORY.md =====", out)
        self.assertIn("===== INDEX.md =====", out)
        self.assertNotIn("===== memory map =====", out)
        self.assertIn('"user_name":"Robin"', out)
        self.assertFalse((tmp_path / "_bmad" / "memory").exists())

    def test_pulse_without_sanctum_is_skipped(self):
        tmp_path = self.tmp_path
        out = _run_main([str(tmp_path), "--pulse"])
        self.assertTrue(out.startswith("MODE: PULSE_SKIPPED"))

    def test_wake_damaged_prints_present_files(self):
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        (sanctum / "PERSONA.md").write_text("# PERSONA.md\n")
        out = _run_main([str(tmp_path), "--wake"])
        self.assertTrue(out.startswith("MODE: DAMAGED"))
        self.assertIn("(missing: CREED.md)", out)

    def test_wake_scaffold_is_first_breath_and_prints_newborn(self):
        """--wake --scaffold on an absent sanctum: born, still First Breath, printed."""
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        out = _run_main([str(tmp_path), "--wake", "--scaffold"])
        self.assertTrue(out.startswith("MODE: FIRST_BREATH"))
        self.assertIn("references/init.md", out)
        self.assertIn("===== HOW-I-REMEMBER.md =====", out)
        self.assertIn("===== memory map =====", out)
        self.assertNotIn("(missing:", out)

    def test_wake_first_breath_without_scaffold(self):
        tmp_path = self.tmp_path
        out = _run_main([str(tmp_path), "--wake"])
        self.assertTrue(out.startswith("MODE: FIRST_BREATH"))
        self.assertIn("--scaffold", out)
        self.assertFalse((tmp_path / "_bmad" / "memory").exists())

    def test_main_emits_menu_text_key(self):
        """The pre-activate JSON output uses the `menu_text` key (not `menu`), rendered from the menu CSV."""
        tmp_path = self.tmp_path
        self.menu_csv.write_text(
            "code,name,description,action,skill,prompt\n"
            'ZZ,Only Row,"The one row of this menu.",only-row,,references/only-row.md\n', encoding="utf-8")

        payload = json.loads(_run_main([str(tmp_path)]))

        self.assertIn("menu_text", payload)
        self.assertNotIn("menu", payload)
        self.assertEqual(payload["menu_text"],
                         "What would you like to do today?\n\n1. [ZZ] Only Row — The one row of this menu.")
        self.assertEqual(payload["routing_table"],
                         {"ZZ": {"name": "only-row", "type": "prompt", "target": "references/only-row.md"}})
        # The load order is surfaced as the v7 identity set.
        self.assertEqual(payload["sanctum_load_order"], mod.SANCTUM_LOAD_ORDER)
        self.assertEqual(mod.SANCTUM_LOAD_ORDER, SPINE)

    def test_unfinished_first_breath_resumes(self):
        """A v7 sanctum without memory/.born is a First Breath cut short."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        (sanctum / "memory" / ".born").unlink()
        out = _run_main([str(tmp_path), "--wake"])
        self.assertTrue(out.startswith("MODE: FIRST_BREATH"))
        self.assertIn("cut short", out)
        self.assertIn("===== PERSONA.md =====", out)
        self.assertIn('"resume":true', out)

    def test_wake_prints_the_menu_once_beside_a_compact_state(self):
        """The menu is its own block; the state JSON is one compact line without it."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        out = _run_main([str(tmp_path), "--wake"])
        self.assertTrue(out.startswith("MODE: WAKING"))
        state = json.loads(out.split("===== STATE =====\n", 1)[1].split("\n", 1)[0])
        self.assertNotIn("menu_text", state)
        self.assertEqual(state["routing_table"]["CS"]["type"], "prompt")
        self.assertEqual(state["routing_table"]["FL"], "RS")
        self.assertIn("===== MENU =====\nWhat would you like to do today?", out)
        self.assertEqual(out.count("[CS] Create Song"), 1)

    def test_scaffold_failure_is_its_own_mode_and_exits_nonzero(self):
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        self.enterContext(mock.patch.object(mod, "scaffold_sidecar", lambda *a, **k: {"scaffolded": False, "error": True, "message": "disk full"}))
        buf = io.StringIO()
        with mock.patch.object(sys, "argv", ["pre_activate.py", str(tmp_path), "--wake", "--scaffold"]), \
                redirect_stdout(buf), redirect_stderr(io.StringIO()):
            self.assertEqual(mod.main(), 1)
        out = buf.getvalue()
        self.assertTrue(out.startswith("MODE: SCAFFOLD_FAILED"))
        self.assertIn("disk full", out)

    def test_learned_rows_that_miss_the_menu_are_warned(self):
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        (sanctum / "CAPABILITIES.md").write_text(
            "## Learned\n\n| Code | Name | Description | Source | Added |\n|---|---|---|---|---|\n"
            "| [CS] | Clash | Clashes. | `capabilities/x.md` | 2026-10-01 |\n"
            "| LX | Broken row without brackets |\n"
        )
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertTrue(any("[CS] clashes" in w for w in payload["warnings"]))
        self.assertTrue(any("not readable" in w for w in payload["warnings"]))

    def test_customization_arrays_reach_the_state(self):
        tmp_path = self.tmp_path
        scripts = tmp_path / "_bmad" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "resolve_customization.py").write_text(
            "import json\nprint(json.dumps({'agent': {'persistent_facts': ['file:docs/house-style.md'],"
            " 'activation_steps_prepend': ['say hi'], 'activation_steps_append': []}}))\n"
        )
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertEqual(payload["customization"]["persistent_facts"], ["file:docs/house-style.md"])
        self.assertEqual(payload["customization"]["activation_steps_prepend"], ["say hi"])

    def test_resolved_icon_reaches_the_wake_state(self):
        """A team override of agent.icon is what the wake prints, so the greeting can lead with it."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        scripts = tmp_path / "_bmad" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "resolve_customization.py").write_text(
            "import json\nprint(json.dumps({'agent': {'icon': 'SAX', 'persistent_facts': 'not-a-list'}}))\n")
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertEqual(payload["customization"]["icon"], "SAX")
        self.assertEqual(payload["customization"]["persistent_facts"], [])  # a non-list is not iterated
        state = _state_of(_run_main([str(tmp_path), "--wake"]))
        self.assertEqual(state["customization"]["icon"], "SAX")

    def test_icon_falls_back_to_the_skill_default(self):
        """No resolver, a resolver with no icon, or a failing one: the icon the skill ships."""
        tmp_path = self.tmp_path
        skill = tmp_path / "skill-with-toml"
        skill.mkdir()
        (skill / "customize.toml").write_text('[agent]\nname = "Mac"\nicon = "HORN"\n', encoding="utf-8")
        self.assertEqual(mod.shipped_icon(skill), "HORN")
        self.assertEqual(mod.shipped_icon(tmp_path / "no-skill"), "")
        (tmp_path / "broken").mkdir()
        (tmp_path / "broken" / "customize.toml").write_text("[agent\nicon =", encoding="utf-8")
        self.assertEqual(mod.shipped_icon(tmp_path / "broken"), "")

        resolved, warning = mod.resolve_customization(tmp_path, skill)
        self.assertEqual(resolved["icon"], "HORN")
        self.assertIn("resolve_customization", warning)

        scripts = tmp_path / "_bmad" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "resolve_customization.py").write_text("import json\nprint(json.dumps({'agent': {}}))\n")
        self.assertEqual(mod.resolve_customization(tmp_path, skill), (
            {"icon": "HORN", "activation_steps_prepend": [], "activation_steps_append": [], "persistent_facts": []},
            None))
        (scripts / "resolve_customization.py").write_text("import sys\nsys.exit(3)\n")
        resolved, warning = mod.resolve_customization(tmp_path, skill)
        self.assertEqual(resolved["icon"], "HORN")
        self.assertIn("could not be resolved", warning)

    def test_no_bmad_means_empty_customization_with_a_reason(self):
        tmp_path = self.tmp_path
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertEqual(payload["customization"], {"icon": mod.shipped_icon(SKILL_DIR), "activation_steps_prepend": [],
                                                    "activation_steps_append": [], "persistent_facts": []})
        self.assertTrue(any("resolve_customization" in w for w in payload["warnings"]))

    # --- wake state keys the activation prompt branches on --------------------

    def test_template_upgrade_reaches_the_wake_with_its_warning(self):
        """A sanctum behind the shipped templates: the wake counts what is pending and warns."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertGreater(payload["template_upgrade"]["safe"], 0)
        self.assertIsInstance(payload["template_upgrade"]["integrate"], list)
        self.assertTrue(any("Template upgrade pending" in w for w in payload["warnings"]), payload["warnings"])
        state = _state_of(_run_main([str(tmp_path), "--wake"]))
        self.assertEqual(state["template_upgrade"], payload["template_upgrade"])

    def test_template_upgrade_counts_come_from_the_plan(self):
        """Against a synthetic skill the summary is exact: the stub titles are the owner's
        lines to integrate, every template section is a safe addition."""
        tmp_path = self.tmp_path
        skill = make_skill(tmp_path)
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        upgrade = mod.template_upgrade(tmp_path, sanctum, skill)
        self.assertEqual(upgrade["integrate"], [f"{name}#preamble" for name in SPINE])
        self.assertGreater(upgrade["safe"], 5)
        state = mod.build_state(_args(), tmp_path, skill)
        self.assertEqual(state["template_upgrade"], upgrade)
        self.assertIn(f"Template upgrade pending: {upgrade['safe']} safe change(s), 5 to integrate. "
                      "Follow references/upgrade-sanctum.md.", state["warnings"])

    def test_template_upgrade_is_null_and_silent_when_nothing_is_pending_to_check(self):
        tmp_path = self.tmp_path
        payload = json.loads(_run_main([str(tmp_path)]))  # no sanctum: nothing to compare
        self.assertIsNone(payload["template_upgrade"])
        self.assertFalse(any("Template upgrade pending" in w for w in payload["warnings"]))

    def test_sync_package_preference_shards_and_memory_reach_the_state(self):
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "portable-sync.tar.gz").write_bytes(b"archive")
        (docs / "mac-preferences-packages.md").write_text("# packages\n")
        (docs / "mac-preferences-archive.md").write_text("# archive\n")
        (sanctum / "raw").mkdir()
        (sanctum / "raw" / "x.md").write_text("---\nstatus: raw\n---\nnotes\n")
        (sanctum / "raw" / "y.md").write_text("---\nstatus: distilled\n---\nnotes\n")
        (sanctum / "memory" / "sessions").mkdir()
        (sanctum / "memory" / "sessions" / "2026-10-01-a.md").write_text("a\n")
        (sanctum / "memory" / "sessions" / "2026-10-02-b.md").write_text("b\n")
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertEqual(payload["sync_package"], {"found": True, "path": "docs/portable-sync.tar.gz"})
        self.assertEqual(payload["voice_context"]["preference_shards"], ["docs/mac-preferences-packages.md"])
        self.assertEqual(payload["memory"], {"tended": None, "session_notes_since": 2, "undistilled_raw": 1})
        (sanctum / "memory" / ".tended").write_text("2026-10-01\n")
        self.assertEqual(json.loads(_run_main([str(tmp_path)]))["memory"],
                         {"tended": "2026-10-01", "session_notes_since": 1, "undistilled_raw": 1})

    def test_sync_package_at_the_root_or_absent(self):
        tmp_path = self.tmp_path
        self.assertEqual(json.loads(_run_main([str(tmp_path)]))["sync_package"], {"found": False, "path": None})
        (tmp_path / "portable-sync.tar.gz").write_bytes(b"archive")
        self.assertEqual(json.loads(_run_main([str(tmp_path)]))["sync_package"],
                         {"found": True, "path": "portable-sync.tar.gz"})

    # --- an old store is never scaffolded beside -----------------------------

    def test_scaffold_builds_nothing_beside_a_legacy_store(self):
        for fmt, names in (("v2", V2_SPINE), ("v1", ["index.md"])):
            with self.subTest(fmt=fmt):
                root = tmp_path = self.tmp_path / fmt
                root.mkdir()
                _full_spine(_make_legacy(tmp_path), names)
                code, out = _run_main_rc([str(tmp_path), "--wake", "--scaffold"])
                self.assertEqual(code, 0)
                self.assertTrue(out.startswith(f"MODE: UPGRADE_{fmt.upper()}\n"))
                self.assertNotIn("scaffold", _state_of(out))
                self.assertFalse((tmp_path / "_bmad" / "memory").exists())

    def test_partial_legacy_store_wakes_damaged_not_first_breath(self):
        """One v2 spine file missing and nothing at the v7 path: reported, never born beside."""
        tmp_path = self.tmp_path
        legacy = _make_legacy(tmp_path)
        _full_spine(legacy, [n for n in V2_SPINE if n != "BOND.md"])
        code, out = _run_main_rc([str(tmp_path), "--wake", "--scaffold"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("MODE: DAMAGED\n"))
        state = _state_of(out)
        self.assertEqual(state["sanctum_path"], str(legacy.resolve()))
        self.assertEqual(state["missing_spine"], ["BOND.md"])
        self.assertEqual(state["legacy_store"], {"path": str(legacy.resolve()), "sidecar_format": "damaged"})
        self.assertIs(state["first_run"], False)
        self.assertNotIn("scaffold", state)
        self.assertIn("===== MEMORY.md =====", out)
        self.assertIn("(missing: BOND.md)", out)
        self.assertNotIn("(missing: HOW-I-REMEMBER.md)", out)  # the old spine is what it lacks, not the v7 one
        self.assertNotIn("===== memory map =====", out)
        self.assertIn("never scaffold beside it", out)
        self.assertFalse((tmp_path / "_bmad" / "memory").exists())

    def test_damaged_v7_path_beside_an_unconverted_store_names_that_store(self):
        """A stub at the v7 path must not make the wake forget the old memory."""
        tmp_path = self.tmp_path
        legacy = _make_legacy(tmp_path)
        _full_spine(legacy, V2_SPINE)
        sanctum = _make_sanctum(tmp_path)
        (sanctum / "memory" / "work").mkdir(parents=True)
        (sanctum / "memory" / "work" / "current.md").write_text("# Current Work\n")
        code, out = _run_main_rc([str(tmp_path), "--wake", "--scaffold"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("MODE: DAMAGED\n"))
        state = _state_of(out)
        self.assertEqual(state["sanctum_path"], str(sanctum.resolve()))
        self.assertEqual(state["legacy_store"], {"path": str(legacy.resolve()), "sidecar_format": "v2"})
        self.assertTrue(any(str(legacy.resolve()) in w and "not converted" in w for w in state["warnings"]))
        self.assertIn("unconverted old store", out.split("===== STATE =====")[0])
        self.assertNotIn("scaffold", state)
        self.assertFalse((sanctum / "PERSONA.md").exists())

    def test_damaged_sanctum_without_an_old_store_has_no_legacy_key_set(self):
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        (sanctum / "PERSONA.md").write_text("# PERSONA.md\n")
        out = _run_main([str(tmp_path), "--wake"])
        state = _state_of(out)
        self.assertIsNone(state["legacy_store"])
        self.assertIn("references/damaged-sanctum.md", out.split("===== STATE =====")[0])
        self.assertIn("===== memory map =====", out)

    # --- scaffold failures and overrides -------------------------------------

    def test_scaffold_failure_reason_comes_from_stderr_when_there_is_no_json(self):
        """init_sanctum.py dying with only stderr: the wake says why, not 'unknown'."""
        tmp_path = self.tmp_path
        skill = tmp_path / "broken-skill"
        (skill / "scripts").mkdir(parents=True)
        (skill / "scripts" / "init_sanctum.py").write_text(
            "import sys\nsys.stderr.write('PermissionError: [Errno 13] cannot create the sanctum\\n')\nsys.exit(3)\n")
        project = tmp_path / "project"
        project.mkdir()
        result = mod.scaffold_sidecar(project, skill)
        self.assertIs(result["scaffolded"], False)
        self.assertEqual(result["message"], "PermissionError: [Errno 13] cannot create the sanctum")
        state = mod.build_state(_args(scaffold=True), project, skill)
        self.assertEqual(state["mode"], "SCAFFOLD_FAILED")
        wake = mod.render_wake(state)
        self.assertIn("Reason: PermissionError: [Errno 13] cannot create the sanctum", wake)
        self.assertNotIn("Reason: unknown", wake)
        self.assertIn("Scaffold failed: PermissionError: [Errno 13] cannot create the sanctum", state["warnings"])

    def test_scaffold_with_a_missing_template_fails_instead_of_first_breath(self):
        tmp_path = self.tmp_path
        skill = _skill_with_scripts(tmp_path)
        (skill / "assets" / "BOND-template.md").unlink()
        project = tmp_path / "project"
        project.mkdir()
        state = mod.build_state(_args(scaffold=True), project, skill)
        self.assertEqual(state["mode"], "SCAFFOLD_FAILED")
        self.assertIn("assets/BOND-template.md", state["scaffold"]["message"])
        self.assertEqual(state["scaffold"]["init_result"]["status"], "error")
        self.assertFalse((project / "_bmad").exists())
        self.assertIn("Reason: ", mod.render_wake(state))

    def test_scaffold_follows_the_sanctum_dir_override(self):
        """--scaffold --sanctum-dir builds the staging copy, never the live sanctum."""
        tmp_path = self.tmp_path
        skill = _skill_with_scripts(tmp_path)
        project = tmp_path / "project"
        project.mkdir()
        staging = tmp_path / "staging"
        state = mod.build_state(_args(scaffold=True, sanctum_dir=str(staging)), project, skill)
        self.assertEqual(state["mode"], "FIRST_BREATH")
        self.assertIs(state["scaffold"]["scaffolded"], True)
        self.assertEqual(state["sanctum_path"], str(staging))
        self.assertEqual(state["scaffold"]["sanctum_path"], str(staging))
        for name in SPINE:
            self.assertTrue((staging / name).is_file(), name)
        self.assertFalse((project / "_bmad").exists())
        self.assertIn("===== PERSONA.md =====\n# Mac — Persona", mod.render_wake(state))

    def test_missing_project_root_is_an_error_not_first_breath(self):
        tmp_path = self.tmp_path
        missing = tmp_path / "no-such-project"
        code, out = _run_main_rc([str(missing), "--wake", "--scaffold"])
        self.assertEqual(code, 2)
        self.assertEqual(out, f"MODE: ERROR\nReason: project root not found (not a directory): {missing.resolve()}\n")
        self.assertFalse(missing.exists())
        code, out = _run_main_rc([str(missing)])
        self.assertEqual(code, 2)
        payload = json.loads(out)
        self.assertEqual((payload["status"], payload["mode"]), ("error", "ERROR"))
        self.assertIn(str(missing.resolve()), payload["reason"])
        a_file = tmp_path / "a-file"
        a_file.write_text("x")
        self.assertEqual(_run_main_rc([str(a_file), "--pulse"])[0], 2)

    # --- menu and identity-file edge cases -----------------------------------

    def test_learned_row_using_an_alias_code_is_left_off_as_its_warning_says(self):
        """A learned [FL] would hijack the FL -> RS alias: it stays off the menu and the route."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        (sanctum / "CAPABILITIES.md").write_text(
            "## Learned\n\n| Code | Name | Description | Source | Added |\n|---|---|---|---|---|\n"
            "| [FL] | Fan Letters | Draft fan letters. | `capabilities/fan-letters.md` | 2026-10-01 |\n"
            "| [LX] | Liner Notes | Draft liner notes. | `capabilities/liner-notes.md` | 2026-10-01 |\n"
        )
        payload = json.loads(_run_main([str(tmp_path)]))
        self.assertNotIn("Fan Letters", payload["menu_text"])
        self.assertNotIn("[FL]", payload["menu_text"])
        self.assertIn("[LX] Liner Notes", payload["menu_text"])
        self.assertEqual(payload["routing_table"]["FL"], "RS")
        self.assertEqual(payload["routing_table"]["LX"]["type"], "learned")
        self.assertTrue(any("[FL] clashes" in w and "left off the menu" in w for w in payload["warnings"]))

    def test_non_utf8_identity_file_does_not_stop_the_wake(self):
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        (sanctum / "PERSONA.md").write_bytes(b"# Persona\n\nNOLA \xff soul.\n")
        (sanctum / "BOND.md").write_bytes(b"- **Name:** Robin \xff\n")
        (sanctum / "CAPABILITIES.md").write_bytes(
            b"## Learned\n\n| [LX] | Liner \xff Notes | Draft. | `capabilities/liner-notes.md` | 2026-10-01 |\n")
        (sanctum / "memory" / "pending.md").write_bytes(b"Raise \xff it.\n")
        code, out = _run_main_rc([str(tmp_path), "--wake"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("MODE: WAKING\n"))
        self.assertIn("NOLA \ufffd soul.", out)
        self.assertIn("Raise \ufffd it.", out)
        self.assertIn("[LX] Liner \ufffd Notes", out)
        self.assertEqual(json.loads(_run_main([str(tmp_path)]))["mode"], "WAKING")


if __name__ == "__main__":
    unittest.main()
