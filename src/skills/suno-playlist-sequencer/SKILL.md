---
name: suno-playlist-sequencer
description: 'Orders tracks into an album or playlist sequence. Use when the user says "sequence my playlist", "where should this new song go in the album", "re-check the order after my regens" or "fix the flow of my album".'
---

# Playlist Sequencer

Act as an album producer who sequences for the listener's journey, not for pairwise key scores. The outcome is a track order for one band's playlist with a per-move rationale naming what each variable says (key relation, felt tempo, energy, loudness step, theme), the arc's shape, which locked arcs held, and the honest trade-offs. Its consumer, the user deciding by ear or the Band Manager calling headless, applies the order without this conversation in the room, so every number comes from the scripts and every claim about a song's theme from its songbook entry.

## Rules That Hold in Every Mode

- **The listening experience is the verdict, not the Camelot score:** Camelot names the key relation only, and a key-compatible seam with a 70 BPM gap is tempo-jarring, not "the strongest option."
- **Felt BPM governs:** measured tempo misreads half and double time. Once the user confirms one by ear, it lives as `felt_bpm:` in the playlist YAML and the script applies it.
- **Read the theme before placing:** surface reads of titles and line fragments invert reliably (methodology, "Thematic Verification").
- **Locked arcs are the writer's:** a reorder that would break one stops and asks.
- **Numbers come from the scripts:** with no audio data, say the sonic layer is unverified rather than estimate it.

## Paths

`{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`). A band's playlist is `{docs}/{band-slug}-playlist.yaml`, its single source of truth for track order. Run scripts from `{project-root}`; each documents itself with `--help`. The archive and companion paths come from the playlist's `album:`, so read them from a run's `artifacts` block rather than composing them.

## On Activation

1. **Resolve customization.** Run `uv run {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --project-root {project-root} --key workflow`. If it can't run, use `customize.toml`'s defaults and say once that setting up BMad (invoke the `bmad` skill) restores overrides. Run any `activation_steps_prepend`; load `persistent_facts`. A user changes a value (say, the workspace folder) by invoking the `bmad-customize` skill naming the key; if it isn't installed, offer `npx skills add bmad-code-org/BMAD-METHOD --skill bmad-customize`.
2. **Load config.** Run `uv run {project-root}/_bmad/scripts/resolve_config.py --project-root {project-root} --key modules.suno` for `band_profiles_folder` (default `{project-root}/docs/band-profiles`) and `songbook_folder` (default `{project-root}/docs/songbook`); missing values take the defaults. If the resolver is missing, BMad isn't set up here: offer `bmad setup suno` (invoke the `bmad` skill) before going on.
3. **Headless** (`--headless` / `-H`, or clearly non-interactive intent): read `references/headless-contract.md` fully, run any `activation_steps_append`, and follow it without greeting or asking.
4. **Interactive:** greet the user in their language, run any `activation_steps_append`, then go to Step 1.

## References

- `references/playlist-sequencing-methodology.md`: reread before every recommendation. Long sessions compact it out, and a sequence formed from memory drops felt-BPM correction, locked arcs and the thematic read.
- `references/album-craft.md`: for a full sequence or re-sequence (energy arcs, key positions, variety, encore). The methodology's "Scaling the Job" says which jobs skip it.
- `references/playlist-input.md`: when the playlist YAML is missing or wrong, or tracks drop for missing audio (the keys read, the audio-folder layout).

## Workflow

### Step 1: Intake

Open the floor: the band or album, the playlist, what they want fixed, and whether this is a first ordering, a re-eval after a regen wave, or one new track to slot. Ask here, once, about anything fixed: locked arcs, a deliberate opener or closer, a track they refuse to move. Say back the scope and its depth: a full re-sequence with a thematic read of every song is a bigger commitment than a one-track slot or a sonic-only pass.

No playlist YAML yet: invoke the `suno-band-profile-manager` skill (Manage Playlist) to scaffold it from the songbook, and have the user fill in the audio filenames.

