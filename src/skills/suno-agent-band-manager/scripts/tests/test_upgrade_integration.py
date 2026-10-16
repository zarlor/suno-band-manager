#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for upgrade-sanctum.py's three-way upgrade: the base record, safe
updates and merges, integration of the owner's lines, and --keep."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402
from test_upgrade_sanctum import SKILL_DIR, _born, _cli_rc, mod, snapshot  # noqa: E402

BASE = "memory/.template-base.json"
MA = "PERSONA.md ## Model Awareness"
THEMATIC = "memory/disciplines/thematic-discipline.md"
OWNER_LINE = "- A learning the owner taught: read the dossier before every placement."


def base_units(sanctum):
    return json.loads((sanctum / BASE).read_text())["units"]


def set_base(sanctum, key, text, status="taken"):
    data = json.loads((sanctum / BASE).read_text())
    data["units"][key] = {"text": text, "status": status, "date": "2026-01-01"}
    (sanctum / BASE).write_text(json.dumps(data))


def section(sanctum, name, heading):
    return dict(mod.split((sanctum / name).read_text()))[heading]


def replace_section(sanctum, name, heading, text):
    sections = mod.split((sanctum / name).read_text())
    (sanctum / name).write_text(mod.join([(h, text if h == heading else b) for h, b in sections]))


def by_key(report, key):
    found = [c for c in report["changes"] if c.get("key") == key]
    assert len(found) == 1, [c.get("key") for c in report["changes"]]
    return found[0]


class TestMerge3(unittest.TestCase):
    def test_edits_in_different_places_merge(self):
        base = "a\nb\nc\nd\ne\n"
        live = "a\nb\nc\nd\ne\nowner\n"
        new = "A\nb\nc\nd\ne\n"
        assert mod.merge3(base, live, new) == "A\nb\nc\nd\ne\nowner\n"

    def test_overlapping_edits_conflict(self):
        assert mod.merge3("a\nb\nc\n", "a\nB-owner\nc\n", "a\nB-template\nc\n") is None

    def test_identical_edits_merge(self):
        assert mod.merge3("a\nb\n", "a\nx\n", "a\nx\n") == "a\nx\n"

    def test_owner_lines_ignore_markdown_lead(self):
        assert mod.owner_lines("- **Why:** it matters\n> new thought\n", "**Why:** it matters\n") == ["> new thought"]


