#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""The transformation option codes: the one table the skill and its scripts share.

validate-options.py checks selections against it and prints it as the menu
(`--list`); assemble-summary.py renders applied codes from it. Edit codes,
names or effects here only.
"""

# code -> (name, what it does). Order is menu order.
OPTION_CODES = {
    "ST": ("Structure Tagging", "Section tags on the arc, sparse descriptors"),
    "CE": ("Chorus Extraction", "Promote existing hook lines to chorus"),
    "CC": ("Chorus Creation", "New 2-4 line chorus from the emotional core"),
    "RA": ("Rhythmic Adjustment", "Even syllable counts within each section"),
    "RE": ("Rhyme Enhancement", "Clearer rhyme patterns"),
    "FR": ("Full Rewrite", "New language; theme, imagery and arc kept"),
    "CD": ("Cliche Detection", "Flag cliches, offer fresher options (on by default: Suno amplifies cliches in delivery)"),
    "WF": ("Word Fidelity Mode", "Writer's exact words; structure only"),
}

CODE_NAMES = {code: name for code, (name, _) in OPTION_CODES.items()}

# The selection rules validate-options.py enforces, as the menu states them.
RULES = [
    "FR and WF exclude each other.",
    "FR drops CE (a full rewrite has no existing hook to promote).",
    "CC may drop when CE finds a strong chorus; the user can keep both.",
]


def menu() -> list[dict]:
    """The option menu in order, one dict per code."""
    return [{"code": code, "name": name, "effect": effect} for code, (name, effect) in OPTION_CODES.items()]
