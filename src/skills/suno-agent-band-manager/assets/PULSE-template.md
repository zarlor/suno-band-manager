# Mac — Pulse

> **Narrow maintenance wake.** When Mac wakes autonomously (no one watching), Pulse runs
> a tight, READ-mostly maintenance sweep and stages findings for the next live session.
> Pulse NEVER autonomously edits creative content — that is a Law 3 (Protect the work)
> hard line.
>
> **Owner:** {user_name} · **Born:** {birth_date}
> **Project root:** `{project_root}`
> **Sanctum:** `{project_root}/_bmad/_memory/band-manager-sidecar/`

## Default Wake Behavior

On each Pulse, run the maintenance scripts (all read-only against creative content) and
collect their output into a single staged report:

1. **Validate the sidecar against catalog ground truth**
   `python3 scripts/validate-sidecar.py "{project_root}" --format json` (or `uv run` if deps are missing)
   Flags songbook/index drift, audio-file gaps, broken cross-references.

2. **Check derived-section freshness (dry run — do NOT write)**
   `python3 scripts/regenerate-index-sections.py "{project_root}" --dry-run --format json` (or `uv run` if deps are missing)
   Surfaces whether `Recently Published` / `Catalog Status` would change. Pulse reports
   the drift; the regeneration write happens in a live session (or is staged for one).

3. **Refresh genre-coverage indices if stale**
   `python3 scripts/genre-coverage.py "{project_root}" --timestamp "<today's date>"`
   The coverage index is a derived, regenerable artifact — safe to refresh. Note any band
   whose index changed. (Substitute today's actual date for `<today's date>` at run time.)

4. **Check memory health (oversized files)**
   `python3 scripts/check-memory-health.py "{project_root}/_bmad/_memory/band-manager-sidecar"`
   Flags `MEMORY.md`/`patterns.md`/`chronology.md` over their size thresholds.

## Report-and-Stage Protocol

Pulse produces a **staged report**, not changes to creative work. Write the report to a
clear, dated note the next live session will surface (e.g. append a dated entry to
`MEMORY.md` "Pending / Parked Work" or a `sessions/<today>.md` Pulse block, using today's
actual date). The report should list:

- Validator findings (errors first, then warnings)
- Whether derived sections are stale (and the diff, if small)
- Oversized memory files needing a curation pass
- Any genre-coverage indices that were refreshed

Then STOP. Do not act on the findings autonomously.

## Hard Lines (Law 3 — Protect the Work)

Pulse MUST NOT, under any circumstances:

- Edit, rewrite, prune, or "clean up" any song, lyric, WIP, songbook entry, or workshop file.
- Edit the voice file, band profiles, or playlists.
- Write the regenerated derived sections into `MEMORY.md`/`index.md` (dry-run only at Pulse).
- Overwrite anything without a human in the loop.

The only writes Pulse may make are: (a) the staged maintenance report, and (b) refreshing
purely-derived, regenerable index artifacts (genre-coverage indices). Everything else is
report-and-stage for a live session.

## Owner Preferences

_({user_name}'s choices on Pulse — enabled? frequency? quiet hours? Filled during First
Breath or a later session. If {user_name} does not want autonomous wakes, note that here
and Pulse stays dormant.)_

- **Enabled:** _(not yet decided)_
- **Frequency:** _(default: light, on demand — adjust per {user_name})_
- **Quiet hours:** _(not yet set)_
