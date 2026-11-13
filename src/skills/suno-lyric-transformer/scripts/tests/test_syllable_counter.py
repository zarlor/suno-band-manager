#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for syllable_counter.py"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "syllable_counter.py")


def run_script(*args):
    """Run the script and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True
    )
    return json.loads(result.stdout) if result.stdout else None, result.returncode


# Also test the count_syllables function directly
import importlib.util
_spec = importlib.util.spec_from_file_location("syllable_counter", Path(__file__).parent.parent / "syllable_counter.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
count_syllables = _mod.count_syllables
estimate_duration = _mod.estimate_duration
format_duration_range = _mod.format_duration_range


class TestSyllableCounting(unittest.TestCase):
    """Test individual word syllable counting."""

    def test_one_syllable_words(self):
        for word in ["cat", "dog", "the", "run", "light", "dream"]:
            with self.subTest(word=word):
                self.assertEqual(count_syllables(word), 1, f"Expected 1 syllable for '{word}', got {count_syllables(word)}")

    def test_two_syllable_words(self):
        for word in ["hello", "window", "walking", "morning", "shadow"]:
            with self.subTest(word=word):
                self.assertEqual(count_syllables(word), 2, f"Expected 2 syllables for '{word}', got {count_syllables(word)}")

    def test_three_syllable_words(self):
        for word in ["beautiful", "another", "everyone", "different"]:
            with self.subTest(word=word):
                result = count_syllables(word)
                self.assertEqual(result, 3, f"Expected 3 syllables for '{word}', got {result}")

    def test_contractions(self):
        self.assertEqual(count_syllables("I'm"), 1)
        self.assertEqual(count_syllables("don't"), 1)
        self.assertEqual(count_syllables("couldn't"), 2)

    def test_empty_string(self):
        self.assertEqual(count_syllables(""), 0)


class TestLyricsAnalysis(unittest.TestCase):
    """Test full lyrics analysis via the script."""

    def test_basic_analysis(self):
        lyrics = (
            "[Verse 1]\n"
            "Walking through the morning light\n"
            "Counting shadows on the wall\n"
        )
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        self.assertEqual(report["script"], "syllable-counter")
        self.assertEqual(report["metrics"]["total_lyric_lines"], 2)
        self.assertGreater(report["metrics"]["total_syllables"], 0)

    def test_min_max_and_average(self):
        report, _ = run_script("--text", "[Verse 1]\ncat dog\nhello window morning\n")
        m = report["metrics"]
        self.assertEqual([d["syllables"] for d in report["line_data"]], [2, 6])
        self.assertEqual((m["min_syllables"], m["max_syllables"], m["average_syllables_per_line"]), (2, 6, 4.0))
        self.assertEqual(m["total_syllables"], 8)

    def test_accents_and_curly_apostrophes_count_like_plain_text(self):
        # The shared counter folds these itself; the script passes lines through untouched.
        fancy, _ = run_script("--text", "[Verse 1]\nmeet me at the café\nwe didn’t stay\n")
        plain, _ = run_script("--text", "[Verse 1]\nmeet me at the cafe\nwe didn't stay\n")
        self.assertEqual([d["syllables"] for d in fancy["line_data"]], [6, 4])
        self.assertEqual(fancy["line_data"][0]["text"], "meet me at the café")
        self.assertEqual(plain["line_data"][1]["syllables"], 4)

    def test_average_keeps_one_decimal(self):
        report, _ = run_script("--text", "[Verse 1]\ncat dog\ncat dog bird\n")
        self.assertEqual(report["metrics"]["average_syllables_per_line"], 2.5)

    def test_line_without_countable_syllables_is_set_aside(self):
        # Digits, punctuation and emoji count 0: such a line must not become the minimum.
        report, _ = run_script("--text", "[Verse 1]\ncat dog\n1999\n...\n\U0001F525\U0001F525\nhello window morning\n")
        m = report["metrics"]
        self.assertEqual([d["line_number"] for d in report["line_data"]], [2, 6])
        self.assertEqual((m["min_syllables"], m["max_syllables"], m["average_syllables_per_line"]), (2, 6, 4.0))
        self.assertEqual([(d["line_number"], d["script"]) for d in report["skipped_lines"]],
                         [(3, "uncountable"), (4, "uncountable"), (5, "uncountable")])
        self.assertEqual(m["skipped_line_count"], 3)

    def test_uncountable_lines_still_count_toward_duration(self):
        with_digits, _ = run_script("--text", "[Verse 1]\ncat dog\n1999\n")
        without, _ = run_script("--text", "[Verse 1]\ncat dog\n")
        self.assertGreater(with_digits["metrics"]["estimated_duration"]["max_seconds"],
                           without["metrics"]["estimated_duration"]["max_seconds"])

    def test_cued_section_tag_starts_a_section(self):
        lyrics = "[Verse 1]\nshort line here\nanother short one\n\n[Chorus: anthemic]\nthe chorus comes in strong\n"
        report, _ = run_script("--text", lyrics)
        self.assertEqual([(s["section"], s["line_count"]) for s in report["section_analysis"]],
                         [("[Verse 1]", 2), ("[Chorus: anthemic]", 1)])

    def test_cue_tag_does_not_split_a_section(self):
        lyrics = "[Verse 1]\nshort line here\n[Harmonized]\nanother short one\n[Banana]\nand one more line\n"
        report, _ = run_script("--text", lyrics)
        self.assertEqual([(s["section"], s["line_count"]) for s in report["section_analysis"]],
                         [("[Verse 1]", 3)])

    def test_section_grouping(self):
        lyrics = (
            "[Verse 1]\n"
            "Short line here\n"
            "Another short one\n"
            "\n"
            "[Chorus]\n"
            "The chorus comes in strong and bold\n"
            "With longer lines that carry more weight\n"
        )
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        self.assertEqual(len(report["section_analysis"]), 2)
        section_names = [s["section"] for s in report["section_analysis"]]
        self.assertIn("[Verse 1]", section_names)
        self.assertIn("[Chorus]", section_names)

    def test_line_data_includes_syllables(self):
        lyrics = "[Verse 1]\nHello world\n"
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        self.assertEqual(len(report["line_data"]), 1)
        self.assertIn("syllables", report["line_data"][0])
        self.assertGreater(report["line_data"][0]["syllables"], 0)

    def test_skips_metatags(self):
        lyrics = "[Mood: haunting]\n[Verse 1]\nWalking through fog\n"
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        # Only the lyric line should be counted, not metatags
        self.assertEqual(report["metrics"]["total_lyric_lines"], 1)

    def test_high_variance_warning(self):
        lyrics = (
            "[Verse 1]\n"
            "Hi\n"
            "This is a much longer line with many more syllables than the first\n"
            "Short\n"
            "Another really long line that goes on and on and on\n"
        )
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        # Should flag high syllable variance
        issues = [f["issue"] for f in report["findings"]]
        self.assertTrue(any("variance" in i.lower() or "syllable" in i.lower() for i in issues))

    def test_report_structure(self):
        lyrics = "[Verse 1]\nA simple test line\n"
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        self.assertIn("script", report)
        self.assertIn("version", report)
        self.assertIn("timestamp", report)
        self.assertIn("status", report)
        self.assertIn("metrics", report)
        self.assertIn("line_data", report)
        self.assertIn("section_analysis", report)
        self.assertIn("findings", report)
        self.assertIn("summary", report)

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("syllable", result.stdout.lower())


class TestDurationEstimation(unittest.TestCase):
    """Test duration estimation function."""

    def test_zero_lines(self):
        min_s, max_s = estimate_duration(0, 0)
        self.assertEqual(min_s, 0)
        self.assertEqual(max_s, 0)

    def test_one_line(self):
        # 7.0 avg syllables is still the low-density range (3.5-5.5 secs/line)
        min_s, max_s = estimate_duration(1, 7.0)
        self.assertEqual(min_s, round(1 * 3.5))
        self.assertEqual(max_s, round(1 * 5.5))

    def test_low_density_song(self):
        # 20 lines at 7.0 avg syllables: the upper edge of the low-density range
        self.assertEqual(estimate_duration(20, 7.0), (70, 110))

    def test_mid_density_song(self):
        # Above 7 and up to 10 avg syllables: 3.0-4.5 secs/line
        self.assertEqual(estimate_duration(20, 9.0), (60, 90))

    def test_density_range_edges(self):
        self.assertEqual(estimate_duration(20, 7.1), (60, 90))    # just into mid
        self.assertEqual(estimate_duration(20, 10.0), (60, 90))   # top of mid
        self.assertEqual(estimate_duration(20, 10.1), (50, 80))   # just into high

    def test_high_density_faster(self):
        # High syllable density = faster delivery = less time per line
        min_s, max_s = estimate_duration(20, 12.0)
        self.assertEqual(min_s, round(20 * 2.5))  # 50
        self.assertEqual(max_s, round(20 * 4.0))  # 80

    def test_instrumental_sections_add_time(self):
        # Sections with instrumental tags add time
        sections = [
            {"name": "[Intro]", "lines": []},
            {"name": "[Verse]", "lines": [{"syllables": 7}] * 4},
            {"name": "[Guitar Solo]", "lines": []},
            {"name": "[Outro]", "lines": []},
        ]
        min_s, max_s = estimate_duration(4, 7.0, sections)
        # 4 lines at mid range + intro (5-15) + guitar solo (10-25) + outro (8-20)
        self.assertGreater(min_s, round(4 * 3.5))  # More than just lyrics
        self.assertGreater(max_s, round(4 * 5.5))

    def test_formatted_range(self):
        formatted = format_duration_range(50, 90)
        self.assertEqual(formatted, "0:50-1:30")

    def test_formatted_range_zero(self):
        formatted = format_duration_range(0, 0)
        self.assertEqual(formatted, "0:00-0:00")

    def test_formatted_range_large(self):
        formatted = format_duration_range(120, 240)
        self.assertEqual(formatted, "2:00-4:00")

    def test_duration_in_report(self):
        lyrics = (
            "[Verse 1]\n"
            "Walking through the morning light\n"
            "Counting shadows on the wall\n"
            "\n"
            "[Chorus]\n"
            "Come undone come undone\n"
            "Let the weight fall where it may\n"
        )
        report, code = run_script("--text", lyrics)
        self.assertIsNotNone(report)
        duration = report["metrics"]["estimated_duration"]
        self.assertIn("min_seconds", duration)
        self.assertIn("max_seconds", duration)
        self.assertIn("formatted", duration)
        self.assertGreater(duration["min_seconds"], 0)
        self.assertGreater(duration["max_seconds"], duration["min_seconds"])
        # Check formatted string pattern M:SS-M:SS
        self.assertIn("-", duration["formatted"])

    def test_duration_always_in_metrics(self):
        report, code = run_script("--text", "[Verse 1]\nHello world\n")
        self.assertEqual(code, 0)
        self.assertIn("estimated_duration", report["metrics"])


class TestLatinOnly(unittest.TestCase):
    MIXED = "[Verse 1]\nWalking through the fog of morning\n夜の雨が降る\nlove is 愛\nThe porch light hums"

    def test_latin_only_skips_and_lists_non_latin_lines(self):
        report, code = run_script("--text", self.MIXED, "--latin-only")
        self.assertEqual(code, 0)
        self.assertEqual([d["line_number"] for d in report["line_data"]], [2, 5])
        skipped = report["skipped_lines"]
        self.assertEqual([(d["line_number"], d["script"]) for d in skipped], [(3, "non_latin"), (4, "mixed")])
        self.assertIs(report["metrics"]["latin_only"], True)
        self.assertEqual(report["metrics"]["skipped_line_count"], 2)

    def test_skipped_lines_still_count_toward_duration(self):
        latin_only, _ = run_script("--text", self.MIXED, "--latin-only")
        latin_text = "[Verse 1]\nWalking through the fog of morning\nThe porch light hums"
        just_latin, _ = run_script("--text", latin_text)
        self.assertGreater(latin_only["metrics"]["estimated_duration"]["max_seconds"],
                           just_latin["metrics"]["estimated_duration"]["max_seconds"])

    def test_instrumental_sections_add_time(self):
        sung = "[Verse 1]\nSalt on the sill again\nthe tide came in"
        with_solo, _ = run_script("--text", "[Intro - guitar, 4 bars]\n\n" + sung + "\n\n[Guitar Solo: slide]\n\n[Outro]\n[End]")
        plain, _ = run_script("--text", sung)
        self.assertGreater(with_solo["metrics"]["estimated_duration"]["min_seconds"],
                           plain["metrics"]["estimated_duration"]["min_seconds"] + 20)

    def test_without_flag_only_a_line_with_nothing_to_count_is_skipped(self):
        report, _ = run_script("--text", self.MIXED)
        # The mixed line still counts its Latin words; the all-Japanese line counts 0
        # and is listed with its script class rather than dragging the minimum to 0.
        self.assertEqual([d["line_number"] for d in report["line_data"]], [2, 4, 5])
        self.assertEqual([(d["line_number"], d["script"]) for d in report["skipped_lines"]], [(3, "non_latin")])
        self.assertGreater(report["metrics"]["min_syllables"], 0)
        self.assertIs(report["metrics"]["latin_only"], False)

    def test_findings_exit_zero(self):
        uneven = "[Verse]\nshort\nthis is a much much longer line with many many words in it\nok\nfine"
        report, code = run_script("--text", uneven)
        self.assertTrue(report["findings"])
        self.assertEqual(code, 0)

    def test_missing_file_exits_2(self):
        _, code = run_script("/nonexistent/lyrics.txt")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
