#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Tests for validate-prompt.py"""

import builtins
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Load the script as a module
SCRIPT_PATH = Path(__file__).parent.parent / "validate-prompt.py"
spec = importlib.util.spec_from_file_location("validate_prompt", SCRIPT_PATH)
validate_prompt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_prompt)


def _tmp_path(test):
    """A temporary directory removed when the test finishes (pytest tmp_path stand-in)."""
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    return Path(tmp.name)


class TestValidateStylePrompt(unittest.TestCase):
    """Tests for style prompt validation."""

    def test_valid_prompt_passes(self):
        """A well-formed prompt under the limit should pass."""
        prompt = "indie folk-rock, melancholic warmth, acoustic guitar over ambient pads, breathy male vocal, intimate lo-fi mix"
        findings = validate_prompt.validate_style_prompt(prompt)
        critical = [f for f in findings if f["severity"] == "critical"]
        self.assertEqual(len(critical), 0)

    def test_over_1000_chars_is_critical(self):
        """Prompts over 1,000 chars should produce a critical finding."""
        prompt = "rock, " * 200  # ~1200 chars
        findings = validate_prompt.validate_style_prompt(prompt)
        critical = [f for f in findings if f["severity"] == "critical"]
        self.assertEqual(len(critical), 1)
        self.assertIn("1,000", critical[0]["issue"])

    def test_v4_pro_200_char_limit(self):
        """v4 Pro should have a 200-char limit, not 1,000."""
        prompt = "rock, warm vocals, gentle acoustic guitar, melancholic mood, wide stereo field, intimate mix, layered harmonies, subtle percussion" * 2
        self.assertGreater(len(prompt), 200)
        self.assertLess(len(prompt), 1000)
        findings = validate_prompt.validate_style_prompt(prompt, model="v4 Pro")
        critical = [f for f in findings if f["severity"] == "critical"]
        self.assertEqual(len(critical), 1)
        self.assertIn("200", critical[0]["issue"])
        self.assertIn("v4 Pro", critical[0]["issue"])

    def test_v5_pro_uses_1000_limit(self):
        """v5 Pro should use 1,000-char limit."""
        prompt = "rock " + "x" * 300
        findings = validate_prompt.validate_style_prompt(prompt, model="v5 Pro")
        critical = [f for f in findings if f["severity"] == "critical"]
        self.assertEqual(len(critical), 0)

    def test_critical_zone_warning(self):
        """Prompts with substantial content beyond 200 chars should warn about critical zone."""
        prompt = "rock, warm vocals, " + "x" * 350
        findings = validate_prompt.validate_style_prompt(prompt)
        zone_warnings = [f for f in findings if "critical zone" in f.get("issue", "").lower()]
        self.assertEqual(len(zone_warnings), 1)

    def test_near_limit_is_low(self):
        """Prompts at 90-100% of limit should produce a low finding."""
        prompt = "x" * 950
        # Add a genre keyword to avoid the front-loading warning
        prompt = "rock " + "x" * 945
        findings = validate_prompt.validate_style_prompt(prompt)
        low = [f for f in findings if f["severity"] == "low" and "near" in f.get("issue", "").lower()]
        self.assertEqual(len(low), 1)

    def test_empty_prompt_is_critical(self):
        """Empty prompts should be critical."""
        findings = validate_prompt.validate_style_prompt("")
        critical = [f for f in findings if f["severity"] == "critical"]
        self.assertEqual(len(critical), 1)

    def test_whitespace_only_is_critical(self):
        """Whitespace-only prompts should be critical."""
        findings = validate_prompt.validate_style_prompt("   \n  ")
        critical = [f for f in findings if f["severity"] == "critical"]
        self.assertEqual(len(critical), 1)

    def test_no_genre_frontloading_warning(self):
        """Prompts without genre in first 200 chars should warn."""
        prompt = "warm and beautiful with layered textures and organic feel throughout the production"
        findings = validate_prompt.validate_style_prompt(prompt)
        medium = [f for f in findings if f["severity"] == "medium" and "genre" in f["issue"].lower()]
        self.assertEqual(len(medium), 1)

    def test_genre_present_no_warning(self):
        """Prompts with genre early should not warn about front-loading."""
        prompt = "indie rock, melancholic, warm production"
        findings = validate_prompt.validate_style_prompt(prompt)
        genre_warnings = [f for f in findings if "genre" in f.get("issue", "").lower()]
        self.assertEqual(len(genre_warnings), 0)

    def test_lyric_metatags_detected(self):
        """Section tags in style prompts should be flagged."""
        prompt = "indie rock [Verse] warm vocals [Chorus] big harmonies"
        findings = validate_prompt.validate_style_prompt(prompt)
        high = [f for f in findings if f["severity"] == "high"]
        self.assertGreaterEqual(len(high), 1)
        self.assertTrue("metatag" in high[0]["issue"].lower() or "lyric" in high[0]["issue"].lower())

    def test_asterisks_detected(self):
        """Asterisks in style prompts should be flagged."""
        prompt = "indie rock, *bold vocals*, warm production"
        findings = validate_prompt.validate_style_prompt(prompt)
        asterisk = [f for f in findings if "asterisk" in f["issue"].lower()]
        self.assertEqual(len(asterisk), 1)
        self.assertEqual(asterisk[0]["severity"], "high")

    def test_southern_lane_genre_recognized(self):
        """Heavy/southern lane genres should satisfy front-loading (no false 'no genre')."""
        for prompt in [
            "heavy swamp metal, gritty male vocals, no screaming",
            "heartland southern rock, driving mid-tempo groove",
            "prog rock, slow build then fade, atmospheric",
            "slowcore, sparse and patient, doom-adjacent weight",
        ]:
            findings = validate_prompt.validate_style_prompt(prompt)
            no_genre = [f for f in findings if "no obvious genre keyword" in f.get("issue", "").lower()]
            self.assertEqual(len(no_genre), 0, f"False 'no genre' trip on: {prompt}")


