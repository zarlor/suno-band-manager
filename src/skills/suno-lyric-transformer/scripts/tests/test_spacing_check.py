#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for spacing_check.py: the writer's spacing must come through verbatim."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "spacing_check.py")

WRITER = "Day   by   Day\n    the porch light hums\n\n\nand I wait"


def run(original, transformed, *flags):
    result = subprocess.run(
        [sys.executable, SCRIPT, "--original-text", original, "--transformed-text", transformed, *flags],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout), result.returncode


def kinds(report, severity=None):
    return [f["category"] for f in report["findings"] if severity is None or f["severity"] == severity]


class TestSpacingCheck(unittest.TestCase):
    def test_tags_added_spacing_kept_passes(self):
        transformed = "[Verse 1]\nDay   by   Day\n    the porch light hums\n\n\n[Chorus]\nand I wait\n\n[End]"
        report, code = run(WRITER, transformed)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(code, 0)
        self.assertEqual(report["metrics"]["whitespace_changes"], 0)
        self.assertEqual(report["metrics"]["blank_lines_removed"], 0)
        self.assertEqual([t["line"] for t in report["added_tag_lines"]], [1, 6, 9])
        self.assertEqual(report["added_tag_lines"][1]["tag"], "[Chorus]")

    def test_tags_already_in_the_source_are_not_added(self):
        report, _ = run("[Verse 1]\nhello", "[Verse 1]\nhello\n\n[End]")
        self.assertEqual(report["added_tag_lines"], [{"line": 4, "tag": "[End]"}])

    def test_internal_spacing_flattened_is_high(self):
        transformed = "[Verse 1]\nDay by Day\n    the porch light hums\n\n\nand I wait"
        report, code = run(WRITER, transformed)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(code, 1)
        issues = [f["issue"] for f in report["findings"] if f["severity"] == "high"]
        self.assertTrue(any("internal spacing" in i for i in issues))

    def test_indentation_removed_is_high(self):
        transformed = "Day   by   Day\nthe porch light hums\n\n\nand I wait"
        report, _ = run(WRITER, transformed)
        issues = [f["issue"] for f in report["findings"] if f["severity"] == "high"]
        self.assertTrue(any("indentation" in i for i in issues))

    def test_tab_vs_spaces_counts_as_indentation_change(self):
        report, _ = run("\tline one\nline two", "    line one\nline two")
        self.assertEqual(report["status"], "fail")

    def test_writer_blank_gap_shrunk_is_high(self):
        transformed = "Day   by   Day\n    the porch light hums\n\nand I wait"
        report, _ = run(WRITER, transformed)
        self.assertEqual(report["metrics"]["blank_lines_removed"], 1)
        self.assertEqual(report["status"], "fail")

    def test_blank_lines_added_at_section_break_are_fine(self):
        original = "line one\nline two"
        transformed = "[Verse 1]\nline one\n\n[Chorus]\nline two"
        report, _ = run(original, transformed)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["metrics"]["blank_lines_added"], 1)

    def test_trailing_inline_tag_is_set_aside(self):
        report, _ = run("Day   by   Day", "Day   by   Day [Silence]")
        self.assertEqual(report["status"], "pass")

    def test_leading_inline_tag_keeps_indentation_check(self):
        report, _ = run("    soft line", "    [Whispered] soft line")
        self.assertEqual(report["status"], "pass")
        report, _ = run("    soft line", "[Whispered] soft line")
        self.assertEqual(report["status"], "fail")

    def test_trailing_whitespace_only_is_low(self):
        report, code = run("line one  \nline two", "line one\nline two")
        self.assertEqual(report["status"], "warning")
        self.assertEqual(kinds(report, "low"), ["spacing"])
        self.assertEqual(code, 1)

    def test_crlf_input_is_not_a_spacing_change(self):
        report, _ = run("line one\r\nline two", "line one\nline two")
        self.assertEqual(report["status"], "pass")

    def test_word_edit_is_info_listed_for_reporting(self):
        report, _ = run("the cold rain falls", "the cold rain pours")
        self.assertEqual(report["status"], "pass")
        edits = [f for f in report["findings"] if f["category"] == "edit"]
        self.assertEqual(len(edits), 1)
        self.assertEqual(report["metrics"]["line_edits"], 1)

    def test_edit_location_gives_lines_on_each_side(self):
        # The tag pushes the edit down a line in the transformed text: the two
        # sides must be numbered separately, since changes[].lines cites transformed_lines.
        report, _ = run("one\nthe cold rain falls", "[Verse]\none\nthe cold rain pours")
        edits = [f for f in report["findings"] if f["category"] == "edit"]
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0]["location"], {"original_lines": [2], "transformed_lines": [3]})
        self.assertEqual(report["added_tag_lines"], [{"line": 1, "tag": "[Verse]"}])

    def test_removed_line_has_no_transformed_lines(self):
        report, _ = run("Title Line\none\ntwo", "[Verse]\none\ntwo")
        edits = [f for f in report["findings"] if f["category"] == "edit"]
        self.assertEqual([e["location"] for e in edits], [{"original_lines": [1], "transformed_lines": []}])

    def test_word_fidelity_flags_word_change(self):
        report, _ = run("the cold rain falls", "the cold rain pours", "--word-fidelity")
        self.assertEqual(report["status"], "fail")
        self.assertIn("word_fidelity", kinds(report, "high"))

    def test_word_fidelity_allows_tags_only(self):
        report, _ = run("the cold rain falls", "[Verse]\nthe cold rain falls\n\n[End]", "--word-fidelity")
        self.assertEqual(report["status"], "pass")
        self.assertIs(report["metrics"]["word_fidelity_broken"], False)

    def test_flatten_returns_flat_copy_and_savings(self):
        transformed = "[Verse 1]\nDay   by   Day\n    the porch light hums\n\n\nand I wait"
        report, _ = run(WRITER, transformed, "--flatten")
        self.assertEqual(report["flat_copy"], "[Verse 1]\nDay by Day\nthe porch light hums\n\nand I wait")
        self.assertEqual(report["metrics"]["flat_saved_chars"], len(transformed) - len(report["flat_copy"]))

    def test_flat_copy_omitted_by_default(self):
        report, _ = run("a", "a")
        self.assertNotIn("flat_copy", report)

    def test_missing_input_exits_2(self):
        result = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


