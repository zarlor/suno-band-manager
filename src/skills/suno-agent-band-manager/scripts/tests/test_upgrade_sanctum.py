#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for upgrade-sanctum.py — v7 repair and template upgrades, owner content kept."""

import json
import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))


def _load(name, filename):
    spec = spec_from_file_location(name, SCRIPTS_DIR / filename)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load("upgrade_sanctum", "upgrade-sanctum.py")
init = _load("init_sanctum", "init-sanctum.py")


def _born(tmp_path):
    """A freshly scaffolded v7 sanctum (owner Sam, from the lone voice file)."""
    (tmp_path / "_bmad").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "voice-context-sam.md").write_text("# Sam\n")
    result = init.scaffold(tmp_path, SKILL_DIR)
    assert result["status"] == "created"
    return tmp_path, Path(result["sanctum_path"])


def snapshot(sanctum):
    return {p.relative_to(sanctum).as_posix(): p.read_bytes() for p in sanctum.rglob("*") if p.is_file()}


def _cli(capsys, *argv):
    with patch.object(sys, "argv", ["upgrade-sanctum.py", *argv]), capsys():
        assert mod.main() == 0
    return capsys.readouterr().out


def _cli_rc(capsys, *argv):
    with patch.object(sys, "argv", ["upgrade-sanctum.py", *argv]), capsys():
        rc = mod.main()
    return rc, capsys.readouterr().out


