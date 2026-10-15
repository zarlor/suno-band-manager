#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for the shared script classifier."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from script_class import (  # noqa: E402
    LATIN, MIXED, NON_LATIN, NONE, TAG_ONLY_LINE, classify_script, latin_checkable,
)


class TestClassifyScript(unittest.TestCase):
    def test_english_is_latin(self):
        self.assertEqual(classify_script("Walking through the fog"), LATIN)

    def test_accented_latin_is_latin(self):
        self.assertEqual(classify_script("Café à la française, señor"), LATIN)

    def test_cyrillic_is_non_latin(self):
        self.assertEqual(classify_script("Привет, мир"), NON_LATIN)

    def test_japanese_is_non_latin(self):
        self.assertEqual(classify_script("夜の雨が降る"), NON_LATIN)

    def test_both_scripts_is_mixed(self):
        self.assertEqual(classify_script("love is 愛"), MIXED)

    def test_no_letters_is_none(self):
        self.assertEqual(classify_script("... 123 !!"), NONE)
        self.assertEqual(classify_script(""), NONE)

    def test_latin_checkable(self):
        self.assertTrue(latin_checkable("plain English line"))
        self.assertTrue(latin_checkable("--- 42"))
        self.assertFalse(latin_checkable("Привет"))
        self.assertFalse(latin_checkable("hello 世界"))

    def test_tag_only_line(self):
        self.assertTrue(TAG_ONLY_LINE.match("  [Verse 1]  "))
        self.assertFalse(TAG_ONLY_LINE.match("[Verse 1] words"))


if __name__ == "__main__":
    unittest.main()
