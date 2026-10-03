---
name: suno-playlist-sequencer
description: Sequences tracks into album-craft playlists. Use when user says 'sequence my playlist', 'order my album', or 'plan my tracklist'.
---

# Playlist Sequencer

## Overview

This skill orders a body of tracks into a coherent album-craft listening experience, balancing sonic flow (Camelot key transitions, felt-BPM continuity, energy arcs) against narrative flow (thematic arcs, locked sequences, encore design). Act as an album producer who sequences for the listener's journey, not just for pairwise key compatibility. It runs deterministic audio analysis over a per-band playlist YAML, applies the album-craft methodology, and presents a recommended sequence with named, per-variable rationale.

**Domain context:** Sequencing has two layers. The *transition-evaluation* layer (Camelot wheel, BPM tolerances, felt-BPM correction, loudness steps) is mechanical and mostly scripted. The *album-craft* layer above it (energy arcs, load-bearing key positions, locked arcs, similar-songs-need-distance, encore structure) is judgment. The data is the *input* to sequencing decisions; it never makes them on its own.

**Design rationale (load-bearing):**

- **Listening experience is the arbiter, not the Camelot score.** Camelot measures the key relationship only. A key-compatible seam with a 70+ felt-BPM gap is "tempo-jarring," not "the strongest option." A parallel-key seam reads as distant on the wheel, yet the ear hears one harmonic center. Name what the ear hears.
- **Felt BPM governs.** Measured tempo misreads half- and double-time, so the ear decides. Once the user confirms a felt BPM, it lives in the playlist YAML (`felt_bpm:`) and the script applies it.
- **Placement weighs the thematic read as well as the math.** Read the song's songbook entry (or its `docs/song-thematic-dossier.md` entry) before any placement claim. Never infer a theme from a title or a line fragment: poets don't telegraph, and surface reads invert reliably. When two songs are cause and effect, never fix a key or tempo seam by handing the effect straight into its cause. That constraint binds the seam only: apart, the two can sit in either order.
- **Never break a documented locked arc on your own authority.** Surface locked arcs first. If a reorder would break one, stop and ask.

## Conventions

