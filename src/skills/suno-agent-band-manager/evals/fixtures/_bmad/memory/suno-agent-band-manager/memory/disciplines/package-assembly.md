# Package Assembly Rule

The core rule — the pipeline skills build every package, the why, the Create-screen order and the pre-output self-check — is in `CREED.md`. This file adds what applies while assembling or refining.

**Running the pipeline.** Run each pipeline skill headless somewhere its JSON reply stays out of the owner's turn, and say nothing until the package is assembled: the owner should read one package, and a skill run inside the conversation makes its raw JSON and fragments the visible turn instead. On a host with subagents, that is one subagent per skill. On a host without subagents, invoke the skills in this conversation, write no text between the calls, and present only the assembled package. The same holds for the suno-feedback-elicitor inside Refine Song. A skill the owner opens directly (say, `suno-band-profile-manager` from its menu) runs in the conversation, because there the skill's own turn is what they asked for. A headless run of Mac has no owner-facing turn and follows `references/headless.md` instead.

**Order.** A build runs the Style Prompt Builder first and the Lyric Transformer second, because the transformer's `section_cues` input is lifted from the builder's style prompt; when no lyrics are transformed the builder runs alone. Only a refinement whose rebuilds don't depend on each other sends the two out together.

**Signs the pipeline was skipped** — any of these in a draft means rebuilding from the skills' output, not patching the draft:

- No Title field. The skills' contracts include it; hand-built packages forget it.
- Copy-ready blocks you wrote or edited yourself instead of presenting what a skill returned.
- Validation scripts (`validate_prompt.py`, `validate_lyrics.py`) run in place of the skills. They check output; they don't produce it.
- Exclusion reasoning that cites another band's version, a prior iteration or a previous generation. Suno is stateless; excludes defend only against drift from the current prompt's descriptors.
- Reasoning like "I already know what the skill would produce" or "the direction is dialed in enough to skip it". The skills apply checks that aren't visible from the conversation: Voice-character rules, descriptor stacking, exclusion drift risk, per-section metatag reinforcement.

**Where it gets skipped:** parallel-band repackaging (the same lyrics for another band — the direction feels decided, so it's tempting to swap the voice and style prompt in conversation); minor refinements after a good first take — any tag change re-runs the Lyric Transformer, any style-descriptor change the Style Prompt Builder; and after a long direction-setting discussion, when the package parameters feel obvious.

**Before presenting a complete package**, read it once for three things, fix what you find without comment, and mention the check only when it caught something the owner should know:

- **Coherence** — the style prompt matches the lyric's energy and mood, and no exclusion fights the genre.
- **Suno pitfalls** — character limits, known problematic metatags and the model's quirks (grep `{skill-root}/references/SUNO-REFERENCE.md` for "Troubleshooting Suno Issues" and the model's row under "Model Comparison").
- **Wild card** — the variant is a different take, not a minor tweak of the primary.

**Quick refinement exception:** a single specific change to a package the pipeline built — a slider, the title, a swapped word — can be made inline. A change to the style prompt, the genre direction or the structure re-runs the relevant skill. A swapped lyric word is shown as the changed line alone (plain text or a quote), or goes through the Lyric Transformer's headless refine and is presented again; never retype it into a Lyrics block with section tags, because the pipeline guard's Stop hook reads a changed tagged Lyrics block as a hand-built package and blocks the turn. An unchanged Lyrics block may be shown again freely.

**Presenting a refinement:** a "What Changed" list at the top, then what the owner's `refinement_output` setting (in the wake's `config`) asks for:

- `full` → the whole copy-paste package again, in the Create-screen order the creed core gives, every field — nothing for the owner to piece together.
- `changes` (the default) → only what changed, since the owner already has the rest:
  - Lyrics only → the updated lyrics.
  - Style only → the updated style prompt and Exclude Styles.
  - Both → the full package.
  - Settings or sliders only (no skill re-run) → a short note with the new values.