class TestTriggerDetection(unittest.TestCase):
    """Tests for enumerable safety-trigger detection."""

    def test_unpaired_metal_flagged(self):
        """'metal' without a positive vocal instruction should be a high trigger finding."""
        findings = validate_prompt.validate_style_prompt("dark metal, heavy riffs, pounding drums")
        triggers = [f for f in findings if f["category"] == "trigger" and "scream" in f["issue"].lower()]
        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]["severity"], "high")
        self.assertIn("metal", triggers[0]["data"]["triggers"])

    def test_paired_metal_reported_low(self):
        """A positive vocal pairing lowers the trigger to low but still reports it as data."""
        findings = validate_prompt.validate_style_prompt(
            "heavy swamp metal, raw melodic singing, down-tuned weight"
        )
        triggers = [f for f in findings if f["category"] == "trigger" and "scream" in f["issue"].lower()]
        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]["severity"], "low")
        self.assertIs(triggers[0]["data"]["paired"], True)
        self.assertIn("raw melodic singing", triggers[0]["data"]["pairings"])

    def test_no_screaming_is_not_a_pairing(self):
        """'metal, no screaming' must not pass as safe: the negative is no pairing, and it is flagged."""
        findings = validate_prompt.validate_style_prompt("metal, no screaming")
        triggers = [f for f in findings if f["category"] == "trigger" and "scream" in f["issue"].lower()]
        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]["severity"], "high")
        self.assertIs(triggers[0]["data"]["paired"], False)
        negations = [f for f in findings if f["category"] == "negation"]
        self.assertTrue(negations)
        self.assertEqual(negations[0]["severity"], "high")
        self.assertIn("no screaming", negations[0]["data"]["phrases"])
        report = validate_prompt.build_report(findings, [], "metal, no screaming", "")
        self.assertEqual(report["status"], "warning")

    def test_negated_positive_phrase_does_not_pair(self):
        """'without clean vocals' doesn't count as a clean-vocal pairing."""
        findings = validate_prompt.validate_style_prompt("doom metal, without clean vocals")
        triggers = [f for f in findings if f["category"] == "trigger" and "scream" in f["issue"].lower()]
        self.assertEqual(triggers[0]["severity"], "high")
        self.assertIs(triggers[0]["data"]["paired"], False)

    def test_fix_text_carries_no_negative(self):
        """The trigger fix text must not recommend an inline negative."""
        findings = validate_prompt.validate_style_prompt("sludge metal, heavy riffs")
        trigger = [f for f in findings if f["category"] == "trigger"][0]
        self.assertNotIn("no screaming", trigger["fix"])

    def test_instrumental_trigger_is_info(self):
        """In an instrumental prompt an unpaired heavy term is informational only."""
        findings = validate_prompt.validate_style_prompt("doom metal, crushing riffs, slow", instrumental=True)
        triggers = [f for f in findings if f["category"] == "trigger" and "scream" in f["issue"].lower()]
        self.assertEqual(triggers[0]["severity"], "info")

    def test_word_boundary_no_false_trip(self):
        """Substrings like 'blackbird' should not trip the 'black' trigger."""
        findings = validate_prompt.validate_style_prompt(
            "folk rock, blackbird imagery, warm acoustic, clean singing"
        )
        triggers = [f for f in findings if f["category"] == "trigger" and "scream" in f["issue"].lower()]
        self.assertEqual(len(triggers), 0)

    def test_keyboard_pull_word_flagged(self):
        """'cinematic' should be flagged as a keyboard-pull dangerous word."""
        findings = validate_prompt.validate_style_prompt("hard rock, cinematic, driving guitars")
        kb = [f for f in findings if f["category"] == "trigger" and "keyboard-pull" in f["issue"].lower()]
        self.assertEqual(len(kb), 1)
        self.assertEqual(kb[0]["severity"], "medium")
        self.assertIn("cinematic", kb[0]["data"]["words"])

    def test_orchestral_and_baroque_flagged(self):
        """Multiple keyboard-pull words should be collected in one finding."""
        findings = validate_prompt.validate_style_prompt("baroque orchestral metal, intricate")
        kb = [f for f in findings if f["category"] == "trigger" and "keyboard-pull" in f["issue"].lower()]
        self.assertEqual(len(kb), 1)
        self.assertIn("baroque", kb[0]["data"]["words"])
        self.assertIn("orchestral", kb[0]["data"]["words"])

    def test_rock_opera_flagged(self):
        """'rock opera' should be flagged as a keyboard-pull dangerous word."""
        findings = validate_prompt.validate_style_prompt(
            "hard rock opera, soaring vocals, driving guitars"
        )
        kb = [f for f in findings if f["category"] == "trigger" and "keyboard-pull" in f["issue"].lower()]
        self.assertEqual(len(kb), 1)
        self.assertIn("rock opera", kb[0]["data"]["words"])

    def test_texture_modifier_does_not_satisfy_front_loading(self):
        """A texture-only prompt (cinematic/orchestral, no real genre) must still trip the
        'no genre front-loaded' warning AND be flagged as a keyboard pull — never both pass."""
        findings = validate_prompt.validate_style_prompt(
            "cinematic, orchestral, atmospheric, sweeping and grand"
        )
        no_genre = [f for f in findings if "no obvious genre keyword" in f.get("issue", "").lower()]
        kb = [f for f in findings if f["category"] == "trigger" and "keyboard-pull" in f["issue"].lower()]
        self.assertEqual(len(no_genre), 1, "texture-only prompt should still warn about missing genre")
        self.assertEqual(len(kb), 1, "texture words should be flagged as keyboard pulls")

    def test_exclamation_flagged_low(self):
        """Exclamation marks should produce a low trigger finding."""
        findings = validate_prompt.validate_style_prompt("upbeat pop rock, energetic!, bright")
        excl = [f for f in findings if f["category"] == "trigger" and "exclamation" in f["issue"].lower()]
        self.assertEqual(len(excl), 1)
        self.assertEqual(excl[0]["severity"], "low")

    def test_clean_prompt_no_triggers(self):
        """A clean safe prompt should produce no trigger findings."""
        findings = validate_prompt.validate_style_prompt(
            "heartland rock, warm male vocals, chimey electric guitar, driving groove"
        )
        triggers = [f for f in findings if f["category"] == "trigger"]
        self.assertEqual(len(triggers), 0)

    def test_empty_prompt_no_trigger_crash(self):
        """Empty prompt should not raise in trigger detection."""
        findings = validate_prompt.validate_style_prompt("")
        # only the empty-critical finding; no trigger findings
        triggers = [f for f in findings if f.get("category") == "trigger"]
        self.assertEqual(len(triggers), 0)


