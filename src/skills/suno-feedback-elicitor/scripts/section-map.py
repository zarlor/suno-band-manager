#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["demucs>=4.0.1", "torch>=2.1", "faster-whisper>=1.1", "librosa>=1.0", "numpy>=2.1", "pyloudnorm>=0.2"]
# ///
"""Section map — where each tagged section of the lyrics landed in a render, and how it sounds.

Compares a render with the lyrics it was generated from, section by section:

1. Demucs (htdemucs) separates the vocal stem from the band.
2. faster-whisper transcribes the vocal stem with word timestamps. The isolated
   vocal transcribes far better than the full mix. The lyrics are NOT given to
   Whisper as a hint, so it reports what was sung, not what was expected.
   Consistency comes from averaging, not from switching features off: Demucs
   averages several seeded time-shifts (cleaner stems, same stems every run),
   and Whisper keeps its fallback retries, seeded, over several passes. Section
   times are the median across passes. Whisper drops words far more often
   than it invents an exact lyric line, so a line counts as not heard only
   when every pass misses it. Added words need most passes to agree, since
   Whisper can invent words; the rest are listed as possible.
3. The transcript is aligned to the lyric lines (fuzzy word matching), which
   gives every tagged section a start and end time. It works even where Suno
   runs sections together, because the words mark the boundaries, not gaps.
   Sections with no lyrics ([Guitar Solo], [Intro]) are placed in the space
   between their sung neighbours and marked as inferred. An untagged lead-in
   or tail of 5 s or more gets its own row.
4. Each section gets: mix loudness and the step from the section before,
   vocal-minus-band loudness (LU), tempo and feel (Beat This! when the PyTorch
   audio tools are on, else librosa), and key.

Also reports words added to the lyrics: a run of words inside a section that
isn't in the lyric, e.g. "one more spin, one more spin, get more spin, gettin'
lost". Whole-line repeats are listed separately (often fine, judged by ear);
fragments of a line are marked as partial repeats. Fillers (oh, yeah, whoa)
are ignored.

It also reports lyric lines that weren't heard (dropped or changed words) and
vocals outside any lyric section: ad-libs, repeats, invented lines, and
wordless vocalizing (an "ooh-whoa" fill, scat, a held vowel), which Whisper
leaves untranscribed. v5.5-era renders scatted a lot; v6 seems to do it less.

Descriptive, not a verdict: transcription of sung vocals is imperfect, so a
"not heard" line is a prompt to listen, not proof of a change.

Lyrics: a plain text file, or a Markdown package/songbook doc. From Markdown,
the fenced block with the most section tags is used (--lyrics-block picks
another).

Optional and heavy: PyTorch, the htdemucs weights (~80 MB) and a Whisper model,
downloaded on first use. Demucs uses a CUDA GPU when present. Whisper runs on
CPU by default (int8); `--whisper-device cuda` needs CUDA 12 cuBLAS/cuDNN
libraries, which the PyTorch CUDA 13 build doesn't provide, and falls back to
CPU when they're missing.

Usage:
    uv run section-map.py <audio-file> --lyrics <lyrics-or-package-file> [options]

    uv run section-map.py "docs/audio/my-band/Song.mp3" --lyrics docs/songbook/my-band/song.md --format text

Exit codes:
  0 = success
  1 = invalid arguments (audio or lyrics not found, no section tags) or runtime error
  2 = missing dependencies
"""

import argparse
import difflib
import json
import os
import re
import statistics
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from audio_deps import require_modules
from json_archiver import input_archive_identifier, resolve_archive_arg, write_archive
from tempo_source import (SOURCE_LABELS, SHIFT_THRESHOLD, add_tempo_source_arg, beat_this_readings, feel_name,
                          resolve_tempo_source, usable)

SCRIPT_NAME = "section-map"
VERSION = "1.1.0"
INSTALL_CMD = "pip install demucs torch faster-whisper librosa numpy pyloudnorm"
DEMUCS_MODEL = "htdemucs"
WHISPER_MODEL = "medium"
WHISPER_PASSES = 3
GPU_SHIFTS = 5  # averaged Demucs time-shifts on a GPU; CPU default is 1 (each shift is a full separation)
# A section whose vocal stem sits this far below the band is residual bleed, not singing.
VOCAL_ABSENT_LU = -15.0
# Matched words further apart than this belong to different passes (a repeated chorus line matched out of place).
CLUSTER_GAP_S = 12.0
MIN_MATCHED_WORDS = 3
SUNG_COVERAGE = 0.5
PARTLY_COVERAGE = 0.25
LINE_HEARD_SHARE = 0.34
# Added words: a run of unmatched heard words must add at least this many words and letters beyond
# the lyric words it sits in place of. Below that it's a mishearing ("runnin'" heard as "run at"),
# not an addition.
MIN_ADDED_TOKENS = 2
MIN_ADDED_LETTERS = 6
# A run that sounds like the lyric words it replaces (letter similarity) is a mishearing.
MISHEARD_SIMILARITY = 0.6
# Share of an added run's tokens found, in order, in a lyric line for it to count as a repeat of it.
REPEAT_MATCH = 0.8
FILLERS = frozenset({"oh", "ohh", "ooh", "oooh", "ah", "ahh", "yeah", "yeh", "yea", "hey", "whoa", "woah", "wo",
                     "uh", "na", "la", "mm", "hmm", "ha"})
