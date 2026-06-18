#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Suno platform constants — single source of truth for all module scripts.

When Suno adds a new model or changes limits, update HERE ONLY.
"""

# Valid Suno models (all versions, current and legacy)
VALID_MODELS = frozenset({
    "v4.5-all", "v4 Pro", "v4.5 Pro", "v4.5+ Pro", "v5 Pro", "v5.5 Pro"
})

# Tier definitions
VALID_TIERS = frozenset({"free", "pro", "premier"})
PAID_TIERS = frozenset({"pro", "premier"})
FREE_TIER_MODEL = "v4.5-all"

# Style prompt character limits per model
STYLE_PROMPT_LIMITS = {
    "v4 Pro": 200,
    "v4.5-all": 1000,
    "v4.5 Pro": 1000,
    "v4.5+ Pro": 1000,
    "v5 Pro": 1000,
    "v5.5 Pro": 1000,
}
STYLE_PROMPT_DEFAULT_MAX = 1000

# Critical zone: first N chars have strongest influence on generation
CRITICAL_ZONE = 200

# Exclusion prompt limits
EXCLUSION_RECOMMENDED_MAX = 200
EXCLUSION_HARD_MAX = 300

# Lyrics character limits (v4.5+/v5/v5.5)
# Hard limit: 5,000 chars — content beyond this is silently truncated
# Quality budget: ~3,000 chars — beyond this, Suno rushes through sections
SUNO_LYRICS_HARD_LIMIT = 5000
SUNO_LYRICS_QUALITY_BUDGET = 3000

# ---------------------------------------------------------------------------
# Style-prompt safety triggers — enumerable exact-string detection.
#
# These mirror the load-bearing tables in
# suno-style-prompt-builder/references/model-prompt-strategies.md
# ("Scream/Harsh Vocal Triggers" and "Dangerous Words and Keyboard Triggers").
#
# DETECTION is deterministic and lives here / in the script; the SUBSTITUTION
# decision stays with the LLM (which safe alternative to use, whether the
# context already pairs a heavy genre with a positive vocal instruction, etc.).
# The reference file remains the source of truth for the *fix* guidance.
# ---------------------------------------------------------------------------

# Heavy-genre terms that pull screaming / harsh vocals unless paired with an
# explicit positive vocal instruction in the same prompt. Detection flags an
# UNPAIRED occurrence; the LLM decides the substitution or the pairing.
HEAVY_VOCAL_TRIGGERS = frozenset({
    "metal", "sludge", "death", "thrash", "black", "doom",
})

# Positive vocal phrases that, when present, "pair" a heavy genre term so it no
# longer reads as an unpaired scream trigger. Substrings, matched case-insensitively.
VOCAL_SAFE_PAIRINGS = (
    "raw melodic singing",
    "melodic singing",
    "clean singing",
    "clean vocals",
    "gritty male vocals",
    "gritty female vocals",
    "gritty vocals",
    "no screaming",
    "melodic vocals",
    "sung vocals",
    "soulful vocals",
)

# Words that reliably pull keyboard/synth-heavy, theatrical, or cinematic-light
# arrangements when guitars/bass should lead. Detection flags presence; the
# reference file carries the per-word rewrite (e.g. "cinematic" -> "dynamic
# shifts, building from gentle to crushing").
KEYBOARD_PULL_WORDS = frozenset({
    "baroque", "orchestral", "cinematic", "rock opera",
})

# Exclamation mark in lyrics/prompt pushes vocal delivery toward shouting.
SHOUT_TRIGGER_CHAR = "!"

# Genre / subgenre keywords for front-loading detection. Kept deliberately broad
# so the validator does not falsely report "no genre keyword" for the southern /
# heavy / atmospheric lanes this module works in. ADD here when a real genre term
# trips a false negative; this is a detection aid, not an exhaustive taxonomy.
GENRE_SIGNALS = frozenset({
    # broad families
    "rock", "pop", "folk", "jazz", "blues", "electronic", "hip hop", "hip-hop",
    "r&b", "country", "classical", "metal", "punk", "indie", "soul", "funk",
    "ambient", "lo-fi", "lofi", "dance", "edm", "house", "techno", "rap",
    "acoustic", "orchestral", "cinematic", "reggae", "latin", "alternative",
    "grunge", "shoegaze", "post-punk", "synth", "synthwave", "disco",
    # rock / metal subgenres and lanes this module actually uses
    "heartland", "southern rock", "heartland rock", "swamp metal", "swamp",
    "prog rock", "prog", "progressive", "groove metal", "doom", "sludge",
    "post-metal", "post-hardcore", "hardcore", "hard rock", "speed metal",
    "slowcore", "americana", "singer-songwriter", "stoner", "psychedelic",
    "psych", "garage", "emo", "darkwave", "dirge", "breakbeat", "second-line",
    "brass band", "new orleans", "nola", "gospel", "bluegrass", "ballad",
    "power ballad", "dark alternative",
})
