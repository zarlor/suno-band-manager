# Create Profile

The outcome is a saved band profile at `{band_profiles_folder}/{slug}.yaml`, a sibling decision log, and the band's empty playlist YAML. The profile's real readers are the Style Prompt Builder, Lyric Transformer and Feedback Elicitor: every field must be specific enough for the Style Prompt Builder to write a distinctive prompt from it. Vague profiles produce vague songs. The field list, types and limits are in `references/profile-schema.md`. Load it now, together with `references/tier-features.md`.

All scripts run as `uv run scripts/<name>.py … --project-root {project-root}`. They read `band_profiles_folder` and `songbook_folder` from module config themselves.

## Open the floor

Invite the user to dump everything: the vibe, bands it should sound like, lyrics or poems lying around, links — and which Suno plan they are on (free / Pro / Premier), so you only offer what they can use. Ask for the plan up front because it gates half the later discovery (sliders, Voices, Custom Models, studio preferences). Once you know it, run `scripts/tier-features.py <tier>` and prune discovery to their reality. Extract what they give, then ask only about what is missing. Absorb volunteered details out of order; never force the user back into sequence.

## Working state lives on disk

- **Decision log.** Once the band is named (propose a kebab-case slug if they don't give one; a rename later is a logged decision, not a redo), start `{band_profiles_folder}/{slug}.decision-log.md`. It is canonical memory: load-bearing decisions, rejected references and descriptors, overrides. If a log already exists for this slug but no profile does, it belongs to an earlier band. Show it to the user and ask whether to continue it or start fresh (archive the old one first). Never silently append to it.
- **Draft profile.** As fields firm up, write them to `{band_profiles_folder}/drafts/{slug}.yaml` (a subfolder, so profile listings skip it), and re-read it when resuming. Conversation drops out of context; the draft does not. The draft is also the staging file you validate before saving.
- **Parked ideas.** Song concepts, lyric fragments or production experiments that are not profile fields go into the decision log as parked ideas when they come up, not at session end.

## What only you can bring

- **References.** Break each "sounds like" down into instrumentation, production style, vocal approach, energy and era. Use web search to check the sound when you have it; if you don't, say so and work from the user's description. Confirm the breakdown matches what they hear.
- **Vocals** (skip if instrumental). Push for evocative specifics ("warm, breathy female vocal with indie folk phrasing", not "female vocals"). When a Voice (`voice_id`) is set, leave gender and timbre out of the style baseline: the Voice already defines them. A band that uses several cloned Voices for different track types records them in `voices:`, with `vocal.voice_id` as the primary.
- **Style baseline.** Front-load the essentials in the first ~200 characters, where they influence generation most. Show the draft: "Read this like a recipe for your sound — does every ingredient belong?"
- **Exclusions.** Capture them as given. Suno handles negatives poorly, so the Style Prompt Builder turns them into positive language later.
- **Writer voice.** Offer to analyze samples now or later.
- **Accumulated learnings.** If the user already knows what works or fails for this sound, record durable patterns in `generation_learnings` / `known_working_patterns` and dead ends in `known_limitations`. Most first-timers have none; don't push.
- **Craft notes as comments.** YAML comments are kept on every save and edit, so a short `# NOTE:` beside the field it explains is a fine home for a craft note.

## Validate, present, save

1. Run `scripts/validate-profile.py {band_profiles_folder}/drafts/{slug}.yaml --project-root {project-root}` for the structural checks (length, enums, exclusions cap, tier/model/slider consistency). `--derive-filename "Band Name"` gives the slug. Fix what it finds before judging quality.
2. Judge what the validator cannot: is the style baseline specific, the vocal direction evocative, and do the exclusions fight the genre? Fix what you can; flag what needs the user.
3. Present a **Band Identity Card** (3-4 sentences on who this band is), then the YAML.
4. On approval, write it all in one batch:
   - `scripts/apply-profile.py --save --in {band_profiles_folder}/drafts/{slug}.yaml --project-root {project-root}`. The file is written verbatim, comments included, and the call refuses to overwrite an existing profile. If its JSON carries `existing_decision_log`, resolve that with the user first. Then delete the draft.
   - `scripts/scaffold-playlist.py {slug} --project-root {project-root}` creates the band's empty playlist YAML. Without it the validator flags the band as soon as a song is added, and playlist work has nowhere to write.
   - Record the meaningful decisions in the decision log: chosen slug, references kept or rejected, tier, any trims.
