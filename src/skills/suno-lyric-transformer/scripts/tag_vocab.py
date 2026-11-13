#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""The bracket-tag vocabulary: the one definition this skill's scripts share.

validate_lyrics.py, section_length_checker.py, syllable_counter.py and
lyrics_diff.py import it, so they agree on which tags open a section and which
tags are recognized. The sets follow the tables of
references/metatag-reference.md that the catalog rates reliable (HIGH,
LOCAL-CONFIRMED, or unmarked = established); a tag it rates LOW, Experimental,
anecdotal or not working stays out, so the validator flags it. When a row
changes there, change it here, and edit tag names here only.

A tag is one of (see classify):
  section     opens a section: [Verse 1], [Chorus: full band], [Guitar Solo]
  end         [End], the stop marker; it opens no section
  descriptor  [Mood: haunting], [Energy: building]
  cue         a delivery cue inside or before a section: [Whispered], [Harmonized]
  standalone  a mood, energy, rhythm, transition, mix or instrument tag: [Haunting], [Half-Time]
  unknown     anything else; Suno may ignore it or sing it
"""

import re

# --- Section heads -----------------------------------------------------------

# Sections that are sung: the only ones that take "Final" and that count as
# empty when no lyric line follows.
SUNG_SECTIONS = ("verse", "chorus", "pre-chorus", "post-chorus", "bridge", "hook", "refrain")

# [<instrument> Solo] opens a section for each of these.
SOLO_INSTRUMENTS = (
    "guitar", "piano", "sax", "saxophone", "drum", "bass", "fiddle", "violin",
    "harmonica", "organ", "synth", "trumpet", "banjo", "mandolin",
    "steel guitar", "slide guitar",
)

# Section Structure Tags, Instrumental & Solo Section Tags, plus the fades the
# scripts have always counted as sections.
SECTION_NAMES = frozenset(SUNG_SECTIONS) | frozenset({
    "intro", "outro", "interlude", "breakdown", "build-up", "buildup", "build",
    "drop", "break", "solo", "instrumental", "instrumental break",
    "instrumental intro", "instrumental outro", "drum break", "percussion break",
    "big finish", "reprise", "coda", "bass drop", "strings rise",
    "fade out", "fade in",
}) | frozenset(f"{instrument} solo" for instrument in SOLO_INSTRUMENTS)

END_TAG = "end"

# What may follow a section name inside the brackets: a v6 cue after a colon,
# a pipe, a spaced hyphen or dash, or an unspaced en/em dash.
CUE_SEPARATOR = r"(?::|\||\s[-–—]\s?|[–—])"

_NAMES = "|".join(
    re.escape(name).replace(r"\ ", r"\s+")
    for name in sorted(SECTION_NAMES, key=len, reverse=True)
)
# [Final Chorus], [Verse 2], [Chorus x2], [Verse 1 - riff continues], [Verse | whispered]
_SECTION_RE = re.compile(
    rf"^(?P<head>(?:(?P<final>final)\s+)?(?P<name>{_NAMES})\s*\d*(?:\s+x\d+)?)"
    rf"(?:\s*(?P<sep>{CUE_SEPARATOR})\s*(?P<cue>.+))?$",
    re.IGNORECASE,
)

# --- Descriptors -------------------------------------------------------------

# [Prefix: value]. Core Descriptor Tags, Additional Descriptor Families and
# [Vocal Arrangement: ...]; `key` predates the catalog. `heavy` is the rhythm-feel
# form the reference recommends ([Heavy: halftime]); bare [Heavy] stays unrecognized
# because as a header it breaks Suno's structural parse. `callback` is the
# Extend/Replace tag ([Callback: ...]).
DESCRIPTOR_PREFIXES = frozenset({
    "mood", "energy", "vocal style", "instrument",
    "atmosphere", "texture", "effect", "harmony", "voice", "vibe", "tempo", "key",
    "vocal arrangement", "heavy", "callback",
})

# --- Inline cues (Vocal Delivery Tags) ----------------------------------------

INLINE_CUES = frozenset({
    # Volume & Intensity. [Soft] and [Quiet] are out: as a header they break
    # Suno's structural parse.
    "whispered", "whisper", "gentle", "spoken", "spoken word", "powerful", "intense",
    "belted", "belting", "shouted", "screamed", "growled", "growl", "gritty",
    "monotone", "breathless",
    # Vocal Style & Technique
    "chest voice", "breathy", "raspy", "smooth", "soulful", "operatic", "crooning",
    "nasal", "airy", "harmonies", "harmonized", "ad-libs", "ad-lib", "vocal run",
    "melisma", "vibrato", "staccato", "legato", "call and response", "chant",
    "choir", "choir vocals", "scat", "hummed", "humming", "whistled", "whistling",
    "backing vocals", "stacked harmonies", "gospel choir", "narrator",
    "female narrator", "announcer", "reporter",
    # Rap & Hip-Hop Delivery
    "rapped", "rap", "fast rap", "double time", "slow flow", "melodic rap",
    "trap flow", "boom bap flow", "mumble rap",
    # Vocal Identity. [Duet] alone is unreliable, so it is out.
    "male vocal", "male vocalist", "male vocals", "male", "man",
    "female vocal", "female vocalist", "female vocals", "female", "woman",
    "boy", "girl", "clean vocal", "harsh vocal",
    # Vocal Effects. [No AutoTune] is a bracket negation, which backfires.
    "reverb", "delay", "autotune", "distorted vocals", "filtered vocals",
    "vocoder", "telephone effect",
    # Vocal Emotion
    "vulnerable", "defiant", "sultry", "joyful", "melancholic", "aggressive",
})

# --- Standalone tags ---------------------------------------------------------

STANDALONE_MOODS = frozenset({
    "uplifting", "haunting", "dark", "nostalgic", "somber", "romantic",
    "dreamy", "peaceful", "anxious", "euphoric", "mysterious", "playful",
    "epic", "intimate", "bittersweet", "triumphant",
})

STANDALONE_ENERGY = frozenset({
    "high energy", "medium energy", "low energy", "chill", "driving",
    "explosive", "building", "relaxed", "frantic", "steady",
})

TIMING_RHYTHM = frozenset({
    "half-time", "double-time", "swung feel", "shuffle", "triplet feel",
    "syncopated", "straight", "four on the floor", "polyrhythmic", "breakbeat",
})

# Dynamic & Transition Tags. [pause], [space], [hard cut] and [Stop] are out:
# single-source or sung as words. [Hard Stop] is the v6 ending template's.
TRANSITIONS = frozenset({
    "fade", "swell", "crescendo", "decrescendo", "silence", "soft end",
    "dramatic end", "instrumental end", "slow fade out", "fast fade out",
    "instrumental fade out", "cinematic fade out", "unresolved tension",
    "key change", "key modulation", "metric modulation", "accelerando",
    "ritardando", "hard stop",
})

# Production & Mix Tags, and the training-data sound effects (Reliability Tiers: HIGH).
MIX_AND_EFFECTS = frozenset({
    "lo-fi", "reverb tail", "echo", "vinyl crackle", "vinyl hiss", "distant voices",
    "bleep", "censored", "phone ringing", "gunshots",
})

# Standalone Instrument Tags.
INSTRUMENTS = frozenset({
    # Keys
    "piano", "electric piano", "rhodes", "wurlitzer", "organ", "hammond organ",
    "harpsichord", "clavinet", "mellotron",
    # Synths
    "synth", "analog synth", "moog synth", "synth pad", "lead synth", "synth stabs",
    "pad", "pluck synth", "arpeggiated synth", "synth bass", "acid bass", "supersaw",
    "wobbly bass",
    # Strings
    "acoustic guitar", "electric guitar", "distorted guitar", "clean guitar",
    "jangly guitar", "fingerpicked guitar", "slide guitar", "12-string guitar",
    "classical guitar", "bass guitar", "slap bass", "upright bass", "fretless bass",
    "violin", "viola", "strings", "string quartet", "string section", "cello",
    "double bass", "pizzicato", "harp", "ukulele", "banjo", "mandolin", "sitar",
    # Brass & Winds
    "saxophone", "tenor sax", "alto sax", "trumpet", "trombone", "french horn",
    "tuba", "brass section", "flute", "clarinet", "oboe", "harmonica", "accordion",
    "bagpipes", "didgeridoo",
    # Percussion
    "drums", "acoustic drums", "electronic drums", "brushed drums", "live drums",
    "808s", "808 bass", "808 drums", "drum machine", "tr-909", "trap hi-hats",
    "taiko drums", "congas", "bongos", "tambourine", "shaker", "handclaps", "claps",
    "gong", "timpani", "cinematic percussion",
    # Orchestral
    "orchestra", "full orchestra", "chamber orchestra", "brass stabs",
})

STANDALONE_TAGS = (STANDALONE_MOODS | STANDALONE_ENERGY | TIMING_RHYTHM
                   | TRANSITIONS | MIX_AND_EFFECTS | INSTRUMENTS)

# --- Tests -------------------------------------------------------------------

_TAG_ONLY_LINE = re.compile(r"^\s*(?:\[[^\[\]]*\]\s*)+$")
_TAG = re.compile(r"\[([^\[\]]*)\]")


def _norm(tag: str) -> str:
    """Lower-case with single spaces, the form the name sets use."""
    return " ".join(tag.lower().split())


def line_tags(line: str) -> list[str]:
    """The tags on a line that holds bracket tags and nothing else, in order.

    [] for a lyric line, a blank line, or a line that mixes tags with words.
    A leading byte-order mark is ignored.
    """
    line = line.lstrip("﻿")
    if not _TAG_ONLY_LINE.match(line):
        return []
    return [tag.strip() for tag in _TAG.findall(line)]


def is_tag_line(line: str) -> bool:
    """True when the line holds only bracket tags (so it is not sung)."""
    return bool(line_tags(line))


def split_section_tag(tag: str) -> dict | None:
    """The parts of a section tag, or None when the tag opens no section.

    head: the section with any cue removed ("Verse 1" from "Verse 1 - half-spoken").
    base: the section's kind ("verse": no number, "Final", repeat count or cue).
    separator, cue: what follows the head ("-", "half-spoken"), or None.
    """
    m = _SECTION_RE.match(tag.strip())
    if not m:
        return None
    base = _norm(m.group("name"))
    if m.group("final") and base not in SUNG_SECTIONS:
        return None
    sep = m.group("sep")
    return {
        "head": m.group("head").strip(),
        "base": base,
        "separator": sep.strip() if sep else None,
        "cue": m.group("cue").strip() if m.group("cue") else None,
    }


def opens_section(tag: str) -> bool:
    """True when the tag starts a new section. [End] does not: it is the stop marker."""
    return split_section_tag(tag) is not None


def section_head(tag: str) -> str | None:
    """The section part of a tag with any cue removed, or None."""
    parts = split_section_tag(tag)
    return parts["head"] if parts else None


def section_base(tag: str) -> str | None:
    """The section's kind in lower case ("verse" for "Final Verse 2: hushed"), or None."""
    parts = split_section_tag(tag)
    return parts["base"] if parts else None


