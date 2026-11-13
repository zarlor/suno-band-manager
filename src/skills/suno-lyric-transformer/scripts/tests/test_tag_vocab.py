#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for tag_vocab.py, the bracket-tag vocabulary the lyric scripts share."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tag_vocab  # noqa: E402

SECTIONS = [
    "Intro", "Verse", "Verse 1", "Verse 12", "Pre-Chorus", "Chorus", "Post-Chorus",
    "Bridge", "Outro", "Final Chorus", "Final Verse", "Hook", "Refrain",
    "Instrumental Intro", "Instrumental Break", "Instrumental Outro", "Drum Break",
    "Percussion Break", "Build", "Build-Up", "Buildup", "Big Finish", "Reprise",
    "Coda", "Chorus x2", "Instrumental", "Interlude", "Solo", "Guitar Solo",
    "Piano Solo", "Sax Solo", "Saxophone Solo", "Drum Solo", "Bass Solo",
    "Synth Solo", "Violin Solo", "Fiddle Solo", "Slide Guitar Solo", "Break",
    "Breakdown", "Drop", "Bass Drop", "Strings Rise", "Fade Out", "Fade In",
    "Chorus: anthemic", "Verse 1: hushed, tense", "Verse | whispered",
    "Chorus | Half-Time", "Verse 1 - riff continues under vocal", "Bridge — THE TURN",
    "Outro – short resolved ending", "Reprise: quieter", "VERSE 2", "guitar  solo",
]

CUES = [
    "Whispered", "Whisper", "Spoken Word", "Spoken", "Belted", "Raspy", "Breathy",
    "Powerful", "Choir", "Harmonized", "Harmonies", "Hummed", "Humming", "Whistled",
    "Whistling", "Crooning", "Scat", "Call and Response", "Gritty", "Monotone",
    "Melodic Rap", "Male", "Female", "Male Vocals", "Clean Vocal", "Harsh Vocal",
    "Vocoder", "Vulnerable", "Whispered, vulnerable",
]

STANDALONE = [
    "Haunting", "Uplifting", "High Energy", "Building", "Half-Time", "Double-Time",
    "Four on the Floor", "Swung Feel", "Silence", "Unresolved tension", "Soft End",
    "Key Change", "Ritardando", "Hard Stop", "Lo-fi", "Vinyl Crackle", "Piano",
    "Acoustic Guitar", "808s", "Strings", "Haunting, dreamy",
]

DESCRIPTORS = [
    "Mood: haunting", "Energy: building", "Vocal Style: whispered",
    "Instrument: solo piano", "Atmosphere: Dreamy", "Texture: Grainy",
    "Effect: Reverb: Hall", "Harmony: High", "Voice: Auto-tune", "Vibe: Cinematic",
    "Tempo: slow", "Vocal Arrangement: lead vocal with group responses",
    "Heavy: halftime", "Callback: the first chorus",
]

UNKNOWN = [
    "Banana", "The Questions", "Reflection", "Heavy", "Loud", "Soft", "Quiet",
    "Stop", "hard cut", "pause", "space", "Duet", "No AutoTune", "no vocals",
    "Falsetto", "Primal Scream", "Diva Solo", "Rain", "Voice 1", "Final Solo",
    "Instrumental section — full prog, complex", "Chorus spoken, emotional",
    "Verses", "Building up", "Whispered, banana", "Genre: metal", "",
]


class TestClassify(unittest.TestCase):
    def check(self, tags, kind):
        for tag in tags:
            with self.subTest(tag=tag):
                self.assertEqual(tag_vocab.classify(tag), kind)

    def test_section_tags(self):
        self.check(SECTIONS, "section")

    def test_inline_cues(self):
        self.check(CUES, "cue")

    def test_standalone_tags(self):
        self.check(STANDALONE, "standalone")

    def test_descriptors(self):
        self.check(DESCRIPTORS, "descriptor")

    def test_end_is_its_own_kind(self):
        self.check(["End", "end", " END "], "end")

    def test_unknown_tags(self):
        self.check(UNKNOWN, "unknown")

    def test_only_section_tags_open_a_section(self):
        for tag in SECTIONS:
            with self.subTest(tag=tag):
                self.assertTrue(tag_vocab.opens_section(tag))
        for tag in CUES + STANDALONE + DESCRIPTORS + UNKNOWN + ["End"]:
            with self.subTest(tag=tag):
                self.assertFalse(tag_vocab.opens_section(tag))

    def test_recognized_is_every_kind_but_unknown(self):
        for tag in SECTIONS + CUES + STANDALONE + DESCRIPTORS + ["End"]:
            with self.subTest(tag=tag):
                self.assertTrue(tag_vocab.is_recognized(tag))
        for tag in UNKNOWN:
            with self.subTest(tag=tag):
                self.assertFalse(tag_vocab.is_recognized(tag))


