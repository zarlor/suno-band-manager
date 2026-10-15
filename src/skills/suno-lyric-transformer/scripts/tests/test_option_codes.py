#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for option_codes.py, the shared option-code table."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import option_codes  # noqa: E402


class TestOptionCodes(unittest.TestCase):
    def test_eight_codes_in_menu_order(self):
        self.assertEqual(list(option_codes.OPTION_CODES), ["ST", "CE", "CC", "RA", "RE", "FR", "CD", "WF"])

    def test_code_names_derive_from_table(self):
        for code, (name, effect) in option_codes.OPTION_CODES.items():
            with self.subTest(code=code):
                self.assertEqual(option_codes.CODE_NAMES[code], name)
                self.assertTrue(effect)

    def test_menu_rows(self):
        rows = option_codes.menu()
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0], {"code": "ST", "name": "Structure Tagging",
                                   "effect": "Section tags on the arc, sparse descriptors"})

    def test_rules_present(self):
        self.assertEqual(len(option_codes.RULES), 3)


if __name__ == "__main__":
    unittest.main()