class TestThreeWayUpgrade(TempDirMixin, unittest.TestCase):
    def test_first_breath_records_the_base(self):
        _, sanctum = _born(self.tmp_path)
        units = base_units(sanctum)
        assert MA in units and THEMATIC in units and "CREED.md ## Principles" in units
        assert all(u["status"] == "taken" for u in units.values())

    def test_owner_edit_stands_while_the_template_is_unchanged(self):
        root, sanctum = _born(self.tmp_path)
        persona = sanctum / "PERSONA.md"
        persona.write_text(persona.read_text().replace("SUNO-REFERENCE.md", "SUNO-REFERENCE.md, and my own notes"))
        assert mod.plan(root, sanctum, SKILL_DIR)["changes"] == []

    def test_untouched_older_template_updates_safely(self):
        root, sanctum = _born(self.tmp_path)
        older = section(sanctum, "PERSONA.md", "## Model Awareness").replace("at the moment it matters", "when it matters")
        replace_section(sanctum, "PERSONA.md", "## Model Awareness", older)
        set_base(sanctum, MA, older)
        report = mod.plan(root, sanctum, SKILL_DIR)
        change = by_key(report, MA)
        assert change["kind"] == "update-section" and change["safe"]
        mod.apply_changes(sanctum, report, {"safe"})
        assert "at the moment it matters" in (sanctum / "PERSONA.md").read_text()
        assert mod.plan(root, sanctum, SKILL_DIR)["changes"] == []

    def test_owner_addition_and_template_change_merge(self):
        root, sanctum = _born(self.tmp_path)
        shipped = section(sanctum, "PERSONA.md", "## Model Awareness")
        older = shipped.replace("at the moment it matters", "when it matters")
        set_base(sanctum, MA, older)
        live = older.rstrip("\n") + "\n\nOwner note: the Persona slot is not the Voice slot.\n\n"
        replace_section(sanctum, "PERSONA.md", "## Model Awareness", live)
        report = mod.plan(root, sanctum, SKILL_DIR)
        change = by_key(report, MA)
        assert change["kind"] == "merge-section" and change["safe"]
        mod.apply_changes(sanctum, report, {"safe"})
        text = (sanctum / "PERSONA.md").read_text()
        assert "at the moment it matters" in text and "Owner note: the Persona slot" in text
        assert mod.plan(root, sanctum, SKILL_DIR)["changes"] == []  # merged text stands

    def test_no_base_with_owner_lines_needs_integration(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        discipline = sanctum / THEMATIC
        shipped = discipline.read_text()
        discipline.write_text(shipped + "\n" + OWNER_LINE + "\n")
        report = mod.plan(root, sanctum, SKILL_DIR)
        change = by_key(report, THEMATIC)
        assert change["kind"] == "integrate-file" and not change["safe"]
        assert change["owner_lines"] == [OWNER_LINE]

        before = snapshot(sanctum)
        result = mod.apply_changes(sanctum, report, {"safe", change["id"]})
        assert result["needs_integration"] == [change["id"]]
        assert snapshot(sanctum) == before  # nothing else was pending, and the integration was refused

    def test_integration_refuses_a_lost_line_and_writes_nothing(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        discipline = sanctum / THEMATIC
        shipped = discipline.read_text()
        discipline.write_text(shipped + "\n" + OWNER_LINE + "\n")
        report = mod.plan(root, sanctum, SKILL_DIR)
        change = by_key(report, THEMATIC)
        before = snapshot(sanctum)
        result = mod.integrate_change(sanctum, report, change["id"], shipped, [], [])
        assert result["status"] == "integration-refused" and result["unaccounted"] == [OWNER_LINE]
        assert snapshot(sanctum) == before

    def test_integration_writes_new_format_and_archives(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        discipline = sanctum / THEMATIC
        shipped = discipline.read_text()
        old_wording = "Old shipped wording nobody needs."
        discipline.write_text(shipped + "\n" + old_wording + "\n" + OWNER_LINE + "\n")
        report = mod.plan(root, sanctum, SKILL_DIR)
        change = by_key(report, THEMATIC)
        story = sanctum / "memory" / "incidents" / "thematic-discipline.md"
        story.write_text(story.read_text() + "\nThe owner's story: " + OWNER_LINE.lstrip("- ") + "\n")
        result = mod.integrate_change(
            sanctum, report, change["id"], shipped, ["memory/incidents/thematic-discipline.md"],
            [{"line": old_wording, "why": "earlier shipped wording"}], today="2026-10-15")
        assert result["status"] == "integrated"
        assert discipline.read_text() == shipped
        archive = (sanctum / result["archived_to"]).read_text()
        assert result["archived_to"].startswith("raw/2026-10-15-upgrade-")
        assert "status: distilled" in archive and OWNER_LINE in archive and "earlier shipped wording" in archive
        assert base_units(sanctum)[THEMATIC]["status"] == "integrated"
        assert mod.plan(root, sanctum, SKILL_DIR)["changes"] == []

    def test_integration_keeps_owner_lines_in_the_text(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        live = section(sanctum, "PERSONA.md", "## Model Awareness").rstrip("\n") + "\n\nOwner: always check the tier first.\n"
        replace_section(sanctum, "PERSONA.md", "## Model Awareness", live)
        report = mod.plan(root, sanctum, SKILL_DIR)
        change = by_key(report, MA)
        assert change["kind"] == "integrate-section"
        wrong = mod.integrate_change(sanctum, report, change["id"], "Owner: always check the tier first.\n", [], [])
        assert wrong["status"] == "integration-refused" and wrong["problems"]
        result = mod.integrate_change(sanctum, report, change["id"], live, [], [])
        assert result["status"] == "integrated"
        assert "Owner: always check the tier first." in (sanctum / "PERSONA.md").read_text()
        assert mod.plan(root, sanctum, SKILL_DIR)["changes"] == []

    def test_keep_stops_the_proposal_until_the_template_changes(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        live = section(sanctum, "PERSONA.md", "## Model Awareness").rstrip("\n") + "\n\nMine, on purpose.\n"
        replace_section(sanctum, "PERSONA.md", "## Model Awareness", live)
        report = mod.plan(root, sanctum, SKILL_DIR)
        change = by_key(report, MA)
        result = mod.keep_changes(sanctum, report, {change["id"]})
        assert result["status"] == "kept"
        again = mod.plan(root, sanctum, SKILL_DIR)
        assert again["changes"] == []
        assert f"{MA} (kept on purpose)" in again["owner_sections_kept"]
        assert "Mine, on purpose." in (sanctum / "PERSONA.md").read_text()
        # The template moves on: the kept text comes back for integration, with the template's change shown.
        set_base(sanctum, MA, live.replace("Mine, on purpose.", "x"), status="kept")
        later = by_key(mod.plan(root, sanctum, SKILL_DIR), MA)
        assert later["kind"] in ("merge-section", "integrate-section")

    def test_missing_incident_is_written_with_its_integration(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        (sanctum / "memory" / "incidents" / "thematic-discipline.md").unlink()
        discipline = sanctum / THEMATIC
        discipline.write_text(discipline.read_text() + "\n" + OWNER_LINE + "\n")
        report = mod.plan(root, sanctum, SKILL_DIR)
        change = by_key(report, THEMATIC)
        assert change["incident"] == "memory/incidents/thematic-discipline.md"
        assert not any(c["file"] == "memory/incidents/thematic-discipline.md" for c in report["changes"])

    def test_cli_integrate_round_trip(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        discipline = sanctum / THEMATIC
        shipped = discipline.read_text()
        discipline.write_text(shipped + "\n" + OWNER_LINE + "\n")
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--apply", "safe", "--format", "json")
        payload = json.loads(out)
        (cid,) = [c["id"] for c in payload["changes"] if c["kind"] == "integrate-file"]
        merged = self.tmp_path / "merged.md"
        merged.write_text(shipped + "\n## Owner learnings\n\n" + OWNER_LINE + "\n")
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--integrate", cid, "--text", str(merged))
        assert rc == 0 and "Integrated:" in out
        assert OWNER_LINE in discipline.read_text()

    def test_wake_reports_pending_integrations(self):
        root, sanctum = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        discipline = sanctum / THEMATIC
        discipline.write_text(discipline.read_text() + "\n" + OWNER_LINE + "\n")
        summary = mod.pending_summary(mod.plan(root, sanctum, SKILL_DIR))
        assert summary["integrate"] == [f"{THEMATIC}#1"]


if __name__ == "__main__":
    unittest.main()
