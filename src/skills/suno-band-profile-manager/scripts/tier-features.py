#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Return Suno feature availability for a given subscription tier.

Maps each tier (free, pro, premier) to its available and unavailable features,
helping the agent and user understand what profile options are valid.

Authoritative for headless/script consumers. The human-readable twin is
`references/tier-features.md` — the two must agree; update both together.

Last validated against Suno: 2026-08-13 (Studio 2.0; download caps and ToS
effective 2026-09-03; three-mode stem separation).
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Graceful degradation: if the _shared constants module can't be imported
# (relocated skill, web sandbox), fall back to the literal tier set so the
# script still runs rather than crashing on an uncaught ImportError.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
try:
    from suno_constants import VALID_TIERS
except ImportError:
    VALID_TIERS = {"free", "pro", "premier"}


LAST_VALIDATED = "2026-08-13"

DOWNLOAD_LIMITS_EFFECTIVE = "2026-09-03"

DOWNLOAD_ACCOUNTING = (
    "One song counts as one download regardless of format or repeat downloads; "
    "all stems of a song are part of that song's single download; failed "
    "downloads do not count. Limits apply retroactively to the whole back "
    "catalogue. Streaming, playback, and on-platform sharing stay unlimited."
)

PRICING_DISPLAY_NOTE = (
    "The pricing page displays $8 (Pro) and $24 (Premier) alongside a "
    "'Monthly / Annual save 20%' toggle, while press coverage reports $10 and "
    "$30 month-to-month. Most likely reading: the displayed figures are "
    "annual-billing per-month rates. Flagged, not confirmed — quote the "
    "displayed figure and the toggle rather than a single monthly price."
)

MODEL_RETIREMENT_NOTICE = (
    "Suno has announced that new models will retire older versions — retiring "
    "means you can no longer generate with a model; existing songs stay "
    "playable. No official source names WHICH versions or WHEN, and there is "
    "no official statement on what happens to Voices, Custom Models, or "
    "Personas built on retired models. Extends, covers, and remixes of "
    "existing songs will run on the new models and may sound different."
)

CHARACTER_LIMIT_PROVENANCE = (
    "Style (1,000 chars; 200 on v4 Pro) and lyric (5,000 chars) limits are "
    "community-attested and validated by use — no Suno help article documents "
    "them. Enforce them; do not cite them as platform documentation."
)


def _downloads(monthly=None, lifetime=None, studio_exempt=False, personal_only=False):
    """Build the download-allowance block shared by every tier."""
    return {
        "effective": DOWNLOAD_LIMITS_EFFECTIVE,
        "monthly": monthly,
        "lifetime": lifetime,
        "resets": "billing date, no carryover" if monthly else None,
        "extra_purchasable": monthly is not None,
        "studio_exempt": studio_exempt,
        "personal_non_commercial_only": personal_only,
        "accounting": DOWNLOAD_ACCOUNTING,
    }


AUTO_SPLIT = {
    "name": "Auto Split",
    "output": "up to 12 stems",
    "credits": "50 credits per extraction",
    "premier_only": False,
}

SPLIT_FROM_MIX = {
    "name": "Split from Mix",
    "output": (
        "split derived from the mixed audio — the extracted stem plus its complement "
        "(replaces the legacy Vocals + Instrumental mode)"
    ),
    "credits": "10 credits per extraction, 20 credits total for both stems created",
    "premier_only": False,
}

ADVANCED_SPLIT = {
    "name": "Advanced Split",
    "output": "~100 instruments; choose which stems to create",
    # The doubling is stem-plus-complement, not two variations: each extraction
    # returns the chosen stem AND everything except that stem, and both count.
    # Verified against help.suno.com/en/articles/12702337 on 2026-08-14.
    "credits": "10 credits per extraction, 20 credits total per stem (each extraction returns the chosen stem plus its complement) — budget at 20 per stem",
    "premier_only": True,
}