FRAME_S = 0.5
# An untagged lead-in or tail at least this long gets its own row.
EDGE_MIN_S = 5.0
# Whisper invents words over quiet or bleed-only stretches; below this mean word probability, say so.
LOW_CONFIDENCE = 0.5

SECTION_HEAD_RE = re.compile(
    r"^(?:final\s+|last\s+)?(intro|verse|pre-?chorus|chorus|post-?chorus|hook|refrain|bridge|breakdown|build-?up|"
    r"build|drop|interlude|instrumental|(?:[\w-]+\s+)?solo|break|outro|coda|end|fade\s*(?:out|in))\b",
    re.IGNORECASE,
)
TAG_LINE_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
# Delivery tags inside a lyric line ("...the storm [Silence]") aren't sung words.
INLINE_TAG_RE = re.compile(r"\[([^\]]*)\]")
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MAJOR_PROFILE = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
MINOR_PROFILE = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)


# ---------------------------------------------------------------- lyrics

def tag_head(tag):
    """A tag's name before its cue: "Verse 1 - tight lockstep" -> "Verse 1"."""
    return re.split(r"\s+[-–—]\s+", tag.strip(), maxsplit=1)[0].strip()


def is_section_tag(line):
    m = TAG_LINE_RE.match(line)
    return bool(m) and bool(SECTION_HEAD_RE.match(tag_head(m.group(1))))


def fenced_blocks(text):
    """Fenced blocks that carry at least one section tag, in document order."""
    return [b for b in FENCE_RE.findall(text) if any(is_section_tag(l) for l in b.splitlines())]


def extract_lyrics(text, block=None):
    """The lyric text: the fenced block with the most section tags (or the Nth tagged block), else the whole text."""
    blocks = fenced_blocks(text)
    if not blocks:
        return text
    if block:
        if not 1 <= block <= len(blocks):
            raise ValueError(f"--lyrics-block {block}: the file has {len(blocks)} tagged block(s)")
        return blocks[block - 1]
    return max(blocks, key=lambda b: sum(1 for l in b.splitlines() if is_section_tag(l)))


def parse_sections(text):
    """(sections, song_modifiers). Each section: {tag, name, cue, modifiers, inline_tags, lines}.

    Section tags open a section; other bracket tags ([Vocal Style: clean], a
    standalone [Silence]) are modifiers of the current section, or of the whole
    song before the first section. Tags inside a lyric line (the end-of-line
    [Silence] breathing device) are stripped from the sung text and listed in
    inline_tags. [End] stops parsing. Untagged lines before any section form an
    "(untagged)" section.
    """
    sections, song_modifiers = [], []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = TAG_LINE_RE.match(line)
        if m:
            tag = m.group(1).strip()
            head = tag_head(tag)
            if SECTION_HEAD_RE.match(head):
                if head.lower() == "end":
                    break
                cue = tag[len(head):].strip(" -–—") or None
                sections.append({"tag": tag, "name": head, "cue": cue, "modifiers": [], "inline_tags": [],
                                 "lines": []})
            elif sections:
                sections[-1]["modifiers"].append(tag)
            else:
                song_modifiers.append(tag)
            continue
        inline = [t.strip() for t in INLINE_TAG_RE.findall(line)]
        line = INLINE_TAG_RE.sub(" ", line)
        line = re.sub(r"\s+", " ", line).strip()
        if not sections:
            sections.append({"tag": "(untagged)", "name": "(untagged)", "cue": None, "modifiers": [],
                             "inline_tags": [], "lines": []})
        for t in inline:
            if t and t not in sections[-1]["inline_tags"]:
                sections[-1]["inline_tags"].append(t)
        if line:
            sections[-1]["lines"].append(line)
    return sections, song_modifiers


