# Audio Analysis Scripts

Objective measurements to set beside the user's ear. The ear still decides: every number here is evidence, not a verdict. Run each script as `uv run {skill-root}/scripts/<name>.py`; `--help` lists its flags, output fields and archive paths. A script that can't provision its dependencies returns JSON with install instructions and exits 2; the feedback workflow runs fully without any of them.

## Analyze Audio route (measure only)

Numbers for a render, no triage and no recommendations. Run `analyze-audio.py <render>` (a folder works for a catalog run) for tempo, key, duration and loudness. When `{pytorch_audio_tools}` is `on` and you have the lyrics the render came from, also run `section-map.py <render> --lyrics <file>`. Run the other scripts only when the question needs them. With the tools off or a dependency missing, say what the reading would have added and carry on.

A non-zero exit is a failed measurement, not a reading: give its reason and no numbers. **Interactive:** present the numbers with the reading notes below that apply (a halftime ambiguity, low key confidence) and let the ear decide; if the user then wants changes, start the feedback steps. **Headless:** return the audio-mode JSON from the headless contract.

## Which script for what

**librosa (light):**
- `analyze-audio.py` — BPM, key, duration and BS.1770 loudness (integrated LUFS, loudness range) for one render or every track in a folder. Exits 1 and writes nothing when no file could be measured.
- `audio-deep-analysis.py` — one track in depth: energy arc, chords over time, section boundaries, spectral balance.
- `tempo-detail.py` — tempo over time with stability and beat regularity; on Beat This! beats it reports 15-second window medians, so one stray beat doesn't read as a tempo change.
- `chord-progression.py` — beat-synchronized chords with Camelot codes. Bar-by-bar chords are noisy under distorted guitars; the 30-second key-centre summaries hold up.

**PyTorch (opt-in, heavy):** the first `uv run` provisions 1–3 GB plus model weights, and uses a CUDA GPU when present.
- `beat-grid.py` — Beat This! beats and downbeats: BPM, entry and exit BPM (first and last 30 s), beats per bar, and how librosa's BPM relates to it (agree / double / half / triplet grid).
- `vocal-placement.py` — vocal-stem loudness minus the rest of the mix (LU), overall and by thirds; thirds with no real vocal are flagged. It describes placement rather than grading it — most useful for comparing renders of one song, or one voice across models.
- `section-map.py` — lines a render up with its lyrics so each tagged section gets a real start and end even where Suno runs sections together. Per section: loudness and the step from the section before, vocal-minus-band, tempo and feel, key. `--lyrics` takes a plain lyrics file or a package or songbook doc. The first run downloads the Whisper model (~1.5 GB).

**What gets written:** `analyze-audio.py` and `audio-deep-analysis.py` archive their JSON under `docs/audio-analysis/` (a single render to its per-song archive, a folder to the dated catalog archive); a folder run of `analyze-audio.py` also refreshes the catalog's markdown companion (AUTOGEN markers keep hand-written sections). The PyTorch scripts archive their JSON. `--no-archive` / `--no-companion` skip those writes.

`audio-files-manifest.py` and `verify-audio-files.py` are multi-machine housekeeping (has every audio file arrived on this machine?), not feedback tools.

## Reading the section map

Run `section-map.py <render> --lyrics <file> --format text` before judging structure, dynamics or vocal placement, and compare each section's timing, loudness step, vocal-minus-band, tempo and feel, and key against the tags and cues that were asked for rather than assuming the render followed them.
- Transcribing sung vocals is imperfect: a line reported **not heard** means listen there, not proof the line changed.
- **Added words** matter: v6 sometimes pads a set line, which can rule out a take. A run that looks like a riff on a lyric line carries a `looks_like_riff_of` hint instead of being filed as a repeat — the ear decides which it is.
- **Whole-line repeats** are listed separately because they're often fine.
- Vocals outside the lyric sections, and untagged lead-ins and tails, get their own rows.

## Tempo source

With the PyTorch audio tools on (`pytorch_audio_tools`), `analyze-audio.py`, `tempo-detail.py` and `chord-progression.py` take tempo and beats from Beat This! instead of librosa, and `chord-progression.py` then reads chords per real bar. If Beat This! can't run they fall back to librosa with a note; every report names its `tempo_source`. `--tempo-source auto|beat-this|librosa` overrides the switch for one run.

When Beat This! and librosa differ by a clean ratio, the ear decides which pulse is felt; neither number settles it alone. Beats per bar reads how the pulse groups, not the notated meter: a 6/8 *feel* typically reads 4.

## Reading tempo and key

- **Felt BPM** — the tempo a listener perceives — is what matters for feedback; compare "it feels too fast" against the felt tempo, not the raw number.
- **librosa misreads by genre, both ways** (about one track in five in production testing): speed metal reads half-time (99 for a felt ~198); doom and sludge read double (144 for a felt ~72); power ballads and heartbeat-pulse tracks overcount (96 for a felt ~68, or a tagged 60). Slow contemplative songs (felt 70–80) consistently read 150–160. Apply the genre-aware correction before acting on a number; librosa is deterministic, so the same file always gives the same reading.
- **The slow-prior reading.** librosa starts its search at 120 BPM, the main reason slow songs read double, so the scripts take a second reading starting at 80 (`bpm_librosa_slow_prior`, or `librosa_bpm_slow_prior` in beat-grid.py; `Slow80` / `lib@80` in tables) and report how they relate (`librosa_prior_relation`: `agree`, `double`, `other`). Neither reading wins every song, so the default stays the headline. A **`double`** (e.g. 117.5 against 60.1) means librosa is torn between two pulses — a likely halftime ambiguity: ask which one the song moves at, or check Beat This! or a hi-hat count.
- **Beat This!** is the better second opinion and fixes most slow-song double reads, but still reads slow doom and ballad feels double, so a clean-ratio disagreement goes to the ear.
- **A big stated-vs-measured miss, once a double read is ruled out, is a listening cue:** listen for an instrument whose job was dropped, and mention it when you find one. In one outside series every off-tempo take had also dropped a requested instrument (ANECDOTAL-controlled, one song). A cue, not a verdict.
- **Hi-hat count** is the cheap reliable check when sources disagree: count hi-hat hits in 10 seconds of a steady groove; for straight eighths, `(hits ÷ 2) × 6` = quarter-note BPM (25 hits → 75 BPM).
- Key confidence below 0.5 is low reliability. Enharmonics: D# = Eb, C# = Db, A# = Bb, F# = Gb.
