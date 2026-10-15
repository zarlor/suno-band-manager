---
name: create-song
description: Orchestrated song creation — gathers direction, runs Lyric Transformer + Style Prompt Builder, presents complete Suno-ready package.
code: CS
---

**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`

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

> **Load the relevant disciplines as the work calls for them** (the sanctum's `memory/disciplines/`). When you start drafting or processing any creative material inline (a lyric swing, a structural sketch, pasted external text), load `memory/disciplines/workshop-capture.md` and capture the verbatim material to its WIP file BEFORE discussing it. When you build a song-direction candidates list or make any "this is fresh/new territory for the band" claim, load `memory/disciplines/catalog-verification-discipline.md` and `memory/disciplines/thematic-discipline.md`. Run `uv run {skill-root}/scripts/genre-coverage.py "{project-root}" --check --band {band-slug}` first; if it exits 1, regenerate the index (drop `--check`), then read `docs/{band-slug}-genre-coverage.md` before asserting. Absence from the index isn't proof of freshness — grep the songbook and profile before any never-done claim.

Collect what you need for the mode. Not everything is required.

**Capture-Don't-Interrupt:** The user may mention things outside the current step — preferences ("I always want raw vocals"), profile ideas, refinement thoughts. Capture them silently and route them after the package is presented: preferences → memory; profile ideas → offer after the song; refinement notes → into the package assembly.

**Always needed (at least one):** song direction — genre, mood, vibe, topic, "sounds like X meets Y," or raw text/poem to transform.

**Valuable context:**
- **Band profile** — If yes, invoke `suno-band-profile-manager` to load it (or read `docs/band-profiles/{name}.yaml` directly). If none exist and they seem interested, offer to create one after the song.
- **Source text** — If provided, the Lyric Transformer becomes the primary skill. If the piece is meant to be *spoken* rather than sung, mention Suno's Speech model (beta, 2026-10-01; plain paragraphs, no section tags) as a possible route alongside `[Spoken Word]` inside a song. It's untested here; see `references/SUNO-REFERENCE.md` → "Platform Changes — 2026-10-03".
- **Model/tier** — From profile, from memory (User Preferences), or ask. Current models (every earlier model was retired 2026-09-09): **v6** (Pro/Premier default), **v6-wild** (Pro/Premier, exploratory — optional; running the unchanged primary prompt on it is an alternative wild card), **v6-mini** (Free). A profile that still names a retired model gets built for v6; say so in the handoff.
- **Voice / Custom Model** — On a paid tier, check whether one is configured and note it for Steps 4–5. A Voice replaces gender descriptors in the style prompt; a Custom Model replaces generic production descriptors it already encodes.
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

**Tier not on record yet:** add one plain line — "Building this for Free (v6-mini, no Exclude Styles or sliders). On Pro or Premier? Say so and I'll build for v6." Write the answer into `memory/owner/preferences.md` the moment it lands.

After Steps 3 and 4 return, apply **Transparency**: compare skill output against the confirmed direction. If either skill added elements not discussed (new imagery, genre modifiers, unexpected metatags), surface them — "The style prompt builder added X — keep or cut?" — before assembling.

## Steps 3 & 4: Run Skills in Parallel (Headless Mode)

> **Load the Package Assembly discipline** `{project-root}/_bmad/memory/suno-agent-band-manager/memory/disciplines/package-assembly.md` before assembling. The always-loaded `CREED.md` core carries the Package Assembly Rule core; the discipline file carries the rest (Violation Tells, Agent-vs-Skill tool choice, highest-risk contexts, refinement presentation scope).
>
> Section tags: only recognized tags (a custom tag gets sung as a lyric), and Bridge means something new where Breakdown means something less; the Lyric Transformer holds the full tag catalog.

**Run both skills in parallel and headless, and say nothing until Step 5.** They are independent — the Style Prompt Builder doesn't need the lyrics. Send both calls in a single message as two Agent subagent invocations, each running one skill headless; Agent keeps the skill's JSON as a tool result rather than a visible turn (the shard's "Tool Choice" section). Narrating the run or showing a raw return leaves the owner with partial packages and JSON instead of one pasteable package.

### Step 3: Lyric Transformer (headless)

Skip it for an instrumental or when the user supplied finished lyrics they want used as-is.

**With source text:** invoke `suno-lyric-transformer --headless` with the text, band profile (for writer-voice constraints), song direction, language if non-English, the per-section cues from the style map (Step 4), and `song_path` when the song already has a songbook entry. Map the interaction mode to options: Demo → balanced defaults (ST + CC + RA + CD); Studio → let the user choose; Jam → full rewrite encouraged.

**Expected return:** the transformer's Transform Return: `transformed_lyrics`, `transformation_summary`, `decision_log`, `intentional_keeps`, and `flat_copy_lyrics` only when needed. `transformed_lyrics` keeps the writer's spacing verbatim (the transformer checks it by script) — the package's Lyrics field carries that spaced version. A flat copy is only a labelled paste aid. Without a `song_path`, the transformer writes no decision log; keep its `decision_log` and `intentional_keeps` for the post-publish pass.

**Only a topic/mood (no source text):**
- **Demo:** default to Suno's auto-lyrics — "Lyrics: Auto-generated by Suno to match your style." Don't ask; skip the Lyric Transformer.
- **Studio:** ask whether they want to write lyrics (then transform them) or use auto-lyrics.
- **Jam:** auto-lyrics unless they volunteer text.

### Step 4: Style Prompt Builder (headless)

Invoke `suno-style-prompt-builder --headless` with the band profile, tier and model, song direction (genre, mood, reference tracks, vocal direction), creativity mode (same mapping as Step 3), the user's exclusions and specific requests ("no piano," "acoustic only"), any attached Voice / Persona / Custom Model, and a working title. The wild card is on by default.

**Expected return:** the builder's success JSON, already in Step 5 order: style prompt and character count, exclusions with rationales, model, vocal gender, the v6 options and sliders with reasoning, title suggestion, wild card, validation report, and `handoff_notes`. Route each `handoff_notes` item to the song's workshop or WIP file — they are mid-build ideas the owner shouldn't lose.

**Prompt adjustments to ask for:**
- The **v6 prompt architecture** (PREVIEW guidance the builder carries): ordered production direction, each instrument's job per section, the vocal placed rather than praised, both edges stated, positive text only with every negative in Exclude Styles. When lyrics are transformed too, pass the key per-section instructions to the Lyric Transformer so its section cues restate the style map word-for-word.
- **Voice** → no gender descriptors in the prompt; note the active Voice in the package.
- **Custom Model** → no generic production descriptors the model already handles (if it encodes "lo-fi tape warmth," don't repeat it); spend the prompt on what's new.
- **Specificity pays** — "fingerpicked nylon guitar with room reverb" beats "acoustic guitar."

## Step 5: Present the Complete Package

Assemble everything into a single, copy-paste-ready output. **Present items in the order they appear in Suno's Create screen**, so the user can work top to bottom without jumping around:

**Voice (or Audio / Inspo) → Lyrics → Style Prompt → Exclude Styles → Settings (Model, then the Controls panel top to bottom) → Title → Save to (band folder) → Wild Card**

*(Panel layout observed 2026-09-17, v6: model picker top right; a "Describe your song" box at the top — leave it empty for a custom package, the Lyrics and Styles fields carry everything; then the optional chips Audio / Voices / Inspo; then Lyrics; then Styles; then the **Controls** panel, which replaced "More Options"; then Song Title; then Save to.)*

- **Never lead with the Title, and never put the Style Prompt ahead of the Lyrics.** The Title is the last field filled in.
- **Settings follow the Controls panel top to bottom:** Vocal Gender, Duration, Max Mode, Weirdness, Style Influence, Audio Influence (shown only once a Voice or Audio is added), Variety, Personalize. Exclude Styles is the panel's first row, which is why it comes straight after the Style Prompt.
- **Save to** comes after the Title: name the band's Suno folder (the panel's "Save to…" row), so the take lands in the right workspace.
- **Every pasteable field goes in its own code block:** Lyrics, Style Prompt, Exclude Styles, Title and the wild-card prompt.
- **Don't repeat the wild card's Exclude Styles when they match the primary's** (owner, 2026-09-17) — say they're the same in a short line. List them in a code block only when the wild card needs different excludes, and say why.
- A short "what's in it" or "what changed" note may go above the package. "Listen for" notes go after the wild card — **at most about three, and only things with an observable answer** (what a running test needs, or a plain fact like brass/high notes/a tail). Never ask the owner to grade a rendering against the package's intent, and never ask what a script can measure after download. See `docs/mac-preferences.md` → the listening-question pre-flight check.

```
## Your Suno Package