class TestValidateExclusionPrompt(unittest.TestCase):
    """Tests for exclusion prompt validation."""

    def test_empty_exclusion_is_info(self):
        """Empty exclusion prompts should produce an info finding (optional)."""
        findings = validate_prompt.validate_exclusion_prompt("")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "info")

    def test_valid_exclusion_passes(self):
        """A reasonable exclusion prompt should pass cleanly."""
        findings = validate_prompt.validate_exclusion_prompt("no autotune, no screaming")
        high_or_critical = [f for f in findings if f["severity"] in ("critical", "high")]
        self.assertEqual(len(high_or_critical), 0)

    def test_very_long_exclusion_is_high(self):
        """Exclusion prompts over 300 chars should produce a high finding."""
        prompt = "no " + ", no ".join([f"thing{i}" for i in range(60)])
        findings = validate_prompt.validate_exclusion_prompt(prompt)
        high = [f for f in findings if f["severity"] == "high"]
        self.assertGreaterEqual(len(high), 1)

    def test_too_many_items_warns(self):
        """More than 3 exclusion items should produce a medium notice."""
        prompt = "no guitar, no piano, no drums, no bass, no synth, no vocals"
        findings = validate_prompt.validate_exclusion_prompt(prompt)
        medium = [f for f in findings if f["severity"] == "medium" and "many" in f["issue"].lower()]
        self.assertEqual(len(medium), 1)

    def test_vague_terms_caught(self):
        """Vague exclusion terms should be flagged."""
        prompt = "no instruments, nothing bad"
        findings = validate_prompt.validate_exclusion_prompt(prompt)
        vague = [f for f in findings if "vague" in f["issue"].lower()]
        self.assertGreaterEqual(len(vague), 1)


