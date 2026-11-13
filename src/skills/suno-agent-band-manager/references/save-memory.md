**Language:** Use `{communication_language}` for all output.

**Preference shard first.** If `{project-root}/docs/mac-preferences-file-hygiene.md` exists (the wake lists it under `voice_context.preference_shards`), read it in full before anything else here: it holds the owner's saving, syncing, durable-file and release rules.

# Save Memory

The tending pass, with the session's note. When to tend or save, and the tending moves themselves, are in the sanctum's `HOW-I-REMEMBER.md` ("Tending"). This route adds the order, the scripts that check the result, and what to do with what they find.

Sanctum: `{project-root}/_bmad/memory/suno-agent-band-manager/`. Write rule: the Dominion section of the sanctum's `CREED.md`.

## Process

1. **Capture unsaved creative work first.** Look back through the conversation for creative material that isn't on disk yet — lyric fragments, images, structural ideas, song concepts without a name. Write it verbatim to the relevant WIP (`docs/wip-{working-title}-fragments.md`) before anything else, and say so: *"A few fragments from tonight aren't on paper yet — saving them to a WIP first."* Conversation doesn't survive the session or the trip to another machine; if it isn't in a file, it's lost.

2. **Handoff checkpoint.** Summarize what this pass will write — today's session note, the standing files it refreshes, a chronology entry, a production-pattern finding, a PERSONA or BOND line — in two to four bullets: *"Here's what I'd save: … Sound right?"* Wait for the owner. They may cut or add something; a pattern finding especially is their call, because it records what Mac has concluded about them.

3. **Bring the standing files up to date.** Whatever this session changed and didn't already land: `memory/work/current.md` (the song in progress — style prompt, model, band profile, mode, what to pick up next), `memory/work/parked.md`, `memory/work/downloads.md`, `memory/work/default-exclusions.md`, `memory/owner/preferences.md`, `memory/bands/active.md`, `memory/module/state.md`. Replace the section a fact changed; a standing file takes the result, and the session note keeps the story.
   - `current.md` changes one song at a time through `update_current.py`, as `HOW-I-REMEMBER.md` "Writing" gives the command (`--remove` when a piece of work is finished). If it refuses (`status: refused`, exit 1, because there is no v7 sanctum to write into), skip that checkpoint and leave `current.md` unwritten: the wake's conversion or restore comes first.
   - Leave `memory/catalog/` alone; step 6 regenerates it.

4. **Write the session note:** `memory/sessions/{today}-{slug}.md` — what happened, what was decided, what to pick up next. A few lines; the detail lives in the files it changed. A milestone or turning point also gets `memory/chronology/{today}-{slug}.md`, a few paragraphs.

5. **Tend**, as `HOW-I-REMEMBER.md` "Tending" says.

6. **Regenerate the catalog.** `uv run {skill-root}/scripts/regenerate_index_sections.py "{project-root}" --format json` rewrites `memory/catalog/recently-published.md` and `memory/catalog/status.md` from the songbook.
   - It exits 1 with `skipped[]` when a songbook entry was left out of the catalog (no frontmatter, a YAML error, a `band_profile` that names no band profile): tell the owner which entries were left out and why, fix the entry's frontmatter or `band_profile` with their say-so, and run it again.
   - It exits non-zero without writing when a catalog file has no derived-section markers: run it again with `--migrate`.
   - Then refresh the coverage index if `uv run {skill-root}/scripts/genre_coverage.py "{project-root}" --check` exits 1 (stale or missing): `uv run {skill-root}/scripts/genre_coverage.py "{project-root}" --timestamp "{today's date}"`, adding `--band {band-slug}` when only one band changed. With no songbook yet it exits 0 and writes nothing.

7. **Validate.** Run both:
   - `uv run {skill-root}/scripts/validate_sanctum.py "{project-root}" --since {date of the previous save}` — the catalog files against the songbook, playlist and voice-file catalog parity, `memory/work/parked.md` against WIP markers, Companion Files rows against disk (and, with `--since`, new `docs/` files the table doesn't list), broken `docs/` cross-references. `--since` takes an ISO date (`YYYY-MM-DD`) only and anything else is a usage error, so leave the flag off when there is no previous save date, as on a first save. Errors stop the save: surface them, because a save that fails validation spreads drift.
   - `uv run {skill-root}/scripts/check_memory_health.py "{project-root}"` — oversized identity or companion files, and standing files that are being appended to.

8. **Act on what's left.** These are independent; do the ones that apply:
   - **Findings from step 7.** Fix sync drift in one batch (a playlist YAML missing a new song, a stale catalog count, a COMPLETED WIP still listed as parked, an untracked companion file). Present them together: *"Found three loose ends — want me to fix them all, go one by one, or skip?"* Each one is also a sign that sync-at-the-point-of-change slipped; tighten that next session. The per-band playlist YAML is the band's single source of truth for its sequence.
   - **Oversized files.** A standing file longer than a screen → find the section being appended to and rewrite it as what is true now. A companion file over budget → offer the owner a compaction pass; don't do it unasked.
   - **WIP completion.** `uv run {skill-root}/scripts/scan_wip_status.py "{project-root}" --format json`. For an active WIP with a `correlation_warning` (its working title matches a published song), ask whether to mark it COMPLETED; `references/completed-wip.md` has the marker format.
   - **Behavioral corrections.** Any correction the owner gave this session that didn't reach `docs/mac-preferences.md` in the turn it landed — append it now.
   - **Production patterns.** After create or refine cycles, `uv run {skill-root}/scripts/songbook_catalog.py "{project-root}" --band {band-slug} --format json` gives model and slider tallies; judge whether a repeat is a pattern worth recording ("Weirdness 55 on your last three — your sweet spot?") and, on the owner's yes, add it to `docs/suno-production-patterns.md` as their finding, not a universal rule.
   - **Evolution (light, optional).** Did anything shift how Mac shows up, or what lands with the owner? One line in PERSONA.md's Evolution Log or BOND.md's Notes Toward the Bond. Durable behavioral rules still go to `docs/mac-preferences.md`.
   - **Renames.** If a song title, band name or playlist order changed, load `references/reconcile.md`.

9. **Travel triage, then stamp.** The sanctum stays on this machine. If anything durable about the owner or the craft lives only in the sanctum, give it a home in `docs/` (the voice file, `docs/mac-preferences.md`, `docs/suno-production-patterns.md`). Then write today's date to `memory/.tended`.

## Output

Confirm in Mac's voice with a short recap:

"Memory saved. Here's what we covered:
- {2-4 bullets: songs created or refined, preferences discovered, profiles updated}
- Ready to pick up right here next time."

For an owner who works across machines, the portable sync comes last, so it carries everything just saved, as `HOW-I-REMEMBER.md` "Tending" says. Offer `bash {project-root}/scripts/pack-portable.sh "{project-root}"` only when that script exists; when it doesn't (the pack scripts ship with the full repository, not with the installed skills), say so and point to INSTALLATION.md "Multi-Machine Sync". Then carry on with whatever they want next.
