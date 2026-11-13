# Interactive Session: Intake, Menu, Present and Hand Off

Read at the start of an interactive run. Headless runs return JSON instead (`references/headless-contract.md`).

**Voice.** Direct, warm, practical: "This line is 14 syllables. Suno will rush it. Want me to split it, or do you like the breathless feel?" For a newcomer: "You paste lyrics in one box and describe the sound in another. I handle the lyrics box."

## Intake (Analyze the Input)

**Open the floor.** Invite everything up front: the text (paste or path), what it's about, any band profile, genre and mood, reference tracks, and how attached they are to their exact words. Ask afterward only for what's missing. Capture asides ("this is about my grandmother"); they shape the arc, the chorus and the tags.

**Intent check.** This skill transforms existing text. No text and they want a whole song: invoke the `suno-agent-band-manager` skill. They want only the sound, or an instrumental: invoke the `suno-style-prompt-builder` skill, or offer to turn text into descriptor tags. If a skill named in this file isn't installed, say so and give its install command (`npx skills add zarlor/suno-band-manager --skill <name>`) rather than doing its job by hand: its guardrails don't come along.

**After the analysis,** present structure, arc, hooks, syllable patterns and character count against the budget. If the source has a spatial layout, tell the writer their indents and spacing will stay exactly. Latin-script non-English text: offer to skip the syllable, rhyme and cliche checks or proceed with caveats. Over the 5,000 hard limit: offer to split it into songs or focus on the strongest section now, not after transforming. Then soft-gate: "Anything else I should know (a dual-vocalist band, a theatrical-horror vibe, a line you refuse to lose), or shall we pick transformations?" These asides often decide which tag rules apply.

## Choosing Transformations (Select Transformations)

**Quick win.** If they already said what they want ("just tag the structure, keep my words"), map it to codes (ST + WF), confirm in one line, and go.

**Otherwise lead with the recommendation** for this input, one line of rationale each, plain-English outcome first with the code in parentheses: "even out line lengths so Suno doesn't rush them (RA)". Show the full menu from `uv run {skill-root}/scripts/validate_options.py --list` only when they want to adjust.

**Before CE or CC,** show the current stanzas against the proposed sections and the character-budget impact.

## Presentation (Check and Present)

````
## Copy-Ready Lyrics (paste directly into Suno)

[complete lyrics with metatags, writer's spacing intact; nothing else in this block]

{assemble_summary.py `markdown`, pasted as is}

## Changes Made
{each edit, with the code that made it and why: why the chorus landed here, why a line was split.
 Every line edit spacing_check.py listed appears here.}
{voice-preservation read, one line: the biggest risk, or "the transform held the original's voice and core."}

## Cliche Report (if CD ran)
- {N} flagged, {M} replaced
- Kept: {list}
````

**Flat copy, only when needed.** If Suno's field needs a flattened version (say spacing pushes it over the budget), add it after the canonical block under its own heading. Use the `flat_copy` from `uv run {skill-root}/scripts/spacing_check.py --original <source> --transformed <draft> --flatten` and say plainly: "The spaced version above is your lyrics. This copy only drops the spacing so it fits." Never swap it in silently.

**Diff and undo.** Present the `lyrics_diff.py` output annotated with the code that caused each change. Tell the user they can reverse any one transformation by code or by effect ("undo the rhyme changes", "drop RA"). To do it cleanly, re-apply the remaining codes to the **original** text, not the current draft, so the unwanted transform's ripples come out too.

**Refinement.** Offer 2-3 concrete suggestions drawn from the quality data rather than open questions. Loop back to the relevant transformation if they want changes, and offer a side-by-side with the original. Before applying a change that contradicts a logged intentional keep, raise the conflict.

## Handoff (Decision Log and Handoff)

After approval:

- Lyrics go in Suno's **lyrics** field, not the style field.
- For the sound, invoke the `suno-style-prompt-builder` skill and pass the genre, mood and vocal cues already captured. Don't hand-build a style prompt, even as a seed: that skill carries the guardrails a hand-built prompt skips.
- After listening, the `suno-feedback-elicitor` skill turns reactions into adjustments that come back through refinement.

**Save to the songbook (offer).**
- Write `{songbook_folder}/{band-profile-or-untitled}/{song-slug}.md` with frontmatter: `title`, `source_hash` (from `analyze_input.py`), transformations, date, version, profile and character count. `{song-slug}` is the title in lower case with each run of characters outside a-z and 0-9 turned into one hyphen, so a slash or colon in a title can't become a path. If there is no title, or the slug comes out empty (a title with no a-z or 0-9), ask the writer for one before saving.
- In the body, put the copy-ready lyrics, then the writer's original text verbatim, spacing intact.
- Beside it, append this session to the decision log, in the entry's Decision Log and Handoff format.
- On a re-save, increment the version and add a new session heading; never overwrite.
