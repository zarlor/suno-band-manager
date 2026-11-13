#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Tests for validate_prompt.py"""

import builtins
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Load the script as a module
SCRIPT_PATH = Path(__file__).parent.parent / "validate_prompt.py"
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

    def test_numbered_and_unlisted_tags_detected(self):
        """Any bracketed tag is a lyric metatag, not only the six bare section names."""
        for tag in ("[Verse 1]", "[Final Chorus]", "[Guitar Solo]", "[Mood: dark]"):
            findings = validate_prompt.validate_style_prompt(f"indie rock, warm vocals {tag} big harmonies")
            tags = [f for f in findings if "metatag" in f["issue"].lower()]
            self.assertEqual([(f["severity"], f["data"]["tags"]) for f in tags], [("high", [tag])], tag)

    def test_word_cut_at_the_critical_zone_is_not_a_genre(self):
        """'popcorn' straddling character 200 must not count as 'pop'."""
        prompt = "warm and beautiful textures, " + "x" * 167 + " popcorn crackle"
        self.assertEqual(prompt[:200][-3:], "pop")
        findings = validate_prompt.validate_style_prompt(prompt)
        self.assertEqual(len([f for f in findings if "no obvious genre keyword" in f["issue"].lower()]), 1)
        whole = "warm and beautiful textures, " + "x" * 167 + " pop, bright"
        self.assertEqual(whole[:200][-3:], "pop")
        self.assertFalse([f for f in validate_prompt.validate_style_prompt(whole)
                          if "no obvious genre keyword" in f["issue"].lower()])

    def test_current_models_limit_is_1000_at_the_boundary(self):
        for model in ("v6", "v6-wild", "v6-mini"):
            at = validate_prompt.validate_style_prompt("rock " + "x" * 995, model=model)
            over = validate_prompt.validate_style_prompt("rock " + "x" * 996, model=model)
            self.assertFalse([f for f in at if f["severity"] == "critical"], model)
            self.assertEqual([f["data"]["over_by"] for f in over if f["severity"] == "critical"], [1], model)
            report = validate_prompt.validate_package({"model": model, "style_prompt": "rock"})
            self.assertEqual(report["metrics"]["style_prompt_limit"], 1000, model)

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

    def test_hard_maximum_is_300_characters(self):
        at = "steel guitar, " + "x" * 286
        self.assertEqual(len(at), 300)
        self.assertFalse([f for f in validate_prompt.validate_exclusion_prompt(at) if f["severity"] == "high"])
        self.assertEqual([f["data"]["char_count"] for f in validate_prompt.validate_exclusion_prompt(at + "x")
                          if f["severity"] == "high"], [301])

    def test_newline_and_pipe_separated_items_are_counted(self):
        for text in ("screaming\nsteel guitar\nautotune\nsynth pads", "screaming | steel guitar | autotune | synth pads"):
            self.assertEqual(validate_prompt.exclusion_items(text), ["screaming", "steel guitar", "autotune", "synth pads"])
            findings = validate_prompt.validate_exclusion_prompt(text)
            self.assertEqual([f["data"]["item_count"] for f in findings if "many" in f["issue"].lower()], [4])

    def test_too_many_items_warns(self):
        """More than 3 exclusion items should produce a medium notice."""
        prompt = "no guitar, no piano, no drums, no bass, no synth, no vocals"
        findings = validate_prompt.validate_exclusion_prompt(prompt)
        medium = [f for f in findings if f["severity"] == "medium" and "many" in f["issue"].lower()]
        self.assertEqual(len(medium), 1)

    def test_negated_items_are_a_low_note(self):
        """'no X' in Exclude Styles is a double negative: noted, never blocking."""
        findings = validate_prompt.validate_exclusion_prompt("no organ, -sax, without reverb, steel guitar")
        note = [f for f in findings if "written as negatives" in f["issue"]]
        self.assertEqual([f["severity"] for f in note], ["low"])
        self.assertEqual(note[0]["data"]["items"], ["no organ", "-sax", "without reverb"])

    def test_bare_items_and_words_starting_with_no_are_not_negatives(self):
        findings = validate_prompt.validate_exclusion_prompt("organ, noise, nu metal, notch filter, non-diegetic sound")
        self.assertFalse([f for f in findings if "written as negatives" in f["issue"]])

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
        self.assertEqual(report["version"], "1.5.0")
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
        self.assertEqual(report["metrics"]["exclusion_recommended_max"], 200)
        self.assertEqual(report["metrics"]["critical_zone"], 200)


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
        self.assertEqual(validate_prompt.find_negations("indie rock, avoiding reverb, avoid synths"),
                         ["avoiding reverb", "avoid synths"])
        avoid = [f for f in validate_prompt.validate_style_prompt("indie rock, warm vocal, avoid synths")
                 if f["category"] == "negation"]
        self.assertEqual([(f["severity"], f["data"]["phrases"]) for f in avoid], [("medium", ["avoid synths"])])

    def test_curly_apostrophe_and_other_contractions_are_medium(self):
        for prompt, phrase in (("indie rock, the drums don\u2019t rush", "don't rush"),
                               ("indie rock, the vocal isn't buried", "isn't buried"),
                               ("indie rock, guitars that won\u2019t distort", "won't distort")):
            neg = [f for f in validate_prompt.validate_style_prompt(prompt) if f["category"] == "negation"]
            self.assertEqual([(f["severity"], f["data"]["phrases"]) for f in neg], [("medium", [phrase])], prompt)

    def test_free_suffix_and_minus_are_medium(self):
        neg = [f for f in validate_prompt.validate_style_prompt("indie rock, reverb-free vocal, full band minus drums")
               if f["category"] == "negation"]
        self.assertEqual([(f["severity"], f["data"]["phrases"]) for f in neg],
                         [("medium", ["reverb-free", "minus drums"])])
        self.assertEqual(validate_prompt.find_negations("carefree indie rock, free-form jazz solo"), [])

    def test_do_not_counted_once(self):
        self.assertEqual(validate_prompt.find_negations("rock, do not rush"), ["do not rush"])

    def test_never_persistence_phrasing_not_flagged(self):
        """v6-endorsed persistence phrasing ('never stops') is direction, not negation."""
        findings = validate_prompt.validate_style_prompt(
            "hard rock, the intro riff continues under the verse vocal, never stops"
        )
        self.assertFalse([f for f in findings if f["category"] == "negation"])

    def test_never_with_an_event_verb_is_flagged(self):
        """'never crashes in' hands Suno 'crashes'."""
        findings = validate_prompt.validate_style_prompt("acoustic sludge ballad, the band never crashes in")
        neg = [f for f in findings if f["category"] == "negation"]
        self.assertEqual(neg[0]["severity"], "medium")
        self.assertEqual(neg[0]["data"]["phrases"], ["never crashes"])

    def test_never_lets_up_not_flagged(self):
        self.assertEqual(validate_prompt.find_negations("driving groove that never lets up"), [])

    def test_gravity_word_is_medium(self):
        findings = validate_prompt.validate_style_prompt("swamp metal, crushing weight, slow riff, raw male vocal")
        grav = [f for f in findings if f["category"] == "gravity"]
        self.assertEqual((grav[0]["severity"], grav[0]["data"]["words"]), ("medium", ["crushing"]))

    def test_gravity_word_on_a_part_is_not_flagged(self):
        findings = validate_prompt.validate_style_prompt("sludge metal, heavy riffs, massive kick, clean sung male vocal")
        self.assertFalse([f for f in findings if f["category"] == "gravity"])

    def test_group_vocal_words_against_choir_excludes(self):
        found = validate_prompt.validate_group_vocal_contradiction(
            "gospel rock, call-and-response verses, solo lead", "choir, backing vocals, gang vocals, layered vocals, crowd chants")
        self.assertEqual(found[0]["data"]["pulls"], ["call-and-response"])
        self.assertEqual(validate_prompt.validate_group_vocal_contradiction("gospel rock, solo lead", "choir"), [])

    def test_old_time_string_band_is_a_genre(self):
        findings = validate_prompt.validate_style_prompt("Old-time Appalachian string-band waltz, fiddle lead, warm female alto")
        self.assertFalse([f for f in findings if "genre keyword" in f["issue"]])

    def test_scream_reason_must_name_each_trigger(self):
        rat = [{"term": "screaming", "defends_against": "'swamp metal' pulls harsh vocals"}]
        findings = validate_prompt.validate_exclusion_rationale(
            rat, "swamp metal and sludge undertones, clean sung male vocal")
        cov = [f for f in findings if "scream trigger" in f["issue"]]
        self.assertEqual(cov[0]["data"]["uncovered"], ["sludge"])

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

    def test_arena_flagged(self):
        findings = validate_prompt.validate_style_prompt("hard rock, arena-sized chorus, big drums")
        crowd = [f for f in findings if "crowd-noise" in f["issue"].lower()]
        self.assertEqual([f["data"]["words"] for f in crowd], [["arena"]])

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

    def test_range_edges(self):
        self.assertEqual(validate_prompt.validate_controls(15, "persona"), [])
        self.assertEqual([f["category"] for f in validate_prompt.validate_controls(14, "persona")], ["range"])
        self.assertEqual([f["category"] for f in validate_prompt.validate_controls(26, "persona")], ["range"])
        self.assertEqual(validate_prompt.validate_controls(35, "voice"), [])
        self.assertEqual(validate_prompt.validate_controls(95, "voice"), [])
        self.assertEqual([f["category"] for f in validate_prompt.validate_controls(34, "voice")], ["range"])
        self.assertEqual([f["category"] for f in validate_prompt.validate_controls(96, "voice")], ["range"])

    def test_non_numeric_audio_influence_is_high(self):
        findings = validate_prompt.validate_controls("high", "voice")
        self.assertEqual([(f["category"], f["severity"]) for f in findings], [("range", "high")])

    def test_vocal_gender_with_voice_flagged(self):
        findings = validate_prompt.validate_controls(55, "voice", vocal_gender="Male")
        self.assertTrue([f for f in findings if "vocal gender" in f["issue"].lower()])


