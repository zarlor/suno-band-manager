---
name: create-song
description: Orchestrated song creation — gathers direction, runs Lyric Transformer + Style Prompt Builder, presents complete Suno-ready package.
code: CS
---

**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`

**Preference shard first.** If `{project-root}/docs/mac-preferences-packages.md` exists (the wake lists it under `voice_context.preference_shards`), read it in full before anything else here: it holds the owner's package, prompt, slider and pipeline rules. The pipeline guard blocks a package presented without it. Before a fresh, never-done or variety claim about the catalog, read `{project-root}/docs/mac-preferences-verification.md` the same way, if it exists.

# Create Song

The main creative workflow. Guide the user from initial inspiration to a complete Suno-ready package: structured lyrics with metatags + model-specific style prompt + exclusion prompt + parameter recommendations.

## Step 1: Infer the Mode (Soft Gate)

**Do not ask the user to choose a mode.** Infer it from their input and confirm with a soft gate:

| Mode | Inferred When | Behavior |
|------|---------------|----------|
| **Demo** | Short request, low detail, "just make me something" | Minimal questions. Use band profile defaults (or sensible genre defaults). Get genre/mood and go. |
| **Studio** | Detailed request, specific asks, album work, 3+ parameters provided | Full songwriter's workshop. Section-by-section control. |
| **Jam** | "Surprise me," experimental requests, "try something weird" | Creativity cranked up. Push boundaries. Wild card variants emphasized. Cross-genre fusion encouraged. |

**Soft confirmation:** After inferring, confirm naturally: "Sounds like a Studio session — let me dig in." or "Quick Demo vibe — I'll keep it fast." The user can redirect.

**First-time users:** Don't explain modes up front. Infer Demo and work. Mention modes after the first song: "By the way, if you ever want more control, just say 'let's go Studio mode.'"

**Default mode from memory:** If the user has a saved default mode, use it as the starting inference unless their current input clearly signals otherwise.

## Step 2: Gather Direction

> **Load the relevant disciplines as the work calls for them** (the sanctum's `memory/disciplines/`). When you start drafting or processing any creative material inline (a lyric swing, a structural sketch, pasted external text), load `memory/disciplines/workshop-capture.md` and capture the verbatim material to its WIP file with `uv run {skill-root}/scripts/capture-wip.py` before discussing it. When you build a song-direction candidates list or make any "this is fresh/new territory for the band" claim, load `memory/disciplines/catalog-verification-discipline.md` and `memory/disciplines/thematic-discipline.md`. Run `uv run {skill-root}/scripts/genre-coverage.py "{project-root}" --check --band {band-slug}` first; if it exits 1, regenerate the index (drop `--check`), then read `docs/{band-slug}-genre-coverage.md` before asserting. Absence from the index isn't proof of freshness — grep the songbook and profile before any never-done claim.

Collect what you need for the mode. Not everything is required.

**Capture-Don't-Interrupt:** The user may mention things outside the current step — preferences ("I always want raw vocals"), profile ideas, refinement thoughts. Capture them silently and route them after the package is presented: preferences → memory; profile ideas → offer after the song; refinement notes → into the package assembly.

**Always needed (at least one):** song direction — genre, mood, vibe, topic, "sounds like X meets Y," or raw text/poem to transform.

**Valuable context:**
- **Band profile** — If yes, invoke `suno-band-profile-manager` to load it (or read `docs/band-profiles/{name}.yaml` directly). If none exist and they seem interested, offer to create one after the song.
- **Source text** — If provided, the Lyric Transformer becomes the primary skill. If the piece is meant to be *spoken* rather than sung, mention Suno's Speech model (beta, 2026-10-01; plain paragraphs, no section tags) as a possible route alongside `[Spoken Word]` inside a song. It's untested here; see `references/SUNO-REFERENCE.md` → "Platform Changes — 2026-10-03".
- **Model/tier** — From profile, from memory (User Preferences), or ask. Current models (every earlier model was retired 2026-09-09): **v6** (Pro/Premier default), **v6-wild** (Pro/Premier, exploratory — optional; running the unchanged primary prompt on it is an alternative wild card), **v6-mini** (Free). A profile that still names a retired model gets built for v6; say so in the handoff.
- **Voice / Custom Model** — On a paid tier, check whether one is configured and note it for Steps 4–5. A Voice replaces gender descriptors in the style prompt; a Custom Model replaces generic production descriptors it already encodes. If none is configured and the band has a settled sound with 10 or more finished songs in one lane — or the user keeps saying v6 sounds generic next to their older songs — mention once, after the package, that a Custom Model trained on those songs is the fix users report most for v6, and that training costs 100 credits and re-uploading Suno songs spends download allowance.
- **Reference tracks** — Capture "sounds like X meets Y" to pass to the Style Prompt Builder.

**Studio mode:** before building, draw out the emotional core, the arc and its turn, the hook line, the sounds the user already hears, and who's singing. **Jam mode:** one question — "Give me a starting point — a word, a feeling, a weird mashup idea — and I'll run with it." **Demo mode:** infer what you can from the request and profile.

**Creative riff (Studio and Jam):** you're a producer, not just a listener — offer one proactive idea per song (an unexpected genre fusion, an instrumentation choice, a structural twist), framed as an idea, not a directive.

**Instrumental:** skip the Lyric Transformer; default exclusions "no vocals, no humming, no choirs, instrumental only"; note the Instrumental toggle for Pro/Premier users (on the reworked v6 Create sidebar, one user found no Instrumental toggle as of 2026-10-05 — if it isn't there, leave Lyrics empty and let the exclude list carry the anti-vocal load); the package shows "Lyrics: Instrumental (no vocals)" instead of a lyrics block.

**Non-English:** add the language to the style prompt (e.g., "sung in French"), warn that metatag reliability may differ with non-Latin scripts, and pass the language to the Lyric Transformer.

**Reference decomposition:** decompose each reference into concrete sonic descriptors and **show your work** before building, so the user can confirm. If you don't confidently know the artist, ask what they like about the sound rather than guessing. Store the decomposition with the band profile data for reuse.

**URLs:** Mac cannot listen to audio — say so. Try to get the song/artist from the URL and look up its sonic character (web search, when available), then ask what catches their ear. For a Suno link, note they can use Extend or Remix directly in Suno.

**Long text (~400+ words):** before invoking the Lyric Transformer, offer three options — (1) condense to one song, (2) split into a multi-song suite, (3) pick the strongest sections — and pass the choice on.

**Song extension:** load the original from memory/songbook. Flag a requested change that diverges from the original's feel ("smooth transition or deliberate contrast?"). Tell them: "Use Extend from the clip's menu in Suno to continue from where the song ends. Paste these new sections into the lyrics field when extending." Warn that extending on a different model than the original can sound inconsistent.

**Zero-input Demo:** "surprise me" with no starting point → pick a genre fusion, build a style prompt with auto-lyrics, and present it with personality: "Alright, here's what I'm feeling today — a little swamp blues meets synthwave. Trust me on this one."

### Handoff Checkpoint (before formal pipeline)

Before Steps 3 and 4, surface the confirmed direction:

> "Here's what I'm taking into the build: **[genre/mood]**, source text is **[title or summary]**, band profile **[name or none]**, model **[selection]**, exclusions **[list]**. Anything I'm missing or getting wrong?"

Wait for confirmation and update if corrected. Demo mode: one sentence. Studio/Jam: more thorough.

**Tier not on record yet:** add one plain line — "Building this for Free (v6-mini, no Exclude Styles or sliders). On Pro or Premier? Say so and I'll build for v6." Write the answer into `memory/owner/preferences.md` the moment it lands, silently: no message about the write before the package (say it in one line beside the package).

After Steps 3 and 4 return, apply **Transparency**: compare skill output against the confirmed direction. If either skill added elements not discussed (new imagery, genre modifiers, unexpected metatags), surface them — "The style prompt builder added X — keep or cut?" — before assembling.

## Steps 3 & 4: Run Skills in Parallel (Headless Mode)

> Section tags: only recognized tags (a custom tag gets sung as a lyric), and Bridge means something new where Breakdown means something less; the Lyric Transformer holds the full tag catalog.

Load the sanctum's `memory/disciplines/package-assembly.md` first; it says how to run them. The two skills are independent — the Style Prompt Builder doesn't need the lyrics — so they run in parallel, and the owner hears nothing until Step 5: no "laying down the foundation now", no "package came back", no checkpoint notice — the package is the next thing they read.

### Step 3: Lyric Transformer (headless)

Skip it for an instrumental or when the user supplied finished lyrics they want used as-is.

**With source text:** invoke `suno-lyric-transformer --headless` with the text, band profile (for writer-voice constraints), song direction, language if non-English, `creativity_mode` from the interaction mode, and `song_path` when the song already has a songbook entry. Map the interaction mode to options: Demo → balanced defaults (ST + CC + RA + CD); Studio → let the user choose; Jam → bolder structure with the writer's own lines (`creativity_mode: experimental`); a full rewrite or new rhymes only when the owner asks for one.

**Expected return:** the transformer's Transform Return: `transformed_lyrics`, `transformation_summary`, `decision_log`, `intentional_keeps`, and `flat_copy_lyrics` only when needed. `transformed_lyrics` keeps the writer's spacing verbatim (the transformer checks it by script) — the package's Lyrics field carries that spaced version. A flat copy is only a labelled paste aid. Without a `song_path`, the transformer writes no decision log; keep its `decision_log` and `intentional_keeps` for the post-publish pass.

**Only a topic/mood (no source text):**
- **Demo:** default to Suno's auto-lyrics — "Lyrics: Auto-generated by Suno to match your style." Don't ask; skip the Lyric Transformer.
- **Studio:** ask whether they want to write lyrics (then transform them) or use auto-lyrics.
- **Jam:** auto-lyrics unless they volunteer text.

### Step 4: Style Prompt Builder (headless)

Invoke `suno-style-prompt-builder --headless` with the builder's own field names: `band_profile`, `tier`, `model`, `genre_mood`, `reference_tracks`, `vocal_direction`, `requests` (the direction and specific asks, "acoustic only"), `creativity_mode` (same mapping as Step 3), `exclusions` (only the owner's own "no X" asks and `memory/work/default-exclusions.md`; the builder reads the profile's `exclusion_defaults` itself and keeps those this prompt pulls toward), `voice` / `persona` / `custom_model`, `instrumental` and `working_title`. The wild card is on by default.

**Expected return:** the builder's success JSON: style prompt and character count, exclusions with rationales, model, vocal gender, the v6 options and sliders with reasoning, title suggestion, wild card, validation report, and `handoff_notes`. Route each `handoff_notes` item to the song's WIP file before presenting the package — `capture-wip.py` with `--source "style builder" --label "Builder notes"`, the notes on stdin through a quoted heredoc — they are mid-build ideas the owner shouldn't lose.

**Prompt adjustments to ask for:**
- The **v6 prompt architecture** (PREVIEW guidance the builder carries): ordered production direction, each instrument's job per section, the vocal placed rather than praised, both edges stated, positive text only with every negative in Exclude Styles. When lyrics are transformed too, pass the key per-section instructions to the Lyric Transformer so its section cues restate the style map word-for-word.
- **Voice** → no gender descriptors in the prompt; note the active Voice in the package.
- **Custom Model** → no generic production descriptors the model already handles (if it encodes "lo-fi tape warmth," don't repeat it); spend the prompt on what's new.
- **Specificity pays** — "fingerpicked nylon guitar with room reverb" beats "acoustic guitar."

## Step 5: Present the Package

One copy-paste-ready package, in the order the fields sit on Suno's Create screen, so the owner fills it top to bottom:

**Voice (or Audio / Inspo) → Lyrics → Style Prompt → Exclude Styles → Settings (Model, then the Controls panel) → Title → Save to → Wild Card**

The values are the skills' returns, unchanged: the transformer's `transformed_lyrics` (the writer's spacing intact), and the builder's style prompt with its character count and limit, excludes, model, settings with their reasons, title and wild card. What the returns don't settle:

- Before presenting, read the package against the song's brief (a voice-over bed stays out of the voice's way; an instrumental has no vocal words). A mismatch you find is fixed, by re-running the builder with the change in `requests`, not shipped with a question about it.

- Each pasteable field — Lyrics, Style Prompt, Exclude Styles, Title, the wild-card prompt — goes in its own code block. A flat copy of the lyrics, when the transformer returned one, is a second block labelled "Flat copy — paste aid only".
- No lyrics block: say "Lyrics: Auto-generated by Suno — set Lyrics Mode to Auto" or "Lyrics: Instrumental (no vocals)".
- Under a Voice, note that gender descriptors were left out of the prompt; under a Custom Model, that the production descriptors it encodes were. A Persona (Pro/Premier, now inside the Voices menu) fills Styles itself, so keep style edits light; how pre-v6 Personas and Voices behave on v6 is undocumented, and one short test generation settles it. Inspo (Pro/Premier, unverified on v6) gets 3–5 reference tracks.
- Free tier has no commercial rights: when the song is meant for public or commercial use (a podcast intro, an ad, a channel's theme, a release), say so in one line beside the package — Pro or Premier downloads carry commercial use.
- Free tier has no Exclude Styles and no sliders. In the Exclude Styles slot, say the exclusions are carried by the style prompt's positive phrasing; under Settings, give the model (v6-mini), Vocal Gender and Lyrics Mode, and note that the sliders are Pro/Premier (whether Free shows Variety, Max Mode, Duration or Personalize is unverified: say exactly that, no more and no less, and give no value or default for any of them, "Listen for" notes included). Give no Pro-only values in a Free package, not even as "on Pro it would be": no exclude list, no slider numbers. One line offers to rebuild for Pro; it is required in every Free package.
- Settings follow the Controls panel top to bottom — Vocal Gender, Duration, Max Mode, Weirdness, Style Influence, Audio Influence (only once a Voice or Audio is added), Variety, Personalize — with Lyrics Mode beside the model. Exclude Styles is the panel's first row, which is why it follows the Style Prompt.
- Save to names the band's Suno folder, so the take lands in the right workspace.
- When the wild card's excludes match the primary's, say so in a line rather than repeating them (owner, 2026-09-17); different excludes go in a code block with the reason.
- A style prompt over its limit gets a warning that Suno silently truncates the end, and an offer to trim.
- Credit each choice to whoever made it: the builder's instrumentation, sliders and excludes are the builder's ("the builder went with…"), the transformer's structure is the transformer's, and only what you decided is "I". The owner tunes what they can see the source of.
- A short "what's in it" note may go above the package. "Listen for" notes go after the wild card: at most about three, each with an observable answer (what a running test needs, or a plain fact like brass, high notes, a tail). Never ask the owner to grade a take against the package's intent, or to judge what a script can measure after download (`docs/mac-preferences.md` → the listening-question pre-flight check).

**First-use Suno walkthrough (the first song only, or when asked):** show it once, then note `Suno panel walkthrough: shown` in `memory/owner/preferences.md`. In plain words: pick the model at the top right; leave "Describe your song" empty, since the Lyrics and Styles fields carry everything; add a Voice, Audio or Inspo from the chips if the package names one; fill the rest top to bottom in the package's order; generate a few takes — Suno reads the same inputs differently each time — and listen in the browser before downloading anything.

**Contextual Suno tip (vary by context, max 1 per package):**
- If lyrics include `[Intro]`: "Tip: Suno's [Intro] tag is notoriously unreliable. If the intro sounds off, try regenerating just the first 10 seconds."
- If model is v6: "Tip: keep Variety at Exact style for this package, and turn Max Mode on (2× credits) for any take you might keep — it's applied at generation, so it can't be added to a finished take. Leave it off only for throwaway sketches of a style's feel."
- Always, with the wild card: "Tip: the wild card uses the same model and sliders as the primary — it's the prompt that varies. For a quick alternative wild card, run the primary prompt unchanged on v6-wild, which adds its own less-predictable variation. Worth one Create even if the primary lands." On Free (no v6-wild), the tip is the first sentence only.
- If Weirdness > 65: "Tip: High Weirdness can produce unexpected gems — generate 5+ versions and pick the wildest one that works."

**After presenting:**

1. **Generate → inspect → refine:** "Go try this on Suno — generate 3-5 versions and listen through them. Suno interprets the same inputs differently each time, so casting a wider net gives you more to work with. When you've heard the results, come back and tell me what you think — that's where songs really come together." To find a style's feel cheaply, a couple of Max Mode–off sketches can come first; the takes you might keep run with Max Mode on. When the owner is testing one change against another, offer about 4 takes (two Creates) per version as a suggestion, with the reason: on v6 the spread between takes can be bigger than the change being tested, and a measured outside series saw the ranking flip between 2 and 4 takes. How many takes they run is their call.
2. **Listen in the browser; download only the keeper** (or a take that needs measuring). Suno caps downloads on every tier (`references/SUNO-REFERENCE.md` → "Plan Comparison", the "Song downloads" row). On a paid tier, say how many downloads are left this cycle when `memory/work/downloads.md` has the number, and update that count the moment the owner says they downloaded.
3. **Section replacement over full regeneration:** if a version is mostly right but has a weak section, suggest section replacement (the Song Editor; v6 also takes plain-language section edits, which launch-week users report as uneven). "If the verse is perfect but the chorus needs work, try replacing just the chorus section instead of rolling the dice on a whole new generation."
4. **Route captured items** from Capture-Don't-Interrupt.
5. If working with a band profile, offer to save successful elements to the profile.
6. **Checkpoint** the song with `uv run {skill-root}/scripts/update-current.py "{project-root}" --song "<title>" --text "(<band>) — style prompt: <its first ~100 characters>; <model>; <mode>; round <n>; next: <what to pick up>"`, never by appending to the file.

## Step 6: Quick Refinement (Optional)

If the user comes back with feedback in the same conversation, handle small things conversationally without the full Refine Song loop — but only changes that don't touch skill output.

| Handle here | Re-run the skill headless (Package Assembly shard) | Go to Refine Song (RS) |
|---|---|---|
| Adjust a slider or setting value | Any style-descriptor change ("make it more aggressive") → Style Prompt Builder | Vague dissatisfaction: "it doesn't sound right" |
| Swap a word or phrase in the lyrics (no tag or structure change) | Any exclusion change → Style Prompt Builder | Several interrelated issues: "the vibe is off and the vocals are wrong" |
| Change the title or Save to folder | Any tag or structure change ("add a bridge") → Lyric Transformer | Reactions that need triage: "it's not what I heard in my head"; 2+ generations still unsatisfied; a fundamental direction change |

Refine Song (`references/refine-song.md`) diagnoses through the suno-feedback-elicitor skill and rebuilds only the changed parts through the pipeline — pass it the creativity mode and the current package.

**Diminishing returns:** after 2-3 rounds, suggest a different approach: "We've been tweaking this one pretty hard. Suno has some randomness baked in — want to run a few more takes of the current package and pick the one that clicks?" (Takes cost credits, not downloads — listen before downloading.)

## Step 7: Post-Publish

When the owner has downloaded or published the keeper, load `references/post-publish.md`.