- Bare paths (e.g. `references/playlist-sequencing-methodology.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory, and so do `docs/...` paths (the project's data). Run scripts from `{project-root}` so their `docs/` defaults land there.
- `{skill-name}` resolves to the skill directory's basename.
- A sibling skill's file is named by skill ("the suno-band-profile-manager skill's `scripts/scaffold-playlist.py`") and resolves from that skill's installed directory.

## Activation Mode Detection

- **Headless** (`--headless` / `-H`, or the intent is plainly non-interactive): run On Activation steps 1-2 with no greeting, then follow `references/headless-contract.md` (inputs including `--locked` arcs, run order, success and blocked JSON).
- **Interactive** (default): proceed to On Activation.

## On Activation

1. **Resolve customization.** Run `uv run {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --project-root {project-root} --key workflow` for `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` and `on_complete` (merge order: base `customize.toml`, then team `{project-root}/_bmad/custom/{skill-name}.toml`, then user `{skill-name}.user.toml`). If the script is unavailable, read those files in that order and merge by hand. Run any `activation_steps_prepend` and load `persistent_facts`, in headless runs too.
2. **Load config.** Run `uv run {project-root}/_bmad/scripts/resolve_config.py --project-root {project-root} --key core` for `{user_name}`, `{communication_language}` and `{document_output_language}`. Module settings (`songbook_folder`, `pytorch_audio_tools`) are in the `suno:` section of `{project-root}/_bmad/config.yaml`. If either is missing, greet generically, default to English and `docs/songbook`, and carry on.
3. **Greet** `{user_name}` in `{communication_language}`, run any `activation_steps_append`, and start the workflow.

## Workflow

### Step 1: Intake

**Open the floor.** Invite everything at once: the band or album, the playlist YAML (or whether one needs scaffolding), what they want fixed ("doesn't flow"), and whether this is a first ordering, a re-eval after a regen wave, or one new track to slot. Ask here, once, about anything fixed: locked arcs, a deliberate opener or closer, a track they refuse to move.

**Frame the scope.** Say back what you're about to do and how deep it goes. A full re-sequence with a thematic read of every song is a bigger commitment than a one-track slot or a sonic-only pass. A 1-2-track adjacent swap, a sonic-only pass on a fixed order, or a playlist of four or fewer tracks skips the arc models (methodology, "When to Use").

**Canonical input** is `docs/{band-slug}-playlist.yaml`, the band's single source of truth for track order. If a band has songbook entries but no YAML, run the suno-band-profile-manager skill's `scripts/scaffold-playlist.py {band-slug} --from-songbook` and have the user fill in the audio filenames.

**Resume.** The workspace is `docs/{band-slug}-playlist-sequencing/`. If it holds a `.memlog.md`, read it once (and a legacy `.decision-log.md` once, if present) and treat settled placements as the standing record: raise any conflict with a prior call before changing it. Otherwise create one with `uv run {project-root}/_bmad/scripts/memlog.py init --workspace docs/{band-slug}-playlist-sequencing --field topic="{album} sequencing"`. If memlog.py is absent, append the same one-line `- (type) text` entries by hand.

### Step 2: Generate Sequencing Data

Run `uv run scripts/playlist-sequencing-data.py --playlist docs/{band-slug}-playlist.yaml`. The JSON holds per-track tempo, keys, energy, and loudness, plus every seam's key relation, tempo change, and loudness step. It also archives itself and refreshes the companion `docs/{band-slug}-playlist-sequencing.md`. If the audio dependencies are missing, it exits 2 with install instructions: say so, and carry on with any archive already on disk.

**Drops.** Any entry in the top-level `dropped[]` was not analyzed (missing audio file or analysis error). Name each one and confirm with the user before sequencing: fix the filename, or go on knowingly without it. A confident sequence over the wrong list is the failure this prevents.

**Re-eval.** The script reads the prior archive before overwriting it and adds a `compare` block: tracks whose tempo, key, energy or loudness moved, and seams that got worse or better. Lead the proposal with that, not a fresh derivation. A second run in the same session compares against the first, so keep the first run's `compare` block.

**Fully degraded** (no deps and no archive): don't invent numbers. Help install the deps, or work on narrative grounds only (locked arcs, theme spacing, act logic) and say plainly that the sonic layer is unverified.

**Optional catalog pass:** `uv run scripts/batch-full-analysis.py --audio-dir docs/audio/{band-slug}` adds energy shifts, section boundaries, and dynamic character. Use it when that shape informs the arc; skip it for a quick reorder.

### Step 3: Apply the Methodology

Reload `references/playlist-sequencing-methodology.md` before every recommendation. Long sessions compact it out, and a sequence formed from memory drops felt-BPM correction, locked arcs, and the thematic read. Work its three ordered gates: surface locked arcs (`uv run scripts/validate-sequence.py docs/{band-slug}-playlist.yaml` reports each one), settle felt BPM and do the thematic read for every song involved before drafting, then recommend with trade-offs.

For a full re-sequence, run a **sonic-flow** lens and a **narrative-flow** lens side by side, and reconcile where they disagree rather than letting one silently win.

### Step 4: Present the Sequence

Before building the order, ask "anything else before I build it?" Skip it if intake already covered the fixed points.

Present an *opinionated proposal*, not a metrics dump: the order, per-move rationale naming what each variable says, the energy-arc shape, which arcs held locked, and honest trade-offs ("trades A-jarring for B-jarring", not "cleaner"). Say where the user's ear should break the tie. Iterate.

**Log as you go** with `uv run {project-root}/_bmad/scripts/memlog.py append --workspace docs/{band-slug}-playlist-sequencing`: `--type decision` for each placement, the alternatives rejected, and any locked-arc break the user authorizes; `--type direction` for narrative asides ("that one's really about my dad"). Capture asides rather than chasing them mid-flow. They are often the thematic context the songbook read would otherwise have to find. When the user confirms a felt BPM by ear, offer to record it as `felt_bpm:` on that track.

**At sign-off,** write the accepted order to `docs/{band-slug}-playlist-sequencing/accepted-order.txt` (one name per line) and run `uv run scripts/validate-sequence.py docs/{band-slug}-playlist.yaml --order <that file>`. Show the user the moves it previews. Fix any error it names, and after the user confirms, run it again with `--write`. Then re-run the sequencing script with `--no-compare` so the archive and companion match the new order. Write the proposal narrative in `{communication_language}` and saved documents in `{document_output_language}`. Then run `{workflow.on_complete}` if set.

## Scripts

Each script documents itself with `--help`. All run with `uv run`, which provisions the dependencies.

- `scripts/playlist-sequencing-data.py`: the per-track and per-seam sequencing data, drops, runs, and re-eval compare.
- `scripts/validate-sequence.py`: the locked-arc check and the pre-write gate on the playlist YAML.
- `scripts/batch-full-analysis.py`: the catalog-wide deeper analysis.
