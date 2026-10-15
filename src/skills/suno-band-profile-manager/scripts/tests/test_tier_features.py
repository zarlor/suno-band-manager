#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for tier-features.py"""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location(
    "tier_features",
    Path(__file__).parent.parent / "tier-features.py"
)
tier_features_mod = module_from_spec(spec)
spec.loader.exec_module(tier_features_mod)
get_tier_features = tier_features_mod.get_tier_features


class TestTierFeatures(unittest.TestCase):
    def test_free_tier(self):
        result = get_tier_features("free")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["tier"], "free")
        self.assertIs(result["sliders_available"], False)
        self.assertIs(result["personas_available"], False)
        self.assertIs(result["audio_influence_available"], False)
        self.assertIs(result["studio_available"], False)
        self.assertEqual(result["models"], ["v6-mini"])

    def test_pro_tier(self):
        result = get_tier_features("pro")
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["sliders_available"], True)
        self.assertIs(result["personas_available"], True)
        self.assertIs(result["audio_influence_available"], True)
        self.assertIs(result["studio_available"], False)
        self.assertIn("v6", result["models"])
        self.assertIn("v6-wild", result["models"])
        self.assertEqual(result["default_model"], "v6")
        self.assertGreaterEqual(len(result["unavailable"]), 1)  # Studio and related

    def test_premier_tier(self):
        result = get_tier_features("premier")
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["sliders_available"], True)
        self.assertIs(result["studio_available"], True)
        self.assertEqual(len(result["unavailable"]), 0)  # Everything available

    def test_studio_is_premier_only(self):
        """Studio 2.0 did not move any capability down to Pro."""
        self.assertIs(get_tier_features("free")["studio_available"], False)
        self.assertIs(get_tier_features("pro")["studio_available"], False)

        premier = get_tier_features("premier")
        self.assertIs(premier["studio_available"], True)
        self.assertEqual(premier["studio_version"], "2.0")

        pro_unavailable = " ".join(get_tier_features("pro")["unavailable"]).lower()
        self.assertIn("studio", pro_unavailable)

    def test_studio_1x_feature_names_are_not_offered_as_current(self):
        """Archived Studio 1.x names must not appear in any tier's feature lists."""
        for tier in ["free", "pro", "premier"]:
            result = get_tier_features(tier)
            listed = " ".join(result["available"] + result["unavailable"]).lower()
            for archived in ["warp marker", "remove fx", "alternates", "quick replace", "milo-1080", "stem cover", "heal edits"]:
                self.assertNotIn(archived, listed, f"{archived} surfaced as a current feature on {tier}")
            # ...but they remain discoverable as an explicit archive list
            self.assertIn("Warp Markers", result["notes"]["studio_1x_archived"])

    def test_take_lanes_is_not_archived(self):
        """Take Lanes and comping survived into the current Studio docs.

    Only the 'Alternates' / 'Quick Replace' names were archived — the
    per-take auditioning capability itself is still current, so it must not
    be listed alongside the genuinely-archived 1.x feature names.
    """
        archived = get_tier_features("premier")["notes"]["studio_1x_archived"]
        joined = " ".join(archived).lower()
        self.assertNotIn("take lane", joined)
        self.assertNotIn("comping", joined)
        self.assertIn("Alternates", archived)

    def test_invalid_tier(self):
        result = get_tier_features("ultimate")
        self.assertEqual(result["status"], "fail")
        self.assertIn("error", result)

    def test_case_insensitive(self):
        result = get_tier_features("PRO")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["tier"], "pro")

    def test_free_has_unavailable_features(self):
        result = get_tier_features("free")
        self.assertGreater(len(result["unavailable"]), 5)  # Many features gated

    def test_all_tiers_have_available(self):
        for tier in ["free", "pro", "premier"]:
            result = get_tier_features(tier)
            self.assertGreater(len(result["available"]), 0)

    def test_all_tiers_have_pricing(self):
        for tier in ["free", "pro", "premier"]:
            result = get_tier_features(tier)
            self.assertIn("pricing", result)
            self.assertIn("monthly", result["pricing"])
            self.assertIn("annual_monthly", result["pricing"])

    def test_all_tiers_have_song_length(self):
        for tier in ["free", "pro", "premier"]:
            result = get_tier_features(tier)
            self.assertIn("song_length_max", result)

    def test_download_quality_is_no_longer_a_tier_differentiator(self):
        """Bitrate/format was dropped: downloads are gated by COUNT, not quality."""
        for tier in ["free", "pro", "premier"]:
            self.assertNotIn("download_quality", get_tier_features(tier))

    def test_all_tiers_have_download_allowance(self):
        for tier in ["free", "pro", "premier"]:
            downloads = get_tier_features(tier)["downloads"]
            self.assertEqual(downloads["effective"], "2026-09-03")
            self.assertIn("accounting", downloads)

    def test_download_caps_by_tier(self):
        free = get_tier_features("free")["downloads"]
        self.assertEqual(free["lifetime"], 7)
        self.assertIsNone(free["monthly"])
        self.assertIs(free["personal_non_commercial_only"], True)

        pro = get_tier_features("pro")["downloads"]
        self.assertEqual(pro["monthly"], 20)
        self.assertIs(pro["studio_exempt"], False)

        premier = get_tier_features("premier")["downloads"]
        self.assertEqual(premier["monthly"], 60)
        self.assertIs(premier["studio_exempt"], True)

    def test_commercial_use_is_bound_to_permitted_downloads(self):
        free = get_tier_features("free")["commercial_use"]
        self.assertIs(free["allowed"], False)

        for tier in ["pro", "premier"]:
            commercial = get_tier_features(tier)["commercial_use"]
            self.assertIs(commercial["allowed"], True)
            self.assertIn("permitted download", commercial["condition"])

    def test_stem_modes_and_advanced_split_gating(self):
        self.assertEqual(get_tier_features("free")["stem_modes"], [])
        self.assertIs(get_tier_features("free")["advanced_split_available"], False)

        pro = get_tier_features("pro")
        pro_modes = [mode["name"] for mode in pro["stem_modes"]]
        self.assertEqual(pro_modes, ["Auto Split", "Split from Mix"])
        self.assertIs(pro["advanced_split_available"], False)

        premier = get_tier_features("premier")
        premier_modes = [mode["name"] for mode in premier["stem_modes"]]
        self.assertEqual(premier_modes, ["Auto Split", "Split from Mix", "Advanced Split"])
        self.assertIs(premier["advanced_split_available"], True)
        advanced = premier["stem_modes"][2]
        self.assertIs(advanced["premier_only"], True)
        # Cost is stem-plus-complement: 10 per extraction, 20 total per stem.
        self.assertIn("10 credits per extraction", advanced["credits"])
        self.assertIn("20 credits total per stem", advanced["credits"])
        self.assertIn("complement", advanced["credits"])

    def test_stem_credit_costs_are_stated(self):
        pro = get_tier_features("pro")["stem_modes"]
        self.assertIn("50 credits per extraction", pro[0]["credits"])        # Auto Split
        # Split from Mix bills per extraction, and an extraction yields two stems
        # (the split plus its complement) — hence the 20-credit total.
        self.assertIn("10 credits per extraction", pro[1]["credits"])
        self.assertIn("20 credits total for both stems", pro[1]["credits"])

    def test_all_tiers_have_credit_cost(self):
        for tier in ["free", "pro", "premier"]:
            result = get_tier_features(tier)
            self.assertIn("credit_cost", result)
            self.assertEqual(result["credit_cost"]["generation"], 10)  # one Create = 2 songs
            self.assertEqual(result["credit_cost"]["per_song"], 5)
            self.assertEqual(result["credit_cost"]["extension"], 5)

    def test_premier_credit_allowance(self):
        self.assertIn("10,000", get_tier_features("premier")["credits_included"])
        self.assertIn("2,500", get_tier_features("pro")["credits_included"])

    def test_audio_upload_limits(self):
        self.assertEqual(get_tier_features("free")["audio_upload_max"], "8 min")
        self.assertEqual(get_tier_features("pro")["audio_upload_max"], "30 min")
        self.assertEqual(get_tier_features("premier")["audio_upload_max"], "30 min")

    def test_replace_section_available_from_pro(self):
        self.assertIs(get_tier_features("free")["replace_section_available"], False)
        self.assertIs(get_tier_features("pro")["replace_section_available"], True)
        self.assertIs(get_tier_features("premier")["replace_section_available"], True)

    def test_notes_carry_provenance_and_retirement(self):
        notes = get_tier_features("pro")["notes"]
        self.assertIn("annual", notes["pricing_display"].lower())
        self.assertIn("retire", notes["model_retirement"].lower())
        self.assertIn("community-attested", notes["character_limits"])

    def test_last_validated_is_reported(self):
        for tier in ["free", "pro", "premier"]:
            self.assertEqual(get_tier_features(tier)["last_validated"], "2026-09-12")

    def test_free_pricing_is_zero(self):
        result = get_tier_features("free")
        self.assertEqual(result["pricing"]["monthly"], 0)
        self.assertEqual(result["pricing"]["annual_monthly"], 0)

    def test_pro_pricing(self):
        result = get_tier_features("pro")
        self.assertEqual(result["pricing"]["monthly"], 10)
        self.assertEqual(result["pricing"]["annual_monthly"], 8)

    def test_premier_pricing(self):
        result = get_tier_features("premier")
        self.assertEqual(result["pricing"]["monthly"], 30)
        self.assertEqual(result["pricing"]["annual_monthly"], 24)

    def test_pre_v6_models_are_retired_not_offered(self):
        """Every pre-v6 model was retired 2026-09-09: none is selectable on any tier."""
        for tier in ["free", "pro", "premier"]:
            result = get_tier_features(tier)
            self.assertEqual(result["legacy_models"], [])
            self.assertIn("v5.5 Pro", result["retired_models"])
            self.assertIn("v4.5-all", result["retired_models"])
            self.assertFalse(set(result["models"]) & set(result["retired_models"]))

    def test_v6_controls_at_paid_tiers(self):
        for tier in ["pro", "premier"]:
            result = get_tier_features(tier)
            self.assertIs(result["max_mode_available"], True)
            self.assertIs(result["variety_available"], True)
            self.assertIs(result["personalize_available"], True)
            available = " ".join(result["available"])
            self.assertIn("Max Mode", available)
            self.assertIn("Variety", available)
        notes = get_tier_features("pro")["notes"]["v6_controls"]
        self.assertIn("rewrites the style prompt", notes["variety"])
        self.assertIn("2x credits", notes["max_mode"])

    def test_free_tier_v6_controls_unverified(self):
        free = get_tier_features("free")
        self.assertIsNone(free["max_mode_available"])
        self.assertIsNone(free["variety_available"])


if __name__ == "__main__":
    unittest.main()
