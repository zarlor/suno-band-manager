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
{If applicable -- specific changes recommended in LT adjustment spec format}

## Studio Features
{If applicable -- recommended Studio workflows}

## Strategy Note
{When applicable: "For this type of issue, try generating 3-5 versions with the adjusted prompt -- Suno's randomness means one may nail it without further changes." Or: "Since only the chorus needs work, consider Replace Section on v5 Pro instead of full regeneration."}

## Additional Notes
{Model suggestions, creative context that influenced recommendations}
```

## Iteration Log

```json
{"session_id": "{timestamp}", "round": 1, "feedback_type": "vague", "dimensions_adjusted": ["vocals", "production"], "key_changes": ["rawer vocals", "less reverb"], "user_intent": "dreamy indie folk", "reasoning_chain": "User said 'too polished' -> mapped to vocal production -> reduced reverb + added raw/intimate descriptors"}
```
