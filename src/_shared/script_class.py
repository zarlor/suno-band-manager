"""Classify a line of text by writing system: Latin, non-Latin, mixed, or none.

The lyric scripts' syllable, rhyme and cliche heuristics only hold for Latin
script, so the line classes here decide which lines those checks may touch.
One definition keeps analyze-input.py's `script_lines` and the `--latin-only`
filters of syllable-counter.py and cliche-detector.py in agreement.
"""

import re
import unicodedata

LATIN = "latin"
NON_LATIN = "non_latin"
MIXED = "mixed"
NONE = "none"

# A line that is only a bracketed tag ("[Verse 1]") carries no lyric script.
TAG_ONLY_LINE = re.compile(r"^\s*\[[^\]]*\]\s*$")


def classify_script(line: str) -> str:
    """Classify a line's letters as latin, non_latin, mixed, or none (no letters)."""
    latin = non_latin = 0
    for ch in line:
        if not ch.isalpha():
            continue
        try:
            name = unicodedata.name(ch)
        except ValueError:
            name = ""
        if name.startswith("LATIN"):
            latin += 1
        else:
            non_latin += 1
    if latin and non_latin:
        return MIXED
    if latin:
        return LATIN
    if non_latin:
        return NON_LATIN
    return NONE


def latin_checkable(line: str) -> bool:
    """True when Latin-script heuristics may run on the line.

    Latin lines and lines without letters qualify; any non-Latin letter
    (a non_latin or mixed line) takes the line out.
    """
    return classify_script(line) in (LATIN, NONE)
