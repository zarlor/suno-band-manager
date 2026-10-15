#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for lyrics-diff.py"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "lyrics-diff.py")


def run_script(*args):
    """Run the script and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True
    )
    return json.loads(result.stdout) if result.stdout else None, result.returncode


class TestLyricsDiff(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def test_identical_lyrics(self):
        text = "[Verse 1]\nHello world\nGoodbye moon"
        report, code = run_script("--original-text", text, "--transformed-text", text)
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(len(report["changes"]), 0)
        self.assertEqual(report["summary"]["lines_added"], 0)
        self.assertEqual(report["summary"]["lines_removed"], 0)
        self.assertEqual(report["summary"]["lines_modified"], 0)

    def test_modified_line(self):
        original = "[Verse 1]\nWalking through the rain"
        transformed = "[Verse 1]\nRunning through the storm"
        report, code = run_script("--original-text", original, "--transformed-text", transformed)
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "info")
        modified = [c for c in report["changes"] if c["type"] == "modified"]
        self.assertGreaterEqual(len(modified), 1)
        self.assertGreaterEqual(report["summary"]["lines_modified"], 1)

    def test_added_lines(self):
        original = "[Verse 1]\nLine one"
        transformed = "[Verse 1]\nLine one\nLine two\nLine three"
        report, code = run_script("--original-text", original, "--transformed-text", transformed)
        self.assertIsNotNone(report)
        added = [c for c in report["changes"] if c["type"] == "added"]
        self.assertGreaterEqual(len(added), 1)
        self.assertGreaterEqual(report["summary"]["lines_added"], 1)

    def test_removed_lines(self):
        original = "[Verse 1]\nLine one\nLine two\nLine three"
        transformed = "[Verse 1]\nLine one"
        report, code = run_script("--original-text", original, "--transformed-text", transformed)
        self.assertIsNotNone(report)
        removed = [c for c in report["changes"] if c["type"] == "removed"]
        self.assertGreaterEqual(len(removed), 1)
        self.assertGreaterEqual(report["summary"]["lines_removed"], 1)

    def test_section_tracking(self):
        original = "[Verse 1]\nOld verse line\n\n[Chorus]\nOld chorus line"
        transformed = "[Verse 1]\nNew verse line\n\n[Chorus]\nNew chorus line"
        report, code = run_script("--original-text", original, "--transformed-text", transformed)
        self.assertIsNotNone(report)
        self.assertGreaterEqual(len(report["summary"]["sections_affected"]), 1)

    def test_unified_diff_output(self):
        original = "[Verse 1]\nHello"
        transformed = "[Verse 1]\nGoodbye"
        report, code = run_script("--original-text", original, "--transformed-text", transformed)
        self.assertIsNotNone(report)
        self.assertIn("unified_diff", report)
        self.assertGreater(len(report["unified_diff"]), 0)

    def test_file_input(self):
        orig_file = self.tmp_path / "orig.txt"
        trans_file = self.tmp_path / "trans.txt"
        orig_file.write_text("[Verse 1]\nOriginal line")
        trans_file.write_text("[Verse 1]\nTransformed line")
        report, code = run_script("--original", str(orig_file), "--transformed", str(trans_file))
        self.assertIsNotNone(report)
        self.assertGreaterEqual(len(report["changes"]), 1)

    def test_report_structure(self):
        report, code = run_script("--original-text", "a", "--transformed-text", "b")
        self.assertIsNotNone(report)
        self.assertIn("script", report)
        self.assertIn("version", report)
        self.assertIn("timestamp", report)
        self.assertIn("status", report)
        self.assertIn("changes", report)
        self.assertIn("summary", report)
        self.assertIn("unified_diff", report)

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("diff", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
