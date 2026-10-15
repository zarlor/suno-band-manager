#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for section-map.py (Demucs + Whisper section alignment).

Demucs and Whisper need PyTorch and model downloads, too heavy for the suite, so
these pin the pure logic: lyric extraction and section parsing, tokenizing, the
transcript-to-lyrics alignment, section placement (including inferred
instrumentals and unheard lines), vocal-activity blocks, and the exit-code
contract (the path and lyric guards run before the dependency check).
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "section-map.py"
spec = importlib.util.spec_from_file_location("section_map", SCRIPT)
sm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sm)

PACKAGE = """# Package

```
Style prompt text [not a section]
```

```
[Mood: stoic, heavy]
[Intro]
[Verse 1 - tight lockstep, controlled weight]
[Vocal Style: clean, sung]
I stand where the water breaks
I hold what the thunder takes
[Guitar Solo - searing, wide]
[Chorus]
Rock in the storm
Rock in the storm
[Final Verse - one bare voice]
Nobody hears the last word
[End]
Anything after End is ignored
```
"""


def words_for(text, start, step=0.4):
    out, t = [], start
    for w in text.split():
        out.append({"word": " " + w, "start": t, "end": t + step * 0.8})
        t += step
    return out


CHORUS = "[Chorus]\none more spin one more spin\ngettin lost for a while\n[Verse]\nthe needle drops again tonight"


def added(heard_chorus, passes=1):
    sections, _ = sm.parse_sections(CHORUS)
    words = words_for(heard_chorus + " the needle drops again tonight", 5.0)
    return next(x for x in sm.locate_consensus(sections, [words] * passes, 60.0) if x["name"] == "Chorus")


COMMON = "[Chorus]\nyou don't know if I will stay\ngettin lost for a while\n[Verse]\nthe needle drops again tonight"


def run(args):
    return subprocess.run([sys.executable, str(SCRIPT), *args, "--no-archive"], capture_output=True, text=True,
                          timeout=60)


class ParsingTest(unittest.TestCase):
    def test_extract_lyrics_picks_the_tagged_block(self):
        lyrics = sm.extract_lyrics(PACKAGE)
        self.assertIn("[Verse 1 - tight lockstep, controlled weight]", lyrics)
        self.assertNotIn("Style prompt", lyrics)
        self.assertEqual(sm.extract_lyrics("[Verse]\nplain text"), "[Verse]\nplain text")

    def test_extract_lyrics_block_out_of_range(self):
        with self.assertRaises(ValueError) as ctx:
            sm.extract_lyrics(PACKAGE, block=3)
        self.assertIn("1 tagged block", str(ctx.exception))

    def test_parse_sections_modifiers_cues_and_end(self):
        sections, song_mods = sm.parse_sections(sm.extract_lyrics(PACKAGE))
        self.assertEqual(song_mods, ["Mood: stoic, heavy"])
        self.assertEqual([s["name"] for s in sections], ["Intro", "Verse 1", "Guitar Solo", "Chorus", "Final Verse"])
        verse = sections[1]
        self.assertEqual(verse["cue"], "tight lockstep, controlled weight")
        self.assertEqual(verse["modifiers"], ["Vocal Style: clean, sung"])
        self.assertEqual(len(verse["lines"]), 2)
        self.assertTrue(all("ignored" not in l for s in sections for l in s["lines"]))

    def test_untagged_lines_before_first_section(self):
        sections, _ = sm.parse_sections("loose line\n[Chorus]\nsung")
        self.assertEqual(sections[0]["name"], "(untagged)")
        self.assertEqual(sections[0]["lines"], ["loose line"])

    def test_inline_silence_is_stripped_and_standalone_silence_does_not_split(self):
        sections, _ = sm.parse_sections(
            "[Verse 1]\nI stand where the water breaks [Silence]\n[Silence]\nI hold what the thunder takes [Silence]\n"
            "[Chorus]\nRock in the storm\n[Silence]\n[End]")
        self.assertEqual([s["name"] for s in sections], ["Verse 1", "Chorus"])
        verse = sections[0]
        self.assertEqual(verse["lines"], ["I stand where the water breaks", "I hold what the thunder takes"])
        self.assertEqual(verse["inline_tags"], ["Silence"])
        self.assertEqual(verse["modifiers"], ["Silence"])
        self.assertEqual(sections[1]["modifiers"], ["Silence"])
        words = words_for("I stand where the water breaks I hold what the thunder takes", 3.0)
        entry = sm.locate_sections(sections, words, 20.0)[0]
        self.assertEqual(entry["coverage"], 1.0)
        self.assertEqual(entry["inline_tags"], ["Silence"])

    def test_tokenize(self):
        self.assertEqual(sm.tokenize("Don’t STOP, rock-and-roll!"), ["dont", "stop", "rock", "and", "roll"])

    def test_align_tolerates_misheard_and_extra_words(self):
        lyric = sm.tokenize("the rock in the storm stands")
        heard = sm.tokenize("yeah the rok in the storm uh stands")
        pairs = sm.align(lyric, heard)
        self.assertEqual([lyric[i] for i, _ in pairs], ["the", "rock", "in", "the", "storm", "stands"])

    def test_main_cluster_drops_a_far_match(self):
        items = [(10.0, "a"), (11.0, "b"), (12.5, "c"), (95.0, "stray")]
        self.assertEqual([p for _, p in sm.main_cluster(items)], ["a", "b", "c"])


