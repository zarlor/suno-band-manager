# Headless Contract

## Input

- `--playlist docs/{band-slug}-playlist.yaml` (required). Without it, return the blocked contract.
- `--locked "Song A > Song B > Song C"` (optional, repeatable): a locked arc that must stay together and in order. These add to any `locked_arcs:` in the playlist YAML. With no user to ask, these are the only locked arcs the run knows about.
- If the caller asks for a catalog-wide pass, also run `uv run scripts/batch-full-analysis.py`.

## Run

1. Run `uv run scripts/validate-sequence.py {playlist} --locked "..."` on the current order. It reports every locked arc and whether it is intact.
2. Run `uv run scripts/playlist-sequencing-data.py --playlist {playlist}` and apply the methodology.
3. With no user to confirm by ear, take tempo from `felt_bpm:` where the YAML records it. Where `felt_bpm_check` is true, sequence on the measured tempo and log it as an assumption.
4. Do the thematic read yourself (methodology, "Thematic Verification"), or leave out thematic claims and log that you did.
5. Before returning, check the recommended order with `validate-sequence.py --order <file>`. Never pass `--write` in headless. The playlist YAML stays unchanged, and the caller decides whether to apply the order.

## Success

```json
{
  "status": "complete",
  "album": "string",
  "recommended_sequence": [{"position": 1, "name": "string", "rationale": "string"}],
  "locked_arcs_respected": ["Song A > Song B"],
  "dropped_tracks": [{"name": "string", "reason": "missing audio file | analysis error"}],
  "flagged_transitions": [{"from": "string", "to": "string", "issue": "string"}],
  "trade_offs": ["string"],
  "playlist_yaml_changed": false,
  "artifacts": {"sequencing_json": "docs/audio-analysis/playlists/{band-slug}.json", "companion": "docs/{band-slug}-playlist-sequencing.md"},
  "decision_log": [{"call": "string", "reason": "string"}]
}
```

- `dropped_tracks[]`: copy it from the script's top-level `dropped[]`. Never sequence a short list without saying so.
- `flagged_transitions[]`: the seams the methodology judged jarring or degraded, worst first. On a re-eval, the script's `compare.seam_changes` (marked `worse`) go here too.
- `decision_log[]`: one entry for every call made without the user. That includes any locked-arc break you declined (recorded, not acted on), any seam sequenced on measured tempo with no ear check, and any thematic claim you left out.

## Blocked

```json
{"status": "blocked", "missing": ["playlist_yaml"], "reason": "one-line cause", "decision_log": []}
```
