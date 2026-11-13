#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for upgrade_sanctum.py's three-way upgrade: the base record, safe
updates and merges, integration of the owner's lines, and --keep.

The sanctum is scaffolded from the synthetic skill (helpers.make_skill): the
section and discipline text the tests change is text they own.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin, snapshot  # noqa: E402
from test_upgrade_sanctum import _born, _cli_rc, _replace_in, mod  # noqa: E402

BASE = "memory/.template-base.json"
MA = "PERSONA.md ## Model Awareness"
THEMATIC = "memory/disciplines/thematic-discipline.md"
OWNER_LINE = "- A learning the owner taught: read the dossier before every placement."
# The line of the synthetic PERSONA template's Model Awareness section that the
# "older template" variants reword.
NEW_WORDING = "at the moment it matters"
OLD_WORDING = "when it matters"


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
    if len(found) != 1:
        raise AssertionError([c.get("key") for c in report["changes"]])
    return found[0]


def older_wording(text):
    """The section as an earlier template shipped it (fails when the wording to change is absent)."""
    if NEW_WORDING not in text:
        raise AssertionError(f"{NEW_WORDING!r} not in the section")
    return text.replace(NEW_WORDING, OLD_WORDING)


class TestMerge3(unittest.TestCase):
    def test_edits_in_different_places_merge(self):
        base = "a\nb\nc\nd\ne\n"
        live = "a\nb\nc\nd\ne\nowner\n"
        new = "A\nb\nc\nd\ne\n"
        self.assertEqual(mod.merge3(base, live, new), "A\nb\nc\nd\ne\nowner\n")

    def test_overlapping_edits_conflict(self):
        self.assertIsNone(mod.merge3("a\nb\nc\n", "a\nB-owner\nc\n", "a\nB-template\nc\n"))

    def test_identical_edits_merge(self):
        self.assertEqual(mod.merge3("a\nb\n", "a\nx\n", "a\nx\n"), "a\nx\n")

    def test_owner_lines_ignore_markdown_lead(self):
        self.assertEqual(mod.owner_lines("- **Why:** it matters\n> new thought\n", "**Why:** it matters\n"), ["> new thought"])


