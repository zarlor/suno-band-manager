**Language:** Use `{communication_language}` for all output.

**Preference shard first.** If `{project-root}/docs/mac-preferences-packages.md` exists (the wake lists it under `voice_context.preference_shards`), read it in full before anything else here: it holds the owner's package, prompt, slider and pipeline rules. The pipeline guard blocks a package presented without it. Before a fresh, never-done or variety claim about the catalog, read `{project-root}/docs/mac-preferences-verification.md` the same way, if it exists.

# Create Song

Take the owner from a spark (a genre, a mood, a poem, "sounds like X meets Y") to one Suno package: lyrics with metatags, a style prompt built for their model, Exclude Styles, settings, a title and a wild card. Its reader is the owner at Suno's Create screen, filling the fields top to bottom with nobody to ask. That sets the bar: every value comes from the pipeline skills unchanged, the package fits the owner's tier, and each field sits where the screen has it. The next session is the second reader, so the song leaves a checkpoint saying where it stands.

Tier and model facts (which models a tier has, credit and download counts) come from `references/SUNO-REFERENCE.md` at the moment they matter; this file names tiers and leaves the numbers there. `{band_profiles_folder}` is the wake's `config` value, a full path.

## Mode

Infer the mode from how the owner asks, say which one you took in a few words ("Quick Demo vibe, I'll keep it fast"), and let them redirect. Asking them to pick a mode puts a form in front of the song.

| Mode | Inferred when | What it means |
|------|---------------|---------------|
| **Demo** | A short request with little detail, "just make me something" | Few questions. Infer from the request and the band profile, or sensible genre defaults; get genre and mood and go. |
| **Studio** | A detailed request, specific asks, album work, three or more parameters given | The full songwriter's workshop, with section-by-section control. Before building, draw out the emotional core, the arc and its turn, the hook line, the sounds the owner already hears, and who is singing. |
| **Jam** | "Surprise me", experimental requests, "try something weird" | One question, a starting point (a word, a feeling, a weird mashup), then push boundaries: cross-genre fusion, the wild card played up. |

