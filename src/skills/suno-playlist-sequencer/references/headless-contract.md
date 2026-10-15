# Headless Contract

No user is in the room: every call a user would make is made here, recorded in `decision_log`, and returned for the caller to accept. `{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`); run scripts from `{project-root}`.

## Input

- `--playlist {docs}/{band-slug}-playlist.yaml` (required). Without it, return the blocked contract.
- `--locked "Song A > Song B > Song C"` (optional, repeatable): an arc that must stay together and in order. These add to any `locked_arcs:` in the playlist YAML, and with no user to ask they are the only other arcs the run knows about. Pass every one of them to every `validate-sequence.py` call below.
- A caller asking for a catalog-wide pass: also run `uv run {skill-root}/scripts/batch-full-analysis.py --audio-dir {docs}/audio/{band-slug}`.

## Run

1. Read `references/playlist-sequencing-methodology.md` fully: the gates in "Process for Reviewing a Playlist", "Transition Discipline", "Cause and Effect at the Seam", "Locked Arcs" and "Thematic Verification" bind this run. For a full sequence of five or more tracks, also read `references/album-craft.md`.
2. Run `uv run {skill-root}/scripts/validate-sequence.py {playlist} --locked "..."` on the current order. It reports every locked arc and whether it is intact. Exit 2 names a broken input: return blocked with that reason.
3. Run `uv run {skill-root}/scripts/playlist-sequencing-data.py --playlist {playlist}`.
   - Exit 1 (unreadable playlist, or no track analyzed): return blocked with the script's `error`.
   - Exit 2 (no audio dependencies): with an archive on disk, sequence from it and log that; without one, return blocked with `missing: ["audio_analysis"]`.
   - `artifacts.archive.status` `kept-prior`: the drops would have shrunk the baseline. Leave it kept and log it: `--force-archive` needs a user to accept the shorter list.
4. With no user to confirm by ear, take tempo from `felt_bpm:` where the YAML records it. Where `felt_bpm_check` is true, sequence on the measured tempo and log it as an assumption.
5. Do the thematic read yourself (methodology, "Thematic Verification"), or leave out thematic claims and log that you did.
6. Write the recommended order to a scratch file, one name per line, and check it with `uv run {skill-root}/scripts/validate-sequence.py {playlist} --order <file>`, passing every `--locked` arc again. Fix and re-check until it exits 0, so the order returned is one that passed. Leave out `--write`: the playlist YAML stays unchanged, and the caller decides whether to apply the order.

## Success

```json
{
  "status": "complete",
  "album": "string",
  "recommended_sequence": [{"position": 1, "name": "string", "rationale": "string"}],
  "locked_arcs_respected": ["Song A > Song B"],
  "dropped_tracks": [{"name": "string", "reason": "string"}],
  "flagged_transitions": [{"from": "string", "to": "string", "issue": "string"}],
  "trade_offs": ["string"],
  "playlist_yaml_changed": false,
  "artifacts": {"archive": {"path": "string", "status": "written"}, "companion": {"path": "string", "status": "written"}},
  "decision_log": [{"call": "string", "reason": "string"}]
}
```

- `locked_arcs_respected[]`: from the final step-6 check's `locked_arcs`, each `intact` arc joined with " > ".
- `dropped_tracks[]`: copy the sequencing script's `dropped[]` names and reasons, so a short list is never mistaken for the whole playlist.
- `flagged_transitions[]`: the seams the methodology judged jarring or degraded, worst first. On a re-eval, the script's `compare.seam_changes` marked `worse` go here too.
- `artifacts`: copy the sequencing script's `artifacts` block as it came.
- `decision_log[]`: one entry for every call made without the user. That includes any locked-arc break you declined (recorded, not acted on), any seam sequenced on measured tempo with no ear check, any thematic claim you left out, a non-null `tempo_source_note`, and a `kept-prior` archive.

## Blocked

```json
{"status": "blocked", "missing": ["playlist_yaml"], "reason": "one-line cause", "decision_log": []}
```

`missing` names what is needed: `playlist_yaml` (no `--playlist`, or the file is unreadable), `audio_files` (nothing analyzed), or `audio_analysis` (no dependencies and no archive).

After emitting the success JSON, run `{workflow.on_complete}` if it's set.
