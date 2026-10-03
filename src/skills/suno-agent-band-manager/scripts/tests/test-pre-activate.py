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
    'Suno Band Manager,suno-setup,Setup Suno Module,SU,"Install or update config.",configure,,anytime,,,false,,\n'
    'Suno Band Manager,suno-agent-band-manager,Create Song,CS,"Create a song package.",create-song,,anytime,,,false,,song package\n'
    'Suno Band Manager,suno-agent-band-manager,Refine Song,RS,"Refine a song.",refine-song,,anytime,,,false,,\n'
    'Suno Band Manager,suno-band-profile-manager,Manage Bands,MB,"Manage band profiles.",manage-profiles,,anytime,,,false,,\n'
    'Suno Band Manager,suno-feedback-elicitor,Feedback Loop,FL,"Diagnose a take.",elicit-feedback,,anytime,,,false,,\n'
    'Suno Band Manager,suno-feedback-elicitor,Analyze Audio,AA,"Measure a render.",analyze-audio,,anytime,,,false,,\n'
)

SPINE = [
    "access-boundaries.md",
    "INDEX.md",
    "MEMORY.md",
    "CREED.md",
    "PERSONA.md",
    "BOND.md",
    "CAPABILITIES.md",
]


def _full_spine(sanctum):
    for name in SPINE:
        (sanctum / name).write_text(f"# {name}\n")


# The real skill directory — init-sanctum.py reads its assets/ templates from here.
SKILL_DIR = Path(__file__).parent.parent.parent


def test_check_first_run_true(tmp_path):
    """First run when sanctum doesn't exist."""
    assert mod.check_first_run(tmp_path) is True


def test_check_first_run_false(tmp_path):
    """Not first run when sanctum exists."""
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    assert mod.check_first_run(tmp_path) is False


def test_check_first_run_honors_sanctum_dir_override(tmp_path):
    """--sanctum-dir override controls first-run detection."""
    staging = tmp_path / "staging"
    # Override points at a non-existent dir → first run.
    assert mod.check_first_run(tmp_path, sanctum_dir=str(staging)) is True
    staging.mkdir()
    # An empty existing dir is NOT first-run (it's "damaged"), but check_first_run
    # is the "absent" question only → False once the dir exists.
    assert mod.check_first_run(tmp_path, sanctum_dir=str(staging)) is False


# --- three-way (four-state) sidecar-format detection ---


def _make_sanctum(tmp_path):
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
    """Old v1 layout (index.md, no v2 markers) → 'v1', needs migration."""
    sanctum = _make_sanctum(tmp_path)
    (sanctum / "index.md").write_text("# old content store\n")
    (sanctum / "patterns.md").write_text("# patterns\n")
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "v1"
    assert state["needs_migration"] is True
    # Critically: NOT first_run (the dir exists), so the old code path would have
    # tried to load v2 files and fallen into the damaged fallback.
    assert mod.check_first_run(tmp_path) is False


def test_detect_format_v2_loads_normally(tmp_path):
    """The full spine present → 'v2', no migration → normal load."""
    sanctum = _make_sanctum(tmp_path)
    _full_spine(sanctum)
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "v2"
    assert state["needs_migration"] is False
    assert state["missing_spine"] == []


def test_detect_format_partial_spine_is_damaged(tmp_path):
    """A half-built v2 (INDEX present, the rest missing) is damaged, not v1 or v2."""
    sanctum = _make_sanctum(tmp_path)
    (sanctum / "INDEX.md").write_text("# thin map\n")
    state = mod.detect_sidecar_format(tmp_path)
    # Never force-migrated over, and never loaded as if whole.
    assert state["sidecar_format"] == "damaged"
    assert state["needs_migration"] is False
    assert "MEMORY.md" in state["missing_spine"]


def test_detect_format_v2_wins_even_with_legacy_index(tmp_path):
    """A full spine plus a stray legacy index.md is still v2."""
    sanctum = _make_sanctum(tmp_path)
    _full_spine(sanctum)
    (sanctum / "index.md").write_text("# stray legacy index\n")
    state = mod.detect_sidecar_format(tmp_path)
    assert state["sidecar_format"] == "v2"
    assert state["needs_migration"] is False


