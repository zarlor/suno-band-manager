**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`

---
name: save-memory
description: Explicitly save current session context to memory
menu-code: SM
---

# Save Memory

Immediately persist the current session context to memory.

**Headless-eligible:** false — save-memory distills the *live conversation* into the sanctum, and several steps (the Handoff Checkpoint, the companion-files audit, the "is this worth remembering?" judgment) require the in-session context and the owner's confirmation. A headless invocation returns `{status: blocked, reason: "interactive-only"}`. Headless capabilities that produce durable state run their *own* persistence inline (per `references/activation.md` Headless Activation) rather than calling save-memory.

## Process

1. **Capture unsaved creative work** — Before saving memory, check the current conversation for creative fragments that haven't been written to files yet:
   - Brainstorming discussions that produced potential lyrics, images, or concepts for a song (even if the song doesn't have a name yet)
   - Working fragments, lines, or structural ideas that emerged from conversation
   - New WIP concepts that were discussed but never written to `docs/wip-*.md`
   
   If unsaved creative work is found, write it to a WIP file (`docs/wip-{working-title}-fragments.md`) BEFORE proceeding with the memory save. This ensures the portable sync archive captures everything. Surface what you're saving: "We had some creative fragments in our conversation that aren't on disk yet — let me save those to a WIP file before we pack up."

   **This step is critical for portable sync** — conversation content doesn't survive session boundaries or machine transitions. If it's not in a file, it's lost.

1a. **Append raw session narrative to `sessions/YYYY-MM-DD.md`** — The v2 sanctum is two-tier: raw per-session narrative lives in `{project-root}/_bmad/_memory/band-manager-sidecar/sessions/{today's date}.md` (NOT loaded on rebirth), and the curated live state is distilled *up* into `MEMORY.md` (loaded on every rebirth). Before touching `MEMORY.md`, append today's raw "what happened" narrative — the running Current/Prior Work detail, the workshop play-by-play, the per-publish detail — to today's session file (create it if this is the first save of the day). This is the durable record; nothing is lost here even when `MEMORY.md` stays tight. Keep the raw detail here; keep only the distilled live state in `MEMORY.md`.

2. **Read current MEMORY.md** — Load existing curated context from `{project-root}/_bmad/_memory/band-manager-sidecar/MEMORY.md`

3. **Distill the current session up into MEMORY.md** — Update the curated live state (NOT a full re-dump of the raw narrative, which lives in `sessions/`):
   - Active song work (style prompt, lyrics, parameters, model, band profile in use)
   - User preferences discovered or changed this session
   - Current interaction mode preference
   - Any band profile updates pending
   - Production knowledge discovered (see Step 2b)
   - Behavioral preferences articulated this session (see Step 2c)
   - Next steps to continue

   **Keep `MEMORY.md` tight (target <~200 lines).** Distillation, not accumulation: if a Current/Prior Work block has aged into history, push its detail down to `sessions/` and leave only a one-line pointer in `MEMORY.md`. `check-memory-health.py` flags `MEMORY.md` when it blows its line bound.

   ### 2c. Behavioral preference writes

   Distinct from musical preferences — if the user articulated a durable behavioral correction this session (how Mac communicates, pacing, framing, conversation discipline), that should already have been appended to `docs/mac-preferences.md` in the same turn the correction landed (per `creed.md` "Sync at the point of change"). At save-memory time, scan the session for any behavioral correction that landed but didn't get written to `docs/mac-preferences.md` — that's a sync gap to fix now. Behavioral preferences belong in `docs/mac-preferences.md` (portable, travels in sync), NOT in agent-harness per-machine memory caches (which don't travel). See `references/memory-system.md` → `docs/mac-preferences.md` section for the full rationale.

   ### Handoff Checkpoint (before writes)

   Before writing to any memory files, surface a brief summary of what will be saved:

   > "Here's what I'd save: **[2-4 bullet summary of changes to MEMORY.md, today's `sessions/` file, patterns.md, chronology.md]**. Sound right?"

   Wait for confirmation. The user may want to exclude something or add context. This is especially important for patterns.md where personal preferences are being recorded — the user should control what gets stored as a "pattern" about them.

   ### 2b. Production knowledge check

   After create-song or refine-song cycles, check for discoverable production patterns:
   - Repeated slider settings across successful songs ("You've used Weirdness 55 on your last 3 songs — want me to note that as your sweet spot?")
   - Genre term combinations that consistently landed
   - Metatag patterns that achieved intended effects
   - What settings/approaches led to first-generation success vs. iteration

   Store these in patterns.md under the Production Knowledge section — as the user's personal findings, not universal prescriptions.

3d. **Update `INDEX.md` if a new organic file was created** — `INDEX.md` is the thin sanctum map: every organic file gets a row, and an unlisted file is a lost file. If this session created a new organic sanctum file (a new `_collection_*.txt`, a new learned `capabilities/` prompt, etc.), add its row to `INDEX.md` in the same save. (Routine `sessions/` and the ALLCAPS skeleton files don't need new rows — they're already mapped.)

4. **Write updated MEMORY.md — narrative sections only** — Update ONLY the narrative sections: Current Work, Pending / Parked Work, Session History, User Preferences, Module State, Default Exclusions, Active Band Profiles. Do NOT hand-edit the Recently Published or Catalog Status sections — they live between `<!-- derived:recently-published:start -->` / `end` and `<!-- derived:catalog-status:start -->` / `end` markers in `MEMORY.md` and are regenerated by script in Step 4a.

4a. **Regenerate derivable sections (automated)** — Run `uv run scripts/regenerate-index-sections.py "{project-root}"` to rewrite the Recently Published and Catalog Status sections **in `MEMORY.md`** from songbook ground truth. This reads every `docs/songbook/**/*.md` frontmatter + body `**Status: LOCKED/PUBLISHED` markers, sorts published songs by publish date, and replaces only the content between the derived-section markers. Narrative sections are preserved unchanged.

   **If the script reports missing markers**, `MEMORY.md` needs one-time migration. Rerun the script with `--migrate`: `uv run scripts/regenerate-index-sections.py "{project-root}" --migrate`. This wraps the existing `## Recently Published` and `## Catalog Status` sections with the required marker pairs in-place, then proceeds with regeneration. If `MEMORY.md` is missing either heading entirely, the migrate pass prints which heading is missing and exits — add the heading (see `references/init.md` for the template) and rerun.

4a-bis. **Regenerate the genre-coverage index (when the catalog changed)** — If this session published a song, added a songbook entry, or otherwise changed what a band has actually recorded, regenerate the per-band coverage index that the Catalog Verification Discipline greps against:

   ```
   uv run scripts/genre-coverage.py "{project-root}" --timestamp "{today's date}"
   ```

   This scans every band's songbook style-prompt anchors AND the band-profile catalog (reference_tracks + per-song genre_applied + filtered prose) and writes `docs/{band}-genre-coverage.md` with an `<!-- AUTOGEN: genre-coverage -->`-bounded section it rewrites in place (narrative around it is preserved). Limit to one band with `--band {band-slug}` if only that band changed; omit `--band` to refresh all. Add `--format json` if you want a machine-readable run summary (entry counts per band) instead of the text line.

   This keeps `docs/{band}-genre-coverage.md` current so the *next* session opens with an already-accurate coverage index to consult — turning the Catalog Verification grep into ground truth on disk rather than a from-memory recollection. If `docs/songbook/` doesn't exist yet (empty catalog, first session), the script exits cleanly with nothing to do — skip this step.

4b. **Validate the result** — Run `uv run scripts/validate-sidecar.py "{project-root}"` to confirm the regenerated `MEMORY.md` derived sections agree with songbook ground truth. Zero errors means the sanctum is clean; warnings are informational (pre-existing content gaps like missing body Status markers on older songs). If the validator reports errors, stop and surface them — a save that fails validation would propagate drift.

5. **Checkpoint other files if needed (parallel batch)** — These writes are independent; run in parallel:
   - `patterns.md` — Add new musical preferences discovered (genre tendencies, vocal preferences, exclusion patterns, creativity level preferences) and production knowledge (see Step 3b)
   - `chronology.md` — Add session summary if significant work was done

   **Pre-write sync check (before chronology):** Before writing the session summary to chronology.md, scan the session's writes for any cross-referenced updates that didn't land in the same batch as their triggering edit. Example triggers to look back on:
   - A new `docs/` file was created — did the voice file's Companion Files table get the entry in that batch?
   - A songbook entry was added/updated — did the **per-band playlist YAML** (`docs/{band-slug}-playlist.yaml`) and voice catalog count get updated in that batch? **This is REQUIRED, not optional** — the per-band playlist YAML is the single source of truth for the band's sequence; not updating it means the next session pulls a stale playlist (see `suno-band-profile-manager/references/profile-schema.md` "Per-Band Playlist YAML" section).
   - An `INDEX.md` map row or path changed — did any doc referencing that path get updated in that batch?
   - A WIP file was marked COMPLETED — did the `MEMORY.md` Pending / Parked Work section drop it in that batch?

   If any mismatch surfaces, surface it here rather than letting the Step 6 audit catch it. The chronology write is the last narrative write of the session — it's the correct moment to self-check that cross-file invariants held at each edit, not just at save time.

6. **Companion files audit (backstop, bidirectional)** — If the user has a voice file, run both directions. Per `creed.md` "Sync at the point of change," this audit should normally find nothing — fix any drift it surfaces in the same write batch.

   **Forward (new files need entries):** Check whether any new `docs/` files were created during the session that aren't in the voice file's Companion Files table. If so, offer to add them: "I notice we created [file] this session — want me to add it to your companion files index?" Include: file path, one-line description, and when-to-load trigger phrase. (Normally the entry would have been added in the same batch that created the file; catching it here means the batch missed it.)

   **Reverse (stale entries in the table):** Check every entry in the Companion Files table:
   - Does the referenced file still exist on disk? If not, the entry is stale — offer to remove it (the file may have been deleted during this or a previous session without the table being updated)
   - Does the entry contain a stale count or description? (e.g., "34 tracks" when the playlist now has 36, or "The Slide — firearm metaphor..." when The Slide is now a published song with a songbook entry). If so, offer to update the description or move the entry to point at the authoritative file (e.g., the songbook entry instead of a deleted WIP file)
   - **Is the entry a WIP file that's now resolved?** If the Companion Files table includes a `docs/wip-*.md` entry, check the `scan-wip-status.py` output below — a file reported `status: completed` is resolved, so its companion-files entry is stale — offer to remove it from the table. Resolved WIPs are historical records, not active reference material, and don't belong in the "load on demand" companion files table.

   Present all findings in one handoff: "I checked the companion files table — here's what I found: [X new files to add, Y stale entries to remove, Z entries with outdated descriptions]. Want me to fix them all, review each, or skip?" If findings are non-empty, also flag it to yourself as a point-of-change sync gap so the next session's edit-time behavior tightens up.

   **WIP completion scan (post-publication) — run the script, keep the judgment:** Run `uv run scripts/scan-wip-status.py "{project-root}" --format json`. It globs `docs/wip-*.md`, reads the `## STATUS: COMPLETED` marker, and correlates each *active* (unmarked) WIP against published songbook titles — emitting per file `{path, status, completed_as, published_date, songbook_ref, correlation_warning}`. You do NOT hand-scan the WIP files. For any file with a non-null `correlation_warning` (an active WIP whose working title matches a published song), surface it: "I notice `{path}` looks like the source fragments for **{matched song}** that's already published. Mark it COMPLETED? (Load `references/reconcile.md` → 'The COMPLETED WIP convention' for the marker format.)" Apply the marker if confirmed — the marker-writing stays with you; the scan/match does not.

7. **Reference reconciliation check** — Before finalizing the save, do a quick consistency scan:
   - The Step 4b validator covers **sanctum-level** drift automatically (`MEMORY.md` derived sections vs. songbook ground truth) **and markdown cross-references under `docs/`** (`cross_reference_missing` findings flag broken inline-code refs like `` `docs/X.md` `` and markdown links like `[text](X.md)` whose targets don't exist on disk). If it passed with no `cross_reference_missing` warnings, the sanctum and cross-refs are clean.
   - If the validator reports `cross_reference_missing` warnings, surface them to the user and either create the target files, rephrase the references as future-intent ("to be logged in X" instead of "logged in X"), or remove them. Don't silently let them propagate to the sync.
   - For **cross-file** drift the validator doesn't check (voice context companion files, playlist ordering docs, WIP file status markers): if any song titles, band profile names, or playlist orders changed during this session, load `references/reconcile.md` and run reconciliation.
   - Compare the values being written to chronology.md against what already exists in the voice context file and songbook — flag any inconsistencies.
   - This step is fast (just a scan) and only triggers the full reconciliation handoff if stale references are actually found.
   - If nothing changed this session, skip silently.

## Output

Confirm save with a brief session recap in Mac's voice:

"Memory saved. Here's what we covered:
- {2-4 bullet points summarizing the session: songs created/refined, preferences discovered, profiles updated}
- Ready to pick up right here next time."

**When complete:** Return to the main menu or continue with the user's next request.
