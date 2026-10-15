#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for assemble-summary.py"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "assemble-summary.py")

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


def run_script(*args):
    """Run the script and return stdout and returncode."""
    result = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    return result.stdout, result.returncode


def run_full(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


def create_test_files(tmp_path):
    """Create sample JSON input files for testing."""
    validation = {
        "script": "validate-lyrics",
        "status": "pass",
        "metrics": {
            "total_lines": 20,
            "lyric_lines": 14,
            "section_count": 4,
            "sections": ["Verse 1", "Chorus", "Verse 2", "Chorus"],
            "character_count": 600,
            "lyric_character_count": 560,
            "metatag_character_count": 40
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
            "max_syllables": 12,
            "estimated_duration": {"min_seconds": 60, "max_seconds": 75, "formatted": "1:00-1:15"}
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


def write(path, data):
    Path(path).write_text(json.dumps(data))


class TestAssembleSummary(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)
        self.val, self.syl, self.cli = create_test_files(self.tmp_path)

    def report(self, *extra, cliches=True):
        args = ["--validation", self.val, "--syllables", self.syl]
        if cliches:
            args += ["--cliches", self.cli]
        output, code = run_script(*args, *extra)
        self.assertEqual(code, 0, output)
        return json.loads(output)

    def test_json_to_stdout_by_default(self):
        report = self.report()
        self.assertEqual(report["script"], "assemble-summary")
        self.assertIn("## Transformation Summary", report["markdown"])
        self.assertEqual(report["status"], "pass")

    def test_markdown_flag_prints_block(self):
        output, code = run_script("--validation", self.val, "--syllables", self.syl,
                                  "--cliches", self.cli, "--markdown")
        self.assertEqual(code, 0)
        self.assertTrue(output.startswith("## Transformation Summary"))
        self.assertIn("Validation Status", output)

    def test_transformation_summary_matches_headless_shape(self):
        ts = self.report("--transformations", "ST,CC,RA,CD")["transformation_summary"]
        self.assertEqual(ts, {
            "sections": ["Verse 1", "Chorus", "Verse 2", "Chorus"],
            "section_count": 4,
            "estimated_duration": "1:00-1:15",
            "transformations_applied": ["ST", "CC", "RA", "CD"],
            "syllable_range": "5-12",
            "character_count": 600,
            "lyric_character_count": 560,
            "metatag_character_count": 40,
            "character_budget": "600/3000 (20%)",
        })

    def test_rendered_descriptions_match_canonical(self):
        md = self.report("--transformations", ",".join(CANONICAL_CODE_DESCRIPTIONS))["markdown"]
        for c, meaning in CANONICAL_CODE_DESCRIPTIONS.items():
            with self.subTest(code=c):
                self.assertIn(f"- {c}: {meaning}", md)

    def test_unknown_code_exits_2(self):
        result = run_full("--validation", self.val, "--syllables", self.syl, "--transformations", "ST,ZZ")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ZZ", result.stderr)

    def test_cliches_omitted_reads_not_run(self):
        report = self.report(cliches=False)
        m = report["metrics"]
        self.assertIs(m["cliche_detection_ran"], False)
        self.assertIsNone(m["total_cliches"])
        self.assertEqual(m["cliche_status"], "not run")
        self.assertIn("**Cliche Detection:** not run", report["markdown"])

    def test_cliche_categories_displayed(self):
        md = self.report()["markdown"]
        self.assertIn("2 found", md)
        self.assertIn("emotional", md)
        self.assertIn("nature", md)

    def test_syllable_range_and_duration_from_reports(self):
        report = self.report()
        self.assertIn("5-12", report["markdown"])
        self.assertIn("avg 8.0", report["markdown"])
        self.assertEqual(report["metrics"]["estimated_duration"], "1:00-1:15")

    def test_character_budget_from_validation_metrics(self):
        data = json.loads(Path(self.val).read_text())
        data["metrics"].update({"character_count": 1850, "lyric_character_count": 1640,
                                "metatag_character_count": 210})
        write(self.val, data)
        report = self.report()
        m = report["metrics"]
        self.assertEqual(m["character_budget"], "1850/3000 (62%)")
        self.assertIs(m["over_quality_budget"], False)
        self.assertIn("Lyrics 1640 + Metatags 210 = 1850/3000 (62%)", report["markdown"])

    def test_status_follows_inputs(self):
        data = json.loads(Path(self.syl).read_text())
        data["status"] = "warning"
        write(self.syl, data)
        self.assertEqual(self.report()["status"], "warning")
        data = json.loads(Path(self.val).read_text())
        data["status"] = "fail"
        write(self.val, data)
        report = self.report()
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["metrics"]["input_status"]["validation"], "fail")

    def test_missing_named_file_exits_2(self):
        missing = str(self.tmp_path / "nonexistent.json")
        for flag in ("--validation", "--syllables", "--cliches"):
            with self.subTest(flag=flag):
                args = {"--validation": self.val, "--syllables": self.syl, "--cliches": self.cli}
                args[flag] = missing
                result = run_full(*[x for kv in args.items() for x in kv])
                self.assertEqual(result.returncode, 2)
                self.assertIn("nonexistent.json", result.stderr)

    def test_unparseable_file_exits_2(self):
        Path(self.cli).write_text("not json")
        result = run_full("--validation", self.val, "--syllables", self.syl, "--cliches", self.cli)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not JSON", result.stderr)

    def test_wrong_script_report_exits_2(self):
        result = run_full("--validation", self.syl, "--syllables", self.syl)
        self.assertEqual(result.returncode, 2)
        self.assertIn("expected validate-lyrics", result.stderr)

    def test_missing_metric_exits_2(self):
        data = json.loads(Path(self.val).read_text())
        del data["metrics"]["character_count"]
        write(self.val, data)
        result = run_full("--validation", self.val, "--syllables", self.syl)
        self.assertEqual(result.returncode, 2)
        self.assertIn("character_count", result.stderr)

    def test_output_file(self):
        out_file = self.tmp_path / "out.json"
        _, code = run_script("--validation", self.val, "--syllables", self.syl, "-o", str(out_file))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out_file.read_text())["script"], "assemble-summary")

    def test_code_names_come_from_the_shared_table(self):
        module = _load_module()
        self.assertEqual(module.CODE_NAMES, CANONICAL_CODE_DESCRIPTIONS)

    def test_help_flag(self):
        result = run_full("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("assemble", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
