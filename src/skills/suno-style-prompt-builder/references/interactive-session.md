# Interactive Session: Present and Refine

Loaded at Step 5 of an interactive run. Headless runs return JSON instead (`references/headless-contract.md`).

## Present

Number each version (v1, v2, ...) and give a one-line formatting rationale. Present in the order of Suno's Create screen, so the user can work top to bottom: Style Prompt → Exclude Styles → Settings (Model, then the Controls panel top to bottom) → Title → Wild Card. Every pasteable field goes in its own code block.

```
## Style Prompt v{N} ({model_name}) -- {formatting_rationale}
{character_count}/{limit} characters

{style_prompt}            <- code block; paste into "Styles"

## Exclude Styles (Pro/Premier)
{character_count}/~200 characters

{exclusion_prompt}        <- code block
{one line per exclude: the descriptor in this prompt it defends against}

## Settings
- Model: {v6 | v6-wild | v6-mini} -- {reasoning}
- Lyrics Mode: {Manual | Auto | Instrumental}
- Controls panel, top to bottom:
  - Vocal Gender: {value, or "leave empty -- the Voice defines it"}
  - Duration: {Auto | m:ss} -- {reasoning}
  - Max Mode: {On for any take you might keep | Off only for throwaway style-feel sketches} -- 2x credits; applied at generation, so it can't be added to a finished take
  - Weirdness: {value} -- {reasoning from what the slider does}
  - Style Influence: {value} -- {reasoning}
  - Audio Influence: {value} -- {Persona 15-25% | Voice 35-95%} (only with a Voice, Persona or audio attached)
  - Variety: Exact style -- keeps this prompt as written
  - Personalize: Off -- keeps the package reproducible
{persona / voice / custom model note, if any}

## Title
{title_suggestion}        <- code block

## Wild Card -- {twist}
{wild_card_prompt}        <- code block
{one-line pitch}
Same model and sliders as the primary. Excludes: {"same as the primary" | the different list, and why}
Or: run the primary prompt unchanged on v6-wild for a different kind of surprise.
Other twists on request: {the twist options you didn't use}
```

On Free, say the sliders and Exclude Styles aren't available and carry the exclusions as positive phrasing in the prompt.

**Notes for other skills.** If the user volunteered lyric ideas, structure preferences or mix notes during the build, list them after the package as "Notes for the Lyric Transformer / Band Manager". If the song has a workshop file (the Band Manager keeps them as `{project-root}/docs/wip-{working-title}-fragments.md`), offer to append the notes there; if not, offer to create one.

After presenting, advise 3–5 Suno takes before editing the prompt, changing only 1–2 variables per iteration. Structural problems are often better fixed with Replace Section or stems than by re-prompting (details: `references/model-prompt-strategies.md` → "Iteration Best Practices"). Cover and remix prompts are out of scope; point the user to Suno's Cover feature.

## Refine

Reread `references/safety-tables.md` before each refine generation. Regenerate only what the change touches: a creativity change redoes the style prompt and the wild card; a model change redoes the formatting; an exclusion change redoes the excludes. Re-run the validator on anything regenerated. Before switching models mid-refinement, preview what the switch changes.

**Version ledger.** As each version is presented, append `vN | {key change} | {variable changed}` to `{project-root}/.style-prompt-ledger-{song-slug}.md` (the slug from the working title, or the profile name plus genre when there's no title). Start the file fresh on v1 of a new song; a refine of the same song appends. The end-of-session summary of versions and their deltas reads from this file, so it survives compaction however long the loop runs.

The session is complete when the user accepts the package, ends the session, or hands off to another skill. Then run `{workflow.on_complete}` if it's set.