def tokenize(text):
    """Lower-case ASCII word tokens; apostrophes dropped (don't -> dont), other punctuation splits."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower().replace("'", "")
    return re.findall(r"[a-z0-9]+", text)


# ---------------------------------------------------------------- alignment

def similar(a, b):
    if a == b:
        return True
    if min(len(a), len(b)) < 3:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.75


def align(lyric, heard, match=2, mismatch=-1, gap=-1):
    """Global alignment of lyric tokens to heard tokens -> [(lyric_index, heard_index)] for matched pairs."""
    n, m = len(lyric), len(heard)
    cache = {}
    prev = [j * gap for j in range(m + 1)]
    trace = [bytearray(m + 1) for _ in range(n + 1)]
    for j in range(1, m + 1):
        trace[0][j] = 2
    for i in range(1, n + 1):
        cur = [i * gap] + [0] * m
        trace[i][0] = 1
        a = lyric[i - 1]
        for j in range(1, m + 1):
            key = (a, heard[j - 1])
            s = cache.get(key)
            if s is None:
                s = cache[key] = match if similar(*key) else mismatch
            d, u, left = prev[j - 1] + s, prev[j] + gap, cur[j - 1] + gap
            # On ties, skip a heard word before taking the diagonal: extra words then land after
            # the lyric they follow ("one more spin, one more spin" + "get more spin"), not inside it.
            if left >= d and left >= u:
                cur[j], trace[i][j] = left, 2
            elif d >= u:
                cur[j] = d
            else:
                cur[j], trace[i][j] = u, 1
        prev = cur
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        t = trace[i][j]
        if t == 0:
            if cache[(lyric[i - 1], heard[j - 1])] == match:
                pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif t == 1:
            i -= 1
        else:
            j -= 1
    return pairs[::-1]


def main_cluster(items, max_gap=CLUSTER_GAP_S):
    """The largest run of (time, payload) items whose neighbours sit within max_gap seconds."""
    items = sorted(items)
    if not items:
        return []
    runs, run = [], [items[0]]
    for it in items[1:]:
        if it[0] - run[-1][0] > max_gap:
            runs.append(run)
            run = []
        run.append(it)
    runs.append(run)
    return max(runs, key=len)


def _classify_added(tokens, all_lines):
    """repeat (a whole lyric line again), partial repeat (a fragment of one), or added, plus the line it repeats."""
    best_frac, best_line, best_len = 0.0, None, 0
    for line in all_lines:
        lt = tokenize(line)
        if not lt:
            continue
        found = sum(b.size for b in difflib.SequenceMatcher(None, tokens, lt, autojunk=False).get_matching_blocks())
        frac = found / len(tokens)
        if frac > best_frac or (frac == best_frac and abs(len(lt) - len(tokens)) < abs(best_len - len(tokens))):
            best_frac, best_line, best_len = frac, line, len(lt)
    if best_frac >= REPEAT_MATCH:
        return ("repeat" if len(tokens) >= REPEAT_MATCH * best_len else "partial repeat"), best_line
    return "added", None


def _added_runs(words, matched_lt, first_w, last_w, owner, lyric_tokens, sec_lines, all_lines):
    """Runs of unmatched heard words, between the section's first and last matched words, that add to the lyric.

    Each run is weighed against the lyric words it sits in place of: it counts
    only when it adds MIN_ADDED_TOKENS words and MIN_ADDED_LETTERS letters
    beyond them and doesn't sound like them.
    """
    out, run, prev_lt = [], [], None

    def close(next_lt):
        tokens = [t for wi in run for t in tokenize(words[wi]["word"])]
        if all(t in FILLERS for t in tokens):
            return
        gap = lyric_tokens[prev_lt + 1:next_lt]
        heard_letters, gap_letters = "".join(tokens), "".join(gap)
        if len(tokens) - len(gap) < MIN_ADDED_TOKENS or len(heard_letters) - len(gap_letters) < MIN_ADDED_LETTERS:
            return
        if gap and difflib.SequenceMatcher(None, heard_letters, gap_letters).ratio() >= MISHEARD_SIMILARITY:
            return
        li_before, li_after = owner[prev_lt][1], owner[next_lt][1]
        kind, repeat_of = _classify_added(tokens, all_lines)
        probs = [words[wi].get("probability", 1.0) for wi in run]
        out.append({"anchor": prev_lt, "start_s": round(words[run[0]]["start"], 2),
                    "text": " ".join(words[wi]["word"].strip() for wi in run), "kind": kind, "repeat_of": repeat_of,
                    "replaces": " ".join(gap) or None, "probability": round(statistics.mean(probs), 2),
                    "position": "inside a line" if li_before == li_after else "between lines",
                    "after_line": sec_lines[li_before]})

    for wi in range(first_w, last_w + 1):
        if wi in matched_lt:
            if run and prev_lt is not None:
                close(matched_lt[wi])
            run = []
            prev_lt = matched_lt[wi]
        elif tokenize(words[wi]["word"]):
            run.append(wi)
    return out


def _locate_core(sections, words):
    """One transcription pass: each section's coverage, span, heard text, per-line not-heard flags and added words."""
    lyric_tokens, owner = [], []  # owner: (section index, line index) per lyric token
    for si, sec in enumerate(sections):
        for li, line in enumerate(sec["lines"]):
            for tok in tokenize(line):
                lyric_tokens.append(tok)
                owner.append((si, li))
    all_lines = [line for sec in sections for line in sec["lines"]]
    heard_tokens, heard_word = [], []
    for wi, w in enumerate(words):
        for tok in tokenize(w["word"]):
            heard_tokens.append(tok)
            heard_word.append(wi)
    pairs = align(lyric_tokens, heard_tokens)

    by_section = {}
    for lt, ht in pairs:
        si, li = owner[lt]
        wi = heard_word[ht]
        by_section.setdefault(si, []).append((words[wi]["start"], (lt, wi, li)))

    out = []
    for si, sec in enumerate(sections):
        n_tokens = sum(len(tokenize(l)) for l in sec["lines"])
        entry = {"n_tokens": n_tokens, "matched_words": 0, "coverage": None, "start_s": None, "end_s": None,
                 "heard": "", "line_flags": [False] * len(sec["lines"]), "added": []}
        if n_tokens:
            cluster = main_cluster(by_section.get(si, []))
            matched_lyric = {p[1][0] for p in cluster}
            entry["matched_words"] = len(matched_lyric)
            entry["coverage"] = round(len(matched_lyric) / n_tokens, 2)
            if len(matched_lyric) >= MIN_MATCHED_WORDS and entry["coverage"] >= PARTLY_COVERAGE:
                first_w = min(p[1][1] for p in cluster)
                last_w = max(p[1][1] for p in cluster)
                entry["start_s"] = round(words[first_w]["start"], 2)
                entry["end_s"] = round(words[last_w]["end"], 2)
                entry["heard"] = " ".join(w["word"].strip() for w in words[first_w:last_w + 1])
                matched_lt = {}
                for _, (lt, wi, _) in cluster:
                    matched_lt[wi] = max(lt, matched_lt.get(wi, -1))
                entry["added"] = _added_runs(words, matched_lt, first_w, last_w, owner, lyric_tokens, sec["lines"],
                                             all_lines)
            line_hits = {}
            for _, (_, _, li) in cluster:
                line_hits[li] = line_hits.get(li, 0) + 1
            for li, line in enumerate(sec["lines"]):
                n = len(tokenize(line))
                entry["line_flags"][li] = n >= 2 and line_hits.get(li, 0) / n < LINE_HEARD_SHARE
        out.append(entry)
    return out


