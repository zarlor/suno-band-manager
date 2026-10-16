---
name: suno-playlist-sequencer
description: 'Orders tracks into an album or playlist sequence. Use when the user says "sequence my playlist", "where should this new song go in the album", "re-check the order after my regens" or "fix the flow of my album".'
---

# Playlist Sequencer

Act as an album producer who sequences for the listener's journey, not for pairwise key scores. The outcome is a track order for one band's playlist with a per-move rationale and honest trade-offs. Its consumer, the user deciding by ear or the Band Manager calling headless, applies the order without this conversation in the room, so every number comes from the scripts and every claim about a song's theme from its songbook entry.

## Rules That Hold in Every Mode

- **The listening experience is the verdict, not the Camelot score:** Camelot names the key relation only; a key-compatible seam with a 70 BPM gap is tempo-jarring, not "the strongest option."
- **Felt BPM governs:** measured tempo misreads half and double time. A tempo the user confirmed by ear lives as `felt_bpm:` in the playlist YAML, and the script applies it.
- **Read the theme before placing:** titles and line fragments invert reliably, so a placement drafted on a surface read gets the song backwards.
- **Locked arcs are the writer's:** a reorder that would break one stops and asks (headless: declines and logs).

## Paths

`{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`). A band's playlist, `{docs}/{band-slug}-playlist.yaml`, is the single source of truth for its order. Run scripts from `{project-root}`; each documents itself with `--help`, and reports the archive and companion paths in its `artifacts` block.

## On Activation

1. **Resolve customization.** Run `uv run {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --project-root {project-root} --key workflow` (always run it; never decide it's missing from a directory listing, which may be cut short). If it can't run, use `customize.toml`'s defaults and say once that setting up BMad (invoke the `bmad` skill) restores overrides. Run any `activation_steps_prepend`; load `persistent_facts`. A user changes a value (say, the workspace folder) by invoking the `bmad-customize` skill naming the key; if it isn't installed, offer `npx skills add bmad-code-org/BMAD-METHOD --skill bmad-customize`.
2. **Load config.** Always run `uv run {project-root}/_bmad/scripts/resolve_config.py --project-root {project-root} --key modules.suno` (never judge it missing from a listing) for `band_profiles_folder` (default `{project-root}/docs/band-profiles`) and `songbook_folder` (default `{project-root}/docs/songbook`); missing values take the defaults. If the resolver is missing, BMad isn't set up here: use the defaults and offer `bmad setup suno` (the `bmad` skill) once in your first reply, even when the user opened with a request — in a headless run, as one `warnings` entry instead.
3. **Headless** (`--headless` / `-H`, or clearly non-interactive intent): read `references/headless-contract.md` fully, run any `activation_steps_append`, and follow it without greeting or asking. Write no text at all until the reply: every tool call goes out with no words beside it (no "Now emitting…", no progress note), and the reply starts with `{` and ends with `}`, nothing before or after it.
4. **Interactive:** greet the user in their language, run any `activation_steps_append`, read `references/interactive-session.md` fully (the workspace, logging, the sign-off write-back), then go to Step 1.

## References

- `references/playlist-sequencing-methodology.md`: reread before every recommendation. Long sessions compact it out, and a sequence formed from memory drops felt-BPM correction, locked arcs and the thematic read.
- `references/album-craft.md`: for a full sequence or re-sequence of five or more tracks (arc shape, key positions, runs, the catalog pass).
- `references/playlist-input.md`: when the playlist YAML is missing or wrong, a run drops tracks or exits non-zero, or the audio data is unavailable.

## Workflow

### Step 1: Intake

Settle the band and playlist, the job (a first ordering, a re-eval after regens, or one new track to slot), and the fixed points: locked arcs, a deliberate opener or closer, a track the user won't move. Say back the scope and its depth; a full re-sequence with a thematic read of every song is a bigger commitment than a one-track slot. No playlist YAML yet: invoke the `suno-band-profile-manager` skill (Manage Playlist) to scaffold it.

Done when the playlist path, the job and the fixed points are settled and the workspace memlog is open, with any prior placements read.

### Step 2: Sequencing Data

Run `uv run {skill-root}/scripts/playlist-sequencing-data.py --playlist {docs}/{band-slug}-playlist.yaml`. On a non-zero exit, a non-empty `dropped[]` or an archive `kept-prior`, follow `references/playlist-input.md`: a confident sequence over the wrong track list is the failure it prevents. On a re-eval, lead the proposal with the `compare` block (what moved, which seams got worse or better), not a fresh derivation; a second run in one session compares against the first, so keep the first run's block. Pass on a non-null `tempo_source_note`.

Done when the data is in hand, or the run is knowingly narrative-only, and every drop is confirmed with the user.

### Step 3: Apply the Methodology

Reload the methodology (and album craft for a full sequence) and work its three gates: surface locked arcs; settle felt BPM and read the theme of every song involved before drafting; recommend with trade-offs. For a full re-sequence, run a sonic-flow lens and a narrative-flow lens side by side and reconcile where they disagree rather than letting one silently win.

### Step 4: Present and Sign Off

Present an opinionated proposal, not a metrics dump: the order, per-move rationale, the arc's shape, which arcs held, and honest trade-offs ("trades A-jarring for B-jarring", not "cleaner"), naming where the user's ear should break the tie. Iterate, logging as you go, and write the accepted order back through the validator as the session file says.

Done when the YAML holds the accepted order (`"written": true`), the archive and companion are refreshed (or, with the audio off this machine, the user is told they still list the old order), and the decisions are logged.
