---
name: save-memory
description: Tend Mac's memory and write the session note
menu-code: SM
---

**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`

# Save Memory

The tending pass. Mac captures as he goes (Persistent Memory), so this is where memory gets tended the way the sanctum's `HOW-I-REMEMBER.md` says, and the session gets its note. Run it when session notes or raw material have built up, when the session is winding down after real work, or when the owner asks — it is not a sign-off ritual.

**Headless-eligible:** false — save-memory distills the live conversation and needs the owner's confirmation at the checkpoint. A headless invocation returns `{status: blocked, reason: "interactive-only"}`; headless capabilities run their own persistence (`references/headless.md`).

Sanctum: `{project-root}/_bmad/memory/suno-agent-band-manager/`. Write rule: the Dominion section of the sanctum's `CREED.md`.

## Process

1. **Capture unsaved creative work first.** Look back through the conversation for creative material that isn't on disk yet — lyric fragments, images, structural ideas, song concepts without a name. Write it verbatim to the relevant WIP (`docs/wip-{working-title}-fragments.md`) before anything else, and say so: *"A few fragments from tonight aren't on paper yet — saving them to a WIP first."* Conversation doesn't survive the session or the trip to another machine; if it isn't in a file, it's lost.

2. **Handoff checkpoint.** Summarize what this pass will write — today's session note, the standing files it refreshes, a chronology entry, a production-pattern finding, a PERSONA or BOND line — in two to four bullets: *"Here's what I'd save: … Sound right?"* Wait for the owner. They may cut or add something; a pattern finding especially is their call, because it records what Mac has concluded about them.

3. **Bring the standing files up to date.** Whatever this session changed and didn't already land: `memory/work/current.md` (the song in progress — style prompt, model, band profile, mode, what to pick up next), `memory/work/parked.md`, `memory/work/downloads.md`, `memory/work/default-exclusions.md`, `memory/owner/preferences.md`, `memory/bands/active.md`, `memory/module/state.md`. Replace the section a fact changed; never append a session's story to a standing file. When a piece of work is finished, take it out of `current.md` — the session note keeps the story. Don't touch `memory/catalog/`; step 6 regenerates it.

4. **Write the session note:** `memory/sessions/{today}-{slug}.md` — what happened, what was decided, what to pick up next. A few lines; the detail lives in the files it changed. A milestone or turning point also gets `memory/chronology/{today}-{slug}.md`, a few paragraphs.

5. **Tend**, as `HOW-I-REMEMBER.md` says: distill every `raw/` file still marked `status: raw` into subject files and mark it `status: distilled`; merge two files about one subject; refresh any standing file a recent note contradicts; put what the owner should hear next time in `memory/pending.md`. Nothing is deleted for being old.

6. **Regenerate the catalog.** `uv run {skill-root}/scripts/regenerate-index-sections.py "{project-root}"` rewrites `memory/catalog/recently-published.md` and `memory/catalog/status.md` from the songbook. If it reports missing markers, re-run with `--migrate`. Then refresh the coverage index if `uv run {skill-root}/scripts/genre-coverage.py "{project-root}" --check` reports it stale: `uv run {skill-root}/scripts/genre-coverage.py "{project-root}" --timestamp "{today's date}"` (add `--band {band-slug}` when only one band changed; it exits cleanly when there is no songbook yet).

7. **Validate.** Run both:
   - `uv run {skill-root}/scripts/validate-sidecar.py "{project-root}" --since {date of the previous save}` — the catalog files vs the songbook, playlist and voice-file catalog parity, `memory/work/parked.md` vs WIP markers, Companion Files rows vs disk (and, with `--since`, new `docs/` files the table doesn't list), broken `docs/` cross-references. Errors stop the save: surface them, because a save that fails validation spreads drift.
   - `uv run {skill-root}/scripts/check-memory-health.py "{project-root}"` — oversized identity or companion files, and standing files that are being appended to.

8. **Act on what's left** — these are independent; do the ones that apply:
   - **Findings from step 7.** Fix sync drift in one batch (a playlist YAML missing a new song, a stale catalog count, a COMPLETED WIP still listed as parked, an untracked companion file). Present them together: *"Found three loose ends — want me to fix them all, go one by one, or skip?"* Each one is also a sign that sync-at-the-point-of-change slipped; tighten that next session. The per-band playlist YAML is the band's single source of truth for its sequence (the suno-band-profile-manager skill's `references/playlist-yaml.md`).
   - **Oversized files.** A standing file longer than a screen → find the section being appended to and rewrite it as what is true now. A companion file over budget → offer the owner a compaction pass; don't do it unasked.
   - **WIP completion.** `uv run {skill-root}/scripts/scan-wip-status.py "{project-root}" --format json`. For an active WIP with a `correlation_warning` (its working title matches a published song), ask whether to mark it COMPLETED (`references/reconcile.md` → "The COMPLETED WIP convention" has the marker format).
   - **Behavioral corrections.** Any correction the owner gave this session that didn't reach `docs/mac-preferences.md` in the turn it landed — append it now.
   - **Production patterns.** After create or refine cycles, `uv run {skill-root}/scripts/songbook-catalog.py "{project-root}" --band {band-slug} --format json` gives model and slider tallies; judge whether a repeat is a pattern worth recording ("Weirdness 55 on your last three — your sweet spot?") and, on the owner's yes, add it to `docs/suno-production-patterns.md` as their finding, not a universal rule.
   - **Evolution (light, optional).** Did anything shift how Mac shows up, or what lands with the owner? One line in PERSONA.md's Evolution Log or BOND.md's Notes Toward the Bond. Durable behavioral rules still go to `docs/mac-preferences.md`.
   - **Renames.** If a song title, band name or playlist order changed, load `references/reconcile.md` for the full reconciliation.

9. **Travel triage, then stamp.** The sanctum stays on this machine. If anything durable about the owner or the craft lives only in the sanctum, give it a home in `docs/` (the voice file, `docs/mac-preferences.md`, `docs/suno-production-patterns.md`). Then write today's date to `memory/.tended`.

## Output

Confirm in Mac's voice with a short recap:

"Memory saved. Here's what we covered:
- {2-4 bullets: songs created or refined, preferences discovered, profiles updated}
- Ready to pick up right here next time."

If the owner works across machines, offer the portable sync now — after the save, so it captures everything: `bash {project-root}/scripts/pack-portable.sh "{project-root}"`. Then carry on with whatever they want next.
