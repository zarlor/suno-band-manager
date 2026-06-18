# Headless Output Contract

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
  "decision_log": [],
  "suggested_next_action": {"skill": "", "mode": "", "params": {}}
}
```

- `status` is `complete` when triage succeeded and adjustments were generated, or `blocked` when feedback couldn't be triaged or required context is missing. On `blocked`, give a one-line `reason` and still return whatever partial analysis and the `decision_log` so the caller can see why.
- `decision_log` is an array of every assumption made without a user in the loop: inferred triage type, reconstructed style prompt, defaulted slider direction, conflict resolutions. A low-confidence guess and a confident call must be distinguishable — the log carries the reasoning, `confidence` carries the grade.

## Headless Input Contract

| Flag | Required | Description |
|------|----------|-------------|
| `--feedback` | Yes | Text string or JSON with feedback content |
| `--style-prompt` | Recommended | Original style prompt used for generation |
| `--model` | Optional | Suno model used (v4.5-all, v4 Pro, v4.5 Pro, v4.5+ Pro, v5 Pro, v5.5 Pro) |
| `--sliders` | Optional | JSON with Weirdness/StyleInfluence values |
| `--lyrics` | Optional | File path to original lyrics |
| `--band-profile` | Optional | Profile name for context loading |
| `--iteration-log` | Optional | File path to previous round's iteration log |

## Flag-to-JSON Translation (you are the translation layer)

The CLI flags above are the *skill's* interface. The deterministic scripts do **not** read those flags — `parse-feedback.py` and `map-adjustments.py` read a JSON blob on stdin with differently-named keys. You translate. Build the JSON from the flags before invoking a script:

| CLI flag | JSON key (scripts) | Notes |
|----------|--------------------|-------|
| `--feedback` | `feedback_text` | required by `parse-feedback.py` |
| `--style-prompt` | `original_style_prompt` | also passed to `map-adjustments.py` as `--style-prompt` for overflow validation |
| `--lyrics` | `original_lyrics` | resolve the file path to its contents first |
| `--model` | `model` | also passed to `map-adjustments.py` as `--model` for the model-specific length check |
| `--sliders` | `slider_settings` | `{"weirdness": 0-100, "style_influence": 0-100}` |
| `--band-profile` | `band_profile` | profile name string |
| (triage result) | `feedback_type`, `dimensions` | your triage output, fed forward as pre-categorization |

`map-adjustments.py` takes its own `dimensions` array plus `--style-prompt` and `--model`; when those are supplied it emits a `style_prompt_overflow` warning keyed to the model's `STYLE_PROMPT_LIMITS` value (v4 Pro = 200, others = 1000) so v4 Pro's silent truncation surfaces as data rather than living only in your head.
