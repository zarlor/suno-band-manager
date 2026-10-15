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
    "module,skill,display-name,menu-code,description,action,args,phase,preceded-by,followed-by,required,output-location,outputs\n"
    'Suno Band Manager,suno-agent-band-manager,Create Song,CS,"Create a song package.",create-song,,anytime,,,false,,song package\n'
    'Suno Band Manager,suno-agent-band-manager,Refine Song,RS,"Refine a song.",refine-song,,anytime,,,false,,\n'
    'Suno Band Manager,suno-band-profile-manager,Manage Bands,MB,"Manage band profiles.",manage-profiles,,anytime,,,false,,\n'
    'Suno Band Manager,suno-feedback-elicitor,Feedback Loop,FL,"Diagnose a take.",elicit-feedback,,anytime,,,false,,\n'
    'Suno Band Manager,suno-feedback-elicitor,Analyze Audio,AA,"Measure a render.",analyze-audio,,anytime,,,false,,\n'
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


# The real skill directory — init-sanctum.py reads its assets/ templates from here.
SKILL_DIR = Path(__file__).parent.parent.parent


def test_check_first_run_true(tmp_path):
    """First run when sanctum doesn't exist."""
    assert mod.check_first_run(tmp_path) is True


def test_check_first_run_false(tmp_path):
    """Not first run when the sanctum holds anything."""
    sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
    sanctum.mkdir(parents=True)
    assert mod.check_first_run(tmp_path) is True  # an empty dir is not a sanctum
    (sanctum / "PERSONA.md").write_text("x")
    assert mod.check_first_run(tmp_path) is False


def test_check_first_run_honors_sanctum_dir_override(tmp_path):
    """--sanctum-dir override controls first-run detection."""
    staging = tmp_path / "staging"
    # Override points at a non-existent dir → first run.
    assert mod.check_first_run(tmp_path, sanctum_dir=str(staging)) is True
    staging.mkdir()
    assert mod.check_first_run(tmp_path, sanctum_dir=str(staging)) is True  # empty
    (staging / "PERSONA.md").write_text("x")
    assert mod.check_first_run(tmp_path, sanctum_dir=str(staging)) is False


# --- three-way (four-state) sidecar-format detection ---


def _make_sanctum(tmp_path):
    sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
    sanctum.mkdir(parents=True)
    return sanctum


def _make_legacy(tmp_path):
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    return sanctum


def test_detect_format_absent(tmp_path):
    """No sanctum dir → 'absent', no migration → genuine first run."""
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "absent"
    assert state["needs_migration"] is False
    # first_run is the 'absent' case.
    assert mod.check_first_run(tmp_path) is True


def test_detect_format_v1_needs_migration(tmp_path):
    """Old v1 layout at the legacy path (index.md, no v2 markers) → 'v1', needs migration."""
    sanctum = _make_legacy(tmp_path)
    (sanctum / "index.md").write_text("# old content store\n")
    (sanctum / "patterns.md").write_text("# patterns\n")
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "v1"
    assert state["needs_migration"] is True
    # Critically: NOT first_run (the dir exists), so the old code path would have
    # tried to load v2 files and fallen into the damaged fallback.
    assert mod.check_first_run(tmp_path) is False


def test_detect_format_v7_loads_normally(tmp_path):
    """The identity set present → 'v7', no migration → normal load."""
    sanctum = _make_sanctum(tmp_path)
    _full_spine(sanctum)
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "v7"
    assert state["needs_migration"] is False
    assert state["missing_spine"] == []


def test_detect_format_legacy_v2_needs_conversion(tmp_path):
    """The old seven-file spine at the legacy path → 'v2', converted, never woken."""
    _full_spine(_make_legacy(tmp_path), V2_SPINE)
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "v2"
    assert state["needs_migration"] is True


def test_detect_format_partial_spine_is_damaged(tmp_path):
    """A half-built v7 sanctum is damaged, never loaded as if whole."""
    sanctum = _make_sanctum(tmp_path)
    (sanctum / "HOW-I-REMEMBER.md").write_text("# layout\n")
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "damaged"
    assert state["needs_migration"] is False
    assert "PERSONA.md" in state["missing_spine"]


def test_detect_format_v2_wins_even_with_legacy_index(tmp_path):
    """A full v2 spine plus a stray legacy index.md is still v2."""
    sanctum = _make_legacy(tmp_path)
    _full_spine(sanctum, V2_SPINE)
    (sanctum / "index.md").write_text("# stray legacy index\n")
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "v2"