def _group_added(per, k, tolerance=2):
    """Group added-word runs from all passes by where they sit (lyric anchor ± tolerance) -> (confirmed, possible).

    Confirmed needs most passes to show the run and Whisper to be reasonably sure of the words
    (mean probability of LOW_CONFIDENCE or more); anything else is possible.
    """
    items = sorted((a["anchor"], pi, a) for pi, p in enumerate(per) for a in p["added"])
    groups = []
    for anchor, pi, a in items:
        if groups and anchor - groups[-1]["last"] <= tolerance:
            groups[-1]["runs"].append((pi, a))
            groups[-1]["last"] = anchor
        else:
            groups.append({"last": anchor, "runs": [(pi, a)]})
    confirmed, possible = [], []
    for g in groups:
        passes = len({pi for pi, _ in g["runs"]})
        a = dict(g["runs"][0][1])
        kinds = [r["kind"] for _, r in g["runs"]]
        a["kind"] = max(set(kinds), key=kinds.count)
        a.pop("anchor")
        a["passes"] = f"{passes}/{k}"
        sure = statistics.mean(r["probability"] for _, r in g["runs"]) >= LOW_CONFIDENCE
        (confirmed if passes * 2 > k and sure else possible).append(a)
    return confirmed, possible


def merge_passes(sections, cores):
    """Consensus across transcription passes, one entry per section.

    A section is placed when most passes place it, at the median start and end;
    coverage is the median. A line is not heard only when every pass misses it
    (Whisper drops words; it rarely invents an exact lyric line). Added words
    count when most passes show them and are listed as possible otherwise.
    """
    k = len(cores)
    merged = []
    for si, sec in enumerate(sections):
        per = [c[si] for c in cores]
        e = {"tag": sec["tag"], "name": sec["name"], "cue": sec["cue"], "modifiers": sec["modifiers"],
             "inline_tags": sec.get("inline_tags", []), "lyric_words": per[0]["n_tokens"], "matched_words": 0,
             "coverage": None, "status": None, "start_s": None, "end_s": None, "located_passes": None,
             "heard": "", "lines_not_heard": [], "added_words": [], "repeats": [], "added_words_possible": []}
        if per[0]["n_tokens"] == 0:
            e["status"] = "instrumental"
            merged.append(e)
            continue
        located = [p for p in per if p["start_s"] is not None]
        e["pass_spans"] = [[p["start_s"], p["end_s"]] for p in located]
        e["coverage"] = round(statistics.median(p["coverage"] for p in per), 2)
        e["matched_words"] = int(statistics.median(p["matched_words"] for p in per))
        e["located_passes"] = f"{len(located)}/{k}"
        if len(located) * 2 > k:
            e["start_s"] = round(statistics.median(p["start_s"] for p in located), 2)
            e["end_s"] = round(statistics.median(p["end_s"] for p in located), 2)
            e["heard"] = min(located, key=lambda p: abs(p["start_s"] - e["start_s"]))["heard"]
            e["status"] = "sung" if e["coverage"] >= SUNG_COVERAGE else "partly sung"
        else:
            e["status"] = "not heard"
        for li, line in enumerate(sec["lines"]):
            if all(p["line_flags"][li] for p in per):
                e["lines_not_heard"].append(line)
        confirmed, possible = _group_added(per, k)
        e["repeats"] = [a for a in confirmed if a["kind"] == "repeat"]
        e["added_words"] = [a for a in confirmed if a["kind"] != "repeat"]
        e["added_words_possible"] = [a for a in possible if a["kind"] != "repeat"]
        merged.append(e)
    return merged


def locate_consensus(sections, word_passes, duration):
    """Place each section in time from one or more transcription passes (see merge_passes)."""
    out = merge_passes(sections, [_locate_core(sections, words) for words in word_passes])
    _place_instrumentals(out, duration)
    _add_untagged_edges(out, duration)
    return out


def locate_sections(sections, words, duration):
    """Place each section in time from a single transcript.

    words: [{"word", "start", "end"}] from the transcriber. Returns one dict per
    section with status (sung / partly sung / not heard / instrumental), start_s,
    end_s, coverage, heard text and lyric lines not heard.
    """
    return locate_consensus(sections, [words], duration)


def _add_untagged_edges(entries, duration, min_s=EDGE_MIN_S):
    """Suno often plays a lead-in or a tail nobody tagged; give each its own row when it's min_s or longer."""
    placed = [e for e in entries if e["start_s"] is not None]
    if not placed:
        return

    def row(tag, a, b):
        return {"tag": tag, "name": tag, "cue": None, "modifiers": [], "inline_tags": [], "lyric_words": 0,
                "matched_words": 0, "located_passes": None, "added_words": [], "repeats": [],
                "added_words_possible": [],
                "coverage": None, "status": "untagged", "start_s": round(a, 2), "end_s": round(b, 2),
                "heard": "", "lines_not_heard": []}

    first, last = min(e["start_s"] for e in placed), max(e["end_s"] for e in placed)
    if first >= min_s:
        entries.insert(0, row("(lead-in)", 0.0, first))
    if duration - last >= min_s:
        entries.append(row("(tail)", last, duration))


