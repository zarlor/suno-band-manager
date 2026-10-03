---
name: refine-song
description: Bring back a Suno take — diagnose what's off through the Feedback Elicitor and rebuild only the changed parts of the package through the pipeline.
code: RS
---

**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`

# Refine Song

The owner has tried a package on Suno and is back with a take. This is the one place that handles it: diagnose what's off, then rebuild only the parts that change, through the same pipeline that built the package. "FL", "feedback loop" and "give feedback on a take" all land here — the suno-feedback-elicitor skill is the diagnosis step inside this flow, not a separate stop on Mac's menu.

**Headless-eligible:** true.

## Headless Mode

If invoked with `--headless` or structured JSON input, skip all interactive steps (the handoff checkpoints, the "want me to rebuild…?" offers, the conversational loop). The input is taken as confirmed.

**Input contract:**
```json
{
  "song_ref": "optional — songbook path or title of the song being refined; if omitted, the caller must supply original_style_prompt/original_lyrics",
  "original_style_prompt": "optional — the prompt being refined (looked up from song_ref if absent)",
  "original_lyrics": "optional — the lyrics being refined",
  "feedback": "required — the listener reaction / adjustment request to act on",
  "model": "optional — model the song used (inferred from tier/profile if absent)",
  "tier": "optional — free|pro|premier (else MEMORY.md User Preferences)",
  "band_profile": "optional — profile name for voice constraints",
  "creativity_mode": "optional — conservative|balanced|experimental, default balanced"
}
```

**Process (no interaction):** Read `MEMORY.md` User Preferences for a missing tier (warn and assume Free if unresolved). Run the Feedback Elicitor headless on the feedback and context, then route its `adjustment_recommendations` back through the Style Prompt Builder and/or Lyric Transformer headless exactly as Step 3 does. The Package Assembly Rule still binds — load `creed-package-assembly.md`. Assemble and return.

**Output:** the refined package delta as structured JSON (only what changed — style prompt, exclusions, lyrics, settings — in the create-song `package` field names), plus the standard headless result envelope (`status`, `capability`, `artifact_path`, `summary`, `warnings`). A refinement that would overwrite a *published* songbook entry is a Law-3-gated write — stage it and report it as a warning rather than applying it. Any other durable write first passes `uv run scripts/validate-path.py "<target path>" write`; a denied path is skipped and reported in `warnings`. If `feedback` is missing or no original prompt/lyrics can be resolved, return `status: blocked` with the reason.

## Step 1: Gather Context

**From this session** (create-song ran earlier): the package, model, settings, band profile and intent are already in context.

**Starting fresh:** look the song up before asking for technical details. `MEMORY.md`'s Recently Published section is already loaded; for anything else run `uv run scripts/songbook-catalog.py "{project-root}" --title "<words they used>"` (or `--band <slug> --since <date>` for "the one from last week"). Confirm: "Is this the one you're refining? {title / style prompt preview}". If nothing matches, ask what they generated and with which prompts.

**Minimal context path:** If the user can't give details ("I just hit Create"), work with what they have: infer the model from tier (Free = v6-mini; paid = v6 unless the package ran on v6-wild), don't ask about sliders on Free, and accept a plain reaction — "I pasted X and got Y, but it sounds too Z" is enough. The Feedback Elicitor handles vague feedback.

**Downloads:** the take is heard in the browser; refinement doesn't need it downloaded. Measuring it does — when a script reading would settle the question (tempo, loudness, a section that ran together), say that downloading it uses one of the cycle's downloads (the count is in `MEMORY.md`'s Downloads section) and update the count if they download.

**Reading the take** (2026-10-03): what plays isn't always what was asked for. Trust the audio and the owner's ear over the song page's displayed style text, which shows the input or Variety's rewrite, not what landed. For a near-keeper that only needs a better ending, a fuller final chorus or a louder vocal, the suno-feedback-elicitor skill's `references/technical-resolution.md` → "Repair Ladder for a Near-Keeper" lists things to try before a full re-roll. They apply only before the take is handed over.

### Handoff Checkpoint (before diagnosis)

> "Here's what I'm sending to the feedback pipeline: original style prompt is **[prompt or 'unknown']**, your feedback is **[summary of what they said]**, and I'm reading this as **[clear/vague/contradictory/technical]**. Sound right?"

Wait for confirmation. This stops vague feedback being over-read into specific parameter changes the user didn't intend.

## Step 2: Diagnose (Feedback Elicitor)

Invoke `suno-feedback-elicitor --headless` with the feedback, original style prompt, lyrics, band profile, model, slider settings, creativity mode, the intent summary, and the song's iteration log on a repeat round. **Expected return:** its `adjustment_recommendations` (style prompt add/remove/reorder notes, exclusions, sliders, lyric changes, model suggestion, Studio features) with `confidence_scores` and `decision_log` — no prose.

Then apply **Transparency**: tell the owner what the diagnosis found and which changes it proposes before rebuilding anything.

## Step 3: Rebuild Only What Changed

> **Load the Package Assembly shard** `{project-root}/_bmad/_memory/band-manager-sidecar/creed-package-assembly.md`. Re-running the pipeline is a package-assembly path; the shard's **Refinement presentation scope** and **Tool Choice** sections govern this step and Step 4.

Offer each rebuild the recommendations call for ("Want me to rebuild the style prompt with these changes?"):

- **Style prompt or exclusion changes** → `suno-style-prompt-builder --headless:refine`, passing the Feedback Elicitor's `adjustment_recommendations` straight through (the builder accepts that shape).
- **Lyric changes** → `suno-lyric-transformer --headless:refine` with the current lyrics as `source_lyrics`, the adjustments, and `song_path` when the song has a songbook entry (the transformer then appends its decision log beside it and won't undo a logged intentional keep).
- **Both** → run them in parallel when independent; when a lyric change shapes the style (a new bridge needs a musical transition), run lyrics first.
- **Slider or setting changes only** → no skill re-run; present them as a short note.
- **Model suggestion** → "The Feedback Elicitor thinks {v6-wild | v6 | v6-mini} might handle this better because of [reason]. Want to try the next generation on it?"
- **Studio features** → present the workflow (e.g., "Try Replace Section on the chorus instead of regenerating the whole song"). Replace Section and stems are Pro **and** Premier; **Suno Studio is Premier-only** and nothing in Studio 2.0 reaches Pro — don't offer a Studio workflow to a Pro user.

## Step 4: Present the Update

Present only what changed, per the shard's Refinement presentation scope, under a "What Changed" list:

```
## {band-name} Refinement Update

### What Changed
- {Bullet list of adjustments and why}

{Only the sections that changed, in Step 5 package order}
```

Then: "Give this version a spin on Suno — listen in the browser, and come back with what you hear. That's how records get made."

## Step 5: Profile Update Check

If the feedback revealed a **systematic preference** rather than a one-song tweak, suggest a profile update ("You've mentioned wanting rawer vocals twice now — want me to update your band profile's vocal direction?") and make it through `suno-band-profile-manager`.

**Published songs:** a refinement that edits a song already in the songbook is a published-attribute change. Its cross-file updates (playlist YAML, voice file, songbook Settings block) go in the same write batch — the sanctum `CREED.md` "Sync at the point of change" principle — and a rename runs `references/reconcile.md` in that batch. Afterwards, `uv run scripts/validate-sidecar.py "{project-root}" --format json` is the backstop. A refinement of the current, not-yet-saved iteration has nothing to sync.

## Loop

Each time the owner returns with a take, loop back to Step 2; the Feedback Elicitor triages fresh each round. After 2-3 rounds on the same song, suggest a wider net: "We've been dialing this in for a few rounds — Suno's got some randomness baked in. Want to run a few more takes of the current package and keep the one that clicks?"
