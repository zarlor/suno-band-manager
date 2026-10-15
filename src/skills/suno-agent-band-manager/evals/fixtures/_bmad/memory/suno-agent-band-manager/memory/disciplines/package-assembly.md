# Package Assembly Rule

The core rule — the pipeline skills build every package, the why, and the pre-output self-check — is in `CREED.md`. This file adds what applies while assembling or refining.

**Running the pipeline.** Send both skills in one message as two Agent subagent calls, each running one skill headless, and say nothing until the package is assembled. Agent keeps a skill's headless JSON as an internal tool result; the Skill tool loads the skill into this conversation, so its JSON becomes the visible turn and the owner gets fragments and raw JSON instead of one package. The same goes for the suno-feedback-elicitor inside Refine Song. Use the Skill tool for a skill the owner opens directly (say, `suno-band-profile-manager` from its menu). A headless run of Mac has no owner-facing turn and follows `references/headless.md` instead.

**Signs the pipeline was skipped** — any of these in a draft means rebuilding from the skills' output, not patching the draft:

- No Title field. The skills' contracts include it; hand-built packages forget it.
- Copy-ready blocks you wrote or edited yourself instead of presenting what a skill returned.
- Validation scripts (`validate-prompt.py`, `validate-lyrics.py`) run in place of the skills. They check output; they don't produce it.
- Exclusion reasoning that cites another band's version, a prior iteration or a previous generation. Suno is stateless; excludes defend only against drift from the current prompt's descriptors.
- Reasoning like "I already know what the skill would produce" or "the direction is dialed in enough to skip it". The skills apply checks that aren't visible from the conversation: Voice-character rules, descriptor stacking, exclusion drift risk, per-section metatag reinforcement.

**Where it gets skipped:** parallel-band repackaging (the same lyrics for another band — the direction feels decided, so it's tempting to swap the voice and style prompt in conversation); minor refinements after a good first take — any tag change re-runs the Lyric Transformer, any style-descriptor change the Style Prompt Builder; and after a long direction-setting discussion, when the package parameters feel obvious.

**Quick refinement exception:** a single specific change to a package the pipeline built — a slider, a swapped word, the title — can be made inline. A change to the style prompt, the genre direction or the structure re-runs the relevant skill.

**Presenting a refinement:** only what changed, with a "What Changed" list at the top — the owner already has the rest, and re-presenting everything buries the deltas.

- Lyrics only → the updated lyrics.
- Style only → the updated style prompt and Exclude Styles.
- Both → the full package.
- Settings or sliders only (no skill re-run) → a short note with the new values.
