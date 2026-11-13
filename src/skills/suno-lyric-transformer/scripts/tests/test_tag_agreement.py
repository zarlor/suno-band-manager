#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""The four scripts that read section tags must agree on which tags open a section.

validate_lyrics.py, section_length_checker.py, syllable_counter.py and
lyrics_diff.py each run on the same draft in the workflow's check step; a tag
that opens a section in one and not in another makes their reports contradict.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent

# tag -> does it open a section?
TAGS = {
    "Verse 2": True,
    "Chorus": True,
    "Chorus: anthemic": True,
    "Verse | whispered": True,
    "Bridge - stripped back, piano only": True,
    "Final Chorus": True,
    "Buildup": True,
    "Violin Solo": True,
    "Instrumental Intro": True,
    "Bass Drop": True,
    "Reprise: quieter": True,
    "Harmonized": False,
    "Whispered": False,
    "Spoken Word": False,
    "Haunting": False,
    "Half-Time": False,
    "Unresolved tension": False,
    "Mood: dark": False,
    "Energy: building": False,
    "End": False,
    "Banana": False,
    "Heavy": False,
}


def run_json(script, *args):
    result = subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                            capture_output=True, text=True)
    return json.loads(result.stdout)


def draft(tag: str, last_line: str = "under the open sky tonight") -> str:
    """Four lines under [Verse 1], then the tag under test, then four more lines."""
    return ("[Verse 1]\nwalking through the morning light\ncounting shadows on the wall\n"
            "holding on to what we know\nletting go of what we were\n"
            f"[{tag}]\nsomething new is on the way\nevery window open wide\n"
            f"all the colors running in\n{last_line}\n")


class TestScriptsAgreeOnSections(unittest.TestCase):
    def opened_by(self, tag: str) -> dict:
        text = draft(tag)
        validator = run_json("validate_lyrics.py", "--text", text)
        lengths = run_json("section_length_checker.py", "--text", text)
        syllables = run_json("syllable_counter.py", "--text", text)
        diff = run_json("lyrics_diff.py", "--original-text", text,
                        "--transformed-text", draft(tag, "under the open sky again"))
        # The edited line is the last one: it sits in the tag's section only if the tag opened one.
        edited_in = diff["changes"][0]["section"]
        self.assertIn(edited_in, (tag, "Verse 1"))
        return {
            "validate-lyrics": tag in validator["metrics"]["sections"],
            "section-length-checker": tag in [s["tag"] for s in lengths["sections"]],
            "syllable-counter": f"[{tag}]" in [s["section"] for s in syllables["section_analysis"]],
            "lyrics-diff": edited_in == tag,
        }

    def test_each_tag_opens_a_section_in_all_four_or_in_none(self):
        for tag, opens in TAGS.items():
            with self.subTest(tag=tag):
                self.assertEqual(self.opened_by(tag), {
                    "validate-lyrics": opens,
                    "section-length-checker": opens,
                    "syllable-counter": opens,
                    "lyrics-diff": opens,
                })

    def test_lines_after_a_cue_stay_in_the_section(self):
        text = draft("Harmonized")
        validator = run_json("validate_lyrics.py", "--text", text)
        lengths = run_json("section_length_checker.py", "--text", text)
        syllables = run_json("syllable_counter.py", "--text", text)
        self.assertEqual(validator["metrics"]["sections"], ["Verse 1"])
        self.assertEqual([(s["tag"], s["line_count"]) for s in lengths["sections"]], [("Verse 1", 8)])
        self.assertEqual([(s["section"], s["line_count"]) for s in syllables["section_analysis"]],
                         [("[Verse 1]", 8)])

    def test_two_tags_on_one_line_open_the_section_in_all_four(self):
        text = draft("Chorus] [Whispered")
        validator = run_json("validate_lyrics.py", "--text", text)
        lengths = run_json("section_length_checker.py", "--text", text)
        syllables = run_json("syllable_counter.py", "--text", text)
        diff = run_json("lyrics_diff.py", "--original-text", text,
                        "--transformed-text", draft("Chorus] [Whispered", "under the open sky again"))
        self.assertEqual(validator["metrics"]["sections"], ["Verse 1", "Chorus"])
        self.assertEqual([s["tag"] for s in lengths["sections"]], ["Verse 1", "Chorus"])
        self.assertEqual([s["section"] for s in syllables["section_analysis"]], ["[Verse 1]", "[Chorus]"])
        self.assertEqual(diff["changes"][0]["section"], "Chorus")


if __name__ == "__main__":
    unittest.main()