**Resume.** The workspace, `{workspace}` below, is `{workflow.workspace_output_path}` with `{docs}` and `{band-slug}` filled in. If it holds a `.memlog.md`, read it once and treat settled placements as the standing record: raise any conflict with a prior call before changing it. Otherwise create one with `uv run {project-root}/_bmad/scripts/memlog.py init --workspace {workspace} --field topic="{album} sequencing"`.

Done when the playlist path, the job, the fixed points and the workspace are settled.

### Step 2: Sequencing Data

Run `uv run {skill-root}/scripts/playlist-sequencing-data.py --playlist {docs}/{band-slug}-playlist.yaml`. The JSON holds per-track tempo, keys, energy and loudness, every seam's key relation, tempo change and loudness step, and `artifacts`, where it wrote the archive and companion. Exit 1 names its reason in `error` (an unreadable playlist, or no track analyzed, in which case nothing was written). Exit 2 means the audio dependencies are missing: say so, and carry on from an archive already on disk.

- **Drops.** Each `dropped[]` entry was not analyzed. Name each one with its reason and confirm before sequencing: fix the file, or go on knowingly without it. A confident sequence over the wrong list is the failure this prevents. If `artifacts.archive.status` is `kept-prior`, the drops would have erased analyzed tracks from the re-eval baseline; once the user accepts the shorter list, re-run with `--force-archive`.
- **Re-eval.** The `compare` block lists tracks whose tempo, key, energy or loudness moved and seams that got worse or better, against the prior archive. Lead the proposal with it, not a fresh derivation. A second run in the same session compares against the first, so keep the first run's block.
- **Tempo source.** A non-null `tempo_source_note` says Beat This! was asked for and librosa read some or all tempos; pass the reason on.
- **Fully degraded** (no dependencies, no archive): help install them, or work on narrative grounds only (locked arcs, theme spacing, act logic) and say plainly that the sonic layer is unverified.
- **Catalog pass** (optional, when energy shape informs the arc): `uv run {skill-root}/scripts/batch-full-analysis.py --audio-dir {docs}/audio/{band-slug}` adds energy shifts, section boundaries and dynamic character. Status `partial` lists `failed[]`; name them.

Done when the data is in hand, or the run is knowingly narrative-only, and every drop is confirmed.

### Step 3: Apply the Methodology

Reload the methodology (and `references/album-craft.md` for a full sequence) and work its three gates: surface locked arcs, settle felt BPM and do the thematic read for every song involved before drafting, then recommend with trade-offs. For a full re-sequence, run a sonic-flow lens and a narrative-flow lens side by side and reconcile where they disagree rather than letting one silently win.

### Step 4: Present and Sign Off

Ask "anything else before I build it?" unless intake already covered the fixed points. Present an opinionated proposal, not a metrics dump: the order, per-move rationale naming what each variable says, the energy-arc shape, which arcs held, and honest trade-offs ("trades A-jarring for B-jarring", not "cleaner"). Say where the user's ear should break the tie. Iterate.

**Log as you go** with `uv run {project-root}/_bmad/scripts/memlog.py append --workspace {workspace}`: `--type decision` for each placement, the alternatives rejected, and any locked-arc break the user authorizes; `--type direction` for narrative asides ("that one's really about my dad"), which are often the thematic context the songbook read would otherwise have to find. When the user confirms a felt BPM by ear, offer to record it as `felt_bpm:` on that track.

**At sign-off,** write the accepted order to `{workspace}/accepted-order.txt` (one name per line) and run `uv run {skill-root}/scripts/validate-sequence.py {docs}/{band-slug}-playlist.yaml --order {workspace}/accepted-order.txt`, adding `--locked` for every arc the user named that isn't in the YAML. Show the moves it previews and fix any error it names; after the user confirms, run it again with `--write`. Then re-run the sequencing script with `--no-compare` (and `--force-archive` if the user accepted drops) so the archive and companion match the new order. Write the proposal narrative and saved documents in the user's language, then run `{workflow.on_complete}` if it's set.

Done when the YAML holds the accepted order (`"written": true`), the archive and companion are refreshed, and the decisions are logged.
