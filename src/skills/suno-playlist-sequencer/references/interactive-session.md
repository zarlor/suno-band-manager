# Interactive Session

The record an interactive run keeps and how the accepted order lands. `{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`); the playlist is `{docs}/{band-slug}-playlist.yaml`. Every script runs as `uv run {skill-root}/scripts/<name>.py`; the sequencing script takes `--project-root {project-root}`, so no path depends on the working directory.

## Workspace and resume

The workspace, `{workspace}`, is `{workflow.workspace_output_path}` with `{output_folder}`, `{active_initiative}` and `{band-slug}` filled in; `{output_folder}` and `{active_initiative}` come from activation's config load, and with no active initiative that segment is dropped. A workspace folder already at `{docs}/{band-slug}-playlist-sequencing`, the earlier default, is continued where it is, so a sequencing job in progress keeps its record.

If the workspace holds a `.memlog.md`, read it once at intake and treat settled placements as the standing record: raise any conflict with a prior call before changing it. Otherwise run `uv run {project-root}/_bmad/scripts/memlog.py init --workspace {workspace} --field topic="{album} sequencing"`.

If `{project-root}/_bmad/scripts/memlog.py` doesn't exist (BMad isn't set up here), keep the same record by hand: create `{workspace}/.memlog.md`, append each entry below to it as one dated line that starts with its type, and say once that setting up BMad (the `bmad` skill) restores the tool.

## Logging

Append with `uv run {project-root}/_bmad/scripts/memlog.py append --workspace {workspace} --type <type> --text "<the entry>"` (`--text` is required):

- `--type decision` for each placement, with the alternatives rejected and any locked-arc break the user authorizes.
- `--type event` for the write itself (the YAML rewritten), not another decision, appended only after the `--write` output shows `"written": true` (a separate command, never chained after the write).
- `--type direction` for narrative asides ("that one's really about my dad"), which are often the thematic context a songbook read would otherwise have to find.

When the user confirms a felt BPM by ear, offer to record it as `felt_bpm:` on that track, so the script stops misreading it.

## Sign-off

1. Write the accepted order to `{workspace}/accepted-order.txt`, one name per line.
2. Run `uv run {skill-root}/scripts/validate_sequence.py {docs}/{band-slug}-playlist.yaml --order {workspace}/accepted-order.txt --archive <archive>`, adding `--locked "A > B"` for every arc the user named that isn't in the YAML. Show the moves it previews (when step 3 writes without asking again, the moves still go in your reply, beside the write) and fix any error it names.
   - `<archive>` is the archive JSON you sequenced from, under `{docs}/audio-analysis/playlists/` (the path `playlist_sequencing_data.py` reports under `artifacts`), when this session's run reported its status as `written`. After any other status (`kept-prior`, `error`, `skipped`) that file holds an earlier run's measurements or none: run `uv run {skill-root}/scripts/playlist_sequencing_data.py --playlist {docs}/{band-slug}-playlist.yaml --project-root {project-root} --no-archive --no-companion --no-compare -o {workspace}/sequencing-run.json` and pass that file as `<archive>`.
   - Its `seams` label every transition, so use those labels when you describe one. A seam that carries `missing` instead of labels is unmeasured (a neighbour was dropped or isn't in the archive): say so rather than describing it.
3. After the user confirms, run it again with `--write`. It rewrites only the `tracks:` order, and only when every check passes. A clear go-ahead given before the preview ("yes, write it") counts as confirmation when the preview passed and showed nothing they haven't already heard about. "Heard about" means the proposal named it: each new seam whose tempo or loudness label isn't `smooth` or whose key relation is distant, and each move. If the preview shows one the proposal didn't name, show it and ask once; if everything was named, write without asking again. If the write's output says `"rewrite": "re-rendered"`, tell the user that comments and quoting inside the `tracks:` list were not kept (the list wasn't a plain block list, so it was written out again).
4. Re-run the sequencing script, `uv run {skill-root}/scripts/playlist_sequencing_data.py --playlist {docs}/{band-slug}-playlist.yaml --project-root {project-root} --no-compare` (and `--force-archive` if the user accepted drops), so the archive and companion match the new order. Without the audio on this machine the script can't re-measure: leave the archive as it is, and say that it still lists the old order until the audio is here and that command runs again (give the user the full command).
5. Write the proposal narrative and any saved document in the user's language, then run `{workflow.on_complete}` if it's set.
