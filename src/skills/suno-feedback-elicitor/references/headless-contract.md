# Headless Contract

## Modes

- `--headless` (or `-H`) — triage the feedback and return the full adjustment recommendations. `--headless:adjustments` is an accepted alias. The return stops at `adjustment_recommendations`: the caller pipes them into the `suno-style-prompt-builder` skill's `--headless:refine` (the shape matches), so this mode doesn't rebuild the prompt itself.
- `--headless:analyze` — triage only: classify the feedback and return `feedback_analysis` and the `decision_log`. No adjustments, no durable writes, no audio measurement.
- `--headless:audio` — measure only: run the audio scripts on a render and return their JSON (see "Audio mode" below). No feedback, triage or recommendations.

When the input carries `feedback_type` / `dimensions` (parse-feedback returns them as `pre_categorized`), trust them and skip re-triage; otherwise triage as the interactive route does and record the inferred type in `decision_log`.

## Input

| Flag | Required | Description |
|------|----------|-------------|
| `--feedback` | Yes | Feedback text, or a JSON object with `feedback_text` (or `feedback`) plus optional `feedback_type` and `dimensions` |
| `--style-prompt` | Recommended | Original style prompt used for generation |
| `--model` | Optional | Suno model used (v6, v6-wild, v6-mini; retired names v4.5-all through v5.5 Pro are still accepted for older records) |
| `--sliders` | Optional | JSON with `weirdness` / `style_influence` values |
| `--lyrics` | Optional | File path to original lyrics |
| `--band-profile` | Optional | Profile name for context loading |
| `--title` | Optional | Song title (names the iteration log) |
| `--iteration-log` | Optional | File path to the song's iteration log |
| `--no-write` | Optional | Write nothing durable (see below) |

Pass the flags straight to `uv run {skill-root}/scripts/parse-feedback.py` — it does the flag-to-JSON translation and reads the lyrics file, so there is no mapping to do by hand. Feed its `parsed.context` plus your `dimensions` (and `tier` from `{suno_tier}`) to `uv run {skill-root}/scripts/map-adjustments.py --stdin`. A `warning` or `fail` status lists the `unmapped` dimensions: map each by judgment from the map reference you read and log it in `decision_log` with medium or low confidence.

## Durable writes

A headless run writes the same iteration-log round and `generation_history` snapshot an interactive one does, never `generation_learnings`, and `--no-write` turns all writes off. The rules and commands are in the durable-writes reference, loaded beside this one.

## Output

```json
{
  "status": "complete|blocked",
  "reason": "",
  "feedback_analysis": {
    "triage_type": "clear|positive|vague|contradictory|technical",
    "identified_dimensions": ["vocals", "energy"],
    "confidence": "high|medium|low"
  },
  "adjustment_recommendations": {
    "style_prompt": {"add": [], "remove": [], "reorder_notes": ""},
    "exclusions": {"add": [], "remove": []},
    "sliders": {"weirdness": "", "style_influence": ""},
    "lyrics": {"changes": []},
    "model_suggestion": "",
    "studio_features": []
  },
  "confidence_scores": {"style_prompt": "high", "sliders": "medium"},
  "iteration_log": {"session_id": "", "round": 1, "tried": [], "user_reaction": "", "reasoning_chain": ""},
  "written_paths": [],
  "suggested_generation_history": null,
  "suggested_profile_learnings": [],
  "decision_log": [],
  "suggested_next_action": {"skill": "", "mode": "", "params": {}}
}
```

- `status` is `complete` when triage succeeded and adjustments were generated, or `blocked` when feedback couldn't be triaged or required context is missing. On `blocked`, give a one-line `reason` and still return whatever partial analysis and the `decision_log` so the caller can see why.
- `decision_log` is an array of every assumption made without a user in the loop: inferred triage type, reconstructed style prompt, defaulted slider direction, conflict resolutions, and each durable write. A low-confidence guess and a confident call must be distinguishable — the log carries the reasoning, `confidence` carries the grade.
- `suggested_next_action` names the `suno-style-prompt-builder` skill with mode `--headless:refine` when the style prompt, exclusions or sliders change, so the caller rebuilds and validates the prompt from `adjustment_recommendations`.

## Audio mode

`--headless:audio` takes `--audio` (required: a render file, or a folder for a catalog run), `--lyrics` (optional: the lyrics the render came from, for the section map) and `--no-write`.

1. Run `uv run {skill-root}/scripts/analyze-audio.py <audio>` (JSON is its default output). A single file archives to the per-song archive and leaves the catalog companion alone; a folder refreshes both.
2. When `pytorch_audio_tools` is `on` and `--lyrics` is given with a single file, also run `uv run {skill-root}/scripts/section-map.py <audio> --lyrics <lyrics>`.
3. With `--no-write`, pass `--no-archive --no-companion` to each script.

Exit codes are the measurement's verdict: 0 is a reading (`pass`, or `partial` when some files failed), 1 means no file could be measured or the path was wrong, 2 means the dependencies couldn't be provisioned. Never report numbers from a run that exited non-zero.

```json
{
  "status": "complete|partial|blocked",
  "mode": "audio",
  "reason": "",
  "measurements": {"analyze-audio": {}, "section-map": null},
  "written_paths": [],
  "decision_log": []
}
```

- `measurements` holds each script's JSON verbatim, keyed by script name; a script that wasn't run is `null`.
- `status` is `complete` when every script run exited 0 with status `pass`, `partial` when one reports `partial` or a requested script failed while another measured, and `blocked` when nothing was measured; give the one-line `reason` from the script's stderr or JSON.
- `written_paths` lists the archive and companion paths the scripts printed (`ARCHIVED:` / `COMPANION:` on stderr).