def test_detect_format_v1_on_case_insensitive_filesystem(tmp_path, monkeypatch):
    """On APFS/NTFS, is_file('INDEX.md') is true for a v1 index.md. Detection must
    compare real directory entries, so the store is still v1."""
    sanctum = _make_legacy(tmp_path)
    (sanctum / "index.md").write_text("# v1 store\n")
    real_is_file = Path.is_file

    def insensitive_is_file(self):
        if self.parent == sanctum:
            return any(p.name.lower() == self.name.lower() for p in sanctum.iterdir())
        return real_is_file(self)

    monkeypatch.setattr(Path, "is_file", insensitive_is_file)
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "v1"
    assert state["needs_migration"] is True


def test_detect_format_damaged(tmp_path):
    """A non-empty v7 dir with no identity file → 'damaged'."""
    sanctum = _make_sanctum(tmp_path)
    (sanctum / "stray.txt").write_text("junk\n")
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "damaged"
    assert state["needs_migration"] is False


def test_detect_format_honors_sanctum_dir_override(tmp_path):
    """--sanctum-dir override drives format detection too."""
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "index.md").write_text("# v1\n")
    state = mod.detect_sidecar_format(tmp_path, sanctum_dir=str(staging))
    assert state["sidecar_format"] == "v1"
    assert state["needs_migration"] is True


def test_main_emits_sidecar_format_and_needs_migration(tmp_path, monkeypatch, capsys):
    """pre-activate JSON output carries sidecar_format + needs_migration."""
    bmad_dir = tmp_path / "_bmad"
    bmad_dir.mkdir()
    (bmad_dir / "module-help.csv").write_text(SAMPLE_CSV)
    sanctum = bmad_dir / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    (sanctum / "index.md").write_text("# old store\n")
    # A v1 store is found at the legacy path.

    monkeypatch.setattr(sys, "argv", ["pre-activate.py", str(tmp_path)])
    mod.main()
    payload = json.loads(capsys.readouterr().out)

    assert payload["sidecar_format"] == "v1"
    assert payload["needs_migration"] is True
    # first_run stays back-compatible: only true for the absent case.
    assert payload["first_run"] is False


def test_scaffold_delegates_to_init_sanctum(tmp_path):
    """Scaffold builds the v7 sanctum via init-sanctum.py."""
    (tmp_path / "_bmad").mkdir()
    result = mod.scaffold_sidecar(tmp_path, SKILL_DIR)
    assert result["scaffolded"] is True
    assert result["via"] == "init-sanctum.py"

    sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
    for name in SPINE:
        assert (sanctum / name).exists(), name
    assert (sanctum / "memory" / "work").is_dir()
    assert (sanctum / "raw").is_dir()


def test_scaffold_idempotent(tmp_path):
    """Scaffold is a no-op when the sanctum already exists (init-sanctum guards)."""
    (tmp_path / "_bmad").mkdir()
    mod.scaffold_sidecar(tmp_path, SKILL_DIR)
    sanctum = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager"
    (sanctum / "BOND.md").write_text("custom content")

    # Second scaffold: init-sanctum.py reports "exists" and creates nothing.
    result = mod.scaffold_sidecar(tmp_path, SKILL_DIR)
    assert result["init_result"].get("status") == "exists"
    assert (sanctum / "BOND.md").read_text() == "custom content"


def _write_csv(tmp_path, content=SAMPLE_CSV):
    """Helper to write a test CSV file."""
    csv_path = tmp_path / "menu.csv"
    csv_path.write_text(content)
    return csv_path


def test_render_menu(tmp_path):
    """Menu renders correctly from assets/menu.csv."""
    csv_path = _write_csv(tmp_path)

    menu = mod.render_menu(csv_path)
    # Agent and external skill entries should appear
    assert "[CS]" in menu
    assert "[RS]" in menu
    assert "[MB]" in menu
    assert "Create Song" in menu


def test_shipped_menu_has_no_setup_row():
    """BMad v7 retired suno-setup: the shipped menu neither lists nor routes to it."""
    csv_path = mod.find_menu_csv(Path(__file__).resolve().parent.parent.parent)
    assert csv_path is not None
    assert "suno-setup" not in csv_path.read_text()
    assert "[CS]" in mod.render_menu(csv_path, [mod.MODULE_CODE])


def test_build_routing_table_agent_capabilities(tmp_path):
    """Agent's own capabilities route to prompt references."""
    csv_path = _write_csv(tmp_path)

    table = mod.build_routing_table(csv_path)
    assert table["CS"]["type"] == "prompt"
    assert table["CS"]["target"] == "references/create-song.md"
    assert table["RS"]["type"] == "prompt"
    assert table["RS"]["target"] == "references/refine-song.md"


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
    # CS is at position 1; FL is skipped, AA follows MB.
    assert table["1"]["name"] == "create-song"
    assert table["2"]["name"] == "refine-song"
    assert table["3"]["name"] == "manage-profiles"
    assert table["4"]["name"] == "analyze-audio"
    assert "5" not in table


