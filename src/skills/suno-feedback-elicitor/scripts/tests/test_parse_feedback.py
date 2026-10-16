#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for parse-feedback.py"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "parse-feedback.py")


def run_script(input_data: dict | str | None = None, extra_args: list[str] | None = None) -> tuple[int, dict]:
    """Run parse-feedback.py with stdin input and return (exit_code, parsed_json)."""
    cmd = [sys.executable, SCRIPT, "--stdin"]
    if extra_args:
        cmd.extend(extra_args)

    input_str = json.dumps(input_data) if isinstance(input_data, dict) else (input_data or "")
    result = subprocess.run(cmd, input=input_str, capture_output=True, text=True)
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        output = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, output


def run_flags(args: list[str]) -> tuple[int, dict]:
    """Run parse-feedback.py with the skill's headless flags (no stdin)."""
    result = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    try:
        return result.returncode, json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.returncode, {"raw_stdout": result.stdout, "raw_stderr": result.stderr}


class ParseFeedbackStdinTest(unittest.TestCase):
    def test_valid_minimal_input(self):
        """Minimal valid input: just feedback_text."""
        code, output = run_script({"feedback_text": "The guitar is too loud"})
        self.assertEqual(code, 0, f"Expected exit 0, got {code}: {output}")
        self.assertEqual(output["status"], "pass")
        self.assertEqual(output["parsed"]["feedback_text"], "The guitar is too loud")
        self.assertEqual(output["summary"]["total"], 0)

    def test_valid_full_input(self):
        """Full valid input with all optional fields."""
        data = {
            "feedback_text": "It feels too polished",
            "original_style_prompt": "indie folk, acoustic, warm",
            "original_lyrics": "[Verse]\nSome lyrics here",
            "band_profile": "midnight-wanderers",
            "model": "v5 Pro",
            "slider_settings": {"weirdness": 45, "style_influence": 60},
            "intent": "I wanted a raw, intimate feel",
            "feedback_type": "clear",
            "dimensions": ["production", "vocals"],
        }
        code, output = run_script(data)
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "pass")
        self.assertEqual(output["parsed"]["context"]["model"], "v5 Pro")
        self.assertEqual(output["parsed"]["context"]["band_profile"], "midnight-wanderers")
        self.assertEqual(output["parsed"]["pre_categorized"]["feedback_type"], "clear")
        self.assertEqual(output["parsed"]["pre_categorized"]["dimensions"], ["production", "vocals"])

    def test_missing_feedback_text(self):
        """Missing feedback_text should fail."""
        code, output = run_script({"model": "v5 Pro"})
        self.assertEqual(code, 1)
        self.assertEqual(output["status"], "fail")
        self.assertGreaterEqual(output["summary"]["critical"], 1)

    def test_empty_feedback_text(self):
        """Empty feedback_text should fail."""
        code, output = run_script({"feedback_text": "   "})
        self.assertEqual(code, 1)
        self.assertEqual(output["status"], "fail")
        self.assertGreaterEqual(output["summary"]["critical"], 1)

    def test_unrecognized_model_info(self):
        """Unrecognized model should produce an info finding and still pass."""
        code, output = run_script({"feedback_text": "Sounds off", "model": "v99 Ultra"})
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "pass",
                         f"Expected pass (info-only findings), got {output['status']}")
        info_findings = [f for f in output["findings"] if f["severity"] == "info"]
        self.assertGreaterEqual(len(info_findings), 1)
        self.assertIn("Unrecognized model", info_findings[0]["issue"])
        self.assertIn("informational", info_findings[0]["fix"])

    def test_invalid_dimension(self):
        """Invalid dimension should produce a low-severity finding but pass."""
        code, output = run_script({"feedback_text": "Too bright", "dimensions": ["brightness"]})
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "warning")
        self.assertGreaterEqual(output["summary"]["low"], 1)

    def test_invalid_feedback_type(self):
        """Invalid feedback_type should produce a warning."""
        code, output = run_script({"feedback_text": "Hmm", "feedback_type": "confused"})
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "warning")

    def test_invalid_slider_range(self):
        """Slider value out of range should warn."""
        code, output = run_script({
            "feedback_text": "Off",
            "slider_settings": {"weirdness": 150},
        })
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "warning")
        self.assertGreaterEqual(output["summary"]["medium"], 1)

    def test_invalid_json_input(self):
        """Non-JSON input should fail."""
        code, output = run_script("this is not json")
        self.assertEqual(code, 1)
        self.assertEqual(output["status"], "fail")

    def test_non_object_json(self):
        """JSON array (not object) should fail."""
        cmd = [sys.executable, SCRIPT, "--stdin"]
        result = subprocess.run(cmd, input="[1, 2, 3]", capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "fail")

    def test_dimensions_not_array(self):
        """dimensions as non-array should produce high severity finding."""
        code, output = run_script({"feedback_text": "Bad", "dimensions": "vocals"})
        self.assertEqual(code, 1)
        self.assertEqual(output["status"], "fail")
        self.assertGreaterEqual(output["summary"]["high"], 1)

    def test_empty_context_stripped(self):
        """Empty optional context fields should be stripped from output."""
        code, output = run_script({"feedback_text": "Good stuff"})
        self.assertEqual(code, 0)
        # Context should only have non-empty fields
        self.assertNotIn("model", output["parsed"]["context"])
        self.assertNotIn("band_profile", output["parsed"]["context"])

    def test_technical_feedback_type(self):
        """'technical' should be a valid feedback type."""
        code, output = run_script({"feedback_text": "There are artifacts", "feedback_type": "technical"})
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "pass")
        self.assertEqual(output["summary"]["total"], 0)

    def test_length_dimension_valid(self):
        """'length' should be a valid dimension."""
        code, output = run_script({"feedback_text": "Song is too short", "dimensions": ["length"]})
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "pass")
        self.assertEqual(output["summary"]["low"], 0)

    def test_quality_dimension_valid(self):
        """'quality' should be a valid dimension."""
        code, output = run_script({"feedback_text": "Audio has clipping", "dimensions": ["quality"]})
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "pass")
        self.assertEqual(output["summary"]["low"], 0)

    def test_unrecognized_model_passes_through(self):
        """Unrecognized model should still appear in parsed output context."""
        code, output = run_script({"feedback_text": "Test", "model": "v99 Ultra"})
        self.assertEqual(code, 0)
        self.assertEqual(output["parsed"]["context"]["model"], "v99 Ultra")