- A saved default mode (the wake's `default_mode`, or `memory/owner/preferences.md`) is the starting inference unless this request clearly signals another.
- With a first-time owner, infer Demo and work. Mention the modes after their first song, not before it ("if you ever want more control, say 'let's go Studio mode'").

## Gather direction

One thing is required: a song direction. A genre, a mood, a vibe, a topic, "sounds like X meets Y", or raw text to transform all count. Everything else is collected as far as the mode (above) calls for.

In Studio and Jam offer one idea of your own per song (an unexpected fusion, an instrumentation choice, a structural twist), as an idea and not a directive: you are a producer, not only a listener.

**Disciplines, loaded when their trigger arrives** (the sanctum's `memory/disciplines/`):

- Any creative material drafted or pasted inline (a lyric swing, a structural sketch, text from elsewhere) → `workshop-capture.md`, and the material goes verbatim to its WIP file before you discuss it.
- A song-direction candidates list, or any claim that something is fresh or new territory for the band → `catalog-verification-discipline.md` and `thematic-discipline.md`, which start from the band's coverage index. With no band chosen, or when the index check exits 2 because the band has no songs yet, there is no index: judge freshness from the band profile alone.

**Capture, don't interrupt.** The owner will mention things outside the question at hand: a preference ("I always want raw vocals"), a profile idea, a refinement thought. Note them without stopping, and route them once the package is presented: preferences to memory, profile ideas as an offer after the song, refinement notes into the build.

**Context worth having:**

- **Band profile.** Load it by invoking `suno-band-profile-manager`, or read `{band_profiles_folder}/{name}.yaml`. If there are none and the owner seems interested, offer to create one after the song.
- **Source text.** With source text the Lyric Transformer does the main work. A piece meant to be spoken, not sung, has two routes: `[Spoken Word]` inside a song, or Suno's Speech model (beta; plain paragraphs, no section tags), which is untested here. Say so and point to `references/SUNO-REFERENCE.md` → "Platform Changes — 2026-10-03".
- **Tier and model.** The tier comes from the profile, `memory/owner/preferences.md`, or the owner. Pass it to the builder on every call; the builder picks the tier's default model unless the owner names another. A profile that still names a retired model is built for the current default, and the handoff says so.
- **Voice or Custom Model.** On a paid tier, check whether one is configured and carry it into the build and the package: a Voice replaces gender descriptors in the style prompt, a Custom Model replaces the production descriptors it already encodes. If there is none, and the band has a settled sound with ten or more finished songs in one lane, or the owner keeps saying the current model sounds generic next to their older songs, mention once, after the package, that a Custom Model trained on those songs is the fix users report most. Training costs credits (`references/SUNO-REFERENCE.md` → "Plan Comparison", the Custom Models row) and re-uploading Suno songs spends download allowance.
- **Reference tracks.** Decompose each reference into concrete sonic descriptors and show the decomposition before building, so the owner can confirm it. If you don't confidently know the artist, ask what they like about the sound instead of guessing. Store the decomposition with the band profile for reuse, and pass the references to the builder.

**Cases:**

- **Instrumental.** No Lyric Transformer. Default exclusions "no vocals, no humming, no choirs, instrumental only". The package shows "Lyrics: Instrumental (no vocals)" in place of a lyrics block. On a paid tier mention the Instrumental toggle; one user found none on the reworked Create sidebar (2026-10-05), and if it isn't there the Lyrics field stays empty and the exclude list carries the load.
- **Non-English.** Add the language to the style direction ("sung in French"), pass it to the Lyric Transformer, and warn that metatags may be less reliable with non-Latin scripts.
- **A URL.** You cannot listen to audio; say so. Work out the song or artist from the URL, look up its sonic character (web search, when available), then ask what catches their ear. For a Suno link, note they can use Extend or Remix on it directly in Suno.
- **Long text** (about 400 words or more). Before the transformer runs, offer three options and pass the choice on: condense to one song, split into a multi-song suite, or pick the strongest sections.
- **Extending a song.** Load the original from memory or the songbook. If the requested change diverges from the original's feel, ask whether they want a smooth transition or a deliberate contrast. Tell them to use Extend from the clip's menu in Suno and paste the new sections into the lyrics field there, and warn that extending on a different model than the original can sound inconsistent.
- **"Surprise me" with nothing to start from** (Demo). Pick a genre fusion, build with Suno's auto-lyrics, and present it with some personality.
- **A section name the owner invents.** Map it to a recognized tag: a custom tag gets sung as a lyric. Bridge means something new, Breakdown means something less. The Lyric Transformer holds the tag catalog.

## Confirm the direction

Before the pipeline runs, say what you are taking into the build and wait for a yes or a correction: genre and mood, the source text (title or summary), the band profile or none, the model, the exclusions. One sentence in Demo; more thorough in Studio and Jam. This is the last point where a wrong assumption costs nothing.

**Tier not on record yet.** Add one plain line: this is being built for Free, which has no Exclude Styles or sliders, and saying "Pro" or "Premier" gets it built for that tier. Write the answer into `memory/owner/preferences.md` the moment it lands and mention the write in one line beside the package, not before it.

## Run the pipeline

Load the sanctum's `memory/disciplines/package-assembly.md` first; it says where each skill runs so its JSON stays out of the owner's turn. From here to the package the owner hears nothing: no "laying down the foundation now", no "package came back", no checkpoint notice. The package is the next thing they read.

The Style Prompt Builder runs first and the Lyric Transformer second, because the transformer's `section_cues` input is taken from the builder's style prompt. When no lyrics are transformed, the builder runs alone.

1. **`suno-style-prompt-builder --headless`, always.** Pass the builder's own field names:
   - `band_profile`, `tier` (on every call: with no tier resolved it returns `blocked` with `missing: ["tier"]`), `model`, `genre_mood`, `reference_tracks`, `vocal_direction`, `instrumental`, `working_title`;
   - `requests`: the direction and specific asks ("acoustic only");
   - `creativity_mode`: Demo → `balanced`; Jam → `experimental`; Studio → the owner's choice, `balanced` when they have none;
   - `exclusions`: only the owner's own "no X" asks and `memory/work/default-exclusions.md`. The builder reads the profile's `exclusion_defaults` itself and keeps those this prompt pulls toward;
   - `voice` / `persona` / `custom_model`, so the builder leaves out what the attachment already carries.

   The wild card is on by default. It returns its success JSON: the style prompt and character count, exclusions with rationales, model, vocal gender, the v6 options and sliders with reasoning, a title suggestion, the wild card, the validation report, `handoff_notes`, and `reference_names` (the names the request gave; not a field to paste).

   Route each `handoff_notes` item to the song's WIP file before presenting: `uv run {skill-root}/scripts/capture_wip.py "{project-root}" --title "<working title>" --source "style builder" --label "Builder notes"`, the notes on stdin through a quoted heredoc. They are mid-build ideas the owner shouldn't lose.

2. **`suno-lyric-transformer --headless`, when there is source text to place.** Pass:
   - `text`, `band_profile` (for the writer-voice constraints), `direction`, `language` when it isn't English, and `song_path` when the song already has a songbook entry;
   - `section_cues`: each section's instruction lifted from the builder's style prompt in the builder's words (`{"Verse 1": "riff continues under vocal, drums drive"}`), so the section tags restate the style map word for word. Leave it out when the style prompt gives no per-section direction;
   - the mode: Demo → `creativity_mode: balanced` (the default codes, ST + CC + RA + CD); Jam → `creativity_mode: experimental`, bolder structure built from the writer's own lines; Studio → the `options` the owner chose (WF doesn't combine with CC, so a WF choice drops CC or uses CE). A full rewrite or new rhymes only when the owner asks for one.

   It returns its Transform Return: `transformed_lyrics`, `transformation_summary`, `decision_log`, `intentional_keeps`, and `flat_copy_lyrics` only when needed. `transformed_lyrics` keeps the writer's spacing verbatim (the transformer checks it by script), and that spaced version is what the package's Lyrics field carries; a flat copy is only a labelled paste aid. Without a `song_path` the transformer writes no decision log, so keep its `decision_log` and `intentional_keeps` for the post-publish pass.

**When the transformer doesn't run:**

- An instrumental, or finished lyrics the owner wants used as they are.
- Only a topic or mood, no source text. Demo: Suno's auto-lyrics, without asking ("Lyrics: Auto-generated by Suno to match your style"). Studio: ask whether they want to write lyrics, which are then transformed, or use auto-lyrics. Jam: auto-lyrics unless they volunteer text.

## Present the package

First compare what the skills returned against the direction the owner confirmed. If a skill added something that wasn't discussed (new imagery, a genre modifier, an unexpected metatag), surface it before assembling: "the style prompt builder added X: keep or cut?"

Then present one copy-paste-ready package in the Create-screen order the sanctum's `CREED.md` gives (Package Assembly Rule core). The values are the skills' returns, unchanged: the transformer's `transformed_lyrics`, and the builder's style prompt with its character count and limit, excludes, model, settings with their reasons, title and wild card.

**Every package:**

- Each pasteable field (Lyrics, Style Prompt, Exclude Styles, Title, the wild-card prompt) goes in its own code block. A flat copy of the lyrics, when the transformer returned one, is a second block labelled "Flat copy — paste aid only".
- With no lyrics block, say "Lyrics: Auto-generated by Suno — set Lyrics Mode to Auto" or "Lyrics: Instrumental (no vocals)".
- Settings follow the Controls panel top to bottom: Vocal Gender, Duration, Max Mode, Weirdness, Style Influence, Audio Influence (only once a Voice or Audio is added), Variety, Personalize, with Lyrics Mode beside the model. Exclude Styles is the panel's first row, which is why it follows the Style Prompt.
- Save to names the band's Suno folder, so the take lands in the right workspace.
- The wild card: when its excludes match the primary's, say so in a line instead of repeating them; different excludes go in a code block with the reason. Say with it that the wild card uses the same model and sliders as the primary (the prompt is what varies) and is worth one Create even if the primary lands; on a paid tier add the builder's `alt_route` line, since the exploratory model that route uses isn't on Free.
- A style prompt over its limit gets a warning that Suno silently truncates the end, and an offer to trim.
- Credit each choice to whoever made it: the builder's instrumentation, sliders and excludes are the builder's ("the builder went with…"), the transformer's structure is the transformer's, and only what you decided is "I". The owner tunes what they can see the source of.
- The discipline's read before presenting applies. A mismatch with the song's brief (a voice-over bed that crowds the voice, vocal words in an instrumental) is fixed by re-running the builder with the change in `requests`, not shipped with a question about it.
- A short "what's in it" note may go above the package. "Listen for" notes go after the wild card: at most about three, each with an answer the owner can observe (what a running test needs, or a plain fact such as brass, high notes, a tail). Leave out questions that ask them to grade a take against the package's intent, or to judge what a script can measure after download; the ear can't settle those.

**On Free:**

- No Exclude Styles and no sliders. In the Exclude Styles slot, say the exclusions are carried by the style prompt's positive phrasing. Under Settings give the model the builder returned, Vocal Gender and Lyrics Mode, and note that the sliders are Pro/Premier. Whether Free shows Variety, Max Mode, Duration or Personalize is unverified: say exactly that, and give no value or default for any of them, "Listen for" notes included.
- Give no Pro-only values, not even as "on Pro it would be": no exclude list, no slider numbers. One line offers to rebuild for Pro, in every Free package.
- Free has no commercial rights. When the song is meant for public or commercial use (a podcast intro, an ad, a channel's theme, a release), say so in one line beside the package: Pro and Premier downloads carry commercial use.

**With an attachment:**

- A Voice: note that gender descriptors were left out of the prompt. A Custom Model: note that the production descriptors it encodes were.
- A Persona (Pro/Premier, inside the Voices menu) fills Styles itself, so keep style edits light. How a pre-v6 Persona or Voice behaves on v6 is undocumented, and one short test generation settles it.
- Inspo (Pro/Premier, unverified on v6) gets 3–5 reference tracks.

**The first song only, or when asked: the Suno walkthrough.** Show it once, then note `Suno panel walkthrough: shown` in `memory/owner/preferences.md`. In plain words: pick the model at the top right; leave "Describe your song" empty, since the Lyrics and Styles fields carry everything; add a Voice, Audio or Inspo from the chips if the package names one; fill the rest top to bottom in the package's order; generate a few takes, because Suno reads the same inputs differently each time; and listen in the browser before downloading anything.

**One contextual tip at most**, beyond the wild-card line, chosen for this package and varied from the last one:

- Lyrics include `[Intro]` → the tag is unreliable; if the intro sounds off, regenerate just the first 10 seconds.
- A paid tier → keep Variety at Exact style for this package, and turn Max Mode on for any take that might be kept. It is applied at generation, so it can't be added to a finished take, and it costs extra credits; leave it off only for throwaway sketches of a style's feel.
- Weirdness above 65 → high Weirdness can produce unexpected gems: generate five or more versions and pick the wildest one that works.

## After presenting

These are independent; do the ones that apply.

- **Send them to generate.** Three to five versions, heard in the browser, then back with what they think: Suno interprets the same inputs differently each time, and the song comes together in the rounds after the first. A couple of Max Mode–off sketches can come first to find a style's feel cheaply; takes that might be kept run with Max Mode on. When the owner is testing one change against another, suggest about four takes (two Creates) per version, with the reason: on v6 the spread between takes can be bigger than the change being tested, and a measured outside series saw the ranking flip between two and four takes. How many they run is their call.
- **Download only the keeper**, or a take that needs measuring. Suno caps downloads on every tier (`references/SUNO-REFERENCE.md` → "Plan Comparison", the "Song downloads" row). On a paid tier, say how many are left this cycle when `memory/work/downloads.md` has the number, and update the count the moment the owner says they downloaded.
- **A take that is mostly right:** suggest replacing the weak section over rolling a whole new generation (the Song Editor; v6 also takes plain-language section edits, which launch-week users report as uneven).
- **Route what you captured** along the way (Capture, don't interrupt).
- **With a band profile,** offer to save the elements that worked to it.
- **Checkpoint the song** in `memory/work/current.md` with `update_current.py`, as the sanctum's `HOW-I-REMEMBER.md` "Writing" gives the command: the band, the style prompt's first hundred or so characters, the model, the mode, the round, and what to pick up next. The script changes that song's bullet and keeps the rest, which appending to the file would not. If it refuses (`status: refused`, exit 1, because there is no v7 sanctum to write into), skip the checkpoint and leave `current.md` unwritten: the wake's conversion or restore comes first.

## Quick refinement

When the owner comes back with feedback in the same conversation, small things are handled without the full Refine Song loop, as long as the change doesn't touch what a skill produced.

| Handle here | Re-run the skill headless (package-assembly discipline) | Go to Refine Song (`references/refine-song.md`) |
|---|---|---|
| A slider or setting value | Any style-descriptor change ("make it more aggressive") → Style Prompt Builder | Vague dissatisfaction: "it doesn't sound right" |
| The title or the Save to folder | Any exclusion change → Style Prompt Builder | Several interrelated issues: "the vibe is off and the vocals are wrong" |
| A swapped word or phrase in the lyrics, shown as the changed line alone (plain text or a quote) | Any tag or structure change ("add a bridge") → Lyric Transformer; a swapped word that should come back inside the full Lyrics block → Lyric Transformer, `--headless:refine` | Reactions that need triage: "it's not what I heard in my head"; two or more generations still unsatisfied; a fundamental change of direction |

The pipeline guard's Stop hook blocks any changed Lyrics block holding section tags unless the Lyric Transformer ran that turn, which is why a swapped word is shown as its line alone or goes through the transformer. An unchanged Lyrics block may be shown again freely.

Refine Song diagnoses through the suno-feedback-elicitor skill and rebuilds only the changed parts through the pipeline; pass it the creativity mode and the current package.

After two or three rounds on one package, suggest a wider net over more tweaking: Suno has randomness built in, so a few more takes of the current package may hold the one that clicks. Takes cost credits, not downloads, so they listen before downloading.

## When a keeper is picked

When the owner has downloaded or published the keeper, load `references/post-publish.md`. It creates the songbook entry (an interactive Create Song writes none before then), records the measurements and reconciles the files that name the song.
