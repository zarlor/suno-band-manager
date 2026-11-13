#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for cliche_detector.py"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "cliche_detector.py")


def run_script(*args):
    """Run the script and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True
    )
    return json.loads(result.stdout) if result.stdout else None, result.returncode


class TestClicheDetector(unittest.TestCase):
    def test_detects_fire_in_soul(self):
        report, code = run_script("--text", "There's a fire in my soul tonight")
        self.assertIsNotNone(report)
        self.assertGreaterEqual(report["metrics"]["total_cliches_found"], 1)
        self.assertTrue(any("fire in my soul" in f["data"]["matched_text"] for f in report["findings"]))

    def test_detects_dance_in_rain(self):
        report, code = run_script("--text", "We'll dance in the rain together")
        self.assertIsNotNone(report)
        self.assertGreaterEqual(report["metrics"]["total_cliches_found"], 1)

    def test_detects_broken_heart(self):
        report, code = run_script("--text", "My broken heart won't heal")
        self.assertIsNotNone(report)
        self.assertGreaterEqual(report["metrics"]["total_cliches_found"], 1)

    def test_detects_stand_tall(self):
        report, code = run_script("--text", "I'm standing tall against the wind")
        self.assertIsNotNone(report)
        self.assertGreaterEqual(report["metrics"]["total_cliches_found"], 1)

    def test_no_cliches_in_clean_text(self):
        report, code = run_script("--text", "The kitchen table holds three plates\nSteam rising from the coffee cup")
        self.assertIsNotNone(report)
        self.assertEqual(report["metrics"]["total_cliches_found"], 0)
        self.assertEqual(code, 0)

    def test_skips_metatags(self):
        text = "[Verse 1]\nFire in my soul\n[Chorus]\nClean lyrics here"
        report, code = run_script("--text", text)
        self.assertIsNotNone(report)
        # Should find the cliche in the lyric line, not in metatags
        self.assertGreaterEqual(report["metrics"]["total_cliches_found"], 1)

    def test_provides_alternatives(self):
        report, code = run_script("--text", "Rise from the ashes of what we were")
        self.assertIsNotNone(report)
        self.assertGreater(len(report["findings"]), 0)
        finding = report["findings"][0]
        self.assertIn("alternatives", finding["data"])
        self.assertGreater(len(finding["data"]["alternatives"]), 0)

    def test_multiple_cliches_in_one_text(self):
        text = (
            "Fire in my soul keeps burning bright\n"
            "Standing tall through broken dreams\n"
            "Dance in the rain with a heart of gold\n"
        )
        report, code = run_script("--text", text)
        self.assertIsNotNone(report)
        self.assertGreaterEqual(report["metrics"]["total_cliches_found"], 3)

    def test_case_insensitive(self):
        report, code = run_script("--text", "FIRE IN MY SOUL")
        self.assertIsNotNone(report)
        self.assertGreaterEqual(report["metrics"]["total_cliches_found"], 1)

    def test_report_structure(self):
        report, code = run_script("--text", "Just a normal line")
        self.assertIsNotNone(report)
        self.assertIn("script", report)
        self.assertIn("version", report)
        self.assertIn("timestamp", report)
        self.assertIn("status", report)
        self.assertIn("metrics", report)
        self.assertIn("findings", report)
        self.assertIn("summary", report)

    def test_cliches_found_exit_zero(self):
        report, code = run_script("--text", "Fire in my soul keeps burning bright")
        self.assertGreaterEqual(report["metrics"]["total_cliches_found"], 1)
        self.assertEqual(code, 0)

    def test_latin_only_skips_non_latin_lines(self):
        text = "my broken heart\nразбитое сердце broken heart\n心が痛い"
        report, code = run_script("--text", text, "--latin-only")
        self.assertEqual(code, 0)
        self.assertEqual([f["location"]["line"] for f in report["findings"]], [1])
        self.assertEqual([(d["line_number"], d["script"]) for d in report["skipped_lines"]],
                         [(2, "mixed"), (3, "non_latin")])
        self.assertIs(report["metrics"]["latin_only"], True)
        self.assertEqual(report["metrics"]["skipped_line_count"], 2)

    def test_without_flag_scans_every_line(self):
        text = "my broken heart\nразбитое сердце broken heart"
        report, _ = run_script("--text", text)
        self.assertEqual(report["metrics"]["total_cliches_found"], 2)
        self.assertEqual(report["skipped_lines"], [])

    def test_missing_file_exits_2(self):
        _, code = run_script("/nonexistent/lyrics.txt")
        self.assertEqual(code, 2)

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("cliche", result.stdout.lower())


class TestMatching(unittest.TestCase):
    def matched(self, text):
        report, _ = run_script("--text", text)
        self.assertEqual(report["metrics"]["total_cliches_found"], len(report["findings"]))
        return [f["data"]["matched_text"].lower() for f in report["findings"]]

    def test_one_phrase_is_flagged_once(self):
        # Two patterns cover this phrase; the longer match is the one cliche.
        self.assertEqual(self.matched("There is a light at the end of the tunnel"),
                         ["light at the end of the tunnel"])
        self.assertEqual(self.matched("Nothing can mend my broken heart"), ["mend my broken heart"])

    def test_one_phrase_is_one_category_count(self):
        report, _ = run_script("--text", "a light at the end of the tunnel")
        self.assertEqual(sum(report["metrics"]["categories"].values()), 1)

    def test_separate_cliches_on_one_line_both_count(self):
        self.assertEqual(self.matched("my broken heart will never give up"),
                         ["broken heart", "never give up"])

    def test_no_match_inside_longer_words(self):
        for text in ("we walked along roads of dust", "I understand tall tales",
                     "an unbroken heart", "the abundance in the rainbow", "you complete mess"):
            with self.subTest(text=text):
                self.assertEqual(self.matched(text), [])

    def test_plural_and_inflected_forms_still_match(self):
        cases = {
            "down long roads we go": "long roads",
            "burning brightly in the night": "burning brightly",
            "the spark that ignites it all": "spark that ignites",
            "your love is eternal": "your love is eternal",
            "chasing the sunset again": "chasing the sunset",
            "we arise from the ashes": "arise from the ashes",
        }
        for text, phrase in cases.items():
            with self.subTest(text=text):
                self.assertEqual(self.matched(text), [phrase])


if __name__ == "__main__":
    unittest.main()
