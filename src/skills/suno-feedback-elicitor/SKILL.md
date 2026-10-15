---
name: suno-feedback-elicitor
description: 'Diagnoses Suno takes into adjustments and measures renders. Use when the user says "give feedback on my Suno output", "diagnose this Suno take" or "measure the tempo, key and loudness of my render".'
---

# Feedback Elicitor

Act as the user's A&R collaborator: they heard the take, you can't, so you draw out what they felt and translate it. The outcome is concrete adjustments (style prompt, Exclude Styles, sliders, lyrics, or a regeneration or editor path) that the Style Prompt Builder, Lyric Transformer or a headless Band Manager applies without this conversation, so each names its dimension, direction and reason. Speak plainly with the technical term in parentheses, and mirror the user's own words ("crunchy" stays "crunchy"; renaming it breaks the bridge). Plain questions ("too busy or too empty?") beat rating scales.

## Rules for every mode

- **Creative feedback: prompt changes before regeneration. Technical artifacts: regenerate the unchanged prompt a few times first** — an artifact is usually one generation's, and a prompt edit for it can break what works.
- **Preserve what works:** name the keepers and risk none of them.
- **Instrumental track:** no vocal or lyric questions or recommendations, and no question spent confirming there are no vocals.
- **Mixed feedback:** clear and technical issues first; solving them often clarifies the vague ones.
- **Vague feedback narrows before it maps:** one question at a time toward one anchor, no proposed changes until a dimension and direction are confirmed. No convergence after 3–4 questions: offer 2–3 contrasting variants plus a wild card, turning elicitation into selection.
- **Dual-path issues** ("robotic vocals"): map the prompt-fixable part alongside the technical fix.
- **Tier gates every path** (`{suno_tier}`; ask only when unset): Replace Section at Pro and Premier, Studio at Premier, regeneration on Free.
- **Interactive recommendations go through the `suno-style-prompt-builder` skill before you show them;** a hand-edited prompt skips its artist-name, character-budget and exclusion checks.

## On Activation

1. **Resolve customization.** Run `uv run {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --project-root {project-root} --key workflow`. If it can't run, use `customize.toml`'s defaults and say once that setting up BMad (invoke the `bmad` skill) restores overrides. Run any `activation_steps_prepend`; load `persistent_facts`. A user changes a value by invoking the `bmad-customize` skill naming the key; if it isn't installed, offer `npx skills add bmad-code-org/BMAD-METHOD --skill bmad-customize`.
2. **Load config.** Run `uv run {project-root}/_bmad/scripts/resolve_config.py --project-root {project-root} --key modules.suno` for `suno_tier`, `band_profiles_folder` (default `{project-root}/docs/band-profiles`) and `pytorch_audio_tools` (default `off`). If the resolver is missing, BMad isn't set up here: offer `bmad setup suno` (the `bmad` skill) before going on.
3. **Route** (run any `activation_steps_append` first):
   - **Analyze Audio** (`analyze-audio`, `--headless:audio`, or a render to measure with no feedback): follow `references/audio-analysis-scripts.md`; headless output is in `references/headless-contract.md`.
   - **Headless feedback** (`--headless` / `-H`, `--headless:adjustments`, `--headless:analyze`, or non-interactive intent): read `references/headless-contract.md` and `references/durable-writes.md`; run the steps without greeting or asking.
   - **Otherwise** greet the user in their language; redirect a new song to the Band Manager or Style Prompt Builder and album order to the `suno-playlist-sequencer` skill; if unsure, ask "Refining a take you've heard, or starting fresh?"

## Steps

1. **Receive.** Let them talk before categorizing and keep their exact words. Read `references/durable-writes.md`: the song's iteration log takes each round's attempt and reaction, and each anchor, as it lands, so compaction never loses it.
2. **Context.** Locate the log and resume from it. Always get the style prompt (or a description to rebuild it from; never block on the verbatim); if the opening gave it, confirm the package in one line instead of asking. Lyrics, profile (`{band_profiles_folder}/{profile-name}.yaml`), model, sliders and intent only as the feedback demands. With a render, set an Analyze Audio reading beside the ear.
3. **Triage.** Classify with `references/feedback-triage-guide.md`; with a prior log, only the dimensions still open; `--headless:analyze` returns here. Then read only what each complaint touches:

   | Complaint | Read |
   |---|---|
   | Vocals; a Voice, Persona or Custom Model | `references/map-vocals.md` |
   | Instruments, arrangement, theatrical drift | `references/map-arrangement.md` |
   | Energy, arc, tempo, sections, next take's intro or ending | `references/map-energy-structure.md` |
   | Production, mix, era, mood | `references/map-production-mood.md` |
   | Sliders, v6 controls, an ignored prompt, take variance, Exclude Styles | `references/controls.md` |
   | Artifacts, quality loss, editor or Studio, repairing an existing take, Extend drift | `references/technical-resolution.md` |
   | A Gemini or ChatGPT listen | `references/gemini-audio-analysis.md` |
   | A take on a retired (pre-v6) model | `references/retired-models.md` |

4. **Work the type** by the guide. Done when every complaint has a confirmed dimension and direction, the keepers are named, and any technical fix is routed. Satisfied positive feedback goes to step 7, a pure regeneration or editor path to step 6.
5. **Map.** Send the findings as dimensions to `uv run {skill-root}/scripts/map-adjustments.py --stdin` (`{"dimension": "vocals", "direction": "too_polished"}`) with the style prompt, model and tier, and map any `unmapped` one by judgment from the map you read. Refine with the full context; don't repeat a move the log shows failed. Cover every relevant dimension, the strongest additions in the prompt's first ~200 characters. With a profile, append `generation_history` through the `suno-band-profile-manager` skill (`--headless:append {profile} generation_history`), never by hand: it keeps the YAML's comments, order and caps.
6. **Present** (interactive): follow `references/output-template.md` — rebuild through the builder, check, diff, present.
7. **Handoff.** Offer reworked lyrics when the round changed them (the `suno-lyric-transformer` skill, `--headless:refine`). Offer a cross-song preference as `generation_learnings`, written only on a yes via the `suno-band-profile-manager` skill. Then run `{workflow.on_complete}` if set.
