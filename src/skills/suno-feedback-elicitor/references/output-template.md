# Feedback Elicitor Output Template

```
## Feedback Summary
{One-paragraph summary of what the user wants changed and why}

## Before/After Preview
**Current sound:** {vivid description of what the current output likely sounds like}
**Target sound:** {vivid description of what the adjusted version should sound like}

## What Changed and Why
{From `map-adjustments.py --diff`: each added, removed, reworded and moved descriptor (and exclusion) with a one-line why, noting what entered or left the first-200-character critical zone. Turns each round into a prompt-engineering micro-lesson.}

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

Lyric changes go to the `suno-lyric-transformer` skill's `--headless:refine` in its refine shape, which carries the current lyrics and the context beside the adjustments:

```json
{
  "source_lyrics": "the current lyrics text",
  "adjustments": [
    {"type": "section-restructure", "detail": "..."},
    {"type": "line-rewrite", "lines": [3, 4], "reason": "..."},
    {"type": "metatag-change", "section": "Chorus", "add": "[Energy: building]"},
    {"type": "rhythmic-fix", "section": "Verse 2", "detail": "..."}
  ],
  "context": {"band_profile": "profile-name", "original_intent": "...", "model_used": "v6"},
  "song_path": "the songbook entry, when there is one"
}
```
