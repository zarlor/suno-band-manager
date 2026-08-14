#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for tier-features.py"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location(
    "tier_features",
    Path(__file__).parent.parent / "tier-features.py"
)
tier_features_mod = module_from_spec(spec)
spec.loader.exec_module(tier_features_mod)
get_tier_features = tier_features_mod.get_tier_features


def test_free_tier():
    result = get_tier_features("free")
    assert result["status"] == "pass"
    assert result["tier"] == "free"
    assert result["sliders_available"] is False
    assert result["personas_available"] is False
    assert result["audio_influence_available"] is False
    assert result["studio_available"] is False
    assert "v4.5-all" in result["models"]
    assert len(result["models"]) == 1


def test_pro_tier():
    result = get_tier_features("pro")
    assert result["status"] == "pass"
    assert result["sliders_available"] is True
    assert result["personas_available"] is True
    assert result["audio_influence_available"] is True
    assert result["studio_available"] is False
    assert "v5 Pro" in result["models"]
    assert "v5.5 Pro" in result["models"]  # Pro gets the top model, not just legacy
    assert len(result["unavailable"]) >= 1  # Studio and related


def test_premier_tier():
    result = get_tier_features("premier")
    assert result["status"] == "pass"
    assert result["sliders_available"] is True
    assert result["studio_available"] is True
    assert len(result["unavailable"]) == 0  # Everything available


def test_studio_is_premier_only():
    """Studio 2.0 did not move any capability down to Pro."""
    assert get_tier_features("free")["studio_available"] is False
    assert get_tier_features("pro")["studio_available"] is False

    premier = get_tier_features("premier")
    assert premier["studio_available"] is True
    assert premier["studio_version"] == "2.0"

    pro_unavailable = " ".join(get_tier_features("pro")["unavailable"]).lower()
    assert "studio" in pro_unavailable


def test_studio_1x_feature_names_are_not_offered_as_current():
    """Archived Studio 1.x names must not appear in any tier's feature lists."""
    for tier in ["free", "pro", "premier"]:
        result = get_tier_features(tier)
        listed = " ".join(result["available"] + result["unavailable"]).lower()
        for archived in ["warp marker", "remove fx", "alternates", "quick replace", "milo-1080", "stem cover", "heal edits"]:
            assert archived not in listed, f"{archived} surfaced as a current feature on {tier}"
        # ...but they remain discoverable as an explicit archive list
        assert "Warp Markers" in result["notes"]["studio_1x_archived"]


def test_take_lanes_is_not_archived():
    """Take Lanes and comping survived into the current Studio docs.

    Only the 'Alternates' / 'Quick Replace' names were archived — the
    per-take auditioning capability itself is still current, so it must not
    be listed alongside the genuinely-archived 1.x feature names.
    """
    archived = get_tier_features("premier")["notes"]["studio_1x_archived"]
    joined = " ".join(archived).lower()
    assert "take lane" not in joined
    assert "comping" not in joined
    assert "Alternates" in archived


def test_invalid_tier():
    result = get_tier_features("ultimate")
    assert result["status"] == "fail"
    assert "error" in result


def test_case_insensitive():
    result = get_tier_features("PRO")
    assert result["status"] == "pass"
    assert result["tier"] == "pro"


def test_free_has_unavailable_features():
    result = get_tier_features("free")
    assert len(result["unavailable"]) > 5  # Many features gated


def test_all_tiers_have_available():
    for tier in ["free", "pro", "premier"]:
        result = get_tier_features(tier)
        assert len(result["available"]) > 0


def test_all_tiers_have_pricing():
    for tier in ["free", "pro", "premier"]:
        result = get_tier_features(tier)
        assert "pricing" in result
        assert "monthly" in result["pricing"]
        assert "annual_monthly" in result["pricing"]


def test_all_tiers_have_song_length():
    for tier in ["free", "pro", "premier"]:
        result = get_tier_features(tier)
        assert "song_length_max" in result


def test_download_quality_is_no_longer_a_tier_differentiator():
    """Bitrate/format was dropped: downloads are gated by COUNT, not quality."""
    for tier in ["free", "pro", "premier"]:
        assert "download_quality" not in get_tier_features(tier)


def test_all_tiers_have_download_allowance():
    for tier in ["free", "pro", "premier"]:
        downloads = get_tier_features(tier)["downloads"]
        assert downloads["effective"] == "2026-09-03"
        assert "accounting" in downloads


