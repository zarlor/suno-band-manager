# Headless Contract

## Modes

- `--headless` (or `-H`) — triage the feedback and return the full adjustment recommendations. `--headless:adjustments` is an accepted alias.
- `--headless:analyze` — triage and categorize only; return `feedback_analysis` (and the `decision_log`) without adjustments.

When the input carries `feedback_type` / `dimensions`, trust them and skip re-triage; otherwise triage with `references/feedback-triage-guide.md` and record the inferred type in `decision_log`.

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

Pass the flags straight to `uv run scripts/parse-feedback.py` — it does the flag-to-JSON translation and reads the lyrics file, so there is no mapping to do by hand. Feed its `parsed.context` plus your `dimensions` (and `tier` from `{suno_tier}`) to `uv run scripts/map-adjustments.py --stdin`.

## Durable writes

A headless run writes the same iteration-log round and `generation_history` snapshot an interactive one does, never `generation_learnings`, and `--no-write` turns all writes off. The rules and commands are in `references/durable-writes.md` → "Headless runs".

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