{If a Voice applies:}
### Voice
{voice_name}
Note: Voice handles vocal identity — gender descriptors have been omitted from the style prompt below.

{If a Custom Model applies:}
### Custom Model
{custom_model_name}
Note: Production descriptors covered by this model have been omitted from the style prompt below. Prompt focuses on song-specific direction.

{If Pro/Premier and Persona applies:}
### Persona
{persona_name} (from: {source_song})
Note: This auto-populates the Styles field. Keep style modifications simple below.
Note: Personas still work and are found inside the Voices menu — they were relocated, not removed. A Voice is the stronger tool for locking vocal identity; a Persona captures style essence instead. How Personas and Voices made before v6 behave on v6 is undocumented — one short test generation settles it.

{If Pro/Premier and Inspo applies (availability on v6 unverified):}
### Inspo
Recommended Inspo playlist: {list of 3-5 reference tracks}
Note: Use Inspo to channel this vibe before setting other parameters.

### Lyrics
{Complete transformed lyrics with metatags from Lyric Transformer, the writer's spacing intact}
{If a flat copy was needed: a second block labelled "Flat copy — paste aid only"}
{Or: "Lyrics: Auto-generated by Suno — set Lyrics Mode to Auto" if no lyrics created}
{Or: "Lyrics: Instrumental (no vocals)" if instrumental mode}

### Style Prompt ({model_name})
{character_count}/{limit} characters

{style_prompt}

{If character_count > limit: "⚠ This prompt exceeds Suno's {limit}-character limit and will be silently truncated. The last {overage} characters will be lost. Want me to trim it?"}

### Exclude Styles
{If Pro/Premier:}
{comma-separated list, e.g.: screaming vocals, steel guitar, autotune, heavy distortion}

{If Free tier:}
Not available on Free tier — exclusions are handled through positive phrasing in the style prompt above.

### Settings
{If free tier:}
- Model: v6-mini
- Vocal Gender: {recommendation}
- Lyrics Mode: {Manual or Auto}
- Note: Weirdness, Style Influence, and Audio Influence sliders are available on Pro/Premier plans; whether Free shows Variety, Max Mode, Duration, or Personalize is not verified

{If paid tier:}
- Model: {v6 | v6-wild} — {reasoning} (the model picker at the top of the Create form)
- Lyrics Mode: {Manual or Auto}
- Controls panel, in order (Exclude Styles, the panel's first row, is covered above):
  - Vocal Gender: {recommendation}
  - Duration: {Auto | m:ss} — {reasoning}
  - Max Mode: {On for any take you might keep | Off only for throwaway style-feel sketches} — 2× credits; buys consistency through the whole song, and it's applied at generation, so it can't be added to a finished take
  - Weirdness: {value}% — {reasoning} (controls creative deviation: lower = safer, higher = more experimental)
  - Style Influence: {value}% — {reasoning} (controls prompt adherence: lower = looser interpretation, higher = tighter to your style prompt)
  - Audio Influence: {value}% — {reasoning}
    {If Persona selected:} Persona slot: 15-25% effective range (25% default, reduce for era mismatch)
    {If Voice selected:} Voice slot: runs much higher and is per-voice — use the value the Style Prompt Builder returned (it holds the canonical ranges and Suno's raise-then-rebuild escalation); don't recite a scale from memory
  - Variety: Off (the leftmost notch, Exact style) — keeps this style prompt exactly as written (any higher notch rewrites it before generating)
  - Personalize: Off — keeps your My Taste profile from reshaping this package

### Song Title
{suggested_title} — in its own code block, like the other pasteable fields

### Save to
{band's Suno workspace, e.g. the band's display name}

### Wild Card Variant — The Unexpected Take
{wild_card_style_prompt}
{One-line pitch for why this twist could work, staying inside the band's core sound: "What if we took this country ballad into a stripped 1970s outlaw arrangement? Same song, same lane — rawer production, and the fiddle carries the hook instead of the band."}
```

**First-use Suno walkthrough (the first song only, or when asked):** show it once, then note `Suno panel walkthrough: shown` in `memory/owner/preferences.md` so it doesn't repeat. A returning user can ask for it again.

"**How to use this in Suno:** Work top to bottom, in the package's order. Pick the model at the top right (v6 unless the package says otherwise). Leave 'Describe your song' empty — the Lyrics and Styles fields carry everything. Add your Voice, Audio or Inspo from the chips if the package names one. Paste the Lyrics, then the Style Prompt into Styles. Open the Controls panel: Exclude Styles first, then Vocal Gender, Duration, Max Mode, Weirdness, Style Influence, Audio Influence, Variety and Personalize as listed. Add the Song Title, pick the Save to folder, and hit Create. Generate a few takes — Suno reads the same inputs differently each time — and listen in the browser before you download anything."

**Contextual Suno tip (vary by context, max 1 per package):**
- If lyrics include `[Intro]`: "Tip: Suno's [Intro] tag is notoriously unreliable. If the intro sounds off, try regenerating just the first 10 seconds."
- If model is v6: "Tip: keep Variety at Exact style for this package, and turn Max Mode on (2× credits) for any take you might keep — it's applied at generation, so it can't be added to a finished take. Leave it off only for throwaway sketches of a style's feel."
- Always, with the wild card: "Tip: the wild card uses the same model and sliders as the primary — it's the prompt that varies. For a quick alternative wild card, run the primary prompt unchanged on v6-wild, which adds its own less-predictable variation. Worth one Create even if the primary lands."
- If Weirdness > 65: "Tip: High Weirdness can produce unexpected gems — generate 5+ versions and pick the wildest one that works."

**After presenting:**

1. **Generate → inspect → refine:** "Go try this on Suno — generate 3-5 versions and listen through them. Suno interprets the same inputs differently each time, so casting a wider net gives you more to work with. When you've heard the results, come back and tell me what you think — that's where songs really come together." To find a style's feel cheaply, a couple of Max Mode–off sketches can come first; the takes you might keep run with Max Mode on. When the owner is testing one change against another, offer about 4 takes (two Creates) per version as a suggestion, with the reason: on v6 the spread between takes can be bigger than the change being tested, and a measured outside series saw the ranking flip between 2 and 4 takes. How many takes they run is their call.
2. **Listen in the browser; download only the keeper** (or a take that needs measuring). Suno caps downloads on every tier (`references/SUNO-REFERENCE.md` → "Plan Comparison", the "Song downloads" row). On a paid tier, say how many downloads are left this cycle when `memory/work/downloads.md` has the number, and update that count the moment the owner says they downloaded.
3. **Section replacement over full regeneration:** if a version is mostly right but has a weak section, suggest section replacement (the Song Editor; v6 also takes plain-language section edits, which launch-week users report as uneven). "If the verse is perfect but the chorus needs work, try replacing just the chorus section instead of rolling the dice on a whole new generation."
4. **Route captured items** from Capture-Don't-Interrupt.
5. If working with a band profile, offer to save successful elements to the profile.

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
