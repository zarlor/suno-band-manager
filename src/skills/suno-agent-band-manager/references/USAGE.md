# Suno Band Manager -- Usage Guide

This guide covers everything you need to know about working with Mac, the Suno Band Manager agent. Mac works with any LLM CLI that supports the [Agent Skills](https://agentskills.io) standard — see `INSTALLATION.md` at the repository root for setup.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Interaction Modes](#2-interaction-modes)
3. [Creating Songs](#3-creating-songs-the-main-workflow)
4. [Band Profiles](#4-band-profiles)
5. [Refining Songs](#5-refining-songs-bring-back-a-take)
6. [Direct Skill Access](#6-direct-skill-access)
7. [Songbook & Memory](#7-songbook--memory)
8. [Headless/Automation](#8-headlessautomation)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Getting Started

### First-Run Experience

The very first time you invoke Mac, he runs through a setup flow to learn how you work. Here is what happens under the hood:

1. Mac checks whether `{project-root}/_bmad/_memory/band-manager-sidecar/` exists.
2. If it does not exist, Mac runs `scripts/pre-activate.py` to scaffold the directory.
3. Mac loads `init.md` and walks you through the first-run setup.

### Setup: One Question, Then Learning as You Go

Mac doesn't open with a form. He asks one thing -- "What kind of music are you looking to make today?" -- and gets you into a song. The rest he picks up as you work and saves to memory the moment he learns it:

| What Mac learns | How | Why It Matters |
|---|---|---|
| **Your Suno plan** (Free, Pro, Premier) | Until you say, Mac builds for Free and tells you so on your first package: "Building this for Free (v6-mini, no Exclude Styles). On Pro or Premier? Say so and I'll build for v6." | Determines which models, sliders, and features Mac can recommend. Free users get v6-mini; Pro/Premier unlock v6 and v6-wild, the Weirdness/Style Influence sliders, the v6 Variety and Max Mode controls, Voices, Custom Models, and more. Suno Studio is Premier-only. It also sets your **download budget** -- from 2026-09-03 Suno caps downloads (Free 7 lifetime, Pro 20/month, Premier 60/month, with Studio exports exempt), and commercial rights attach to a permitted download rather than to the plan itself. Mac keeps count of the downloads you've used this cycle (tell him when you download), says what's left when you pick a keeper, and steers you to listen in the browser and download only the keeper. |
| **How you like to work** (Demo, Studio, Jam) | Starts in Demo; notices if you're hands-on and suggests Studio after the first song | Sets your default interaction mode. You can switch anytime -- even mid-song. |
| **Your band or project** | When you mention one, Mac offers to create a band profile after the song | Profiles keep every song's sound consistent. |
| **What you always or never want** | "I hate autotune" becomes a default exclusion | Your baseline exclusions, genres, and vocal preferences -- starting points you can change anytime. |

All of these preferences are changeable through conversation at any time -- no need to edit config files or re-run the installer.

### What Gets Created

After setup, Mac scaffolds the sanctum (memory) directory. The files you'll care
about most:

| File | Purpose |
|------|---------|
| `MEMORY.md` | Your preferences, active work, essential context (curated; loaded every session) |
| `INDEX.md` | A thin map of the sanctum — what every file holds |
| `sessions/YYYY-MM-DD.md` | Raw per-day session notes (the full play-by-play) |
| `patterns.md` | Musical preferences Mac learns over time |
| `chronology.md` | Session timeline |

Mac also creates `access-boundaries.md`, which defines where the agent can read and write:

- **Read access:** `docs/band-profiles/` and the sidecar memory folder
- **Write access:** Sidecar memory folder only
- **Deny zones:** Everything else

---

## 2. Interaction Modes

Mac has three interaction modes plus auto-detection. Each one changes how much Mac asks you before generating output.

### Demo Mode

**When to use:** You want something fast. "Just make me a song." Minimal questions, maximum speed.

**What Mac does:**
- Asks for genre/mood at most
- Uses band profile defaults (or sensible genre defaults)
- Defaults to Suno's auto-lyrics if you do not provide text
- Skips the songwriter's workshop questions

**Example interaction:**

```
You: Make me something moody and electronic.
Mac: Got it -- moody electronic it is. Let me put together your package.
     [Generates complete Suno package with no further questions]
```

### Studio Mode

**When to use:** You want full creative control. Album work, specific vision, detailed customization.

**What Mac does:** Runs the full songwriter's workshop. Expect questions like:
- "What's the emotional core of this song? What feeling should someone walk away with?"
- "Is there a story arc -- a beginning, middle, turn?"
- "What's the one line you want stuck in people's heads?"
- "Any specific instruments, textures, or production choices you hear in your head?"
- "Vocal direction -- who's singing this? What do they sound like?"

**Example interaction:**

```
You: I want to build a track around a poem I wrote about leaving home.
Mac: Great material for a song. Let's dig in --
     What's the emotional core here? Is it loss, freedom, nostalgia, or something more complicated?
You: It's bittersweet -- sad to leave but excited about what's next.
Mac: Love that tension. Is there a turn in the poem -- a moment where the mood shifts from one to the other?
```

### Jam Mode

**When to use:** You want to experiment. "Surprise me." Push boundaries, try weird combinations.

**What Mac does:**
- Asks one question: "Give me a starting point -- a word, a feeling, a weird mashup idea -- and I'll run with it."
- Cranks creativity up. Cross-genre fusion encouraged.
- Wild card variants emphasized.
- If you say "surprise me" with zero input, Mac picks a random genre fusion and runs with it.

**Example interaction:**

```
You: Surprise me.
Mac: Alright, here's what I'm feeling today -- a little swamp blues meets synthwave.
     Trust me on this one.
     [Generates full package with an experimental edge]
```

### Auto-Detect

If your opening message includes 3 or more specific parameters (model, sliders, vocal direction, genre, metatags), Mac skips mode selection and goes straight to Studio mode:

```
You: I need a v6 style prompt for a dreamy indie folk song with breathy vocals,
     acoustic guitar, and lo-fi tape saturation. Weirdness around 45.
Mac: Got it all -- let me build your package.
```

### Switching Modes Mid-Session

Say "let's go Studio mode," "switch to Demo," or "let's jam" at any point. Mac acknowledges the switch and adjusts immediately.

If Mac notices you consistently prefer a different mode than your default, he'll offer to update it: "You've been vibing with Studio mode lately -- want me to make that your default?"

You can also change your default directly: "Make Studio my default mode." Mac updates memory immediately.

### Changing Preferences

You can update any preference by telling Mac during conversation. Changes take effect immediately and persist across sessions.

| Change | What to Say | What Mac Does |
|--------|------------|---------------|
| **Upgrade tier** | "I upgraded to Pro" | Updates memory, announces newly available features (including Voices, Custom Models, My Taste), offers to update band profiles |
| **Change default mode** | "Make Studio my default" | Updates memory immediately |
| **Add exclusions** | "I never want autotune" | Updates memory, notes if band profiles are affected |
| **Remove exclusions** | "Stop excluding piano" | Updates memory |
| **Any ongoing preference** | State it as a general preference, not a one-song request | Updates memory via write-through |

---

## 3. Creating Songs (the Main Workflow)

Creating a song is Mac's core capability (menu code: **CS**). Here is the full workflow, step by step.

### Step 1: Providing Song Direction

Mac needs at least one source of musical direction. You have several options:

**Genre and mood:**
```
You: Warm indie rock with a melancholy edge
```

**Reference tracks ("sounds like X meets Y"):**
```
You: Something that sounds like Dr. John meets Bon Iver
```

When you provide reference tracks, Mac decomposes each into concrete sonic descriptors (instrumentation, vocal style, production, energy, era) and shows you the breakdown before building the prompt. If Mac does not confidently know the artist, he will ask you to describe what you like about their sound rather than guessing.

**Band profile baseline:**
```
You: Use my Midnight Porch band profile
```

**Combination of all three:**
```
You: Use my Midnight Porch profile but make it darker -- sounds like Portishead meets trip-hop
```

### Step 2: Providing Source Text

If you have a poem, raw lyrics, or text to transform, paste it in. Mac will route it through the Lyric Transformer.

- **Demo mode:** Applies balanced defaults (Structure Tagging + Chorus Creation + Rhythmic Adjustment + Cliche Detection)
- **Studio mode:** Lets you choose which transformations to apply
- **Jam mode:** Pushes toward full rewrite, experimental

If you do not provide source text:
- **Demo/Jam mode:** Defaults to Suno's auto-lyrics
- **Studio mode:** Asks if you want to write lyrics or use auto-lyrics

### Instrumental-Only Songs

```
You: Make me an instrumental -- ambient electronic, something for studying
```

Mac skips the Lyric Transformer entirely, auto-populates exclusion defaults ("no vocals, no humming, no choirs, instrumental only"), and notes the Instrumental toggle for paid-tier users.

### Non-English Lyrics

```
You: I have a poem in French I want to turn into a song
```

Mac acknowledges the language, adds it as a style prompt element ("sung in French"), and warns that metatag reliability may vary with non-Latin scripts.

### Long Text Handling

If your source text exceeds roughly 400 words, Mac warns you before proceeding:

```
Mac: That's a lot of material -- a typical song has 200-400 words.
     Want me to: (1) condense it to fit one song, (2) split it into a multi-song suite,
     or (3) pick the strongest sections?
```

### The Output Package

Every song creation produces a complete, copy-paste-ready package. The wild card variant is included by default -- it takes your core song intent but twists one or two elements (a lean into an adjacent lane, era shift, mood inversion, a different instrument's job) while staying inside your band's core sound. It uses the same model and sliders as the primary; running the primary prompt unchanged on v6-wild is another quick way to get a wild card. You can use it, ignore it, or cherry-pick elements from it. The wild card is skipped if you explicitly request conservative mode.

Here is a full example:

```
## Your Suno Package

### Lyrics
[Mood: bittersweet]
[Vocal Style: intimate]

[Verse 1]
The porch light flickers on the empty street
Where summer left its footprints in the heat
I count the cracks along the garden wall
And wonder if you heard me when I called

[Chorus]
[Belted]
Come back to the house where the jasmine grows
Where the screen door swings and the evening slows
I left a light on, I left a chair
I left a song hanging in the air

[Verse 2]
[Instrument: acoustic guitar, upright bass]
The radio still hums your favorite tune
The moths are dancing underneath the moon
I saved the letters, pressed between the pages
Of a book that's older than our ages

[Chorus]
Come back to the house where the jasmine grows
Where the screen door swings and the evening slows
I left a light on, I left a chair
I left a song hanging in the air

[Bridge]
[Whispered]
Maybe the distance isn't miles --
Maybe it's just the space between two smiles

[Final Chorus]
[Energy: building]
[Belted]
Come back to the house where the jasmine grows
Where the screen door swings and the evening slows
I left a light on, I left a chair
I left a song hanging in the air

[Outro]
[Hummed]
[Fade Out]

### Style Prompt (v6-mini)
187/1,000 characters

Warm indie folk, bittersweet Americana, intimate lo-fi production, acoustic guitar
fingerpicking, soft brush drums, upright bass, breathy female vocal, porch-recording
warmth, tape saturation, evening atmosphere, nostalgic

### Exclude Styles
electric guitar, autotune, heavy drums, synths

### Settings
- Vocal Gender: Female
- Lyrics Mode: Manual
- Note: Weirdness, Style Influence, and Audio Influence sliders are available on Pro/Premier plans

### Song Title
Jasmine House

### Wild Card Variant -- The Unexpected Take
Warm 1960s coffeehouse folk ballad, one fingerpicked acoustic guitar and upright bass,
close-mic'd intimate vocal, tape warmth, brushed snare only on the last chorus

"What if we took this folk ballad back to a 1960s coffeehouse? Same song, same lane --
fewer instruments, a closer vocal, and tape warmth instead of a full band."
```

For a field-by-field mapping of where each component goes in Suno's UI, see [Suno Reference — Package Field Mapping](SUNO-REFERENCE.md#package-field-mapping).

### Tips for Using the Output in Suno

Mac walks you through this on your first song (and any time you ask). Work top to bottom in the package's order -- it matches Suno's Create screen:

1. Pick the **model** at the top right -- v6 (v6-mini on Free). For a quick wild card, run the same prompt on v6-wild; the package's own wild-card prompt runs on v6 with the same sliders.
2. Leave **"Describe your song"** empty -- the Lyrics and Styles fields carry everything.
3. Add your **Voice** or **Persona** (Pro/Premier), **Audio**, or **Inspo** from the chips if the package names one (Inspo availability on v6 unverified)
4. Paste **Lyrics** into the Lyrics field (Lyrics Mode Manual)
5. Paste the **Style Prompt** into **Styles**
6. In the **Controls panel**, top to bottom: **Exclude Styles** as a comma-separated list (Pro/Premier), then Vocal Gender, Duration, **Max Mode** (on for any take you might keep -- 2× credits; it's applied at generation and can't be added to a finished take), Weirdness, Style Influence, Audio Influence, **Variety at Exact style** (any higher notch rewrites your style prompt), and **Personalize** off
7. Add your **Song Title** and pick the **Save to** folder for the band
8. Hit **Create** and generate **3-5 versions** -- Suno interprets the same inputs differently each time. When you're comparing one change against another, about 4 takes per version reads more reliably than 2 (the spread between takes can be bigger than the change). That's a suggestion; how many you run is up to you
9. **Listen in the browser before downloading.** Downloads are capped, so download only the keeper (or a take Mac needs to measure). If a version is mostly right but one section is weak, try **section replacement** in the Song Editor rather than regenerating the whole song

**A note on tempo control:** BPM tags in lyrics (e.g., `[Verse: 65 BPM]`) have no detectable effect on Suno's output -- confirmed by librosa analysis across multiple songs. Perceived tempo is actually controlled through how lyrics are written: short fragmented lines feel slow, packed lines feel fast, and line breaks control where the singer breathes. For drum feel changes, use metatags like `[Heavy: halftime]` rather than BPM values. Mac handles this automatically when building your lyrics package.

**Spoken pieces:** Suno's separate Speech model (beta, 2026-10-01) makes spoken word over music from plain paragraphs. It's a possible route for a poem you want spoken rather than sung, but it's untested here, and Mac will say so.

---

## 4. Band Profiles

### What a Band Profile Is

A band profile is the sonic equivalent of a brand book. It captures the DNA of a musical project: genre, vocal character, production style, creative boundaries, language, and optionally the songwriter's authentic writing voice. Once created, it serves as a foundation that all skills draw from to maintain consistency across songs.

### Why You Would Want One

- Consistent sound across multiple songs (album/EP work)
- Skip re-explaining your preferences every time
- Store your "sounds like" references for reuse
- Capture slider values and exclusions that work for you
- Preserve your writing voice when Mac transforms lyrics

**A note on vocal consistency:** Band profiles maintain consistency in your *prompts* -- genre, style, exclusions, and vocal direction. However, Suno interprets the same style prompt differently on every generation. The only way to get a truly consistent vocal identity across songs is with the **Voice** feature (Pro/Premier plans on v5.5), which locks in a specific vocal character. Without a Voice, you are relying on descriptive prompt language, which gets you in the right neighborhood but not an exact match. If consistent vocal identity across an album or project matters to you, a Pro plan with Voices is strongly recommended.

**Personas and Voices:** Personas were **not** discontinued -- they were moved inside the Voices menu, which is why they can look gone. They still work. Voices is a separate, additional feature that serves the same goal by a different mechanism: a Persona captures the *style essence* of a source generation, while a Voice is actual voice cloning from an audio sample you provide. For a locked vocal identity on v5.5, a Voice is the stronger tool; a Persona is still useful when the thing you want to carry forward is a whole sonic character rather than a specific singer. Mac will suggest the move when it fits, and will not tell you Personas are gone.

### Creating Your First Profile

Through Mac's menu, select **MB** (Manage Bands), or say "I want to create a band profile."

Mac (via the Band Profile Manager skill) walks you through a conversational discovery:

1. **Band name** -- What is this project called?
2. **Instrumental or vocal?** -- Skips vocal direction if instrumental
3. **Genre and mood baseline** -- Open-ended: "What does this band sound like?"
4. **Reference tracks** -- "Name 2-3 artists or songs that capture the vibe." Mac decomposes them into concrete sonic descriptors and stores both.
5. **Language** -- What language will the lyrics be in?
6. **Model and tier** -- Which Suno model/plan do you use?
7. **Vocal direction** (if vocal) -- Gender, tone, delivery, energy, diction. Specific is better: "warm, breathy female vocal with indie folk phrasing" not just "female vocals."
8. **Style prompt baseline** -- Built from your answers. Mac shows a draft and iterates with you.
9. **Exclusion defaults** -- What should never appear? Max 5 recommended.
10. **Creative settings** -- Conservative/balanced/experimental. Slider preferences if on a paid tier.
11. **Voice / Persona reference** -- Do you have an existing Suno Voice or Persona to link? Do you have a Custom Model?
12. **Writer voice** -- Optional. Analyze your writing style now or skip for later.

Between sections, Mac asks "Anything else to add, or move on?" -- he does not auto-advance.

After discovery, Mac:
- Assembles the profile YAML
- Validates the structure
- Generates a **Band Identity Card** (3-4 sentence natural language summary)
- Presents both for review
- Saves to `docs/band-profiles/{profile-name}.yaml` on approval

### Writer Voice Analysis

If you choose to analyze your writing voice, provide 3 or more writing samples (poems, lyrics, prose -- 10 lines or more each). The more samples you provide, the more accurate the analysis. Pick pieces that feel most like you.

You can paste samples directly into the conversation, or point Mac to files on disk -- a text file, a PDF, a folder of poems. Mac will read and analyze them.

Mac extracts patterns across:
- **Vocabulary preferences** -- formal/casual, abstract/concrete
- **Sentence rhythm** -- short punchy vs. long flowing, fragment use
- **Imagery tendencies** -- nature, urban, body, celestial, domestic
- **Emotional tone** -- raw/restrained, hopeful/melancholic
- **Metaphor style** -- extended vs. quick, conventional vs. surprising
- **Repetition patterns** -- anaphora, refrains, echo structures

Mac shows the analysis with example quotes from your samples, so you can confirm or correct. This gets stored as the `writer_voice` section of your band profile and constrains lyric generation to match your authentic voice.

### Loading and Switching Profiles

```
You: Load my Midnight Porch profile
You: Switch to my Neon Drift profile
You: Use Midnight Porch for this song
```

If Mac has a profile loaded from a previous session, he will offer continuity: "Your band profile Midnight Porch is still loaded -- keeping that?"

### Editing Profiles

```
You: Edit my Midnight Porch profile -- make it more aggressive
You: Update Neon Drift to use v6-wild
You: Add "no synth pads" to my exclusions
```

Mac loads the profile, applies your changes, re-validates, shows a structured diff of changes, and saves on confirmation. If genre or mood change, Mac suggests updating the style prompt baseline to match.

**Tier drift detection:** When loading a profile, Mac compares the profile's stored tier against your current tier. If they differ, he offers to unlock new features.

### Duplicating Profiles

```
You: Duplicate Midnight Porch as Midnight Porch v2
You: Fork Neon Drift for an acoustic experiment
```

Creates a copy as a starting point for a new version, side project, or sound evolution experiment.

### Health Check

```
You: Is my Midnight Porch profile good?
You: Check my profile
```

Mac assesses completeness and quality beyond structural validation:
- Is the style baseline specific enough?
- Is writer voice populated?
- Are reference tracks present?
- Are exclusion defaults thoughtful?
- Is vocal direction detailed?
- Any successful generation snapshots saved?

Presented as friendly recommendations, not failures: "Your profile is valid and usable. Here is how to make it even better..."

---

## 5. Refining Songs (bring back a take)

Refine Song (menu code: **RS**) is where songs get great, and it's the one place to bring a take back. Try the package on Suno, listen, then tell Mac what you hear. He works in two parts:

1. **Diagnose.** Mac runs the Feedback Elicitor behind the scenes to work out what's actually off -- even when all you can say is "it doesn't feel right."
2. **Rebuild only what changed.** The style prompt, the lyrics, or both go back through the same skills that built the package, and Mac shows you just the changed parts under a "What Changed" list. A settings-only change comes back as a short note.

Saying "feedback loop" or "FL" to Mac lands here too. (The Feedback Elicitor still runs on its own as a standalone skill -- see [Direct Skill Access](#6-direct-skill-access) -- but on its own it diagnoses without rebuilding the package.)

### How to Start a Refinement

**If you are in the same session as create-song:**
```
You: The vocals sound too polished -- I wanted something rawer
```
Mac handles a slider tweak or a word swap on the spot. Anything that changes the style prompt, the exclusions, or the lyrics' tags and structure goes back through the matching skill, and deeper feedback goes through the full diagnose-and-rebuild.

**If you are starting fresh:**
Select **RS** from the menu or say "I want to refine a song." Mac looks the song up in your songbook first and asks only what he can't find. You don't need to download the take to refine it -- only when a measurement would settle the question, and Mac will say it costs a download.

**What plays isn't always what was asked for.** The style text on a Suno song page shows what you typed (or Suno's rewrite of it), not what actually landed. Mac goes by the audio and your ear. If a take is nearly right but its ending, final chorus or vocal level lets it down, Mac can suggest repairs to try before a full re-roll: Extend from before the last section, Fade Out, and a few others.

### The Five Feedback Types

Mac (via the Feedback Elicitor) triages your feedback into one of five categories, each handled differently:

| Type | Your Signal | Example | Mac's Approach |
|------|------------|---------|----------------|
| **Clear** | Specific, actionable | "The guitar is too loud" | Direct mapping to parameter changes |
| **Positive** | You like it, want to evolve | "This is great! Can we try a darker version?" | Identify what to keep vs. evolve |
| **Vague** | Something is off but you cannot say what | "It just doesn't feel right" | Guided elicitation (see below) |
| **Contradictory** | Conflicting desires | "More energetic but also more chill" | First Principles reset |
| **Technical** | Audio quality issues | "There's a weird glitch" | Regeneration or Studio feature recommendations |

Mixed feedback is handled component by component -- clear and technical parts first, since resolving concrete issues often clarifies vague ones.

### How Mac Handles Vague Feedback

This is the feedback loop's core differentiator. When you know something is off but cannot articulate what, Mac uses a three-phase elicitation sequence:

**Phase 1: Binary Narrowing**
Reduces the problem space through yes/no questions across dimensions: music/production, vocals, energy, structure, lyrics, vibe. One question at a time.

```
Mac: Let's narrow this down. Is the issue more with the music/production,
     or with the vocals/lyrics?
You: The music, I think.
Mac: Okay -- is the instrumentation wrong, or is it more the energy/mood of the track?
You: The energy feels off.
```

**Phase 2: Comparative Anchoring**
Uses reference points to calibrate. Does not require musical knowledge.

```
Mac: On a scale of 1-10, where 1 is a quiet coffee shop and 10 is a packed arena,
     where does the current track land? And where do you want it?
You: It's at like a 7, and I want it at a 4.
```

**Phase 3: Emotional Vocabulary Bridge**
Presents opposing pairs so you can place the current output and your target on the spectrum:

```
Mac: Think of the production as a spectrum:
     Polished ←————→ Raw
     Where's the current track, and where do you want it?
You: It's way too polished -- I want it about 70% toward raw.
```

**Escape hatch:** If narrowing does not converge after 3-4 questions, Mac pivots: "Instead of narrowing down -- can you name a song or artist that sounds like what you wanted? I'll work backwards from there."

**Non-convergence fallback:** If elicitation still does not converge, Mac suggests generating 2-3 variants with different parameter profiles and letting you compare. This turns an elicitation problem into a selection problem.

### What the Diagnosis Looks Like

After elicitation, the diagnosis comes back as structured recommendations, and Mac tells you what it found before rebuilding. In the Feedback Elicitor's standalone form it looks like this:

```
## Feedback Summary
You want rawer, less polished vocals with more intimate production -- closer to
a demo recording than a studio mix.

## Before/After Preview
Current sound: A polished indie folk track with clean, studio-mixed vocals and
full production.
Target sound: A raw, intimate porch recording with rough-edged vocals, minimal
processing, and room ambience.

## Style Prompt Adjustments
Current: "Warm indie folk, intimate lo-fi production..."
Recommended: "Raw indie folk, demo recording quality, rough-edged vocals..."
Changes:
- Replaced "intimate lo-fi" with "demo recording quality" for rawer production
- Added "room ambience, single-mic feel" for less polish
Confidence: High -- direct from your feedback

## Exclusion Prompt Adjustments
Recommended: "no heavy reverb, no studio polish, no auto-tune"

## Strategy Note
Generate 3-5 versions with the adjusted prompt -- Suno's randomness means one
may nail it without further changes.
```

### Profile Update Suggestions

If Mac notices a systematic preference (not just a one-song tweak), he suggests updating your band profile:

```
Mac: You've mentioned wanting rawer vocals twice now -- want me to update your
     band profile's vocal direction so future songs start from there?
```

### The Iteration Loop

You can keep refining. Each time you return with a take, Mac diagnoses it fresh and rebuilds what changed. Adjustments compound, and the song converges on your vision.

```
Round 1: "Too polished" → Raw up the production
Round 2: "Better, but the chorus needs more impact" → Adjust chorus energy
Round 3: "That's it." → Save successful elements to profile
```

---

## 6. Direct Skill Access

Mac orchestrates five specialized skills. You can use them directly through Mac's menu or invoke them independently.

**Claude Code (slash commands):**
- `/suno-setup` -- Install or reconfigure the module
- `/suno-agent-band-manager` -- Talk to Mac (the orchestrating agent)
- `/suno-band-profile-manager` -- Manage band profiles directly
- `/suno-style-prompt-builder` -- Build style prompts directly
- `/suno-lyric-transformer` -- Transform lyrics directly
- `/suno-feedback-elicitor` -- Diagnose a take directly (adjustment recommendations, no rebuild)

**Other LLM CLIs:** Skills in `.agents/skills/` are auto-discovered. Use your tool's native skill activation (e.g., `@skill-name` in Windsurf, `$skill-name` in Codex, or by description match in Gemini CLI).

### When to Use Skills Directly vs. Through Mac

| Use Mac When... | Use Skills Directly When... |
|-----------------|---------------------------|
| You want the full guided experience | You know exactly what you need |
| You want mode selection (Demo/Studio/Jam) | You want to skip the conversation |
| You want a complete package (lyrics + style + params) | You only need one piece (just a style prompt, just lyrics) |
| You are iterating and want Mac to track context | You are scripting/automating |

### Skill Quick Reference

| Menu Code | Skill | Standalone Use Case |
|-----------|-------|-------------------|
| **SP** | Style Prompt Builder (the suno-style-prompt-builder skill) | You already have lyrics and just need the sound description |
| **TL** | Lyric Transformer (the suno-lyric-transformer skill) | You have text to convert and don't need a style prompt |
| **FL** | Feedback Elicitor (the suno-feedback-elicitor skill) | You want a take diagnosed into adjustment recommendations without the rebuild (through Mac, use RS) |
| **AA** | Feedback Elicitor (the suno-feedback-elicitor skill) | You want a render's tempo, key, loudness (and a section map with the PyTorch tools on) measured |
| **MB** | Band Profile Manager (the suno-band-profile-manager skill) | You want to create, edit, list, duplicate, or delete profiles directly |
| **WV** | Band Profile Manager (the suno-band-profile-manager skill) | You want to analyze writer voice patterns from writing samples |
| **HC** | Band Profile Manager (the suno-band-profile-manager skill) | You want to assess a profile's completeness and quality |
| **AL** | Lyric Transformer (the suno-lyric-transformer skill) | You want to analyze text for song structure potential without transforming it |

### Lyric Transformer Options

| Code | Transformation | What It Does |
|------|---------------|--------------|
| ST | Structure Tagging | Adds section metatags (`[Verse]`, `[Chorus]`, etc.) |
| CE | Chorus Extraction | Finds existing hook material and promotes to chorus |
| CC | Chorus Creation | Writes a new chorus from the poem's emotional core |
| RA | Rhythmic Adjustment | Normalizes syllable counts for vocal phrasing |
| RE | Rhyme Enhancement | Strengthens rhyme patterns |
| FR | Full Rewrite | Complete rewrite as song lyrics (preserves theme) |
| CD | Cliche Detection | Flags overused phrases and suggests alternatives |
| WF | Word Fidelity Mode | Uses your exact words, only adds structure |

Note: FR and WF are mutually exclusive.

### Audio Analysis with External Tools

For detailed audio analysis of Suno output, three complementary tools are available:
- **librosa scripts** (included in the Feedback Elicitor) — programmatic BPM, key detection, loudness (LUFS / loudness range), tempo stability, and energy arc analysis. Optional PyTorch tools add a second opinion on tempo (`beat-grid.py`, Beat This!), vocal placement against the band (`vocal-placement.py`, Demucs), and a section map that lines a render up with its lyrics (`section-map.py`, Demucs + Whisper) to show when each tagged section lands and how it sounds. Turn on **PyTorch audio tools** in `/suno-setup` and the other scripts take their tempo from Beat This! instead of librosa. Run `analyze-audio.py` on a directory of MP3s for batch analysis, or `audio-deep-analysis.py` on individual tracks for deep dives. Requires Python 3 with librosa and numpy.
- **Gemini 3.1 Pro** — upload MP3 to Google AI Studio for AI-powered instrument identification, genre classification, and style prompt accuracy feedback. A two-pass workflow is mandatory for fusion genres.
- **ChatGPT** — upload MP3 for "blind" analysis (without the style prompt) to get unbiased genre and instrument identification. Useful for catching cases where the style prompt intent diverges from what Suno actually produced.

See the Feedback Elicitor's audio-analysis-workflow reference for detailed setup and prompting guidance.

### Improving Your Suno Prompting with A/B Testing

For users who want to systematically improve their style prompts, Gemini audio analysis enables a powerful A/B testing workflow:

1. Generate 2-3 versions of a song on Suno
2. Run each through Gemini blind (no style prompt provided) at 0.5 temp
3. Compare what Gemini hears to what you prompted
4. Change ONE variable (word position, tag, slider value), regenerate, and analyze again
5. Document what moved and what didn't

This replaces gut-feel prompt tweaking with systematic iteration. Mac can suggest this as an optional step after presenting a Suno package — just ask "can we A/B test this prompt?"

### Playlist Sequencing

Mac routes playlist/album ordering to the dedicated `suno-playlist-sequencer` skill, which combines data and creative judgment:

- **librosa scripts** — `playlist-sequencing-data.py` generates BPM, key (with Camelot wheel codes), energy levels, loudness, and per-seam readings between adjacent tracks: the key move (`key_compat`: compatible / near / distant, which rates the key relationship only), the BPM change, and the loudness step. Each is read separately; none is the seam's verdict; `batch-full-analysis.py` adds catalog-wide energy/section/spectral analysis. (`chord-progression.py`, for key centers over time within individual tracks, stays in the Feedback Elicitor.)
- **Camelot wheel harmonic mixing** — key-relationship readings based on DJ harmonic mixing principles (+/-1 number = a compatible key move, relative major/minor = mood shift, beyond +2 = a distant key move, for intentional contrast). They rate the key relationship only; tempo, loudness and energy are separate
- **Narrative sequencing** — the skill considers thematic arcs, emotional progression, and lyrical connections between songs alongside the sonic data

Tell Mac "help me order my playlist" or "sequence these songs for an album" and provide the audio files or sequencing data. Mac hands the work to `suno-playlist-sequencer`, which balances sonic flow (BPM transitions, key compatibility, timbral variety) with narrative progression (thematic arc, emotional journey) to suggest an ordering.

See the suno-playlist-sequencer skill's `references/playlist-sequencing-methodology.md` for the full sequencing methodology (its Transition Discipline section covers key and tempo moves at the seam), and the suno-feedback-elicitor skill's `references/audio-analysis-scripts.md` → "Reading librosa numbers" for felt BPM versus measured BPM.

---

## 7. Songbook & Memory

### Browse Songbook (menu code: SB)

The songbook is your creative portfolio -- past songs, successful prompts, iteration history, and creative evolution.

Mac reads the songbook through a catalog script (every song's band, title, status, dates, model, settings, and style prompt), plus the Feedback Elicitor's iteration logs in `docs/feedback-history/` and his session timeline.

Songbook entries should include a **Listening Notes** section — 2-3 lines capturing what the generation actually sounds like (how the intro opens, overall feel, standout sonic moments). Style prompts describe intent; listening notes describe reality. These diverge frequently and are critical for playlist ordering.

Songs are grouped by band profile (or "Unaffiliated" for one-offs). For each song, you can:
- **View details** -- Full lyrics, style prompt, parameters, iteration history
- **Reuse** -- Use a style prompt as a starting point for a new song
- **Compare** -- Side-by-side comparison of two songs
- **Export** -- All data in a copy-ready format

If your songbook is empty, Mac lets you know and offers to start your first song.

### How Mac Remembers Your Preferences

Mac stores learned preferences in `patterns.md` within the sidecar memory. Over time, this captures:
- Genre tendencies
- Vocal preferences
- Exclusions you consistently use
- Slider values that produce results you like
- Feedback patterns (e.g., you always want rawer vocals)

### How Session Memory Works

During a session, Mac tracks:
- Which band profile is loaded
- What songs you have created or refined
- Your interaction mode
- Creative context you have shared

The `MEMORY.md` file stores active work and essential context between sessions (the raw day-by-day detail lives in `sessions/`).

### Saving and Resuming Sessions

At the end of a song creation, Mac asks: "Good session. Want me to remember your preferences for next time?" If yes, he saves session context via the save-memory capability (menu code: **SM**).

When you return, Mac checks memory for active sessions or recent work and offers continuity:
- "Your band profile Midnight Porch is still loaded -- keeping that?"
- "Last time we were working on 'Jasmine House.' Want to continue, or start something new?"

---

## 8. Headless/Automation

> **This section is for scripting and batch workflows.** If you use Mac interactively, skip to [Troubleshooting](#9-troubleshooting).

All skills support headless (non-interactive) operation for scripting, batch processing, and automation.

### Headless Create-Song

**Input contract (JSON):**

```json
{
  "genre_mood": "required -- genre, mood, vibe description",
  "source_text": "optional -- poem or text to transform",
  "lyrics": "optional -- finished lyrics to use as-is (with lyrics_ready: true)",
  "lyrics_ready": "optional -- true skips the Lyric Transformer",
  "band_profile": "optional -- profile name to load",
  "tier": "optional -- free|pro|premier (else Mac's memory)",
  "model": "optional -- default v6 on Pro/Premier, v6-mini on Free (also: v6-wild)",
  "exclusions": "optional -- list (else Mac's default exclusions + the profile's)",
  "voice": "optional", "persona": "optional", "custom_model": "optional",
  "creativity_mode": "optional -- conservative|balanced|experimental, default balanced",
  "instrumental": "optional -- true for instrumental-only",
  "language": "optional -- default English",
  "include_wild_card": "optional -- default true",
  "save_to_songbook": "optional -- default false"
}
```

**Output:** the standard result envelope (`status`, `capability`, `artifact_path`, `summary`, `warnings`) plus a `package` object in Suno's Create-screen order: `voice`, `lyrics`, `style_prompt`, `char_count`, `exclude_styles`, `settings` (`model`, `vocal_gender`, `duration`, `max_mode`, `weirdness`, `style_influence`, `audio_influence`, `variety`, `personalize`), `title`, `save_to`, `wild_card`. Anything the input leaves out (tier, exclusions) comes from Mac's memory; if the tier can't be resolved, the package is built for Free with a warning. `artifact_path` is null unless `save_to_songbook` is true. Headless Refine Song takes `feedback` plus the song (`song_ref`, or the original prompt and lyrics) and returns only what changed, with the same envelope.

### Headless Modes for Each Skill

**Style Prompt Builder** (contract: the skill's `references/headless-contract.md`):
- `--headless` -- build a package. A named band profile supplies the baseline and other inputs override it; without a profile, `genre_mood` is required. The wild card is on by default (`include_wild_card: true`). The older `--headless:from-profile`, `--headless:custom`, and "`--headless` with a profile name" forms are aliases of this one mode
- `--headless:refine` -- accept an existing prompt + the Feedback Elicitor's adjustment recommendations
- `--headless:migrate` -- reformat a prompt from one model to another

**Lyric Transformer:**
- `--headless` with text -- analyze + transform with balanced defaults (`--headless:transform` is an alias); the writer's spacing comes back verbatim
- `--headless:analyze` -- analyze input only, return analysis JSON
- `--headless:refine` -- accept adjustment spec, apply targeted changes

**Feedback Elicitor:**
- `--headless` -- triage + return full adjustment recommendations (`--headless:adjustments` is an alias)
- `--headless:analyze` -- triage and categorize feedback only

**Band Profile Manager:**
- `--headless` -- list all profiles as JSON array
- `--headless:create` -- create profile from provided YAML
- `--headless:validate` -- validate an existing profile
- `--headless:load <name>` -- read and return profile as JSON
- `--headless:edit <name>` -- accept YAML field overrides, apply and save
- `--headless:delete <name>` -- delete without confirmation
- `--headless:duplicate <source> <new_name>` -- copy profile

### Headless Error Contract

When required inputs are missing, a headless call returns `status: "blocked"` with a one-line reason (and, where the skill has one, the missing fields and its decisions so far). The Style Prompt Builder's shape:

```json
{"status": "blocked", "missing": ["genre_mood"], "reason": "No band profile and no genre_mood given.", "decisions": []}
```

### Batch Processing Concept

Headless modes enable batch workflows. Example: generate style prompts for multiple genre/mood combinations using a script that calls the Style Prompt Builder with `--headless` and a `genre_mood` for each entry, collecting the results.

---

## 9. Troubleshooting

### Common Issues and Solutions

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| Mac does not recognize my band profile | Profile name mismatch or missing file | Say "list profiles" to see available names. Profiles live in `docs/band-profiles/` as YAML files. |
| Style prompt is too long | Exceeded 1,000 characters (the v6 family's limit) | Mac warns about this. Ask him to trim it. Front-load essentials in the first ~200 characters (critical zone — strongest influence). Content beyond 200 is supplementary, not wasted. |
| Lyrics exceed Suno's limit | Over 5,000 characters (hard limit) or over 3,000 (quality degrades) | Ask Mac to condense. The Lyric Transformer tracks character budgets — warns at 3,000 (quality), errors at 5,000 (hard limit). |
| Mac asks too many questions | You are in Studio mode | Say "let's switch to Demo mode" for a faster experience. |
| Mac does not ask enough questions | You are in Demo mode | Say "let's go Studio mode" for the full songwriter's workshop. |
| Mac forgot my preferences | It wasn't written to memory | Mac saves preferences as he learns them. If one slipped, tell him again; SM (Save Memory) runs a full consolidating save any time. |
| Profile says wrong tier | Your Suno plan changed | Tell Mac "I upgraded to Pro" -- he updates memory and offers to update your profiles. Mac also detects tier drift when loading profiles. |
| Profile references Personas but I'm on v6 | Personas moved inside the Voices menu -- they were relocated, not removed, and still work | Nothing is broken. Tell Mac your model version if you want him to suggest a Voice instead; a Voice locks vocal identity more tightly than a Persona does. |
| Mutually exclusive transformation error | Selected FR + WF or other conflicts | Full Rewrite and Word Fidelity cannot be used together. Chorus Extraction is skipped if Full Rewrite is selected. |

### What to Do When Skills Are Unavailable

If an external skill fails to load, Mac tells you which one. Without the Style Prompt Builder or the Lyric Transformer he won't hand you a Suno package -- those skills carry the checks (artist names, character budgets, section tags) that keep a package from failing in Suno -- but he can keep shaping the direction and drafting with you until it's back:

```
Mac: I can't reach my style prompt specialist right now, so no package yet --
     but let's keep working the direction and the lyrics, and I'll build the
     moment it's back.
```

He never silently fails or fabricates skill output.

### Suno-Specific Issues

For detailed troubleshooting of Suno platform issues (prompt formatting, audio quality, vocal artifacts, instrument bleed, metatag behavior), see the [Suno Reference — Troubleshooting](SUNO-REFERENCE.md#troubleshooting-suno-issues).

### Getting Unstuck

If you are not sure what to do:
- Say "help" or describe what you are trying to accomplish -- Mac redirects gracefully
- If Mac seems confused about your intent, try stating it differently: "I want to make a new song" vs. "I want to refine an existing one"
- Check the menu -- select a capability by its code (CS, RS, SB, SM, MB, SP, TL, ...)
- For Suno-specific questions Mac cannot answer, consult [Suno's help center](https://help.suno.com)

---

## Quick Reference: Menu Codes

| Code | Capability | Skill | Description |
|------|-----------|-------|-------------|
| **SU** | Setup Module | Setup | Install or reconfigure the Suno module |
| **CS** | Create Song | Band Manager (Mac) | Full song creation workflow |
| **RS** | Refine Song | Band Manager (Mac) | Bring back a take: diagnose it and rebuild the changed parts ("FL" / "feedback loop" also land here) |
| **SB** | Browse Songbook | Band Manager (Mac) | Browse past songs and creative history |
| **SM** | Save Memory | Band Manager (Mac) | Save session context |
| **MB** | Manage Bands | Profile Manager | Band profile CRUD |
| **WV** | Analyze Writer Voice | Profile Manager | Extract writing voice patterns from samples |
| **HC** | Profile Health Check | Profile Manager | Assess profile completeness and quality |
| **MP** | Manage Playlist | Profile Manager | Scaffold or edit a band's canonical playlist YAML |
| **SP** | Build Style Prompt | Style Prompt Builder | Model-aware style prompt generation |
| **TL** | Transform Lyrics | Lyric Transformer | Poem/text to Suno-ready lyrics |
| **AL** | Analyze Lyrics | Lyric Transformer | Analyze text for song structure potential |
| **FL** | Feedback Loop | Feedback Elicitor | Standalone diagnosis only (not on Mac's menu -- through Mac, use RS) |
| **AA** | Analyze Audio | Feedback Elicitor | Measure a render's tempo, key, loudness (and section map with the PyTorch tools on) |
| **PS** | Sequence Playlist | Playlist Sequencer | Album-craft track ordering with per-move rationale |
