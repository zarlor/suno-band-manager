---
name: reconcile
description: Reconcile stale references across docs and sidecar files after authoritative data changes.
---

**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`

# Reconcile References

When authoritative data changes in one file, stale references may persist in other files. This reference defines how to detect and fix them.

**Headless-eligible:** false — reconciliation hinges on judgment a script can't make (which hits are intentional historical references like "formerly known as" vs. genuine drift, and the in-context replacement) and on the owner's Handoff Checkpoint approval before any write. A headless invocation returns `{status: blocked, reason: "interactive-only"}`. The deterministic parts are scripts a headless caller can run directly for a punch list: `scripts/find-stale-refs.py` (the old-value search), `scripts/validate-sidecar.py` (catalog parity) and `scripts/scan-wip-status.py` (WIP markers).

## When to Run

Reconciliation is triggered after these events:
- A song title changes (rename in songbook, working title → final title)
- A song publishes (WIP → published, audio file added)
- A playlist reorders or adds/removes tracks
- A band profile name or key attributes change
- A WIP is abandoned or superseded
- Tier/preference changes (Free → Pro, default mode changes)
- **Files are deleted** (WIP files, old voice files, obsolete references) — stale entries pointing to deleted files need cleanup in companion files tables, sanctum MEMORY.md/INDEX.md, chronology, and any docs that listed them

## Authoritative Sources

| Data | Authoritative Source | May Be Referenced In |
|------|---------------------|---------------------|
| Song title | Songbook entry (`docs/songbook/{band}/{song}.md`) | Per-band playlist YAML, playlist ordering doc, voice context, sanctum MEMORY.md/chronology, WIP files, companion files |
| Song status (WIP/published) | Songbook entry | Voice context (WIP sections, catalog), sanctum MEMORY.md, per-band playlist YAML, WIP files (marked COMPLETED, never deleted) |
| Playlist order & track numbers | **Per-band playlist YAML** (`docs/{band-slug}-playlist.yaml`) | Playlist ordering doc (derived narrative companion), voice context (catalog section), songbook placement notes, sanctum MEMORY.md position references, script-generated companion at `docs/{band-slug}-playlist-sequencing.md` |
| Band profile (genre, vocal, name) | Band profile YAML (`docs/band-profiles/*.yaml`) | Voice context, songbook entries referencing profile values, sanctum MEMORY.md. The band profile YAML carries no `playlist:` block — playlist data lives in the per-band playlist YAML (the suno-band-profile-manager skill's `references/playlist-yaml.md`). |
| Tier/preferences | Sanctum MEMORY.md / config (`{project-root}/_bmad/config*.yaml`) | Voice context (Suno Setup section), band profile tier field |
| Voice file location | The file itself (`docs/voice-context-*.md`) | Pre-activate expectations, sanctum INDEX.md (map row) |

## Process

### Step 1: Identify the Change

Determine what changed and what the old vs. new values are. The trigger context (create-song post-publish, save-memory, profile edit, etc.) provides this. Note:
- **What** changed (song title, status, playlist order, profile attribute)
- **Old value** (the value being replaced)
- **New value** (the authoritative current value)
- **Source file** (where the authoritative change was made)

### Step 2: Search for Stale References

Run the search script with the old value (and the new one, for a replacement preview):

```
uv run scripts/find-stale-refs.py "{project-root}" --old "<old value>" --new "<new value>" --format json
```

It searches the defined set — songbook entries, band profiles, every `docs/*-playlist.yaml`, playlist ordering and sequencing docs, voice files and every file in their Companion Files tables, `docs/wip-*.md`, and the sanctum's `MEMORY.md`, `INDEX.md`, `chronology.md` and `patterns.md` — and returns each hit with file, line, context and match kind (`exact`, `casefold`, `subtitle`). Add `--partial` to also match the first significant word of a multi-word value, and `--include-sessions` to search the raw `sessions/` logs (usually history, not drift). It also lists `docs/...` references whose target file is gone (`missing_targets`). Sequencing docs refresh themselves between their AUTOGEN markers — don't hand-edit inside them.

Then run `uv run scripts/validate-sidecar.py "{project-root}" --format json` for the parity checks: `playlist_drift` (playlist and songbook name different songs), `voice_catalog_drift` (a stale published count), `companion_missing` (a Companion Files row pointing at nothing), `pending_drift`, and `cross_reference_missing`.

Your part is the judgment: which hits are intentional history ("formerly known as", a dated session note) and which are drift, and whether any other count-bearing description ("34 tracks", "577 lines") has gone stale because its content changed.

### Step 3: Handoff Checkpoint

Surface all proposed updates to the user before writing anything:

> "I found references to **[old value]** in these files:
> - `[file1]` line [N]: [context snippet]
> - `[file2]` line [N]: [context snippet]
>
> Want me to update them all to **[new value]**? I can also do them one by one if you want to review each."

Wait for confirmation. The user may want to:
- Update all at once
- Review and approve each individually
- Skip some (the old reference may be intentional — historical context, "formerly known as")
- Skip entirely

### Step 4: Apply Updates

Apply each confirmed update in context, not by blind find-replace; WIP files of published songs get the COMPLETED marker (below) and are never deleted; then report what changed ("Updated 3 files, marked 1 WIP file COMPLETED").

### Special Cases

**Playlist reordering:** When track numbers change, update ALL track number references in the voice context catalog section. This is a bulk update — present the full before/after for the catalog section rather than individual line changes.

**WIP → Published:** Check for `docs/wip-*` files that reference the published song. **Apply the COMPLETED WIP convention (below)** to mark them resolved — do NOT delete them. The fragments are the historical record of the brainstorming that led to the song. The marker ensures they don't appear as active work on future sessions while preserving their content for reference. Record the WIP path as `source_wip:` in the songbook entry's frontmatter too, so `scan-wip-status.py` can tie the two together even after a rename.

**Band profile rename:** This is the widest-impact change — every songbook entry references the profile by name in frontmatter. Surface the scope before proceeding.

## The COMPLETED WIP convention

When a song is published from a WIP fragments file, mark the file with a standard COMPLETED block at the top — immediately after the title heading, before the original content. This preserves the brainstorming record while signaling to future sessions (and future machines after a portable sync) that the file is not active work. Do NOT delete the file — fragments are creative history (brainstorming that didn't make the song, direction changes, cut images, working-title evolution).

### The exact marker format

Apply this block at the top of the WIP file, immediately after the `#` title heading and any `## WIP —` date line, separated by a `---` horizontal rule above and below:

```markdown
# <Original WIP title>
## WIP — <original dates>

---

## STATUS: COMPLETED as "<Published Song Title>" — published <YYYY-MM-DD>

This fragments file is preserved as historical record. The song was completed
as **<Published Song Title>** on <YYYY-MM-DD> <brief context: what session,
what band, what musical direction>. See the songbook entry at
`docs/songbook/<band>/<song-slug>.md` for the finished form, style prompt,
exclude styles, settings, and the full generation log.

**This WIP file is NOT active work — do not list it in pending/parked work.**

---

<original fragments content continues here, unchanged>
```

**Key elements** (all required):
1. A `## STATUS: COMPLETED as "<title>" — published <date>` heading — this is the machine-readable marker that pending/parked listings should grep for
2. One paragraph of context pointing to the songbook entry (absolute path within the repo)
3. The explicit "NOT active work — do not list in pending/parked work" line — this is the instruction to future Mac sessions
4. A `---` horizontal rule below to separate the marker block from the original fragments

### Listing discipline (sanctum MEMORY.md maintenance)

When building or updating the "Pending / Parked Work" section of the sanctum `MEMORY.md`:

1. **Run `uv run scripts/scan-wip-status.py "{project-root}" --format json`** — the marker scan. It reports each `docs/wip-*.md` file as `status: completed | active`, with `completed_as` / `songbook_ref` for resolved ones and a `correlation_warning` (with `correlated_by: source_wip | title`) for any active WIP that looks like the source of a published song. Read the script output rather than the files.
2. **Skip files reported `status: completed`** — they are resolved, not pending. Partition the script output: `active` (with no warning) → pending; `completed` → resolved.
3. **When including resolved WIPs in the index for historical reference**, put them under a separate "Resolved WIP fragments (historical record only — not active work)" subsection, clearly delineated from active pending/parked work, with a pointer to the songbook entry they became (`songbook_ref` from the script).

The sanctum `MEMORY.md`'s Pending / Parked Work section is the primary place a future Mac session looks to decide what to work on next. A stale WIP listed there will be picked up as a candidate. The scan-before-list rule prevents this — and the script makes the partition a group-by over structured data rather than a per-file read.

### Applying the marker to existing unmarked WIPs

If you encounter a WIP file without a COMPLETED marker but you can confirm the song is published (by finding the songbook entry), apply the marker in context — surface it as a cleanup: "I noticed `docs/wip-X.md` is for a song that's already published as Y. Marking it COMPLETED so it doesn't get picked up next session." Then apply the block and confirm.

Do NOT guess — if you're not sure the song is published, ask. The marker is a positive assertion that the WIP resolved into a specific published song; applying it to a still-active WIP would lose work.

## Scope Boundaries

- Only search within Mac's access boundaries (docs/ and sidecar memory)
- Never modify files outside the known document locations
- If a reference is ambiguous (partial match, could refer to something else), ask rather than assume
- Keep it lightweight — this is a quick consistency check, not a full audit
- Reconciliation is a SERVICE, not a gate — never block the user's workflow to force reconciliation. Offer it, run it if accepted, report results
