#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for validate-options.py"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "validate-options.py")

# Canonical code -> meaning, mirrored from SKILL.md "Full menu" table
# (Step 2: Select Transformations). This is the source of truth; both
# validate-options.py and assemble-summary.py must agree with it.
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


class TestValidateOptions:
    def test_all_valid_codes(self):
        report, code = run_script("ST,CC,RA,CD")
        assert report is not None
        assert report["script"] == "validate-options"
        assert report["status"] == "pass"
        assert set(report["validated_codes"]) == {"ST", "CC", "RA", "CD"}
        assert report["removed_codes"] == []

    def test_invalid_code(self):
        report, code = run_script("ST,ZZ,RA")
        assert report is not None
        assert report["status"] == "error"
        issues = [f["issue"] for f in report["findings"]]
        assert any("ZZ" in i for i in issues)

    def test_fr_wf_mutual_exclusion(self):
        report, code = run_script("FR,WF")
        assert report is not None
        assert report["status"] == "error"
        issues = [f["issue"] for f in report["findings"]]
        assert any("mutually exclusive" in i.lower() for i in issues)

    def test_fr_auto_removes_ce(self):
        report, code = run_script("FR,CE,RA")
        assert report is not None
        assert "CE" in report["removed_codes"]
        assert "CE" not in report["validated_codes"]
        assert "FR" in report["validated_codes"]
        assert "RA" in report["validated_codes"]

    def test_ce_cc_info_note(self):
        report, code = run_script("CE,CC")
        assert report is not None
        issues = [f["issue"] for f in report["findings"]]
        assert any("CC" in i and "redundant" in i.lower() for i in issues)
        # CC should still be in validated codes (info only, not removed)
        assert "CC" in report["validated_codes"]

    def test_empty_codes(self):
        report, code = run_script("--codes", "")
        assert report is not None
        assert report["status"] == "error"
        assert any(f["severity"] == "critical" for f in report["findings"])

    def test_codes_flag(self):
        report, code = run_script("--codes", "ST,RA")
        assert report is not None
        assert report["status"] == "pass"
        assert set(report["validated_codes"]) == {"ST", "RA"}

    def test_duplicate_codes(self):
        report, code = run_script("ST,ST,RA")
        assert report is not None
        issues = [f["issue"] for f in report["findings"]]
        assert any("Duplicate" in i for i in issues)
        assert report["validated_codes"].count("ST") == 1

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "validate" in result.stdout.lower()

    def test_report_structure(self):
        report, code = run_script("ST")
        assert report is not None
        assert "script" in report
        assert "version" in report
        assert "timestamp" in report
        assert "status" in report
        assert "validated_codes" in report
        assert "removed_codes" in report
        assert "findings" in report
        assert "summary" in report

    def test_re_is_a_valid_code(self):
        # RE (Rhyme Enhancement) is part of the canonical 8-code menu; it must
        # validate cleanly rather than be reported as an invalid code.
        report, code = run_script("ST,RE,CD")
        assert report is not None
        assert report["status"] == "pass"
        assert set(report["validated_codes"]) == {"ST", "RE", "CD"}

    def test_code_descriptions_match_canonical(self):
        # Guard against silent drift: validate-options.py CODE_DESCRIPTIONS must
        # match the canonical SKILL.md "Full menu" mapping exactly.
        module = _load_module()
        assert module.CODE_DESCRIPTIONS == CANONICAL_CODE_DESCRIPTIONS

    def test_valid_codes_match_canonical_keys(self):
        # The set of accepted codes must be exactly the canonical menu codes.
        module = _load_module()
        assert module.VALID_CODES == set(CANONICAL_CODE_DESCRIPTIONS)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