def _place_instrumentals(entries, duration):
    """Give sections without lyrics the space between their located neighbours (split evenly), marked inferred."""
    i = 0
    while i < len(entries):
        if entries[i]["status"] != "instrumental":
            i += 1
            continue
        j = i
        while j < len(entries) and entries[j]["status"] == "instrumental":
            j += 1
        before = next((e["end_s"] for e in reversed(entries[:i]) if e["end_s"] is not None), 0.0)
        after = next((e["start_s"] for e in entries[j:] if e["start_s"] is not None), duration)
        if after > before:
            step = (after - before) / (j - i)
            for k in range(i, j):
                entries[k]["start_s"] = round(before + (k - i) * step, 2)
                entries[k]["end_s"] = round(before + (k - i + 1) * step, 2)
                entries[k]["status"] = "instrumental (inferred)"
        i = j


# ---------------------------------------------------------------- vocal activity

def blocks_from_activity(active, frame_s=FRAME_S, bridge_frames=3, min_s=2.0):
    """[(start_s, end_s)] runs of active frames, bridging gaps up to bridge_frames, dropping runs under min_s."""
    blocks, i, n = [], 0, len(active)
    while i < n:
        if not active[i]:
            i += 1
            continue
        j = i
        while j < n and (active[j] or any(active[j + 1:j + 1 + bridge_frames])):
            j += 1
        if (j - i) * frame_s >= min_s:
            blocks.append((round(i * frame_s, 1), round(j * frame_s, 1)))
        i = j
    return blocks


def label_outside(heard, all_lines):
    """For vocals outside the lyric sections: the lyric line they repeat (whole or in part), else None."""
    tokens = [t for t in tokenize(heard) if t not in FILLERS]
    if len(tokens) < 2:
        return None
    kind, line = _classify_added(tokens, all_lines)
    return {"kind": kind, "line": line} if line else None


def outside_spans(blocks, spans, min_s=3.0):
    """Parts of the sung blocks not covered by any section span, at least min_s long."""
    spans = sorted((a, b) for a, b in spans if a is not None and b is not None)
    left = []
    for a, b in blocks:
        cur = a
        for s, e in spans:
            if e <= cur or s >= b:
                continue
            if s > cur:
                left.append((cur, min(s, b)))
            cur = max(cur, e)
        if cur < b:
            left.append((cur, b))
    return [(round(a, 1), round(b, 1)) for a, b in left if b - a >= min_s]


# ---------------------------------------------------------------- audio

def key_of(chroma_mean):
    import numpy as np

    best, name = -2.0, None
    for i in range(12):
        rolled = np.roll(chroma_mean, -i)
        for profile, mode in ((MAJOR_PROFILE, "major"), (MINOR_PROFILE, "minor")):
            c = float(np.corrcoef(rolled, profile)[0, 1])
            if c > best:
                best, name = c, f"{PITCH_CLASSES[i]} {mode}"
    return name, round(best, 3)


def resolve_device(requested):
    import torch

    if requested != "auto":
        return requested
    return "cuda" if torch.cuda.is_available() else "cpu"


def separate(model, wav, device, shifts=1, seed=0):
    """Demucs stems, averaged over `shifts` seeded time-shifts (the same stems every run for a given seed)."""
    import random

    import torch
    from demucs.apply import apply_model

    random.seed(seed)
    torch.manual_seed(seed)
    mix = torch.tensor(wav, dtype=torch.float32)
    ref = mix.mean(0)
    mean, std = ref.mean(), ref.std() + 1e-8
    with torch.no_grad():
        stems = apply_model(model, ((mix - mean) / std)[None], shifts=shifts, split=True, overlap=0.25,
                            progress=False, device=device)[0]
    stems = (stems * std + mean).cpu().numpy()
    return dict(zip(model.sources, stems))


def _same_words(a, b):
    return [(w["word"], round(w["start"], 2)) for w in a] == [(w["word"], round(w["start"], 2)) for w in b]


def transcribe_passes(vocal_16k, model_name, device, language, passes=WHISPER_PASSES, seed=0):
    """Word-timestamped transcripts of the vocal stem -> (distinct transcripts, device used, passes run).

    Whisper keeps its fallback retries (higher-temperature re-decodes of passages
    it can't read at first); each pass seeds them differently, so the passes can
    disagree exactly where the audio is hard. When a pass matches the one before
    it, nothing is left to disagree about and the rest are skipped.
    """
    import ctranslate2
    from faster_whisper import WhisperModel

    attempts = [("cuda", "float16"), ("cpu", "int8")] if device == "cuda" else [("cpu", "int8")]
    last_exc = None
    for dev, compute in attempts:
        try:
            model = WhisperModel(model_name, device=dev, compute_type=compute)
            runs, done = [], 0
            for p in range(max(1, passes)):
                ctranslate2.set_random_seed(seed + p)
                segments, _ = model.transcribe(vocal_16k, word_timestamps=True, vad_filter=False, beam_size=5,
                                               condition_on_previous_text=False, language=language)
                words = [{"word": w.word, "start": float(w.start), "end": float(w.end),
                          "probability": round(float(w.probability), 3)}
                         for seg in segments for w in (seg.words or [])]
                done += 1
                if runs and _same_words(words, runs[-1]):
                    break
                runs.append(words)
            return runs, dev, done
        except Exception as exc:  # CUDA 12 libraries missing, etc.
            last_exc = exc
            print(f"  NOTE: Whisper on {dev} failed ({type(exc).__name__}); trying the next device.", file=sys.stderr)
    raise RuntimeError(f"Whisper could not run: {last_exc}")


