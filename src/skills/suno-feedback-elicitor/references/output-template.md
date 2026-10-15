# Presenting Recommendations (interactive)

## Rebuild and check first

Invoke the `suno-style-prompt-builder` skill with `--headless:refine`, passing its refine shape:

```json
{"prompt": "<current style prompt>", "model": "<model>", "style_prompt": {"add": [], "remove": [], "reorder_notes": ""}, "exclusions": {"add": [], "remove": []}, "sliders": {"weirdness": "", "style_influence": ""}, "model_suggestion": ""}
```

It returns the refined prompt, Exclude Styles and sliders with its validator's report, so artist-name, character-budget and exclusion checks have all run. Then run `uv run {skill-root}/scripts/map-adjustments.py --check-final --style-prompt <refined> --exclude <refined excludes>` and fix any descriptor an exclusion cancels. A `blocked` return means the prompt wasn't rebuilt: present the adjustments as recommendations and say so. Whether the sliders contradict the prompt, and whether a change risks a liked element, stays your judgment.

Build "What Changed and Why" from `uv run {skill-root}/scripts/map-adjustments.py --diff --style-prompt <before> --new-style-prompt <after>` (add `--exclude` / `--new-exclude` when the exclusions changed), giving each item its one-line why.

## Template

Open with a vivid before and after ("Right now: arena rock with polished vocals. Target: coffee-shop acoustic, rawer and intimate"). Omit sections that don't apply. Comparing generations: what each does well or poorly, what to carry forward, which changes mattered most. Close with "Does this capture what you're after?" and loop back if needed.

```
## Feedback Summary
{One paragraph: what the user wants changed and why}

## Before/After Preview
**Current sound:** {vivid description of the current output}
**Target sound:** {vivid description of the adjusted version}

## What Changed and Why
{From the --diff: each added, removed, reworded and moved descriptor (and exclusion) with a one-line why, noting what entered or left the first-200-character critical zone, so each round is a small prompt-engineering lesson.}

## Style Prompt Adjustments
**Current:** {original style prompt if available}
**Recommended:** {the builder's refined prompt}
**Confidence:** {High -- direct from your feedback / Medium -- interpreted from our conversation / Experimental -- worth trying}

## Exclusion Prompt Adjustments
**Current:** {original exclusions if available}
**Recommended:** {the builder's refined exclusions}

## Slider Adjustments
{If applicable -- Weirdness and Style Influence with reasoning}

## Lyric Adjustments
{If applicable -- the Lyric Transformer adjustment spec below}

## Studio Features
{If applicable -- editor or Studio workflows the user's tier has}

## Strategy Note
{When applicable: how many takes to try with the adjusted prompt, or "Since only the chorus needs work, consider Replace Section (Pro or Premier) instead of full regeneration."}

## Additional Notes
{Model suggestions, creative context that shaped the recommendations}
```

## Lyric Transformer adjustment spec

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
