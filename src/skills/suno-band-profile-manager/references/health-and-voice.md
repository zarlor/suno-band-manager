# Health Check and Writer Voice

Scripts run as `uv run {skill-root}/scripts/<name>.py … --project-root {project-root}`. Every profile write goes through `scripts/apply-profile.py`, which keeps the owner's YAML comments, key order and existing list entries.

## Health Check

The outcome is a friendly, concrete read of whether this profile can carry a distinctive song, with improvements offered rather than failures listed, and nothing written without the user's yes.

Read the profile, its decision log and `scripts/validate-profile.py {slug}` output in parallel. **The reply's first line is the verdict:** can the profile carry a song today, yes or no, and the one change that matters most (one field or one action, not a list); nothing comes before it. Then report the validator's findings with their fixes; when it returns `fail`, say the profile doesn't pass, never that it is valid. Then judge what it can't: is every field specific enough for the Style Prompt Builder to write a distinctive prompt? Measure against the standards the user set in the decision log, not a generic rubric, and give each improvement as a rewrite the user can accept — each rewrite meets that same standard itself (if the log asks for a real instrument plus a place or texture, so does every rewrite, including `vocal.tone`). Rewrites build on what the profile and its log already say; when they would have to invent a sound (from a parked idea, say), give one example, say it is invented, and ask the user for the real direction instead of rewriting every field around it. Every sound field you rewrite (`genre`, `style_baseline`, `mood`, `vocal.tone`, `vocal.delivery`, `vocal.energy`) meets the log's standard, and a `style_baseline` rewrite places the vocal direction inside its first ~200 characters (the schema's rule). Before presenting, check each rewrite against it word by word: one that names no real instrument, or no place or texture when the log asks for both, gets reworked, and you claim the standard only for rewrites that meet it. An empty `writer_voice` is an invitation to analyze samples.

Then ask whether recent sessions taught anything worth recording. A durable pattern goes to `generation_learnings`; this round's settings go to `generation_history`. Add each, once the user agrees, with `scripts/apply-profile.py {slug} --append <field> --append-json '<entry>'`.

## Analyze Writer Voice

The outcome is the band's `writer_voice` filled from the user's own writing, each key backed by a line quoted from the samples, so the Lyric Transformer can write in their voice.

Ask for 3-5 samples (poems, lyrics, prose; ideally 10-40 lines each) — "pick pieces that feel most like you". Read pasted text or files in parallel. If the profile already has `writer_voice`, ask whether to replace it, add to it, or refine parts of it. Fill `vocabulary`, `rhythm`, `imagery`, `emotional_tone`, `metaphor_style`, `repetition_patterns` and `sample_quotes`. Present the analysis, let the user correct it, then save it with `scripts/apply-profile.py {slug} --set` (the `writer_voice` mapping on stdin).

If no band is named, ask which one. If no band exists yet (many writers know their voice before their sound), keep the analysis and route into Create, where it becomes the new band's `writer_voice`; a stub profile would fail validation.