class TestEmit(unittest.TestCase):
    BASE = {"status": "complete", "mode": "build", "model": "v6", "tier": "pro",
            "style_prompt": "heartland rock, warm male vocal, chimey electric guitar, driving groove",
            "style_prompt_chars": 5, "exclusion_prompt": "steel guitar",
            "exclusion_rationale": [{"term": "steel guitar", "defends_against": "'heartland rock' can pull pedal steel"}],
            "validation": {"stale": True}, "handoff_notes": [], "decisions": []}

    def emit(self, **overrides):
        package = {**self.BASE, **overrides}
        report = validate_prompt.validate_package(package)
        return validate_prompt.emit_package(package, report)

    def test_clean_package_is_returned_with_the_script_report_and_counts(self):
        out, code = self.emit()
        self.assertEqual(code, 0)
        self.assertEqual(out["style_prompt_chars"], len(self.BASE["style_prompt"]))
        self.assertEqual(out["validation"]["script"], "validate-prompt")
        self.assertEqual(list(out)[:6], ["status", "mode", "model", "tier", "style_prompt", "style_prompt_chars"])
        self.assertEqual(list(out)[-3:], ["validation", "handoff_notes", "decisions"])

    def test_unjudged_medium_finding_is_refused(self):
        bad = [{"term": "steel guitar", "defends_against": "the profile's 'string-band' defaults"}]
        out, code = self.emit(exclusion_rationale=bad)
        self.assertEqual((code, out["status"]), (1, "emit_refused"))
        self.assertEqual(len(out["findings"]), 1)

    def test_judged_medium_finding_is_accepted(self):
        bad = [{"term": "steel guitar", "defends_against": "the profile's 'string-band' defaults"}]
        package = {**self.BASE, "exclusion_rationale": bad}
        fid = [f["id"] for f in validate_prompt.validate_package(package)["findings"] if f["severity"] == "medium"][0]
        out, code = self.emit(exclusion_rationale=bad,
                              decisions=[{"finding": fid, "call": "kept", "reason": "owner's standing exclude"}])
        self.assertEqual(code, 0)
        self.assertEqual(out["validation"]["status"], "review")

    def test_decision_naming_a_stale_finding_is_refused(self):
        out, code = self.emit(decisions=[{"finding": "deadbeef", "call": "kept", "reason": "old run"}])
        self.assertEqual((code, out["status"]), (1, "emit_refused"))
        self.assertEqual(out["findings"], ["deadbeef"])

    def test_high_finding_is_refused_even_when_judged(self):
        out, code = self.emit(style_prompt="death metal, blast beats, dark")
        self.assertEqual((code, out["status"]), (1, "emit_refused"))

    def test_finding_ids_are_stable(self):
        a = validate_prompt.validate_package({**self.BASE, "exclusion_prompt": "a, b, c, d, e, f"})
        b = validate_prompt.validate_package({**self.BASE, "exclusion_prompt": "a, b, c, d, e, f"})
        self.assertEqual([f["id"] for f in a["findings"]], [f["id"] for f in b["findings"]])
        self.assertTrue(a["findings"])

    def test_wild_card_count_comes_from_the_script(self):
        wc = {"style_prompt": "southern rock, warm male vocal, slide guitar lead", "style_prompt_chars": 1, "model": "v6",
              "exclusion_prompt": "steel guitar",
              "exclusion_rationale": [{"term": "steel guitar", "defends_against": "'southern rock' can pull pedal steel"}]}
        out, code = self.emit(wild_card=wc)
        self.assertEqual(code, 0)
        self.assertEqual(out["wild_card"]["style_prompt_chars"], len(wc["style_prompt"]))