def beat_times_for(path, y_mono_22k, source):
    """(beat times, overall BPM, source used)."""
    import librosa
    import numpy as np

    if source == "beat-this":
        readings = beat_this_readings([path], include_beats=True)
        reading = readings[0] if readings else None
        if usable(reading) and reading.get("beats_s"):
            return np.array(reading["beats_s"]), float(reading["bpm"]), "beat-this"
    tempo, beats = librosa.beat.beat_track(y=y_mono_22k, sr=22050)
    return librosa.frames_to_time(beats, sr=22050), float(np.atleast_1d(tempo)[0]), "librosa"


def measure_sections(entries, y, stems, sr, meter, chroma, beat_times, overall_bpm):
    """Add mix/vocal loudness, step, tempo/feel and key to every placed section."""
    import numpy as np

    from loudness import integrated

    vocals = stems["vocals"]
    band = sum(v for k, v in stems.items() if k != "vocals")
    prev_lufs = None
    for e in entries:
        for k in ("mix_lufs", "step_lu", "vocal_minus_band_lu", "vocal_present", "bpm", "feel", "key",
                  "key_confidence"):
            e.setdefault(k, None)
        if e["start_s"] is None or e["end_s"] is None or e["end_s"] - e["start_s"] < 1.0:
            continue
        a, b = int(e["start_s"] * sr), int(e["end_s"] * sr)
        mix = integrated(meter, y[:, a:b].T)
        voc, bnd = integrated(meter, vocals[:, a:b].T), integrated(meter, band[:, a:b].T)
        e["mix_lufs"] = mix
        e["step_lu"] = None if mix is None or prev_lufs is None else round(mix - prev_lufs, 1)
        prev_lufs = mix if mix is not None else prev_lufs
        if voc is not None and bnd is not None:
            e["vocal_minus_band_lu"] = round(voc - bnd, 1)
            e["vocal_present"] = e["vocal_minus_band_lu"] > VOCAL_ABSENT_LU
        else:
            e["vocal_present"] = False
        inside = beat_times[(beat_times >= e["start_s"]) & (beat_times < e["end_s"])]
        if len(inside) >= 5:
            bpm = 60.0 / float(np.median(np.diff(inside)))
            e["bpm"] = round(bpm, 1)
            ratio = bpm / overall_bpm if overall_bpm else 1.0
            e["feel"] = feel_name(ratio) if abs(ratio - 1) >= SHIFT_THRESHOLD else None
        fa, fb = int(e["start_s"] * 22050 / 512), int(e["end_s"] * 22050 / 512)
        if fb - fa >= 10:
            e["key"], e["key_confidence"] = key_of(chroma[:, fa:fb].mean(axis=1))


def vocal_blocks(stems, sr):
    """Where the vocal stem is actually singing (0.5 s frames), as (start_s, end_s) runs."""
    import numpy as np

    vocals = stems["vocals"].mean(0)
    band = sum(v for k, v in stems.items() if k != "vocals").mean(0)
    hop = int(FRAME_S * sr)
    n = len(vocals) // hop
    if n == 0:
        return []
    power = lambda x: (x[: n * hop].reshape(n, hop) ** 2).mean(1)  # noqa: E731
    vdb = 10 * np.log10(np.maximum(power(vocals), 1e-12))
    bdb = 10 * np.log10(np.maximum(power(band), 1e-12))
    active = (vdb > vdb.max() - 25) & (vdb - bdb > -18)
    return blocks_from_activity(list(map(bool, active)))


# ---------------------------------------------------------------- output

def _t(s):
    return "-" if s is None else f"{int(s // 60)}:{int(s % 60):02d}"


def _v(v, fmt="{:+.1f}"):
    return "-" if v is None else fmt.format(v)