def test_menu_folds_feedback_loop_into_refine_song(tmp_path):
    """FL leaves Mac's menu; typing FL routes to RS (alias). AA stays."""
    csv_path = _write_csv(tmp_path)
    menu = mod.render_menu(csv_path)
    assert "[FL]" not in menu
    assert "[AA]" in menu
    table = mod.build_routing_table(csv_path)
    assert table["FL"]["target"] == "references/refine-song.md"
    assert table["FL"]["alias_of"] == "RS"


def test_learned_capabilities_reach_the_menu(tmp_path):
    """Rows in the sanctum CAPABILITIES.md Learned table appear on the menu."""
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


def test_find_menu_csv_in_skill_assets(tmp_path):
    """Finds the menu in the skill's own assets."""
    skill_dir = tmp_path / "skills" / "suno-agent-band-manager"
    (skill_dir / "assets").mkdir(parents=True)
    csv_file = skill_dir / "assets" / "menu.csv"
    csv_file.write_text(SAMPLE_CSV)
    assert mod.find_menu_csv(skill_dir) == csv_file


def test_find_menu_csv_not_found(tmp_path):
    """Returns None when the menu file is missing; a v6 module-help.csv is not read."""
    (tmp_path / "_bmad").mkdir()
    (tmp_path / "_bmad" / "module-help.csv").write_text(SAMPLE_CSV)
    skill_dir = tmp_path / "skills" / "suno-agent-band-manager"
    skill_dir.mkdir(parents=True)
    assert mod.find_menu_csv(skill_dir) is None


def test_sanctum_load_order_is_the_v7_identity_set(tmp_path):
    """The always-loaded waking set is the five identity files, in order; Pulse adds PULSE.md."""
    assert mod.SANCTUM_LOAD_ORDER == ["PERSONA.md", "CREED.md", "BOND.md", "HOW-I-REMEMBER.md", "CAPABILITIES.md"]
    assert mod.PULSE_LOAD_ORDER == [*mod.SANCTUM_LOAD_ORDER, "PULSE.md"]


def _run_main(monkeypatch, capsys, argv):
    monkeypatch.setattr(sys, "argv", ["pre-activate.py", *argv])
    mod.main()
    return capsys.readouterr().out


def test_missing_csv_still_wakes(tmp_path, monkeypatch, capsys):
    """No assets/menu.csv: menu is null with a warning, the sanctum still wakes."""
    sanctum = _make_sanctum(tmp_path)
    _full_spine(sanctum)
    monkeypatch.setattr(mod, "find_menu_csv", lambda *_: None)
    payload = json.loads(_run_main(monkeypatch, capsys, [str(tmp_path)]))
    assert payload["sidecar_format"] == "v7"
    assert payload["mode"] == "WAKING"
    assert payload["menu_text"] is None
    assert payload["routing_table"] is None
    assert any("menu.csv" in w for w in payload["warnings"])
    assert payload["sanctum_load_order"][0] == "PERSONA.md"


def test_config_resolved_from_v7_config_and_bond(tmp_path, monkeypatch, capsys):
    """pre-activate resolves the suno answers from BMad v7 config and the owner
    from BOND.md; the voice file matches with no --user-name."""
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "config.toml").write_text(
        '[core]\noutput_folder = "{project-root}/out"\n'
        '[modules.suno]\nsuno_tier = "premier"\ndefault_mode = "studio"\n'
    )
    sanctum = _make_sanctum(tmp_path)
    _full_spine(sanctum)
    (sanctum / "BOND.md").write_text("# Bond\n\n- **Name:** Alex Smith\n- **Language:** English\n")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "voice-context-alex-smith.md").write_text("# voice\n")
    (docs / "voice-context-someone-else.md").write_text("# voice\n")
    (docs / "mac-preferences.md").write_text("# prefs\n")
    payload = json.loads(_run_main(monkeypatch, capsys, [str(tmp_path)]))
    assert payload["config"]["user_name"] == "Alex Smith"
    assert payload["config"]["suno_tier"] == "premier"
    assert payload["config"]["default_mode"] == "studio"
    assert payload["config"]["output_folder"] == "{project-root}/out"
    vc = payload["voice_context"]
    assert vc["matched_file"] == "docs/voice-context-alex-smith.md"
    assert vc["mac_preferences"] == "docs/mac-preferences.md"
    assert vc["sizes"]["docs/mac-preferences.md"]["tokens_est"] >= 1