class LocateTest(unittest.TestCase):
    def test_locate_sections_places_sung_instrumental_and_missing(self):
        sections, _ = sm.parse_sections(sm.extract_lyrics(PACKAGE))
        words = (words_for("I stand where the water breaks I hold what the thunder takes", 10.0)
                 + words_for("rock in the storm rock in the storm", 40.0))
        entries = {e["name"]: e for e in sm.locate_sections(sections, words, duration=60.0)}
        verse, solo, chorus, last = entries["Verse 1"], entries["Guitar Solo"], entries["Chorus"], entries["Final Verse"]
        self.assertEqual(verse["status"], "sung")
        self.assertEqual(verse["coverage"], 1.0)
        self.assertEqual(verse["start_s"], 10.0)
        self.assertEqual(chorus["status"], "sung")
        self.assertEqual(chorus["start_s"], 40.0)
        self.assertEqual(solo["status"], "instrumental (inferred)")
        self.assertEqual(solo["start_s"], verse["end_s"])
        self.assertEqual(solo["end_s"], chorus["start_s"])
        self.assertEqual(entries["Intro"]["start_s"], 0.0)
        self.assertEqual(entries["Intro"]["end_s"], 10.0)
        self.assertEqual(last["status"], "not heard")
        self.assertEqual(last["lines_not_heard"], ["Nobody hears the last word"])

    def test_untagged_lead_in_and_tail_get_rows(self):
        sections, _ = sm.parse_sections("[Verse]\nI stand where the water breaks tonight")
        entries = sm.locate_sections(sections, words_for("I stand where the water breaks tonight", 20.0), 40.0)
        self.assertEqual([e["name"] for e in entries], ["(lead-in)", "Verse", "(tail)"])
        self.assertEqual(entries[0]["start_s"], 0.0)
        self.assertEqual(entries[0]["end_s"], 20.0)
        self.assertEqual(entries[0]["status"], "untagged")
        self.assertEqual(entries[2]["end_s"], 40.0)

    def test_changed_line_is_reported(self):
        sections, _ = sm.parse_sections("[Verse]\nI stand where the water breaks\nI hold what the thunder takes")
        words = words_for("I stand where the water breaks and nothing else comes out", 5.0)
        entry = next(e for e in sm.locate_sections(sections, words, 30.0) if e["name"] == "Verse")
        self.assertEqual(entry["lines_not_heard"], ["I hold what the thunder takes"])
        self.assertEqual(entry["status"], "sung")  # 6 of 12 words

    def test_consensus_over_passes(self):
        sections, _ = sm.parse_sections(
            "[Verse]\nI stand where the water breaks\nI hold what the thunder takes\nnobody hears the last word")
        full = "I stand where the water breaks I hold what the thunder takes nobody hears the last word"
        p1 = words_for(full, 10.0)
        p2 = words_for("I stand where the water breaks I hold what the thunder takes", 10.4)
        p3 = words_for("I stand where the water breaks the thunder nobody hears the last word", 10.2)
        e = next(x for x in sm.locate_consensus(sections, [p1, p2, p3], 40.0) if x["name"] == "Verse")
        self.assertEqual(e["located_passes"], "3/3")
        self.assertEqual(e["start_s"], 10.2)  # median start
        # Whisper drops words; one pass hearing a line is enough to count it as sung.
        self.assertEqual(e["lines_not_heard"], [])
        e2 = next(x for x in sm.locate_consensus(sections, [p2, p2, p2], 40.0) if x["name"] == "Verse")
        self.assertEqual(e2["lines_not_heard"], ["nobody hears the last word"])  # every pass missed it

    def test_any_pass_that_places_a_section_places_it(self):
        sections, _ = sm.parse_sections("[Verse]\nForged in fire lived in life\n[Chorus]\nLook into the cracks find the universe")
        found = words_for("Forged in fire lived in life", 20.0) + words_for("Look into the cracks find the universe", 40.0)
        lost = words_for("I'm going to sing a little bit", 20.0) + words_for("Look into the cracks find the universe", 40.0)
        verse = next(x for x in sm.locate_consensus(sections, [found, lost], 60.0) if x["name"] == "Verse")
        self.assertEqual(verse["status"], "sung")
        self.assertEqual(verse["start_s"], 20.0)
        self.assertEqual(verse["located_passes"], "1/2")

    def test_single_pass_matches_locate_sections(self):
        sections, _ = sm.parse_sections(sm.extract_lyrics(PACKAGE))
        words = words_for("I stand where the water breaks I hold what the thunder takes", 10.0)
        self.assertEqual(sm.locate_sections(sections, words, 60.0), sm.locate_consensus(sections, [words], 60.0))