def test_detect_format_v1_on_case_insensitive_filesystem(tmp_path, monkeypatch):
    """On APFS/NTFS, is_file('INDEX.md') is true for a v1 index.md. Detection must
    compare real directory entries, so the store is still v1."""
    sanctum = _make_sanctum(tmp_path)
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
    """Dir exists but neither index.md nor MEMORY.md → 'damaged' (re-scaffold)."""
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

    monkeypatch.setattr(sys, "argv", ["pre-activate.py", str(tmp_path)])
    mod.main()
    payload = json.loads(capsys.readouterr().out)

    assert payload["sidecar_format"] == "v1"
    assert payload["needs_migration"] is True
    # first_run stays back-compatible: only true for the absent case.
    assert payload["first_run"] is False


def test_scaffold_delegates_to_init_sanctum(tmp_path):
    """Scaffold builds the v2 sanctum via init-sanctum.py (not the old stubs)."""
    (tmp_path / "_bmad").mkdir()
    result = mod.scaffold_sidecar(tmp_path, SKILL_DIR)
    assert result["scaffolded"] is True
    assert result["via"] == "init-sanctum.py"

    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    # v2 sanctum skeleton files (from assets/ templates), not the old 3 stubs.
    assert (sanctum / "INDEX.md").exists()
    assert (sanctum / "MEMORY.md").exists()
    assert (sanctum / "CREED.md").exists()
    assert (sanctum / "PERSONA.md").exists()
    assert (sanctum / "sessions").is_dir()


def test_scaffold_idempotent(tmp_path):
    """Scaffold is a no-op when the sanctum already exists (init-sanctum guards)."""
    (tmp_path / "_bmad").mkdir()
    mod.scaffold_sidecar(tmp_path, SKILL_DIR)
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    (sanctum / "MEMORY.md").write_text("custom content")

    # Second scaffold: init-sanctum.py reports "exists" and creates nothing.
    result = mod.scaffold_sidecar(tmp_path, SKILL_DIR)
    assert result["init_result"].get("status") == "exists"
    assert (sanctum / "MEMORY.md").read_text() == "custom content"


def _write_csv(tmp_path, content=SAMPLE_CSV):
    """Helper to write a test CSV file."""
    csv_path = tmp_path / "module-help.csv"
    csv_path.write_text(content)
    return csv_path


def test_render_menu(tmp_path):
    """Menu renders correctly from module-help.csv."""
    csv_path = _write_csv(tmp_path)

    menu = mod.render_menu(csv_path)
    # Setup skill entry should be excluded
    assert "Setup" not in menu
    # Agent and external skill entries should appear
    assert "[CS]" in menu
    assert "[RS]" in menu
    assert "[MB]" in menu
    assert "Create Song" in menu


def test_render_menu_excludes_setup(tmp_path):
    """Menu does not include the setup skill entry."""
    csv_path = _write_csv(tmp_path)
    menu = mod.render_menu(csv_path)
    assert "[SU]" not in menu


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
    # First non-setup entry is CS at position 1; FL is skipped, AA follows MB.
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


def test_find_module_csv_installed(tmp_path):
    """Finds CSV at installed location."""
    bmad_dir = tmp_path / "_bmad"
    bmad_dir.mkdir()
    csv_file = bmad_dir / "module-help.csv"
    csv_file.write_text(SAMPLE_CSV)

    skill_dir = tmp_path / "skills" / "suno-agent-band-manager"
    skill_dir.mkdir(parents=True)

    result = mod.find_module_csv(tmp_path, skill_dir)
    assert result == csv_file


def test_find_module_csv_setup_assets(tmp_path):
    """Falls back to setup skill assets when not installed."""
    skills_dir = tmp_path / "skills"
    setup_assets = skills_dir / "suno-setup" / "assets"
    setup_assets.mkdir(parents=True)
    csv_file = setup_assets / "module-help.csv"
    csv_file.write_text(SAMPLE_CSV)

    skill_dir = skills_dir / "suno-agent-band-manager"
    skill_dir.mkdir(parents=True)

    result = mod.find_module_csv(tmp_path, skill_dir)
    assert result == csv_file


def test_find_module_csv_not_found(tmp_path):
    """Returns None when CSV is not found."""
    skill_dir = tmp_path / "skills" / "suno-agent-band-manager"
    skill_dir.mkdir(parents=True)

    result = mod.find_module_csv(tmp_path, skill_dir)
    assert result is None


def test_sanctum_load_order_is_the_canonical_seven(tmp_path):
    """The always-loaded waking set is exactly the canonical 7 files, in order."""
    assert mod.SANCTUM_LOAD_ORDER == [
        "access-boundaries.md",
        "INDEX.md",
        "MEMORY.md",
        "CREED.md",
        "PERSONA.md",
        "BOND.md",
        "CAPABILITIES.md",
    ]
    # access-boundaries.md must load FIRST (Dominion contract before any file op).
    assert mod.SANCTUM_LOAD_ORDER[0] == "access-boundaries.md"