class ParseFeedbackFlagsTest(unittest.TestCase):
    def test_skill_route_flags_are_accepted_and_ignored(self):
        for flag in ("--headless", "-H", "--headless:analyze"):
            code, out = run_flags([flag, "--feedback", "the vocals are buried", "--no-write"])
            self.assertEqual(code, 0, (flag, out))

    def test_other_unknown_flags_still_fail(self):
        code, out = run_flags(["--feedback", "x", "--bogus"])
        self.assertNotEqual(code, 0)

    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp_path = Path(td.name)

    def test_flags_translate_to_json_keys(self):
        """Headless flags map onto the script's JSON keys; --lyrics is read from the file."""
        lyrics = self.tmp_path / "lyrics.txt"
        lyrics.write_text("[Verse]\nline one\n", encoding="utf-8")
        log = self.tmp_path / "song.md"
        log.write_text("## Round 1\n", encoding="utf-8")
        code, out = run_flags([
            "--feedback", "vocals too polished", "--style-prompt", "warm indie rock", "--model", "v6",
            "--sliders", '{"weirdness": 55, "style_influence": 70}', "--lyrics", str(lyrics),
            "--band-profile", "test-band", "--iteration-log", str(log), "--title", "My Song", "--no-write",
        ])
        self.assertEqual(code, 0, out)
        ctx = out["parsed"]["context"]
        self.assertEqual(out["parsed"]["feedback_text"], "vocals too polished")
        self.assertEqual(ctx["original_style_prompt"], "warm indie rock")
        self.assertEqual(ctx["model"], "v6")
        self.assertEqual(ctx["slider_settings"], {"weirdness": 55, "style_influence": 70})
        self.assertEqual(ctx["original_lyrics"], "[Verse]\nline one\n")
        self.assertEqual(ctx["band_profile"], "test-band")
        self.assertEqual(ctx["iteration_log_path"], str(log))
        self.assertEqual(ctx["title"], "My Song")
        self.assertIs(out["parsed"]["write"], False)
        self.assertTrue("pre_categorized" not in out["parsed"] or out["parsed"]["pre_categorized"] == {})

    def test_feedback_flag_accepts_json_with_pre_categorization(self):
        code, out = run_flags(["--feedback",
                               '{"feedback": "too busy", "feedback_type": "clear", "dimensions": ["instrumentation"]}'])
        self.assertEqual(code, 0, out)
        self.assertEqual(out["parsed"]["feedback_text"], "too busy")
        self.assertEqual(out["parsed"]["pre_categorized"], {"feedback_type": "clear", "dimensions": ["instrumentation"]})
        self.assertIs(out["parsed"]["write"], True)

    def test_missing_lyrics_file_fails_cleanly(self):
        code, out = run_flags(["--feedback", "too loud", "--lyrics", str(self.tmp_path / "nope.txt")])
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "fail")
        self.assertIn("--lyrics", out["findings"][0]["issue"])

    def test_bad_sliders_json_fails_cleanly(self):
        code, out = run_flags(["--feedback", "too loud", "--sliders", "{weirdness: 50"])
        self.assertEqual(code, 1)
        self.assertIn("--sliders", out["findings"][0]["issue"])

    def test_context_flag_without_feedback_is_rejected(self):
        result = subprocess.run([sys.executable, SCRIPT, "--stdin", "--model", "v6"], input="{}",
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs --feedback", result.stderr)


if __name__ == "__main__":
    unittest.main()