def format_text(m):
    lines = [
        f"# Section map: {m['file']}",
        f"Lyrics: {m['lyrics_source']} | Whisper {m['whisper_model']} ({m['whisper_device']}, "
        f"{m.get('whisper_passes_run', 1)} pass(es), {m.get('whisper_distinct_transcripts', 1)} distinct) | "
        f"Demucs x{m.get('demucs_shifts', 1)} | "
        f"Tempo: {SOURCE_LABELS.get(m['tempo_source'], m['tempo_source'])} {m['overall_bpm']} BPM",
        "",
        f"{'Section':<34} {'Time':<11} {'Status':<24} {'Cov':>4} {'LUFS':>6} {'Step':>5} {'Voc-band':>8} "
        f"{'BPM':>6} {'Feel':<12} Key",
        "-" * 132,
    ]
    for e in m["sections"]:
        span = f"{_t(e['start_s'])}-{_t(e['end_s'])}" if e["start_s"] is not None else "-"
        cov = "-" if e["coverage"] is None else f"{e['coverage']:.0%}"
        vocal = _v(e.get("vocal_minus_band_lu")) + ("" if e.get("vocal_present") in (None, True) else "*")
        key = e.get("key") or "-"
        lines.append(
            f"{e['tag'][:34]:<34} {span:<11} {e['status']:<24} {cov:>4} {_v(e.get('mix_lufs'), '{:.1f}'):>6} "
            f"{_v(e.get('step_lu')):>5} {vocal:>8} {_v(e.get('bpm'), '{:.1f}'):>6} {(e.get('feel') or ''):<12} {key}"
        )
    lines.append("")
    lines.append("* = no real vocal in that section. Instrumental times are inferred from the sung sections around them; "
                 "(lead-in) and (tail) are stretches nobody tagged.")
    unheard = [(e["tag"], l) for e in m["sections"] for l in e["lines_not_heard"]]
    if unheard:
        lines.append("")
        lines.append("Lyric lines not heard (dropped, changed, or just mis-transcribed: listen before concluding):")
        lines.extend(f"  [{tag}] {line}" for tag, line in unheard)
    def added_line(tag, a):
        partial = "  (partial repeat)" if a["kind"] == "partial repeat" else ""
        partial += f"  in place of \"{a['replaces']}\"" if a.get("replaces") else ""
        partial += f"  p={a['probability']}" if a.get("probability") is not None else ""
        return (f"  [{tag}] {_t(a['start_s'])}  \"{a['text']}\"  {a['position']}, after \"{a['after_line']}\""
                f"{partial}  ({a['passes']} passes)")

    added = [(e["tag"], a) for e in m["sections"] for a in e.get("added_words", [])]
    if added:
        lines.append("")
        lines.append("Words added to the lyrics (a set line changed or padded; listen, this can rule out a take):")
        lines.extend(added_line(tag, a) for tag, a in added)
    repeats = [(e["tag"], a) for e in m["sections"] for a in e.get("repeats", [])]
    if repeats:
        lines.append("")
        lines.append("Whole-line repeats (often fine; judge by ear):")
        lines.extend(f"  [{tag}] {_t(a['start_s'])}  \"{a['text']}\"  repeats \"{a['repeat_of']}\"  ({a['passes']} passes)"
                     for tag, a in repeats)
    possible = [(e["tag"], a) for e in m["sections"] for a in e.get("added_words_possible", [])]
    if possible:
        lines.append("")
        lines.append("Possible added words (only some passes heard them; may be a transcription artifact):")
        lines.extend(added_line(tag, a) for tag, a in possible)
    if m["vocals_outside_sections"]:
        lines.append("")
        lines.append("Vocals outside the lyric sections (ad-libs, repeats, invented lines, wordless fills):")
        for v in m["vocals_outside_sections"]:
            low = v.get("mean_probability") is not None and v["mean_probability"] < LOW_CONFIDENCE
            rpt = v.get("repeats")
            note = (f"  (repeats lyric \"{rpt['line']}\"" + (", in part" if rpt["kind"] == "partial repeat" else "")
                    + ")") if rpt else ""
            lines.append(f"  {_t(v['start_s'])}-{_t(v['end_s'])}  {v['heard'] or '(wordless: vocalizing, scat, or a held vowel)'}"
                         + note + ("  (low confidence: may be a transcription artifact)" if low else ""))
    return "\n".join(lines)