def test_download_caps_by_tier():
    free = get_tier_features("free")["downloads"]
    assert free["lifetime"] == 7
    assert free["monthly"] is None
    assert free["personal_non_commercial_only"] is True

    pro = get_tier_features("pro")["downloads"]
    assert pro["monthly"] == 20
    assert pro["studio_exempt"] is False

    premier = get_tier_features("premier")["downloads"]
    assert premier["monthly"] == 60
    assert premier["studio_exempt"] is True


def test_commercial_use_is_bound_to_permitted_downloads():
    free = get_tier_features("free")["commercial_use"]
    assert free["allowed"] is False

    for tier in ["pro", "premier"]:
        commercial = get_tier_features(tier)["commercial_use"]
        assert commercial["allowed"] is True
        assert "permitted download" in commercial["condition"]


def test_stem_modes_and_advanced_split_gating():
    assert get_tier_features("free")["stem_modes"] == []
    assert get_tier_features("free")["advanced_split_available"] is False

    pro = get_tier_features("pro")
    pro_modes = [mode["name"] for mode in pro["stem_modes"]]
    assert pro_modes == ["Auto Split", "Split from Mix"]
    assert pro["advanced_split_available"] is False

    premier = get_tier_features("premier")
    premier_modes = [mode["name"] for mode in premier["stem_modes"]]
    assert premier_modes == ["Auto Split", "Split from Mix", "Advanced Split"]
    assert premier["advanced_split_available"] is True
    advanced = premier["stem_modes"][2]
    assert advanced["premier_only"] is True
    # Cost is stem-plus-complement: 10 per extraction, 20 total per stem.
    assert "10 credits per extraction" in advanced["credits"]
    assert "20 credits total per stem" in advanced["credits"]
    assert "complement" in advanced["credits"]


def test_stem_credit_costs_are_stated():
    pro = get_tier_features("pro")["stem_modes"]
    assert "50 credits per extraction" in pro[0]["credits"]        # Auto Split
    # Split from Mix bills per extraction, and an extraction yields two stems
    # (the split plus its complement) — hence the 20-credit total.
    assert "10 credits per extraction" in pro[1]["credits"]
    assert "20 credits total for both stems" in pro[1]["credits"]


def test_all_tiers_have_credit_cost():
    for tier in ["free", "pro", "premier"]:
        result = get_tier_features(tier)
        assert "credit_cost" in result
        assert result["credit_cost"]["generation"] == 10  # one Create = 2 songs
        assert result["credit_cost"]["per_song"] == 5
        assert result["credit_cost"]["extension"] == 5


def test_premier_credit_allowance():
    assert "10,000" in get_tier_features("premier")["credits_included"]
    assert "2,500" in get_tier_features("pro")["credits_included"]


def test_audio_upload_limits():
    assert get_tier_features("free")["audio_upload_max"] == "8 min"
    assert get_tier_features("pro")["audio_upload_max"] == "30 min"
    assert get_tier_features("premier")["audio_upload_max"] == "30 min"


def test_replace_section_available_from_pro():
    assert get_tier_features("free")["replace_section_available"] is False
    assert get_tier_features("pro")["replace_section_available"] is True
    assert get_tier_features("premier")["replace_section_available"] is True


def test_notes_carry_provenance_and_retirement():
    notes = get_tier_features("pro")["notes"]
    assert "annual" in notes["pricing_display"].lower()
    assert "retire" in notes["model_retirement"].lower()
    assert "community-attested" in notes["character_limits"]


def test_last_validated_is_reported():
    for tier in ["free", "pro", "premier"]:
        assert get_tier_features(tier)["last_validated"] == "2026-08-13"


def test_free_pricing_is_zero():
    result = get_tier_features("free")
    assert result["pricing"]["monthly"] == 0
    assert result["pricing"]["annual_monthly"] == 0


def test_pro_pricing():
    result = get_tier_features("pro")
    assert result["pricing"]["monthly"] == 10
    assert result["pricing"]["annual_monthly"] == 8


def test_premier_pricing():
    result = get_tier_features("premier")
    assert result["pricing"]["monthly"] == 30
    assert result["pricing"]["annual_monthly"] == 24


def test_legacy_models_flagged():
    for tier in ["pro", "premier"]:
        result = get_tier_features(tier)
        assert "legacy_models" in result
        assert "v4 Pro" in result["legacy_models"]
        # v5.5 Pro is the current model — it must never be listed as legacy
        assert "v5.5 Pro" not in result["legacy_models"]
