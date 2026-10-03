# Feedback Elicitor Output Template

```
## Feedback Summary
{One-paragraph summary of what the user wants changed and why}

## Before/After Preview
**Current sound:** {vivid description of what the current output likely sounds like}
**Target sound:** {vivid description of what the adjusted version should sound like}

## What Changed and Why
{Word-level micro-diff of style prompt: highlight added, removed, and repositioned words with one-line explanations per change. Turns each round into a prompt-engineering micro-lesson.}

## Style Prompt Adjustments
**Current:** {original style prompt if available}
**Recommended:** {modified style prompt}
**Changes:** {bullet list of what changed and why}
**Confidence:** {High -- direct from your feedback / Medium -- interpreted from our conversation / Experimental -- worth trying}

## Exclusion Prompt Adjustments
**Current:** {original exclusions if available}
**Recommended:** {modified exclusions}

## Slider Adjustments
{If applicable -- Weirdness and Style Influence recommendations with reasoning}

## Lyric Adjustments
{If applicable -- specific changes recommended in LT adjustment spec format (below)}

## Studio Features
{If applicable -- recommended Studio workflows}

## Strategy Note
{When applicable: "For this type of issue, try generating 3-5 versions with the adjusted prompt -- Suno's randomness means one may nail it without further changes." Or: "Since only the chorus needs work, consider Replace Section (Pro or Premier) instead of full regeneration."}

## Additional Notes
{Model suggestions, creative context that influenced recommendations}
```

## Lyric Transformer Adjustment Spec

Lyric changes go to the Lyric Transformer (`--headless:refine`) in this shape:

```json
{"adjustments": [
  {"type": "section-restructure", "detail": "..."},
  {"type": "line-rewrite", "lines": [3, 4], "reason": "..."},
  {"type": "metatag-change", "section": "Chorus", "add": "[Energy: building]"},
  {"type": "rhythmic-fix", "section": "Verse 2", "detail": "..."}
]}
```

## Iteration Log

The persistent iteration log is one markdown file per song at `docs/feedback-history/{band-or-session}/{song-slug}.md`: `{band-or-session}` is the band-profile name, or a session timestamp `YYYYMMDD-HHMM` when no profile is in play; `{song-slug}` is the song title kebab-cased, or the same timestamp when the song is untitled. `uv run scripts/feedback-log.py locate` derives the path and the next round number. Each round gets a `## Round {n} — YYYY-MM-DD` heading. Each round's entry captures what was tried and the user's reaction in prose; the JSON line below is the same per-round snapshot in machine-readable form — embed it under the round heading (and it doubles as the headless `iteration_log` payload).

```json
{"session_id": "{timestamp}", "round": 1, "feedback_type": "vague", "dimensions_adjusted": ["vocals", "production"], "key_changes": ["rawer vocals", "less reverb"], "user_intent": "dreamy indie folk", "reasoning_chain": "User said 'too polished' -> mapped to vocal production -> reduced reverb + added raw/intimate descriptors"}
```
