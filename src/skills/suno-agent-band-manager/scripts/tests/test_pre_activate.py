#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for pre-activate.py"""

import io
import json
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_resolver import install_resolver  # noqa: E402
from helpers import TempDirMixin  # noqa: E402

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
    "code,name,description,skill,action\n"
    'CS,Create Song,"Create a song package.",suno-agent-band-manager,create-song\n'
    'RS,Refine Song,"Refine a song.",suno-agent-band-manager,refine-song\n'
    'MB,Manage Bands,"Manage band profiles.",suno-band-profile-manager,manage-profiles\n'
    'FL,Feedback Loop,"Diagnose a take.",suno-feedback-elicitor,elicit-feedback\n'
    'AA,Analyze Audio,"Measure a render.",suno-feedback-elicitor,analyze-audio\n'
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


# The real skill directory — init-sanctum.py reads its assets/ templates from here.
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


def _run_main(argv):
    """Run main() with argv patched; return what it printed to stdout."""
    out = io.StringIO()
    with mock.patch.object(sys, "argv", ["pre-activate.py", *argv]), \
            redirect_stdout(out), redirect_stderr(io.StringIO()):
        mod.main()
    return out.getvalue()


class PreActivateTests(TempDirMixin, unittest.TestCase):
    def test_check_first_run_true(self):
        """First run when sanctum doesn't exist."""
        tmp_path = self.tmp_path
        assert mod.check_first_run(tmp_path) is True

    def test_check_first_run_false(self):
        """Not first run when the sanctum holds anything."""
        tmp_path = self.tmp_path
        sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
        sanctum.mkdir(parents=True)
        assert mod.check_first_run(tmp_path) is True  # an empty dir is not a sanctum
        (sanctum / "PERSONA.md").write_text("x")
        assert mod.check_first_run(tmp_path) is False

    def test_check_first_run_honors_sanctum_dir_override(self):
        """--sanctum-dir override controls first-run detection."""
        tmp_path = self.tmp_path
        staging = tmp_path / "staging"
        # Override points at a non-existent dir → first run.
        assert mod.check_first_run(tmp_path, sanctum_dir=str(staging)) is True
        staging.mkdir()
        assert mod.check_first_run(tmp_path, sanctum_dir=str(staging)) is True  # empty
        (staging / "PERSONA.md").write_text("x")
        assert mod.check_first_run(tmp_path, sanctum_dir=str(staging)) is False

    def test_detect_format_absent(self):
        """No sanctum dir → 'absent', no migration → genuine first run."""
        tmp_path = self.tmp_path
        state = mod.detect_sidecar_format(tmp_path)
        assert state["sidecar_format"] == "absent"
        assert state["needs_migration"] is False
        # first_run is the 'absent' case.
        assert mod.check_first_run(tmp_path) is True

    def test_detect_format_v1_needs_migration(self):
        """Old v1 layout at the legacy path (index.md, no v2 markers) → 'v1', needs migration."""
        tmp_path = self.tmp_path
        sanctum = _make_legacy(tmp_path)
        (sanctum / "index.md").write_text("# old content store\n")
        (sanctum / "patterns.md").write_text("# patterns\n")
        state = mod.detect_sidecar_format(tmp_path)
        assert state["sidecar_format"] == "v1"
        assert state["needs_migration"] is True
        # Critically: NOT first_run (the dir exists), so the old code path would have
        # tried to load v2 files and fallen into the damaged fallback.
        assert mod.check_first_run(tmp_path) is False

    def test_detect_format_v7_loads_normally(self):
        """The identity set present → 'v7', no migration → normal load."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        state = mod.detect_sidecar_format(tmp_path)
        assert state["sidecar_format"] == "v7"
        assert state["needs_migration"] is False
        assert state["missing_spine"] == []

    def test_detect_format_legacy_v2_needs_conversion(self):
        """The old seven-file spine at the legacy path → 'v2', converted, never woken."""
        tmp_path = self.tmp_path
        _full_spine(_make_legacy(tmp_path), V2_SPINE)
        state = mod.detect_sidecar_format(tmp_path)
        assert state["sidecar_format"] == "v2"
        assert state["needs_migration"] is True

    def test_detect_format_partial_spine_is_damaged(self):
        """A half-built v7 sanctum is damaged, never loaded as if whole."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        (sanctum / "HOW-I-REMEMBER.md").write_text("# layout\n")
        state = mod.detect_sidecar_format(tmp_path)
        assert state["sidecar_format"] == "damaged"
        assert state["needs_migration"] is False
        assert "PERSONA.md" in state["missing_spine"]

    def test_detect_format_v2_wins_even_with_legacy_index(self):
        """A full v2 spine plus a stray legacy index.md is still v2."""
        tmp_path = self.tmp_path
        sanctum = _make_legacy(tmp_path)
        _full_spine(sanctum, V2_SPINE)
        (sanctum / "index.md").write_text("# stray legacy index\n")
        state = mod.detect_sidecar_format(tmp_path)
        assert state["sidecar_format"] == "v2"

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
        assert state["sidecar_format"] == "v1"
        assert state["needs_migration"] is True

    def test_detect_format_damaged(self):
        """A non-empty v7 dir with no identity file → 'damaged'."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        (sanctum / "stray.txt").write_text("junk\n")
        state = mod.detect_sidecar_format(tmp_path)
        assert state["sidecar_format"] == "damaged"
        assert state["needs_migration"] is False

    def test_detect_format_honors_sanctum_dir_override(self):
        """--sanctum-dir override drives format detection too."""
        tmp_path = self.tmp_path
        staging = tmp_path / "staging"
        staging.mkdir()
        (staging / "index.md").write_text("# v1\n")
        state = mod.detect_sidecar_format(tmp_path, sanctum_dir=str(staging))
        assert state["sidecar_format"] == "v1"
        assert state["needs_migration"] is True

    def test_main_emits_sidecar_format_and_needs_migration(self):
        """pre-activate JSON output carries sidecar_format + needs_migration."""
        tmp_path = self.tmp_path
        bmad_dir = tmp_path / "_bmad"
        bmad_dir.mkdir()
        (bmad_dir / "module-help.csv").write_text(SAMPLE_CSV)
        sanctum = bmad_dir / "_memory" / "band-manager-sidecar"
        sanctum.mkdir(parents=True)
        (sanctum / "index.md").write_text("# old store\n")
        # A v1 store is found at the legacy path.

        payload = json.loads(_run_main([str(tmp_path)]))

        assert payload["sidecar_format"] == "v1"
        assert payload["needs_migration"] is True
        # first_run stays back-compatible: only true for the absent case.
        assert payload["first_run"] is False

    def test_scaffold_delegates_to_init_sanctum(self):
        """Scaffold builds the v7 sanctum via init-sanctum.py."""
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        result = mod.scaffold_sidecar(tmp_path, SKILL_DIR)
        assert result["scaffolded"] is True
        assert result["via"] == "init-sanctum.py"

        sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
        for name in SPINE:
            assert (sanctum / name).exists(), name
        assert (sanctum / "memory" / "work").is_dir()
        assert (sanctum / "raw").is_dir()

    def test_scaffold_idempotent(self):
        """Scaffold is a no-op when the sanctum already exists (init-sanctum guards)."""
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        mod.scaffold_sidecar(tmp_path, SKILL_DIR)
        sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
        (sanctum / "BOND.md").write_text("custom content")

        # Second scaffold: init-sanctum.py reports "exists" and creates nothing.
        result = mod.scaffold_sidecar(tmp_path, SKILL_DIR)
        assert result["init_result"].get("status") == "exists"
        assert (sanctum / "BOND.md").read_text() == "custom content"

    def test_render_menu(self):
        """Menu renders correctly from assets/menu.csv."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)

        menu = mod.render_menu(csv_path)
        # Agent and external skill entries should appear
        assert "[CS]" in menu
        assert "[RS]" in menu
        assert "[MB]" in menu
        assert "Create Song" in menu

    def test_shipped_menu_has_no_setup_row(self):
        """BMad v7 retired suno-setup: the shipped menu neither lists nor routes to it."""
        csv_path = mod.find_menu_csv(Path(__file__).resolve().parent.parent.parent)
        assert csv_path is not None
        assert "suno-setup" not in csv_path.read_text()
        assert "[CS]" in mod.render_menu(csv_path)

    def test_build_routing_table_agent_capabilities(self):
        """Agent's own capabilities route to prompt references."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)

        table = mod.build_routing_table(csv_path)
        assert table["CS"]["type"] == "prompt"
        assert table["CS"]["target"] == "references/create-song.md"
        assert table["RS"]["type"] == "prompt"
        assert table["RS"]["target"] == "references/refine-song.md"

    def test_build_routing_table_external_skills(self):
        """External skill capabilities route to skill invocation."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)

        table = mod.build_routing_table(csv_path)
        assert table["MB"]["type"] == "skill"
        assert table["MB"]["target"] == "suno-band-profile-manager"

    def test_routing_table_is_keyed_by_code_in_menu_order(self):
        """Codes only; their order is the menu's line order, so a number maps to a printed line."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)

        table = mod.build_routing_table(csv_path)
        assert not any(key.isdigit() for key in table)
        # CS is line 1; FL is skipped, AA follows MB; the alias comes last.
        assert list(table) == ["CS", "RS", "MB", "AA", "FL"]
        lines = mod.render_menu(csv_path).splitlines()
        assert lines[2].startswith("1. [CS]") and lines[5].startswith("4. [AA]")

    def test_menu_folds_feedback_loop_into_refine_song(self):
        """FL leaves Mac's menu; typing FL routes to RS (alias). AA stays."""
        tmp_path = self.tmp_path
        csv_path = _write_csv(tmp_path)
        menu = mod.render_menu(csv_path)
        assert "[FL]" not in menu
        assert "[AA]" in menu
        table = mod.build_routing_table(csv_path)
        assert table["FL"] == "RS"

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
        assert learned[0]["code"] == "LX"
        menu = mod.render_menu(csv_path, learned=learned)
        assert "[LX] Liner Notes" in menu
        table = mod.build_routing_table(csv_path, learned=learned)
        assert table["LX"]["type"] == "learned"
        assert table["LX"]["target"].endswith("capabilities/liner-notes.md")

    def test_find_menu_csv_in_skill_assets(self):
        """Finds the menu in the skill's own assets."""
        tmp_path = self.tmp_path
        skill_dir = tmp_path / "skills" / "suno-agent-band-manager"
        (skill_dir / "assets").mkdir(parents=True)
        csv_file = skill_dir / "assets" / "menu.csv"
        csv_file.write_text(SAMPLE_CSV)
        assert mod.find_menu_csv(skill_dir) == csv_file

    def test_find_menu_csv_not_found(self):
        """Returns None when the menu file is missing; a v6 module-help.csv is not read."""
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        (tmp_path / "_bmad" / "module-help.csv").write_text(SAMPLE_CSV)
        skill_dir = tmp_path / "skills" / "suno-agent-band-manager"
        skill_dir.mkdir(parents=True)
        assert mod.find_menu_csv(skill_dir) is None

    def test_sanctum_load_order_is_the_v7_identity_set(self):
        """The always-loaded waking set is the five identity files, in order; Pulse adds PULSE.md."""
        assert mod.SANCTUM_LOAD_ORDER == ["PERSONA.md", "CREED.md", "BOND.md", "HOW-I-REMEMBER.md", "CAPABILITIES.md"]
        assert mod.PULSE_LOAD_ORDER == [*mod.SANCTUM_LOAD_ORDER, "PULSE.md"]

    def test_missing_csv_still_wakes(self):
        """No assets/menu.csv: menu is null with a warning, the sanctum still wakes."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        self.enterContext(mock.patch.object(mod, "find_menu_csv", lambda *_: None))
        payload = json.loads(_run_main([str(tmp_path)]))
        assert payload["sidecar_format"] == "v7"
        assert payload["mode"] == "WAKING"
        assert payload["menu_text"] is None
        assert payload["routing_table"] is None
        assert any("menu.csv" in w for w in payload["warnings"])
        assert payload["sanctum_load_order"][0] == "PERSONA.md"

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
        assert payload["config"]["user_name"] == "Alex Smith"
        assert payload["config"]["suno_tier"] == "premier"
        assert payload["config"]["default_mode"] == "studio"
        assert payload["config"]["output_folder"] == "{project-root}/out"
        vc = payload["voice_context"]
        assert vc["matched_file"] == "docs/voice-context-alex-smith.md"
        assert vc["mac_preferences"] == "docs/mac-preferences.md"
        assert vc["sizes"]["docs/mac-preferences.md"]["tokens_est"] >= 1

    def test_config_defaults_when_missing(self):
        """No config at all: English defaults, a warning, no crash."""
        tmp_path = self.tmp_path
        payload = json.loads(_run_main([str(tmp_path)]))
        assert payload["config"]["communication_language"] == "English"
        assert payload["config"]["user_name"] is None
        assert any(w.startswith("user_name") for w in payload["warnings"])

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
        assert out.startswith("MODE: WAKING")
        positions = [out.index(f"===== {name} =====") for name in [*SPINE, "memory map", "memory/pending.md"]]
        assert positions == sorted(positions)
        assert "memory/work/ (1 files)" in out
        assert "Raise the Redux playlist." in out
        assert "pick up here" not in out  # memory is mapped, not printed
        assert "===== PULSE.md =====" not in out

    def test_pulse_prints_maintenance_set(self):
        """--pulse prints the identity files, then PULSE.md, then the map."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        (sanctum / "PULSE.md").write_text("# PULSE.md\n")
        out = _run_main([str(tmp_path), "--pulse"])
        assert out.startswith("MODE: PULSE")
        names = [*SPINE, "PULSE.md", "memory map"]
        positions = [out.index(f"===== {n} =====") for n in names]
        assert positions == sorted(positions)

    def test_wake_on_a_legacy_v2_store_routes_to_conversion(self):
        """A v2 store wakes as itself (old spine printed) and is told to convert."""
        tmp_path = self.tmp_path
        legacy = _make_legacy(tmp_path)
        _full_spine(legacy, V2_SPINE)
        (legacy / "BOND.md").write_text("- **Name:** Robin\n")
        out = _run_main([str(tmp_path), "--wake"])
        assert out.startswith("MODE: UPGRADE_V2")
        assert "references/upgrade-v2.md" in out
        assert "===== MEMORY.md =====" in out and "===== INDEX.md =====" in out
        assert "===== memory map =====" not in out
        assert '"user_name":"Robin"' in out
        assert not (tmp_path / "_bmad" / "memory").exists()

    def test_pulse_without_sanctum_is_skipped(self):
        tmp_path = self.tmp_path
        out = _run_main([str(tmp_path), "--pulse"])
        assert out.startswith("MODE: PULSE_SKIPPED")

    def test_wake_damaged_prints_present_files(self):
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        (sanctum / "PERSONA.md").write_text("# PERSONA.md\n")
        out = _run_main([str(tmp_path), "--wake"])
        assert out.startswith("MODE: DAMAGED")
        assert "(missing: CREED.md)" in out

    def test_wake_scaffold_is_first_breath_and_prints_newborn(self):
        """--wake --scaffold on an absent sanctum: born, still First Breath, printed."""
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        out = _run_main([str(tmp_path), "--wake", "--scaffold"])
        assert out.startswith("MODE: FIRST_BREATH")
        assert "references/init.md" in out
        assert "===== HOW-I-REMEMBER.md =====" in out
        assert "===== memory map =====" in out
        assert "(missing:" not in out

    def test_wake_first_breath_without_scaffold(self):
        tmp_path = self.tmp_path
        out = _run_main([str(tmp_path), "--wake"])
        assert out.startswith("MODE: FIRST_BREATH")
        assert "--scaffold" in out
        assert not (tmp_path / "_bmad" / "memory").exists()

    def test_main_emits_menu_text_key(self):
        """The pre-activate JSON output uses the `menu_text` key (not `menu`)."""
        tmp_path = self.tmp_path
        bmad_dir = tmp_path / "_bmad"
        bmad_dir.mkdir()
        (bmad_dir / "module-help.csv").write_text(SAMPLE_CSV)

        payload = json.loads(_run_main([str(tmp_path)]))

        assert "menu_text" in payload
        assert "menu" not in payload
        assert "[CS]" in payload["menu_text"]
        # The load order is surfaced as the v7 identity set.
        assert payload["sanctum_load_order"] == mod.SANCTUM_LOAD_ORDER == SPINE

    def test_unfinished_first_breath_resumes(self):
        """A v7 sanctum without memory/.born is a First Breath cut short."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        (sanctum / "memory" / ".born").unlink()
        out = _run_main([str(tmp_path), "--wake"])
        assert out.startswith("MODE: FIRST_BREATH")
        assert "cut short" in out and "===== PERSONA.md =====" in out
        assert '"resume":true' in out

    def test_wake_prints_the_menu_once_beside_a_compact_state(self):
        """The menu is its own block; the state JSON is one compact line without it."""
        tmp_path = self.tmp_path
        sanctum = _make_sanctum(tmp_path)
        _full_spine(sanctum)
        out = _run_main([str(tmp_path), "--wake"])
        assert out.startswith("MODE: WAKING")
        state = json.loads(out.split("===== STATE =====\n", 1)[1].split("\n", 1)[0])
        assert "menu_text" not in state
        assert state["routing_table"]["CS"]["type"] == "prompt" and state["routing_table"]["FL"] == "RS"
        assert "===== MENU =====\nWhat would you like to do today?" in out
        assert out.count("[CS] Create Song") == 1

    def test_scaffold_failure_is_its_own_mode_and_exits_nonzero(self):
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        self.enterContext(mock.patch.object(mod, "scaffold_sidecar", lambda *a, **k: {"scaffolded": False, "error": True, "message": "disk full"}))
        buf = io.StringIO()
        with mock.patch.object(sys, "argv", ["pre-activate.py", str(tmp_path), "--wake", "--scaffold"]), \
                redirect_stdout(buf), redirect_stderr(io.StringIO()):
            assert mod.main() == 1
        out = buf.getvalue()
        assert out.startswith("MODE: SCAFFOLD_FAILED") and "disk full" in out

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
        assert any("[CS] clashes" in w for w in payload["warnings"])
        assert any("not readable" in w for w in payload["warnings"])

    def test_customization_arrays_reach_the_state(self):
        tmp_path = self.tmp_path
        scripts = tmp_path / "_bmad" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "resolve_customization.py").write_text(
            "import json\nprint(json.dumps({'agent': {'persistent_facts': ['file:docs/house-style.md'],"
            " 'activation_steps_prepend': ['say hi'], 'activation_steps_append': []}}))\n"
        )
        payload = json.loads(_run_main([str(tmp_path)]))
        assert payload["customization"]["persistent_facts"] == ["file:docs/house-style.md"]
        assert payload["customization"]["activation_steps_prepend"] == ["say hi"]

    def test_no_bmad_means_empty_customization_with_a_reason(self):
        tmp_path = self.tmp_path
        payload = json.loads(_run_main([str(tmp_path)]))
        assert payload["customization"] == {"activation_steps_prepend": [], "activation_steps_append": [], "persistent_facts": []}
        assert any("resolve_customization" in w for w in payload["warnings"])


if __name__ == "__main__":
    unittest.main()
