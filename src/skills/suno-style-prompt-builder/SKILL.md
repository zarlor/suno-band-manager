---
name: suno-style-prompt-builder
description: Generates model-aware Suno style prompts. Use when user says 'build a style prompt', 'generate style prompt', or 'create a Suno prompt'.
---

# Style Prompt Builder

## Overview

This skill generates Suno-ready style prompts optimized for the user's chosen model tier, blending band profile baselines with per-song creative direction. Act as a producer's sound engineer who thinks in sonic textures, frequency ranges, and production approaches. Through guided conversation (or headless structured input), it produces a complete prompt package: style prompt, exclusion prompt, slider recommendations, and an optional experimental wild card variant.

**Domain context:** Suno's model families respond to fundamentally different prompt styles -- v4.5 wants conversational descriptions while v5 wants crisp, film-brief descriptors; never mix the two approaches. Style prompts are hard-capped at 1,000 characters (200 for v4 Pro) and silently truncated. Real-world testing suggests v4.5-all may only effectively use ~200 characters. Front-load all essential genre, mood, and vocal descriptors in the first ~200 characters (the "critical zone") -- everything after is supplementary. The "Exclude Styles" field is separate and follows its own rules.

**Design rationale (load-bearing constraints):**

- **Decompose, never name-drop.** Never put artist names in style prompts -- Suno will not reliably replicate them. Decompose references into concrete sonic descriptors. When you are not confident you know an artist's distinctive sound, web-search to verify *before* decomposing; never fabricate sonic details. A wrong decomposition produces a prompt that sounds nothing like intent, and the user won't know why.
- **Frame positively.** Translate negatives ("no screaming") into positives ("raw melodic singing with grit on peaks"). Suno does not reliably process in-prompt negation; the Exclude Styles field carries the negatives.
- **Less exclusion is more.** Prioritize the 2-3 most important exclusions; too many destabilize the arrangement.
- **Always output the full package** (style + exclusion + sliders + wild card). Generating everything up front is cheaper than re-running per piece, and the wild card encourages creative exploration without risk.
- **Capture-don't-interrupt.** When users volunteer lyric ideas, structure preferences, or mix notes mid-build, acknowledge and store them for handoff to the appropriate sibling skill rather than redirecting.

## Conventions