def test_config_defaults_when_missing(tmp_path, monkeypatch, capsys):
    """No config at all: English defaults, a warning, no crash."""
    payload = json.loads(_run_main(monkeypatch, capsys, [str(tmp_path)]))
    assert payload["config"]["communication_language"] == "English"
    assert payload["config"]["user_name"] is None
    assert any(w.startswith("user_name") for w in payload["warnings"])


def test_wake_prints_spine_in_load_order(tmp_path, monkeypatch, capsys):
    """--wake prints MODE, state, the identity files in order, then the memory map."""
    sanctum = _make_sanctum(tmp_path)
    _full_spine(sanctum)
    (sanctum / "PULSE.md").write_text("# PULSE.md\n")
    (sanctum / "memory" / "work").mkdir(parents=True)
    (sanctum / "memory" / "work" / "current.md").write_text("pick up here")
    (sanctum / "memory" / "pending.md").write_text("Raise the Redux playlist.\n")
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--wake"])
    assert out.startswith("MODE: WAKING")
    positions = [out.index(f"===== {name} =====") for name in [*SPINE, "memory map", "memory/pending.md"]]
    assert positions == sorted(positions)
    assert "memory/work/ (1 files)" in out
    assert "Raise the Redux playlist." in out
    assert "pick up here" not in out  # memory is mapped, not printed
    assert "===== PULSE.md =====" not in out


def test_pulse_prints_maintenance_set(tmp_path, monkeypatch, capsys):
    """--pulse prints the identity files, then PULSE.md, then the map."""
    sanctum = _make_sanctum(tmp_path)
    _full_spine(sanctum)
    (sanctum / "PULSE.md").write_text("# PULSE.md\n")
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--pulse"])
    assert out.startswith("MODE: PULSE")
    names = [*SPINE, "PULSE.md", "memory map"]
    positions = [out.index(f"===== {n} =====") for n in names]
    assert positions == sorted(positions)


def test_wake_on_a_legacy_v2_store_routes_to_conversion(tmp_path, monkeypatch, capsys):
    """A v2 store wakes as itself (old spine printed) and is told to convert."""
    legacy = _make_legacy(tmp_path)
    _full_spine(legacy, V2_SPINE)
    (legacy / "BOND.md").write_text("- **Name:** Robin\n")
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--wake"])
    assert out.startswith("MODE: UPGRADE_V2")
    assert "references/upgrade-v2.md" in out
    assert "===== MEMORY.md =====" in out and "===== INDEX.md =====" in out
    assert "===== memory map =====" not in out
    assert '"user_name": "Robin"' in out
    assert not (tmp_path / "_bmad" / "memory").exists()


def test_pulse_without_sanctum_is_skipped(tmp_path, monkeypatch, capsys):
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--pulse"])
    assert out.startswith("MODE: PULSE_SKIPPED")


def test_wake_damaged_prints_present_files(tmp_path, monkeypatch, capsys):
    sanctum = _make_sanctum(tmp_path)
    (sanctum / "PERSONA.md").write_text("# PERSONA.md\n")
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--wake"])
    assert out.startswith("MODE: DAMAGED")
    assert "(missing: CREED.md)" in out


def test_wake_scaffold_is_first_breath_and_prints_newborn(tmp_path, monkeypatch, capsys):
    """--wake --scaffold on an absent sanctum: born, still First Breath, printed."""
    (tmp_path / "_bmad").mkdir()
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--wake", "--scaffold"])
    assert out.startswith("MODE: FIRST_BREATH")
    assert "references/init.md" in out
    assert "===== HOW-I-REMEMBER.md =====" in out
    assert "===== memory map =====" in out
    assert "(missing:" not in out


def test_wake_first_breath_without_scaffold(tmp_path, monkeypatch, capsys):
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--wake"])
    assert out.startswith("MODE: FIRST_BREATH")
    assert "--scaffold" in out
    assert not (tmp_path / "_bmad" / "memory").exists()


def test_main_emits_menu_text_key(tmp_path, monkeypatch, capsys):
    """The pre-activate JSON output uses the `menu_text` key (not `menu`)."""
    bmad_dir = tmp_path / "_bmad"
    bmad_dir.mkdir()
    (bmad_dir / "module-help.csv").write_text(SAMPLE_CSV)

    monkeypatch.setattr(sys, "argv", ["pre-activate.py", str(tmp_path)])
    mod.main()
    payload = json.loads(capsys.readouterr().out)

    assert "menu_text" in payload
    assert "menu" not in payload
    assert "[CS]" in payload["menu_text"]
    # The load order is surfaced as the v7 identity set.
    assert payload["sanctum_load_order"] == mod.SANCTUM_LOAD_ORDER == SPINE
