# Presenting and Handing Off

Load this at Step 4's presentation and for the Step 5 handoff in interactive runs.

## Presentation

````
## Copy-Ready Lyrics (paste directly into Suno)

[complete lyrics with metatags, writer's spacing intact; nothing else in this block]

{assemble-summary.py `markdown`, pasted as is}

## Changes Made
{each edit, with the code that made it and why: why the chorus landed here, why a line was split.
 Every line edit spacing-check.py listed appears here.}
{voice-preservation read, one line: the biggest risk, or "the transform held the original's voice and core."}

## Cliche Report (if CD ran)
- {N} flagged, {M} replaced
- Kept: {list}
````

**Flat copy, only when needed.** If Suno's field needs a flattened version (say spacing pushes it over the budget), add it after the canonical block under its own heading. Use the `spacing-check.py --flatten` output and say plainly: "The spaced version above is your lyrics. This copy only drops the spacing so it fits." Never swap it in silently.

**Diff and undo.** Present the `lyrics-diff.py` output annotated with the code that caused each change. Tell the user they can reverse any one transformation by code or by effect ("undo the rhyme changes", "drop RA"). To do it cleanly, re-apply the remaining codes to the **original** text, not the current draft, so the unwanted transform's ripples come out too.

**Refinement.** Offer 2-3 concrete suggestions drawn from the quality data rather than open questions. Loop back to the relevant transformation if they want changes, and offer a side-by-side with the original.

## Handoff

After approval:

- Lyrics go in Suno's **lyrics** field, not the style field.
- For the sound, route to the Style Prompt Builder and pass the genre, mood and vocal cues already captured. Don't hand-build a style prompt, even as a seed: that skill carries the guardrails a hand-built prompt skips.
- After listening, the Feedback Elicitor turns reactions into adjustments that come back through Refinement.

**Save to the songbook (offer).**
- Write `{songbook_folder}/{band-profile-or-untitled}/{song-title}.md` with frontmatter: `source_hash` (from `analyze-input.py`), transformations, date, version, profile and character count.
- In the body, put the copy-ready lyrics, then the writer's original text verbatim, spacing intact.
- Beside it, append a session to `{song-title}.decision-log.md` with the structural decisions and intentional keeps (format in `references/headless-contract.md` → "Where Keeps Are Written"). That log is what stops a later refinement from undoing a choice the writer made on purpose.
- On a re-save, increment the version and add a new session heading; never overwrite.
