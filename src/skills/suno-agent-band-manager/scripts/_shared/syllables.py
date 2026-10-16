"""Syllable counts for English lyric lines: a vowel-cluster heuristic with overrides.

Shared by the lyric transformer's syllable counter and the band manager's WIP capture,
so a line is counted the same way wherever it is judged.
"""

import re

# Common words with known syllable counts that the algorithm gets wrong
SYLLABLE_OVERRIDES = {
    "the": 1, "every": 3, "different": 3, "evening": 3, "heaven": 2,
    "beautiful": 3, "comfortable": 3, "interesting": 4, "chocolate": 3,
    "fire": 2, "hour": 2, "flower": 2, "power": 2, "tower": 2,
    "desire": 3, "inspire": 3, "higher": 2, "liar": 2, "wire": 2,
    "quiet": 2, "lion": 2, "riot": 2, "diary": 3, "science": 2,
    "poem": 2, "being": 2, "seeing": 2, "doing": 2, "going": 2,
    "cruel": 2, "fuel": 2, "jewel": 2, "real": 1, "deal": 1,
    "people": 2, "little": 2, "middle": 2, "simple": 2, "able": 2,
    "maybe": 2, "somewhere": 2, "nowhere": 2, "everywhere": 3,
    "i'm": 1, "you're": 1, "we're": 1, "they're": 1, "he's": 1,
    "she's": 1, "it's": 1, "don't": 1, "won't": 1, "can't": 1,
    "couldn't": 2, "wouldn't": 2, "shouldn't": 2, "didn't": 2,
    "isn't": 2, "wasn't": 2, "aren't": 2, "weren't": 2,
}


def count_syllables(word: str) -> int:
    """Count syllables in a single word using vowel cluster heuristic."""
    word = word.lower().strip()

    # Remove non-alpha except apostrophes
    word = re.sub(r"[^a-z']", "", word)

    if not word:
        return 0

    # Check overrides first
    if word in SYLLABLE_OVERRIDES:
        return SYLLABLE_OVERRIDES[word]

    # Vowel cluster counting with adjustments
    vowels = "aeiouy"
    count = 0
    prev_vowel = False

    for i, char in enumerate(word):
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    # Adjustments
    # Silent e at end
    if word.endswith('ee'):
        pass  # 'coffee', 'free': the final vowel sound is real, not a silent e
    elif word.endswith('e') and not word.endswith(('le', 'ce', 'se', 'ge', 'ze', 'ne', 'me', 've', 'te', 'de', 'be', 'fe', 'he', 'ke', 'pe', 'we', 'ye')):
        count -= 1
    elif word.endswith('e') and len(word) > 3 and word[-2] not in vowels:
        count -= 1

    # -ed ending (usually not a syllable unless preceded by t or d)
    if word.endswith('ed') and len(word) > 3:
        if word[-3] not in ('t', 'd'):
            count -= 1

    # -le at end is usually a syllable
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        count += 1

    # -es ending
    if word.endswith('es') and len(word) > 3:
        if word[-3] in ('s', 'z', 'x', 'ch', 'sh'):
            pass  # -es IS a syllable here
        elif word[-3] not in vowels:
            count -= 1

    # Ensure at least 1 syllable for any word
    return max(1, count)


def count_line_syllables(line: str) -> int:
    """Count total syllables in a line of text."""
    # Remove metatags
    line = re.sub(r'\[.*?\]', '', line)
    words = line.split()
    return sum(count_syllables(w) for w in words)