class TestThreeWayUpgrade(TempDirMixin, unittest.TestCase):
    def test_first_breath_records_the_base(self):
        _, sanctum, _ = _born(self.tmp_path)
        units = base_units(sanctum)
        self.assertIn(MA, units)
        self.assertIn(THEMATIC, units)
        self.assertIn("CREED.md ## Principles", units)
        self.assertTrue(all(u["status"] == "taken" for u in units.values()))

    def test_owner_edit_stands_while_the_template_is_unchanged(self):
        root, sanctum, skill = _born(self.tmp_path)
        persona = sanctum / "PERSONA.md"
        shipped = persona.read_text()
        _replace_in(persona, "The third line never changes.", "The third line, and my own notes.")
        self.assertNotEqual(persona.read_text(), shipped)  # the owner's edit is really there
        report = mod.plan(root, sanctum, skill)
        self.assertEqual(report["changes"], [])
        self.assertEqual(persona.read_text(), shipped.replace("The third line never changes.",
                                                              "The third line, and my own notes."))

    def test_untouched_older_template_updates_safely(self):
        root, sanctum, skill = _born(self.tmp_path)
        shipped_file = (sanctum / "PERSONA.md").read_text()
        older = older_wording(section(sanctum, "PERSONA.md", "## Model Awareness"))
        replace_section(sanctum, "PERSONA.md", "## Model Awareness", older)
        set_base(sanctum, MA, older)
        before = (sanctum / "PERSONA.md").read_text()
        report = mod.plan(root, sanctum, skill)
        change = by_key(report, MA)
        self.assertEqual(change["kind"], "update-section")
        self.assertTrue(change["safe"])
        result = mod.apply_changes(sanctum, report, {"safe"})
        self.assertEqual((sanctum / "PERSONA.md").read_text(), shipped_file)
        # The file was backed up as it stood before the rewrite.
        self.assertEqual((Path(result["backup_path"]) / "PERSONA.md").read_text(), before)
        self.assertEqual(mod.plan(root, sanctum, skill)["changes"], [])

    def test_owner_addition_and_template_change_merge(self):
        root, sanctum, skill = _born(self.tmp_path)
        shipped = section(sanctum, "PERSONA.md", "## Model Awareness")
        older = older_wording(shipped)
        set_base(sanctum, MA, older)
        live = older.rstrip("\n") + "\n\nOwner note: the Persona slot is not the Voice slot.\n\n"
        replace_section(sanctum, "PERSONA.md", "## Model Awareness", live)
        before = (sanctum / "PERSONA.md").read_text()
        report = mod.plan(root, sanctum, skill)
        change = by_key(report, MA)
        self.assertEqual(change["kind"], "merge-section")
        self.assertTrue(change["safe"])
        result = mod.apply_changes(sanctum, report, {"safe"})
        merged = section(sanctum, "PERSONA.md", "## Model Awareness")
        self.assertEqual(merged, shipped.rstrip("\n") + "\n\nOwner note: the Persona slot is not the Voice slot.\n\n")
        self.assertEqual((Path(result["backup_path"]) / "PERSONA.md").read_text(), before)
        self.assertEqual(mod.plan(root, sanctum, skill)["changes"], [])  # merged text stands

    def test_no_base_with_owner_lines_needs_integration(self):
        root, sanctum, skill = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        discipline = sanctum / THEMATIC
        shipped = discipline.read_text()
        discipline.write_text(shipped + "\n" + OWNER_LINE + "\n")
        report = mod.plan(root, sanctum, skill)
        change = by_key(report, THEMATIC)
        self.assertEqual(change["kind"], "integrate-file")
        self.assertFalse(change["safe"])
        self.assertEqual(change["owner_lines"], [OWNER_LINE])
        self.assertEqual(change["id"], f"{THEMATIC}#integrate-file")

        before = snapshot(sanctum)
        result = mod.apply_changes(sanctum, report, {"safe", change["id"]})
        self.assertEqual(result["needs_integration"], [change["id"]])
        self.assertEqual(snapshot(sanctum), before)  # nothing else was pending, and the integration was refused

    def test_integration_refuses_a_lost_line_and_writes_nothing(self):
        root, sanctum, skill = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        discipline = sanctum / THEMATIC
        shipped = discipline.read_text()
        discipline.write_text(shipped + "\n" + OWNER_LINE + "\n")
        report = mod.plan(root, sanctum, skill)
        change = by_key(report, THEMATIC)
        before = snapshot(sanctum)
        result = mod.integrate_change(sanctum, report, change["id"], shipped, [], [])
        self.assertEqual(result["status"], "integration-refused")
        self.assertEqual(result["unaccounted"], [OWNER_LINE])
        self.assertEqual(snapshot(sanctum), before)

    def test_integration_writes_new_format_and_archives(self):
        root, sanctum, skill = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        discipline = sanctum / THEMATIC
        shipped = discipline.read_text()
        old_wording = "Old shipped wording nobody needs."
        discipline.write_text(shipped + "\n" + old_wording + "\n" + OWNER_LINE + "\n")
        before = discipline.read_text()
        report = mod.plan(root, sanctum, skill)
        change = by_key(report, THEMATIC)
        story = sanctum / "memory" / "incidents" / "thematic-discipline.md"
        story.write_text(story.read_text() + "\nThe owner's story: " + OWNER_LINE.lstrip("- ") + "\n")
        result = mod.integrate_change(
            sanctum, report, change["id"], shipped, ["memory/incidents/thematic-discipline.md"],
            [{"line": old_wording, "why": "earlier shipped wording"}], today="2026-10-15")
        self.assertEqual(result["status"], "integrated")
        self.assertEqual(discipline.read_text(), shipped)
        # Beside the raw/ record, the usual backup holds the file as it stood before the write.
        self.assertEqual((Path(result["backup_path"]) / THEMATIC).read_text(), before)
        archive = (sanctum / result["archived_to"]).read_text()
        self.assertTrue(result["archived_to"].startswith("raw/2026-10-15-upgrade-"))
        self.assertIn("status: distilled", archive)
        self.assertIn(OWNER_LINE, archive)
        self.assertIn("earlier shipped wording", archive)
        self.assertEqual(base_units(sanctum)[THEMATIC]["status"], "integrated")
        self.assertEqual(mod.plan(root, sanctum, skill)["changes"], [])

    def test_integration_keeps_owner_lines_in_the_text(self):
        root, sanctum, skill = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        live = section(sanctum, "PERSONA.md", "## Model Awareness").rstrip("\n") + "\n\nOwner: always check the tier first.\n"
        replace_section(sanctum, "PERSONA.md", "## Model Awareness", live)
        report = mod.plan(root, sanctum, skill)
        change = by_key(report, MA)
        self.assertEqual(change["kind"], "integrate-section")
        before = snapshot(sanctum)
        wrong = mod.integrate_change(sanctum, report, change["id"], "Owner: always check the tier first.\n", [], [])
        self.assertEqual(wrong["status"], "integration-refused")
        self.assertEqual(wrong["problems"],
                         ["the text must be the whole section, starting with its heading (## Model Awareness)"])
        self.assertEqual(snapshot(sanctum), before)
        result = mod.integrate_change(sanctum, report, change["id"], live, [], [])
        self.assertEqual(result["status"], "integrated")
        self.assertIn("Owner: always check the tier first.", (sanctum / "PERSONA.md").read_text())
        self.assertEqual(mod.plan(root, sanctum, skill)["changes"], [])

    def test_keep_stops_the_proposal_until_the_template_changes(self):
        root, sanctum, skill = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        live = section(sanctum, "PERSONA.md", "## Model Awareness").rstrip("\n") + "\n\nMine, on purpose.\n"
        replace_section(sanctum, "PERSONA.md", "## Model Awareness", live)
        report = mod.plan(root, sanctum, skill)
        change = by_key(report, MA)
        result = mod.keep_changes(sanctum, report, {change["id"]})
        self.assertEqual(result["status"], "kept")
        again = mod.plan(root, sanctum, skill)
        self.assertEqual(again["changes"], [])
        self.assertIn(f"{MA} (kept on purpose)", again["owner_sections_kept"])
        self.assertIn("Mine, on purpose.", (sanctum / "PERSONA.md").read_text())
        # The template moves on: the kept text comes back for integration, with the template's change shown.
        set_base(sanctum, MA, live.replace("Mine, on purpose.", "x"), status="kept")
        later = by_key(mod.plan(root, sanctum, skill), MA)
        self.assertIn(later["kind"], ("merge-section", "integrate-section"))

    def test_missing_incident_is_written_with_its_integration(self):
        root, sanctum, skill = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        (sanctum / "memory" / "incidents" / "thematic-discipline.md").unlink()
        discipline = sanctum / THEMATIC
        discipline.write_text(discipline.read_text() + "\n" + OWNER_LINE + "\n")
        report = mod.plan(root, sanctum, skill)
        change = by_key(report, THEMATIC)
        self.assertEqual(change["incident"], "memory/incidents/thematic-discipline.md")
        self.assertFalse(any(c["file"] == "memory/incidents/thematic-discipline.md" for c in report["changes"]))

    def test_cli_integrate_round_trip(self):
        root, sanctum, skill = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        discipline = sanctum / THEMATIC
        shipped = discipline.read_text()
        discipline.write_text(shipped + "\n" + OWNER_LINE + "\n")
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--skill-path", str(skill),
                          "--apply", "safe", "--format", "json")
        payload = json.loads(out)
        (cid,) = [c["id"] for c in payload["changes"] if c["kind"] == "integrate-file"]
        merged = self.tmp_path / "merged.md"
        merged.write_text(shipped + "\n## Owner learnings\n\n" + OWNER_LINE + "\n")
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--skill-path", str(skill),
                          "--integrate", cid, "--text", str(merged))
        self.assertEqual(rc, 0)
        self.assertIn("Integrated:", out)
        self.assertIn(OWNER_LINE, discipline.read_text())

    def test_pending_summary_counts_safe_changes_and_lists_integrations(self):
        """pending_summary() is what the wake reports; the wake's own use of it is tested in test_pre_activate."""
        root, sanctum, skill = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        discipline = sanctum / THEMATIC
        discipline.write_text(discipline.read_text() + "\n" + OWNER_LINE + "\n")
        (sanctum / "HOW-I-REMEMBER.md").unlink()
        (sanctum / "raw").rmdir()
        summary = mod.pending_summary(mod.plan(root, sanctum, skill))
        self.assertEqual(summary, {"safe": 2, "integrate": [f"{THEMATIC}#integrate-file"]})

    def test_integration_with_empty_text_is_refused_not_raised(self):
        """An empty --text file: an integration-refused report with the reason, and nothing written."""
        root, sanctum, skill = _born(self.tmp_path)
        (sanctum / BASE).unlink()
        live = section(sanctum, "PERSONA.md", "## Model Awareness").rstrip("\n") + "\n\nOwner: always check the tier first.\n"
        replace_section(sanctum, "PERSONA.md", "## Model Awareness", live)
        discipline = sanctum / THEMATIC
        discipline.write_text(discipline.read_text() + "\n" + OWNER_LINE + "\n")
        report = mod.plan(root, sanctum, skill)
        before = snapshot(sanctum)
        for key, text in ((MA, ""), (MA, "\n  \n"), (THEMATIC, "")):
            with self.subTest(key=key, text=text):
                change = by_key(report, key)
                dropped = [{"line": line, "why": "testing the empty text"} for line in change["owner_lines"]]
                result = mod.integrate_change(sanctum, report, change["id"], text, [], dropped)
                self.assertEqual(result["status"], "integration-refused")
                self.assertEqual(result["problems"], ["the text is empty"])
                self.assertEqual(snapshot(sanctum), before)
        empty = self.tmp_path / "empty.md"
        empty.write_text("")
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--skill-path", str(skill),
                          "--integrate", by_key(report, MA)["id"], "--text", str(empty), "--format", "json")
        self.assertEqual((rc, json.loads(out)["status"]), (1, "integration-refused"))
        self.assertEqual(snapshot(sanctum), before)


if __name__ == "__main__":
    unittest.main()
