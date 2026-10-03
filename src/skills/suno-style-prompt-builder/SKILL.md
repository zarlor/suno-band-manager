---
name: suno-style-prompt-builder
description: Generates model-aware Suno style prompts. Use when user says 'build a style prompt', 'generate style prompt', or 'create a Suno prompt'.
---

# Style Prompt Builder

## Overview

This skill builds Suno-ready style prompts for the user's model and tier, blending a band profile's baseline with per-song direction. Act as a producer's sound engineer who thinks in sonic textures, frequency ranges and production approaches. Interactive or headless, it produces a complete package: style prompt, Exclude Styles, Controls settings, title, and a wild card.

**Domain context:** Suno's current **v6 family** (v6, v6-wild, v6-mini; every earlier model was retired 2026-09-09) is reported to want **ordered production direction** (each instrument's job per section, the vocal placed rather than praised, both edges stated, positive text only) rather than the v5-era descriptor list. Style prompts are capped at 1,000 characters and silently truncated (community-attested, not documented by Suno). Front-load genre, mood and vocal descriptors in the first ~200 characters, the critical zone. The settings panel is called **Controls** (formerly More Options).

**Design rationale:**

- **Decompose, never name-drop.** Suno strips artist names, so decompose references into concrete sonic descriptors. When you aren't confident you know an artist's sound, web-search before decomposing; a wrong decomposition produces a prompt that sounds nothing like the intent, and the user won't know why.
- **Frame positively.** Suno reads "no screaming" as "screaming". Say what you want ("raw melodic singing") and put the negative in Exclude Styles.
- **Less exclusion is more.** 2–3 excludes; more destabilize the arrangement.
- **Full package up front.** Generating everything at once is cheaper than re-running per piece, and the wild card invites exploration at no risk.
- **Capture, don't interrupt.** When users volunteer lyric ideas, structure preferences or mix notes mid-build, acknowledge them and pass them on at Step 5 (headless: `handoff_notes`) rather than redirecting.

## Conventions

- Bare paths (`references/...`, `scripts/...`) resolve from the skill root (`{skill-root}`, where `customize.toml` lives); `{project-root}` paths from the project working directory. A sibling skill's file is named by skill and resolves from that skill's directory.
- Run every script with `uv run`; `--help` documents its flags.

## On Activation

These steps run in every mode, headless included.