class TestUpgradeSanctum(TempDirMixin, unittest.TestCase):
    def test_fresh_sanctum_needs_nothing(self):
        root, sanctum = _born(self.tmp_path)
        report = mod.plan(root, sanctum, SKILL_DIR)
        assert report["status"] == "dry-run"
        assert report["sidecar_format"] == "v7"
        assert report["changes"] == []

    def test_dry_run_writes_nothing(self):
        root, sanctum = _born(self.tmp_path)
        creed = sanctum / "CREED.md"
        creed.write_text(creed.read_text().replace("present no package", "improvise a package"))
        before = snapshot(sanctum)
        report = mod.plan(root, sanctum, SKILL_DIR)
        assert any(c["kind"] == "replace-section" for c in report["changes"])
        assert snapshot(sanctum) == before

    def test_missing_section_is_safe_add_and_applies(self):
        root, sanctum = _born(self.tmp_path)
        creed = sanctum / "CREED.md"
        text = creed.read_text()
        start = text.index("## Standing Orders")
        end = text.index("## Package Assembly Rule")
        creed.write_text(text[:start] + text[end:])
        report = mod.plan(root, sanctum, SKILL_DIR)
        adds = [c for c in report["changes"] if c["kind"] == "add-section"]
        assert adds and adds[0]["heading"] == "## Standing Orders" and adds[0]["safe"]
        result = mod.apply_changes(sanctum, report, {"safe"})
        assert result["status"] == "applied"
        new = creed.read_text()
        assert new.index("## Standing Orders") < new.index("## Package Assembly Rule")
        backup = Path(result["backup_path"])
        assert backup.parent == sanctum.parent and backup.name.startswith(".suno-agent-band-manager-upgrade-backup-")
        assert (backup / "CREED.md").is_file()
        assert mod.plan(root, sanctum, SKILL_DIR)["changes"] == []

    def test_replacement_needs_its_id(self):
        root, sanctum = _born(self.tmp_path)
        persona = sanctum / "PERSONA.md"
        persona.write_text(persona.read_text().replace("SUNO-REFERENCE.md", "v5.5 (paid)"))
        report = mod.plan(root, sanctum, SKILL_DIR)
        (change,) = [c for c in report["changes"] if c["file"] == "PERSONA.md"]
        assert change["kind"] == "replace-section" and change["safe"] is False
        mod.apply_changes(sanctum, report, {"safe"})
        assert "v5.5 (paid)" in persona.read_text()
        mod.apply_changes(sanctum, report, {change["id"]})
        assert "v5.5 (paid)" not in persona.read_text()
        assert "SUNO-REFERENCE.md" in persona.read_text()

    def test_owner_sections_are_never_proposed(self):
        root, sanctum = _born(self.tmp_path)
        persona = sanctum / "PERSONA.md"
        persona.write_text(persona.read_text() + "- **2026-10-01** — Learned to hold the bridge back.\n")
        creed = sanctum / "CREED.md"
        creed.write_text(creed.read_text().replace("## Mission\n", "## Mission\n\nFor Sam: a personal catalog.\n", 1))
        bond = sanctum / "BOND.md"
        bond.write_text(bond.read_text().replace("- **Language:** English", "- **Language:** English\n- **Tier:** Pro"))
        bond.write_text(bond.read_text() + "\n## Their Bands\n\n- Paper Lanterns\n")
        report = mod.plan(root, sanctum, SKILL_DIR)
        assert report["changes"] == []
        kept = " ".join(report["owner_sections_kept"])
        assert "PERSONA.md ## Evolution Log" in kept
        assert "CREED.md ## Mission" in kept
        assert "BOND.md ## Owner Summary" in kept
        assert "BOND.md ## Their Bands" in kept

    def test_standing_memory_is_never_proposed(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / "memory" / "work" / "current.md").write_text("# Current Work\n\nA song in progress.\n")
        (sanctum / "memory" / "owner" / "preferences.md").unlink()
        assert mod.plan(root, sanctum, SKILL_DIR)["changes"] == []

    def test_missing_identity_file_restored_with_dominion(self):
        root, sanctum = _born(self.tmp_path)
        original = (sanctum / "CREED.md").read_text()
        (sanctum / "CREED.md").unlink()
        (sanctum / "HOW-I-REMEMBER.md").unlink()
        report = mod.plan(root, sanctum, SKILL_DIR)
        assert report["sidecar_format"] == "damaged"
        assert sorted(report["missing_identity"]) == ["CREED.md", "HOW-I-REMEMBER.md"]
        assert sorted(c["file"] for c in report["changes"]) == ["CREED.md", "HOW-I-REMEMBER.md"]
        assert all(c["kind"] == "create-file" and c["safe"] for c in report["changes"])
        mod.apply_changes(sanctum, report, {"safe"})
        creed = (sanctum / "CREED.md").read_text()
        assert creed == original
        assert "{dominion}" not in creed and "### Read Access" in creed and "### Deny Zones" in creed
        assert mod.plan(root, sanctum, SKILL_DIR)["sidecar_format"] == "v7"

    def test_missing_folders_are_created(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / "capabilities").rmdir()
        (sanctum / "memory" / "chronology").rmdir()
        report = mod.plan(root, sanctum, SKILL_DIR)
        assert sorted(c["file"] for c in report["changes"]) == ["capabilities/", "memory/chronology/"]
        assert all(c["kind"] == "create-folder" and c["safe"] for c in report["changes"])
        mod.apply_changes(sanctum, report, {"safe"})
        assert (sanctum / "capabilities").is_dir() and (sanctum / "memory" / "chronology").is_dir()

    def test_missing_disciplines_are_reseeded_only_missing(self):
        root, sanctum = _born(self.tmp_path)
        original = (sanctum / "memory" / "disciplines" / "research-discipline.md").read_text()
        (sanctum / "memory" / "disciplines" / "package-assembly.md").unlink()
        (sanctum / "memory" / "incidents" / "workshop-capture.md").unlink()
        grown = sanctum / "memory" / "disciplines" / "research-discipline.md"
        report = mod.plan(root, sanctum, SKILL_DIR)
        creates = sorted(c["file"] for c in report["changes"] if c["kind"] == "create-file")
        assert creates == ["memory/disciplines/package-assembly.md", "memory/incidents/workshop-capture.md"]
        grown.write_text(original + "\n- A learning the owner taught.\n")  # after planning
        mod.apply_changes(sanctum, report, {"safe"})
        assert (sanctum / "memory" / "disciplines" / "package-assembly.md").is_file()
        assert (sanctum / "memory" / "incidents" / "workshop-capture.md").is_file()
        assert "A learning the owner taught." in grown.read_text()  # only missing files written

    def test_changed_discipline_is_a_reviewed_replacement(self):
        root, sanctum = _born(self.tmp_path)
        discipline = sanctum / "memory" / "disciplines" / "thematic-discipline.md"
        discipline.write_text(discipline.read_text() + "\n- A learning the owner taught.\n")
        report = mod.plan(root, sanctum, SKILL_DIR)
        (change,) = report["changes"]
        assert change["kind"] == "replace-file" and change["safe"] is False
        assert "A learning the owner taught." in change["diff"]
        mod.apply_changes(sanctum, report, {"safe"})
        assert "A learning" in discipline.read_text()
        result = mod.apply_changes(sanctum, report, {change["id"]})
        assert "A learning" not in discipline.read_text()
        assert (Path(result["backup_path"]) / "memory" / "disciplines" / "thematic-discipline.md").is_file()

    def test_incident_stories_are_create_only(self):
        root, sanctum = _born(self.tmp_path)
        story = sanctum / "memory" / "incidents" / "workshop-capture.md"
        story.write_text("# owner incident archive\n")
        assert mod.plan(root, sanctum, SKILL_DIR)["changes"] == []

    def test_capabilities_builtin_regenerated_learned_kept(self):
        root, sanctum = _born(self.tmp_path)
        caps = sanctum / "CAPABILITIES.md"
        text = caps.read_text()
        text = text.replace("The menu the wake prints", "The menu below")
        text = text.replace(
            "|------|------|-------------|--------|-------|\n",
            "|------|------|-------------|--------|-------|\n| [LX] | Liner Notes | x | owner | 2026-10-01 |\n",
        )
        caps.write_text(text)
        report = mod.plan(root, sanctum, SKILL_DIR)
        (change,) = report["changes"]
        assert change["kind"] == "regenerate-section" and change["heading"] == "## Built-in" and change["safe"]
        assert "CAPABILITIES.md ## Learned" in report["owner_sections_kept"]
        mod.apply_changes(sanctum, report, {"safe"})
        new = caps.read_text()
        assert "The menu the wake prints" in new
        assert "| [LX] | Liner Notes | x | owner | 2026-10-01 |" in new

    def test_old_store_is_refused(self):
        for fmt in ("v1", "v2"):
            with self.subTest(fmt=fmt):
                root = self.tmp_path / fmt
                legacy = root / "_bmad" / "_memory" / "band-manager-sidecar"
                legacy.mkdir(parents=True)
                names = ["index.md"] if fmt == "v1" else mod._seed.V2_SPINE
                for name in names:
                    (legacy / name).write_text("# old\n")
                report = mod.plan(root, legacy, SKILL_DIR)
                assert report["status"] == "not-applicable"
                assert report["sidecar_format"] == fmt
                assert "migrate-sanctum-to-v7.py" in report["message"]

    def test_partial_old_store_is_refused(self):
        store = self.tmp_path / "store"
        store.mkdir()
        (store / "MEMORY.md").write_text("# old\n")
        (store / "CREED.md").write_text("# old\n")
        report = mod.plan(self.tmp_path, store, SKILL_DIR)
        assert report["status"] == "not-applicable"
        assert "migrate-sanctum-to-v7.py" in report["message"]

    def test_absent_sanctum_is_first_breath(self):
        report = mod.plan(self.tmp_path, self.tmp_path / "nothing", SKILL_DIR)
        assert report["status"] == "not-applicable" and "First Breath" in report["message"]

    def test_cli_json_dry_run(self):
        root, _ = _born(self.tmp_path)
        payload = json.loads(_cli(self.capsys, "--project-root", str(root), "--format", "json"))
        assert payload["status"] == "dry-run"
        assert payload["changes"] == []

    def test_cli_apply_safe(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / "HOW-I-REMEMBER.md").unlink()
        out = _cli(self.capsys, "--project-root", str(root), "--apply", "safe")
        assert "Applied: HOW-I-REMEMBER.md#1" in out
        assert (sanctum / "HOW-I-REMEMBER.md").is_file()

    def test_cli_points_a_legacy_project_at_the_converter(self):
        legacy = self.tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
        legacy.mkdir(parents=True)
        for name in mod._seed.V2_SPINE:
            (legacy / name).write_text("# old\n")
        out = _cli(self.capsys, "--project-root", str(self.tmp_path))
        assert "(v2)" in out and "migrate-sanctum-to-v7.py" in out

    def test_cli_apply_unknown_id_exits_1(self):
        root, _ = _born(self.tmp_path)
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--apply", "NOPE.md#9",
                          "--format", "json")
        payload = json.loads(out)
        assert rc == 1
        assert payload["status"] == "nothing-applied" and payload["unknown_ids"] == ["NOPE.md#9"]

    def test_cli_apply_partly_unknown_ids_exits_1_but_applies_the_rest(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / "HOW-I-REMEMBER.md").unlink()
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--apply", "safe,TYPO#1")
        assert rc == 1
        assert "Applied: HOW-I-REMEMBER.md#1" in out and "Unknown ids (not applied): TYPO#1" in out
        assert (sanctum / "HOW-I-REMEMBER.md").is_file()

    def test_cli_apply_safe_with_nothing_pending_is_clean(self):
        root, _ = _born(self.tmp_path)
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--apply", "safe", "--format", "json")
        assert rc == 0 and json.loads(out)["status"] == "nothing-to-apply"

    def test_cli_apply_on_legacy_store_exits_1(self):
        legacy = self.tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
        legacy.mkdir(parents=True)
        for name in mod._seed.V2_SPINE:
            (legacy / name).write_text("# old\n")
        rc, out = _cli_rc(self.capsys, "--project-root", str(self.tmp_path), "--apply", "safe")
        assert rc == 1 and "uv run {skill-root}/scripts/migrate-sanctum-to-v7.py" in out

    def test_cli_empty_apply_exits_1(self):
        root, _ = _born(self.tmp_path)
        rc, _ = _cli_rc(self.capsys, "--project-root", str(root), "--apply", ",")
        assert rc == 1


if __name__ == "__main__":
    unittest.main()
