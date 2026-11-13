**Language:** Use `{communication_language}` for all output.

**Preference shard first.** If `{project-root}/docs/mac-preferences-file-hygiene.md` exists (the wake lists it under `voice_context.preference_shards`), read it in full before anything else here: it holds the owner's saving, syncing, durable-file and release rules.

# Reconcile References

Reconciliation is a service, not a gate: offer it, run it if the owner accepts, report what changed, and never hold up their work to force it. It is a quick consistency pass over the known files, not a full audit.

The outcome: after authoritative data changed in one file (a song title or status, a playlist order, a band or profile name, a tier or preference, a file that was deleted), every other file that names the old value either agrees with the new one or keeps the old one on purpose, and the owner approved each change before it was written.

`{songbook_folder}` and `{band_profiles_folder}` are the wake's `config` values, full paths already. Search and write only inside Mac's access boundaries (the Dominion section of the sanctum's `CREED.md`).

## Authoritative Sources

| Data | Authoritative Source | May Be Referenced In |
|------|---------------------|---------------------|
| Song title | Songbook entry (`{songbook_folder}/{band}/{song}.md`) | Per-band playlist YAML, playlist ordering doc, voice context, sanctum `memory/work/` and `memory/chronology/`, WIP files, companion files |
| Song status (WIP/published) | Songbook entry | Voice context (WIP sections, catalog), sanctum `memory/work/current.md` and `parked.md`, per-band playlist YAML, WIP files (marked COMPLETED) |
| Playlist order & track numbers | **Per-band playlist YAML** (`{band-slug}-playlist.yaml` in the folder that holds `{band_profiles_folder}`, `docs/` by default) | Playlist ordering doc (derived narrative companion), voice context (catalog section), songbook placement notes, position references in the sanctum's `memory/` files, script-generated sequencing companion and archive (their paths come from the sequencer's `artifacts` block; they're slugged from the playlist's `album:`) |
| Band profile (genre, vocal, name) | Band profile YAML (`{band_profiles_folder}/*.yaml`) | Voice context, songbook entries referencing profile values, sanctum `memory/bands/active.md`. The band profile YAML carries no `playlist:` block — playlist data lives in the per-band playlist YAML, whose format the suno-band-profile-manager skill owns. |
| Tier/preferences | Sanctum `memory/owner/preferences.md` / config (the `modules.suno` answers, which `bmad setup suno` shows and changes) | Voice context (Suno Setup section), band profile tier field |
| Voice file location | The file itself (`docs/voice-context-*.md`) | Pre-activate expectations, the sanctum's `memory/` files that name it |

## Find the stale references

Run the search with the old value, and the new one for a replacement preview:

```
uv run {skill-root}/scripts/find_stale_refs.py "{project-root}" --old "<old value>" --new "<new value>" --format json
```

- `hits[]` are content matches across the songbook, band profiles, playlist YAMLs and docs, voice files and their Companion Files, WIPs and the sanctum's `memory/`, each with file, line, context and match kind (`exact`, `casefold`, `subtitle`). `--partial` also matches the first significant word of a multi-word value; `--include-raw` also searches the sanctum's `raw/`, which is usually history rather than drift.
- `named_by_old[]` lists every file and folder (`{path, kind: file | folder}`) whose own name carries the old value or its slug: the band's songbook folder, its playlist YAML, its profile, its coverage doc, its audio-analysis folder, a sanctum memory file. A content search cannot see a name, so these need renaming too.
- `missing_targets[]` are `docs/...` references whose target file is gone, which is how entries left behind by a deleted file show up.

Sequencing docs refresh themselves between their AUTOGEN markers, so leave the text inside them alone.

Then run `uv run {skill-root}/scripts/validate_sanctum.py "{project-root}" --format json` for the parity checks: `playlist_drift` (playlist and songbook name different songs), `voice_catalog_drift` (a stale published count), `companion_missing` (a Companion Files row pointing at nothing), `pending_drift` and `cross_reference_missing`.

Your part is the judgment: which hits are intentional history ("formerly known as", a dated session note) and which are drift; whether a partial match really means this song or band (ask when it could mean something else); and whether any count-bearing description ("34 tracks", "577 lines") went stale because its content changed.

## Confirm, then apply

Show the owner every proposed update before writing anything: each hit's file, line and context, each file or folder to rename, and the new value. They may take them all at once, review them one by one, leave some as they are, or skip the pass.

Apply each confirmed update in context, not by blind find-and-replace, then report what changed ("Updated 3 files, renamed 1, marked 1 WIP COMPLETED").

## Cases with their own rule

- **Playlist reordering.** When track numbers change, every track-number reference in the voice context's catalog section changes with them. Present the full before and after for that section instead of line-by-line changes.
- **A WIP whose song published.** Mark each `docs/wip-*` file that the published song came from COMPLETED and keep it; `references/completed-wip.md` has the marker format and the reason WIPs are kept.
- **Band or profile rename.** The widest change: every songbook entry names the profile in its frontmatter, and `named_by_old[]` lists the files and folders still carrying the old slug. Tell the owner the scope before proceeding.