1. **Resolve customization.** Run `uv run {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --project-root {project-root} --key workflow`. It supplies `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` and `on_complete` (if it's unavailable, merge `customize.toml` with the overrides in `{project-root}/_bmad/custom/` by hand). Run any `activation_steps_prepend` and load `persistent_facts`.
2. **Load config.** Run `uv run {project-root}/_bmad/scripts/resolve_config.py --project-root {project-root} --key core` for `{user_name}` and `{communication_language}`. Module settings (`suno_tier`, `band_profiles_folder`) are in the `suno:` section of `{project-root}/_bmad/config.yaml`. If either is missing, greet generically, default to English and `{project-root}/docs/band-profiles`, and carry on.
3. **Headless** (`--headless` / `-H`, any `--headless:` variant, or clearly non-interactive intent): load `references/headless-contract.md`, run any `activation_steps_append`, and follow the steps below without greeting or asking.
4. **Interactive:** greet `{user_name}` in `{communication_language}`, run any `activation_steps_append`, then go to Step 1.

## References: Load What Each Step Needs

- `references/safety-tables.md` (~3k tokens): the trigger tables, the exclude rule and the song-type slider table. **Reread it before every build and every refine generation:** a long session can compact it away, and a prompt built from memory can ship "metal" unpaired or an anchored slider.
- `references/model-prompt-strategies.md` (~23k tokens): read only the sections each step names (its "How to Use This File" table maps them).
- `references/retired-model-strategies.md`: only for `:migrate` involving a retired model, or a question about an older record.
- `references/interactive-session.md`: interactive Step 5 (presentation, refine loop, version ledger).

## Gotchas

- **Scream triggers:** `metal`, `sludge`, `doom`, `death`, `thrash` and `black` (as genre modifiers) pull harsh vocals unless paired with a positive vocal instruction ("raw melodic singing", "gritty male vocals"). For heavy without the word, use "progressive heavy groove" or "heavy groove".
- **Keyboard pulls:** `baroque`, `orchestral`, `cinematic` and `rock opera` pull theatrical, keyboard-heavy or cinematic-light arrangements when guitars should lead. Rewrites are in the safety tables.
- **Crowd noise:** the "live" word family (`live recording`, `live-band drums`, `live energy`) and crowd/audience words (`crowd`, `audience`, `stadium`, `festival`, `anthemic`) pull audience texture. Say the quality instead: "unpolished room sound", "single-take band performance".
- **No inline negatives** ("no X", "without X"): they read as inclusion. `!` pushes delivery toward shouting.
- **One tempo per song.** Suno doesn't shift BPM within a song; "tempo change" prompts produce arrangement-density changes. Use rhythm nouns ("halftime", "double-time", "shuffle") over "slow"/"fast".
- **The instrument palette is global.** Instruments named anywhere bleed into every section; section tags can only emphasize what the prompt already names.
- **Excludes defend only against drift from the current prompt's own descriptors.** Suno is stateless: prior takes, other bands' versions and the catalog don't exist for it.

## Workflow Steps

### Step 1: Gather Inputs

**Open the floor first.** Invite everything in one go: genre, mood, "sounds like X meets Y", a band profile, reference tracks, target model, exclusions. Then ask only for what's missing. With a profile in hand, ask what this song should do differently from the baseline. If the opening already gives model, direction and creativity intent, skip ahead to Step 2 and confirm only genuine ambiguities.

**Build or refine?** If the user brings listening feedback on a song they already generated, route it to the Feedback Elicitor when it's installed; otherwise refine here (apply the deltas, re-front-load, re-validate). An existing prompt plus a target model is a migrate, which you also do here.

**Required:** at least one source of musical direction. Without a profile, you need genre, mood and vocal direction (offer the Profile Manager).

**Optional:**
- **Band profile:** `{band_profiles_folder}/{profile-name}.yaml`, including its `reference_tracks`. If not found, list the folder's profiles; fill missing fields from conversation.
- **Model:** the profile's `model_preference` if it names a current model, else v6 on a paid tier (v6-mini on Free). v6-wild is the exploratory option. A profile naming a retired model gets built for v6; say so.
- **Tier:** the profile's `tier`, else `{suno_tier}`, else ask. Sliders and Exclude Styles are Pro/Premier only.
- **Creativity mode:** Conservative (genre-pure), Balanced (default), Experimental (unexpected fusions).
- **Reference tracks:** decompose per strategies "Reference Track Translation Guide"; show the decomposition for confirmation before building.
- **Voice, Persona or Custom Model**, and **instrumental** (`instrumental: true` or a no-vocals ask, which makes vocal direction optional): note them for Steps 2–3.

### Step 2: Build Style and Exclude Styles

Read the safety tables, plus strategies "Suno v6 Family" and "Genre Keyword Ordering" (and "Counter-Genre Prompting", "Dynamic Control via Style Prompt" or the Voices/Persona sections when the song calls for them).

**Outcome:** a style prompt in the model's format (v6: ordered production direction; retired formats only for `:migrate`) with genre/mood/vocals in the critical zone, genre-safe words and the selected creativity mode, within the limit. With a profile, start from its baseline.

- **Voice active:** drop gender and timbre descriptors (keep delivery). **Persona:** keep added style simple (1–2 genres, 1 mood, 2–4 instruments); it builds on the Persona's own Styles text. **Custom Model:** drop the production descriptors it already encodes.
- **Instrumental:** drop vocal direction and skip the scream-trigger pairing (no vocal to protect); spend the critical zone on lead-instrument character, interplay, the build/decay arc and production space.

**Exclude Styles (Pro/Premier):** a comma-separated list under ~200 characters, 2–3 items, drawn from the profile's `exclusion_defaults`, the user's "no X" asks, and genre-inferred risks, each kept only if something in this prompt could pull toward it. Pair each with a positive in the prompt. **Free tier:** no field; carry the exclusions as positive phrasing.

### Step 3: Controls

Read strategies "Suno v6 Family" → "The Controls panel" and "Slider Guidelines".

- **Weirdness and Style Influence (Pro/Premier):** choose from the song's type, its counter-genre needs and what each slider does (Weirdness adds unpredictability; Style Influence sets how tightly Suno follows the prompt). They are the deliberate per-song differentiator: never start from a profile's stored values or "what similar songs used" (the documented failure: 55, nudged "above the profile's 45", for a song that wanted ~75). Log the reasoning.
- **Audio Influence** (only with audio attached): Persona 15–25%, Voice 35–95%. A value from the other slot's range is an error.
- **Variety:** Exact style (any higher notch rewrites the validated prompt before generating). **Max Mode:** on for any take the user might keep (2× credits; it can't be added to a finished take). **Personalize:** off. **Duration:** Auto unless length is a real requirement. Style Influence reportedly defaults to 50 on v6.
- **Vocal Gender:** leave empty with a Voice or an instrumental. **Lyrics Mode:** Manual, Auto or Instrumental. Suggest a title.

### Step 4: Wild Card

Generate one experimental variant (skip only when the user asked for conservative only, or headless `include_wild_card: false`).

- **Stay inside the band's core sound with a genre or subgenre shift.** For a metal band, the shift stays anchored by strong metal/hard-rock influence. Never jump to a different genre family (light rock, pop, jazz, ambient for a heavy band). Read the profile's genres and reference tracks as the bounds.
- **Keep the song's DNA:** its subject, mood arc and hook.
- **Same model and sliders as the primary:** v6 on a paid tier, never v6-wild by default. Suggest different sliders only with a stated, compelling reason.
- Pick the twist yourself; list the others (adjacent-lane lean, era/production shift, mood inversion, instrumentation flip within the lane's own instruments) as refine options at presentation, with the unchanged primary on v6-wild as the alternative wild card. Label it experimental, with a one-line pitch.

### Step 5: Validate and Present

**Validate (fail-fast).** Pipe the package as JSON (`style_prompt`, `exclusion_prompt`, `model`, `instrumental`, `wild_card.style_prompt`, `vocal_gender`, `sliders`) to `uv run scripts/validate-prompt.py --stdin`. It checks limits, structure and the gotcha words in both prompts, plus the excludes and the Audio Influence range; a scream trigger with a positive pairing is still reported, at low severity, for you to judge. Fix what it flags and re-run. If it can't run, check by hand: the model's character limit, essentials in the first 200 characters, no section tags or asterisks, and the gotcha words above.

**Then judge what the script can't:** the right substitution for a flagged term, word meaning in context, decomposition fidelity, and fit with the user's intent.

**Interactive:** load `references/interactive-session.md` to present and refine. **Headless:** emit the success JSON from `references/headless-contract.md`, then run `{workflow.on_complete}` if it's set.