class TestSectionParts(unittest.TestCase):
    def test_plain_section(self):
        self.assertEqual(tag_vocab.split_section_tag("Verse 1"),
                         {"head": "Verse 1", "base": "verse", "separator": None, "cue": None})

    def test_cue_forms(self):
        cases = {
            "Verse 1 - half-spoken": ("Verse 1", "verse", "-", "half-spoken"),
            "Chorus: full band": ("Chorus", "chorus", ":", "full band"),
            "Verse | whispered": ("Verse", "verse", "|", "whispered"),
            "Bridge — THE TURN": ("Bridge", "bridge", "—", "THE TURN"),
            "Breakdown–The Turn": ("Breakdown", "breakdown", "–", "The Turn"),
            "Final Chorus 2: louder": ("Final Chorus 2", "chorus", ":", "louder"),
            "Chorus x2": ("Chorus x2", "chorus", None, None),
            "Slide  Guitar Solo": ("Slide  Guitar Solo", "slide guitar solo", None, None),
        }
        for tag, (head, base, sep, cue) in cases.items():
            with self.subTest(tag=tag):
                self.assertEqual(tag_vocab.split_section_tag(tag),
                                 {"head": head, "base": base, "separator": sep, "cue": cue})

    def test_base_and_head_helpers(self):
        self.assertEqual(tag_vocab.section_base("Final Verse 3 - bare"), "verse")
        self.assertEqual(tag_vocab.section_head("Final Verse 3 - bare"), "Final Verse 3")
        self.assertIsNone(tag_vocab.section_base("Harmonized"))
        self.assertIsNone(tag_vocab.section_head("End"))

    def test_final_only_on_sung_sections(self):
        self.assertTrue(tag_vocab.opens_section("Final Refrain"))
        self.assertFalse(tag_vocab.opens_section("Final Outro"))

    def test_sung_sections(self):
        for tag in ("Verse 1", "Final Chorus", "Bridge: stripped", "Refrain"):
            with self.subTest(tag=tag):
                self.assertTrue(tag_vocab.is_sung_section(tag))
        for tag in ("Intro", "Guitar Solo", "Outro", "Reprise", "Harmonized", "End"):
            with self.subTest(tag=tag):
                self.assertFalse(tag_vocab.is_sung_section(tag))

    def test_every_solo_instrument_makes_a_section_name(self):
        for instrument in tag_vocab.SOLO_INSTRUMENTS:
            with self.subTest(instrument=instrument):
                self.assertIn(f"{instrument} solo", tag_vocab.SECTION_NAMES)

    def test_end_is_not_a_section_name(self):
        self.assertNotIn("end", tag_vocab.SECTION_NAMES)


class TestLineTags(unittest.TestCase):
    def test_tag_only_lines(self):
        cases = {
            "[Verse 1]": ["Verse 1"],
            "  [Chorus: full band]  ": ["Chorus: full band"],
            "[Verse 1] [Whispered]": ["Verse 1", "Whispered"],
            "[Silence][Break]": ["Silence", "Break"],
            "﻿[Verse 1]": ["Verse 1"],
        }
        for line, tags in cases.items():
            with self.subTest(line=line):
                self.assertEqual(tag_vocab.line_tags(line), tags)
                self.assertTrue(tag_vocab.is_tag_line(line))

    def test_lines_that_are_sung(self):
        for line in ("", "   ", "plain words", "[male vocals] I was there", "stay [Silence]",
                     "[Chorus", "Chorus]", "[Verse 1] words [Silence]"):
            with self.subTest(line=line):
                self.assertEqual(tag_vocab.line_tags(line), [])
                self.assertFalse(tag_vocab.is_tag_line(line))

    def test_section_opener_is_the_first_section_tag_on_the_line(self):
        self.assertEqual(tag_vocab.section_opener("[Verse 1] [Whispered]"), "Verse 1")
        self.assertEqual(tag_vocab.section_opener("[Whispered] [Chorus: big]"), "Chorus: big")
        for line in ("[Whispered]", "[Mood: dark]", "[End]", "[Banana]", "words", ""):
            with self.subTest(line=line):
                self.assertIsNone(tag_vocab.section_opener(line))


if __name__ == "__main__":
    unittest.main()