class AddedWordsTest(unittest.TestCase):
    def test_added_words_between_lines_are_flagged(self):
        e = added("one more spin one more spin get more spin gettin lost for a while")
        self.assertEqual([a["text"] for a in e["added_words"]], ["get more spin"])
        a = e["added_words"][0]
        self.assertEqual(a["kind"], "added")
        self.assertEqual(a["position"], "between lines")
        self.assertEqual(a["after_line"], "one more spin one more spin")
        self.assertEqual(e["coverage"], 1.0)
        self.assertEqual(e["repeats"], [])

    def test_words_added_inside_a_line(self):
        e = added("one more spin one more spin gettin lost in the fog for a while")
        self.assertEqual([(a["text"], a["position"]) for a in e["added_words"]], [("in the fog", "inside a line")])

    def test_whole_line_repeat_is_listed_not_flagged(self):
        e = added("one more spin one more spin gettin lost for a while gettin lost for a while")
        self.assertEqual(e["added_words"], [])
        self.assertIn([a["repeat_of"] for a in e["repeats"]], ([], ["gettin lost for a while"]))

    def test_fillers_are_ignored(self):
        e = added("one more spin one more spin oh yeah gettin lost for a while")
        self.assertEqual(e["added_words"], [])
        self.assertEqual(e["repeats"], [])

    def test_words_tacked_onto_the_last_line_are_caught(self):
        sections, _ = sm.parse_sections("[Chorus]\nLook into the cracks\nfind the universe\n[Verse]\nthe needle drops again tonight")
        words = words_for("Look into the cracks find the universe", 100.0)
        tail = words_for("of Christ", words[-1]["end"] + 1.5)
        for w in tail:
            w["probability"] = 0.27
        rest = words_for("the needle drops again tonight", tail[-1]["end"] + 6.0)
        e = next(x for x in sm.locate_consensus(sections, [words + tail + rest], 200.0) if x["name"] == "Chorus")
        self.assertEqual(e["added_words"], [])  # Whisper wasn't sure of the words...
        self.assertEqual([(a["text"], a["position"]) for a in e["added_words_possible"]],
                         [("of Christ", "after the last line")])
        for w in tail:
            w["probability"] = 0.9
        e = next(x for x in sm.locate_consensus(sections, [words + tail + rest], 200.0) if x["name"] == "Chorus")
        self.assertEqual([a["text"] for a in e["added_words"]], ["of Christ"])  # ...and it is when it's sure

    def test_misheard_opening_of_the_next_section_is_not_an_addition(self):
        sections, _ = sm.parse_sections("[Verse]\nrocks thrown they fight have the need\n[Chorus]\nLook into the cracks\nfind the universe")
        words = (words_for("rocks thrown they fight have the need", 90.0)
                 + words_for("Looking to the cracks find the universe", 94.0))
        verse = next(x for x in sm.locate_consensus(sections, [words], 200.0) if x["name"] == "Verse")
        self.assertEqual(verse["added_words"], [])
        self.assertEqual(verse["added_words_possible"], [])

    def test_edge_scan_stops_at_the_next_section_and_the_window(self):
        sections, _ = sm.parse_sections("[Chorus]\nLook into the cracks\nfind the universe\n[Verse]\nthe needle drops again tonight")
        words = words_for("Look into the cracks find the universe", 100.0)
        late = words_for("something much later", words[-1]["end"] + 9.0)  # beyond EDGE_ADD_S
        rest = words_for("the needle drops again tonight", late[-1]["end"] + 1.0)
        e = next(x for x in sm.locate_consensus(sections, [words + late + rest], 200.0) if x["name"] == "Chorus")
        self.assertEqual(e["added_words"], [])
        self.assertEqual(e["added_words_possible"], [])

    def test_repeat_of_a_phrase_spread_over_one_word_lines(self):
        sections, _ = sm.parse_sections("[Breakdown]\nNOT\nBUILT\nTHAT\nWAY\n[Outro]\nChomp the glass again tonight")
        words = (words_for("NOT BUILT THAT WAY", 140.0) + words_for("not built that way", 143.0)
                 + words_for("Chomp the glass again tonight", 146.0))
        e = next(x for x in sm.locate_consensus(sections, [words], 200.0) if x["name"] == "Breakdown")
        self.assertEqual(e["added_words"], [])
        self.assertEqual(e["added_words_possible"], [])
        self.assertEqual([a["repeat_of"] for a in e["repeats"]], ["NOT / BUILT / THAT / WAY"])

    def test_near_spelled_repeat_is_still_a_repeat(self):
        # Whisper writes "doing" where the lyric has "doin'".
        self.assertEqual(sm._classify_added(sm.tokenize("What am I doing?"), ["What am I doin'?"]),
                         ("repeat", "What am I doin'?"))

    def test_repeated_one_word_hit_is_a_repeat(self):
        self.assertEqual(sm._classify_added(["chomp", "chomp", "chomp"], ["CHOMP!", "Here it comes again"]),
                         ("partial repeat", "CHOMP!"))

    def test_mishearing_is_not_an_addition(self):
        # "gettin" heard as "get it in": one lyric word replaced by three similar-sounding ones.
        e = added("one more spin one more spin get it in lost for a while")
        self.assertEqual(e["added_words"], [])
        self.assertEqual(e["added_words_possible"], [])

    def test_short_extra_is_not_an_addition(self):
        e = added("one more spin one more spin oh at gettin lost for a while")
        self.assertEqual(e["added_words"], [])

    def test_unsure_words_stay_possible(self):
        sections, _ = sm.parse_sections(CHORUS)
        words = words_for("one more spin one more spin get more spin gettin lost for a while the needle drops again tonight",
                          5.0)
        for w in words[6:9]:
            w["probability"] = 0.2
        e = next(x for x in sm.locate_consensus(sections, [words], 60.0) if x["name"] == "Chorus")
        self.assertEqual(e["added_words"], [])
        self.assertEqual([a["text"] for a in e["added_words_possible"]], ["get more spin"])

    def test_added_words_need_most_passes(self):
        sections, _ = sm.parse_sections(CHORUS)
        clean = words_for("one more spin one more spin gettin lost for a while the needle drops again tonight", 5.0)
        padded = words_for("one more spin one more spin get more spin gettin lost for a while the needle drops again tonight",
                           5.0)
        one = next(x for x in sm.locate_consensus(sections, [padded, clean, clean], 60.0) if x["name"] == "Chorus")
        self.assertEqual(one["added_words"], [])
        self.assertEqual([a["passes"] for a in one["added_words_possible"]], ["1/3"])
        two = next(x for x in sm.locate_consensus(sections, [padded, padded, clean], 60.0) if x["name"] == "Chorus")
        self.assertEqual([a["passes"] for a in two["added_words"]], ["2/3"])

    def test_common_word_addition_stays_added_with_a_riff_hint(self):
        # "I know you" uses only words from the first line but doesn't repeat itself: new words, not a riff.
        line = "you don't know if I will stay"
        self.assertEqual(sm._classify_added(sm.tokenize("I know you"), [line]), ("added", None))
        self.assertEqual(sm.riff_of(sm.tokenize("I know you"), [line]), line)
        sections, _ = sm.parse_sections(COMMON)
        words = words_for("you don't know if I will stay I know you gettin lost for a while the needle drops again tonight",
                          5.0)
        e = next(x for x in sm.locate_consensus(sections, [words], 60.0) if x["name"] == "Chorus")
        self.assertEqual(e["repeats"], [])
        self.assertEqual([a["text"] for a in e["added_words"]], ["I know you"])
        a = e["added_words"][0]
        self.assertEqual(a["kind"], "added")
        self.assertEqual(a["looks_like_riff_of"], line)
        metrics = {"file": "x.mp3", "lyrics_source": "pkg.md", "whisper_model": "medium", "whisper_device": "cpu",
                   "tempo_source": "librosa", "overall_bpm": 120.0, "sections": [e], "vocals_outside_sections": []}
        self.assertIn(f'(may riff on "{line}")', sm.format_text(metrics))

    def test_genuine_addition_has_no_riff_hint(self):
        e = added("one more spin one more spin get more spin gettin lost for a while")
        self.assertNotIn("looks_like_riff_of", e["added_words"][0])


