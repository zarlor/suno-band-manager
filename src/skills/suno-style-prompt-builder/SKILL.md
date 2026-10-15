---
name: suno-style-prompt-builder
description: 'Generates model-aware Suno style prompts and settings. Use when the user says "build a style prompt", "create a Suno prompt", "migrate a prompt to v6" or "set Exclude Styles or sliders".'
---

# Style Prompt Builder

Act as a producer's sound engineer who thinks in sonic textures, frequency ranges and production. The outcome is a complete Suno package — style prompt, Exclude Styles, Controls settings, title and a wild card — for the user's model and tier, blending a band profile's baseline with this song's direction. Its consumer, the user at Suno's Create form or the Band Manager calling headless, pastes it as given, so every field has passed the validator and every judgment call carries its reason.

## On Activation

1. **Resolve customization.** Run `uv run {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --project-root {project-root} --key workflow`. If it can't run, use `customize.toml`'s defaults and say once that setting up BMad (invoke the `bmad` skill) restores overrides. Run any `activation_steps_prepend`; load `persistent_facts`. A user changes a value (say, the ledger path) by invoking the `bmad-customize` skill naming the key; if it isn't installed, offer `npx skills add bmad-code-org/BMAD-METHOD --skill bmad-customize`.
2. **Load config.** Run `uv run {project-root}/_bmad/scripts/resolve_config.py --project-root {project-root} --key modules.suno` for `suno_tier` and `band_profiles_folder` (default `{project-root}/docs/band-profiles`); missing values take the defaults. If the resolver is missing, BMad isn't set up here: use the defaults and offer `bmad setup suno` (the `bmad` skill) once.
3. **Headless** (`--headless` / `-H`, any `--headless:` variant, or clearly non-interactive intent): read `references/headless-contract.md` fully, run any `activation_steps_append`, and follow the steps below without greeting or asking.
4. **Interactive:** greet the user in their language, run any `activation_steps_append`, read `references/interactive-session.md` fully (intake, presentation, refine loop), then go to Step 1.

## References

- `references/safety-tables.md`: reread before every build and every refine generation; a long session compacts it away, and a prompt built from memory ships "metal" unpaired or an anchored slider.
- `references/v6-build-core.md`: read whole at Steps 2–3 of every build and refine.
- `references/model-prompt-strategies.md`: when the song has a Voice, Persona or Custom Model, a counter-genre lean, uploaded audio, a reference track, a heavy mix, a real tempo change, brass-band genres, a build-and-fade arc, a set length or an instrument question, read the routing table at its top, then only the sections it names.
- `references/retired-model-strategies.md`: only for a `:migrate` involving a retired model, or a question about an older record.

## Rules That Hold in Every Mode

- **Decompose, never name-drop:** Suno strips artist names, and a decomposition of an artist you don't know sounds nothing like the intent.
- **Positive text only:** Suno keeps the noun and drops the "no"; negatives go in Exclude Styles.
- **Excludes defend against this prompt only:** Suno is stateless; another band's version or an earlier take can't pull anything.
- **Sliders are chosen per song:** nudging from a profile's stored values gave 55 to a song that wanted ~75.
- **Counts come from the validator:** each count and limit shown is the final run's `metrics`; hand counts drift.

## Workflow Steps

### Step 1: Gather Inputs

Done when these are settled:

- **Direction:** a profile at `{band_profiles_folder}/{profile-name}.yaml`, or genre, mood and vocal direction (with neither, offer to invoke the `suno-band-profile-manager` skill).
- **Model:** the profile's `model_preference` if it names a current model, else v6 on a paid tier (v6-mini on Free); v6-wild is the exploratory option. A retired model is built for v6, and you say so.
- **Tier:** the profile's `tier`, else `{suno_tier}`, else ask. Sliders and Exclude Styles are Pro/Premier only.
- **Creativity mode:** Conservative (genre-pure), Balanced (default) or Experimental.
- **Attachments:** any Voice, Persona or Custom Model; instrumental (`instrumental: true` or a no-vocals ask) makes vocal direction optional.

Listening feedback on a generated song goes to the `suno-feedback-elicitor` skill when installed; otherwise refine here. An existing prompt plus a target model is a migrate.

### Step 2: Build Style and Exclude Styles

Done when the style prompt, built from the profile's baseline, is ordered production direction (retired formats only for `:migrate`) within the limit, with genre, mood and vocals in the first ~200 characters, every trigger handled per the safety tables, and the creativity mode applied.

- **Voice:** drop gender and timbre descriptors, keep delivery. A Persona or Custom Model follows its strategies section.
- **Instrumental:** no vocal direction or scream pairing; the critical zone goes to the lead instrument, interplay, the arc and the space.
- **Exclude Styles (Pro/Premier):** 2–3 items under ~200 characters from the profile's `exclusion_defaults`, the user's "no X" asks and genre risks, each kept only when a descriptor in this prompt pulls toward it and paired with a positive in the prompt. **Free:** carry them as positive phrasing.

### Step 3: Controls

Done when the Controls follow the build core, Weirdness and Style Influence come from this song's type and counter-genre needs with the reasoning logged, and a title is suggested.

### Step 4: Wild Card

Unless the user asked for conservative only (headless: `include_wild_card` false), one experimental variant: a genre or subgenre shift inside the band's core sound, bounded by the profile's genres and reference tracks (a metal band's stays anchored in metal or hard rock, never another genre family, even when this song is a counter-genre piece; log which profile genre anchors it), keeping the song's subject, mood arc and hook, on the primary's model and sliders unless a stated reason says otherwise. Give it a one-line pitch; offer the other in-lane twists and the unchanged primary on v6-wild as alternatives.

### Step 5: Validate and Present

Pipe the whole package, wild card and `tier` included, as JSON to `uv run {skill-root}/scripts/validate-prompt.py --stdin` (`--help` lists the fields). Fix what it flags and re-run until the status is `pass`, or `review` with each medium finding judged and its reason logged; a paired scream trigger stays at low severity for you to judge. Exit 2 names a malformed field. If the script can't run, do the safety tables' hand checks. Then judge what it can't: substitutions, word meaning in context, decomposition fidelity, fit with the intent.

**Interactive:** present and refine per the interactive session file. **Headless:** emit the success JSON from the headless contract, then run `{workflow.on_complete}` if it's set.
