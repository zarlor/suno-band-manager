#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for map-adjustments.py"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "map-adjustments.py")


def run_script(input_data: dict | str | None = None, extra_args: list[str] | None = None) -> tuple[int, dict]:
    """Run map-adjustments.py with stdin input and return (exit_code, parsed_json)."""
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


def run_check_final(style: str, exclude: str = "") -> tuple[int, dict]:
    result = subprocess.run([sys.executable, SCRIPT, "--check-final", "--style-prompt", style, "--exclude", exclude],
                            capture_output=True, text=True)
    return result.returncode, json.loads(result.stdout)


class MapAdjustmentsTest(unittest.TestCase):
    def test_single_dimension(self):
        """Single dimension should produce relevant adjustments."""
        data = {"dimensions": [{"dimension": "vocals", "direction": "too_polished"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "pass")
        adj = output["adjustments"]
        self.assertIn("raw vocal", adj["style_prompt"]["add_descriptors"])
        self.assertTrue(any("polished" in p for p in adj["style_prompt"]["remove_patterns"]))

    def test_multiple_dimensions(self):
        """Multiple dimensions should combine adjustments."""
        data = {
            "dimensions": [
                {"dimension": "vocals", "direction": "too_polished"},
                {"dimension": "energy", "direction": "too_low"},
            ]
        }
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        # Should have vocal adjustments
        self.assertIn("raw vocal", adj["style_prompt"]["add_descriptors"])
        # Should have energy adjustments
        self.assertIn("high energy", adj["style_prompt"]["add_descriptors"])

    def test_slider_adjustments_paid_tier(self):
        """Paid tier should get direct slider recommendations."""
        data = {
            "dimensions": [{"dimension": "vibe", "direction": "too_generic"}],
            "tier": "pro",
        }
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("sliders", adj)
        self.assertIn("weirdness", adj["sliders"])
        self.assertNotIn("note", adj["sliders"])  # No "not available" note for paid tier

    def test_slider_adjustments_free_tier(self):
        """Free tier should get slider note about unavailability."""
        data = {
            "dimensions": [{"dimension": "vibe", "direction": "too_generic"}],
            "tier": "free",
        }
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("sliders", adj)
        self.assertIn("note", adj["sliders"])  # Should have unavailability note
        self.assertIn("recommended_if_upgraded", adj["sliders"])

    def test_lyric_changes(self):
        """Structure dimensions should produce lyric change recommendations."""
        data = {"dimensions": [{"dimension": "structure", "direction": "needs_bridge"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("lyrics", adj)
        self.assertGreater(len(adj["lyrics"]["changes"]), 0)
        self.assertIn("Bridge", adj["lyrics"]["changes"][0])

    def test_unknown_dimension(self):
        """Unknown dimension should produce a note, not fail."""
        data = {"dimensions": [{"dimension": "color", "direction": "too_blue"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("notes", adj)
        self.assertTrue(any("Unknown dimension" in n for n in adj["notes"]))

    def test_unknown_direction(self):
        """Unknown direction for valid dimension should produce a note."""
        data = {"dimensions": [{"dimension": "vocals", "direction": "too_purple"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("notes", adj)
        self.assertTrue(any("Unknown direction" in n for n in adj["notes"]))

    def test_deduplication(self):
        """Duplicate descriptors should be deduped."""
        data = {
            "dimensions": [
                {"dimension": "energy", "direction": "too_low"},
                {"dimension": "energy", "direction": "too_low"},
            ]
        }
        code, output = run_script(data)
        self.assertEqual(code, 0)
        add_descs = output["adjustments"]["style_prompt"]["add_descriptors"]
        self.assertEqual(len(add_descs), len(set(add_descs)), "Descriptors should be deduped")

    def test_missing_dimensions_field(self):
        """Missing dimensions should fail."""
        code, output = run_script({"tier": "pro"})
        self.assertEqual(code, 1)
        self.assertEqual(output["status"], "fail")

    def test_invalid_json(self):
        """Invalid JSON should fail."""
        code, output = run_script("not json")
        self.assertEqual(code, 1)
        self.assertEqual(output["status"], "fail")

    def test_empty_dimensions(self):
        """Empty dimensions array should pass with empty adjustments."""
        data = {"dimensions": []}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertEqual(adj["style_prompt"]["add_descriptors"], [])
        self.assertEqual(adj["style_prompt"]["remove_patterns"], [])

    def test_exclusion_generation(self):
        """Dimensions with exclusion recommendations should populate exclusions."""
        data = {"dimensions": [{"dimension": "instrumentation", "direction": "too_much"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertGreater(len(adj["exclusions"]["add"]), 0)

    def test_dimension_with_note(self):
        """Dimensions that need further clarification should include notes."""
        data = {"dimensions": [{"dimension": "music", "direction": "general_issue"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("notes", adj)
        self.assertTrue(any("further narrowing" in n.lower() for n in adj["notes"]))

    def test_quality_robotic_vocals(self):
        """Quality dimension robotic_vocals should produce style and exclusion adjustments."""
        data = {"dimensions": [{"dimension": "quality", "direction": "robotic_vocals"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("natural vocal", adj["style_prompt"]["add_descriptors"])
        self.assertIn("no auto-tune", adj["exclusions"]["add"])

    def test_quality_clipping(self):
        """Quality dimension clipping should add clean mix descriptors and remove heavy patterns."""
        data = {"dimensions": [{"dimension": "quality", "direction": "clipping"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("clean mix", adj["style_prompt"]["add_descriptors"])
        self.assertIn("heavy", adj["style_prompt"]["remove_patterns"])

    def test_quality_muffled(self):
        """Quality dimension muffled should add crisp descriptors."""
        data = {"dimensions": [{"dimension": "quality", "direction": "muffled"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("crisp", adj["style_prompt"]["add_descriptors"])
        self.assertIn("lo-fi", adj["style_prompt"]["remove_patterns"])

    def test_quality_artifacts_note(self):
        """Quality dimension artifacts should produce a note about regeneration."""
        data = {"dimensions": [{"dimension": "quality", "direction": "artifacts"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("notes", adj)
        self.assertTrue(any("regenerate" in n.lower() for n in adj["notes"]))

    def test_length_too_short(self):
        """Length dimension too_short should produce lyric change recommendations."""
        data = {"dimensions": [{"dimension": "length", "direction": "too_short"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("lyrics", adj)
        self.assertTrue(any("extend" in c.lower() or "add sections" in c.lower() for c in adj["lyrics"]["changes"]))

    def test_length_outro_cuts_off(self):
        """Length dimension outro_cuts_off should recommend Outro and Fade Out."""
        data = {"dimensions": [{"dimension": "length", "direction": "outro_cuts_off"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("lyrics", adj)
        self.assertTrue(any("Outro" in c for c in adj["lyrics"]["changes"]))

    def test_length_pacing_drags(self):
        """Length dimension pacing_drags should recommend energy metatags."""
        data = {"dimensions": [{"dimension": "length", "direction": "pacing_drags"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("lyrics", adj)
        self.assertTrue(any("Energy" in c or "Build-Up" in c for c in adj["lyrics"]["changes"]))

    def test_consistency_check_no_conflicts(self):
        """Clean adjustments should produce no consistency warnings."""
        data = {"dimensions": [{"dimension": "vocals", "direction": "too_polished"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertNotIn("consistency_warnings", adj)

    def test_consistency_check_add_remove_conflict(self):
        """Conflicting add/remove should produce a consistency warning."""
        # instrumentation too_little adds "lush arrangement" etc. but also combine with
        # production too_polished which adds "lo-fi" and removes "crisp", "polished"
        # We need a case where add and remove overlap. Let's use energy too_high (adds "gentle", "soft")
        # combined with energy too_low (adds "high energy" and removes "gentle", "soft")
        data = {
            "dimensions": [
                {"dimension": "energy", "direction": "too_high"},
                {"dimension": "energy", "direction": "too_low"},
            ]
        }
        code, output = run_script(data)
        self.assertEqual(code, 0)
        adj = output["adjustments"]
        self.assertIn("consistency_warnings", adj)
        conflict_types = [w["type"] for w in adj["consistency_warnings"]]
        self.assertIn("add_remove_conflict", conflict_types)

    def test_style_prompt_overflow_v4_pro(self):
        """A long style prompt under v4 Pro's 200-char limit triggers an overflow warning."""
        long_prompt = "warm indie rock, " * 20  # ~340 chars, well over 200
        data = {"dimensions": [{"dimension": "vocals", "direction": "too_polished"}]}
        code, output = run_script(
            data, extra_args=["--style-prompt", long_prompt, "--model", "v4 Pro"]
        )
        self.assertEqual(code, 0)
        warnings = output["adjustments"].get("consistency_warnings", [])
        overflow = [w for w in warnings if w["type"] == "style_prompt_overflow"]
        self.assertTrue(overflow, "Expected a style_prompt_overflow warning for v4 Pro")
        self.assertEqual(overflow[0]["limit"], 200)

    def test_style_prompt_no_overflow_default_model(self):
        """The same long prompt is under the 1000-char default limit for other models."""
        long_prompt = "warm indie rock, " * 20  # ~340 chars, under 1000
        data = {"dimensions": [{"dimension": "vocals", "direction": "too_polished"}]}
        code, output = run_script(
            data, extra_args=["--style-prompt", long_prompt, "--model", "v5 Pro"]
        )
        self.assertEqual(code, 0)
        warnings = output["adjustments"].get("consistency_warnings", [])
        self.assertFalse([w for w in warnings if w["type"] == "style_prompt_overflow"])

    def test_style_prompt_overflow_from_json_keys(self):
        """Overflow validation also reads original_style_prompt/model from the input JSON."""
        long_prompt = "x" * 250
        data = {
            "dimensions": [{"dimension": "vocals", "direction": "too_polished"}],
            "original_style_prompt": long_prompt,
            "model": "v4 Pro",
        }
        code, output = run_script(data)
        self.assertEqual(code, 0)
        warnings = output["adjustments"].get("consistency_warnings", [])
        self.assertTrue([w for w in warnings if w["type"] == "style_prompt_overflow"])

    def test_no_style_prompt_no_overflow_check(self):
        """Without a style prompt, no overflow warning is produced."""
        data = {"dimensions": [{"dimension": "vocals", "direction": "too_polished"}]}
        code, output = run_script(data)
        self.assertEqual(code, 0)
        warnings = output["adjustments"].get("consistency_warnings", [])
        self.assertFalse([w for w in warnings if w["type"] == "style_prompt_overflow"])


class CheckFinalTest(unittest.TestCase):
    def test_check_final_flags_descriptor_cancelled_by_exclusion(self):
        code, out = run_check_final("raw indie rock, spacious reverb, dry vocal", "no reverb, no autotune")
        self.assertEqual(code, 0)
        self.assertEqual(out["mode"], "check-final")
        self.assertEqual(out["status"], "warning")
        self.assertEqual([w["type"] for w in out["consistency_warnings"]], ["add_exclude_conflict"])
        self.assertIn("spacious reverb", out["consistency_warnings"][0]["detail"])

    def test_check_final_clean_package_passes(self):
        code, out = run_check_final("raw indie rock, dry vocal, close mic", "no autotune, no synth pads")
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "pass")
        self.assertEqual(out["consistency_warnings"], [])

    def test_check_final_ignores_empty_items(self):
        code, out = run_check_final("raw indie rock, , dry vocal", "no autotune,,")
        self.assertEqual(out["status"], "pass")

    def test_check_final_requires_style_prompt(self):
        result = subprocess.run([sys.executable, SCRIPT, "--check-final"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs --style-prompt", result.stderr)


if __name__ == "__main__":
    unittest.main()