def build_json(metrics):
    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "metrics": metrics,
        "findings": [],
        "summary": {"total": 0},
    }


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(
        description="Map a render's sections against its lyrics: timing, vocal placement, loudness, tempo, key.",
    )
    parser.add_argument("audio", help="The render (audio file)")
    parser.add_argument("--lyrics", required=True,
                        help="Lyrics file: plain text, or a Markdown package/songbook doc (the fenced block with "
                             "the most section tags is used)")
    parser.add_argument("--lyrics-block", type=int, default=None,
                        help="Use the Nth fenced block that carries section tags (1-based) instead of the richest")
    parser.add_argument("--device", default="auto", help="Torch device for Demucs: auto, cpu, cuda, cuda:1 ...")
    parser.add_argument("--whisper-model", default=WHISPER_MODEL,
                        help=f"faster-whisper model: tiny, base, small, medium, large-v3 ... (default: {WHISPER_MODEL})")
    parser.add_argument("--whisper-device", choices=["cpu", "cuda"], default="cpu",
                        help="Whisper device (default: cpu; cuda needs CUDA 12 cuBLAS/cuDNN and falls back to cpu)")
    parser.add_argument("--language", default=None, help="Lyric language code (e.g. en). Default: auto-detect")
    parser.add_argument("--passes", type=int, default=WHISPER_PASSES,
                        help=f"Whisper passes to take a consensus over (default: {WHISPER_PASSES}; stops early when "
                             "two passes agree)")
    parser.add_argument("--shifts", type=int, default=None,
                        help=f"Demucs time-shifts to average (default: {GPU_SHIFTS} on a GPU, 1 on CPU)")
    parser.add_argument("--include-words", action="store_true",
                        help="Keep every pass's word timings in the JSON (word_passes) for a closer look")
    parser.add_argument("--seed", type=int, default=0,
                        help="Seed for the Demucs shifts and Whisper retries; the same seed gives the same map")
    add_tempo_source_arg(parser)
    parser.add_argument("--format", choices=["json", "text"], default="json", dest="output_format",
                        help="Output format (default: json)")
    parser.add_argument("-o", "--output", default=None, help="Output file path (default: stdout)")
    parser.add_argument("--archive", nargs="?", const="", default="",
                        help=("Persist the JSON to the analysis archive. With no path: "
                              "docs/audio-analysis/songs/[{band-slug}/]{song}-section-map.json. Default: ON."))
    parser.add_argument("--no-archive", dest="archive", action="store_const", const=None,
                        help="Skip writing the JSON archive.")
    args = parser.parse_args()

    def fail(msg):
        print(json.dumps({"script": SCRIPT_NAME, "status": "fail", "error": msg}), file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(args.audio):
        fail(f"Audio file not found: {args.audio}")
    if not os.path.isfile(args.lyrics):
        fail(f"Lyrics file not found: {args.lyrics}")
    try:
        lyric_text = extract_lyrics(Path(args.lyrics).read_text(encoding="utf-8"), args.lyrics_block)
    except ValueError as exc:
        fail(str(exc))
    sections, song_modifiers = parse_sections(lyric_text)
    if not any(s["name"] != "(untagged)" for s in sections):
        fail(f"No section tags ([Verse 1], [Chorus] ...) found in {args.lyrics}")

    require_modules(["torch", "demucs", "faster_whisper", "librosa", "numpy", "pyloudnorm"], INSTALL_CMD,
                    "Section map")
    import librosa
    import numpy as np
    import pyloudnorm as pyln
    from demucs.pretrained import get_model

    device = resolve_device(args.device)
    try:
        model = get_model(DEMUCS_MODEL)
        model.to(device).eval()
    except Exception as exc:
        fail(f"Could not load Demucs {DEMUCS_MODEL} on {device}: {exc}")
    sr = model.samplerate

    shifts = args.shifts if args.shifts is not None else (GPU_SHIFTS if str(device).startswith("cuda") else 1)
    print(f"  separating stems (Demucs, {shifts} averaged shift(s))...", file=sys.stderr, flush=True)
    y, _ = librosa.load(args.audio, sr=sr, mono=False)
    if y.ndim == 1:
        y = np.stack([y, y])
    y = y[: model.audio_channels]
    stems = separate(model, y, device, shifts, args.seed)
    duration = y.shape[1] / sr

    print(f"  transcribing the vocal stem (Whisper {args.whisper_model}, up to {args.passes} passes)...",
          file=sys.stderr, flush=True)
    vocal_16k = librosa.resample(stems["vocals"].mean(0), orig_sr=sr, target_sr=16000).astype(np.float32)
    try:
        runs, whisper_device, passes_run = transcribe_passes(vocal_16k, args.whisper_model, args.whisper_device,
                                                             args.language, args.passes, args.seed)
    except RuntimeError as exc:
        fail(str(exc))

    print("  aligning the transcript to the lyrics...", file=sys.stderr, flush=True)
    words = runs[0]
    entries = locate_consensus(sections, runs, duration)

    mono_22k = librosa.resample(y.mean(0), orig_sr=sr, target_sr=22050)
    beat_times, overall_bpm, tempo_used = beat_times_for(args.audio, mono_22k, resolve_tempo_source(args.tempo_source))
    chroma = librosa.feature.chroma_cqt(y=mono_22k, sr=22050)
    measure_sections(entries, y, stems, sr, pyln.Meter(sr), chroma, beat_times, overall_bpm)

    blocks = vocal_blocks(stems, sr)
    outside = []
    # A stretch counts as inside a section if any pass placed that section there.
    covered = [(e["start_s"], e["end_s"]) for e in entries if e["status"] in ("sung", "partly sung")]
    covered += [tuple(span) for e in entries for span in e.get("pass_spans", [])]
    for a, b in outside_spans(blocks, covered):
        inside = [w for w in words if a <= w["start"] < b]
        heard = " ".join(w["word"].strip() for w in inside)
        outside.append({"start_s": a, "end_s": b, "heard": heard,
                        "mean_probability": round(statistics.mean(w["probability"] for w in inside), 2)
                        if inside else None,
                        "repeats": label_outside(heard, [l for sec in sections for l in sec["lines"]])})

    metrics = {
        "file": os.path.basename(args.audio),
        "lyrics_source": os.path.basename(args.lyrics),
        "duration_s": round(duration, 1),
        "demucs_device": device,
        "whisper_model": args.whisper_model,
        "whisper_device": whisper_device,
        "whisper_passes_run": passes_run,
        "whisper_distinct_transcripts": len(runs),
        "demucs_shifts": shifts,
        "seed": args.seed,
        "tempo_source": tempo_used,
        "overall_bpm": round(overall_bpm, 1),
        "song_modifiers": song_modifiers,
        "sections": entries,
        "sung_blocks": [{"start_s": a, "end_s": b} for a, b in blocks],
        "vocals_outside_sections": outside,
        "counts": {
            status: sum(1 for e in entries if e["status"] == status)
            for status in ("sung", "partly sung", "not heard", "instrumental (inferred)", "instrumental", "untagged")
        },
        "transcript": " ".join(w["word"].strip() for w in words),
    }
    if args.include_words:
        metrics["word_passes"] = runs
    json_data = build_json(metrics)
    output = format_text(metrics) if args.output_format == "text" else json.dumps(json_data, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n")
    else:
        print(output)

    category, identifier = input_archive_identifier(args.audio, SCRIPT_NAME)
    target = resolve_archive_arg(category, identifier, args.archive)
    if target is not None:
        res = write_archive(target, json_data)
        print(f"  ARCHIVED: {res['path']} ({res['bytes_written']} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
