#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for shared Suno constants — verify internal consistency."""
import sys
from pathlib import Path

# Add _shared to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from suno_constants import (
    VALID_MODELS, VALID_TIERS, PAID_TIERS, FREE_TIER_MODEL,
    STYLE_PROMPT_LIMITS, STYLE_PROMPT_DEFAULT_MAX,
    CRITICAL_ZONE, EXCLUSION_RECOMMENDED_MAX, EXCLUSION_HARD_MAX,
    SUNO_LYRICS_HARD_LIMIT, SUNO_LYRICS_QUALITY_BUDGET,
    HEAVY_VOCAL_TRIGGERS, VOCAL_SAFE_PAIRINGS, KEYBOARD_PULL_WORDS,
    SHOUT_TRIGGER_CHAR, GENRE_SIGNALS,
)


class TestSunoConstants:

    def test_valid_models_is_frozenset(self):
        assert isinstance(VALID_MODELS, frozenset)

    def test_valid_tiers_is_frozenset(self):
        assert isinstance(VALID_TIERS, frozenset)

    def test_paid_tiers_subset_of_valid_tiers(self):
        assert PAID_TIERS.issubset(VALID_TIERS)

    def test_free_tier_not_in_paid(self):
        assert "free" not in PAID_TIERS

    def test_free_tier_model_is_valid(self):
        assert FREE_TIER_MODEL in VALID_MODELS

    def test_style_prompt_limits_models_are_valid(self):
        for model in STYLE_PROMPT_LIMITS:
            assert model in VALID_MODELS, f"Model '{model}' in STYLE_PROMPT_LIMITS but not in VALID_MODELS"

    def test_all_models_have_style_limits(self):
        for model in VALID_MODELS:
            assert model in STYLE_PROMPT_LIMITS, f"Model '{model}' in VALID_MODELS but missing from STYLE_PROMPT_LIMITS"

    def test_style_prompt_default_max_is_positive(self):
        assert STYLE_PROMPT_DEFAULT_MAX > 0

    def test_critical_zone_less_than_default_max(self):
        assert CRITICAL_ZONE <= STYLE_PROMPT_DEFAULT_MAX

    def test_exclusion_recommended_less_than_hard(self):
        assert EXCLUSION_RECOMMENDED_MAX <= EXCLUSION_HARD_MAX

    def test_lyrics_quality_budget_less_than_hard_limit(self):
        assert SUNO_LYRICS_QUALITY_BUDGET < SUNO_LYRICS_HARD_LIMIT

    def test_lyrics_limits_are_positive(self):
        assert SUNO_LYRICS_HARD_LIMIT > 0
        assert SUNO_LYRICS_QUALITY_BUDGET > 0

    def test_v55_pro_present(self):
        """v5.5 Pro must be in both VALID_MODELS and STYLE_PROMPT_LIMITS."""
        assert "v5.5 Pro" in VALID_MODELS
        assert "v5.5 Pro" in STYLE_PROMPT_LIMITS


class TestStylePromptTriggers:
    """Tests for the style-prompt safety trigger tables."""

    def test_heavy_vocal_triggers_are_frozenset(self):
        assert isinstance(HEAVY_VOCAL_TRIGGERS, frozenset)

    def test_heavy_vocal_triggers_cover_documented_terms(self):
        """The reference documents metal/sludge/death/thrash/black as scream triggers."""
        for term in ("metal", "sludge", "death", "thrash", "black"):
            assert term in HEAVY_VOCAL_TRIGGERS

    def test_keyboard_pull_words_cover_documented_terms(self):
        """The reference documents baroque/orchestral/cinematic as keyboard pulls."""
        for term in ("baroque", "orchestral", "cinematic"):
            assert term in KEYBOARD_PULL_WORDS

    def test_keyboard_pull_words_are_frozenset(self):
        assert isinstance(KEYBOARD_PULL_WORDS, frozenset)

    def test_vocal_safe_pairings_nonempty_strings(self):
        assert len(VOCAL_SAFE_PAIRINGS) > 0
        assert all(isinstance(p, str) and p for p in VOCAL_SAFE_PAIRINGS)

    def test_shout_trigger_char_is_exclamation(self):
        assert SHOUT_TRIGGER_CHAR == "!"

    def test_genre_signals_is_frozenset(self):
        assert isinstance(GENRE_SIGNALS, frozenset)

    def test_genre_signals_cover_module_lanes(self):
        """Front-loading detection must not false-trip on this module's heavy/southern lanes."""
        for term in ("swamp metal", "heartland rock", "prog rock", "slowcore", "doom",
                     "southern rock", "americana"):
            assert term in GENRE_SIGNALS, f"GENRE_SIGNALS missing '{term}'"

    def test_genre_signals_lowercase(self):
        """Detection lowercases the prompt before matching, so signals must be lowercase."""
        assert all(g == g.lower() for g in GENRE_SIGNALS)

    def test_pairings_lowercase(self):
        assert all(p == p.lower() for p in VOCAL_SAFE_PAIRINGS)