class TestPackageValidation(unittest.TestCase):
    def test_singular_vocal_pairing_protects_a_heavy_genre(self):
        report = validate_prompt.validate_package(
            {"model": "v6", "style_prompt": "heavy swamp metal lullaby, clean sung vocal, slow sway, warm room"})
        heavy = [f for f in report["findings"] if "scream trigger" in f["issue"]]
        self.assertTrue(heavy)
        self.assertEqual(heavy[0]["severity"], "low")

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
            "exclusion_prompt": "steel guitar",
            "exclusion_rationale": [{"term": "steel guitar", "defends_against": "'heartland rock' can pull pedal steel"}],
            "wild_card": {"style_prompt": "southern rock, warm male vocal, slide guitar lead, swampy groove",
                          "exclusion_prompt": "steel guitar",
                          "exclusion_rationale": [{"term": "steel guitar", "defends_against": "'southern rock' can pull pedal steel"}]},
        }
        package.update(overrides)
        return package

    def test_rationale_quoting_this_prompt_passes(self):
        package = self._package(exclusion_rationale=[
            {"term": "steel guitar", "defends_against": "'heartland rock' can pull pedal steel"}])
        report = validate_prompt.validate_package(package)
        self.assertFalse([f for f in report["findings"] if f.get("category") == "exclusion"])

    def test_rationale_citing_words_not_in_the_prompt_is_medium(self):
        package = self._package(exclusion_rationale=[
            {"term": "steel guitar", "defends_against": "the profile's 'string-band' genre defaults"}])
        report = validate_prompt.validate_package(package)
        found = [f for f in report["findings"] if f.get("category") == "exclusion"]
        self.assertEqual([f["severity"] for f in found], ["medium"])
        self.assertEqual(found[0]["data"]["quoted"], ["string-band"])

    def test_rationale_quoting_nothing_is_low(self):
        package = self._package(exclusion_prompt="autotune", exclusion_rationale=[
            {"term": "autotune", "defends_against": "v6 tends to polish vocals"}])
        found = [f for f in validate_prompt.validate_package(package)["findings"] if f.get("category") == "exclusion"]
        self.assertEqual([f["severity"] for f in found], ["low"])

    def test_wild_card_rationale_checks_the_wild_card_prompt(self):
        package = self._package(wild_card={
            "style_prompt": "southern rock, warm male vocal, slide guitar lead, swampy groove",
            "exclusion_prompt": "banjo",
            "exclusion_rationale": [{"term": "banjo", "defends_against": "'swampy groove' can pull banjo"}]})
        found = [f for f in validate_prompt.validate_package(package)["findings"] if f.get("category") == "exclusion"]
        self.assertEqual(found, [])

    def test_possessive_apostrophe_is_not_a_quote(self):
        package = self._package(exclusion_prompt="autotune", exclusion_rationale=[
            {"term": "autotune", "defends_against": "the band's 'warm male vocal' could read as polished"}])
        found = [f for f in validate_prompt.validate_package(package)["findings"] if f.get("category") == "exclusion"]
        self.assertEqual(found, [])

    def test_wild_card_adding_a_scream_trigger_needs_its_own_excludes(self):
        package = {"model": "v6",
                   "style_prompt": "Southern heavy groove, raw melodic singing, gritty male vocal, dark and defiant",
                   "exclusion_prompt": "screaming",
                   "exclusion_rationale": [{"term": "screaming", "defends_against": "'heavy groove' can pull harsh vocals"}],
                   "wild_card": {"style_prompt": "Sludge groove, raw melodic singing, gritty male vocal, slow and crushing",
                                 "exclusion_prompt": None}}
        found = [f for f in validate_prompt.validate_package(package)["findings"]
                 if f.get("data", {}).get("added_triggers")]
        self.assertEqual(found[0]["data"]["added_triggers"], ["sludge"])
        self.assertEqual(found[0]["severity"], "medium")

    def test_wild_card_trigger_named_in_a_reason_passes(self):
        package = {"model": "v6",
                   "style_prompt": "Southern heavy groove, raw melodic singing, gritty male vocal",
                   "exclusion_prompt": "screaming",
                   "exclusion_rationale": [{"term": "screaming", "defends_against": "'heavy groove' and the wild card's 'sludge' pull harsh vocals"}],
                   "wild_card": {"style_prompt": "Sludge groove, raw melodic singing, gritty male vocal", "exclusion_prompt": None}}
        found = [f for f in validate_prompt.validate_package(package)["findings"]
                 if f.get("data", {}).get("added_triggers")]
        self.assertEqual(found, [])

    def test_emit_refuses_without_tier(self):
        package = {"model": "v6", "style_prompt": "heartland rock, warm male vocal"}
        out, code = validate_prompt.emit_package(package, validate_prompt.validate_package(package))
        self.assertEqual((code, out["status"]), (1, "emit_refused"))

    def test_every_quoted_fragment_must_be_in_the_prompt(self):
        package = self._package(exclusion_rationale=[
            {"term": "steel guitar", "defends_against": "'heartland rock' plus the request's 'big band moment'"}])
        found = [f for f in validate_prompt.validate_package(package)["findings"] if f.get("category") == "exclusion"]
        self.assertEqual(found[0]["data"]["quoted"], ["big band moment"])

    def test_inherited_wild_exclude_must_fit_the_wild_prompt(self):
        package = self._package(exclusion_rationale=[
            {"term": "steel guitar", "defends_against": "'heartland rock' can pull pedal steel"}],
            wild_card={"style_prompt": "southern rock, slide guitar lead", "exclusion_prompt": None})
        found = [f for f in validate_prompt.validate_package(package)["findings"]
                 if f.get("data", {}).get("inherited_term") == "steel guitar"]
        self.assertEqual(len(found), 1)

    def test_free_tier_max_mode_and_variety_are_flagged(self):
        package = {"model": "v6-mini", "tier": "free", "style_prompt": "folk lullaby, soft female vocal, fingerpicked guitar",
                   "v6_options": {"max_mode": True, "variety": "Balanced"}}
        sev = sorted(f["severity"] for f in validate_prompt.validate_package(package)["findings"] if f.get("category") == "tier")
        self.assertEqual(sev, ["high", "medium"])

    def test_vocal_gender_must_be_lower_case(self):
        package = {"model": "v6", "style_prompt": "folk lullaby, fingerpicked guitar", "vocal_gender": "Male"}
        self.assertTrue([f for f in validate_prompt.validate_package(package)["findings"] if "vocal_gender" in f["issue"]])

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