TIER_FEATURES = {
    "free": {
        "available": [
            "v4.5-all model",
            "50 credits/day, renews daily (~10 songs)",
            "Vocal Gender selection",
            "Manual/Auto Lyrics mode",
            "Song Title",
            "8 min audio upload",
            "Song length determined by model — v4.5-all supports up to ~8 min",
            "My Taste (passive personalization, can be disabled)",
            "Voice recording entry point (available to try on free plans since 2026-08-07; "
            "clone creation and use in generation remain paid)",
            f"7 total lifetime trial downloads, personal and non-commercial (from {DOWNLOAD_LIMITS_EFFECTIVE})",
        ],
        "unavailable": [
            "All paid models (v4 Pro, v4.5 Pro, v4.5+ Pro, v5 Pro, v5.5 Pro)",
            "Commercial use",
            "Personas (consistent style reuse)",
            "Voices (clone creation and use in generation)",
            "Custom Models",
            "Weirdness slider (0-100)",
            "Style Influence slider (0-100)",
            "Audio Influence slider (0-100)",
            "Exclude Styles field",
            "Add Vocals / Add Instrumental",
            "Stem separation (Auto Split, Split from Mix, Advanced Split)",
            "Song Editor / Legacy Editor (Replace Section, Extend, Crop, Fade, Rearrange)",
            "Remaster",
            "Covers",
            "Suno Studio 2.0",
            "Duration slider (v5.5 web only)",
            "Priority queue",
            "Add-on credits",
            "Monthly download allowance (free tier gets 7 lifetime trial downloads only)",
        ],
        "models": ["v4.5-all"],
        "legacy_models": [],
        "sliders_available": False,
        "personas_available": False,
        "voices_available": False,
        "voice_recording_available": True,
        "custom_models_available": False,
        "audio_influence_available": False,
        "exclude_styles_available": False,
        "legacy_editor_available": False,
        "replace_section_available": False,
        "studio_available": False,
        "studio_version": None,
        "stem_modes": [],
        "advanced_split_available": False,
        "duration_slider_available": False,
        "song_length_max": "Determined by model — v4.5-all supports up to ~8 min",
        "audio_upload_max": "8 min",
        "credits_included": "50/day, renews daily (~10 songs)",
        "downloads": _downloads(lifetime=7, personal_only=True),
        "commercial_use": {
            "allowed": False,
            "condition": "Free outputs may be used for lawful, personal, non-commercial purposes only.",
        },
        "credit_cost": {"generation": 10, "per_song": 5, "extension": 5},
        "pricing": {"monthly": 0, "annual_monthly": 0},
    },
    "pro": {
        "available": [
            "v5.5 Pro plus legacy models (v4 Pro, v4.5 Pro, v4.5+ Pro, v5 Pro) and v4.5-all",
            "2,500 credits/month (~500 songs)",
            "Commercial use — for outputs obtained as a permitted download",
            "Personas (still supported; they live inside the Voices menu)",
            "Voices (v5.5 voice cloning)",
            "Custom Models (up to 3)",
            "Weirdness slider (0-100)",
            "Style Influence slider (0-100)",
            "Audio Influence slider (0-100, with Voice/Persona or audio upload)",
            "Exclude Styles field",
            "Add Vocals / Add Instrumental (beta)",
            "Covers (beta)",
            "Remaster (Subtle/Normal/High)",
            "Auto Split stems (up to 12, 50 credits per extraction)",
            "Split from Mix stems (20 credits total)",
            "30 min audio upload",
            "Song Editor / Legacy Editor (Replace Section, Extend, Crop, Fade, Rearrange)",
            "Duration slider (v5.5, web, requires Style set to Custom)",
            "Priority queue",
            "Add-on credits",
            "Song length determined by model — v4.5/v5/v5.5 support up to ~8 min",
            f"20 downloads per month (from {DOWNLOAD_LIMITS_EFFECTIVE})",
        ],
        "unavailable": [
            "Suno Studio 2.0 (browser-based generative DAW)",
            "Studio MIDI import/record/edit and audio-to-MIDI",
            "Studio chat bar (generates instruments, vocals, custom plugins)",
            "Studio wavetable synth, audio effects, and automation curves",
            "Studio 32-bit/48kHz multitrack and stem export",
            "Advanced Split stems (~100 instruments)",
            "Unlimited Studio downloads (Studio exports are exempt from the monthly cap)",
        ],
        "models": ["v4.5-all", "v4 Pro", "v4.5 Pro", "v4.5+ Pro", "v5 Pro", "v5.5 Pro"],
        "legacy_models": ["v4 Pro", "v4.5 Pro", "v4.5+ Pro", "v5 Pro"],
        "sliders_available": True,
        "personas_available": True,
        "voices_available": True,
        "voice_recording_available": True,
        "custom_models_available": True,
        "audio_influence_available": True,
        "exclude_styles_available": True,
        "legacy_editor_available": True,
        "replace_section_available": True,
        "studio_available": False,
        "studio_version": None,
        "stem_modes": [AUTO_SPLIT, SPLIT_FROM_MIX],
        "advanced_split_available": False,
        "duration_slider_available": True,
        "song_length_max": "Determined by model — v4.5/v5/v5.5 support up to ~8 min",
        "audio_upload_max": "30 min",
        "credits_included": "2,500/month (~500 songs)",
        "downloads": _downloads(monthly=20),
        "commercial_use": {
            "allowed": True,
            "condition": (
                "Commercial exploitation is permitted only for outputs obtained as a "
                "permitted download; obtaining a copy by any other channel is prohibited, "
                "as is removing or obscuring watermarks, fingerprints, or metadata. "
                "Downloaded outputs keep perpetual commercial rights after a downgrade. "
                "Remixes are jointly owned and non-commercial on every tier."
            ),
        },
        "credit_cost": {"generation": 10, "per_song": 5, "extension": 5},
        "pricing": {"monthly": 10, "annual_monthly": 8},
    },
    "premier": {
        "available": [
            "v5.5 Pro plus legacy models (v4 Pro, v4.5 Pro, v4.5+ Pro, v5 Pro) and v4.5-all",
            "10,000 credits/month (~2,000 songs)",
            "Commercial use — for outputs obtained as a permitted download",
            "Personas (still supported; they live inside the Voices menu)",
            "Voices (v5.5 voice cloning)",
            "Custom Models (up to 3)",
            "Weirdness slider (0-100)",
            "Style Influence slider (0-100)",
            "Audio Influence slider (0-100, with Voice/Persona or audio upload)",
            "Exclude Styles field",
            "Add Vocals / Add Instrumental (beta)",
            "Covers (beta)",
            "Remaster (Subtle/Normal/High)",
            "Auto Split stems (up to 12, 50 credits per extraction)",
            "Split from Mix stems (20 credits total)",
            "Advanced Split stems (~100 instruments; 10 credits per extraction, 20 total per stem because each extraction returns the stem plus its complement)",
            "30 min audio upload",
            "Song Editor / Legacy Editor (Replace Section, Extend, Crop, Fade, Rearrange)",
            "Duration slider (v5.5, web, requires Style set to Custom)",
            "Suno Studio 2.0 (browser-based generative DAW)",
            "Studio MIDI import/record/edit, piano roll, audio-to-MIDI, MIDI-as-prompt",
            "Studio chat bar (generates instruments, vocals, custom plugins and synth presets)",
            "Studio wavetable synth, built-in effects, and automation curves",
            "Studio export: full song, selected range, or multitrack in 32-bit WAV or MP3; stems as WAV",
            "Unlimited Studio downloads (exempt from the monthly cap)",
            "Priority queue, 10 concurrent",
            "Add-on credits",
            "Song length determined by model — v4.5/v5/v5.5 support up to ~8 min",
            f"60 downloads per month (from {DOWNLOAD_LIMITS_EFFECTIVE}), plus unlimited Studio exports",
        ],
        "unavailable": [],
        "models": ["v4.5-all", "v4 Pro", "v4.5 Pro", "v4.5+ Pro", "v5 Pro", "v5.5 Pro"],
        "legacy_models": ["v4 Pro", "v4.5 Pro", "v4.5+ Pro", "v5 Pro"],
        "sliders_available": True,
        "personas_available": True,
        "voices_available": True,
        "voice_recording_available": True,
        "custom_models_available": True,
        "audio_influence_available": True,
        "exclude_styles_available": True,
        "legacy_editor_available": True,
        "replace_section_available": True,
        "studio_available": True,
        "studio_version": "2.0",
        "stem_modes": [AUTO_SPLIT, SPLIT_FROM_MIX, ADVANCED_SPLIT],
        "advanced_split_available": True,
        "duration_slider_available": True,
        "song_length_max": "Determined by model — v4.5/v5/v5.5 support up to ~8 min",
        "audio_upload_max": "30 min",
        "credits_included": "10,000/month (~2,000 songs)",
        "downloads": _downloads(monthly=60, studio_exempt=True),
        "commercial_use": {
            "allowed": True,
            "condition": (
                "Commercial exploitation is permitted only for outputs obtained as a "
                "permitted download; obtaining a copy by any other channel is prohibited, "
                "as is removing or obscuring watermarks, fingerprints, or metadata. "
                "Downloaded outputs keep perpetual commercial rights after a downgrade. "
                "Remixes are jointly owned and non-commercial on every tier."
            ),
        },
        "credit_cost": {"generation": 10, "per_song": 5, "extension": 5},
        "pricing": {"monthly": 30, "annual_monthly": 24},
    },
}