class TestBuildReport(unittest.TestCase):
    """Tests for report generation."""

    def test_report_structure(self):
        """Report should have all required fields."""
        report = validate_prompt.build_report([], [], "test", "", "/test/path")
        self.assertEqual(report["script"], "validate-prompt")
        self.assertEqual(report["version"], "1.4.0")
        self.assertEqual(report["status"], "pass")
        self.assertIn("findings", report)
        self.assertIn("summary", report)
        self.assertIn("metrics", report)

    def test_critical_finding_sets_fail(self):
        """Critical findings should set status to fail."""
        findings = [{"severity": "critical", "category": "structure", "issue": "test", "fix": "test"}]
        report = validate_prompt.build_report(findings, [], "test", "")
        self.assertEqual(report["status"], "fail")

    def test_high_finding_sets_warning(self):
        """High findings (without critical) should set status to warning."""
        findings = [{"severity": "high", "category": "structure", "issue": "test", "fix": "test"}]
        report = validate_prompt.build_report(findings, [], "test", "")
        self.assertEqual(report["status"], "warning")

    def test_metrics_include_char_counts(self):
        """Metrics should include character counts."""
        report = validate_prompt.build_report([], [], "hello world", "no guitar")
        self.assertEqual(report["metrics"]["style_prompt_chars"], 11)
        self.assertEqual(report["metrics"]["exclusion_prompt_chars"], 9)


