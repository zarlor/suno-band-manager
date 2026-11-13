#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for upgrade_sanctum.py — v7 repair and template upgrades, owner content kept.

The sanctum under test is scaffolded from a small synthetic skill
(helpers.make_skill), so each test edits text it owns. One smoke test runs the
plan against the shipped skill and checks shape only.
"""

import json
from datetime import date
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin, load_script, make_skill, snapshot  # noqa: E402

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

mod = load_script("upgrade_sanctum", "upgrade_sanctum.py")
init = load_script("init_sanctum", "init_sanctum.py")


def _born(tmp_path, skill=None):
    """A freshly scaffolded v7 sanctum whose owner, Sam, has been met.

    The scaffold never names the owner (First Breath asks), so the fixture
    fills the name in as First Breath does and records that text as the base,
    which leaves a sanctum identical to its templates rendered for Sam.

    Returns (project root, sanctum, skill): the skill is the synthetic one
    unless another is passed.
    """
    skill = skill or make_skill(tmp_path)
    root = tmp_path / "project"
    (root / "_bmad").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "docs" / "voice-context-sam.md").write_text("# Sam\n", encoding="utf-8")
    result = init.scaffold(root, skill)
    if result["status"] != "created":
        raise AssertionError(result)
    sanctum = Path(result["sanctum_path"])
    unset = init._seed.OWNER_UNSET
    for path in sanctum.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        met = text.replace(f"**Language:** {unset}", "**Language:** English").replace(unset, "Sam")
        if path.name == "BOND.md":  # the bond's table names the voice file by the owner's slug
            met = met.replace("voice-context-<owner>.md", "voice-context-sam.md")
        if met != text:
            path.write_text(met, encoding="utf-8")
    init._seed.record_seeded_base(sanctum, date.today().isoformat())
    return root, sanctum, skill


def _cli_rc(capsys, *argv):
    with patch.object(sys, "argv", ["upgrade_sanctum.py", *argv]), capsys():
        rc = mod.main()
    return rc, capsys.readouterr().out


def _replace_in(path, old, new):
    """Edit a file, failing loudly when the text to change is not there."""
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"{old!r} not in {path.name}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


class TestUpgradeSanctum(TempDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.root, self.sanctum, self.skill = _born(self.tmp_path)

    def plan(self):
        return mod.plan(self.root, self.sanctum, self.skill)

    def cli(self, *argv):
        return _cli_rc(self.capsys, "--project-root", str(self.root), "--skill-path", str(self.skill), *argv)

    def cli_error(self, *argv):
        """Run the CLI expecting argparse to stop it: returns (exit code, stderr)."""
        with patch.object(sys, "argv", ["upgrade_sanctum.py", "--project-root", str(self.root),
                                        "--skill-path", str(self.skill), *argv]), self.capsys():
            with self.assertRaises(SystemExit) as stopped:
                mod.main()
        return stopped.exception.code, self.capsys.readouterr().err

    def test_fresh_sanctum_needs_nothing(self):
        report = self.plan()
        self.assertEqual(report["status"], "dry-run")
        self.assertEqual(report["sidecar_format"], "v7")
        self.assertEqual(report["changes"], [])
        self.assertEqual(report["notes"], [])

    def test_shipped_skill_fresh_sanctum_needs_nothing(self):
        """Smoke check: what First Breath writes from the shipped skill is what the upgrade expects."""
        root, sanctum, _ = _born(self.tmp_path / "shipped", skill=SKILL_DIR)
        report = mod.plan(root, sanctum, SKILL_DIR)
        self.assertEqual((report["status"], report["sidecar_format"]), ("dry-run", "v7"))
        self.assertEqual([c["id"] for c in report["changes"]], [])

    def test_dry_run_writes_nothing(self):
        (self.sanctum / "memory" / ".template-base.json").unlink()  # an older sanctum: no base on record
        _replace_in(self.sanctum / "CREED.md", "hand over no package", "improvise a package")
        before = snapshot(self.sanctum)
        report = self.plan()
        (change,) = report["changes"]
        self.assertEqual((change["kind"], change["id"]), ("integrate-section", "CREED.md#package-assembly-rule-core"))
        self.assertEqual(change["owner_lines"], ["Use the skills; improvise a package built from memory."])
        self.assertEqual(snapshot(self.sanctum), before)

    def test_missing_section_is_safe_add_and_applies(self):
        creed = self.sanctum / "CREED.md"
        text = creed.read_text(encoding="utf-8")
        start = text.index("## Standing Orders")
        end = text.index("## Package Assembly Rule")
        creed.write_text(text[:start] + text[end:], encoding="utf-8")
        before = creed.read_text(encoding="utf-8")
        report = self.plan()
        (add,) = report["changes"]
        self.assertEqual((add["kind"], add["heading"], add["safe"]), ("add-section", "## Standing Orders", True))
        self.assertEqual(add["id"], "CREED.md#standing-orders")
        result = mod.apply_changes(self.sanctum, report, {"safe"})
        self.assertEqual(result["status"], "applied")
        self.assertEqual(creed.read_text(encoding="utf-8"), text)  # back to what First Breath wrote
        backup = Path(result["backup_path"])
        self.assertEqual(backup.parent, self.sanctum.parent)
        self.assertTrue(backup.name.startswith(".suno-agent-band-manager-upgrade-backup-"))
        self.assertEqual((backup / "CREED.md").read_text(encoding="utf-8"), before)
        self.assertEqual(self.plan()["changes"], [])

    def test_owner_sections_are_never_proposed(self):
        persona = self.sanctum / "PERSONA.md"
        persona.write_text(persona.read_text(encoding="utf-8") + "- **2026-10-01** — Learned to hold the bridge back.\n",
                           encoding="utf-8")
        _replace_in(self.sanctum / "CREED.md", "## Mission\n", "## Mission\n\nFor Sam: a personal catalog.\n")
        bond = self.sanctum / "BOND.md"
        _replace_in(bond, "- **Language:** English", "- **Language:** English\n- **Tier:** Pro")
        bond.write_text(bond.read_text(encoding="utf-8") + "\n## Their Bands\n\n- Paper Lanterns\n", encoding="utf-8")
        report = self.plan()
        self.assertEqual(report["changes"], [])
        self.assertEqual(sorted(report["owner_sections_kept"]), [
            "BOND.md ## Owner Summary", "BOND.md ## Their Bands", "CREED.md ## Mission",
            "PERSONA.md ## Evolution Log",
        ])

    def test_standing_memory_is_never_proposed(self):
        (self.sanctum / "memory" / "work" / "current.md").write_text("# Current Work\n\nA song in progress.\n")
        (self.sanctum / "memory" / "owner" / "preferences.md").unlink()
        self.assertEqual(self.plan()["changes"], [])

    def test_missing_identity_file_restored_with_dominion(self):
        original = (self.sanctum / "CREED.md").read_text(encoding="utf-8")
        (self.sanctum / "CREED.md").unlink()
        (self.sanctum / "HOW-I-REMEMBER.md").unlink()
        report = self.plan()
        self.assertEqual(report["sidecar_format"], "damaged")
        self.assertEqual(sorted(report["missing_identity"]), ["CREED.md", "HOW-I-REMEMBER.md"])
        self.assertEqual(sorted(c["id"] for c in report["changes"]),
                         ["CREED.md#create-file", "HOW-I-REMEMBER.md#create-file"])
        self.assertTrue(all(c["kind"] == "create-file" and c["safe"] for c in report["changes"]))
        mod.apply_changes(self.sanctum, report, {"safe"})
        creed = (self.sanctum / "CREED.md").read_text(encoding="utf-8")
        self.assertEqual(creed, original)
        self.assertNotIn("{dominion}", creed)
        self.assertIn("### Read Access", creed)
        self.assertEqual(self.plan()["sidecar_format"], "v7")

    def test_missing_folders_are_created(self):
        (self.sanctum / "capabilities").rmdir()
        (self.sanctum / "memory" / "chronology").rmdir()
        report = self.plan()
        self.assertEqual(sorted(c["id"] for c in report["changes"]),
                         ["capabilities/#create-folder", "memory/chronology/#create-folder"])
        self.assertTrue(all(c["kind"] == "create-folder" and c["safe"] for c in report["changes"]))
        mod.apply_changes(self.sanctum, report, {"safe"})
        self.assertTrue((self.sanctum / "capabilities").is_dir())
        self.assertTrue((self.sanctum / "memory" / "chronology").is_dir())

    def test_missing_disciplines_are_reseeded_and_a_file_that_reappeared_is_left_alone(self):
        package = self.sanctum / "memory" / "disciplines" / "package-assembly.md"
        story = self.sanctum / "memory" / "incidents" / "workshop-capture.md"
        shipped_story = story.read_text(encoding="utf-8")
        package.unlink()
        story.unlink()
        report = self.plan()
        creates = sorted(c["file"] for c in report["changes"] if c["kind"] == "create-file")
        self.assertEqual(creates, ["memory/disciplines/package-assembly.md", "memory/incidents/workshop-capture.md"])
        # Between the plan and the apply the owner writes the discipline themselves.
        package.write_text("# Package Assembly Rule\n\nThe owner's own version.\n", encoding="utf-8")
        mod.apply_changes(self.sanctum, report, {"safe"})
        self.assertEqual(package.read_text(encoding="utf-8"), "# Package Assembly Rule\n\nThe owner's own version.\n")
        self.assertEqual(story.read_text(encoding="utf-8"), shipped_story)

    def test_incident_stories_are_create_only(self):
        story = self.sanctum / "memory" / "incidents" / "workshop-capture.md"
        story.write_text("# owner incident archive\n", encoding="utf-8")
        self.assertEqual(self.plan()["changes"], [])

    def test_capabilities_builtin_regenerated_learned_kept(self):
        caps = self.sanctum / "CAPABILITIES.md"
        shipped = caps.read_text(encoding="utf-8")
        builtin = dict(mod.split(shipped))["## Built-in"]
        _replace_in(caps, builtin, "## Built-in\n\nAn older roster line.\n\n")
        _replace_in(caps, "|------|------|-------------|--------|-------|\n",
                    "|------|------|-------------|--------|-------|\n| [LX] | Liner Notes | x | owner | 2026-10-01 |\n")
        before = caps.read_text(encoding="utf-8")
        report = self.plan()
        (change,) = report["changes"]
        self.assertEqual((change["kind"], change["heading"], change["safe"]),
                         ("regenerate-section", "## Built-in", True))
        self.assertIn("CAPABILITIES.md ## Learned", report["owner_sections_kept"])
        result = mod.apply_changes(self.sanctum, report, {"safe"})
        new = caps.read_text(encoding="utf-8")
        self.assertEqual(dict(mod.split(new))["## Built-in"], builtin)
        self.assertIn("| [LX] | Liner Notes | x | owner | 2026-10-01 |", new)
        # The rewrite was backed up first.
        self.assertEqual((Path(result["backup_path"]) / "CAPABILITIES.md").read_text(encoding="utf-8"), before)

    def test_old_store_is_refused(self):
        for fmt in ("v1", "v2"):
            with self.subTest(fmt=fmt):
                root = self.tmp_path / fmt
                legacy = root / "_bmad" / "_memory" / "band-manager-sidecar"
                legacy.mkdir(parents=True)
                names = ["index.md"] if fmt == "v1" else mod._seed.V2_SPINE
                for name in names:
                    (legacy / name).write_text("# old\n")
                report = mod.plan(root, legacy, self.skill)
                self.assertEqual(report["status"], "not-applicable")
                self.assertEqual(report["sidecar_format"], fmt)
                self.assertIn("migrate_sanctum_to_v7.py", report["message"])

    def test_partial_old_store_is_refused(self):
        store = self.tmp_path / "store"
        store.mkdir()
        (store / "MEMORY.md").write_text("# old\n")
        (store / "CREED.md").write_text("# old\n")
        report = mod.plan(self.tmp_path, store, self.skill)
        self.assertEqual(report["status"], "not-applicable")
        self.assertIn("migrate_sanctum_to_v7.py", report["message"])
        self.assertEqual(sorted(p.name for p in store.iterdir()), ["CREED.md", "MEMORY.md"])

    def test_incomplete_store_at_the_legacy_path_is_never_planned_into(self):
        """A partial old store that carries none of the old-layout markers: still nothing created in it."""
        root = self.tmp_path / "legacy-project"
        legacy = mod._seed.legacy_sanctum_dir(root)
        legacy.mkdir(parents=True)
        (legacy / "index.md").write_text("# v1\n")
        (legacy / "CREED.md").write_text("# stray v2 file\n")
        report = mod.plan(root, legacy, self.skill)
        self.assertEqual((report["status"], report["sidecar_format"]), ("not-applicable", "damaged"))
        self.assertEqual(report["changes"], [])
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--skill-path", str(self.skill),
                          "--apply", "safe", "--format", "json")
        self.assertEqual((rc, json.loads(out)["status"]), (1, "not-applicable"))
        self.assertEqual(sorted(p.name for p in legacy.iterdir()), ["CREED.md", "index.md"])

    def test_unfinished_v7_path_beside_an_unconverted_store_is_not_restored_from_templates(self):
        """Restoring the identity files would make every later wake ignore the old store."""
        root = self.tmp_path / "both"
        legacy = mod._seed.legacy_sanctum_dir(root)
        legacy.mkdir(parents=True)
        for name in mod._seed.V2_SPINE:
            (legacy / name).write_text("# old\n")
        stub = mod._seed.sanctum_dir(root)
        (stub / "memory" / "work").mkdir(parents=True)
        (stub / "memory" / "work" / "current.md").write_text("# Current Work\n")
        before = snapshot(stub)
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--skill-path", str(self.skill),
                          "--apply", "safe", "--format", "json")
        payload = json.loads(out)
        self.assertEqual((rc, payload["status"]), (1, "not-applicable"))
        self.assertEqual((payload["legacy_store"], payload["legacy_format"]), (str(legacy.resolve()), "v2"))
        self.assertEqual(payload["changes"], [])
        self.assertEqual(snapshot(stub), before)

    def test_absent_sanctum_is_first_breath(self):
        report = mod.plan(self.tmp_path, self.tmp_path / "nothing", self.skill)
        self.assertEqual(report["status"], "not-applicable")
        self.assertIn("init_sanctum.py", report["message"])

    # --- change ids ---------------------------------------------------------

    def test_change_ids_do_not_renumber_between_plans(self):
        """An id from the first plan names the same section after another change was applied."""
        (self.sanctum / "memory" / ".template-base.json").unlink()
        persona = self.sanctum / "PERSONA.md"
        identity = "## Identity\n\nA band manager for Sam.\n\nOwner line in Identity.\n\n"
        awareness = dict(mod.split(persona.read_text(encoding="utf-8")))["## Model Awareness"]
        _replace_in(persona, "## Identity\n\nA band manager for Sam.\n\n", identity)
        _replace_in(persona, awareness, awareness.rstrip("\n") + "\n\nOwner line in Model Awareness.\n\n")
        first = self.plan()
        ids = {c["heading"]: c["id"] for c in first["changes"]}
        self.assertEqual(ids, {"## Identity": "PERSONA.md#identity", "## Model Awareness": "PERSONA.md#model-awareness"})
        # The first of the two is settled; the other keeps its id in the next plan.
        kept = mod.keep_changes(self.sanctum, first, {"PERSONA.md#identity"})
        self.assertEqual(kept["kept"], ["PERSONA.md#identity"])
        second = self.plan()
        self.assertEqual([(c["id"], c["heading"]) for c in second["changes"]],
                         [("PERSONA.md#model-awareness", "## Model Awareness")])
        # The settled id, reused by mistake, is unknown: it never lands on another section.
        again = mod.keep_changes(self.sanctum, second, {"PERSONA.md#identity"})
        self.assertEqual((again["status"], again["unknown_ids"]), ("nothing-kept", ["PERSONA.md#identity"]))
        rc, out = self.cli("--keep", "PERSONA.md#identity", "--format", "json")
        self.assertEqual((rc, json.loads(out)["unknown_ids"]), (1, ["PERSONA.md#identity"]))
        base = json.loads((self.sanctum / "memory" / ".template-base.json").read_text(encoding="utf-8"))["units"]
        self.assertEqual(sorted(k for k, v in base.items() if v["status"] == "kept"), ["PERSONA.md ## Identity"])

    def test_headings_that_slug_alike_get_distinct_ids(self):
        used = set()
        first = mod.change_id({"file": "X.md", "heading": "## Notes", "kind": "update-section"}, used)
        second = mod.change_id({"file": "X.md", "heading": "## Notes!", "kind": "update-section"}, used)
        whole = mod.change_id({"file": "X.md", "heading": None, "kind": "create-file"}, used)
        self.assertEqual((first, second, whole), ("X.md#notes", "X.md#notes-2", "X.md#create-file"))

    # --- duplicate headings and unreadable files ----------------------------

    def test_duplicate_template_heading_is_not_compared_or_written(self):
        """Two `## Model Awareness` sections: the plan would read one and the write hit the other."""
        (self.sanctum / "memory" / ".template-base.json").unlink()
        persona = self.sanctum / "PERSONA.md"
        persona.write_text(
            persona.read_text(encoding="utf-8") + "\n## Model Awareness\n\nThe owner's second copy.\n", encoding="utf-8")
        (self.sanctum / "HOW-I-REMEMBER.md").unlink()  # something safe is pending elsewhere
        before = persona.read_text(encoding="utf-8")
        report = self.plan()
        self.assertEqual([c["id"] for c in report["changes"]], ["HOW-I-REMEMBER.md#create-file"])
        self.assertTrue(any(n.startswith("PERSONA.md: ## Model Awareness appears more than once") for n in report["notes"]),
                        report["notes"])
        mod.apply_changes(self.sanctum, report, {"safe"})
        self.assertEqual(persona.read_text(encoding="utf-8"), before)

    def test_duplicate_owner_heading_does_not_block_the_file(self):
        bond = self.sanctum / "BOND.md"
        bond.write_text(bond.read_text(encoding="utf-8") + "\n## Their Bands\n\n- One\n\n## Their Bands\n\n- Two\n",
                        encoding="utf-8")
        report = self.plan()
        self.assertEqual(report["notes"], [])
        self.assertEqual(report["changes"], [])

    def test_non_utf8_live_file_is_noted_not_raised(self):
        (self.sanctum / "PERSONA.md").write_bytes(b"# Persona \xff\n")
        (self.sanctum / "memory" / "disciplines" / "research-discipline.md").write_bytes(b"\xff\n")
        report = self.plan()
        self.assertEqual(report["changes"], [])
        self.assertEqual(sorted(n.split(" is not valid UTF-8")[0] for n in report["notes"]),
                         ["PERSONA.md", "memory/disciplines/research-discipline.md"])

    # --- CLI ----------------------------------------------------------------

    def test_cli_json_dry_run(self):
        rc, out = self.cli("--format", "json")
        payload = json.loads(out)
        self.assertEqual((rc, payload["status"], payload["changes"]), (0, "dry-run", []))

    def test_cli_apply_safe(self):
        (self.sanctum / "HOW-I-REMEMBER.md").unlink()
        rc, out = self.cli("--apply", "safe")
        self.assertEqual(rc, 0)
        self.assertIn("Applied: HOW-I-REMEMBER.md#create-file", out)
        self.assertTrue((self.sanctum / "HOW-I-REMEMBER.md").is_file())

    def test_cli_points_a_legacy_project_at_the_converter(self):
        root = self.tmp_path / "legacy-project"
        legacy = root / "_bmad" / "_memory" / "band-manager-sidecar"
        legacy.mkdir(parents=True)
        for name in mod._seed.V2_SPINE:
            (legacy / name).write_text("# old\n")
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--skill-path", str(self.skill))
        self.assertEqual(rc, 0)
        self.assertIn("(v2)", out)
        self.assertIn("migrate_sanctum_to_v7.py", out)
        rc, out = _cli_rc(self.capsys, "--project-root", str(root), "--skill-path", str(self.skill), "--apply", "safe")
        self.assertEqual(rc, 1)
        self.assertIn("uv run {skill-root}/scripts/migrate_sanctum_to_v7.py", out)

    def test_cli_apply_unknown_id_exits_1(self):
        rc, out = self.cli("--apply", "NOPE.md#gone", "--format", "json")
        payload = json.loads(out)
        self.assertEqual(rc, 1)
        self.assertEqual((payload["status"], payload["unknown_ids"]), ("nothing-applied", ["NOPE.md#gone"]))

    def test_cli_apply_partly_unknown_ids_exits_1_but_applies_the_rest(self):
        (self.sanctum / "HOW-I-REMEMBER.md").unlink()
        rc, out = self.cli("--apply", "safe,TYPO#1")
        self.assertEqual(rc, 1)
        self.assertIn("Applied: HOW-I-REMEMBER.md#create-file", out)
        self.assertIn("Unknown ids (not applied): TYPO#1", out)
        self.assertTrue((self.sanctum / "HOW-I-REMEMBER.md").is_file())

    def test_cli_apply_safe_with_nothing_pending_is_clean(self):
        rc, out = self.cli("--apply", "safe", "--format", "json")
        self.assertEqual((rc, json.loads(out)["status"]), (0, "nothing-to-apply"))

    def test_cli_empty_apply_exits_1(self):
        rc, _ = self.cli("--apply", ",")
        self.assertEqual(rc, 1)

    def test_cli_unreadable_text_or_dropped_is_bad_input_and_nothing_is_done(self):
        """A missing --text, a missing --dropped or one that is not a JSON list: exit 2 with the
        reason, before the --keep on the same command line records anything."""
        (self.sanctum / "memory" / ".template-base.json").unlink()
        _replace_in(self.sanctum / "CREED.md", "hand over no package", "improvise a package")
        text = self.tmp_path / "section.md"
        text.write_text("## Package Assembly Rule — CORE\n\nUse the skills; improvise a package built from memory.\n")
        not_json = self.tmp_path / "dropped.txt"
        not_json.write_text("not json")
        not_list = self.tmp_path / "dropped.json"
        not_list.write_text('{"line": "x", "why": "y"}')
        cid = "CREED.md#package-assembly-rule-core"
        before = snapshot(self.sanctum)
        cases = {
            "--text": ["--integrate", cid, "--text", str(self.tmp_path / "missing.md"), "--keep", cid],
            "--dropped": ["--integrate", cid, "--text", str(text), "--dropped", str(self.tmp_path / "missing.json")],
            "could not be read as JSON": ["--integrate", cid, "--text", str(text), "--dropped", str(not_json)],
            "must hold a JSON list": ["--integrate", cid, "--text", str(text), "--dropped", str(not_list)],
            "needs --text": ["--integrate", cid],
        }
        for expected, argv in cases.items():
            with self.subTest(expected=expected):
                code, err = self.cli_error(*argv, "--format", "json")
                self.assertEqual(code, 2)
                self.assertIn(expected, err)
                self.assertEqual(snapshot(self.sanctum), before)


if __name__ == "__main__":
    unittest.main()
