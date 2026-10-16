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
6. Write the recommended order to a scratch file in a fresh `mktemp -d` folder (never a fixed `/tmp` name another run could share), one name per line, and check it with `uv run {skill-root}/scripts/validate-sequence.py {playlist} --order <file> --archive <archive>`, passing every `--locked` arc again (`<archive>` is the archive JSON you sequenced from, under `{docs}/audio-analysis/playlists/` (the path `playlist-sequencing-data.py` reports under `artifacts`)). Fix and re-check until it exits 0, so the order returned is one that passed. Its `seams` carry each transition's measured `bpm_quality` and `loudness_quality`, new seams included: describe a seam with those labels, call one smooth, seamless or clean only when both labels read `smooth` (an `ok` tempo label, 3–6%, is a noticeable change, not a smooth one), never call a `jump` seam the best or strongest, and name the percentage of any `jump` beside your placement reasoning. Claims about slots you rejected rest on the same labels: `--slot-table "<track>"` (with `--archive`) lists every slot the track could take, the seams each makes, the seam it replaces and any locked arc it splits. Before returning, write the exact `rationale` texts and `trade_offs` you will return (copied in, not a summary) to a scratch file and run the check once more with `--rationale <file>`: it fails on any clause that calls a `jump` seam smooth, clean or the best, judging a clause about level on the loudness label and one about tempo on the tempo label. The final `--order` check runs on the exact order you return; run it with `--brief` (only the fields a reply cites, so nothing needs filtering), read the output from a path you named or from stdout (never the newest file in a shared `/tmp` folder), keep `seams` and `locked_arcs` whole, and take the figures you cite from them, as the labels give them (a label's percentage, never one you work out). A comparative claim about slots ("the only slot that adds no jump", "every other slot is worse") comes from `--slot-table`'s `slot_summary`, never from your own scoring, and says its scope: `slots_at_fewest` counts only slots that keep every locked arc ("the only arc-safe slot with no new jump"); `net_by_slot` has the rest. Every `jump` you describe carries the label's percentage. Positions 1, 4, 7 and 10 take the strongest songs (album-craft); when a locked arc or a seam forces a weaker song into one, say so in `trade_offs`. Leave out `--write`: the playlist YAML stays unchanged, and the caller decides whether to apply the order.

**Work silently and finish everything:** send no message before the reply: every tool call goes out with no words beside it (no "Now emitting…", no progress note), and run no background commands: every tool call finishes before you return, so nothing reports after the reply. Scratch files go in a fresh `mktemp -d` folder, never a fixed `/tmp` name another run could share.

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

- `locked_arcs_respected[]`: from the final step-6 check's `locked_arcs`, each `intact` arc joined with " > ".
- `dropped_tracks[]`: copy the sequencing script's `dropped[]` names and reasons, so a short list is never mistaken for the whole playlist.
- `flagged_transitions[]`: the seams the methodology judged jarring or degraded, worst first. On a re-eval, the script's `compare.seam_changes` marked `worse` go here too.
- `artifacts`: copy the sequencing script's `artifacts` block as it came. When you sequenced from an existing archive without running the script, it is `{"archive": {"path": "<the archive you read>", "status": "read"}, "companion": null}`.
- `arc_shape`: name the shape the whole order makes in a few words (album-craft's "Arc shape": a W, an inverted U, a front-loaded double peak), never a slot-by-slot walk (the walk belongs in the rationales). Name it from the energies' peaks, as album-craft does: two peaks with a valley is an M, three peaks with two valleys a W.
- `warnings[]`: what the caller should know that isn't a call: BMad not set up here (one entry), a missing config value taken as its default.
- `decision_log[]`: one entry for every call made without the user. That includes any locked-arc break you declined (recorded, not acted on), each track sequenced on measured tempo with no ear check (named one by one, exactly the tracks the sequencing data flags `felt_bpm_check` true, no more), any thematic claim you left out, a non-null `tempo_source_note`, and a `kept-prior` archive.

## Blocked

```json
{"status": "blocked", "missing": ["playlist_yaml"], "reason": "one-line cause", "decision_log": []}
```

`missing` names what is needed: `playlist_yaml` (no `--playlist`, or the file is unreadable), `audio_files` (nothing analyzed), or `audio_analysis` (no dependencies and no archive).

After emitting the success JSON, run `{workflow.on_complete}` if it's set.
