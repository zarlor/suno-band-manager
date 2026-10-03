#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for assemble-summary.py"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "assemble-summary.py")

# Canonical code -> meaning, mirrored from SKILL.md menu table
# (Step 2: Select Transformations). This is the source of truth; both
# assemble-summary.py and validate-options.py must agree with it.
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
    """Import assemble-summary.py as a module despite the hyphenated filename."""
    spec = importlib.util.spec_from_file_location("assemble_summary", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(*args, input_data=None):
    """Run the script and return stdout and returncode."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True,
        input=input_data
    )
    return result.stdout, result.returncode


def create_test_files(tmp_path):
    """Create sample JSON input files for testing."""
    validation = {
        "script": "validate-lyrics",
        "status": "pass",
        "metrics": {
            "total_lines": 20,
            "lyric_lines": 14,
            "section_count": 4,
            "sections": ["Verse 1", "Chorus", "Verse 2", "Chorus"]
        },
        "findings": [],
        "summary": {"total": 0}
    }

    syllables = {
        "script": "syllable-counter",
        "status": "pass",
        "metrics": {
            "total_lyric_lines": 14,
            "total_syllables": 112,
            "average_syllables_per_line": 8.0,
            "min_syllables": 5,
            "max_syllables": 12
        },
        "findings": [],
        "summary": {"total": 0}
    }

    cliches = {
        "script": "cliche-detector",
        "status": "pass",
        "metrics": {
            "total_cliches_found": 2,
            "categories": {"emotional": 1, "nature": 1}
        },
        "findings": [],
        "summary": {"total": 2}
    }

    val_file = tmp_path / "validation.json"
    syl_file = tmp_path / "syllables.json"
    cli_file = tmp_path / "cliches.json"

    val_file.write_text(json.dumps(validation))
    syl_file.write_text(json.dumps(syllables))
    cli_file.write_text(json.dumps(cliches))

    return str(val_file), str(syl_file), str(cli_file)


class TestAssembleSummary:
    def test_basic_assembly(self, tmp_path):
        val, syl, cli = create_test_files(tmp_path)
        output, code = run_script("--validation", val, "--syllables", syl, "--cliches", cli)
        assert code == 0
        assert "Transformation Summary" in output
        assert "Validation Status" in output
        assert "Sections:" in output

    def test_with_transformations(self, tmp_path):
        val, syl, cli = create_test_files(tmp_path)
        output, code = run_script(
            "--validation", val, "--syllables", syl, "--cliches", cli,
            "--transformations", "ST,CC,RA"
        )
        assert code == 0
        assert "Transformations Applied" in output
        assert "ST:" in output
        assert "CC:" in output
        assert "RA:" in output

    def test_rendered_descriptions_match_canonical(self, tmp_path):
        # Each applied code must render with its canonical SKILL.md meaning.
        val, syl, cli = create_test_files(tmp_path)
        all_codes = ",".join(CANONICAL_CODE_DESCRIPTIONS)
        output, code = run_script(
            "--validation", val, "--syllables", syl, "--cliches", cli,
            "--transformations", all_codes
        )
        assert code == 0
        for c, meaning in CANONICAL_CODE_DESCRIPTIONS.items():
            assert f"- {c}: {meaning}" in output

    def test_code_descriptions_match_canonical(self):
        # Guard against silent drift: assemble-summary.py CODE_DESCRIPTIONS must
        # match the canonical SKILL.md menu-table mapping exactly.
        module = _load_module()
        assert module.CODE_DESCRIPTIONS == CANONICAL_CODE_DESCRIPTIONS

    def test_skill_menu_table_matches_canonical(self):
        # The SKILL.md Step 2 menu table is the human-facing source of truth.
        import re
        skill = (Path(__file__).parent.parent.parent / "SKILL.md").read_text()
        rows = dict(re.findall(r"^\| ([A-Z]{2}) \| ([^|]+?) \|", skill, re.MULTILINE))
        assert rows == CANONICAL_CODE_DESCRIPTIONS

    def test_json_output(self, tmp_path):
        val, syl, cli = create_test_files(tmp_path)
        out_file = tmp_path / "output.json"
        output, code = run_script(
            "--validation", val, "--syllables", syl, "--cliches", cli,
            "-o", str(out_file)
        )
        assert code == 0
        report = json.loads(out_file.read_text())
        assert report["script"] == "assemble-summary"
        assert "metrics" in report
        assert "markdown" in report

    def test_markdown_output_file(self, tmp_path):
        val, syl, cli = create_test_files(tmp_path)
        out_file = tmp_path / "output.md"
        output, code = run_script(
            "--validation", val, "--syllables", syl, "--cliches", cli,
            "-o", str(out_file)
        )
        assert code == 0
        content = out_file.read_text()
        assert "## Transformation Summary" in content

    def test_cliche_categories_displayed(self, tmp_path):
        val, syl, cli = create_test_files(tmp_path)
        output, code = run_script("--validation", val, "--syllables", syl, "--cliches", cli)
        assert code == 0
        assert "2 found" in output
        assert "emotional" in output
        assert "nature" in output

    def test_syllable_range_displayed(self, tmp_path):
        val, syl, cli = create_test_files(tmp_path)
        output, code = run_script("--validation", val, "--syllables", syl, "--cliches", cli)
        assert code == 0
        assert "5-12" in output
        assert "avg 8.0" in output

    def test_estimated_duration(self, tmp_path):
        val, syl, cli = create_test_files(tmp_path)
        output, code = run_script("--validation", val, "--syllables", syl, "--cliches", cli)
        assert code == 0
        # 4 sections * 15 sec = 60 sec = 1:00
        assert "1:00" in output

    def test_character_budget_from_validation_metrics(self, tmp_path):
        val, syl, cli = create_test_files(tmp_path)
        data = json.loads(Path(val).read_text())
        data["metrics"].update({"character_count": 1850, "lyric_character_count": 1640,
                                "metatag_character_count": 210})
        Path(val).write_text(json.dumps(data))
        out_file = tmp_path / "out.json"
        _, code = run_script("--validation", val, "--syllables", syl, "--cliches", cli, "-o", str(out_file))
        assert code == 0
        report = json.loads(out_file.read_text())
        m = report["metrics"]
        assert m["character_budget"] == "1850/3000 (62%)"
        assert m["lyric_character_count"] == 1640
        assert m["metatag_character_count"] == 210
        assert m["over_quality_budget"] is False
        assert "Lyrics 1640 + Metatags 210 = 1850/3000 (62%)" in report["markdown"]

    def test_duration_prefers_syllable_counter_range(self, tmp_path):
        val, syl, cli = create_test_files(tmp_path)
        data = json.loads(Path(syl).read_text())
        data["metrics"]["estimated_duration"] = {"min_seconds": 165, "max_seconds": 210,
                                                 "formatted": "2:45-3:30"}
        Path(syl).write_text(json.dumps(data))
        output, code = run_script("--validation", val, "--syllables", syl, "--cliches", cli)
        assert code == 0
        assert "2:45-3:30" in output

    def test_missing_files_handled(self, tmp_path):
        missing = str(tmp_path / "nonexistent.json")
        output, code = run_script(
            "--validation", missing, "--syllables", missing, "--cliches", missing
        )
        assert code == 2

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "assemble" in result.stdout.lower()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