class OutsideVocalsTest(unittest.TestCase):
    def test_blocks_from_activity_bridges_short_gaps(self):
        active = [False] * 2 + [True] * 6 + [False] * 2 + [True] * 4 + [False] * 10 + [True] * 2
        self.assertEqual(sm.blocks_from_activity(active), [(1.0, 7.0)])

    def test_outside_vocals_that_repeat_a_lyric_are_labeled(self):
        lines = ["I'm the slide that's violently slammed in the dark", "and another one after that"]
        self.assertEqual(sm.label_outside("Slammed in the dark", lines),
                         {"kind": "partial repeat", "line": "I'm the slide that's violently slammed in the dark"})
        self.assertEqual(sm.label_outside("check and another one after that.", lines)["line"],
                         "and another one after that")
        riff = "And another one after that After that, after that, and another one after that."
        self.assertEqual(sm.label_outside(riff, lines), {"kind": "partial repeat", "line": "and another one after that"})
        # Riffing needs the run's words to come from the line: "get" isn't in "one more spin, one more spin".
        self.assertEqual(sm._classify_added(sm.tokenize("get more spin"), ["one more spin, one more spin"]),
                         ("added", None))

        self.assertIsNone(sm.label_outside("Screamer! Screamer!", lines))
        self.assertIsNone(sm.label_outside("oh yeah", lines))

    def test_outside_common_word_run_gets_a_hint_not_a_repeat_label(self):
        line = "you don't know if I will stay"
        self.assertEqual(sm.label_outside("I know you", [line]),
                         {"kind": "added", "line": None, "looks_like_riff_of": line})

    def test_clip_ranges_pad_merge_and_clamp(self):
        self.assertEqual(sm.clip_ranges([(20.0, 61.5), (92.0, 150.0)], 168.0), [19.25, 62.25, 91.25, 150.75])
        self.assertEqual(sm.clip_ranges([(0.2, 10.0), (10.5, 20.0)], 20.3), [0.0, 20.3])  # touching blocks merge
        self.assertEqual(sm.clip_ranges([], 60.0), [])

    def test_outside_spans(self):
        # The 10-12 s gap is under the 3 s minimum, so only the two ends remain.
        self.assertEqual(sm.outside_spans([(0.0, 30.0)], [(12.0, 20.0), (5.0, 10.0)]), [(0.0, 5.0), (20.0, 30.0)])
        self.assertEqual(sm.outside_spans([(0.0, 4.0)], [(0.0, 4.0)]), [])