- Bare paths (e.g. `references/model-prompt-strategies.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Activation Mode Detection

**Check activation context immediately:**

1. **Headless mode**: If user passes `--headless` or `-H` flags, or intent clearly indicates non-interactive execution:
   - `--headless:from-profile` -- generate using only profile baseline
   - `--headless:custom` -- generate from provided parameters without profile
   - `--headless:refine` -- accept an existing prompt + structured adjustments and apply deltas. Accepts the sibling Feedback Elicitor's `adjustment_recommendations` shape so its output can be piped in directly:
     ```json
     {
       "prompt": "string", "model": "string",
       "style_prompt": {"add": [], "remove": [], "reorder_notes": ""},
       "exclusions": {"add": [], "remove": []},
       "sliders": {"weirdness": "", "style_influence": ""},
       "model_suggestion": ""
     }
     ```
     `reorder_notes` is free-text reordering guidance (the producer shape); apply it as a re-front-loading instruction. A legacy `adjustments.reorder: string[]` / `adjustments.replace[]` shape is still accepted for backward compatibility.
   - `--headless:migrate` -- accept existing prompt + original model + target model, reformat using target model's strategy from `references/model-prompt-strategies.md`
   - `--headless` with profile name -- hybrid mode (profile baseline + overrides)
   - Bare `--headless` with no sub-mode and no profile -- require at minimum `genre_mood`; apply defaults
   - Reload `references/model-prompt-strategies.md` before generating (see Compaction Survival), then output the complete prompt package as the success JSON below. No interaction; headless **skips the decomposition-confirmation step** and records that skip in `decisions[]`.
   - **Validate before emitting (all sub-modes, including `:refine` and `:migrate`):** run `uv run scripts/validate-prompt.py --style "{style_prompt}" --exclude "{exclusion_prompt}" --model "{target_model}"` on the reformatted/adjusted prompt -- the migrate/refine paths produce a new prompt against a (possibly new) model's char + critical-zone budget, so the same fail-fast check Step 5 runs interactively applies here. Fix anything flagged, re-run, and fold the script's report into the `validation` field of the success JSON (or note it if the script can't execute).
   - **Sliders obey the per-song anti-anchoring rule even headless:** choose Weirdness/Style Influence fresh from the Slider Guidelines table by reasoning from song type + what each slider does -- never default to a profile's stored `sliders:` (the bare-Demo fallback is the only exception). Log each chosen value with its behavioral reasoning in `decisions[]`. User-supplied slider values are authoritative -- pass them through, don't re-derive.

   **Headless defaults** (when optional parameters omitted): Creativity=Balanced, Model=v4.5-all, Wild card=disabled (unless `include_wild_card=true`)

   **Headless success contract**: On completion, emit the package as JSON. `decisions[]` logs every non-obvious call the user would have weighed in interactively -- dangerous-word substitutions, genre demotions, slider choices, the skipped decomposition confirmation -- each with a one-line `reason`:
   ```json
   {
     "status": "complete",
     "model": "v5 Pro",
     "style_prompt": "string",
     "exclusion_prompt": "string",
     "sliders": {"weirdness": 55, "style_influence": 75, "audio_influence": null},
     "wild_card": {"style_prompt": "string", "reasoning": "string"},
     "validation": { "...": "validate-prompt.py report (or note if unavailable)" },
     "decisions": [
       {"call": "substituted 'progressive heavy groove' for 'metal'", "reason": "profile excludes screaming; 'metal' triggers harsh vocals"},
       {"call": "skipped decomposition confirmation", "reason": "headless mode -- no interactive turn available"}
     ]
   }
   ```
   `wild_card` is `null` when disabled. `status` is `complete` or `blocked`.

   **Headless blocked/error contract**: When required inputs are missing, return `status: "blocked"` with the missing fields and a one-line reason; still include any `decisions[]` recorded so far:
   ```json
   {"status": "blocked", "missing": ["genre_mood"], "reason": "Required input 'genre_mood' not provided for --headless:custom mode.", "decisions": []}
   ```

2. **Interactive mode** (default): Proceed to On Activation

## On Activation

1. **Resolve customization** -- run `{project-root}/_bmad/scripts/resolve_customization.py {skill-name}` to merge `customize.toml` with any team/user overrides. Apply `activation_steps_prepend` before the steps below and `activation_steps_append` after greeting; load `persistent_facts` (durable project context). If the resolver is unavailable, proceed with defaults.
2. **Load config via bmad-init skill** -- use `{user_name}` for greeting, `{communication_language}` for all communications. Fallback: greet generically, default to English. Do not block on missing config.
3. **Greet user** and proceed to Step 1

## Compaction Survival (HARD RULE)

All load-bearing safety knowledge -- scream/harsh-vocal triggers, the Dangerous Words / keyboard-pull list, the Genre Term Behavior Table, and the **Slider Guidelines table + per-song anti-anchoring rule** (choose Weirdness/Style Influence fresh each song reasoning from what each slider DOES; never anchor to a profile's stored `sliders:` defaults or to "what similar catalog songs used" -- a profile's stored sliders are a weak fallback for a bare Demo *only*, the single exception) -- lives in `references/model-prompt-strategies.md`. A long interactive session or an open-ended Step 5 refine loop can compact that reference out of context, and a prompt built without it can silently ship "metal", "cinematic", an unpaired heavy genre that triggers screaming or pulls keyboards, or a slider value lazily anchored to a profile default instead of chosen for the song.

**Therefore: before EVERY build and EVERY refine generation, (re)load `references/model-prompt-strategies.md` and treat its gotcha tables as non-negotiable inputs.** Do not generate or revise a style prompt from memory of these tables -- reload them. `validate-prompt.py` is the deterministic backstop (it flags enumerable triggers), but the substitution decision and any term not in its table still require the live reference.

## Workflow Steps

### Step 1: Gather Inputs

**Open the floor first.** Invite the user to share everything they have in one go -- genre, mood, vibe, "sounds like X meets Y", a band profile name, reference tracks, target model, exclusions, paths to anything relevant. The dump replaces most of the question script; then ask only for what's still missing. Adapt the invitation to the input: a vague "build me a prompt" gets "tell me what you're going for"; a profile name or reference already in hand gets "what do you want this song to do differently from the baseline?".

**Signpost build vs. refine at the front door.** If the user's intent is to *adjust output they already generated and listened to* ("the vocals came out too harsh", "make it less busy", "this generation drifted"), that is post-generation feedback -- hand it toward the **Feedback Elicitor** rather than building a fresh prompt here. This skill builds and migrates prompts; the Elicitor maps listening feedback into adjustments. A new build from a fresh creative direction stays here.

**Standalone (no agent/Mac orchestration):** When this skill is invoked directly rather than through the Band Manager agent, the in-skill `:refine` and `:migrate` machinery is still available to the user -- they don't need the Feedback Elicitor or the agent to refine or model-migrate an existing prompt. If a standalone user hands you an existing prompt plus listening feedback, do the refine here (apply deltas, re-front-load, re-validate via Step 5 / the headless validate clause); if they hand you a prompt + a target model, do the migrate here (reformat to the target model's strategy, re-validate against its char budget). Only route to the Feedback Elicitor when it's actually present in the user's setup.

**Expert quick-win short-circuit.** If the opening dump already yields model + musical direction + creativity intent (an experienced user who handed you everything), skip the rest of the gather and proceed straight to Step 2 -- confirm only genuine ambiguities. Don't re-ask for things already provided. **If the user supplied explicit slider values, treat them as authoritative** -- pass them through to Step 3 and do not re-derive them from the table or a profile default.

**Required:** At least one source of musical direction -- genre, mood, vibe, "sounds like X meets Y", or modifications to a loaded band profile baseline.

**Optional but valuable:**
- **Band profile** -- read from `docs/band-profiles/{profile-name}.yaml`. Use `reference_tracks` if present. If not found, list available profiles. If fields are missing, warn and fill from conversation.
- **Model** -- default to profile's `model_preference` if available. Options: v4.5-all (free), v4 Pro (200-char limit), v4.5 Pro, v4.5+ Pro, v5 Pro, v5.5 Pro.
- **Creativity mode** -- Conservative (genre-pure, Weirdness 20-35), Balanced (default, 40-60), Experimental (unexpected fusions, 65-85)
- **Specific requests** -- instrument preferences, mood descriptions, exclusions
- **Reference tracks** -- decompose into concrete style descriptors (see `references/model-prompt-strategies.md` for confidence check and decomposition framework)
- **Inspo playlists (v4.5+ Pro)** -- suggest as alternative to manual reference decomposition when user has successful generations or real reference tracks

**No profile loaded:** Need genre, mood, and vocal direction at minimum. Offer to proceed without profile or hand off to Profile Manager.

**Instrumental detection:** If the profile sets `instrumental: true` (or the user asks for an instrumental / no-vocals track), flag it now and carry it into Steps 2-3 -- vocal direction is not a required input for instrumental songs, and the build branches accordingly (see Step 2's instrumental branch).

**Tier detection:** Determine from profile `tier` field or ask. Affects slider and Exclude Styles field availability (Weirdness/Style Influence are Pro/Premier only).

**Efficiency:** When model is known during Step 1, load `references/model-prompt-strategies.md` alongside the profile read.

### Step 2: Build Style & Exclusion Prompts

(Re)load `references/model-prompt-strategies.md` for model-specific construction rules, genre term behavior, and dangerous word lists -- per the Compaction Survival rule, this reload happens before every build, not just the first.

**Instrumental branch (when instrumental was flagged in Step 1):** Drop all vocal direction from the style prompt and skip the Vocal-Gender recommendation in Step 3 -- there are no vocals to describe. Skip the scream-trigger *pairing* prompts too: an unpaired heavy genre term (`metal`, `sludge`) needs no positive vocal instruction here because there are no vocals to protect (the validator's `trigger` finding for an unpaired heavy term is a non-issue for instrumentals -- note it as handled rather than "fixing" it with a vocal phrase). Note `[Instrumental]` handling for the package. **Redirect the critical-zone budget that vocals would have used into arrangement, texture, and dynamics** -- lead instrument character, interplay, build/decay arc, production space -- since those now carry the song's identity.

**Strategy:** From profile baseline, from scratch, or hybrid (default when profile exists).

**Key limitation:** The style prompt sets ONE overall sonic mood. Suno does NOT actually shift tempo within a song — "tempo change" or "tempo shift" prompts produce arrangement-density variation (instrumentation pullback / compression), not actual BPM movement. Set baseline feel here; use lyric density and rhythm-noun metatags (`[Heavy: halftime]`, `[Double Time]`) for section-level perceived-tempo changes.

**Outcome:** A model-formatted style prompt that front-loads genre/mood/vocals in the critical zone, uses genre-safe terminology, and respects character limits. The prompt should:

- Follow the model's formatting style (v4.5: conversational sentences; v5/v5.5: crisp 5-8 descriptor film-brief; v4 Pro: simple descriptors within 200 chars)
- Translate reference tracks into concrete descriptors (show decomposition to user for confirmation before building)
- Apply the selected creativity mode
- Use genre-safe word choices per the Genre Term Behavior Table and Dangerous Words list in the strategies reference

**Genre word triggers** -- words that override other instructions:
- **"Metal"** triggers screaming/harsh vocals. For heavy without screaming: "progressive heavy groove", "heavy groove"
- **"Sludge"** triggers harsh vocals. Use "heavy", "thick", "dense"
- **"Death"**, **"thrash"**, **"black"** (as genre modifiers) trigger extreme vocal styles
- When a profile specifies these genres but excludes screaming, automatically substitute safe alternatives

**Keyboard-pull dangerous words** -- **"baroque"**, **"orchestral"**, **"cinematic"**, and **"rock opera"** pull theatrical/keyboard/synth-heavy or cinematic-light arrangements when guitars/bass should lead. These are texture modifiers, not genres. Replace per the Dangerous Words and Keyboard Triggers table in the strategies reference (e.g. "rock opera" -> "power ballad, dynamic shifts, building from gentle to crushing"). `validate-prompt.py` flags them; the reference carries the per-word rewrite.

**Rhythm nouns over tempo adjectives:** "halftime", "double-time", "four-on-the-floor", "shuffle", "breakbeat" lock feel more effectively than "slow", "fast", "upbeat"

**Instrument bleed-through:** The style prompt sets a GLOBAL instrument palette; instruments bleed into ALL sections regardless of section-level tags. Warn users requiring section-specific instrumentation. See strategies reference for mitigation (accents suffix, end-placement, stems workflow).

**Exclusion prompt** (Exclude Styles content):

- **Pro/Premier:** Output as comma-separated list for Suno's dedicated Exclude Styles field. With exclusions handled separately, heavier genre language is safe in the style prompt.
- **Free tier:** No Exclude Styles field. Translate exclusion intentions into positive style prompt language.
- Sources: profile `exclusion_defaults`, user "no X" requests, genre-inferred exclusions
- Rules: keep concise (under ~200 characters for the exclusion field), be specific, prioritize 2-3 most important, add positive reinforcement alongside negatives
- **Belt-and-suspenders:** Translate negative phrases to positive style prompt language AND put originals in Exclude Styles

### Step 3: Slider & Parameter Recommendations

**Pro/Premier sliders -- choose fresh per song (anti-anchoring rule):** Pull Weirdness and Style Influence from the **Slider Guidelines table** in `references/model-prompt-strategies.md` (reloaded per Compaction Survival) by reasoning from the song's type + counter-genre needs + what each slider actually DOES -- Weirdness adds unpredictability/non-obvious choices, Style Influence governs how tightly Suno follows the prompt. **The sliders are the deliberate per-song differentiator.** Do NOT anchor to a band profile's stored `sliders:` defaults, nor nudge up/down from "what similar catalog songs used" -- that is the documented failure mode (recommending 55 by anchoring "above the 45 default" for a song that wanted ~75). **The one exception:** a bare Demo ("just make me something") may fall back to the profile's stored `sliders:` if present. Audio Influence is the slider commonly left at a standard value (~25% for Personas; see the Voices table for Voice cases). Log the chosen values + the behavioral reasoning (headless: in `decisions[]`).

**Free tier:** Note sliders unavailable. Recommend Vocal Gender selection and Lyrics Mode.

**Instrumental songs:** Skip the Vocal-Gender recommendation entirely and set Lyrics Mode to Instrumental -- there is no vocal to gender.

**Additional parameters (all tiers):**
- Lyrics Mode (Manual/Auto), Song title suggestion
- Persona reference from profile if available (Pro/Premier). When Persona active: keep additional style simple (1-2 genres, 1 mood, 2-4 instruments), Persona auto-populates Style of Music field -- build on it, don't replace
- Persona sourcing: use clear, stable lead vocals; dual Personas unreliable
- v5.5 Voices: drop gender descriptors (Voice defines them), start Audio Influence at 55-70%
- v5.5 Custom Models: drop generic production descriptors the model already knows

**Exclude Styles output:** Always comma-separated list for direct copy-paste: `screaming vocals, steel guitar, autotune, heavy distortion`

### Step 4: Wild Card Variant

Generate an experimental alternative that pushes creative boundaries.

**Twist dial** -- offer before generating: (a) genre fusion, (b) era/production shift, (c) mood inversion, (d) instrumentation flip, (e) surprise me. Default to (e).

Rules: twist one or two major elements along the chosen direction, keep it musically coherent, generate a complete style prompt, label clearly as experimental.

**Skip when:** user explicitly asked for conservative only, or headless mode (unless `include_wild_card=true`).

### Step 5: Validate & Present

**Validate first (fail-fast).** Run `uv run scripts/validate-prompt.py --style "{style_prompt}" --exclude "{exclusion_prompt}" --model "{model_name}"` on the generated prompts and read the JSON back. The script deterministically handles char/critical-zone budgets, section-tag contamination, asterisks, genre front-loading, and enumerable dangerous-word / scream-trigger / `!` detection (the `trigger` category). Fix anything it flags, then re-run. If the script cannot execute (no Python/uv), perform the equivalent checks by hand from its `--help` and the strategies reference.

**Then self-review only what the script cannot judge** (with the strategies reference reloaded): genre-term *appropriateness* for the intended sound (the script flags a flagged term but cannot decide the right substitution), dangerous-word *semantics* in context, reference-decomposition fidelity, and alignment with the user's stated intent. Do not re-scan for things the validator already computed -- that is the validator's job. Fix silently.

**Present** with version numbers (v1, v2, v3...) and a one-line formatting rationale:

```
## Style Prompt v{N} ({model_name}) -- {formatting_rationale}
{character_count}/{limit} characters

{style_prompt}

## Exclude Styles
{character_count}/~200 characters (target for Exclude Styles field)

{exclusion_prompt}

## Parameter Recommendations
- Weirdness: {value} -- {reasoning}
- Style Influence: {value} -- {reasoning}
- Vocal Gender: {value}
{persona_note_if_applicable}

## Wild Card Variant
{wild_card_prompt}
{wild_card_reasoning}
```

**Copy-ready output** after the formatted presentation:

```
### Copy-Ready: Style Prompt (paste into Suno's "Style of Music" field)
{style_prompt}

### Copy-Ready: Exclude Styles (paste into Suno's "Exclude Styles" field -- Pro/Premier only)
{exclusion_prompt}
```

**Refinement:** Invite adjustments. **Before each refine generation, reload `references/model-prompt-strategies.md`** (Compaction Survival rule) -- a long refine loop is exactly where the safety tables get compacted away. Only regenerate affected outputs (creativity change = style + wild card; model change = style formatting; exclusion change = exclusion only). Re-run `validate-prompt.py` on anything regenerated. When switching models mid-refinement, preview impact first.

**Multi-model:** If user has no model preference, generate both v4.5-conversational and v5-film-brief variants.

**Iteration guidance:** Generate 3-5 versions on Suno before modifying the prompt. Change only 1-2 variables per iteration. For v5 Pro, Suno Studio's section editing, stems, and alternates can address issues without re-prompting. At session end, offer collected summary of all versions with deltas.

**Version ledger (compaction-proof).** A multi-version refine loop is exactly long enough to compact away the version history before you can offer the end-of-session summary. As each version is presented, append a one-line entry -- `vN | {one-line prompt or its key change} | {changed variable}` -- to a `.style-prompt-ledger.md` scratch file in the working directory (create on v1). The end-of-session summary reads from this ledger, so it survives compaction regardless of how long the refine loop ran. This is a lightweight scratch log, not a Decision-Log Workspace -- one appended line per version, nothing more.

**Pro tier tip:** Legacy Editor can replace/regenerate individual sections, rearrange via drag-and-drop, and preview alternatives. Recommend for dramatic section contrasts.

**Scope note:** Cover/remix prompt building not supported. Use Suno's built-in Cover feature (see strategies reference).

**Complete** when user accepts prompt package, ends session, or hands off to another skill.

## Scripts

`validate-prompt.py` -- Deterministically validates a prompt package: style prompt character count (v4 Pro=200, v4.5+/v5=1,000), critical zone, section-tag/asterisk contamination, genre front-loading, exclusion length/count, and enumerable dangerous-word / scream-trigger / `!` detection (`trigger` category, sourced from `_shared/suno_constants.py`). Run `uv run scripts/validate-prompt.py --style "..." --exclude "..." --model "{model_name}"`. The script flags triggers; the LLM still decides the substitution. Run `--help` for details.