def is_sung_section(tag: str) -> bool:
    """True for a section that carries lyrics by nature (verse, chorus, bridge...)."""
    return section_base(tag) in SUNG_SECTIONS


def section_opener(line: str) -> str | None:
    """The tag that opens a section on this line: the first section tag of a
    tag-only line, else None."""
    return next((tag for tag in line_tags(line) if opens_section(tag)), None)


def is_end_tag(tag: str) -> bool:
    return _norm(tag) == END_TAG


def is_descriptor(tag: str) -> bool:
    """[Prefix: value] with a known prefix."""
    return ":" in tag and _norm(tag.split(":")[0]) in DESCRIPTOR_PREFIXES


def _bare_kind(tag: str) -> str | None:
    name = _norm(tag)
    if name in INLINE_CUES:
        return "cue"
    if name in STANDALONE_TAGS:
        return "standalone"
    return None


def classify(tag: str) -> str:
    """section, end, descriptor, cue, standalone or unknown.

    A comma list of bare tags ([Whispered, vulnerable]) takes the kind of its
    first part when every part is known.
    """
    if is_end_tag(tag):
        return "end"
    if opens_section(tag):
        return "section"
    if is_descriptor(tag):
        return "descriptor"
    kinds = [_bare_kind(part) for part in tag.split(",")]
    if all(kinds):
        return kinds[0]
    return "unknown"


def is_inline_cue(tag: str) -> bool:
    return classify(tag) == "cue"


def is_standalone_tag(tag: str) -> bool:
    return classify(tag) == "standalone"


def is_recognized(tag: str) -> bool:
    """True for every kind but unknown."""
    return classify(tag) != "unknown"
