# Mac — Pulse

> **Narrow maintenance wake.** Pulse runs only when Mac is invoked with `--pulse` (a
> scheduled run, no one at the keyboard) and only if {user_name} has turned it on below.
> The wake prints access-boundaries, CREED, PERSONA and this file — Mac keeps his laws
> and character even here. Pulse reads, measures and stages findings for the next live
> session. It never edits creative content — that is a Law 3 (Protect the work) hard line.
>
> **Owner:** {user_name} · **Born:** {birth_date}
> **Project root:** `{project-root}`
> **Sanctum:** `{project-root}/_bmad/_memory/band-manager-sidecar/`

## Default Wake Behavior

If Owner Preferences below says Pulse is not enabled, stop here. Otherwise run these in
order (all read-only against creative content) and collect the results into one report:

1. **Curate memory first (proposal only)**
   `uv run scripts/check-memory-health.py "{project-root}/_bmad/_memory/band-manager-sidecar"`
   If MEMORY.md is over budget or has packed lines, read it and the recent `sessions/`
   logs and draft the distilled version: what stays, what moves down to `sessions/`.
   Put the draft in the report — do not edit MEMORY.md in place. Note any companion
   file over budget and any unlisted INDEX.md file.

2. **Validate the sanctum against catalog ground truth**
   `uv run scripts/validate-sidecar.py "{project-root}" --format json`
   Flags songbook/index drift, audio-file gaps, broken cross-references.

3. **Check derived-section freshness (dry run — do NOT write)**
   `uv run scripts/regenerate-index-sections.py "{project-root}" --dry-run --format json`
   Surfaces whether `Recently Published` / `Catalog Status` would change.

4. **Refresh stale genre-coverage indices**
   `uv run scripts/genre-coverage.py "{project-root}" --check` exits 1 when an index is
   stale or missing; then run `uv run scripts/genre-coverage.py "{project-root}" --timestamp "<today's date>"`.
   A derived, regenerable artifact — safe to refresh. Note any band whose index changed.

## Report-and-Stage Protocol

Write the report to MEMORY.md's `## Pulse Report` section (replace what is there),
dated with today's date: validator findings (errors first), whether derived sections are
stale, the proposed MEMORY.md distillation, oversized companion files, and any
refreshed coverage indices. Put long detail in `sessions/<today>.md` and point to it.
The next live session opens with this report, then clears the section once shown.

Then STOP. Do not act on the findings autonomously.

## Hard Lines (Law 3 — Protect the Work)

Pulse does not, under any circumstances:

- Edit, rewrite, prune, or "clean up" any song, lyric, WIP, songbook entry, or workshop file.
- Edit the voice file, mac-preferences, band profiles, or playlists.
- Write the regenerated derived sections or the curated version into `MEMORY.md` (it stages them).
- Overwrite anything without a human in the loop.

The only writes Pulse may make are: (a) the `## Pulse Report` section and its sessions/
detail, and (b) refreshing the purely derived genre-coverage indices. Before each write,
check the path: `uv run scripts/validate-path.py <path> write --boundaries
"{project-root}/_bmad/_memory/band-manager-sidecar/access-boundaries.md" --project-root "{project-root}"`.

## Owner Preferences

_({user_name}'s choices on Pulse — asked once during First Breath, changeable any time.
If {user_name} does not want autonomous wakes, Pulse stays dormant.)_

- **Enabled:** _(not yet decided)_
- **Frequency:** _(default: light, on demand — adjust per {user_name})_
- **Quiet hours:** _(not yet set)_
