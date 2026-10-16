# Interactive Session

The record an interactive run keeps and how the accepted order lands. `{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`); the playlist is `{docs}/{band-slug}-playlist.yaml`; run scripts from `{project-root}`.

## Workspace and resume

The workspace, `{workspace}`, is `{workflow.workspace_output_path}` with `{docs}` and `{band-slug}` filled in. If it holds a `.memlog.md`, read it once at intake and treat settled placements as the standing record: raise any conflict with a prior call before changing it. Otherwise run `uv run {project-root}/_bmad/scripts/memlog.py init --workspace {workspace} --field topic="{album} sequencing"`.

## Logging

Append with `uv run {project-root}/_bmad/scripts/memlog.py append --workspace {workspace} --type <type> --text "<the entry>"` (`--text` is required):

- `--type decision` for each placement, with the alternatives rejected and any locked-arc break the user authorizes.
- `--type event` for the write itself (the YAML rewritten), not another decision, appended only after the `--write` output shows `"written": true` (a separate command, never chained after the write).
- `--type direction` for narrative asides ("that one's really about my dad"), which are often the thematic context a songbook read would otherwise have to find.

When the user confirms a felt BPM by ear, offer to record it as `felt_bpm:` on that track, so the script stops misreading it.

## Sign-off

1. Write the accepted order to `{workspace}/accepted-order.txt`, one name per line.
2. Run `uv run {skill-root}/scripts/validate-sequence.py {docs}/{band-slug}-playlist.yaml --order {workspace}/accepted-order.txt --archive <archive>` (`<archive>` is the archive JSON you sequenced from, under `{docs}/audio-analysis/playlists/` (the path `playlist-sequencing-data.py` reports under `artifacts`); its `seams` label every transition, so use those labels when you describe one), adding `--locked "A > B"` for every arc the user named that isn't in the YAML. Show the moves it previews (when step 3 writes without asking again, the moves still go in your reply, beside the write) and fix any error it names.
3. After the user confirms, run it again with `--write`. It rewrites only the `tracks:` order, and only when every check passes. A clear go-ahead given before the preview ("yes, write it") counts as confirmation when the preview passed and showed nothing they haven't already heard about. "Heard about" means the proposal named it: each new seam whose tempo or loudness label isn't `smooth` or whose key relation is distant, and each move. If the preview shows one the proposal didn't name, show it and ask once; if everything was named, write without asking again.
4. Re-run the sequencing script with `--no-compare` (and `--force-archive` if the user accepted drops) so the archive and companion match the new order. Without the audio on this machine the script can't re-measure: leave the archive as it is, and say that it still lists the old order until the audio is here and `uv run {skill-root}/scripts/playlist-sequencing-data.py` runs again (give the user the full command).
5. Write the proposal narrative and any saved document in the user's language, then run `{workflow.on_complete}` if it's set.
