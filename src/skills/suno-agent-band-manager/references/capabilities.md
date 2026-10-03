# Mac — Capabilities

## Creed Shards

The heavy creed disciplines live in sanctum shards loaded on demand. Which shard loads when is mapped in the sanctum's always-loaded `CREED.md` (its shard map); the full loaded / on-demand / not-loaded picture is in the sanctum's `INDEX.md`. Load the shard from the sanctum, never the skill's authored `references/creed.md` (seed source, not loaded on waking).

## External Skills

This agent orchestrates the following registered skills:

- `suno-band-profile-manager` — Band profile CRUD, writer voice analysis, the per-band playlist YAML
- `suno-style-prompt-builder` — Model-aware style prompt generation. **Expected return:** its headless success JSON (`references/headless-contract.md` in that skill). No commentary.
- `suno-lyric-transformer` — Poem/text to Suno-ready lyrics. **Expected return:** its Transform Return (`references/headless-contract.md` in that skill) — structured lyrics with metatags, the writer's spacing intact. No commentary.
- `suno-feedback-elicitor` — Diagnoses a take into structured adjustment recommendations (style prompt deltas, lyric changes, slider adjustments, model suggestions). Mac calls it inside Refine Song (RS), which then rebuilds the package; it isn't a separate item on Mac's menu, though the skill still runs standalone. It also owns the audio analysis scripts.
- `suno-playlist-sequencer` — Album/playlist/tracklist sequencing (energy arcs, key transitions, locked arcs, encore design). **Expected return:** A recommended sequence with per-move rationale, locked arcs respected, and honest trade-offs.

When invoking these skills, pass relevant context (band profile data, model selection, creativity mode, user direction) so the skill doesn't re-ask for information the user already provided.

**Creative riff (Studio/Jam only):** During direction-gathering, Mac is a producer — not just a listener. Offer one proactive creative suggestion per song: an unexpected genre fusion, an instrumentation choice, a structural twist. Frame it as an idea, not a directive.

**Access note:** Band profile writes happen through `suno-band-profile-manager`, not directly by Mac. Mac's access boundaries restrict direct writes to the sidecar memory only.

## Skill Availability

If the style or lyric skill is missing when a package is needed, say which one plainly and don't present a Suno package — the Package Assembly Rule has no inline fallback. Direction-gathering and drafting can carry on until it's back. For any other missing skill, say what's unavailable and offer what Mac can do without it; never fabricate a skill's output.

## Catalog Scripts (this skill)

Run these instead of reading and comparing catalog files by hand (`uv run scripts/<name>.py --help` for flags):

- `validate-sidecar.py` — MEMORY.md derived sections vs the songbook, playlist-vs-songbook title sets, voice-file catalog counts, Pending / Parked Work vs WIP markers, Companion Files table vs disk (`--since DATE` adds files the table doesn't list), broken `docs/` cross-references
- `find-stale-refs.py` — every reference to an old value across the catalog docs and sanctum, with match kind and a replacement preview
- `songbook-catalog.py` — per-song extract (status, dates, model, settings, style prompt) with per-band tallies, for browsing and lookup
- `scan-wip-status.py` — WIP COMPLETED markers, correlated to published songs by `source_wip` then title
- `genre-coverage.py` — the per-band coverage index (extracted fields and verbatim style prompts); `--check` says whether it's stale

## Audio Analysis (optional — `librosa`, `numpy`, `pyloudnorm`, auto-provisioned by `uv run`)

The Feedback Elicitor's scripts measure BPM, key, loudness, energy arcs, section boundaries, chord progressions and playlist seam readings (key move, tempo change, loudness step) from audio files. Its `references/audio-analysis-scripts.md` covers which script does what and how to read the numbers.

**When to offer:** when a downloaded file is at hand — the user provides one, asks about tempo/key/energy, or wants playlist analysis. Downloads are capped, so analyse files the owner already has; before asking for a new download, say it uses one of the cycle's downloads (the count is in `MEMORY.md`'s Downloads section). After a publish, the order is create-song Step 7.

**How to check:** run any audio script — if dependencies are missing, it returns structured JSON with install instructions (exit code 2).

**Available scripts** (in the Feedback Elicitor's scripts directory):
- `analyze-audio.py` — Batch BPM/key/duration/loudness (LUFS, LRA) for a directory
- `audio-deep-analysis.py` — Deep single-track analysis
- `chord-progression.py` — Beat-synchronized chord detection
- `tempo-detail.py` — Detailed tempo stability analysis
- `beat-grid.py` — *Optional, PyTorch:* Beat This! beats/downbeats. With the PyTorch audio tools turned on in `/suno-setup`, every script above takes its tempo from it; otherwise it's a second opinion on librosa's halftime reads
- `vocal-placement.py` — *Optional, PyTorch:* Demucs vocal-vs-band loudness, overall and by thirds
- `section-map.py` — *Optional, PyTorch:* a render lined up with its lyrics (Demucs vocal stem + Whisper word timestamps): when each tagged section lands, with per-section loudness step, vocal-minus-band, tempo/feel and key, plus lyric lines not heard. With the PyTorch audio tools on, run it on a downloaded render with its package lyrics before judging structure or dynamics

**For playlist/album/tracklist work:** route to the `suno-playlist-sequencer` skill — don't sequence inline. That skill owns the `playlist-sequencing-data.py` / `batch-full-analysis.py` analysis scripts and the album-craft methodology (per-track variables, energy arc models, key positions, locked arcs, encore structure, similar-songs-need-distance, felt-vs-librosa-BPM, mandatory Thematic Verification). Pass it the band/album and any locked-sequence context.

**Per-band playlist YAML:** each band's `docs/{band-slug}-playlist.yaml` is the single source of truth for its track sequence; the sequencer reads it and writes per-band outputs, so bands never overwrite each other. Schema, scaffolding and lifecycle rules: the suno-band-profile-manager skill's `references/playlist-yaml.md`.
