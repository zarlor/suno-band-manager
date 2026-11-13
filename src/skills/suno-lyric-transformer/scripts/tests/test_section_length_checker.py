#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for section_length_checker.py"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "section_length_checker.py")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tag_vocab  # noqa: E402


def run_script(*args):
    """Run the script and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True
    )
    return json.loads(result.stdout) if result.stdout else None, result.returncode


class TestSectionLengthChecker(unittest.TestCase):
    def test_sections_within_range(self):
        lyrics = (
            "[Verse 1]\n"
            "Line one of the verse\n"
            "Line two of the verse\n"
            "Line three of the verse\n"
            "Line four of the verse\n"
            "\n"
            "[Chorus]\n"
            "Chorus line one\n"
            "Chorus line two\n"
            "Chorus line three\n"
        )
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["metrics"]["sections_pass"], 2)
        self.assertEqual(report["metrics"]["sections_fail"], 0)

    def test_verse_too_short(self):
        lyrics = (
            "[Verse 1]\n"
            "Only one line\n"
            "\n"
            "[Chorus]\n"
            "Chorus one\n"
            "Chorus two\n"
        )
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "warning")
        short_sections = [s for s in report["sections"] if s["status"] == "short"]
        self.assertGreaterEqual(len(short_sections), 1)
        self.assertEqual(short_sections[0]["base_name"], "verse")

    def test_verse_too_long(self):
        lyrics = "[Verse 1]\n" + "\n".join(f"Line {i}" for i in range(1, 12)) + "\n"
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        long_sections = [s for s in report["sections"] if s["status"] == "long"]
        self.assertGreaterEqual(len(long_sections), 1)

    def test_intro_can_be_empty(self):
        lyrics = (
            "[Intro]\n"
            "\n"
            "[Verse 1]\n"
            "Line one\nLine two\nLine three\nLine four\n"
        )
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        intro = [s for s in report["sections"] if s["base_name"] == "intro"]
        self.assertEqual(len(intro), 1)
        self.assertEqual(intro[0]["status"], "pass")

    def test_numbered_sections_normalized(self):
        lyrics = (
            "[Verse 2]\n"
            "Line one\nLine two\nLine three\nLine four\n"
            "\n"
            "[Chorus]\n"
            "Chorus one\nChorus two\n"
        )
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        verse = [s for s in report["sections"] if s["tag"] == "Verse 2"]
        self.assertEqual(len(verse), 1)
        self.assertEqual(verse[0]["base_name"], "verse")

    def test_tags_that_open_no_section_leave_lines_in_the_current_one(self):
        # A delivery cue, a standalone mood, a descriptor, an unrecognized tag and [End]
        # all sit inside the verse: its four lines are counted, not split off.
        for tag in ("Spoken Word", "Harmonized", "Haunting", "Energy: low", "Banana", "End"):
            with self.subTest(tag=tag):
                report, _ = run_script("--text", f"[Verse 1]\none\ntwo\n[{tag}]\nthree\nfour\n")
                self.assertEqual([(s["tag"], s["line_count"], s["status"]) for s in report["sections"]],
                                 [("Verse 1", 4, "pass")])

    def test_no_section_tags_is_not_a_pass(self):
        for lyrics in ("Just some raw text\nWith no tags", "[Spoken Word]\nSome content\n", ""):
            with self.subTest(lyrics=lyrics):
                report, code = run_script("--text", lyrics)
                self.assertEqual((report["status"], code), ("warning", 0))
                self.assertEqual(report["metrics"]["total_sections"], 0)
                self.assertEqual([(f["severity"], f["issue"]) for f in report["findings"]],
                                 [("high", "No section tags found, so no section length was checked.")])

    def test_every_section_name_has_a_range(self):
        # The vocabulary and the range table must not drift apart: a tag the
        # validator accepts as a section can't come back here as "unknown".
        for name in sorted(tag_vocab.SECTION_NAMES):
            with self.subTest(section=name):
                report, _ = run_script("--text", f"[{name.title()}]\n")
                self.assertEqual(len(report["sections"]), 1)
                self.assertNotEqual(report["sections"][0]["status"], "unknown")
                self.assertIsNotNone(report["sections"][0]["expected_range"])

    def test_buildup_and_added_solos_have_ranges(self):
        report, _ = run_script("--text", "[Buildup]\na\nb\n\n[Build-Up]\na\nb\n\n[Violin Solo]\n\n[Synth Solo]\n")
        self.assertEqual([(s["base_name"], s["expected_range"], s["status"]) for s in report["sections"]],
                         [("buildup", [2, 4], "pass"), ("build-up", [2, 4], "pass"),
                          ("violin solo", [0, 2], "pass"), ("synth solo", [0, 2], "pass")])

    def test_return_and_ending_sections_have_ranges(self):
        lyrics = "[Verse 1]\na\nb\nc\nd\n\n[Instrumental Break]\n\n[Reprise]\nx\ny\n\n[Coda]\nz\n[End]\n"
        report, code = run_script("--text", lyrics)
        by_name = {s["base_name"]: s["status"] for s in report["sections"]}
        for name in ("instrumental break", "reprise", "coda"):
            with self.subTest(section=name):
                self.assertEqual(by_name.get(name), "pass")

    def test_v6_cue_tags_resolve_to_their_section(self):
        lyrics = "[Intro - guitar, instrumental]\n\n[Verse 1 - half-spoken]\na\nb\nc\nd\n\n[Chorus: full band]\nx\ny\n\n[Energy: low]\n[End]\n"
        report, code = run_script("--text", lyrics)
        names = [(s["tag"], s["base_name"]) for s in report["sections"]]
        self.assertIn(("Verse 1 - half-spoken", "verse"), names)
        self.assertIn(("Chorus: full band", "chorus"), names)
        self.assertNotIn("unknown", [s["status"] for s in report["sections"] if s["base_name"] in ("verse", "chorus", "intro")])
        self.assertFalse([s for s in report["sections"] if s["tag"].startswith("Energy")])

    def test_report_structure(self):
        lyrics = "[Verse 1]\nLine one\nLine two\nLine three\nLine four\n"
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        self.assertIn("script", report)
        self.assertIn("version", report)
        self.assertIn("timestamp", report)
        self.assertIn("status", report)
        self.assertIn("sections", report)
        self.assertIn("findings", report)
        self.assertIn("summary", report)

    def test_out_of_range_sections_exit_zero(self):
        report, code = run_script("--text", "[Verse 1]\nonly one line\n[Chorus]\nhook")
        self.assertEqual(report["status"], "warning")
        self.assertEqual(code, 0)

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("section", result.stdout.lower())

    def test_descriptor_metatags_not_counted_as_content(self):
        """Descriptor metatags like [Energy: slow] should not inflate line counts."""
        lyrics = (
            "[Verse 1]\n"
            "[Energy: slow]\n"
            "[Vocal Style: clean]\n"
            "[Mood: dark]\n"
            "Line one of the verse\n"
            "Line two of the verse\n"
            "Line three of the verse\n"
            "Line four of the verse\n"
        )
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        verse = [s for s in report["sections"] if s["base_name"] == "verse"]
        self.assertEqual(len(verse), 1)
        # Should count only 4 lyric lines, not 7
        self.assertEqual(verse[0]["line_count"], 4)
        self.assertEqual(verse[0]["status"], "pass")

    def test_prog_genre_relaxes_verse_limit(self):
        """With --genre prog, verses can have up to 16 lines without warning."""
        lines = "\n".join(f"Line {i}" for i in range(1, 13))
        lyrics = f"[Verse 1]\n{lines}\n"
        # Without genre flag, 12 lines should be too long (max 8)
        report_normal, _ = run_script("--text", lyrics)
        self.assertIsNotNone(report_normal)
        verse_normal = [s for s in report_normal["sections"] if s["base_name"] == "verse"]
        self.assertEqual(verse_normal[0]["status"], "long")

        # With prog genre, 12 lines should pass (max becomes 16)
        report_prog, _ = run_script("--text", lyrics, "--genre", "prog")
        self.assertIsNotNone(report_prog)
        verse_prog = [s for s in report_prog["sections"] if s["base_name"] == "verse"]
        self.assertEqual(verse_prog[0]["status"], "pass")

    def test_multi_word_genre_relaxes_limits(self):
        lyrics = "[Verse 1]\n" + "\n".join(f"Line {i}" for i in range(1, 13)) + "\n"
        for genre in ("prog metal", "Progressive Rock", "experimental/ambient", "death-metal", "METAL"):
            with self.subTest(genre=genre):
                report, _ = run_script("--text", lyrics, "--genre", genre)
                self.assertEqual(report["sections"][0]["expected_range"], [4, 16])
                self.assertEqual(report["sections"][0]["status"], "pass")
        for genre in ("folk", "indie pop", "programmatic"):
            with self.subTest(genre=genre):
                report, _ = run_script("--text", lyrics, "--genre", genre)
                self.assertEqual(report["sections"][0]["expected_range"], [4, 8])
                self.assertEqual(report["sections"][0]["status"], "long")

    def test_interlude_is_known_section(self):
        """Interlude should now be a known section type with defined range."""
        lyrics = "[Interlude]\nSome content\nMore content\n"
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        interlude = [s for s in report["sections"] if s["base_name"] == "interlude"]
        self.assertEqual(len(interlude), 1)
        self.assertEqual(interlude[0]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