class TestCLI(unittest.TestCase):
    """Tests for command-line interface."""

    def test_help_flag(self):
        """--help should exit 0 with usage info."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("validate", result.stdout.lower())

    def test_style_flag_produces_json(self):
        """--style should produce valid JSON output."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--style", "indie rock, warm vocals"],
            capture_output=True, text=True
        )
        output = json.loads(result.stdout)
        self.assertEqual(output["script"], "validate-prompt")
        self.assertIn("findings", output)

    def test_model_flag_v4_pro(self):
        """--model 'v4 Pro' should apply 200-char limit."""
        prompt = "rock, " * 40  # ~240 chars, over 200 but under 1000
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--style", prompt, "--model", "v4 Pro"],
            capture_output=True, text=True
        )
        output = json.loads(result.stdout)
        critical = [f for f in output["findings"] if f["severity"] == "critical"]
        self.assertGreaterEqual(len(critical), 1)
        self.assertIn("200", critical[0]["issue"])

    def test_no_args_exits_2(self):
        """No arguments should exit with code 2."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 2)


class TestNegationDetection(unittest.TestCase):
    """Inline negatives read as inclusion on v6; the validator flags them."""

    def test_no_and_without_are_high(self):
        findings = validate_prompt.validate_style_prompt("indie rock, warm vocals, no reverb, without autotune")
        neg = [f for f in findings if f["category"] == "negation" and f["severity"] == "high"]
        self.assertEqual(len(neg), 1)
        self.assertEqual(neg[0]["data"]["phrases"], ["no reverb", "without autotune"])

    def test_not_and_avoid_are_medium(self):
        findings = validate_prompt.validate_style_prompt("indie rock, chorus energy from instruments, not extra voices")
        neg = [f for f in findings if f["category"] == "negation"]
        self.assertEqual(len(neg), 1)
        self.assertEqual(neg[0]["severity"], "medium")
        self.assertEqual(neg[0]["data"]["phrases"], ["not extra"])

    def test_do_not_counted_once(self):
        self.assertEqual(validate_prompt.find_negations("rock, do not rush"), ["do not rush"])

    def test_never_persistence_phrasing_not_flagged(self):
        """v6-endorsed persistence phrasing ('never stops') is direction, not negation."""
        findings = validate_prompt.validate_style_prompt(
            "hard rock, the intro riff continues under the verse vocal, never stops"
        )
        self.assertFalse([f for f in findings if f["category"] == "negation"])

    def test_hyphenated_no_not_flagged(self):
        findings = validate_prompt.validate_style_prompt("garage rock, no-frills production")
        self.assertFalse([f for f in findings if f["category"] == "negation"])


class TestCrowdNoiseWords(unittest.TestCase):
    """The 'live' word family and crowd/audience words pull crowd noise."""

    def test_live_family_flagged(self):
        for prompt in ["hard rock, live recording", "southern rock, live-band drums", "rock, live energy"]:
            findings = validate_prompt.validate_style_prompt(prompt)
            crowd = [f for f in findings if f["category"] == "trigger" and "crowd-noise" in f["issue"].lower()]
            self.assertEqual(len(crowd), 1, prompt)
            self.assertIn("live", crowd[0]["data"]["words"])

    def test_crowd_and_audience_words_flagged(self):
        findings = validate_prompt.validate_style_prompt("pop rock, anthemic, stadium chorus, roaring crowds, audience claps")
        crowd = [f for f in findings if "crowd-noise" in f["issue"].lower()][0]
        self.assertGreaterEqual(set(crowd["data"]["words"]), {"anthemic", "stadium", "crowd", "audience"})
        self.assertEqual(crowd["severity"], "medium")

    def test_lively_and_alive_not_flagged(self):
        findings = validate_prompt.validate_style_prompt("folk rock, lively strummed guitar, alive and bright")
        self.assertFalse([f for f in findings if "crowd-noise" in f["issue"].lower()])

    def test_crowd_words_in_exclusions_are_fine(self):
        findings = validate_prompt.validate_exclusion_prompt("crowd noise, live audience")
        self.assertFalse([f for f in findings if f["category"] == "trigger"])


class TestGenreWordBoundary(unittest.TestCase):
    def test_substring_does_not_count_as_genre(self):
        """'soulful' is not 'soul' and 'synthetic' is not 'synth'."""
        findings = validate_prompt.validate_style_prompt("soulful vocals over synthetic textures, warm and slow")
        self.assertTrue([f for f in findings if "no obvious genre keyword" in f.get("issue", "").lower()])

    def test_hyphenated_genre_still_counts(self):
        findings = validate_prompt.validate_style_prompt("folk-rock, warm, intimate")
        self.assertFalse([f for f in findings if "no obvious genre keyword" in f.get("issue", "").lower()])


class TestControls(unittest.TestCase):
    def test_persona_with_voice_value_is_range_error(self):
        findings = validate_prompt.validate_controls(50, "persona")
        self.assertEqual(findings[0]["category"], "range")
        self.assertEqual(findings[0]["severity"], "high")

    def test_voice_with_persona_value_is_range_error(self):
        findings = validate_prompt.validate_controls(20, "voice")
        self.assertEqual(findings[0]["category"], "range")

    def test_values_inside_range_pass(self):
        self.assertEqual(validate_prompt.validate_controls(25, "persona"), [])
        self.assertEqual(validate_prompt.validate_controls(55, "voice"), [])
        self.assertEqual(validate_prompt.validate_controls(None, ""), [])

    def test_vocal_gender_with_voice_flagged(self):
        findings = validate_prompt.validate_controls(55, "voice", vocal_gender="Male")
        self.assertTrue([f for f in findings if "vocal gender" in f["issue"].lower()])


class TestPackageValidation(unittest.TestCase):
    def test_wild_card_exclusions_are_validated_like_the_primary(self):
        package = {
            "model": "v6",
            "style_prompt": "Acoustic folk lullaby, fingerpicked guitar, soft female vocal, swaying 3/4 feel",
            "exclusion_prompt": "drums",
            "wild_card": {"style_prompt": "Dark folk, fingerpicked guitar, soft vocal", "model": "v6",
                          "exclusion_prompt": "drums, bass, choir, synths, strings"},
        }
        report = validate_prompt.validate_package(package)
        self.assertEqual(report["metrics"]["wild_card_exclusion_chars"], len("drums, bass, choir, synths, strings"))
        fields = [f["location"]["field"] for f in report["findings"]]
        self.assertIn("wild_card_exclusion_prompt", fields)

    def test_wild_card_without_its_own_exclusions_adds_nothing(self):
        package = {"model": "v6", "style_prompt": "Acoustic folk lullaby, fingerpicked guitar, soft female vocal",
                   "exclusion_prompt": "drums", "wild_card": {"style_prompt": "Dark folk, soft vocal", "model": "v6",
                                                              "exclusion_prompt": None}}
        report = validate_prompt.validate_package(package)
        self.assertNotIn("wild_card_exclusion_chars", report["metrics"])

    def _package(self, **overrides):
        package = {
            "model": "v6",
            "style_prompt": "heartland rock, warm male vocal, chimey electric guitar, driving groove",
            "exclusion_prompt": "steel guitar, autotune",
            "wild_card": {"style_prompt": "southern rock, warm male vocal, slide guitar lead, swampy groove"},
        }
        package.update(overrides)
        return package

    def test_clean_package_passes(self):
        report = validate_prompt.validate_package(self._package())
        self.assertEqual(report["status"], "pass")
        self.assertGreater(report["metrics"]["wild_card_prompt_chars"], 0)

    def test_wild_card_is_validated(self):
        package = self._package(wild_card={"style_prompt": "rock, " * 200})
        report = validate_prompt.validate_package(package)
        wc = [f for f in report["findings"] if f["location"]["field"] == "wild_card_prompt"]
        self.assertTrue(any(f["severity"] == "critical" for f in wc))
        self.assertEqual(report["status"], "fail")

    def test_wild_card_triggers_flagged(self):
        package = self._package(wild_card={"style_prompt": "doom metal, live recording, no screaming"})
        report = validate_prompt.validate_package(package)
        wc = [f for f in report["findings"] if f["location"]["field"] == "wild_card_prompt"]
        categories = {f["category"] for f in wc}
        self.assertLessEqual({"trigger", "negation"}, categories)

    def test_metrics_report_model_limit(self):
        report = validate_prompt.validate_package({"model": "v4 Pro", "style_prompt": "rock, warm"})
        self.assertEqual(report["metrics"]["style_prompt_limit"], 200)

    def test_controls_in_package(self):
        package = self._package(sliders={"audio_influence": 50, "audio_source": "persona"})
        report = validate_prompt.validate_package(package)
        self.assertTrue([f for f in report["findings"] if f["location"]["field"] == "controls"])


class TestPackageCLI(unittest.TestCase):
    def test_stdin_package(self):
        package = {"model": "v6", "style_prompt": "indie rock, \"quoted\" $HOME `tick` vocals",
                   "wild_card_prompt": "indie folk, warm"}
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--stdin"],
            input=json.dumps(package), capture_output=True, text=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(output["metrics"]["style_prompt_chars"], len(package["style_prompt"]))
        self.assertEqual(output["metrics"]["wild_card_prompt_chars"], len("indie folk, warm"))

    def test_input_file_json(self):
        tmp_path = _tmp_path(self)
        path = tmp_path / "package.json"
        path.write_text(json.dumps({"model": "v6", "style_prompt": "metal, no screaming"}))
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--input-file", str(path)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "warning")

    def test_wild_card_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--style", "indie rock, warm", "--wild-card", "rock, live energy"],
            capture_output=True, text=True,
        )
        output = json.loads(result.stdout)
        self.assertTrue([f for f in output["findings"] if f["location"]["field"] == "wild_card_prompt"])

    def test_bad_json_exits_2(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--stdin"],
            input="{not json", capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)


def _run_cli(*args, stdin=None):
    return subprocess.run([sys.executable, str(SCRIPT_PATH), *args],
                          input=stdin, capture_output=True, text=True)


class TestStatusAndExit(unittest.TestCase):
    def test_medium_only_is_review_and_exits_1(self):
        result = _run_cli("--style", "indie rock, warm male vocal, cinematic swells", "--model", "v6")
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "review")
        self.assertEqual(result.returncode, 1)

    def test_low_only_is_pass(self):
        report = validate_prompt.validate_package({"model": "v6", "style_prompt": "indie rock, warm vocal!"})
        self.assertEqual(report["status"], "pass")

    def test_four_exclusion_items_trigger_notice(self):
        findings = validate_prompt.validate_exclusion_prompt("choir, backing vocals, gang vocals, crowd chants")
        self.assertTrue([f for f in findings if f["severity"] == "medium" and "many" in f["issue"].lower()])

    def test_three_exclusion_items_are_fine(self):
        findings = validate_prompt.validate_exclusion_prompt("screaming, steel guitar, autotune")
        self.assertFalse([f for f in findings if "many" in f["issue"].lower()])


class TestModelCheck(unittest.TestCase):
    def _models(self, report):
        return [f for f in report["findings"] if f["category"] == "model"]

    def test_current_model_passes(self):
        for model in ("v6", "v6-wild", "v6-mini"):
            report = validate_prompt.validate_package({"model": model, "style_prompt": "indie rock, warm vocal"})
            self.assertFalse(self._models(report))

    def test_retired_model_is_high(self):
        report = validate_prompt.validate_package({"model": "v5.5 Pro", "style_prompt": "indie rock, warm vocal"})
        found = self._models(report)
        self.assertTrue(found)
        self.assertEqual(found[0]["severity"], "high")
        self.assertIn("retired", found[0]["issue"])
        self.assertEqual(report["status"], "warning")

    def test_unknown_model_is_high_with_hint(self):
        report = validate_prompt.validate_package({"model": "V6", "style_prompt": "indie rock, warm vocal"})
        found = self._models(report)
        self.assertTrue(found)
        self.assertEqual(found[0]["severity"], "high")
        self.assertIn("v6", found[0]["issue"])

    def test_wild_card_model_checked(self):
        report = validate_prompt.validate_package({
            "model": "v6", "style_prompt": "indie rock, warm vocal",
            "wild_card": {"style_prompt": "indie folk, warm vocal", "model": "v5 Pro"},
        })
        self.assertTrue(self._models(report))

    def test_wild_card_on_other_model_is_medium(self):
        report = validate_prompt.validate_package({
            "model": "v6", "style_prompt": "indie rock, warm vocal",
            "wild_card": {"style_prompt": "indie folk, warm vocal", "model": "v6-wild"},
        })
        mismatch = [f for f in report["findings"] if "wild card runs on" in f["issue"].lower()]
        self.assertTrue(mismatch)
        self.assertEqual(mismatch[0]["severity"], "medium")
        self.assertEqual(report["metrics"]["wild_card_prompt_limit"], 1000)


class TestTierRules(unittest.TestCase):
    def _tier(self, report):
        return [f for f in report["findings"] if f["category"] == "tier"]

    def test_free_with_excludes_and_sliders_flagged(self):
        report = validate_prompt.validate_package({
            "model": "v6-mini", "tier": "free", "style_prompt": "indie rock, warm vocal",
            "exclusion_prompt": "autotune", "sliders": {"weirdness": 50, "style_influence": 70},
        })
        issues = " ".join(f["issue"] for f in self._tier(report))
        self.assertIn("Exclude Styles", issues)
        self.assertIn("Slider", issues)
        self.assertEqual(report["status"], "warning")

    def test_free_on_paid_model_flagged(self):
        report = validate_prompt.validate_package({"model": "v6", "tier": "free", "style_prompt": "indie rock"})
        self.assertTrue(self._tier(report))

    def test_clean_free_package_passes(self):
        report = validate_prompt.validate_package({
            "model": "v6-mini", "tier": "free", "style_prompt": "indie rock, warm vocal",
            "exclusion_prompt": None, "sliders": None,
        })
        self.assertFalse(self._tier(report))

    def test_pro_tier_unrestricted(self):
        report = validate_prompt.validate_package({
            "model": "v6", "tier": "pro", "style_prompt": "indie rock, warm vocal",
            "exclusion_prompt": "autotune", "sliders": {"weirdness": 50},
        })
        self.assertFalse(self._tier(report))

    def test_tier_flag(self):
        result = _run_cli("--style", "indie rock, warm vocal", "--exclude", "autotune",
                          "--model", "v6-mini", "--tier", "free")
        output = json.loads(result.stdout)
        self.assertTrue([f for f in output["findings"] if f["category"] == "tier"])


class TestMalformedInput(unittest.TestCase):
    def _exit(self, package):
        return _run_cli("--stdin", stdin=json.dumps(package))

    def test_string_sliders_exits_2_with_reason(self):
        result = self._exit({"style_prompt": "indie rock", "sliders": "same as primary"})
        self.assertEqual(result.returncode, 2)
        self.assertIn("sliders", result.stderr)

    def test_string_instrumental_exits_2(self):
        result = self._exit({"style_prompt": "indie rock", "instrumental": "false"})
        self.assertEqual(result.returncode, 2)
        self.assertIn("instrumental", result.stderr)

    def test_non_string_prompt_exits_2(self):
        result = self._exit({"style_prompt": ["indie rock"]})
        self.assertEqual(result.returncode, 2)
        self.assertIn("style_prompt", result.stderr)

    def test_unknown_tier_exits_2(self):
        result = self._exit({"style_prompt": "indie rock", "tier": "gold"})
        self.assertEqual(result.returncode, 2)
        self.assertIn("tier", result.stderr)

    def test_wild_card_sliders_string_is_accepted(self):
        report = validate_prompt.validate_package({
            "model": "v6", "style_prompt": "indie rock, warm vocal",
            "wild_card": {"style_prompt": "indie folk, warm vocal", "sliders": "same as primary"},
        })
        self.assertEqual(report["status"], "pass")

    def test_missing_file_exits_2(self):
        tmp_path = _tmp_path(self)
        result = _run_cli("--input-file", str(tmp_path / "nope.json"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("not found", result.stderr)


class TestYamlInput(unittest.TestCase):
    def test_yaml_keeps_nested_fields(self):
        tmp_path = _tmp_path(self)
        path = tmp_path / "package.yaml"
        path.write_text(
            "model: v6\n"
            "instrumental: true\n"
            "style_prompt: doom metal, slow crushing riffs, droning bass\n"
            "wild_card:\n"
            "  style_prompt: sludge metal, swampy feedback\n"
        )
        result = _run_cli("--input-file", str(path))
        output = json.loads(result.stdout)
        triggers = [f for f in output["findings"] if f.get("data", {}).get("triggers")]
        # instrumental survives, so the scream trigger is informational, not high
        self.assertTrue(triggers)
        self.assertTrue(all(f["severity"] == "info" for f in triggers))
        self.assertGreater(output["metrics"]["wild_card_prompt_chars"], 0)

    def test_yaml_without_pyyaml_exits_2(self):
        tmp_path = _tmp_path(self)
        real_import = builtins.__import__

        def no_yaml(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("no yaml")
            return real_import(name, *args, **kwargs)

        path = tmp_path / "package.yaml"
        path.write_text("style_prompt: indie rock\n")
        with mock.patch.object(builtins, "__import__", no_yaml):
            with self.assertRaises(validate_prompt.PackageError) as ctx:
                validate_prompt._load_package_file(path)
        self.assertIn("pyyaml", str(ctx.exception))

    def test_bad_yaml_exits_2(self):
        tmp_path = _tmp_path(self)
        path = tmp_path / "package.yml"
        path.write_text("style_prompt: [unclosed\n")
        result = _run_cli("--input-file", str(path))
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
