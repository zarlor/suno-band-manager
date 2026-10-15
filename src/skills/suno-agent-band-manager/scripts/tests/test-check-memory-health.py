#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for check-memory-health.py (v7 sanctum)."""

import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location(
    "check_memory_health",
    Path(__file__).parent.parent / "check-memory-health.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def _w(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _run(monkeypatch, capsys, *argv):
    monkeypatch.setattr(sys, "argv", ["check-memory-health.py", *argv])
    rc = mod.main()
    return rc, capsys.readouterr().out


def test_healthy_sanctum(v7_project):
    root, sanctum = v7_project
    result = mod.check_health(sanctum, root)
    assert result["maintenance_recommended"] is False
    assert result["identity"]["over_threshold"] is False
    assert result["standing_too_long"] == []
    assert result["undistilled_raw"] == []
    assert result["tending"]["tending_due"] is False


def test_no_memory_md_or_index_checks(v7_project):
    """v7 has no MEMORY.md token budget and no INDEX.md coverage check."""
    root, sanctum = v7_project
    _w(sanctum / "liner-notes.md", "an unlisted organic file is fine now")
    result = mod.check_health(sanctum, root)
    assert "index_unlisted" not in result
    assert "files" not in result
    assert result["maintenance_recommended"] is False


def test_identity_set_over_budget(v7_project):
    root, sanctum = v7_project
    _w(sanctum / "PERSONA.md", "p" * 30000)
    _w(sanctum / "CREED.md", "c" * 30000)  # ~15k tokens together
    result = mod.check_health(sanctum, root)
    assert result["identity"]["total_tokens_est"] > 12000
    assert result["identity"]["over_threshold"] is True
    assert "identity set" in result["recommendation"]


def test_missing_identity_file_reported(v7_project):
    root, sanctum = v7_project
    (sanctum / "HOW-I-REMEMBER.md").unlink()
    result = mod.check_health(sanctum, root)
    assert result["identity"]["missing"] == ["HOW-I-REMEMBER.md"]
    assert result["maintenance_recommended"] is True


def test_companion_files_owner_voice_and_preferences(v7_project):
    root, sanctum = v7_project
    _w(root / "docs" / "voice-context-sam.md", "v" * 1000)
    _w(root / "docs" / "voice-context-other.md", "o" * 100000)  # not the owner's: not measured
    _w(root / "docs" / "mac-preferences.md", "p" * 100000)  # ~25k tokens
    result = mod.check_health(sanctum, root)
    assert set(result["companions"]) == {"docs/voice-context-sam.md", "docs/mac-preferences.md"}
    assert result["companions_over_budget"] == ["docs/mac-preferences.md"]
    assert "compaction" in result["recommendation"]


def test_standing_file_longer_than_a_screen(v7_project):
    root, sanctum = v7_project
    _w(sanctum / "memory" / "work" / "parked.md", "- a parked thread\n" * 70)  # 70 lines
    _w(sanctum / "memory" / "owner" / "preferences.md", "x" * 4500 + "\n")  # few lines, many chars
    _w(sanctum / "memory" / "module" / "state.md", "- short\n" * 10)
    result = mod.check_health(sanctum, root)
    flagged = [f["file"] for f in result["standing_too_long"]]
    assert flagged == ["memory/owner/preferences.md", "memory/work/parked.md"]
    assert "appended to" in result["recommendation"]


def test_non_standing_folders_are_not_measured(v7_project):
    """chronology/, sessions/, incidents/, the generated catalog/ and the disciplines
    are never flagged for length; a new kind of folder is."""
    root, sanctum = v7_project
    for rel in (
        "memory/chronology/2026-04-01-long-milestone.md",
        "memory/sessions/2026-10-02-long-session.md",
        "memory/incidents/workshop-capture.md",
        "memory/catalog/status.md",
        "memory/disciplines/thematic-discipline.md",
    ):
        _w(sanctum / rel, "line\n" * 200)
    _w(sanctum / "raw" / "2026-05-27-session-log.md", "---\nstatus: distilled\n---\n" + "x" * 50000)
    result = mod.check_health(sanctum, root)
    assert result["standing_too_long"] == []
    _w(sanctum / "memory" / "gear" / "studio.md", "line\n" * 61)
    _w(sanctum / "memory" / "pending.md", "p" * 4001)
    flagged = [f["file"] for f in mod.check_health(sanctum, root)["standing_too_long"]]
    assert flagged == ["memory/gear/studio.md", "memory/pending.md"]


def test_undistilled_raw(v7_project):
    root, sanctum = v7_project
    _w(sanctum / "raw" / "2026-10-02-owner-poems.md", "---\nstatus: raw\ndistilled_to: []\n---\nwords\n")
    _w(sanctum / "raw" / "2026-09-01-session-log.md", "---\nstatus: distilled\n---\nold\n")
    result = mod.check_health(sanctum, root)
    assert result["undistilled_raw"] == ["2026-10-02-owner-poems.md"]
    assert result["maintenance_recommended"] is True


def test_tending_due_after_three_notes(v7_project):
    root, sanctum = v7_project
    sessions = sanctum / "memory" / "sessions"
    _w(sessions / "2026-09-20-before.md", "old")  # before the stamp: not counted
    for day in ("2026-10-02", "2026-10-05"):
        _w(sessions / f"{day}-note.md", "n")
    assert mod.check_health(sanctum, root)["tending"]["tending_due"] is False
    _w(sessions / "2026-10-09-note.md", "n")
    result = mod.check_health(sanctum, root)
    assert result["tending"]["session_notes_since"] == 3
    assert result["tending"]["tending_due"] is True
    assert "tend memory" in result["recommendation"]


def test_never_tended_is_due(v7_project):
    root, sanctum = v7_project
    (sanctum / "memory" / ".tended").unlink()
    result = mod.check_health(sanctum, root)
    assert result["tending"]["tended"] is None
    assert result["tending"]["tending_due"] is True


def test_cli_project_root_json(v7_project, monkeypatch, capsys):
    root, sanctum = v7_project
    rc, out = _run(monkeypatch, capsys, str(root), "--format", "json")
    assert rc == 0
    result = json.loads(out)
    assert result["sidecar_format"] == "v7"
    assert Path(result["sanctum_path"]) == sanctum


def test_cli_text_format(v7_project, monkeypatch, capsys):
    root, _ = v7_project
    rc, out = _run(monkeypatch, capsys, str(root), "--format", "text")
    assert rc == 0
    assert "Identity set:" in out and "Tended: 2026-10-01" in out


def test_cli_accepts_sanctum_path_positionally(v7_project, monkeypatch, capsys):
    root, sanctum = v7_project
    _w(root / "docs" / "mac-preferences.md", "prefs")
    rc, out = _run(monkeypatch, capsys, str(sanctum))
    assert rc == 0
    assert "docs/mac-preferences.md" in json.loads(out)["companions"]


def test_cli_sanctum_dir_override(v7_project, monkeypatch, capsys, tmp_path_factory):
    root, sanctum = v7_project
    staging = tmp_path_factory.mktemp("staging")
    for name in mod._seed.IDENTITY_FILES:
        _w(staging / name, "x")
    _w(staging / "raw" / "2026-10-10-x.md", "---\nstatus: raw\n---\n")
    rc, out = _run(monkeypatch, capsys, str(root), "--sanctum-dir", str(staging))
    assert rc == 0
    assert json.loads(out)["undistilled_raw"] == ["2026-10-10-x.md"]


def test_cli_refuses_legacy_v2_store(tmp_path, monkeypatch, capsys):
    legacy = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    for name in mod._seed.V2_SPINE:
        _w(legacy / name, "x")
    rc, out = _run(monkeypatch, capsys, str(tmp_path))
    assert rc == 1
    result = json.loads(out)
    assert result["sidecar_format"] == "v2"
    assert "migrate-sanctum-to-v7.py" in result["message"]


def test_cli_absent_sanctum(tmp_path, monkeypatch, capsys):
    rc, out = _run(monkeypatch, capsys, str(tmp_path))
    assert rc == 1
    assert json.loads(out)["sidecar_format"] == "absent"