def _run_main(monkeypatch, capsys, argv):
    monkeypatch.setattr(sys, "argv", ["pre-activate.py", *argv])
    mod.main()
    return capsys.readouterr().out


def test_missing_csv_still_wakes(tmp_path, monkeypatch, capsys):
    """No module-help.csv: menu is null with a warning, the sanctum still wakes."""
    sanctum = _make_sanctum(tmp_path)
    _full_spine(sanctum)
    monkeypatch.setattr(mod, "find_module_csv", lambda *_: None)
    payload = json.loads(_run_main(monkeypatch, capsys, [str(tmp_path)]))
    assert payload["sidecar_format"] == "v2"
    assert payload["mode"] == "WAKING"
    assert payload["menu_text"] is None
    assert payload["routing_table"] is None
    assert any("module-help.csv" in w for w in payload["warnings"])
    assert payload["sanctum_load_order"][0] == "access-boundaries.md"


def test_config_resolved_without_bmad_init(tmp_path, monkeypatch, capsys):
    """pre-activate resolves user_name and the suno section itself; the voice
    file matches with no --user-name."""
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "module-help.csv").write_text(SAMPLE_CSV)
    (bmad / "config.user.yaml").write_text("user_name: Alex Smith\ncommunication_language: English\n")
    (bmad / "config.yaml").write_text(
        "document_output_language: English\noutput_folder: '{project-root}/out'\n"
        "suno:\n  name: Suno Band Manager\n  description: long text\n    continued here\n"
        "  suno_tier: premier\n  default_mode: studio\n"
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "voice-context-alex-smith.md").write_text("# voice\n")
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
    """--wake prints MODE, state, then the seven files, access-boundaries first."""
    sanctum = _make_sanctum(tmp_path)
    _full_spine(sanctum)
    (sanctum / "PULSE.md").write_text("# PULSE.md\n")
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--wake"])
    assert out.startswith("MODE: WAKING")
    positions = [out.index(f"===== {name} =====") for name in SPINE]
    assert positions == sorted(positions)
    assert "===== PULSE.md =====" not in out


def test_pulse_prints_maintenance_set(tmp_path, monkeypatch, capsys):
    """--pulse prints access-boundaries, CREED, PERSONA, PULSE — in that order."""
    sanctum = _make_sanctum(tmp_path)
    _full_spine(sanctum)
    (sanctum / "PULSE.md").write_text("# PULSE.md\n")
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--pulse"])
    assert out.startswith("MODE: PULSE")
    names = ["access-boundaries.md", "CREED.md", "PERSONA.md", "PULSE.md"]
    positions = [out.index(f"===== {n} =====") for n in names]
    assert positions == sorted(positions)
    assert "===== MEMORY.md =====" not in out


def test_pulse_without_sanctum_is_skipped(tmp_path, monkeypatch, capsys):
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--pulse"])
    assert out.startswith("MODE: PULSE_SKIPPED")


def test_wake_damaged_prints_present_files(tmp_path, monkeypatch, capsys):
    sanctum = _make_sanctum(tmp_path)
    (sanctum / "MEMORY.md").write_text("# MEMORY.md\n")
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--wake"])
    assert out.startswith("MODE: DAMAGED")
    assert "(missing: CREED.md)" in out


def test_wake_scaffold_is_first_breath_and_prints_newborn(tmp_path, monkeypatch, capsys):
    """--wake --scaffold on an absent sanctum: born, still First Breath, printed."""
    (tmp_path / "_bmad").mkdir()
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--wake", "--scaffold"])
    assert out.startswith("MODE: FIRST_BREATH")
    assert "references/init.md" in out
    assert "===== access-boundaries.md =====" in out
    assert "(missing:" not in out


def test_wake_first_breath_without_scaffold(tmp_path, monkeypatch, capsys):
    out = _run_main(monkeypatch, capsys, [str(tmp_path), "--wake"])
    assert out.startswith("MODE: FIRST_BREATH")
    assert "--scaffold" in out
    assert not (tmp_path / "_bmad" / "_memory").exists()


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
    # The load order is surfaced as the canonical 7.
    assert payload["sanctum_load_order"] == mod.SANCTUM_LOAD_ORDER
    assert len(payload["sanctum_load_order"]) == 7
