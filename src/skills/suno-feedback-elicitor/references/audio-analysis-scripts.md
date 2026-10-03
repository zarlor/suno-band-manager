# Audio Analysis Scripts

Objective measurements to set beside the user's ear. The ear still decides: every number here is evidence, not a verdict. Run each script with `uv run scripts/<name>.py` — `uv` provisions its dependencies from the script's PEP 723 header. Run `--help` for flags, output fields and archive paths. If the dependencies can't be provisioned, a script returns JSON with install instructions (exit code 2); the feedback workflow runs fully without any of them.

## Which script for what

**librosa (light):**
- `analyze-audio.py` — BPM, key, duration and BS.1770 loudness (integrated LUFS, loudness range) for every track in a folder.
- `audio-deep-analysis.py` — one track in depth: energy arc, chords over time, section boundaries, spectral balance.
- `tempo-detail.py` — tempo over time with stability and beat regularity. On Beat This! beats it reports 15-second window medians, so one stray beat doesn't read as a tempo change.
- `chord-progression.py` — beat-synchronized chords with Camelot codes. Bar-by-bar chords are noisy under distorted guitars; the 30-second key-centre summaries hold up.

**PyTorch (opt-in, heavy):** the first `uv run` provisions 1-3 GB plus model weights, and uses a CUDA GPU when present.
- `beat-grid.py` — Beat This! beats and downbeats: BPM, entry and exit BPM (first and last 30 s), beats per bar, and how librosa's BPM relates to it (agree / double / half / triplet grid).
- `vocal-placement.py` — vocal-stem loudness minus the rest of the mix (LU), overall and by thirds; thirds with no real vocal are flagged. It describes placement rather than grading it — most useful for comparing renders of one song, or one voice across models.
- `section-map.py` — lines a render up with the lyrics it was generated from, so each tagged section gets a real start and end even where Suno runs sections together. Per section: loudness and the step from the section before, vocal-minus-band, tempo and feel, and key. `--lyrics` takes a plain lyrics file or a package/songbook doc. About a minute per song; the first run downloads the Whisper model (~1.5 GB).

**What gets written:** `analyze-audio.py` and `audio-deep-analysis.py` write a JSON archive under `docs/audio-analysis/` and refresh the song's markdown companion doc (AUTOGEN markers keep hand-written sections); the PyTorch scripts archive their JSON. `--no-archive` / `--no-companion` skip those writes.

`audio-files-manifest.py` and `verify-audio-files.py` are multi-machine housekeeping (has every audio file arrived on this machine?), not feedback tools; no workflow step needs them.

## Section map

When the PyTorch audio tools are on and you have the render and the lyrics it came from, run `section-map.py <render> --lyrics <file> --format text` before judging structure, dynamics or vocal placement. Compare each section's timing, loudness step, vocal-minus-band, tempo/feel and key against the tags and cues that were asked for, rather than assuming the render followed them. With the tools off, say what the map would add and carry on without it.

Read it with these limits in mind:
- Transcribing sung vocals is imperfect. A line reported as **not heard** means listen there — not proof the line changed.
- **Added words** matter: v6 sometimes pads a set line, which can rule out a take. A run that looks like a riff on a lyric line carries a `looks_like_riff_of` hint instead of being filed as a repeat — the ear decides which it is.
- **Whole-line repeats** are listed separately because they're often fine.
- Vocals outside the lyric sections, and untagged lead-ins and tails, get their own rows.

## Tempo source

When the PyTorch audio tools are on (`pytorch_audio_tools` in the module config), `analyze-audio.py`, `tempo-detail.py` and `chord-progression.py` take tempo and beats from Beat This! instead of librosa — and `chord-progression.py` then reads chords per real bar. Off, they use librosa. If Beat This! can't run they fall back to librosa with a note, and every report names its source (`tempo_source`). `--tempo-source auto|beat-this|librosa` overrides the switch for one run.

