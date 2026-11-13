# Headless Contract

No user is in the room: every call a user would make is made here, recorded in `decision_log`, and returned for the caller to accept. `{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`). Every script runs as `uv run {skill-root}/scripts/<name>.py`; `playlist_sequencing_data.py` and `batch_full_analysis.py` take `--project-root {project-root}`, so no path depends on the working directory.

## Input

- `--playlist {docs}/{band-slug}-playlist.yaml` (required). Without it, return the blocked contract.
- `--locked "Song A > Song B > Song C"` (optional, repeatable): an arc that must stay together and in order. These add to any `locked_arcs:` in the playlist YAML, and with no user to ask they are the only other arcs the run knows about. Pass every one of them to every `validate_sequence.py` call below.
- A caller asking for a catalog-wide pass: after step 3, also run `uv run {skill-root}/scripts/batch_full_analysis.py --audio-dir <audio_dir> --project-root {project-root}`, where `<audio_dir>` is the `audio_dir` the sequencing report names (the folder the playlist's files resolved to, which is `{docs}/audio/{band-slug}` only when that folder exists and nothing overrides it). Status `partial`: name its `failed[]` in `warnings`. Exit 1 or 2: skip the pass and log that in `decision_log` with the script's `error`. Exit 3: its report printed and only a file went unwritten, so use the report and add the unwritten file to `warnings`.

## Run

1. `references/playlist-sequencing-methodology.md` binds this run (read it fully now unless activation already did): the gates in "Process for Reviewing a Playlist", "Transition Discipline", "Cause and Effect at the Seam", "Locked Arcs" and "Thematic Verification". For a full sequence of five or more tracks, `references/album-craft.md` binds it too, on the same terms.
2. Run `uv run {skill-root}/scripts/validate_sequence.py {playlist} --locked "..."` on the current order. It reports every locked arc and whether it is intact.
   - Exit 2 names a broken input: return blocked with that reason.
   - Exit 1 means the current order itself fails a check: copy its `errors[]` into `decision_log`. A duplicated track name, a locked arc naming a track the playlist doesn't have, or a `locked_arcs:` item with fewer than two tracks returns blocked with that error as `reason`, because no order can pass step 6 until the input is fixed. A locked arc the current order already has split or out of order doesn't stop the run: the order you return holds the arc together and in order (step 6 passes nothing less), and `trade_offs` says the playlist had it broken.
3. Make this run's scratch folder with `mktemp -d` (`<scratch>` below; every scratch file goes there) and run `uv run {skill-root}/scripts/playlist_sequencing_data.py --playlist {playlist} --project-root {project-root} -o <scratch>/sequencing-run.json`. On exit 0 or 3 the report is in that file; on exit 1 or 2 the failure JSON is on stdout.
   - Exit 1 (unreadable playlist, duplicate track names, or no track analyzed): return blocked with the script's `error`.
   - Exit 2 (no audio dependencies): with an archive on disk, sequence from it and log that; without one, return blocked with `missing: ["audio_analysis"]`.
   - Exit 3 (the analysis ran, but the archive or the companion could not be written; `artifacts` gives the `reason`): carry on from the report and add that reason to `warnings`.
   - `artifacts.archive.status` `kept-prior`: the drops would have shrunk the baseline. Leave it kept and log it: `--force-archive` needs a user to accept the shorter list.
   - `<archive>` in step 6 is `<scratch>/sequencing-run.json`, this run's own report, whatever `artifacts.archive.status` says: after `kept-prior` or `error` the archive on disk holds an earlier run's measurements, or none. Only after exit 2 is `<archive>` the archive on disk you sequenced from: the playlist's file under `{docs}/audio-analysis/playlists/`, named for the album's slug.
4. With no user to confirm by ear, take tempo from `felt_bpm:` where the YAML records it. Where `felt_bpm_check` is true, sequence on the measured tempo and log it as an assumption.
5. Do the thematic read yourself (methodology, "Thematic Verification"), or leave out thematic claims and log that you did.
6. Check the order, and then the words about it, with `validate_sequence.py`, in the order below. Every call passes every `--locked` arc again, and none passes `--write`: the playlist YAML stays unchanged, and the caller decides whether to apply the order.
   1. **The order passes.** Write the recommended order to `<scratch>/order.txt`, one name per line, and run `uv run {skill-root}/scripts/validate_sequence.py {playlist} --order <scratch>/order.txt --archive <archive>`. Fix the order and re-check. Done when the check exits 0, so the order returned is one that passed. If a third check still exits 1, or any check exits 2, return blocked with the validator's `errors` (or `error`) as `reason`: the constraints can't all be met, and trying again would loop.
   2. **Seams are described in the validator's labels.** Its `seams` carry each transition's measured `bpm_quality` and `loudness_quality`, new seams included. Describe a seam with those labels; call one smooth, seamless or clean only when both labels read `smooth` (an `ok` tempo label, 3–6%, is a noticeable change, not a smooth one); never call a `jump` seam the best or strongest; and name the percentage of any `jump` beside your placement reasoning. A seam row that carries `missing` (a neighbour was dropped, or is absent from the archive) is unmeasured, as is the tempo of one whose `bpm_quality` is `unknown`: say so, list the seam in `flagged_transitions`, and describe it with no label. Done when every seam the rationales and trade-offs mention is described by its labels, and every `jump` carries the label's percentage.
   3. **Claims about rejected slots come from the slot table.** Run the check with `--slot-table "<track>"` (and `--archive`): it lists every slot the track could take, the seams each makes, the seam it replaces and any locked arc it splits. Claims about slots you rejected rest on those labels. A comparative claim ("the only slot that adds no jump", "every other slot is worse") comes from the table's `slot_summary`, never from your own scoring, and says its scope: `slots_at_fewest` counts only slots that keep every locked arc ("the only arc-safe slot with no new jump"); `net_by_slot` has the rest. Done when each claim about another slot matches a slot-table row or a `slot_summary` field; a reply that makes no such claim needs no slot table.
   4. **Key positions are accounted for.** Positions 1, 4, 7 and 10 take the strongest songs (album-craft). Done when `trade_offs` names every one of those positions that a locked arc or a seam forced a weaker song into.
   5. **The words pass.** Write the exact `rationale` texts and `trade_offs` you will return (copied in, not a summary) to `<scratch>/rationale.txt` and run the check again with `--rationale <scratch>/rationale.txt`: it fails on any clause that calls a `jump` seam smooth, clean or the best, judging a clause about level on the loudness label and one about tempo on the tempo label. Done when it exits 0 on the text exactly as it will be returned; any later edit to that text needs another run. A clause that still fails after two rewrites is cut.
   6. **The final check is on what you return.** Run the `--order` check once more on the exact order you return, with `--brief` (only the fields a reply cites, so nothing needs filtering). Read its output from stdout or from a path you named (never the newest file in a shared `/tmp` folder), keep `seams` and `locked_arcs` whole, and take the figures you cite from them, as the labels give them (a label's percentage, never one you work out). Done when this run exits 0 and the reply's order, `locked_arcs_respected` and every cited figure match its output.

**Work silently and finish everything:** send no message before the reply: every tool call goes out with no words beside it (no "Now emitting…", no progress note), and run no background commands: every tool call finishes before you return, so nothing reports after the reply. Scratch files go in a fresh `mktemp -d` folder, never a fixed `/tmp` name another run could share.

Once the final check has passed and before the reply, run `{workflow.on_complete}` if it's set; the JSON reply stays the last thing sent.

## Success

**The reply is the JSON object alone:** no text before or after it and no code fence, so a script can parse it. Anything worth saying goes in a field the schema below has (`warnings`, `decision_log`, `trade_offs`); add no other fields.

```json
{
  "status": "complete",
  "album": "string",
  "recommended_sequence": [{"position": 1, "name": "string", "rationale": "string"}],
  "locked_arcs_respected": ["Song A > Song B"],
  "dropped_tracks": [{"name": "string", "reason": "string"}],
  "flagged_transitions": [{"from": "string", "to": "string", "issue": "string"}],
  "trade_offs": ["string"],
  "arc_shape": "the album's energy shape in a phrase (e.g. an M of two peaks with a valley to breathe, a front-loaded double peak with a contemplative descent)",
  "playlist_yaml_changed": false,
  "artifacts": {"archive": {"path": "string", "status": "written"}, "companion": {"path": "string", "status": "written"}},
  "decision_log": [{"call": "string", "reason": "string"}],
  "warnings": []
}
```

- `locked_arcs_respected[]`: from the final check's `locked_arcs` (step 6.6), each `intact` arc joined with " > ".
- `dropped_tracks[]`: copy the sequencing script's `dropped[]` names and reasons, so a short list is never mistaken for the whole playlist.
- `flagged_transitions[]`: the seams the methodology judged jarring or degraded, worst first, and every unmeasured seam (step 6.2). On a re-eval, the script's `compare.seam_changes` marked `worse` go here too.
- `artifacts`: copy the sequencing script's `artifacts` block as it came. When you sequenced from an existing archive without running the script, it is `{"archive": {"path": "<the archive you read>", "status": "read"}, "companion": null}`.
- `arc_shape`: name the shape the whole order makes in a few words (album-craft's "Arc shape": a W, an inverted U, a front-loaded double peak), never a slot-by-slot walk (the walk belongs in the rationales). Name it from the energies' peaks, as album-craft does: two peaks with a valley is an M, three peaks with two valleys a W.
- `warnings[]`: what the caller should know that isn't a call: BMad not set up here (one entry), a config resolver that failed, a missing config value taken as its default, each track in the sequencing report's `felt_bpm_ignored[]` (its `felt_bpm:` isn't a positive number, so its measured tempo was used), an archive or companion that wasn't written, a catalog pass's `failed[]`.
- `decision_log[]`: one entry for every call made without the user. That includes the current order's `errors[]` from step 2 and any split arc you put back together, any locked-arc break you declined (recorded, not acted on), each track sequenced on measured tempo with no ear check (named one by one, exactly the tracks the sequencing data flags `felt_bpm_check` true, no more), any thematic claim you left out, a non-null `tempo_source_note`, a `kept-prior` archive, and a catalog pass you skipped.

## Blocked

```json
{"status": "blocked", "missing": ["playlist_yaml"], "reason": "one-line cause", "decision_log": []}
```

`missing` names what is needed: `playlist_yaml` (no `--playlist`, the file is unreadable, two of its tracks share a name, or a `locked_arcs:` item is too short), `audio_files` (nothing analyzed), or `audio_analysis` (no dependencies and no archive). It is `[]` when nothing is missing and the inputs can't be met together: a `--locked` arc naming a track the playlist doesn't have, or an order that no third check passed.