class FormatTextTest(unittest.TestCase):
    def test_format_text_lists_added_words(self):
        e = added("one more spin one more spin get more spin gettin lost for a while")
        metrics = {"file": "x.mp3", "lyrics_source": "pkg.md", "whisper_model": "medium", "whisper_device": "cpu",
                   "tempo_source": "librosa", "overall_bpm": 180.0, "sections": [e], "vocals_outside_sections": []}
        text = sm.format_text(metrics)
        self.assertIn('Words added to the lyrics', text)
        self.assertIn('"get more spin"  between lines', text)

    def test_format_text_reports_the_slow_prior_reading(self):
        e = added("one more spin one more spin get more spin gettin lost for a while")
        note = "Likely halftime ambiguity: librosa reads 117.5 BPM at its default and 60.1 with a slow prior."
        metrics = {"file": "x.mp3", "lyrics_source": "pkg.md", "whisper_model": "medium", "whisper_device": "cpu",
                   "tempo_source": "librosa", "overall_bpm": 117.5, "bpm_librosa_slow_prior": 60.1,
                   "librosa_prior_relation": "double", "tempo_note": note, "sections": [e],
                   "vocals_outside_sections": []}
        text = sm.format_text(metrics)
        self.assertIn("librosa 117.5 BPM (slow-prior reading 60.1, double)", text)
        self.assertIn(note, text)
        del metrics["bpm_librosa_slow_prior"], metrics["tempo_note"]
        self.assertNotIn("slow-prior", sm.format_text(metrics))

    def test_format_text_lists_unheard_and_outside_vocals(self):
        sections, _ = sm.parse_sections(sm.extract_lyrics(PACKAGE))
        words = words_for("I stand where the water breaks I hold what the thunder takes", 10.0)
        entries = sm.locate_sections(sections, words, 60.0)
        metrics = {"file": "x.mp3", "lyrics_source": "pkg.md", "whisper_model": "medium", "whisper_device": "cpu",
                   "tempo_source": "beat-this", "overall_bpm": 125.0, "sections": entries,
                   "vocals_outside_sections": [{"start_s": 50.0, "end_s": 55.0, "heard": "oh yeah", "mean_probability": 0.9},
                                               {"start_s": 5.0, "end_s": 9.0, "heard": "thanks for watching",
                                                "mean_probability": 0.2}]}
        text = sm.format_text(metrics)
        self.assertIn("Verse 1 - tight lockstep", text)
        self.assertIn("not heard", text)
        self.assertIn("[Chorus] Rock in the storm", text)
        self.assertIn("0:50-0:55  oh yeah", text)
        self.assertIn("Beat This!", text)
        self.assertIn("0:05-0:09  thanks for watching  (low confidence: may be a transcription artifact)", text)
        self.assertIn("1 pass(es)", text)
        self.assertNotIn("oh yeah  (low", text)


class ExitCodeTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp_path = Path(td.name)

    def test_missing_audio_exits_1(self):
        lyr = self.tmp_path / "l.txt"
        lyr.write_text("[Verse]\nx")
        self.assertEqual(run(["/nonexistent-audio-xyz.mp3", "--lyrics", str(lyr)]).returncode, 1)

    def test_missing_lyrics_exits_1(self):
        audio = self.tmp_path / "a.mp3"
        audio.write_bytes(b"")
        self.assertEqual(run([str(audio), "--lyrics", str(self.tmp_path / "none.txt")]).returncode, 1)

    def test_lyrics_without_section_tags_exit_1(self):
        audio, lyr = self.tmp_path / "a.mp3", self.tmp_path / "l.txt"
        audio.write_bytes(b"")
        lyr.write_text("just words\nno tags")
        proc = run([str(audio), "--lyrics", str(lyr)])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("No section tags", proc.stderr)


if __name__ == "__main__":
    unittest.main()