class TestEmitCLI(unittest.TestCase):
    """The --emit branch as the headless builder runs it: what it prints and how it exits."""

    def test_clean_package_prints_the_package_and_exits_0(self):
        result = _run_cli("--stdin", "--emit", stdin=json.dumps(TestEmit.BASE))
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual(out["style_prompt"], TestEmit.BASE["style_prompt"])
        self.assertEqual(out["style_prompt_chars"], len(TestEmit.BASE["style_prompt"]))
        self.assertEqual(out["validation"]["script"], "validate-prompt")
        self.assertEqual(out["validation"]["status"], "pass")

    def test_standing_high_finding_is_refused_with_exit_1(self):
        package = {**TestEmit.BASE, "style_prompt": "death metal, blast beats, dark"}
        result = _run_cli("--stdin", "--emit", stdin=json.dumps(package))
        self.assertEqual(result.returncode, 1)
        out = json.loads(result.stdout)
        self.assertEqual(out["status"], "emit_refused")
        self.assertNotIn("style_prompt", out)
        self.assertTrue(out["findings"])

    def test_non_list_decisions_exits_2_not_a_traceback(self):
        for extra in ((), ("--emit",)):
            result = _run_cli("--stdin", *extra, stdin=json.dumps({**TestEmit.BASE, "decisions": 7}))
            self.assertEqual(result.returncode, 2, extra)
            self.assertIn("decisions", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_decision_without_call_or_reason_does_not_judge_a_finding(self):
        bad = [{"term": "steel guitar", "defends_against": "the profile's 'string-band' defaults"}]
        package = {**TestEmit.BASE, "exclusion_rationale": bad}
        fid = [f["id"] for f in validate_prompt.validate_package(package)["findings"] if f["severity"] == "medium"][0]
        for decision in ({"finding": fid}, {"finding": fid, "call": "kept", "reason": "  "},
                         {"finding": fid, "call": "", "reason": "the user's standing exclude"}):
            package["decisions"] = [decision]
            out, code = validate_prompt.emit_package(package, validate_prompt.validate_package(package))
            self.assertEqual((code, out["status"], out["findings"]), (1, "emit_refused", [fid]), decision)


class TestFlagsCLI(unittest.TestCase):
    def test_passing_package_exits_0(self):
        result = _run_cli("--style", "heartland rock, warm male vocal", "--model", "v6", "--tier", "pro")
        self.assertEqual((result.returncode, json.loads(result.stdout)["status"]), (0, "pass"))

    def test_instrumental_flag_makes_the_scream_trigger_informational(self):
        result = _run_cli("--style", "doom metal, slow riffs", "--instrumental")
        triggers = [f for f in json.loads(result.stdout)["findings"] if f.get("data", {}).get("triggers")]
        self.assertEqual([f["severity"] for f in triggers], ["info"])

    def test_audio_flags_are_range_checked(self):
        result = _run_cli("--style", "indie rock, warm vocal", "--audio-influence", "50", "--audio-source", "persona")
        ranged = [f for f in json.loads(result.stdout)["findings"] if f["category"] == "range"]
        self.assertEqual([f["data"]["audio_source"] for f in ranged], ["persona"])
        self.assertEqual(result.returncode, 1)

    def test_vocal_gender_flag_with_a_voice_is_flagged(self):
        result = _run_cli("--style", "indie rock, warm vocal", "--audio-influence", "55", "--audio-source", "voice",
                          "--vocal-gender", "male")
        self.assertTrue([f for f in json.loads(result.stdout)["findings"] if "vocal gender" in f["issue"].lower()])

    def test_style_or_exclude_beside_a_package_is_refused(self):
        package = json.dumps({"model": "v6", "style_prompt": "indie rock, warm vocal"})
        for flags in (("--style", "death metal"), ("--exclude", "autotune")):
            result = _run_cli("--stdin", *flags, stdin=package)
            self.assertEqual(result.returncode, 2, flags)
            self.assertIn("package", result.stderr)
            self.assertEqual(result.stdout, "")


class TestReferenceNames(unittest.TestCase):
    BASE = {"model": "v6", "tier": "pro",
            "style_prompt": "heartland rock, warm male vocal, chimey electric guitar, driving groove",
            "reference_names": ["Tom Petty", "Free Fallin'", "Low"]}

    def _names(self, **overrides):
        report = validate_prompt.validate_package({**self.BASE, **overrides})
        return [(f["location"]["field"], f["severity"], f["data"]["name"])
                for f in report["findings"] if f["category"] == "reference_name"]

    def test_decomposed_prompt_has_no_finding(self):
        self.assertEqual(self._names(), [])

    def test_name_in_the_style_prompt_is_high(self):
        found = self._names(style_prompt="heartland rock in the style of tom petty, warm male vocal")
        self.assertEqual(found, [("style_prompt", "high", "Tom Petty")])

    def test_song_title_with_a_curly_apostrophe_matches(self):
        found = self._names(style_prompt="heartland rock, warm male vocal, a Free Fallin\u2019 jangle")
        self.assertEqual(found, [("style_prompt", "high", "Free Fallin'")])

    def test_name_in_the_wild_card_and_in_excludes(self):
        found = self._names(
            exclusion_prompt="Tom Petty",
            exclusion_rationale=[{"term": "Tom Petty", "defends_against": "'heartland rock' pulls his sound"}],
            wild_card={"style_prompt": "southern rock, warm male vocal, Tom Petty jangle", "exclusion_prompt": "tom petty",
                       "exclusion_rationale": [{"term": "tom petty", "defends_against": "'southern rock'"}]})
        self.assertEqual(sorted(found), [("exclusion_prompt", "high", "Tom Petty"),
                                         ("wild_card_exclusion_prompt", "high", "Tom Petty"),
                                         ("wild_card_prompt", "high", "Tom Petty")])

    def test_one_word_name_is_medium_and_matches_whole_words_only(self):
        self.assertEqual(self._names(style_prompt="slowcore rock, low drone, warm male vocal"),
                         [("style_prompt", "medium", "Low")])
        self.assertEqual(self._names(style_prompt="slowcore rock, lower register, slow, warm male vocal"), [])

    def test_unlisted_name_is_not_detected(self):
        self.assertEqual(self._names(reference_names=[], style_prompt="heartland rock like tom petty, warm vocal"), [])

    def test_emit_refuses_a_name_drop(self):
        package = {**self.BASE, "style_prompt": "heartland rock, Tom Petty jangle, warm male vocal"}
        out, code = validate_prompt.emit_package(package, validate_prompt.validate_package(package))
        self.assertEqual((code, out["status"]), (1, "emit_refused"))

    def test_non_list_reference_names_exits_2(self):
        result = _run_cli("--stdin", stdin=json.dumps({**self.BASE, "reference_names": "Tom Petty"}))
        self.assertEqual(result.returncode, 2)
        self.assertIn("reference_names", result.stderr)


class TestSliderValues(unittest.TestCase):
    def _range(self, sliders, **extra):
        report = validate_prompt.validate_package(
            {"model": "v6", "tier": "pro", "style_prompt": "indie rock, warm vocal", "sliders": sliders, **extra})
        return [(f["severity"], f.get("data", {}).get("slider")) for f in report["findings"] if f["category"] == "range"]

    def test_values_in_range_pass(self):
        self.assertEqual(self._range({"weirdness": 0, "style_influence": 100}), [])
        self.assertEqual(self._range({"weirdness": 55, "style_influence": 75, "audio_influence": None, "audio_source": None}), [])

    def test_out_of_range_is_high(self):
        self.assertEqual(self._range({"weirdness": 101, "style_influence": -1}),
                         [("high", "weirdness"), ("high", "style_influence")])

    def test_non_numeric_is_high(self):
        self.assertEqual(self._range({"weirdness": "high", "style_influence": True}),
                         [("high", "weirdness"), ("high", "style_influence")])

    def test_audio_influence_without_a_source_is_high(self):
        found = self._range({"weirdness": 50, "style_influence": 70, "audio_influence": 55})
        self.assertEqual(found, [("high", None)])

    def test_audio_influence_with_a_slot_is_reported_once(self):
        self.assertEqual(len(self._range({"audio_influence": 150, "audio_source": "voice"})), 1)
        self.assertEqual(len(self._range({"audio_influence": "loud", "audio_source": "persona"})), 1)


class TestExclusionCoverage(unittest.TestCase):
    BASE = {"model": "v6", "tier": "pro",
            "style_prompt": "heartland rock, warm male vocal, chimey electric guitar, driving groove"}

    def _exclusion(self, **overrides):
        report = validate_prompt.validate_package({**self.BASE, **overrides})
        return [(f["severity"], f["data"].get("terms")) for f in report["findings"] if f["category"] == "exclusion"]

    def test_exclude_without_an_entry_is_medium(self):
        found = self._exclusion(
            exclusion_prompt="steel guitar, autotune",
            exclusion_rationale=[{"term": "steel guitar", "defends_against": "'heartland rock' can pull pedal steel"}])
        self.assertEqual(found, [("medium", ["autotune"])])

    def test_excludes_with_no_rationale_at_all_are_medium(self):
        self.assertEqual(self._exclusion(exclusion_prompt="steel guitar, autotune"),
                         [("medium", ["steel guitar", "autotune"])])
        self.assertEqual(self._exclusion(), [])

    def test_one_entry_may_cover_a_whole_family(self):
        family = "choir, backing vocals, gang vocals, layered vocals, crowd chants"
        found = self._exclusion(
            style_prompt="gospel rock, solo lead vocal, one singer only, warm organ",
            exclusion_prompt=family,
            exclusion_rationale=[{"term": family, "defends_against": "'gospel rock' pulls a choir"}])
        self.assertEqual(found, [])

    def test_wild_card_excludes_need_entries_too(self):
        found = self._exclusion(wild_card={"style_prompt": "southern rock, warm male vocal, slide guitar lead",
                                           "exclusion_prompt": "banjo"})
        self.assertEqual(found, [("medium", ["banjo"])])

    def test_non_list_rationale_exits_2(self):
        result = _run_cli("--stdin", stdin=json.dumps({**self.BASE, "exclusion_prompt": "banjo",
                                                       "exclusion_rationale": "it drifts"}))
        self.assertEqual(result.returncode, 2)
        self.assertIn("exclusion_rationale", result.stderr)


class TestWildCardGroupVocals(unittest.TestCase):
    FAMILY = "choir, backing vocals, gang vocals, layered vocals, crowd chants"
    RATIONALE = [{"term": FAMILY, "defends_against": "'gospel rock' pulls a choir"}]

    def _pulls(self, wild_card):
        report = validate_prompt.validate_package({
            "model": "v6", "tier": "pro", "style_prompt": "gospel rock, solo lead vocal, warm organ",
            "exclusion_prompt": self.FAMILY, "exclusion_rationale": self.RATIONALE, "wild_card": wild_card})
        return [f["data"]["pulls"] for f in report["findings"] if f.get("data", {}).get("pulls")]

    def test_wild_card_inheriting_the_excludes_is_checked(self):
        self.assertEqual(self._pulls({"style_prompt": "gospel rock, call-and-response verses, warm organ",
                                      "exclusion_prompt": None}), [["call-and-response"]])

    def test_wild_card_with_its_own_excludes_is_checked_against_them(self):
        self.assertEqual(self._pulls({"style_prompt": "gospel rock, gang shouts, warm organ",
                                      "exclusion_prompt": "choir",
                                      "exclusion_rationale": [{"term": "choir", "defends_against": "'gospel rock'"}]}),
                         [["gang"]])
        self.assertEqual(self._pulls({"style_prompt": "gospel rock, gang shouts, warm organ",
                                      "exclusion_prompt": "steel guitar",
                                      "exclusion_rationale": [{"term": "steel guitar", "defends_against": "'gospel rock'"}]}),
                         [])


class TestEnvironment(unittest.TestCase):
    TEXT = "heartland rock, caf\u00e9 warmth, \u201cclose\u201d male vocal \u2014 slow"

    def test_missing_shared_folder_exits_2_with_a_reason(self):
        tmp_path = _tmp_path(self)
        shutil.copy(SCRIPT_PATH, tmp_path / "validate_prompt.py")
        result = subprocess.run([sys.executable, str(tmp_path / "validate_prompt.py"), "--style", "indie rock"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("_shared", result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "error")

    def test_stdin_and_stdout_are_utf8_whatever_the_stream_encoding(self):
        package = {**TestEmit.BASE, "style_prompt": self.TEXT}
        env = {**os.environ, "PYTHONIOENCODING": "ascii"}
        result = subprocess.run([sys.executable, str(SCRIPT_PATH), "--stdin", "--emit"],
                                input=json.dumps(package, ensure_ascii=False).encode("utf-8"),
                                capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        out = json.loads(result.stdout.decode("utf-8"))
        self.assertEqual(out["style_prompt"], self.TEXT)
        self.assertEqual(out["style_prompt_chars"], len(self.TEXT))

    def test_package_file_and_output_file_are_utf8_in_a_non_utf8_locale(self):
        tmp_path = _tmp_path(self)
        source, target = tmp_path / "package.json", tmp_path / "out.json"
        source.write_text(json.dumps({**TestEmit.BASE, "style_prompt": self.TEXT}, ensure_ascii=False), encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING" and not k.startswith("LC_")}
        env.update({"LC_ALL": "C", "LANG": "C", "PYTHONCOERCECLOCALE": "0", "PYTHONUTF8": "0"})
        result = subprocess.run([sys.executable, str(SCRIPT_PATH), "--input-file", str(source), "--emit",
                                 "--output", str(target)], capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        out = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(out["style_prompt"], self.TEXT)
        self.assertEqual(out["style_prompt_chars"], len(self.TEXT))


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
        findings = validate_prompt.validate_exclusion_prompt("screaming, steel guitar, autotune, synth pads")
        self.assertTrue([f for f in findings if f["severity"] == "medium" and "many" in f["issue"].lower()])

    def test_whole_group_vocal_family_counts_as_one_item(self):
        findings = validate_prompt.validate_exclusion_prompt(
            "choir, backing vocals, gang vocals, layered vocals, crowd chants, autotune")
        self.assertFalse([f for f in findings if "many" in f["issue"].lower() or "family" in f["issue"].lower()])

    def test_partial_group_vocal_family_is_medium(self):
        findings = validate_prompt.validate_exclusion_prompt("choir, backing vocals, gang vocals, layered vocals")
        fam = [f for f in findings if "family" in f["issue"].lower()]
        self.assertEqual(fam[0]["severity"], "medium")
        self.assertEqual(fam[0]["data"]["missing"], ["crowd chants"])

    def test_single_family_member_is_low(self):
        findings = validate_prompt.validate_exclusion_prompt("choir, autotune")
        fam = [f for f in findings if "family" in f["issue"].lower()]
        self.assertEqual(fam[0]["severity"], "low")

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

    def test_free_with_voice_settings_or_wild_card_excludes_flagged(self):
        report = validate_prompt.validate_package({
            "model": "v6-mini", "tier": "free", "style_prompt": "indie rock, warm vocal",
            "sliders": {"audio_influence": 55, "audio_source": "voice"},
            "wild_card": {"style_prompt": "indie folk, warm vocal", "exclusion_prompt": "autotune"},
        })
        issues = [f["issue"] for f in self._tier(report)]
        self.assertEqual(len([i for i in issues if "audio_influence" in i]), 1)
        self.assertEqual(len([i for i in issues if "wild card carries Exclude Styles" in i]), 1)
        self.assertTrue(all(f["severity"] == "high" for f in self._tier(report)))

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
