---
name: post-publish
description: The pass that runs once a keeper is downloaded or published — measure it, record it, reconcile and index.
---

**Language:** Use `{communication_language}` for all output.

**Preference shard first.** If `{project-root}/docs/mac-preferences-audio-playlists.md` exists (the wake lists it under `voice_context.preference_shards`), read it in full before anything else here: it holds the owner's audio and playlist rules. The record and reconcile steps also need `{project-root}/docs/mac-preferences-file-hygiene.md`, read the same way.

# Post-Publish (When the Keeper Is Downloaded)

The owner has a keeper: a take they downloaded, or a track they published, with its audio in the band's audio folder. Offer this pass; it runs on that one file, because downloads are capped and each one is spent on purpose. When it's done, the songbook entry holds measured numbers, every file that names the song agrees with it, and the coverage index includes it. In order:

1. **Measure.** Invoke the suno-feedback-elicitor skill's Analyze Audio capability on the keeper for tempo, key, duration and loudness. When `pytorch_audio_tools` is on in the module config, ask it for the section map too, with the package lyrics, before judging structure or dynamics.
2. **Songbook entry.** Write the measured BPM, key, duration and LUFS into the songbook entry, and record `source_wip: docs/wip-<slug>.md` in its frontmatter when the song grew from a WIP. If the Lyric Transformer returned a `decision_log` / `intentional_keeps` without a `song_path`, append them as a `## Session YYYY-MM-DD (transform)` section to `{song-title}.decision-log.md` beside the entry.
3. **Reconcile** (below).
4. **Index.** `uv run {skill-root}/scripts/genre-coverage.py "{project-root}" --band {band-slug}` so the coverage index reflects the new song.

Scripts are the source of truth for numbers. Outside LLM listening notes (Gemini and the like) help with qualitative description but are unreliable for BPM, duration and vocal-dynamics claims — check them against the script output, never the other way round. Playlist placement goes to the suno-playlist-sequencer skill rather than being done inline; it weighs key transitions, tempo flow, energy arc and thematic fit together.

## Reconciliation

Sync happens at the point of change (the sanctum `CREED.md` Principles): each publish write carries its cross-file updates in the same batch — songbook entry, the band's playlist YAML, the voice file's catalog count and Companion Files row, the sanctum's `memory/work/current.md` and `memory/work/parked.md`. Then one deterministic backstop:

- **Run `uv run {skill-root}/scripts/validate-sidecar.py "{project-root}" --format json`** and act on `playlist_drift` (the playlist and songbook name different songs), `voice_catalog_drift` (a stale published count), `pending_drift` (a COMPLETED WIP still listed, or an active one missing) and `companion_missing` findings.
- **Title changed from the working title:** load `references/reconcile.md` and run it with the old and new titles.
- **Song came from a WIP file:** mark that WIP COMPLETED — never delete it. You know which WIP you worked from this session; mark it directly (`references/reconcile.md` → "The COMPLETED WIP convention" has the marker). `uv run {skill-root}/scripts/scan-wip-status.py "{project-root}" --format json` is the backstop for WIPs this session didn't touch: its `correlation_warning` names unmarked WIPs that a published entry's `source_wip` points at, or whose working title matches. The marker is required whenever a song originated from a WIP, even if nothing else changed — without it, the next session (especially on another machine after a portable sync) treats the finished song as pending work.

A song that published under its original title with no metadata changes needs nothing beyond the validator run.
