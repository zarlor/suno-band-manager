#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for shared Suno constants — verify internal consistency."""
import sys
import unittest
from pathlib import Path

# Add _shared to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from suno_constants import (
    VALID_MODELS, VALID_TIERS, PAID_TIERS, FREE_TIER_MODEL,
    CURRENT_MODELS, RETIRED_MODELS, DEFAULT_MODEL, MODEL_RETIREMENT_DATE,
    STYLE_PROMPT_LIMITS, STYLE_PROMPT_DEFAULT_MAX,
    CRITICAL_ZONE, EXCLUSION_RECOMMENDED_MAX, EXCLUSION_HARD_MAX,
    SUNO_LYRICS_HARD_LIMIT, SUNO_LYRICS_QUALITY_BUDGET,
    HEAVY_VOCAL_TRIGGERS, VOCAL_SAFE_PAIRINGS, KEYBOARD_PULL_WORDS,
    SHOUT_TRIGGER_CHAR, GENRE_SIGNALS,
)


class TestSunoConstants(unittest.TestCase):

    def test_valid_models_is_frozenset(self):
        self.assertIsInstance(VALID_MODELS, frozenset)

    def test_valid_tiers_is_frozenset(self):
        self.assertIsInstance(VALID_TIERS, frozenset)

    def test_paid_tiers_subset_of_valid_tiers(self):
        self.assertTrue(PAID_TIERS.issubset(VALID_TIERS))

    def test_free_tier_not_in_paid(self):
        self.assertNotIn("free", PAID_TIERS)

    def test_free_tier_model_is_valid(self):
        self.assertIn(FREE_TIER_MODEL, VALID_MODELS)

    def test_style_prompt_limits_models_are_valid(self):
        for model in STYLE_PROMPT_LIMITS:
            self.assertIn(model, VALID_MODELS, f"Model '{model}' in STYLE_PROMPT_LIMITS but not in VALID_MODELS")

    def test_all_models_have_style_limits(self):
        for model in VALID_MODELS:
            self.assertIn(model, STYLE_PROMPT_LIMITS, f"Model '{model}' in VALID_MODELS but missing from STYLE_PROMPT_LIMITS")

    def test_style_prompt_default_max_is_positive(self):
        self.assertGreater(STYLE_PROMPT_DEFAULT_MAX, 0)

    def test_critical_zone_less_than_default_max(self):
        self.assertLessEqual(CRITICAL_ZONE, STYLE_PROMPT_DEFAULT_MAX)

    def test_exclusion_recommended_less_than_hard(self):
        self.assertLessEqual(EXCLUSION_RECOMMENDED_MAX, EXCLUSION_HARD_MAX)

    def test_lyrics_quality_budget_less_than_hard_limit(self):
        self.assertLess(SUNO_LYRICS_QUALITY_BUDGET, SUNO_LYRICS_HARD_LIMIT)

    def test_lyrics_limits_are_positive(self):
        self.assertGreater(SUNO_LYRICS_HARD_LIMIT, 0)
        self.assertGreater(SUNO_LYRICS_QUALITY_BUDGET, 0)

    def test_v55_pro_present(self):
        """v5.5 Pro stays recognized (retired, but older profiles still name it)."""
        self.assertIn("v5.5 Pro", VALID_MODELS)
        self.assertIn("v5.5 Pro", STYLE_PROMPT_LIMITS)
        self.assertIn("v5.5 Pro", RETIRED_MODELS)

    def test_v6_family_is_current(self):
        self.assertEqual(CURRENT_MODELS, frozenset({"v6", "v6-wild", "v6-mini"}))
        self.assertEqual(MODEL_RETIREMENT_DATE, "2026-09-09")

    def test_current_and_retired_are_disjoint(self):
        self.assertFalse(CURRENT_MODELS & RETIRED_MODELS)

    def test_valid_models_is_current_plus_retired(self):
        self.assertEqual(VALID_MODELS, CURRENT_MODELS | RETIRED_MODELS)

    def test_free_tier_and_default_models_are_current(self):
        self.assertIn(FREE_TIER_MODEL, CURRENT_MODELS)
        self.assertIn(DEFAULT_MODEL, CURRENT_MODELS)


class TestStylePromptTriggers(unittest.TestCase):
    """Tests for the style-prompt safety trigger tables."""

    def test_heavy_vocal_triggers_are_frozenset(self):
        self.assertIsInstance(HEAVY_VOCAL_TRIGGERS, frozenset)

    def test_heavy_vocal_triggers_cover_documented_terms(self):
        """The reference documents metal/sludge/death/thrash/black as scream triggers."""
        for term in ("metal", "sludge", "death", "thrash", "black"):
            self.assertIn(term, HEAVY_VOCAL_TRIGGERS)

    def test_keyboard_pull_words_cover_documented_terms(self):
        """The reference documents baroque/orchestral/cinematic/rock opera as keyboard pulls."""
        for term in ("baroque", "orchestral", "cinematic", "rock opera"):
            self.assertIn(term, KEYBOARD_PULL_WORDS)

    def test_keyboard_pull_words_are_frozenset(self):
        self.assertIsInstance(KEYBOARD_PULL_WORDS, frozenset)

    def test_keyboard_pull_and_genre_signals_disjoint(self):
        """Texture modifiers must not double as genres — a word cannot both satisfy
        front-loading AND read as a dangerous keyboard pull (self-contradicting signal)."""
        overlap = KEYBOARD_PULL_WORDS & GENRE_SIGNALS
        self.assertEqual(overlap, frozenset(), (
            f"KEYBOARD_PULL_WORDS and GENRE_SIGNALS overlap on {sorted(overlap)}; "
            "these are texture modifiers, not genres — remove from GENRE_SIGNALS."
        ))

    def test_vocal_safe_pairings_nonempty_strings(self):
        self.assertGreater(len(VOCAL_SAFE_PAIRINGS), 0)
        self.assertTrue(all(isinstance(p, str) and p for p in VOCAL_SAFE_PAIRINGS))

    def test_shout_trigger_char_is_exclamation(self):
        self.assertEqual(SHOUT_TRIGGER_CHAR, "!")

    def test_genre_signals_is_frozenset(self):
        self.assertIsInstance(GENRE_SIGNALS, frozenset)

    def test_genre_signals_cover_module_lanes(self):
        """Front-loading detection must not false-trip on this module's heavy/southern lanes."""
        for term in ("swamp metal", "heartland rock", "prog rock", "slowcore", "doom",
                     "southern rock", "americana"):
            self.assertIn(term, GENRE_SIGNALS, f"GENRE_SIGNALS missing '{term}'")

    def test_genre_signals_lowercase(self):
        """Detection lowercases the prompt before matching, so signals must be lowercase."""
        self.assertTrue(all(g == g.lower() for g in GENRE_SIGNALS))

    def test_pairings_lowercase(self):
        self.assertTrue(all(p == p.lower() for p in VOCAL_SAFE_PAIRINGS))

    def test_genre_signals_cover_added_lanes(self):
        from suno_constants import GENRE_SIGNALS
        for word in ("thrash", "krautrock", "rockabilly"):
            self.assertIn(word, GENRE_SIGNALS)


if __name__ == "__main__":
    unittest.main()