# Studio 1.x feature names that do NOT appear in current official Studio 2.0
# copy — Suno moved those articles into a "Studio Archive" category on
# 2026-08-13. They were Premier-only when documented and are deliberately
# excluded from the tier lists above; verify in the live UI before surfacing
# any of them to a user.
#
# Deliberately NOT in this list: Take Lanes and comping, multitrack editing, AI
# stem generation, and the Full Song / Selected Time Range / Multitracks export
# set — those survived into the current docs. Only the "Alternates" and "Quick
# Replace" halves of the old Alternates/Take-Lanes pairing are archived.
STUDIO_1X_ARCHIVED_FEATURES = [
    "Warp Markers",
    "Remove FX",
    "Alternates",
    "Quick Replace",
    "EQ (6-band per track)",
    "Time Signature control",
    "Context Window",
    "Recording (microphone)",
    "Loop Recording",
    "Sounds Mode (text-to-sound)",
    "Stem Cover",
    "Heal Edits",
    "MIDI export (10 credits/stem)",
    "MILO-1080 Sequencer",
]


def get_tier_features(tier: str) -> dict:
    """Return feature availability for the given tier."""
    script_name = "tier-features"
    tier_lower = tier.lower().strip()

    if tier_lower not in VALID_TIERS:
        return {
            "script": script_name,
            "version": "3.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "fail",
            "error": f"Unknown tier '{tier}'. Must be one of: {', '.join(sorted(VALID_TIERS))}",
        }

    features = TIER_FEATURES[tier_lower]
    return {
        "script": script_name,
        "version": "3.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "tier": tier_lower,
        "last_validated": LAST_VALIDATED,
        "notes": {
            "pricing_display": PRICING_DISPLAY_NOTE,
            "model_retirement": MODEL_RETIREMENT_NOTICE,
            "character_limits": CHARACTER_LIMIT_PROVENANCE,
            "studio_1x_archived": STUDIO_1X_ARCHIVED_FEATURES,
        },
        **features,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Return available/unavailable Suno features for a given subscription tier.",
        epilog="Exit codes: 0=success, 1=invalid tier"
    )
    parser.add_argument("tier", choices=["free", "pro", "premier"], help="Suno subscription tier")
    parser.add_argument("-o", "--output", help="Output file (defaults to stdout)")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostics to stderr")
    args = parser.parse_args()

    if args.verbose:
        print(f"Getting features for tier: {args.tier}", file=sys.stderr)

    result = get_tier_features(args.tier)
    output = json.dumps(result, indent=2)

    if args.output:
        from pathlib import Path
        Path(args.output).write_text(output)
        if args.verbose:
            print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)

    sys.exit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
