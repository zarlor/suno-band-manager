#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
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


def test_extract_lyrics_picks_the_tagged_block():
    lyrics = sm.extract_lyrics(PACKAGE)
    assert "[Verse 1 - tight lockstep, controlled weight]" in lyrics and "Style prompt" not in lyrics
    assert sm.extract_lyrics("[Verse]\nplain text") == "[Verse]\nplain text"


def test_extract_lyrics_block_out_of_range():
    try:
        sm.extract_lyrics(PACKAGE, block=3)
    except ValueError as exc:
        assert "1 tagged block" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_parse_sections_modifiers_cues_and_end():
    sections, song_mods = sm.parse_sections(sm.extract_lyrics(PACKAGE))
    assert song_mods == ["Mood: stoic, heavy"]
    assert [s["name"] for s in sections] == ["Intro", "Verse 1", "Guitar Solo", "Chorus", "Final Verse"]
    verse = sections[1]
    assert verse["cue"] == "tight lockstep, controlled weight"
    assert verse["modifiers"] == ["Vocal Style: clean, sung"] and len(verse["lines"]) == 2
    assert all("ignored" not in l for s in sections for l in s["lines"])


def test_untagged_lines_before_first_section():
    sections, _ = sm.parse_sections("loose line\n[Chorus]\nsung")
    assert sections[0]["name"] == "(untagged)" and sections[0]["lines"] == ["loose line"]


def test_inline_silence_is_stripped_and_standalone_silence_does_not_split():
    sections, _ = sm.parse_sections(
        "[Verse 1]\nI stand where the water breaks [Silence]\n[Silence]\nI hold what the thunder takes [Silence]\n"
        "[Chorus]\nRock in the storm\n[Silence]\n[End]")
    assert [s["name"] for s in sections] == ["Verse 1", "Chorus"]
    verse = sections[0]
    assert verse["lines"] == ["I stand where the water breaks", "I hold what the thunder takes"]
    assert verse["inline_tags"] == ["Silence"] and verse["modifiers"] == ["Silence"]
    assert sections[1]["modifiers"] == ["Silence"]
    words = words_for("I stand where the water breaks I hold what the thunder takes", 3.0)
    entry = sm.locate_sections(sections, words, 20.0)[0]
    assert entry["coverage"] == 1.0 and entry["inline_tags"] == ["Silence"]


def test_tokenize():
    assert sm.tokenize("Don’t STOP, rock-and-roll!") == ["dont", "stop", "rock", "and", "roll"]


def test_align_tolerates_misheard_and_extra_words():
    lyric = sm.tokenize("the rock in the storm stands")
    heard = sm.tokenize("yeah the rok in the storm uh stands")
    pairs = sm.align(lyric, heard)
    assert [lyric[i] for i, _ in pairs] == ["the", "rock", "in", "the", "storm", "stands"]


def test_main_cluster_drops_a_far_match():
    items = [(10.0, "a"), (11.0, "b"), (12.5, "c"), (95.0, "stray")]
    assert [p for _, p in sm.main_cluster(items)] == ["a", "b", "c"]


def test_locate_sections_places_sung_instrumental_and_missing():
    sections, _ = sm.parse_sections(sm.extract_lyrics(PACKAGE))
    words = (words_for("I stand where the water breaks I hold what the thunder takes", 10.0)
             + words_for("rock in the storm rock in the storm", 40.0))
    entries = {e["name"]: e for e in sm.locate_sections(sections, words, duration=60.0)}
    verse, solo, chorus, last = entries["Verse 1"], entries["Guitar Solo"], entries["Chorus"], entries["Final Verse"]
    assert verse["status"] == "sung" and verse["coverage"] == 1.0 and verse["start_s"] == 10.0
    assert chorus["status"] == "sung" and chorus["start_s"] == 40.0
    assert solo["status"] == "instrumental (inferred)" and solo["start_s"] == verse["end_s"]
    assert solo["end_s"] == chorus["start_s"]
    assert entries["Intro"]["start_s"] == 0.0 and entries["Intro"]["end_s"] == 10.0
    assert last["status"] == "not heard" and last["lines_not_heard"] == ["Nobody hears the last word"]


def test_untagged_lead_in_and_tail_get_rows():
    sections, _ = sm.parse_sections("[Verse]\nI stand where the water breaks tonight")
    entries = sm.locate_sections(sections, words_for("I stand where the water breaks tonight", 20.0), 40.0)
    assert [e["name"] for e in entries] == ["(lead-in)", "Verse", "(tail)"]
    assert entries[0]["start_s"] == 0.0 and entries[0]["end_s"] == 20.0 and entries[0]["status"] == "untagged"
    assert entries[2]["end_s"] == 40.0


