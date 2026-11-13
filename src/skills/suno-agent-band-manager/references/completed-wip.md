# The COMPLETED WIP Marker

When a song is published from a WIP fragments file (`docs/wip-*.md`), the file is marked COMPLETED and kept. It is never deleted: the fragments are the record of how the song came to be (the brainstorming that didn't make it, the direction changes, the cut images, the working titles), and the marker is what tells the next session, on this machine or on another after a portable sync, that the file is finished work and not something to pick up.

`{songbook_folder}` is the wake's `config` value, a full path; write the songbook path in the marker relative to the project root.

## The marker

The block goes at the top of the WIP, after the `#` title heading and any `## WIP —` date line, with a `---` rule above and below it and the original fragments unchanged beneath:

```markdown
# <Original WIP title>
## WIP — <original dates>

---

## STATUS: COMPLETED as "<Published Song Title>" — published <YYYY-MM-DD>

This fragments file is preserved as historical record. The song was completed
as **<Published Song Title>** on <YYYY-MM-DD> <brief context: what session,
what band, what musical direction>. See the songbook entry at
`<songbook folder>/<band>/<song-slug>.md` for the finished form, style prompt,
exclude styles, settings, and the full generation log.

**This WIP file is NOT active work — do not list it in pending/parked work.**

---

<original fragments content continues here, unchanged>
```

`scan_wip_status.py` and `validate_sanctum.py` read the `## STATUS: COMPLETED` heading line (the title in double quotes after `as`, the date after `published`) and the backticked songbook path, so keep those as the template has them. The "not active work" line is for the next reader.

Record the WIP's path as `source_wip:` in the songbook entry's frontmatter in the same write, so the scan can tie the two together even after a rename.

## Listing WIPs in `memory/work/parked.md`

Before building or updating the sanctum's `memory/work/parked.md`, run `uv run {skill-root}/scripts/scan_wip_status.py "{project-root}" --format json` and work from its output instead of opening each file: a WIP reported `active` with no warning is pending work, and one reported `completed` is not. That file is where the next session looks for what to work on, so a finished WIP listed there gets picked up as a candidate.

A completed WIP kept in the list for reference goes under its own `### Resolved WIP fragments (historical record only — not active work)` subsection, with the songbook entry it became (`songbook_ref` in the scan). The validator reads a `###` heading containing "resolved" or "historical" as the boundary between active and finished work.

## An unmarked WIP for a published song

The scan's `correlation_warning` (with `correlated_by: source_wip | title`) names an active WIP that looks like the source of a published song. Confirm the song is published by finding its songbook entry, tell the owner in a line ("`docs/wip-X.md` is for a song already published as Y — marking it COMPLETED so it isn't picked up next session"), then apply the block.

When the match isn't certain, ask. The marker asserts that this WIP became that song, and on a WIP still in progress it would hide live work.