class TestFileInput(unittest.TestCase):
    """--original PATH --transformed PATH is the form the workflow runs."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def run_files(self, original, transformed, *flags):
        (self.tmp / "source.txt").write_text(original, encoding="utf-8")
        (self.tmp / "draft.txt").write_text(transformed, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, SCRIPT, "--original", str(self.tmp / "source.txt"),
             "--transformed", str(self.tmp / "draft.txt"), *flags],
            capture_output=True, text=True)
        return json.loads(result.stdout), result.returncode

    def test_flattened_draft_fails_with_exit_1(self):
        flattened = "[Verse 1]\nDay by Day\nthe porch light hums\n\nand I wait\n"
        report, code = self.run_files(WRITER + "\n", flattened)
        self.assertEqual((report["status"], code), ("fail", 1))
        self.assertEqual(report["metrics"]["blank_lines_removed"], 1)
        self.assertEqual(report["metrics"]["whitespace_changes"], 2)

    def test_faithful_draft_passes_with_exit_0(self):
        report, code = self.run_files(WRITER + "\n", "[Verse 1]\n" + WRITER + "\n\n[End]\n")
        self.assertEqual((report["status"], code), ("pass", 0))

    def test_newline_escapes_in_a_file_are_literal_text(self):
        # Only the --*-text arguments turn a backslash-n into a newline.
        report, code = self.run_files("one\\ntwo", "one\\ntwo")
        self.assertEqual((report["metrics"]["writer_lines"], code), (1, 0))

    def test_missing_file_exits_2(self):
        (self.tmp / "source.txt").write_text(WRITER, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, SCRIPT, "--original", str(self.tmp / "source.txt"),
             "--transformed", str(self.tmp / "absent.txt")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("absent.txt", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