def test_changed_line_is_reported():
    sections, _ = sm.parse_sections("[Verse]\nI stand where the water breaks\nI hold what the thunder takes")
    words = words_for("I stand where the water breaks and nothing else comes out", 5.0)
    entry = next(e for e in sm.locate_sections(sections, words, 30.0) if e["name"] == "Verse")
    assert entry["lines_not_heard"] == ["I hold what the thunder takes"]
    assert entry["status"] == "sung"  # 6 of 12 words


def test_consensus_over_passes():
    sections, _ = sm.parse_sections(
        "[Verse]\nI stand where the water breaks\nI hold what the thunder takes\nnobody hears the last word")
    full = "I stand where the water breaks I hold what the thunder takes nobody hears the last word"
    p1 = words_for(full, 10.0)
    p2 = words_for("I stand where the water breaks I hold what the thunder takes", 10.4)
    p3 = words_for("I stand where the water breaks the thunder nobody hears the last word", 10.2)
    e = next(x for x in sm.locate_consensus(sections, [p1, p2, p3], 40.0) if x["name"] == "Verse")
    assert e["located_passes"] == "3/3" and e["start_s"] == 10.2  # median start
    assert e["lines_not_heard"] == []  # each line is missed by at most one pass
    assert {u["line"]: u["missed_in"] for u in e["lines_uncertain"]} == {
        "I hold what the thunder takes": 1, "nobody hears the last word": 1}
    e2 = next(x for x in sm.locate_consensus(sections, [p2, p2, p1], 40.0) if x["name"] == "Verse")
    assert e2["lines_not_heard"] == ["nobody hears the last word"]  # missed by 2 of 3


def test_single_pass_matches_locate_sections():
    sections, _ = sm.parse_sections(sm.extract_lyrics(PACKAGE))
    words = words_for("I stand where the water breaks I hold what the thunder takes", 10.0)
    assert sm.locate_sections(sections, words, 60.0) == sm.locate_consensus(sections, [words], 60.0)


def test_blocks_from_activity_bridges_short_gaps():
    active = [False] * 2 + [True] * 6 + [False] * 2 + [True] * 4 + [False] * 10 + [True] * 2
    assert sm.blocks_from_activity(active) == [(1.0, 7.0)]


def test_outside_spans():
    # The 10-12 s gap is under the 3 s minimum, so only the two ends remain.
    assert sm.outside_spans([(0.0, 30.0)], [(12.0, 20.0), (5.0, 10.0)]) == [(0.0, 5.0), (20.0, 30.0)]
    assert sm.outside_spans([(0.0, 4.0)], [(0.0, 4.0)]) == []


def test_format_text_lists_unheard_and_outside_vocals():
    sections, _ = sm.parse_sections(sm.extract_lyrics(PACKAGE))
    words = words_for("I stand where the water breaks I hold what the thunder takes", 10.0)
    entries = sm.locate_sections(sections, words, 60.0)
    metrics = {"file": "x.mp3", "lyrics_source": "pkg.md", "whisper_model": "medium", "whisper_device": "cpu",
               "tempo_source": "beat-this", "overall_bpm": 125.0, "sections": entries,
               "vocals_outside_sections": [{"start_s": 50.0, "end_s": 55.0, "heard": "oh yeah", "mean_probability": 0.9},
                                           {"start_s": 5.0, "end_s": 9.0, "heard": "thanks for watching",
                                            "mean_probability": 0.2}]}
    text = sm.format_text(metrics)
    assert "Verse 1 - tight lockstep" in text and "not heard" in text
    assert "[Chorus] Rock in the storm" in text and "0:50-0:55  oh yeah" in text and "Beat This!" in text
    assert "0:05-0:09  thanks for watching  (low confidence: may be a transcription artifact)" in text
    assert "1 pass(es)" in text
    assert "oh yeah  (low" not in text


def run(args):
    return subprocess.run([sys.executable, str(SCRIPT), *args, "--no-archive"], capture_output=True, text=True,
                          timeout=60)


def test_missing_audio_exits_1(tmp_path):
    lyr = tmp_path / "l.txt"
    lyr.write_text("[Verse]\nx")
    assert run(["/nonexistent-audio-xyz.mp3", "--lyrics", str(lyr)]).returncode == 1


def test_missing_lyrics_exits_1(tmp_path):
    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"")
    assert run([str(audio), "--lyrics", str(tmp_path / "none.txt")]).returncode == 1


def test_lyrics_without_section_tags_exit_1(tmp_path):
    audio, lyr = tmp_path / "a.mp3", tmp_path / "l.txt"
    audio.write_bytes(b"")
    lyr.write_text("just words\nno tags")
    proc = run([str(audio), "--lyrics", str(lyr)])
    assert proc.returncode == 1 and "No section tags" in proc.stderr
