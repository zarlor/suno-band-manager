---
name: save-memory
description: Consolidate the session into Mac's memory — the two-tier save
menu-code: SM
---

**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`

# Save Memory

The consolidating pass. Mac captures as he goes (Persistent Memory), so this is where the session gets curated: raw detail down into `sessions/`, the live state up into MEMORY.md, derived sections regenerated, everything validated. Run it when real uncurated work has piled up or the owner asks — it is not a sign-off ritual.

**Headless-eligible:** false — save-memory distills the live conversation and needs the owner's confirmation at the checkpoint. A headless invocation returns `{status: blocked, reason: "interactive-only"}`; headless capabilities run their own persistence (`references/headless.md`).

Sanctum: `{project-root}/_bmad/_memory/band-manager-sidecar/`. Write rule: the sanctum's `access-boundaries.md`.

## Process

1. **Capture unsaved creative work first.** Look back through the conversation for creative material that isn't on disk yet — lyric fragments, images, structural ideas, song concepts without a name. Write it verbatim to the relevant WIP (`docs/wip-{working-title}-fragments.md`) before anything else, and say so: *"A few fragments from tonight aren't on paper yet — saving them to a WIP first."* Conversation doesn't survive the session or the trip to another machine; if it isn't in a file, it's lost.

2. **Handoff checkpoint.** Summarize what this save will write — MEMORY.md changes, today's `sessions/` entry, any `patterns.md` or `chronology.md` additions, a PERSONA or BOND line — in two to four bullets: *"Here's what I'd save: … Sound right?"* Wait for the owner. They may cut or add something; `patterns.md` especially is their call, because it records what Mac has concluded about them.

3. **Append the raw narrative** to `sessions/{today}.md` (create it on the first save of the day): the play-by-play, workshop detail, the story behind any publish. This is the durable record — nothing is lost here even when MEMORY.md stays lean.

4. **Distill into MEMORY.md — narrative sections only.** Update Current Work, Pending / Parked Work, User Preferences, Downloads, Default Exclusions, Active Band Profiles, Module State and Session History with the live state: the song in progress (style prompt, model, band profile, mode), preferences discovered, downloads spent, what to pick up next. Don't touch Recently Published or Catalog Status — they sit between `<!-- derived:… -->` markers and step 5 regenerates them. Keep the file near its token budget (`references/memory-system.md`): when a work block has aged into history, move its detail to `sessions/` and leave a one-line pointer. One line per thought — never pack a session into a single line.

5. **Regenerate the derived sections.** `uv run scripts/regenerate-index-sections.py "{project-root}"` rewrites Recently Published and Catalog Status in MEMORY.md from the songbook. If it reports missing markers, re-run with `--migrate`; if a heading is missing entirely, add it (see `assets/MEMORY-template.md`) and re-run. Then refresh the coverage index if `uv run scripts/genre-coverage.py "{project-root}" --check` reports it stale: `uv run scripts/genre-coverage.py "{project-root}" --timestamp "{today's date}"` (add `--band {band-slug}` when only one band changed; it exits cleanly when there is no songbook yet).

6. **Validate.** Run both:
   - `uv run scripts/validate-sidecar.py "{project-root}" --since {date of the previous save}` — derived sections vs the songbook, playlist and voice-file catalog parity, Pending / Parked Work vs WIP markers, Companion Files rows vs disk (and, with `--since`, new `docs/` files the table doesn't list), broken `docs/` cross-references. Errors stop the save: surface them, because a save that fails validation spreads drift.
   - `uv run scripts/check-memory-health.py "{project-root}/_bmad/_memory/band-manager-sidecar"` — MEMORY.md and spine tokens, packed lines, companion-file sizes, organic files missing from INDEX.md.

7. **Act on what's left** — these are independent; do the ones that apply:
   - **Findings from step 6.** Fix sync drift in one batch (a playlist YAML missing a new song, a stale catalog count, a COMPLETED WIP still listed as active, an untracked companion file, an INDEX.md row). Present them together: *"Found three loose ends — want me to fix them all, go one by one, or skip?"* Each one is also a sign that sync-at-the-point-of-change slipped; tighten that next session. The per-band playlist YAML is the band's single source of truth for its sequence (the suno-band-profile-manager skill's `references/playlist-yaml.md`).
   - **Over budget.** MEMORY.md over budget → curate it now. A companion file over budget → offer the owner a compaction pass; don't do it unasked.
   - **WIP completion.** `uv run scripts/scan-wip-status.py "{project-root}" --format json`. For an active WIP with a `correlation_warning` (its working title matches a published song), ask whether to mark it COMPLETED (`references/reconcile.md` → "The COMPLETED WIP convention" has the marker format).
   - **Behavioral corrections.** Any correction the owner gave this session that didn't reach `docs/mac-preferences.md` in the turn it landed — append it now.
   - **Production patterns.** After create or refine cycles, `uv run scripts/songbook-catalog.py "{project-root}" --band {band-slug} --format json` gives model and slider tallies; judge whether a repeat is a pattern worth recording ("Weirdness 55 on your last three — your sweet spot?") and, on the owner's yes, add it to `patterns.md` as their finding, not a universal rule.
   - **Chronology.** If the sanctum keeps a `chronology.md` and the session mattered, add a summary.
   - **Evolution (light, optional).** Did anything shift how Mac shows up, or what lands with the owner? One line in PERSONA.md's Evolution Log or BOND.md's Notes Toward the Bond. Durable behavioral rules still go to `docs/mac-preferences.md`.
   - **Renames.** If a song title, band name or playlist order changed, load `references/reconcile.md` for the full reconciliation.

## Output

Confirm in Mac's voice with a short recap:

"Memory saved. Here's what we covered:
- {2-4 bullets: songs created or refined, preferences discovered, profiles updated}
- Ready to pick up right here next time."

If the owner works across machines, offer the portable sync now — after the save, so it captures everything: `bash {project-root}/scripts/pack-portable.sh "{project-root}"`. Then carry on with whatever they want next.
