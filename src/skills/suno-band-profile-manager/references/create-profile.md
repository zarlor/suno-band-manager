# Create Profile

The outcome is a saved band profile at `{band_profiles_folder}/{slug}.yaml`, a sibling decision log, and the band's empty playlist YAML. The profile's real readers are the Style Prompt Builder, Lyric Transformer and Feedback Elicitor: every field must be specific enough for the Style Prompt Builder to write a distinctive prompt from it. Vague profiles produce vague songs. The field list, caps, tier gates and Voice rules are in the profile schema, loaded with this file.

All scripts run as `uv run {skill-root}/scripts/<name>.py … --project-root {project-root}`. They read `band_profiles_folder` and `songbook_folder` from module config themselves.

## Open the floor

Invite the user to dump everything: the vibe, bands it should sound like, lyrics or poems lying around, links — and which Suno plan they are on (free / Pro / Premier), so you only offer what they can use. Ask for the plan up front because it gates half the later discovery (sliders, Voices, Custom Models, studio preferences). Once you know it, run `scripts/tier-features.py <tier>` (the JSON lists what the plan has and lacks) and prune discovery to their reality. Extract what they give, then ask only about what is missing. Absorb volunteered details out of order; never force the user back into sequence.

## Working state lives on disk

- **Decision log.** Once the band is named (the slug is `scripts/validate-profile.py --derive-filename "Band Name"`'s `slug`; a rename later is a logged decision, not a redo), start `{band_profiles_folder}/{slug}.decision-log.md`. It is canonical memory: load-bearing decisions, rejected references and descriptors, overrides. If a log already exists for this slug but no profile does, it belongs to an earlier band. Show it to the user and ask whether to continue it or start fresh (archive the old one first); appending unasked would graft another band's reasoning onto this one.
- **Draft profile.** As fields firm up, write them to `{band_profiles_folder}/drafts/{slug}.yaml` (a subfolder, so profile listings skip it), and re-read it when resuming. Conversation drops out of context; the draft does not. The draft is also the staging file you validate before saving.
- **Parked ideas.** Song concepts, lyric fragments or production experiments that are not profile fields go into the decision log as parked ideas when they come up, not at session end.

## What only you can bring

- **References.** Break each "sounds like" down into instrumentation, production style, vocal approach, energy and era. Check the sound with web search whenever the tool is available (load it if it is deferred) and say that you did; only when there is no search tool, say so and work from the user's description. Confirm the breakdown matches what they hear, and wait for that before it goes in the profile; a user who says to skip it ("I trust you, save it") waives it, and you say it wasn't confirmed. Never search the disk outside the project for references.
- **Vocals** (skip if instrumental). Push for evocative specifics ("warm, breathy female vocal with indie folk phrasing", not "female vocals"). A band with a Voice keeps timbre and gender words out of the file entirely, comments included (the decision log can quote what the owner said about the voice), and follows the schema's "A band with a Voice".
- **Style baseline.** Show the draft: "Read this like a recipe for your sound — does every ingredient belong?"
- **Exclusions.** Capture them as given. Suno handles negatives poorly, so the Style Prompt Builder turns them into positive language later.
- **Writer voice.** Offer to analyze samples now or later.
- **Accumulated learnings.** If the user already knows what works or fails for this sound, record durable patterns in `generation_learnings` / `known_working_patterns` and dead ends in `known_limitations`. Most first-timers have none; don't push.
- **Craft notes as comments.** YAML comments are kept on every save and edit, so a short `# NOTE:` beside the field it explains is a fine home for a craft note.

## Validate, present, save

1. Run `scripts/validate-profile.py {slug} --staged {band_profiles_folder}/drafts/{slug}.yaml --project-root {project-root}` for the structural checks. Fix what it finds before judging quality, and re-run it after any change to the draft (a comment included): the file you save is the file that passed.
2. Judge what the validator cannot: is the style baseline specific, the vocal direction evocative and inside its first ~200 characters, does any phrase contradict another ("natural room reverb" beside "dry"), and do the exclusions fight the genre? Fix what you can; flag what needs the user.
3. Present a **Band Identity Card**, then the full YAML in a code block (even when the user waived a draft review: it is what gets saved). The card is at most four sentences: who the band is, its sound, its voice, and what sets it apart — one sentence each. Count before presenting; anything more belongs in the YAML.
4. On approval, write it all in one batch:
   - `scripts/apply-profile.py --save --in {band_profiles_folder}/drafts/{slug}.yaml --own-log --project-root {project-root}`. The file is written verbatim, comments included, and the call refuses to overwrite an existing profile. `--own-log` says the slug's decision log is the one you started under "Working state" (an earlier band's log was settled then); leave it off if you didn't start one this session, and a leftover log comes back as `existing_decision_log` for the user to decide. Then delete the draft, and the `drafts/` folder if it is left empty.
   - `scripts/scaffold-playlist.py {slug} --project-root {project-root}` creates the band's empty playlist YAML. Without it the validator flags the band as soon as a song is added, and playlist work has nowhere to write.
   - Record the meaningful decisions in the decision log: chosen slug, references kept or rejected, tier, any trims.