When Beat This! and librosa differ by a clean ratio, the ear decides which pulse is felt — neither number settles it alone. Beats per bar reads how the pulse groups, not the notated meter: a 6/8 *feel* typically reads 4.

## Reading librosa numbers

- **BPM misreads are genre-dependent and go both directions:**
  - Speed metal → reads **half-time** (e.g., reports 99 BPM when felt tempo is ~198 — reads snare on beat 3 as beat 1)
  - Doom/sludge → reads **double-time** (e.g., reports 144 BPM when felt tempo is ~72 — counts subdivisions as pulse)
  - Power ballads → overcounts (e.g., reports 96 BPM when felt is ~68)
  - Heartbeat/pulse tracks → overcounts (e.g., reports 96 when tagged 60)
- **~19% of tracks have significant BPM misreads** in production testing (31-track catalog). Always verify against genre/feel.
- **"Felt BPM"** — the human-perceived tempo vs. librosa's measurement. When a user says "it feels too fast/slow," compare their perception against felt BPM, not librosa BPM. Felt BPM is what matters for playlist sequencing and feedback triage.
- **LLM BPM estimates also diverge** — Gemini AI Studio, Gemini web, and ChatGPT produce different values for the same track. No single source is reliable for BPM; cross-reference at least two.
- Key confidence below 0.5 is low reliability
- Enharmonic equivalents: D# = Eb, C# = Db, A# = Bb, F# = Gb
- librosa is deterministic — same file always produces the same results. Use as ground truth for BPM/key baseline, but always apply genre-aware correction before acting on the number.
- **Slow contemplative songs (felt tempo 70-80 BPM) trigger halftime detection consistently.** librosa raw values around 150-160 BPM with felt tempo around 75-80 BPM is a well-documented pattern. When librosa reports 152 BPM on a song that "feels" much slower than that, the felt tempo is likely half (76). Cross-verify with hi-hat counting before trusting either value.
- **The slow-prior reading.** librosa starts its tempo search at 120 BPM, and that pull is the main cause of slow songs reading double. So the scripts take a second librosa reading that starts at 80 BPM (`bpm_librosa_slow_prior`, or `librosa_bpm_slow_prior` in beat-grid.py; `Slow80` / `lib@80` in tables) and say how the two relate (`librosa_prior_relation`: `agree`, `double`, or `other`). On a 34-track reference catalog with ear-verified tempos, the default read 10 on the felt tempo and 14 double; the 80 start read 17 on it and 1 double, but halved 4 fast songs. Neither reading wins every song, so the default stays the headline number. A **`double`** (default about 2x the slow reading, e.g. 117.5 vs 60.1) means librosa itself is torn between two pulses: a likely halftime ambiguity. Ask which one the song moves at, or check Beat This! or a hi-hat count. The felt-BPM corrections stay authoritative.
- **Second opinion: `beat-grid.py` (Beat This!).** On an 83-track reference catalog, Beat This! matched the human-verified felt BPM on 9 of 15 tracks, against librosa's 7, and fixed most slow-song halftime double-reads. It still reads slow doom and ballad feels double, so a clean-ratio disagreement goes to the ear (or the hi-hat count below).
- **A big stated-vs-measured miss, after the double-read check, is a listening cue** (2026-10-03 sweep). Once a halftime ambiguity is ruled out, a render far off its stated tempo is worth a closer listen for an instrument whose job was dropped. In one outside series of 24 takes, every off-tempo take had also missed a requested instrument (ANECDOTAL-controlled, one song). Mention it when you find it. It's a cue, not a verdict.
- **Manual hi-hat counting is the cheap reliable BPM verification** when AI tools disagree. Count hi-hat hits in a 10-second window of a steady-groove section. Most rock/pop songs play hi-hats as straight eighth notes. Calculation: `(hat hits in 10 sec ÷ 2) × 6 = quarter-note BPM`. Example: 25 hi-hat hits in 10 sec → (25 ÷ 2) × 6 = 75 BPM. When sources contest the BPM, this 30-second manual check is the tiebreaker.
