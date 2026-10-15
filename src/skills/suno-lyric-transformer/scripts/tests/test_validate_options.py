#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for validate-options.py"""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "validate-options.py")

# The expected code -> name table (option_codes.py holds the live one).
CANONICAL_CODE_DESCRIPTIONS = {
    "ST": "Structure Tagging",
    "CE": "Chorus Extraction",
    "CC": "Chorus Creation",
    "RA": "Rhythmic Adjustment",
    "RE": "Rhyme Enhancement",
    "FR": "Full Rewrite",
    "CD": "Cliche Detection",
    "WF": "Word Fidelity Mode",
}


def _load_module():
    """Import validate-options.py as a module despite the hyphenated filename."""
    spec = importlib.util.spec_from_file_location("validate_options", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(*args):
    """Run the script and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True
    )
    return json.loads(result.stdout) if result.stdout else None, result.returncode


class TestValidateOptions(unittest.TestCase):
    def test_all_valid_codes(self):
        report, code = run_script("ST,CC,RA,CD")
        self.assertIsNotNone(report)
        self.assertEqual(report["script"], "validate-options")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(set(report["validated_codes"]), {"ST", "CC", "RA", "CD"})
        self.assertEqual(report["removed_codes"], [])

    def test_invalid_code(self):
        report, code = run_script("ST,ZZ,RA")
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "error")
        issues = [f["issue"] for f in report["findings"]]
        self.assertTrue(any("ZZ" in i for i in issues))

    def test_fr_wf_mutual_exclusion(self):
        report, code = run_script("FR,WF")
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "error")
        issues = [f["issue"] for f in report["findings"]]
        self.assertTrue(any("mutually exclusive" in i.lower() for i in issues))

    def test_fr_auto_removes_ce(self):
        report, code = run_script("FR,CE,RA")
        self.assertIsNotNone(report)
        self.assertIn("CE", report["removed_codes"])
        self.assertNotIn("CE", report["validated_codes"])
        self.assertIn("FR", report["validated_codes"])
        self.assertIn("RA", report["validated_codes"])

    def test_ce_cc_info_note(self):
        report, code = run_script("CE,CC")
        self.assertIsNotNone(report)
        issues = [f["issue"] for f in report["findings"]]
        self.assertTrue(any("CC" in i and "redundant" in i.lower() for i in issues))
        # CC should still be in validated codes (info only, not removed)
        self.assertIn("CC", report["validated_codes"])

    def test_empty_codes(self):
        report, code = run_script("--codes", "")
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "error")
        self.assertTrue(any(f["severity"] == "critical" for f in report["findings"]))

    def test_codes_flag(self):
        report, code = run_script("--codes", "ST,RA")
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(set(report["validated_codes"]), {"ST", "RA"})

    def test_duplicate_codes(self):
        report, code = run_script("ST,ST,RA")
        self.assertIsNotNone(report)
        issues = [f["issue"] for f in report["findings"]]
        self.assertTrue(any("Duplicate" in i for i in issues))
        self.assertEqual(report["validated_codes"].count("ST"), 1)

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("validate", result.stdout.lower())

    def test_report_structure(self):
        report, code = run_script("ST")
        self.assertIsNotNone(report)
        self.assertIn("script", report)
        self.assertIn("version", report)
        self.assertIn("timestamp", report)
        self.assertIn("status", report)
        self.assertIn("validated_codes", report)
        self.assertIn("removed_codes", report)
        self.assertIn("findings", report)
        self.assertIn("summary", report)

    def test_re_is_a_valid_code(self):
        # RE (Rhyme Enhancement) is part of the canonical 8-code menu; it must
        # validate cleanly rather than be reported as an invalid code.
        report, code = run_script("ST,RE,CD")
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(set(report["validated_codes"]), {"ST", "RE", "CD"})

    def test_valid_codes_come_from_the_shared_table(self):
        module = _load_module()
        self.assertEqual(module.VALID_CODES, set(CANONICAL_CODE_DESCRIPTIONS))

    def test_list_prints_menu_and_rules(self):
        report, code = run_script("--list")
        self.assertEqual(code, 0)
        self.assertEqual({o["code"]: o["name"] for o in report["options"]}, CANONICAL_CODE_DESCRIPTIONS)
        self.assertTrue(all(o["effect"] for o in report["options"]))
        self.assertEqual(len(report["rules"]), 3)

    def test_exit_codes(self):
        _, code = run_script("ST,RA")
        self.assertEqual(code, 0)
        report, code = run_script("FR,CE")  # CE auto-removed: warning, still usable
        self.assertEqual(report["status"], "warning")
        self.assertEqual(code, 0)
        _, code = run_script("FR,WF")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
