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
| `--iteration-log` | Optional | File path to the song's iteration log; a path that doesn't exist yet is a first round |
| `--no-write` | Optional | Write nothing durable: no log round, no profile write, no audio archive or companion |

Pass the flags straight to `uv run {skill-root}/scripts/parse_feedback.py` (it accepts and ignores `--headless` itself) — it does the flag-to-JSON translation and reads the lyrics file, so there is no mapping to do by hand. Feed its `parsed.context` fields at the top level of the JSON (or as `context`) plus your `dimensions` (and `tier` from `{suno_tier}`) to `uv run {skill-root}/scripts/map_adjustments.py --stdin`. A `warning` or `fail` status lists the `unmapped` dimensions: map each by judgment from the map reference you read and log it in `decision_log` with medium or low confidence.

- **`--iteration-log` names a log that isn't there yet** (`parsed.context.iteration_log_exists` is false): this is round 1, and the round is written to that path.
- **`{suno_tier}` is unset:** send no `tier`. `map_adjustments.py` then returns the slider moves under `sliders.recommended` with `tier: "unknown"` instead of calling the user Free; give sliders and editor paths as conditional on the tier ("on Pro or Premier: …") and log the unknown tier in `decision_log`.

## Output

**The reply is the JSON object alone:** no text before or after it and no code fence, so a script can parse it. Anything worth saying goes in a field the schema below has (`warnings`, `decision_log`); add no other fields.

**Work silently and finish everything:** send no message before the reply: every tool call goes out with no words beside it (no "Now emitting…", no progress note), and run no background commands: every tool call finishes before you return, so nothing reports after the reply. Scratch files go in a fresh `mktemp -d` folder, never a fixed `/tmp` name another run could share.

```json
{
  "status": "complete|blocked",
  "reason": "",
  "feedback_analysis": {
    "triage_type": "clear|positive|vague|contradictory|technical",
    "secondary_types": [],
    "identified_dimensions": ["vocals", "energy"],
    "confidence": "high|medium|low"
  },
  "adjustment_recommendations": {
    "style_prompt": {"add": [], "remove": [], "keep": [], "reorder_notes": ""},
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
  "warnings": [],
  "suggested_next_action": {"skill": "", "mode": "", "params": {}}
}
```

- `status` is `complete` when triage succeeded and adjustments were generated, or `blocked` when feedback couldn't be triaged or required context is missing. On `blocked`, give a one-line `reason` and still return whatever partial analysis and the `decision_log` so the caller can see why.
- `triage_type` is the type that leads the work; when the feedback mixes types (a technical fix plus a vague remark), list the others in `secondary_types` in the order they're handled.
- `identified_dimensions` all go to `map_adjustments.py` together, so every dimension named here has its adjustments in the return.
- `style_prompt.add` items are literal descriptors, exactly as they would sit in the prompt: no instructions or notes inside them ("(appended to 'gritty male lead vocal')" belongs in `reorder_notes`). Each describes the whole song's sound, never one section ("…in the verses"): the style prompt mostly ignores section directions, which belong in the lyrics' section cues (`lyrics.changes`).
- `style_prompt.keep` lists only the descriptors behind what the user named as right ("the riff is perfect" → the riff's descriptor), not every descriptor left unchanged: the builder's refine never removes or rewords them, so a wider list freezes the prompt. It is the only field for keepers; don't invent `keepers` or `locked_descriptors` elsewhere. Keepers hold in every field: a section cue in `lyrics.changes` ("stripped-back band") mustn't thin a part the user said to keep either.
- An artifact's prompt edits (`map_adjustments.py`'s `if_artifact_persists`) stay out of `style_prompt` (its `reorder_notes` included) and `exclusions`: name them only in `decision_log`, as the fallback if the artifact persists.
- `sliders` holds a change only when the complaint calls for it: each value is one new setting (a single number, never a range like "75-80") or a direction, plus the reason tied to this feedback ("style_influence 75: the vocal-forward wording must win over the band's default"). A slider the feedback doesn't touch stays `""`, so the caller keeps the current value.
- `confidence_scores` has exactly the keys `style_prompt`, `exclusions`, `sliders` and `lyrics`; a field with no adjustment scores `null`.
- `iteration_log.session_id` is the session stamp `YYYYMMDD-HHMM` (from `date +%Y%m%d-%H%M`, the one `feedback_log.py` uses), never made up.
- `iteration_log.tried` is what made this take (the prompt, excludes and settings the user generated with), never this round's recommendations, which haven't been tried yet.
- `written_paths`, `suggested_generation_history` and `suggested_profile_learnings` follow the "Headless runs" rules in `references/durable-writes.md`, which the entry loads beside this file; read it again if it has left context.
- `decision_log` is an array of every assumption made without a user in the loop, each `{"decision": ..., "reasoning": ..., "confidence": "high|medium|low"}`: inferred triage type, reconstructed style prompt, defaulted slider direction, conflict resolutions, and each durable write. A low-confidence guess and a confident call must be distinguishable — the log carries the reasoning, `confidence` carries the grade.
- `warnings` carries what the caller should know that isn't a decision: BMad not set up here (one entry), a missing profile, a durable write that failed.
- `suggested_next_action` names the `suno-style-prompt-builder` skill with mode `--headless:refine` only when the style prompt, exclusions or sliders change (a repair or a regeneration of the unchanged prompt leaves `skill` empty and says the next step in `mode`, e.g. "Replace Section 1:40-1:52, then regenerate if it persists"), so the caller rebuilds and validates the prompt from `adjustment_recommendations`.
- `suggested_next_action.params` is the builder's refine input: `prompt` (the current style prompt), `model`, `tier`, `exclusion_prompt` when known, and `band_profile`; the adjustments themselves come from `adjustment_recommendations` (its `style_prompt`, `exclusions`, `sliders`), named exactly as the builder's refine shape names them.

## Audio mode

`--headless:audio` takes `--audio` (required: a render file, or a folder for a catalog run), `--lyrics` (optional: the lyrics the render came from, for the section map) and `--no-write`.

1. Run `uv run {skill-root}/scripts/analyze_audio.py <audio>` (JSON is its default output). A single file archives to the per-song archive and leaves the catalog companion alone; a folder refreshes both (one band's folder, its own dated archive and companion).
2. When `pytorch_audio_tools` is `on` and `--lyrics` is given with a single file, also run `uv run {skill-root}/scripts/section_map.py <audio> --lyrics <lyrics>`.
3. With `--no-write`, pass `--no-archive` to each script, and `--no-companion` too to `analyze_audio.py` alone: no other script has that flag, and an unknown flag fails the run.

Exit codes are the measurement's verdict: 0 is a reading (`pass`, or `partial` when some files failed); 1 means no reading (a wrong path, a file that couldn't be measured, or a malformed command), with the reason in the script's JSON (`error`, or per-file `findings` when every file failed) and on stderr; 2 means the dependencies couldn't be provisioned. Never report numbers from a run that exited non-zero.

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

