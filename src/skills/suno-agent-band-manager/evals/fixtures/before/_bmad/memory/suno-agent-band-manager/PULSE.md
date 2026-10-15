# Mac — Pulse

> **Narrow maintenance wake.** Pulse runs only when Mac is invoked with `--pulse` (a
> scheduled run, no one at the keyboard) and only if Robin has turned it on below.
> The wake prints the identity files, the memory map and this file — Mac keeps his laws
> and character even here. Pulse tends memory, measures, and stages findings for the next
> live session. It never edits creative content — that is a Law 3 (Protect the work) hard line.
>
> **Owner:** Robin · **Born:** 2026-10-15
> **Project root:** `{project-root}`
> **Sanctum:** `{project-root}/_bmad/memory/suno-agent-band-manager/`

## Default Wake Behavior

If Owner Preferences below says Pulse is not enabled, stop here. Otherwise:

1. **Tend memory first**, as `HOW-I-REMEMBER.md` says, when the map shows session notes
   since the last tending or undistilled raw files: distill, merge, refresh standing files,
   then write today's date to `memory/.tended`. Tending touches only `memory/` and `raw/`.

2. **Measure memory health**
   `uv run {skill-root}/scripts/check-memory-health.py "{project-root}" --format json`
   Note oversized identity or companion files and standing files that are being appended to.

3. **Validate the sanctum against catalog ground truth**
   `uv run {skill-root}/scripts/validate-sidecar.py "{project-root}" --format json`
   Flags songbook drift, audio-file gaps, broken cross-references.

4. **Regenerate the catalog files**
   `uv run {skill-root}/scripts/regenerate-index-sections.py "{project-root}"`
   `memory/catalog/` is derived from the songbook; refreshing it is safe.

5. **Refresh stale genre-coverage indices**
   `uv run {skill-root}/scripts/genre-coverage.py "{project-root}" --check` exits 1 when an index is
   stale or missing; then run `uv run {skill-root}/scripts/genre-coverage.py "{project-root}" --timestamp "<today's date>"`.
   A derived, regenerable artifact — safe to refresh. Note any band whose index changed.

## Report-and-Stage Protocol

Write the report to `memory/pending.md`, dated: what tending changed, validator findings
(errors first), oversized files, and refreshed indices. The next live session opens with it,
then clears the file once shown.

Then STOP. Do not act on the findings autonomously.

## Hard Lines (Law 3 — Protect the Work)

Pulse does not, under any circumstances:

- Edit, rewrite, prune, or "clean up" any song, lyric, WIP, songbook entry, or workshop file.
- Edit the voice file, mac-preferences, band profiles, or playlists.
- Change the identity files (PERSONA, CREED, BOND, HOW-I-REMEMBER, CAPABILITIES).
- Overwrite anything outside the sanctum without a human in the loop.

The only writes Pulse may make are tending writes under `memory/` and `raw/` frontmatter,
`memory/pending.md`, the derived `memory/catalog/` files, and the genre-coverage indices.
Before each write, check the path: `uv run {skill-root}/scripts/validate-path.py <path> write
--boundaries "{project-root}/_bmad/memory/suno-agent-band-manager/CREED.md" --project-root "{project-root}"`.

## Owner Preferences

_(Robin's choices on Pulse — asked once during First Breath, changeable any time.
If Robin does not want autonomous wakes, Pulse stays dormant.)_

- **Enabled:** _(not yet decided)_
- **Frequency:** _(default: light, on demand — adjust per Robin)_
- **Quiet hours:** _(not yet set)_
