# Suno Metatag Reference

Metatags are keywords in square brackets placed in the Lyrics field to guide Suno's generation. This catalog covers the tags known to work as of August 2026 plus the v6 findings below. Suno publishes no tag specification for v6, so when a tag's effect is in doubt, check current sources.

## How to Load This File

This file is too large to read whole on every run. Load only the sections the job needs: pass each name below to `uv run {skill-root}/scripts/metatag-sections.py --section "<name>"` (repeat `--section` for several). A name is a heading or the start of one; a section comes with its subsections.

Grades used throughout: HIGH (several sources agree), MEDIUM or Experimental (one or two sources, inconsistent), unmarked (established). LOCAL-CONFIRMED and LOCAL-OBSERVED are this module's own production tests; COMMUNITY, VENDOR and ANECDOTAL name the outside source class.

| When | Load |
|------|------|
| Any transform for a v6-family model | Suno v6 |
| Structure Tagging (ST), Chorus Extraction/Creation (CE/CC) | Section Structure Tags · Parameterized Section Tags · Dynamic & Transition Tags · Placement Rules · Formatting Rules |
| Adding descriptor tags (`[Mood:]`, `[Energy:]`, `[Vocal Style:]`), dual vocalists or duets | Descriptor Metatags |
| Rhythmic Adjustment (RA) | Punctuation Effects · Capitalization Effects · Repeated Vocables · Line Density as Tempo Control · Inline Performance Modifiers |
| Backing vocals, parentheses, group or call-and-response vocals | Parentheses · Establishing Non-Default Vocal Arrangements |
| Held notes, pronunciation, stretched or spelled-out words | Stretched Words · Vowel Stretching · Pronunciation · Spaced-Out Letters as Vocal Effect |
| Screams or heavy lanes next to clean sections | Scream Bleed-Through Prevention · [Chorus] Peak-Default in Heavy Lanes |
| Specific vocal delivery requested (whisper, belt, rap, vocal effects) | Vocal Delivery Tags |
| Instrumental sections, solos, instrumental tracks | Instrumental & Solo Section Tags · Ghost Vocals on Instrumental Tracks · Open-Ended Instrumental Sections · Example with Instrumental Sections |
| Instrument control per section | Per-Section Instrument Control · Standalone Instrument Tags |
| Sound effects | Sound Effect Tags |
| Tempo or feel cues | Timing & Rhythm Tags · Half-Time / Double-Time Drum Feel · Structural Timing in Lyrics |
| Considering an unusual or invented tag | Experimental Section Tags · Tags Confirmed Not Working |
| Checking where a finding came from | Sources |

## Suno v6

Findings since the 2026-09-09 launch, graded as elsewhere; ANECDOTAL-controlled marks a single tester who changed one variable at a time and published the negatives. They are guidelines: a song sometimes needs more than one way of asking.

- **Section cues are read at render time.** A short cue in the section tag (`[Verse 1 - riff continues under vocal, drums drive]`, or the pipe form `[Verse | whispered]`) is reported honored (VENDOR). Mirror the style field's section map word for word and name the scene: `[Bridge - closing time, the harbor wakes up: fast driving double-time build]`. Matching words reinforce; a contradiction ("quiet verse" in one field, "riff continues" in the other) resolves as the band thinning out (VENDOR).
- **Keep cues musical.** A chorus cue that echoed its own hook appeared to leak into the sung line (LOCAL-OBSERVED, n=2). Use instrument, energy, arrangement and mood words; add a scene name only when its words aren't in the lyric.
- **Lyric-field cues can override the style field** (ANECDOTAL, all three v6 models), consistent with the long-standing observation that lyrics dominate the output.
- **`[Silence]` at the end of a line that rushes** steadies rushed, flat, melody-less delivery (ANECDOTAL-controlled). Put it on the lines that rush, not every line, where the phrasing turns mechanical (VENDOR). It switches a pause on; it doesn't set its length. Stop markers don't stack: punctuation before `[Silence]` sped the line up, so skip `[Silence][Break]` combinations.
- **Mid-line commas make the singer stop** (ANECDOTAL-controlled). A reported stutter from end-of-line commas never showed up in production testing (2026-09-15, many v6 takes with line-ending commas), so leave the writer's line-end commas alone.
- **Invented tags are dropped, not interpreted:** `[2 Bar Rest]` did nothing; `[Silence]` works because the model already knows the token (ANECDOTAL-controlled). CAPS still mean harder delivery (ANECDOTAL-controlled).
- **Write held notes on the page.** A stretched vowel (`sta-a-ay`) was the one change that produced a sustained note for one tester (VENDOR, citing a user). Budget about 6-8 syllables for a ballad verse line and end chorus lines on open vowels.
- **State the edges.** An unspecified intro comes back as humming or a spoken line; an unspecified ending vamps or cuts off mid-lyric (VENDOR + COMMUNITY). Intro: `[Intro - guitar riff, 4 bars, instrumental only]`; the ending template is under Ending Control.
- **The words themselves steer delivery:** a pre-chorus opening on "tick tick" kept coming back whispered until the words changed (ANECDOTAL).
- **A mood word can read as intensity.** A final verse tagged "unresolved tension", meant to stay bare, came out as the song's loudest section (LOCAL-OBSERVED, n=1). Where a section must stay bare, try describing its harmony and arrangement (`[Final Verse - voice and one guitar, ends off the home chord]`) instead of its emotion.
- **Duets:** male/female line assignment is followed far better than before (COMMUNITY). Name the singers in the style field (Singer A / Singer B), tag every section with the name, and keep traded lines short. A vocalist tag can open the sung line itself (`[male vocals] I was there before the morning`); one heavy-metal duet guide (ANECDOTAL, dozens of duets) reports the split followed with high probability, less often with Vocal Gender set, and that text after a mid-line `!` or `?` tends to switch singer, so keep those marks out of a line one singer should finish.
- **Chatty lines drift into speech** more often on v6 (ANECDOTAL ×2): on a sung song with conversational lines, put `sung` in the vocal-style tag.
- **With a Voice, drop harmonized or dual vocal-style tags:** v6 doubles on its own (LOCAL-OBSERVED). For a clean lead use `[Vocal Style: clean]`, `clean, sung` in dense or fast sections (it counters spoken or rap drift) and `soft, sung` in quiet ones. Grit words in vocal tags roughen a Voice sample.
- **BPM and meter tags didn't move the tempo** in the one v6 render tested (LOCAL-OBSERVED, n=1, confounded). Put the feel in the cue (half-time, double-time, sparse, dense); a BPM figure that mirrors the style field word for word (`..., 150 BPM feel]`) is soft reinforcement worth testing (COMMUNITY).
- **Not yet re-tested on v6:** the `[Refrain]` fix for quiet repeats in heavy lanes, and the ending toolkit.

## Section Structure Tags

Core tags that define song structure. Suno uses these to organize musical sections.

**Use recognized tags only.** Suno doesn't know invented tags like `[The Questions]` or `[Reflection]`: at best it ignores them, at worst it sings the tag text as a lyric. Map each section to a recognized tag and shape its feel with parameterized syntax or descriptor tags.

**Intensity words aren't section tags.** `[Heavy]`, `[Loud]`, `[Soft]` or `[Quiet]` as a section header breaks Suno's structural parse: in production testing `[Heavy]` as a header made Suno skip the `[Intro]` and start on that section, on more than a few gens. Carry the intensity on a recognized section instead (`[Verse]` + `[Energy: dense, engulfing, peak]` + `[Vocal Style: full power]`), or use `[Bridge]` when the section must be harmonically new. When `validate-lyrics.py` flags a section tag as unrecognized, map it to a recognized one, even if an old songbook entry used it.

**Fill a section tag with direction, not a narrative label.** Suno can act on tempo, dynamics, vocal style, mood and energy inside the brackets; it has no signal for a human-readable label, which at best is ignored, at worst gets sung, and either way burns character budget.

| Format | Effect |
|--------|--------|
| `[VERSE 1 — THE ROOM]` | Suno can't act on "— THE ROOM"; it may sing it |
| `[Verse 1: hushed, tense]` | Arrangement and delivery cues Suno interprets |
| `[Breakdown — THE TURN]` | Narrative label, no generation signal |
| `[Breakdown: stripped, declarative]` | Functional direction Suno can act on |

When a source (a songbook entry, or another band's version) carries em-dashed labels, translate each into direction that keeps its intent ("— THE TURN" becomes `[Breakdown: stripped, declarative]`) and keep the label in songbook notes, outside the paste-ready lyrics.

| Tag | Usage | Notes |
|-----|-------|-------|
| `[Intro]` | Instrumental or minimal vocal opening | Notoriously unreliable — keep short or omit |
| `[Verse]` / `[Verse 1]` / `[Verse 2]` | Narrative/story sections | Number if multiple |
| `[Pre-Chorus]` | Transitional build before chorus | Short — 2-4 lines, creates tension/lift toward chorus |
| `[Chorus]` | Main hook/payoff section | Short repeated hooks > long novel choruses |
| `[Post-Chorus]` | Section immediately after chorus | Extends chorus energy or provides cooldown. Genre-dependent: very effective in pop/EDM, may blend with chorus in rock/metal |
| `[Bridge]` | Contrasting section — new harmonic content | Introduces NEW chords, melody, perspective. A bridge gives you something the song hasn't heard yet. Usually appears once |
| `[Outro]` | Closing section | Fade, resolution, or final statement |
| `[End]` | Hard stop | Use to signal a definitive ending |
| `[Final Chorus]` | Last chorus iteration | Often bigger/louder than standard chorus |
| `[Hook]` | Short catchy phrase | Distinct from chorus — can be a repeated motif |
| `[Refrain]` | Repeated line or phrase | Simpler than a full chorus. **In heavy genres this is the tag for a quiet repeating section** — see "[Chorus] Peak-Default in Heavy Lanes" below (LOCAL-CONFIRMED). External sources document `[Refrain]` only as a genre-tied structural tag (blues, folk, hymns) |
| `[Instrumental Intro]` | Instrumental-only opening | More reliable than bare `[Intro]` for ensuring no vocals (HIGH) |
| `[Instrumental Break]` | Explicit instrumental mid-song break | Clearer intent than `[Break]` alone (HIGH) |
| `[Drum Break]` | Percussion-only break section | Strips everything except drums (HIGH) |
| `[Percussion Break]` | Percussion-focused break | Similar to Drum Break but may include auxiliary percussion (HIGH) |
| `[Build]` | Rising energy section | Shorthand for `[Build-Up]`; confirmed on v5 (HIGH) |
| `[Big Finish]` | Grand climactic ending section | Signals a big, climactic ending (HIGH) |
| `[Chorus x2]` | Repeat chorus twice | Chorus doubling without rewriting lyrics (HIGH) |

### [Bridge] vs [Breakdown] — Functional Distinction

These serve fundamentally different purposes:

- **[Bridge]** = **something new.** New chords, new melody, potentially a different key. It repositions the song's narrative and emotional angle. Maintains or shifts energy without necessarily stripping instrumentation. Use for narrative/emotional turns, contrasting perspectives, moments where the song needs to go somewhere it hasn't been.

- **[Breakdown]** = **something less.** Subtractive arrangement — specifically strips instruments (typically drums and/or bass) while spotlighting vocals or a single motif. Use when you want the song to thin out, expose the vocal, create breathing room. In metal/metalcore context, forces a tempo drop and heavy rhythm (genre-aware behavior). Effective for creating maximum contrast before a high-energy section — the stripped-back breakdown makes the next section hit harder.

**Choosing between them:**
- Song needs a new harmonic direction → `[Bridge]`
- Song needs to strip down and spotlight the vocal → `[Breakdown]`
- Song needs both (strip down AND new perspective) → `[Bridge | Half-Time]` + `[Energy: stripped, minimal]`

### [Chorus] Peak-Default in Heavy Lanes — Use [Refrain] for Quiet Repeats (LOCAL-CONFIRMED)

`[Chorus]` carries a trained expectation that the section is the song's peak. **How strong that expectation is depends on the genre lane, and the difference is large enough to change how you tag.**

- **In restrained lanes** (folk, singer-songwriter, ballad, ambient, quiet alt), the peak-default is weak. A quiet chorus is achievable with descriptors alone — `[Chorus]` plus quiet-section wording behaves.
- **In heavy lanes** (metal, hard rock, metalcore, thrash-adjacent), the peak-default is **dominant and overrides descriptors.** Quiet-chorus descriptors and soft section tags fail there: the section renders as a peak regardless — full band, raised vocal, often yelled or gang-chanted.

**The working fix — confirmed in module production testing across multiple generations (2026-07), three parts, used together:**

1. **Retag the quiet repeating section `[Refrain]` instead of `[Chorus]`.** `[Refrain]` carries "repeated line" without carrying "this is the peak."
2. **Assign the roles explicitly at the prompt level** — state the inversion in the style prompt, e.g. "the verses carry the power; the refrains fall away to near-silence." The tag alone does not tell Suno where the song's energy lives.
3. **Exclude `anthemic chorus`.** This blocks the arrangement convention the lane keeps reaching for.

**Reserve `[Chorus]` for sections that are allowed to peak.** In a heavy-lane song where the loud material is in the verses, tagging any section `[Chorus]` reintroduces the problem you just solved. (Not yet re-tested on v6.)

**External status (2026-08):** heavy-genre users report the same problem (the model "hellbent on having the singer yell/scream in the refrain", with gang chants and stadium choruses) (COMMUNITY); their inline-descriptor fix (`[Chorus spoken, emotional]`) is reported to "not always work". The `[Refrain]` retag is ours alone.

### [Pre-Chorus] and [Post-Chorus] — Distinct Musical Sections

Both create genuinely distinct musical moments, not just extensions of adjacent sections:

- **[Pre-Chorus]** creates a **tension/lift build** before the chorus. Suno adds percussion, harmony layers, increases vocal intensity. Without this tag, transitional lyrics before a chorus may be sung awkwardly as "an extra line that doesn't fit the meter." Adding the tag signals the break in pattern is intentional. Keep short — 2-4 lines.

- **[Post-Chorus]** creates an **extension or cooldown** after the chorus. Can manifest as a repeated chant, vocal chops, instrumental hook, or response line. Inherits the chorus's energy level but creates a different musical moment. Most effective in pop/EDM; in rock/metal may blend more closely with the chorus.

### [Interlude] — Transitional Palette Cleanser

Defaults to **instrumental** (listed under Instrumental & Solo Section Tags). If lyrics are placed below it, Suno will attempt to sing them but with lighter/transitional musical treatment. Creates a brief palate cleanser between major sections — neutralizes energy rather than dramatically shifting it. Chaining `[Interlude]` with `[Solo]` is effective for changing movement or overall tone.

### Mapping Non-Standard Sections to Recognized Tags

When a song has sections that aren't traditional verse/chorus/bridge (e.g., spoken word passages, interrogative sections, narrative asides), map them to the closest recognized tag and use parameterized syntax to shape the feel:

| Section Intent | Recommended Tag | Why |
|---|---|---|
| Interrogative/reflective passage | `[Breakdown: building intensity]` | Strips instrumentation, spotlights vocal, creates contrast with surrounding sections |
| Spoken word passage | `[Verse X]` + `[Spoken Word]` | Verse structure with delivery override |
| Energy reset between aggressive sections | `[Break]` or `[Breakdown]` | Creates silence/space to prevent energy bleed |
| Closing passage that isn't a chorus | `[Outro]` | Suno treats as closing — appropriate energy wind-down |
| Build toward climax | `[Pre-Chorus]` or `[Build]` | Creates tension/lift |
| Repeated motif or chant | `[Post-Chorus]` or `[Hook]` | Inherits prior energy, repetition-friendly |

## Instrumental & Solo Section Tags

Tags that create instrumental moments with no lyrics. These add duration to the song beyond what lyric lines alone suggest.

| Tag | Usage | Typical Duration |
|-----|-------|-----------------|
| `[Instrumental]` | General instrumental section | 10-25 sec |
| `[Interlude]` | Musical bridge between sections | 8-20 sec |
| `[Solo]` | Generic instrumental solo | 10-25 sec |
| `[Guitar Solo]` | Guitar-focused solo section | 10-25 sec |
| `[Piano Solo]` | Piano-focused solo section | 10-25 sec |
| `[Sax Solo]` / `[Saxophone Solo]` | Saxophone solo | 10-25 sec |
| `[Drum Solo]` | Drum-focused solo section | 8-20 sec |
| `[Bass Solo]` | Bass-focused solo section | 8-20 sec |
| `[Break]` | Brief pause or stripped-back moment | 5-15 sec |
| `[Breakdown]` | Stripped-back section, reduces energy | 8-20 sec |
| `[Build-Up]` / `[Buildup]` | Rising energy, leads into a climax | 5-15 sec |
| `[Drop]` | Sudden energy release (EDM/electronic) | 10-20 sec |
| `[Synth Solo]` | Synthesizer solo section (HIGH) | 10-25 sec |
| `[Violin Solo]` | Violin solo section (HIGH) | 10-25 sec |
| `[Bass Drop]` | Sudden heavy bass entry, EDM style (HIGH) | 5-15 sec |
| `[Strings Rise]` | Strings gradually build/swell (HIGH) | 8-20 sec |

## Vocal Delivery Tags

Control how Suno's vocal engine performs specific sections. Place right before the section tag or between the section tag and the first lyric line. Use one primary delivery cue per section — stacking reduces effectiveness.

**Three-layer vocal specification** (HookGenius technique) — for maximum vocal control, specify across three layers:
1. **Character**: 'raspy female vocals', 'smooth baritone', 'deep female alto'
2. **Delivery**: 'breathy', 'powerful belt', 'whispered', 'falsetto', 'aggressive'
3. **Effects**: 'reverb-drenched', 'dry close-mic', 'doubled harmonies', 'lo-fi filtered'

'Just saying male vocals gives Suno no direction' — specificity across all three layers dramatically improves consistency.

**Vocal delivery reliability tiers** (HookGenius 300+ tag testing):
- **HIGH**: `[Raspy]`, `[Breathy]`, `[Powerful]`, `[Spoken Word]`, `[Choir]`, gender tags
- **MEDIUM**: `[Operatic]`, `[Whispered]` (reliable but reduces overall track energy), `[Melodic Rap]`, `[AutoTune]`, `[Harmonies]`
- **LOW**: `[Falsetto]`, `[Growling]`, `[Yodeling]` (rarely produces actual yodeling)

### Volume & Intensity
| Tag | Effect |
|-----|--------|
| `[Whispered]` / `[Whisper]` | Soft, breathy, intimate delivery |
| `[Soft]` / `[Gentle]` / `[Quiet]` | Subdued, low-volume singing |
| `[Spoken]` / `[Spoken Word]` | Spoken rather than sung |
| `[Powerful]` / `[Intense]` | Full-force, emotional delivery |
| `[Belted]` / `[Belting]` | Powerful, full-voice, high-energy singing |
| `[Shouted]` / `[Screamed]` | Aggressive, loud delivery |
| `[Growled]` / `[Growl]` | Low, guttural vocal delivery |
| `[Gritty]` | Gritty, rough vocal tone (HIGH) |
| `[Monotone]` | Flat, monotone delivery (HIGH) |
| `[Breathless]` | Breathless, urgent delivery (HIGH) |

### Vocal Style & Technique
| Tag | Effect |
|-----|--------|
| `[Falsetto]` / `[Head Voice]` | High, airy vocal register — **LOW reliability** (HookGenius testing: 'sometimes Suno delivers it, sometimes ignores it entirely'). Try 'natural falsetto, airy high register, effortless' in the style prompt instead for more consistent results. |
| `[Chest Voice]` | Full, resonant lower register |
| `[Breathy]` | Airy, breath-heavy vocal |
| `[Raspy]` | Rough, textured vocal |
| `[Smooth]` / `[Soulful]` | Polished, warm delivery |
| `[Operatic]` | Classical vocal technique |
| `[Crooning]` | Soft, intimate jazz-style singing |
| `[Nasal]` | Nasal-toned delivery |
| `[Airy]` | Light, ethereal vocal |
| `[Harmonies]` / `[Harmonized]` | Multi-voice harmony layering |
| `[Ad-libs]` / `[Ad-lib]` | Improvised vocal fills and runs |
| `[Vocal Run]` / `[Melisma]` | Extended note runs across syllables |
| `[Vibrato]` | Oscillating pitch on sustained notes |
| `[Staccato]` | Short, detached vocal phrasing |
| `[Legato]` | Smooth, connected vocal phrasing |
| `[Call and Response]` | Back-and-forth vocal pattern |
| `[Chant]` | Rhythmic, repetitive vocal pattern |
| `[Choir]` / `[Choir Vocals]` | Full choir sound |
| `[Scat]` | Improvised nonsense syllables (jazz) |
| `[Hummed]` / `[Humming]` | Hummed melody, no words |
| `[Whistled]` / `[Whistling]` | Whistled melody |
| `[Backing Vocals]` | Explicit backing vocal layer (distinct from parentheses technique) (HIGH) |
| `[Stacked Harmonies]` | Dense layered harmonies (HIGH) |
| `[Gospel Choir]` | Gospel-style choir (HIGH) |
| `[Narrator]` / `[Female Narrator]` | Narration voice, distinct from `[Spoken Word]` (HIGH) |
| `[Announcer]` / `[Reporter]` | Announcer or reporter voice style (HIGH) |
| `[Primal Scream]` | Raw, primal scream vocal (Experimental) |
| `[Diva Solo]` | Big diva-style vocal moment (Experimental) |
| `[Vocaloid]` | Vocaloid-style synthetic vocal (Experimental) |
| `[Gregorian Chant]` | Gregorian chant style (Experimental) |
| `[Androgynous Vocals]` | Gender-ambiguous voice (Experimental) |

### Rap & Hip-Hop Delivery
| Tag | Effect |
|-----|--------|
| `[Rapped]` / `[Rap]` | Rhythmic spoken delivery |
| `[Fast Rap]` / `[Double Time]` | High-speed rap delivery |
| `[Slow Flow]` | Deliberate, spaced-out rap |
| `[Melodic Rap]` | Singing-rapping hybrid |
| `[Trap Flow]` | Trap-style cadence with hi-hat patterns |
| `[Boom Bap Flow]` | Classic hip-hop rhythmic delivery |
| `[Mumble Rap]` | Mumbled, indistinct rap delivery (HIGH) |

### Vocal Identity
| Tag | Effect |
|-----|--------|
| `[Male Vocal]` / `[Male Vocalist]` / `[Man]` | Male voice |
| `[Female Vocal]` / `[Female Vocalist]` / `[Woman]` | Female voice |
| `[Boy]` / `[Girl]` | Younger-sounding voice |
| `[Duet]` | Two distinct voices alternating |

### Vocal Effects
| Tag | Effect |
|-----|--------|
| `[Reverb]` | Reverberant vocal treatment |
| `[Delay]` | Echo/delay on vocals |
| `[AutoTune]` / `[No AutoTune]` | Add or prevent pitch correction |
| `[Distorted Vocals]` | Distortion effect on voice |
| `[Filtered Vocals]` | Filtered/muffled vocal sound |
| `[Vocoder]` | Robotic/synthesized vocal effect |
| `[Telephone Effect]` | Lo-fi phone-quality vocal |
| `[Glitch]` | Glitch effect on vocals (Experimental) |

### Vocal Emotion
| Tag | Effect |
|-----|--------|
| `[Vulnerable]` | Fragile, exposed delivery |
| `[Defiant]` | Strong, resistant tone |
| `[Sultry]` | Sensual, low-energy seduction |
| `[Joyful]` | Bright, happy delivery |
| `[Melancholic]` | Sad, wistful tone |
| `[Aggressive]` | Forceful, combative delivery |

## Descriptor Metatags

Provide guidance to Suno's interpretation. Keep text short: 1-3 words.

### Core Descriptor Tags (Established)
| Tag | Example | Placement |
|-----|---------|-----------|
| `[Mood: ...]` | `[Mood: haunting]` | Top (global) or before section (local) |
| `[Energy: ...]` | `[Energy: building]` | Before section |
| `[Vocal Style: ...]` | `[Vocal Style: whispered]` | Before section |
| `[Instrument: ...]` | `[Instrument: solo piano]` | Before section |

### Additional Descriptor Families (HIGH confidence — colon syntax)
These follow the same `[Category: value]` pattern as the core descriptors above:

| Tag | Examples | Notes |
|-----|---------|-------|
| `[Atmosphere: ...]` | `[Atmosphere: Dreamy]`, `[Atmosphere: Cyberpunk]`, `[Atmosphere: Medieval]` | Sets environmental/spatial context |
| `[Texture: ...]` | `[Texture: Grainy]`, `[Texture: Velvet]` | Controls sonic texture quality |
| `[Effect: ...]` | `[Effect: Lo-fi]`, `[Effect: Reverb: Hall]`, `[Effect: Delay: Ping-pong]`, `[Effect: Distortion]`, `[Effect: Sidechain]`, `[Effect: Radio Filter]`, `[Effect: Bitcrusher]` (digital degradation/8-bit sound), `[Effect: Autopan]` (sound panning left to right), `[Effect: Sidechain]` (pumping volume effect, common in House) | Production effects — supports nested colon syntax for specificity |
| `[Harmony: ...]` | `[Harmony: High]` | Harmony register/style guidance |
| `[Voice: ...]` | `[Voice: Auto-tune]` | Vocal processing direction |
| `[Vibe: ...]` | `[Vibe: Cinematic]` | Overall vibe/feel — similar to Mood but more production-oriented |
| `[Tempo: ...]` | `[Tempo: slow]` | Tempo suggestion (note: BPM-specific tags remain ineffective — see Experimental Section Tags). Numeric forms like `[Tempo: 90 BPM]` are CONTESTED vendor guidance, so leave them out; see "CONTESTED — don't adopt new colon-modifier tag forms" below |

### Standalone Mood Tags (bare bracket — no colon needed) (HIGH)
These work as simple bracket tags without the `[Mood: ...]` prefix:

`[Uplifting]`, `[Haunting]`, `[Dark]`, `[Nostalgic]`, `[Somber]`, `[Romantic]`, `[Dreamy]`, `[Peaceful]`, `[Anxious]`, `[Euphoric]`, `[Mysterious]`, `[Playful]`, `[Epic]`, `[Intimate]`, `[Bittersweet]`, `[Triumphant]`

### Standalone Energy Tags (bare bracket — no colon needed) (HIGH)
These work as simple bracket tags without the `[Energy: ...]` prefix:

`[High Energy]`, `[Medium Energy]`, `[Low Energy]`, `[Chill]`, `[Driving]`, `[Explosive]`, `[Building]`, `[Relaxed]`, `[Frantic]`, `[Steady]`

**Mood word effectiveness:** Vivid, visceral words work better than polite ones. `[Mood: Mardi Gras]`, `[Mood: wild, party]`, `[Mood: dark, haunting]` are more effective than `[Mood: festive]` or `[Mood: celebratory]`. Suno responds to emotional intensity in tag language.

### Energy Tags — Production-Tested Behavior

These energy and vocal style descriptors have been tested across multiple gens with consistent results — treat as working defaults, not guarantees (Suno is probabilistic):

| Tag | Observed Effect |
|-----|-----------------|
| `[Energy: stripped, minimal]` | Tends to reduce instrumentation (consistent across observed gens) |
| `[Energy: massive]` | Tends to add full band weight (consistent across observed gens) |
| `[Energy: building]` | Works for gradual intensity increase (consistent across observed gens) |
| `[Vocal Style: whispered]` | More consistently quiet than `[Vocal Style: clean, distant]` across observed gens — preferred go-to for quiet sections |
| `[Vocal Style: acapella]` | Sometimes works, sometimes Suno adds light instrumentation anyway |
| `[Whispered, vulnerable]` | Worked consistently across observed folk-intimate / acoustic-singer-songwriter / ballad-intimate gens. **Context-dependent caveat (single-song observation):** In theatrical-horror / voodoo-rock / dramatic-narrative contexts, `[Whispered, vulnerable]` may pull Suno into spoken-word delivery rather than sung-quiet. Working alternative when sung-quiet is required in those genres: `[Vocal Style: soft, sung]` — the explicit `sung` token defeated spoken-word drift on that track. Whether the tag-pull and the alt-tag fix generalize across more theatrical-horror songs needs more observations. |

### Three-Phase Dynamic Arcs (Up, Peak, Down)
For songs that need to build UP and come back DOWN, place descent tags at the **transition point**, not just the outro. The mistake is saving all the quiet tags for `[Outro]` — by then the energy has already carried through. Instead:

1. Place `[Energy: minimal, fading to silence]` and `[Vocal Style: whispered, vulnerable]` **before** the final lines, at the moment the song should begin its descent.
2. `[Whispered, vulnerable]` is reliable for quiet sections in folk-intimate / acoustic-singer-songwriter / ballad contexts. Prefer it over `[Soft]` or `[Gentle]` when you need a guaranteed drop — but see the caveat above: in theatrical-horror / voodoo-rock / dramatic-narrative territory, it can pull Suno into spoken-word delivery. Use `[Vocal Style: soft, sung]` there; the explicit `sung` token defeats spoken-word drift.
3. The descent tag placement matters more than the outro tags. If the transition into the final section is already quiet, the outro follows naturally.

### Section-Tag Wording Can Itself Invite Choir Effects (ANECDOTAL, 2026-08)

An extension to the anti-choir stack (style prompt + Exclude Styles + section tags — the full stack lives in Mac's `docs/suno-production-patterns.md`): **the wording inside a section tag can invite the very group vocals you are excluding**, when the label implies group participation. A bare `[Chorus]` in a genre whose choruses are conventionally stacked is already a nudge toward extra voices.

- **Refined positive wording** (source's phrasing): "Solo lead vocal performance by one singer only… Chorus energy comes from instruments and arrangement, not extra voices."
- **Section-tag form:** `[Chorus - Solo Lead Vocal, Instrumental Lift Only]` — states where the lift comes from instead of only forbidding voices.
- **The limit, stated plainly by the same source:** "Exclude improves your odds, but it cannot override a prompt that strongly asks for group-vocal energy." Exclusion is probability reduction; the prompt is the stronger signal.

COMMUNITY for the stack itself (it matches our existing three-layer approach); ANECDOTAL for the label-invites-choir refinement. Related **local finding, still ours alone:** the "live"-family terms (`live`, `live recording`, `live performance`) pull crowd noise and crowd-vocal texture — external anti-choir guidance does not list them among its risk terms, and a 2026-08 re-search found nothing confirming it.

### Duet Recipe (ANECDOTAL — single aggregation, multi-user-replicated within it)

For male/female duets specifically, the reported working recipe splits across both fields: put the word **"Duet" in the STYLE field**, and put `[Male vocals]` / `[Female vocals]` in the **Lyrics** field at the switch points. Cap voice switches at **4-6 per track** — past that the model starts averaging the voices together.

This is consistent with our own harder-won finding below: gender contrast is the only reliably working duet axis, and `[Duet]` *alone* in the lyrics is unreliable. Treat this as a refinement of "gender contrast is the easiest path," not as a solution to the same-gender dual-voice problem, which remains unsolved.

**Screamed or harsh delivery: tag it in the Style field; do not phonetically spell the scream in the lyrics** (ANECDOTAL). Spelled-out screams get sung as words.

### Vocal Style Findings — Harmonized as Sweet Spot
`[Vocal Style: gritty]` combined with high energy and high Weirdness produces screaming even with Exclude Styles set to block it. `[Vocal Style: clean]` removes too much edge — it strips the character out of the vocals. **`[Vocal Style: harmonized]` on all sections is the sweet spot for dual-vocalist work** — it blends both voices naturally without pushing into scream territory or losing grit. "Raw gritty melodic singing" in the style prompt works fine when paired with `[Vocal Style: harmonized]` in the metatags — the style prompt provides the tonal character while the metatag controls the delivery mode.

### Dual Vocals — What Works and What Doesn't (updated 2026-04-09 with community research)

**Bottom line:** There is no fully reliable method in Suno v5/v5.5 to produce two genuinely distinct male voices trading lines in a single generation. Community consensus (Jack Righteous, Suno.wiki, HookGenius, Suno Architect) describes duets as "more of an exploit than a feature." **Same-gender male-male dual voicing is the hardest case** — nearly all working duet techniques rely on male/female gender contrast because gender is the strongest vocal signal the model respects.

**What DOES work reliably:**
- `dual male vocals harmonized and gritty` in the style prompt produces harmony/doubling on choruses (not distinct voices trading: the same voice doubled or harmonizing)
- `[Male]` / `[Female]` per-line — the only reliable duet technique, requires gender contrast
- `[Clean Vocal]` / `[Harsh Vocal]` — works in metalcore/deathcore/post-hardcore context, produces clean-vs-screaming contrast (not clean-vs-manic-speaking)

**What doesn't work:**
- `[Voice 1]` / `[Voice 2]` — numbering is ignored
- `[Male Vocal 1]` / `[Male Vocal 2]` — same-gender numbering ignored
- `[Lead Vocal]` / `[Response Vocal]` — ignored
- `[Duet]` alone — unreliable, voices swap roles or collapse into one timbre
- `dual vocals trading` in style prompt — does not produce trading
- Same-gender named characters (`[Lazarus]` / `[Mongoose]`) — inconsistent
- Persona + dual voices — Persona is designed for single-voice consistency, actively fights against vocal variation
- Describing two equal vocalists in style prompt — model averages conflicting descriptors into one voice

**Workarounds ranked by reliability (for same-gender dual-voice needs):**

1. **Multi-stage Studio Replace Section workflow** (HIGH reliability) — Persona OFF. Generate base track with main voice only. Use Replace Section on each intrusive voice section with a completely different style prompt (different vocal character descriptors, different delivery tags). Iterate section-by-section. Slow but actually works.

2. **Nu-metal/rapcore hybrid framing** (MEDIUM reliability, best aesthetic match for "manic/unhinged" characters) — Frame as "experimental nu-metal with rapid-fire manic spoken interjections" or invoke Mr. Bungle / System of a Down / Mike Patton / Serj Tankian territory. Rap-feature contexts tolerate vocal role-shifting better than straight metal. Model has training data of rapid vocal-character shifts in these genres.

3. **Metalcore clean/harsh framing** (MEDIUM-HIGH reliability, but produces scream not manic) — `[Clean Vocal]` main lines + `[Harsh Vocal]` or `[Shouted]` interjections. Reliably produces contrast, but the harsh voice comes out aggressive/screamed rather than gleeful/unhinged.

4. **Lead + Adlibs pattern** (MEDIUM reliability) — Main voice dominant, intrusive voice as sparse 3-6 word interjections maximum. Use `[adlibs: higher pitched spoken, manic]` inline before interjections. Keep sections to 8-12 lines max. Best fallback when the model keeps collapsing to one timbre.

5. **Separate generations + DAW stitch** (HIGH reliability, external tools) — Generate two full versions (one all-main, one all-intrusive) with different style prompts, then stitch sections manually in a DAW or via Extend.

**Parenthetical backing vocals for dual-voice effect:** Parentheses work as backing vocals reliably in pop/R&B/soul/gospel/hip-hop contexts. In thrash/metal contexts they come in as whispered phrases or ambience rather than true second-voice backing so they don't suit rapid intrusive-voice dialogue in those genres.

**Key prerequisite for all dual-voice attempts: Persona OFF.** Personas lock vocal character by design. Band profiles that use a Persona for their main sound must drop it for dual-voice songs and rebuild the sound character in the style prompt.

## Dynamic & Transition Tags

Tags that control energy flow and transitions within the song.

| Tag | Effect |
|-----|--------|
| `[Fade In]` | Gradual volume increase at start |
| `[Fade Out]` / `[Fade]` | Gradual volume decrease |
| `[Swell]` | Gradual intensity increase |
| `[Crescendo]` | Building volume/intensity |
| `[Decrescendo]` | Decreasing volume/intensity |
| `[Silence]` | Brief moment of silence |
| `[pause]` | Total silence; optionally timed as `[Pause 2s]` (ANECDOTAL — single source, V5-era) |
| `[space]` | Not silence — pads, reverb tails, room tone (ANECDOTAL — single source) |
| bare empty line | A short instrumental phrase or breath (ANECDOTAL — single source) |
| `[hard cut]` | Backfires: Suno often sings the words "hard cut", the same failure as negation and `[Stop]` (ANECDOTAL). Leave it out |
| `[Stop]` | Suno sings or yells the word "Stop" instead of stopping, so it can't control an ending |
| `[End]` | Hard stop — prevents trailing instrumental generation after lyrics. Most reliable single ending tag, but may still produce 5-15 seconds of trailing instrumental. |
| `[Soft End]` | Gentle ending variation (HIGH) |
| `[Dramatic End]` | Dramatic ending variation (HIGH). Production testing (2026-04): no abrupt ending on thrash/metal; it still trailed instrumental |
| `[Big Finish]` | Grand climactic ending (HIGH) — also works as a section tag |
| `[Instrumental End]` | Finish with instrumentation only, no vocals (HIGH) |
| `[Slow Fade Out]` | Longer, gentler fade — best for ambient/cinematic (HIGH) |
| `[Fast Fade Out]` | Quick fade — best for dance/shortform (HIGH) |
| `[Instrumental Fade Out]` | Vocals end, instruments continue briefly then fade (HIGH) |
| `[Cinematic Fade Out]` | Strings/pads fade first, rhythm fades last (HIGH) |
| `[Unresolved tension]` | Avoids tonic resolution, ends on suspended chord (HIGH) |
| `[Key Change]` / `[Key Modulation]` | Signal a key change, usually upward for a lift (HIGH) |
| `[Metric Modulation]` | Rhythmic shift changing perceived tempo (HIGH) |
| `[Accelerando]` | Gradually speed up tempo (HIGH) |
| `[Ritardando]` | Gradually slow down tempo (HIGH) |

**Grid loss after a tempo change:** after `[Accelerando]` or `[Ritardando]` Suno can lose the rhythmic grid for the rest of the track. Give it a way home: if the Bridge speeds up, open the final Chorus or Outro with a strong structural tag like `[Chorus]` so it recalibrates. Some sources suggest a numeric anchor (`[Tempo: 120 BPM]`) instead; treat that as unsupported, since BPM tags are librosa-confirmed ineffective here and numeric colon-modifier forms are CONTESTED vendor guidance (see below).

### Ending Control

No tag combination reliably stops a song cleanly right after the vocal. In production testing (2026-04) cropping in Suno's editor was the only deterministic ending, and primary-source users (r/SunoAI, 2026-08) report the same on v5.5: two-bar outros appended to nearly everything, FX tails cut, no ending prompt stopping a runaway. Tag for the best attempt and tell the user to expect a crop rather than promising a clean ending. Not yet re-tested on v6.

Pick by goal, and don't stack both goals in one lyric block:

- **A resolved ending:** `[Outro]` + `[End]` paired, the vendor-guide consensus (COMMUNITY); neither alone does as well. Aim for a 15-25 second outro that starts from a stable section, not over a fill or a vocal run. Prefer this when the Duration slider is set, since the slider's failure is a hard cutoff with no resolution; `[Outro – short resolved ending]` is one form seen in the wild (ANECDOTAL). On v6, users report `[Final Chorus]` … `[Instrumental Outro]` `[Hard Stop]` `[End]` with the style field asking to "complete every written lyric before a short instrumental outro and final hard stop" (VENDOR + COMMUNITY): the instrumental outro is a buffer, so a song that decides to end early spends it instead of cutting the singer off.
- **A short stop close to the last vocal:** `[Final Verse]` + `[Unresolved tension]` + `[End]`, the best combination in our testing. `[Outro]` tells Suno to play out a conclusion, which is what buys the long tail, so leave it out here; `[Unresolved tension]` avoids the tonic resolution that invites a coda. "abrupt ending" in the style prompt adds a small effect that stacks, most in genres with short endings (punk, hardcore).

Whichever you pick:

- `[End]` goes on the absolute last line with nothing below it, not even a blank line, which is reported to weaken it (COMMUNITY).
- `[Fade Out]` doesn't produce a fade. Guides call it a modifier beside `[Outro]` + `[End]`; primary-source users report it working in no configuration; `[Fade Out]` + `[End]` still left 14 seconds of tail on a thrash track. At high Weirdness the pair is still worth tagging, but a real fade is applied in the editor.
- These fail: `[Stop]` and `[hard cut]` get sung as words; `[Dramatic End]` still trails on thrash and metal; a doubled `[End]` acts as one; `[Outro: fading, sparse]` signals conclusion mode and can add instrumental.

**Repairing a bad ending** (ANECDOTAL; matches how we triage): trailing material → Crop; an abrupt final second → Fade Out in the editor; mid-song repeats → Replace Section; a missing ending → Extend. Replace Section on just the tail, retried, can also land a shorter ending. Don't regenerate a whole song over its ending. The Duration slider itself is a style-side setting, the `suno-style-prompt-builder` skill's.

## Sound Effect Tags

**Sound effects are the least reliable category of metatags.** Multiple sources confirm they "don't work at all, or only work partially, and might play in an unexpected part of a song." Plan for post-production rather than relying on in-lyrics effects.

**Bracket tags near lyrics may be interpreted as VOCAL PROCESSING, not standalone sounds.** `[Static]` placed before a lyric line may apply a static/distortion effect to the vocals rather than producing actual static noise. Tags like `[Distorted Vocals]`, `[Filtered Vocals]`, `[Telephone Effect]` are explicitly vocal effects; environmental tags like `[Static]`, `[Rain]` occupy an ambiguous zone where Suno may treat them as either ambient sounds or vocal treatments depending on context.

### Reliability Tiers

**HIGH — Training-data-derived tags** (appear in real lyric transcriptions from Genius/AZLyrics):
- `[bleep]` / `[Censored]` — bleep/censor sound
- `[phone ringing]` — phone ring
- `[gunshots]` — gunshot sounds
- `[spoken word]` — switches to spoken delivery

These work because Suno's model learned them from actual song transcriptions.

**LOW — Environmental/ambient tags** (listed in guides but inconsistently recognized):

| Tag | Examples |
|-----|---------|
| **Nature** | `[Rain]`, `[Thunder]`, `[Wind]`, `[Ocean Waves]`, `[Birds Chirping]`, `[Forest]` |
| **Urban** | `[City Ambience]`, `[Phone Ringing]`, `[Beeping]`, `[Static]` |
| **Human** | `[Applause]`, `[Cheering]`, `[Clapping]`, `[Chuckles]`, `[Giggles]`, `[Sighs]`, `[Screams]`, `[Cough]`, `[Clears Throat]` |
| **Music** | `[Record Scratch]`, `[Bell Dings]`, `[Fire Crackling]` |
| **Animals** | `[Barking]`, `[Squawking]`, `[Howling]` |

**Best results:** `[Applause]` at the end of live-sounding tracks, `[Birds Chirping]` at intros for morning ambiance. Most others are unreliable.

### Asterisk Inline Sound Effects

`*text*` cues are intended for background atmospheric layering, distinct from bracket tags. In practice, Suno may interpret them as percussion/rhythmic patterns rather than true ambient sounds (e.g., `*machinegun fire*` may produce rapid rim-shots rather than actual gunfire sound).

Confirmed working examples (atmosphere, not percussion):
- `*rainfall*`, `*wind sounds*`, `*ocean waves*`, `*vinyl crackle*`
- `*distant thunder*`, `*soft whispers*`, `*crowd cheering*`, `*cafe ambience*`

**Hybrid notation** `(*effect*)` — parentheses wrapping asterisks — may be more reliable for getting actual sound textures when bracket or asterisk notation alone fails.

**Limitations:** Overuse clutters tracks; effects may overpower vocals; results are unpredictable; effects may map to percussion/drum patterns rather than ambient sounds. Use sparingly and plan for post-production.

**Note:** This is the ONE exception to the 'no asterisks in lyrics' rule documented elsewhere.

### Reliable Alternatives to In-Lyrics Sound Effects

1. **Style prompt descriptors** — describe the atmospheric intent in the style prompt ("mechanical, industrial atmosphere") rather than using in-lyrics effect tags
2. **Suno Sounds** (Studio 1.x feature, Premier) — generated standalone sound effects, instrument samples, and ambient clips as separate audio files, to layer in a DAW. **Archived:** Sounds Mode does not appear in current Studio 2.0 copy — verify in the live UI before relying on it.
3. **Post-production** — generate the song cleanly, then add effects in a DAW. This is the most reliable approach for specific sound design.
4. **Stems extraction** (Pro/Premier) — Auto Split gives up to 12 stems; add effects to individual stems externally

Source: [Suno AI Sound Effects with Asterisks — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-sound-effects-asterisks)

## Production & Mix Tags (HIGH)

Tags that control production quality and mix effects. Place before sections or at top for global effect.

| Tag | Effect |
|-----|--------|
| `[Lo-fi]` | Lo-fi production quality |
| `[Reverb Tail]` | Extended reverb decay effect |
| `[Echo]` | Echo effect |
| `[Vinyl Crackle]` / `[Vinyl Hiss]` | Vinyl texture overlay |
| `[Distant Voices]` | Distant/far-away vocal texture |

## Timing & Rhythm Tags (HIGH)

Tags that control rhythmic feel and timing within sections. These are distinct from BPM tags (which remain ineffective — see Experimental Section Tags). These tags describe rhythmic patterns and feels that Suno can interpret.

| Tag | Effect |
|-----|--------|
| `[Half-Time]` | Half-time feel — slower, heavier beat |
| `[Swung Feel]` / `[Shuffle]` | Swing/shuffle rhythm |
| `[Triplet Feel]` | Triplet-based rhythmic feel |
| `[Syncopated]` | Syncopated rhythm |
| `[Straight]` | Straight (non-swung) rhythm |
| `[Four on the Floor]` | Steady kick on every beat |
| `[Polyrhythmic]` | Multiple simultaneous rhythms |
| `[Breakbeat]` | Breakbeat rhythm pattern |

**Rhythm nouns over tempo adjectives:** "Halftime," "double-time," "shuffle," "breakbeat" lock rhythmic feel better than "slow," "fast," "upbeat." These nouns describe specific drum patterns Suno can interpret; adjectives are vague and often ignored.

## Standalone Instrument Tags (HIGH)

These work as bare bracket tags in the lyrics field — not just via `[Instrument: ...]` colon syntax. Place before a section to feature that instrument, or use as section tags for solos/features.

### Keys
`[Piano]`, `[Electric Piano]`, `[Rhodes]`, `[Wurlitzer]`, `[Organ]`, `[Hammond Organ]`, `[Harpsichord]`, `[Clavinet]`, `[Mellotron]`

### Synths
`[Synth]`, `[Analog Synth]`, `[Moog Synth]`, `[Synth Pad]`, `[Lead Synth]`, `[Synth Stabs]`, `[Pad]`, `[Pluck Synth]`, `[Arpeggiated Synth]`, `[Synth Bass]`, `[Acid Bass]`, `[Supersaw]`, `[Wobbly Bass]`

### Strings
`[Acoustic Guitar]`, `[Electric Guitar]`, `[Distorted Guitar]`, `[Clean Guitar]`, `[Jangly Guitar]`, `[Fingerpicked Guitar]`, `[Slide Guitar]`, `[12-String Guitar]`, `[Classical Guitar]`, `[Bass Guitar]`, `[Slap Bass]`, `[Upright Bass]`, `[Fretless Bass]`, `[Violin]`, `[Viola]`, `[Strings]`, `[String Quartet]`, `[String Section]`, `[Cello]`, `[Double Bass]`, `[Pizzicato]`, `[Harp]`, `[Ukulele]`, `[Banjo]`, `[Mandolin]`, `[Sitar]`

### Brass & Winds
`[Saxophone]`, `[Tenor Sax]`, `[Alto Sax]`, `[Trumpet]`, `[Trombone]`, `[French Horn]`, `[Tuba]`, `[Brass Section]`, `[Flute]`, `[Clarinet]`, `[Oboe]`, `[Harmonica]`, `[Accordion]`, `[Bagpipes]`, `[Didgeridoo]`

### Percussion
`[Drums]`, `[Acoustic Drums]`, `[Electronic Drums]`, `[Brushed Drums]`, `[Live Drums]` (see caveat below), `[808s]`, `[808 Bass]`, `[808 Drums]`, `[Drum Machine]`, `[TR-909]`, `[Trap Hi-Hats]`, `[Taiko Drums]`, `[Congas]`, `[Bongos]`, `[Tambourine]`, `[Shaker]`, `[Handclaps]`, `[Claps]`, `[Gong]`, `[Timpani]`, `[Cinematic Percussion]`

**⚠ `[Live Drums]` and the "live" word family.** In the **Style** field, any form of the word — `live recording`, `live-band drums`, `live energy` — pulls crowd and audience texture on v5.5 (LOCAL-CONFIRMED, recurring). That finding is about the **Style field**, and this is the **Lyrics** field, where a bracketed instrument tag is scoped to a section rather than describing the whole production — so `[Live Drums]` is not automatically contaminated by it. It has not been isolated in testing either way. **Safe practice: get the un-programmed drum character from the Style field with wording that avoids the word ("acoustic kit, natural room ambience, single-take feel"), and if you want the section-level tag as well, listen for crowd texture on the first generation before trusting it.** Separately, `[Live Version]` is confirmed not-working (see Tags Confirmed Not Working) — a different tag with a different failure, not evidence about this one.

### Orchestral
`[Orchestra]`, `[Full Orchestra]`, `[Chamber Orchestra]`, `[Brass Stabs]`

## Per-Section Instrument Control

Suno has no per-section instrument exclusion — there is no `[No Brass]` or `[Instrument: exclude X]` tag. The Exclude Styles field is global and inconsistent for instrument exclusion. Instead, use these strategies:

### Negation Inside Standalone Brackets Backfires (COMMUNITY, 2026-08)

A bare negative bracket tag — `[no vocals]`, `[no drums]`, `[No Brass]` — **acts as a positive prompt.** The reported mechanism is that the model reads the noun and drops the negation, so `[no vocals]` *invites* vocals. Three independent threads report this, one with an OP-confirmed fix after switching the term to Exclude Styles.

This is the same failure class as `[hard cut]` (sung literally) and `[Stop]` (vocalized) — the bracket contents reach the model as content, not as an instruction to withhold.

**Rule: route every negative to the Exclude Styles field, or to positive filling in the lyrics** (name the instruments a section *should* have — Strategy 1 below). Never spend a lyric-side bracket on a negation.

**Unresolved exception:** the author of the ghost-vocal mumbling work reports explicit negatives working **inside compound pipe tags** (`[Break | Instrumental Only | No Vocals | ...]`). Standalone-bracket versus pipe-tag context is a plausible reconciliation but nobody has tested it. Until someone does: standalone negatives are known-bad, pipe-tag negatives are unproven, and Exclude Styles is the path that works.

**Hyphen-prefix exclude syntax (ANECDOTAL leaning COMMUNITY):** in the Exclude Styles field, a minus prefix per term — `-oohs, -aahs, -humming, -vocalise, -scatting, -crowd chants` — is reported working, and corroborates the minus-prefix form already used in our own catalog. This is Exclude-Styles-field syntax, not a lyric-side tag.

### Strategy 1: Positive Instrument Filling
Tell Suno what instruments a section SHOULD have — this fills the "instrument attention" and crowds out unwanted elements:
```
[Verse 3]
[Instrument: heavy distorted guitar, crushing bass]
```
By specifying the instruments you want, there's less room for unwanted instruments to creep in.

### Strategy 2: Style Prompt Instrument Ordering
Place instruments you want throughout the song in the first ~200 characters of the style prompt. Place instruments you only want in specific sections (e.g., "NOLA funk brass") at the very END of the prompt — later content has less global influence, so it's more likely to appear only where metatags reinforce it.

### Strategy 3: Section-Specific Generation (Pro/Premier)
Use the Legacy Editor (Pro) or Studio (Premier) to generate different sections separately with different style prompts. For example:
- Generate verses with a style prompt that has NO brass references
- Generate the outro/finale with brass in the style prompt
- Splice together using the editor

### Strategy 4: Reinforce with Energy + Instrument Tags Together
Pair `[Instrument: ...]` with `[Energy: ...]` tags for stronger section differentiation:
```
[Verse 3]
[Energy: building]
[Instrument: distorted guitar, pounding drums]

[Outro]
[Energy: celebratory]
[Instrument: brass section, funk bass, horns]
```

### Named Entrance/Exit Tags on v6 — a Thing to Try (2026-10-03 sweep)
One author reports that `[Instrument: Brass Out]` / `[Instrument: Brass In]` style tags at section boundaries *"WORK. V6 honors instrument entrances and exits on cue"* (one author, folk styles, no counts; ANECDOTAL). Against it, two users couldn't remove one instrument from a section. Drums kept appearing in drumless verses after ~70 prompts, and a Simple-mode edit didn't remove a guitar (ANECDOTAL ×2). The advice they got was to suggest something to replace it rather than ask for removal (Strategy 1). In production testing, the whole band backing off has worked, but taking out a single instrument hasn't. Untested here. List it as one more thing to try when a single instrument has to drop out of a section, alongside Strategies 1–4. It isn't a negation, so it doesn't fall under the bracket-negation rule above, but whether it behaves like one is unknown.

### Key Limitation
Even with these strategies, Suno's instrument control is probabilistic — the style prompt sets a global palette, and section-level tags nudge within that palette. For dramatic instrument changes between sections, section-by-section generation (Strategy 3) is the most reliable approach.

### The Stems Solution (Pro/Premier)

Per-section instrument control via prompting alone is unreliable. The most reliable workflow for songs requiring different instruments in different sections:

1. **Generate** with ALL desired instruments in the style prompt (accepting that they'll bleed into all sections)
2. **Extract stems** — Pro's **Auto Split** produces up to 12 stems: vocals, backing vocals, drums, bass, guitar, keys, strings, **brass**, woodwinds, percussion, synth, FX (50 credits). Premier's **Advanced Split** goes to ~100 instruments
3. **Edit in a DAW** (e.g., Audacity) — mute/remove unwanted instrument stems per section
4. **Export** the final mix — note that from 2026-09-03 all stems from a song count as that song's **single** download against the monthly cap

Brass separates well as a dedicated stem. This is the recommended approach for songs with section-specific instrumentation.

**Important:** External DAW editing is a one-way operation. Once you edit outside Suno, you lose Suno's editing capabilities (Replace Section, Extend, etc.) on that version. Plan your Suno edits BEFORE exporting to a DAW.

## Parameterized Section Tags (HIGH — MAJOR v5 Feature)

Section tags support inline arrangement instructions via colon (`:`) or pipe (`|`) syntax. This allows per-section arrangement control directly in the section tag itself, without needing separate descriptor tags.

### Colon Syntax — Arrangement Instructions
```
[Verse: whispered vocals, acoustic guitar only]
[Chorus: full band, powerful vocals]
[Bridge: stripped back, piano only]
[Verse 2: lo-fi, distant vocals, minimal drums]
```

### Pipe Syntax — Rhythmic/Feel Modifiers
```
[Chorus | Half-Time]
[Chorus | Double-Time]
[Verse 3 | Swung Feel]
```

**Compound pipe tags (COMMUNITY, 2026-08).** Users chain several instructions through one section tag, e.g. `[Break | Instrumental Only | No Vocals | Do Not Use Lyrics as FX]`, and the same syntax turns up independently in unrelated users' lyric sheets — which is what raises it above one person's habit. Note the tension with the "no X" finding below: negation inside a *standalone* bracket backfires, but the author of the ghost-vocal work reports explicit negatives working **inside compound pipe tags.** That reconciliation — pipe-tag context versus standalone bracket — is plausible but unresolved. Use compound pipe tags for positive direction with confidence; treat the embedded negatives as unproven.

Both syntaxes are confirmed working on v5. On v6, a dash form — `[Verse 1 - riff continues under vocal, drums drive]` — and pipe cues like `[Verse | whispered]` are reported read at render time (VENDOR); see "Suno v6 (PREVIEW)". The colon syntax is more flexible (accepts comma-separated arrangement descriptions), while the pipe syntax is cleaner for single modifiers. These can be combined with separate descriptor tags on subsequent lines for maximum control, but the inline approach is often sufficient and saves character budget.

**Relationship to BPM tags:** Note that `[Verse 1: 65 BPM]` style BPM parameterization remains ineffective (see Experimental Section Tags below). The parameterized syntax works for arrangement/feel instructions, not for tempo numbers.

### Heavy genres on v6: per-section blocks (to try)

For metal sub-genres that keep collapsing into one generic sound, four users (COMMUNITY, qualitative, 2026-10) report more control from a block of descriptor lines under each section tag than from a genre list in the style field:

```
[Chorus 1]
[Genre: ...]
[Mood: ...]
[Instruments: ...]
[Vocals: ...]
[Production: ...]
```

One of them: it "doesn't do it perfectly but gives much more control than just asking : [metal, deathmetal, growls, heavy guitar]". Two other users suggest keeping each bracketed instruction to about seven descriptors (untested). `[Mood: ...]` and `[Instrument: ...]` are established descriptor families (below); `[Genre: ...]` and `[Production: ...]` are not validated here, so try the block on one Create before building a package around it.

**Harsh vocals, stepped rather than switched** (ANECDOTAL, one tester, 2026-10): moving the delivery up across sections (clean → powerful clean → slight grit → raspy belt → heavily distorted belt) instead of tagging `[Scream]` or `[Death Growl]`, which "sometimes made V6 switch to what sounded like a completely different vocalist."

### CONTESTED — don't adopt new colon-modifier tag forms on vendor evidence

**Status as of 2026-08-13: CONTESTED, actively disputed.** A family of colon-modifier tags — `[Chorus: powerful]`, `[Energy: High]`, `[Tempo: 90 BPM]` and similar — circulates widely, but it is **asserted only by tag-generator vendors with a commercial interest in a large tag vocabulary.** Two independent exhaustive metatag references contain **no** colon syntax at all, and one explicitly flags invented tags as a common user mistake. There is no neutral source confirming that Suno parses a colon modifier as a modifier rather than as text.

**What this does and does not change here:**

- **Keeps its place:** the parameterized *section* tags documented immediately above (`[Verse: whispered vocals, acoustic guitar only]`, `[Chorus | Half-Time]`) and the core descriptor families (`[Mood: ...]`, `[Energy: ...]`, `[Vocal Style: ...]`, `[Instrument: ...]`). These are in the file because **our own production generations** showed the effects, not because a vendor listed them. Local evidence outranks vendor lists.
- **Do not adopt:** any *new* colon-modifier form on the strength of a tag-generator site, tag-count marketing, or a "1000+ tags" list. The failure mode is not neutral — an unrecognized tag can be **sung as lyrics** or, as our own Stillness finding showed, break Suno's structural parse.
- **Already-known-bad within this family:** `[Tempo: 90 BPM]` and every other numeric-BPM colon form. BPM tags are librosa-confirmed ineffective here (see "BPM Tags — Confirmed Ineffective"), so a vendor list recommending them is evidence about the list, not about Suno.
- **Bearing on our quiet-section work:** this is why the `[Refrain]`-in-heavy-lanes technique is **not** safe to generalize from tag lists — nothing external validates it (see the note under Section Structure Tags).

When in doubt, use a recognized section tag plus an established descriptor tag on its own line. That path is validated; the colon-modifier path is not.

## Experimental Section Tags

These are partially supported and may not work consistently across all models.

| Tag Syntax | Purpose | Notes |
|-----------|---------|-------|
| `[Verse 1: 7/8]` / `[Chorus: 4/4]` | Time signature hint per section | **Aspirational — expect 4/4.** Module production testing (2026-07) found meter signals move feel and tempo, not subdivision; see "Structural Metaphor via Time Signature Changes" above. The Studio time-signature picker was documented as "not yet sent to generative models" for Studio **1.2**; that article is now archived and the claim is **unverified for Studio 2.0**, so in-lyric tags remain the only lever we can reason about |
| `[Callback: ...]` | During Extend/Replace, references a prior section's feel | HIGH reliability for Extend/Replace workflows — 'Callback phrasing is respected reliably across Extend chains' (community-validated). Experimental for standard generation. e.g., `[Callback: Verse 1 energy]` — useful for maintaining continuity across generations |

### BPM Tags — Confirmed Ineffective

**BPM tags in lyrics have ZERO detectable effect on Suno's actual output.** This was tested across 5 songs with librosa analysis:
- A track tagged at 60 BPM throughout — Suno delivered 95.7 BPM
- A track tagged 65-150 BPM across sections — Suno delivered 123 BPM steady, no variation

Tags like `[Verse: 65 BPM]` or `[Chorus: 130 BPM]` are ignored by the generative model. Suno picks its own tempo based on genre, style prompt, and arrangement context. **Do not use BPM tags in lyrics — they waste character budget and create false expectations.**

For actual tempo/pacing control, see "Line Density as Tempo Control" and "Half-Time / Double-Time Drum Feel" below.

## Tags Confirmed Not Working

These tags are commonly recommended online but have been tested and found to have no reliable effect on Suno's output:

| Tag | Finding | Source |
|-----|---------|--------|
| BPM tags (`[Verse: 65 BPM]`) | Zero effect on output — confirmed by librosa analysis | Production testing |
| `[Bilingual]` / `[Spanglish]` | Placeholders with no evidence of special model behavior | Community testing |
| `[Live Version]` | Not reliably parsed; may subtly influence mixing but no strong evidence | Community testing |
| `[Mono]` / `[Wide Stereo]` | Subtle and inconsistent — Suno v5 does not reliably obey them | Community testing |
| `[Clean Lyrics]` / `[Explicit]` | Do not override the content filter | Community testing |
| `[Key Change]` (for precise control) | May nudge toward modulation but doesn't guarantee a specific key change — for precise transposition, export to a DAW | Community testing |
| Time signature tags in lyrics | Move feel/tempo but not the subdivision — expect 4/4 (module production testing, 2026-07, 3 data points). The Studio 1.2 "not sent to generative models" line is archived and unverified for Studio 2.0 | Production testing + archived official docs |

## Lyric Formatting as Suno Controls

These aren't metatags but formatting techniques that directly control Suno's vocal and rhythmic interpretation.

### Punctuation Effects

Symbol-to-pacing mapping. The comma / dash / ellipsis / `!` / `?` rows are long-established here; the period, `~`, trailing-dots, in-word-hyphen, and stacking rows are COMMUNITY (3+ independent sources, carried in from the 2026-07-18 research sweep).

| Character | Effect | Guidance |
|-----------|--------|----------|
| `.` (period) | Full break — end of a phrase, singer resets | COMMUNITY. The strongest of the pause marks; use where a line should genuinely land, not merely breathe |
| `,` (comma) | Breath pause / one beat | Use to shape natural phrasing |
| `—` / `--` (dash) | Hard pause / extended syllable linkage | Creates a harder pause than comma or ellipsis |
| `...` (ellipsis) | Micro-pause / trailing delivery | Suggests trailing off — more subtle than a dash. On v6 (2026-10-03 sweep), the only outside reading treats it as a breath or pause cue (one tester, ANECDOTAL). A production take that kept the ellipsis also lost the singer's riffing on that line (n=1), so the pause can win over ornament |
| trailing dots after a word (`hold...`) | Note hold — sustains the final syllable | COMMUNITY. Distinct from a mid-line ellipsis pause: at the end of a line it reads as sustain rather than gap |
| `~` (tilde) | Vibrato / wavering on the marked syllable | COMMUNITY. Sparse use only — it is a single-purpose ornament, not a pacing mark |
| in-word hyphen (`to-night`) | Syllable stretch / syllable separation | **Dual role — see the collision flag under Pronunciation / Phonetics.** It is our pacing-stretch device *and* the community's phonetic separator, and we have not established which dominates |
| `!` (exclamation) | **Bark/attack trigger** | Tells Suno's vocal engine to attack or bark that word, and the attack bleeds forward into later sections, so keep it out of sections that should be clean or quiet. Use sparingly even in aggressive sections; in metal it bleeds forward hard. |
| `?` (question mark) | Interrogative delivery | Generally respected — Suno lifts intonation at the end |
| No punctuation | Suno decides phrasing | Can be useful for intentional ambiguity — let the model choose |

**Stacking limit: at most two symbols together** (COMMUNITY). Beyond that the pacing intent stops reading and the marks start behaving unpredictably.

**Counter-signal worth knowing (2026-08 primary sources):** community reporting gives this pacing model **no support**, and two reports run against it — excess symbols blamed for verses looping, and advice to *remove* ellipses and parentheses because empty space and punctuation "invite improvisation" from the model. Our own A/B data (the vocable-count test below) is direct local evidence that punctuation changes delivery, so the table stands — but treat heavy punctuation as carrying an improv-invite risk, and keep the density low.

### Capitalization Effects
| Style | Effect | Guidance |
|-------|--------|----------|
| Sentence case | Normal delivery | Use throughout as baseline |
| ALL CAPS | **Loudness ceiling** | Confirmed: ALL CAPS words are sung with more passion/volume. If you cap words in Verse 1, you've already hit the ceiling — nowhere to build. Save caps for the absolute peak moment only (one word, one line, in the climax). *One ANECDOTAL source softly disputes this, calling caps "less reliable for rhythm control" — flagged, not adopted; our own production use is consistent and the claim here is about loudness, not rhythm.* |

### Repeated Vocables — Punctuate Every Member (LOCAL-CONFIRMED, A/B tested)

When a repeated vocable's **count** matters — three wails, four knocks, a specific number of chants — Suno merges or drops members unless every one of them is punctuated. Confirmed in module production testing by direct A/B on the same line:

| Written | Rendered |
|---|---|
| `waah waah, waah,` | three wahs collapsed into fewer — the unpunctuated pair merged |
| `waah, waah, waah,` | the intended count, cleanly separated |

**Rule: punctuate every member of a repeated vocable group.** Commas *within* a group, periods *between* groups when the groups should read as separate utterances. The punctuation is doing the counting — spacing alone does not survive the vocal engine, which treats an unpunctuated repeat as a single stretched utterance or a typo.

This is the same mechanism behind the exclamation-separator fix for doubled-word parentheticals below (`(plunging! plunging!)`), which is the aggressive-genre variant of the same rule. Nothing external addresses either — **both remain ours.**

### Stretched Words — Phonetic Disambiguation

When stretching a word with hyphenated letters for dramatic effect (e.g., `to-o-o-lling`), check whether the repeated vowel could collapse into a different word in Suno's vocal interpretation. If so, add a consonant or alt-vowel spelling to anchor the intended sound.

**Example — broken and fixed (production testing):**
- Broken: `to-o-o-lling` → Suno reads as "tooling" (the `to-o-o` collapses to "too" and lands on the more common nearby word)
- Fixed: `toh-o-o-lling` → Suno reads as "tolling" (the `h` forces the "OH" vowel rather than "OO")
- Result: `12 times tooling` became `12 times tolling` — intended word preserved through the stretch

**Why it happens:** Suno's vocal engine collapses repeated vowels into the simpler phoneme, and phonetically-ambiguous stretches drift to the closest common word in the engine's training data. Adding a consonant after the first vowel breaks the collapse and pins the intended sound.

**Disambiguation techniques:**
- **Insert `h`:** `toh-o-o-lling`, `moh-oh-oh-rning`, `loh-oh-oh-st`
- **Alt-vowel spelling:** `dy-eye-ing` instead of `dy-iii-ing`, `sigh-igh-ed` instead of `si-ii-ed`
- **Double-consonant anchor:** `roll-l-l-ling` emphasizes the `ll`, harder to collapse
- **Re-articulate the word:** `tolling... tolling... tolling` (ellipses + repetition) instead of elongation notation — often cleaner than stretching one word

**How to apply:** Before committing any hyphenated stretched-word in lyrics, run the collapse test mentally — *if this word gets sung as a long vowel, what word would Suno's engine settle on?* If the answer differs from the intended word, add phonetic disambiguation. Same applies when transforming poetry that has visual word-stretching conventions — the visual meaning may not survive vocal interpretation without phonetic anchors.

### Parentheses
| Format | Effect |
|--------|--------|
| `(words in parentheses)` | Interpreted as **backing vocals/texture**, not lead melody. Useful for dual vocal interplay: lead line with (backing harmonies). |

**Parenthetical Backing Vocals — Production-Tested Details:**
- **Space before the opening paren is required: `word (echo)` not `word(echo)`.** Verified across a full catalog — every song with working parenthetical backing vocals uses spaces before the paren. The no-space form caused an echo word to be skipped entirely on one song's bridge across multiple generations until spaces were added.
- **Paren must be at END of line.** Mid-line parens — parens with text after the closing paren on the same line — are dropped inconsistently. If the sentence continues past the paren, break the line after the closing paren and put the continuation on a new line. Example broken-and-fixed (production testing):
  ```
  Broken (mid-line, "(blasting)" dropped across gens):
    The neverending (blasting) Sound of the Bell

  Fixed (paren at end of line, renders reliably):
    The neverending (blasting)
    Sound of the Bell
  ```
- Build echo density as intensity climbs — selective use beats every-line use.
- Works best as single-word echoes in early verses, full-phrase echoes in later verses.
- Confirmed working: Suno rendered `(blasting)` as a distinct backing vocal layer (once spaces-before-paren + paren-at-end-of-line rules were both applied).
- **Long-paren fold-back fails as backing vocal (single data point):** A 10-syllable parenthetical like `(or at least that you think you need to be)` on its own line pulled as primary vocal rather than backing vocal interjection, even with triple-reinforcement (position-1 style-prompt descriptor + global `[Vocal Arrangement]` tag + per-section `[Vocal Style]` tags + paren-split into two shorter parens). Short parens (1-4 syllables) land as backing vocal interjections reliably; long parens (10+ syllables) pull as primary vocal continuation. The boundary is approximate — probably 5-7 syllables depending on context. When the fold-back logic requires a longer response phrase, the backing-vocal call-and-response effect may not land even with triple-reinforcement.
- **Genre-dependent:** Parentheses produce true backing vocals in pop/R&B/soul/gospel/hip-hop contexts. In thrash/metal they come in as whispered phrases or ambience rather than a second voice. Not suitable for rapid intrusive-voice dialogue in heavy genres — see Dual Vocals section above for genre-appropriate alternatives.
- **Risk framing from primary sources (2026-08):** experienced users describe parentheses as an **ad-lib trigger, not a control** — "Suno treats empty space or parentheses as room to improvise." That is the opposite of our catalog's experience, and the likely difference is discipline: our reliable results all use the space-before-paren and paren-at-end-of-line rules above, which the complaining reports do not mention following. **Keep the discipline; treat undisciplined parens as an invitation to improvise.** If a generation is coming back with unrequested ad-libs, parenthetical density is a reasonable first thing to cut. Suppression levers live style-side: that's a style-field fix, so invoke the `suno-style-prompt-builder` skill.
- **On v6, instructions in parentheses may be sung** (COMMUNITY-compiled, 2026-09, plus one first-hand report, 2026-10; no controlled test): a compilation of v6 tips marks as consensus, by tallying sources rather than testing, that parentheses hold sung text and that "Instructions in parentheses get sung, sometimes as gang vocals". One user's `(Hey!)` came out as crowd shouts. Keep arrangement and performance directions in square brackets on v6, and test the end-of-line performance cues below on one Create before relying on them.

**Doubled-word parentheticals — atmospheric/ritualistic backing (April 2026 production observation):**

Identical doubled words inside parens — `(plunging plunging)`, `(watching watching)`, `(caressing caressing)` — produce a ritualistic/trance group-vocal effect that intensifies the preceding lyrical image rather than echoing it. Different use case from the traditional `word(echo)` backing-vocal technique. Works well for psychedelic, swamp-blues, voodoo-atmosphere, gothic, and ritual-trance genres.

**Two production problems observed with doubled-word parentheticals:**

1. **Single-word truncation** — Suno sometimes renders `(plunging plunging)` as just `(plunging)`, interpreting the doubled word as a typo. **Fix: exclamation-separator.** `(plunging! plunging!)` forces Suno to read them as two distinct utterances by placing punctuation between. Genre caveat: exclamations trigger aggressive vocal attacks in metal and heavy-rock contexts — use with care outside psych/blues/folk/Americana/atmospheric-rock genres.

2. **First-section failure** — Suno uses the first lyrical section to establish the song's sonic palette. Non-default vocal arrangements (like group-backing-on-parens in rockabilly or psychedelic-blues, where backing vocals aren't the genre default) frequently fire on V2+ but MISS on V1 entirely. Once Suno "commits" to the absence of backing vocals in V1, it often continues inconsistently even if tags explicitly request them. See **"Establishing Non-Default Vocal Arrangements"** subsection below for production-tested remediation.

**Inline vs. line-separated parentheticals:** When the backing-vocal pattern fires inconsistently across verses, inline parentheticals (`The knife (plunging! plunging!)` on the same line as the lyric) are more reliable than line-separated indented parens. The line-separated style signals "spoken interjection" to Suno (see next subsection); inline signals "sung backing vocal."

### Establishing Non-Default Vocal Arrangements (April 2026)

When a song requires a non-default vocal arrangement — group backing vocals throughout, call-and-response, dual vocal interplay, parenthetical chants — that isn't typical for the target genre, Suno's first-section behavior frequently becomes load-bearing. Suno treats the first lyrical section as arrangement establishment; if the arrangement element doesn't fire on V1, Suno often "locks in" its absence and the pattern continues inconsistently through the rest of the song.

**Production-tested remediation: wordless-chant intro** — the most reliable single lever.

Add a dedicated `[Intro]` section with **non-lyrical content that demonstrates the vocal arrangement pattern before any story-bearing lyrics arrive**. Example:

```
[Intro]
[Instrumental groove with group vocal chants establishing the pattern]
(oh oh) (ah ah) (oh oh) (ah ah)

[Verse 1]
[Energy: hypnotic, established groove]
[Vocal Style: lead with prominent group backing vocals on every parenthetical]
The knife (plunging! plunging!)
The door (slamming! slamming!)
...
```

Suno hears the pattern first, commits to it as part of the song's sonic identity, then applies it consistently through V1+.

**What doesn't work alone** (observed across multiple gens on a rockabilly-primary / psychedelic-blues-wild-card song, April 2026):

- **Renaming `[Verse 1]` to `[Intro]` without adding pre-lyrical content.** Section-type relabel doesn't carry enough weight. Tried across 1 Create (2 gens) — both missed backing vocals on the renamed-Intro section anyway.
- **Strong per-verse `[Vocal Style:]` tags on V1 alone.** Suno interprets per-section vocal style tags as advisory and frequently ignores them for arrangement elements that would require the whole arrangement to shift (e.g., bringing in group backing vocals that the song "doesn't have").
- **Global `[Vocal Arrangement:]` tag at the top of lyrics alone.** Necessary but not sufficient — contributes reinforcement only when combined with an actual pre-lyrical demonstration section.

**Belt-and-suspenders combination** (confirmed-working for group-backing-in-parens with a clean-voice Voice clone on v5.5, psychedelic swamp voodoo blues, April 2026):

1. Wordless-chant intro section demonstrating the pattern (primary lever)
2. Global `[Vocal Arrangement: lead vocal with group responses on parenthetical lines throughout]` at the top of the lyrics block
3. Per-section `[Vocal Style: lead with backing vocal in parenthesis]` on every verse
4. Stronger-phrased tag on V1 specifically (`lead with prominent group backing vocals on every parenthetical`)
5. Critical-zone style prompt placement: the arrangement descriptor at position 1 of the style prompt (e.g., `group backing vocals throughout, psychedelic swamp voodoo blues, ...`)
6. Exclamation-separators on doubled-word parentheticals across all verses

**Energy tag interaction caution:** `[Energy: building]` on V1 can fight vocal-arrangement establishment. "Building" signals start-minimal-and-layer-in and may suppress group backing vocals Suno would otherwise include. When V1 needs the arrangement present from bar 1, use `[Energy: hypnotic, established groove]` or similar locked-in framing and reserve `[Energy: building]` for later verses where escalation is the actual goal.

**Why this pattern exists (hypothesis):** Suno's arrangement decisions appear to lock in early based on the first vocal section's delivery. Non-default vocal arrangements require Suno to "decide" the song has that arrangement — and the decision happens during the first sung section. A wordless intro with the pattern demonstrated gives Suno pre-commit evidence that the arrangement is part of the song's identity, not a per-section advisory.

**Isolated parentheticals as performed speech (April 2026 production observation):**

When parentheticals are placed on their own indented lines — not attached to a preceding line as `word(echo)` — Suno often delivers them as **spoken interjections** rather than sung backing vocal harmonies. This is a practical observation from production generations across multiple songs, not documented behavior.

```
she's telling me about her day
and I am making
                        the right noises

        (uh-huh)
                (sure)
                        (really)
                                (sorry to hear that)
```

In this pattern, Suno tends to render `(uh-huh)`, `(sure)`, `(really)`, etc. as brief spoken interjections — a backing-vocal layer delivered as speech rather than singing. Works reliably across most genres including rock, Americana, adult alternative, and nu-metal (a `(He's lying!)`-style interjection in a nu-metal track is an adjacent case).

**Practical implications:**
- **Good for conversational/reactive interjections** (filler speech, reactions, asides) that shouldn't compete with the sung lead as harmony. The spoken delivery keeps them in the background without requiring a full `[Spoken Word]` section.
- **Works with v5.5 Voices** even though Suno's documentation cautions that Voices aren't suitable for sustained spoken word. Brief parenthetical interjections are a different case from `[Spoken Word]`-tagged full sections — the interjection length is short enough that Voices don't drift.
- **Fallback if not delivered spoken:** if a specific generation renders them as sung backing vocals instead of spoken, regenerate — the behavior is consistent across most gens but not 100% deterministic.
- **Distinct from attached parentheticals** — `word(echo)` still works as the traditional backing-vocal echo technique. The isolated-line pattern is a different use case producing different behavior.

### Inline Performance Modifiers (HIGH)
Parenthetical performance cues placed at the END of a lyric line to direct vocal delivery for that specific line. **This is a SEPARATE use of parentheses from backing vocals** — context determines interpretation. Backing vocals typically echo/repeat a word from the line; performance modifiers are delivery instructions.

| Cue | Effect | Example |
|-----|--------|---------|
| `(breathy)` | Breathy delivery on that line | `I can't stop thinking about you (breathy)` |
| `(belt)` | Belted/powerful delivery | `HOLD ON (belt)` |
| `(breath)` | Audible breath/pause | `wait for me... (breath)` |
| `(hold)` | Sustained/held note | `stay with me (hold)` |

**Disambiguation from backing vocals:** Backing vocal parentheses contain lyric words that Suno sings as a second voice — e.g., `running through the fire(fire)`. Performance modifiers contain delivery instructions — e.g., `running through the fire (breathy)`. When in doubt, the presence of a recognizable delivery keyword (`breathy`, `belt`, `hold`, `breath`) signals a performance modifier.

### Structural Timing in Lyrics — Not Reliably Parsed (downgraded 2026-08-13)

Time-based instructions at the top of the lyrics field are widely recommended:

```
lyrics begin at 0:15; instrumental only after 1:45
```

**They are not reliably parsed.** Both community reporting and our own production use agree: `lyrics begin at 0:00` and its relatives sometimes appear to land and often do nothing, and there is no way to tell which happened except by listening. This was previously documented here as HIGH confidence; that was wrong.

**How to treat them:**
- **Harmless as an extra.** They cost a few characters and occasionally help. Including one is not a mistake.
- **Never load-bearing.** If the song's structure depends on vocals starting at a specific moment, this line will not deliver it.
- **A short instrumental intro is Suno-standard.** Asking for vocals at 0:00 is asking the model to skip something it does by default in most genres — expect the default to win.
- **Post-generation crop is the only deterministic fix** for an intro that is too long, exactly as with endings.
- **Two v6 intro habits the lyric sheet can't override (COMMUNITY, 2026-10):** most v6 songs open with the same one-note synth or string swell, and Exclude or "no intro" doesn't reliably stop it; and a drum-only opening (drums alone for the first bars) isn't reliably promptable — other instruments join anyway, even when excluded. Don't build a song whose opening depends on either. A hard-start line at the top of the lyrics (`[Hit beat one immediately, no intro, no synth pad]`) and a bracket naming when each instrument enters are untested suggestions; the reliable routes are cropping the swell and building a drum-only intro in Studio or a DAW.

### Line Density as Tempo Control
This is the **PRIMARY mechanism** for controlling perceived tempo in Suno-generated vocals.

| Technique | Effect | Example |
|-----------|--------|---------|
| Short fragmented lines (1-3 words) | Slower delivery — each line gets its own phrase | `Fall` / `apart` / `slowly` |
| Single words on their own line | Slows and strips down — creates dramatic pauses | `Gone` |
| Long packed lines (many syllables) | Faster delivery — Suno compresses to fit | `Running through the city streets with nothing left to lose tonight` |
| Sparse words, long lines | Slow, spacious feel | `Drifting... on... the... tide` |
| Line breaks | Musical breaths — write breaks where you want the singer to breathe | |

**Key insight:** Word density is the main control for perceived tempo. BPM tags have zero effect (confirmed by librosa — see Experimental Section Tags above). Energy metatags alone (`[Energy: high]`) don't reliably drive actual BPM shifts — they signal intensity but not tempo. Suno picks a single steady BPM for the entire song regardless of tags; what changes is *perceived* tempo through delivery density and arrangement.

**Foundational principle: Suno does not actually shift tempo within a song.** When a style prompt requests "tempo shifts" / "tempo changes" / "dynamic pacing," and when section metatags request `[Heavy: halftime]` / `[Double Time]`, Suno produces **arrangement-density variation** — instrumentation pullback to create a halftime *feel*, compression to create a double-time *feel* — but the underlying BPM stays absolutely constant across the song. Production-confirmed across multiple catalog tracks whose prompts explicitly requested tempo changes: librosa-measured BPM is steady end-to-end; the listener's experience of "slower in lucid sections, faster in manic" is entirely arrangement-driven. **Practical implication:** stop treating "tempo changes" as a tempo control; treat it as an **arrangement-density / delivery-density** control. Plan for one underlying tempo per song and use the techniques below to vary perceived feel within that fixed tempo grid. Felt-tempo readings (taken from the densest section where the pulse is most countable) should be the basis for sequencing decisions, not librosa raw — see `audio-analysis-reference.md` Felt BPM Corrections table for catalog examples.

**Why it works:** Librosa analysis confirms that BPM does not actually change between sections, even when sections *feel* dramatically different in speed. A "hustle bustle" section with packed syllables feels like acceleration, but the underlying tempo is identical. The perception of speed comes from how much vocal content Suno must deliver per beat — and from how dense the arrangement is (sparse passages feel slower than dense ones at the same BPM).

**Recommended multi-technique approach for perceived tempo contrast:**
The most effective tempo contrast uses these together — line density is the most reliable single technique:
1. **Line density (PRIMARY)** — short fragmented lines for slow sections, packed lines for fast. Most reliable mechanism.
2. **Half-time / double-time drum feel** — use rhythm nouns in metatags: `[Heavy: halftime]`, `[Double Time]`. Creates perception of halved or doubled tempo without BPM change. See below.
3. **Instrumental density / arrangement dropout** — pulling instruments out creates space that feels slower. Adding everything back feels like acceleration. Use `[Energy: stripped, minimal]` for slow feel, `[Energy: massive]` for fast feel.
4. **Line breaks as breath points** — more line breaks = more pauses = slower perceived delivery. Fewer breaks = longer phrases = faster feel. Write breaks where you want the singer to breathe.
5. **Energy metatags** — `[Energy: low]` / `[Energy: high]` to signal intensity shifts (affects feel, not actual BPM)
6. **Style prompt priming** — include "tempo changes" in the style prompt
7. **Weirdness slider** (Pro/Premier) — higher values (60-65+ tested) encourage rhythmic variation

**Leave BPM tags out:** they are confirmed ineffective (see above). Each of the above techniques reinforces the others. Line density alone produces the most consistent results.

### Half-Time / Double-Time Drum Feel

Drums can switch to half-time snare patterns without the actual BPM changing, creating the perception of halved tempo. This is one of the most effective perceived tempo control techniques after line density.

| Tag | Effect | Notes |
|-----|--------|-------|
| `[Heavy: halftime]` | Half-time drum feel — snare on beat 3 only | Creates perception of halved tempo. Powerful for heavy/slow sections. |
| `[Double Time]` | Double-time drum feel — snare on every beat | Creates perception of doubled tempo. Good for energy surges. |
| `[Breakdown]` + halftime language | Stripped-back half-time section | Combine with short fragmented lines for maximum slow-down effect |

**Rhythm nouns over tempo adjectives:** "Halftime," "double-time," "shuffle," "breakbeat" lock rhythmic feel better than "slow," "fast," "upbeat." These nouns describe specific drum patterns Suno can interpret; adjectives like "slow" are vague and often ignored.

### Scream Bleed-Through Prevention
Once Suno enters aggressive/scream mode, it tends to carry that energy forward into subsequent sections. Prevention strategies:

1. `[Vocal Style: whispered]` is a **harder vocal reset** than `[Vocal Style: clean]` — use after aggressive sections
2. Every section after an aggressive one needs an explicit vocal style reset tag
3. Never use `!` or ALL CAPS in sections immediately following an aggressive section
4. Consider adding a `[Break]` or `[Instrumental]` buffer between aggressive and clean sections

### Spaced-Out Letters as Vocal Effect
Placing spaces between every letter of a word — e.g., `R I G H T N E S S` — is a coin flip. Sometimes Suno spells out each letter individually, creating a powerful wall-of-sound moment. Sometimes it just sings the word normally. Not reliable enough to depend on. Worth trying for high-impact single words where a spelled-out delivery would be dramatic, but always have a fallback plan if Suno ignores it.

### Whispered Repeat as Closer
Adding a final whispered repeat of the last word or phrase after the poem ends creates a powerful closing echo-into-silence effect. Suno handles this well — it's a good standard technique for closing tracks.
```
[Outro]
Final lyric line here

[Whispered]
Forever

[End]
```
The `[Whispered]` tag before the single repeated word, followed by `[End]`, produces a natural fade-to-silence moment. Use the most resonant word from the final line or the song's central image.

### Vowel Stretching & Syllable Manipulation
| Technique | Effect |
|-----------|--------|
| `loooove`, `feeeel` | Nudges cadence — extended vowels suggest held/sustained delivery |
| `to-o-o-lling` | Hyphenated vowel extension can stretch a word for dramatic effect — results vary |
| Use sparingly | Test iteratively — results are inconsistent |

### Pronunciation / Phonetics
Suno has no dictionary — it guesses pronunciation from spelling patterns. This creates problems with homographs and unusual words.

- **Homographs are the biggest problem:** `lives` (verb "he lives" vs noun "our lives"), `read`, `lead` — Suno picks one pronunciation and may guess wrong.
- **Context from surrounding words doesn't reliably help** Suno pick the right pronunciation.
- **Phonetic spelling fixes:** `through` to `thru`, `lives` (verb) to `livz`, `Breaths` (verb) to `Breethz`.
- **Hyphenation forces syllable breaks:** `to-night`, `liv-uz`.
- **Only use phonetic spelling where a word has more than one valid reading** — don't phonetically spell unambiguous words.
- **Keep original spelling in the songbook** and note the phonetic substitution in the Suno lyrics version.
- **Post-generation lyric editing works** for pronunciation fixes — generate, listen, then fix spellings and re-generate if needed.

**Community respelling rules (COMMUNITY, multi-source, added 2026-08-13) — these match and sharpen the practice above:**

- **Hyphenated syllables plus caps for stress:** `SEER-sha`. Write the sound a singer produces, not the etymological spelling.
- **Keep ONE spelling, consistently, across the whole lyric.** Changing the spelling of a word between verses changes the performance — the model reads it as a different word, not the same word spelled two ways.
- **Only respell AFTER a word actually fails, and only the failing word.** Pre-emptive respelling costs character budget and risks introducing a new mispronunciation. This is the same discipline as our mid-word-anchor rule: leave the syllables Suno gets right alone.
- **Pronunciation is permanent post-generation.** Fix it in the lyrics *before* generating. The only surgical remedy afterwards is Replace Section on the misread span — and do **not** try to fix pronunciation with Chat ("fix the singer") or with Cover; neither is a pronunciation tool.

**⚠ Collision flag — hyphens do two jobs at once (open question, flagged not resolved).** An in-word hyphen is **our** syllable-STRETCH pacing device (`to-o-o-lling`, see Stretched Words above) *and* the community's phonetic syllable separator (`in-fih-nigh-tum`, `to-night`). Both uses are plausibly real, which means **a hyphen inserted for pacing may silently alter pronunciation, and a hyphen inserted for pronunciation may silently alter pacing.** We have not tested which dominates, or whether it depends on whether the hyphenation spans a repeated vowel. This is a targeted test candidate. Until it is run: when a word needs both treatments, prefer re-articulation (`tolling... tolling...`) over stacking a stretch and a respelling into one hyphenated token.

#### Mid-Word Vowel Anchoring with English-Word Fragments

When a word's mispronunciation is localized to one syllable (typical for Latin terms, scientific vocabulary, or unusual proper nouns), respell only that syllable with an English-word fragment that unambiguously encodes the target vowel sound. The principle: hand Suno a spelling-pattern it has clearly trained on, mid-word, in place of the ambiguous original.

**Example — broken and fixed (production testing, a track with a Latin phrase in the lyric):**
- Broken: `ad infinitum` → Suno reads "ahd in-fih-NIH-tuhm" (short-i in the stressed syllable, wrong)
- Fixed: `ad in-fih-nigh-tum` → Suno reads "ahd in-fih-NIGH-tuhm" (long-i correct, Anglicized pronunciation lands)
- Result: production-confirmed clean delivery on regen 2026-04-29 with `nigh` lowercase

**Why `nigh` works:** It's an English word with unambiguous long-i pronunciation (rhymes with high/sigh/thigh). Suno's spelling-pattern prediction has clearly trained on it. The hyphenation `in-fih-nigh-tum` forces syllable breaks; the phonetic anchor sits inside that hyphenated structure and Suno renders the long-i without drifting to a more common nearby word.

**Common mid-word vowel anchors (English fragments, all uniquely-pronounced in standard English):**
- **Long-i:** `nigh`, `eye`, `igh` (stretched only — see Stretched Words section), `nye` / `dye` / `rye` family
- **Long-a:** `way`, `ray`, `bay` family
- **Long-o:** `oh`, `dough`, `toe`, `bow` (where unambiguous)
- **Long-e:** `ee`, `bee`, `tea`
- **Long-u (yoo):** `you`, `cue`, `due`
- **Long-u (oo):** `boot`, `moo`, `flu`

**How to apply:**
1. Identify the syllable Suno is mispronouncing (single syllable, usually).
2. Identify the target vowel sound (long-i, long-a, etc.).
3. Substitute that syllable with an English-word fragment containing the target sound.
4. Hyphenate to force the syllable break around the substitution: `original-fix-original`.
5. Per the "phonetics only where ambiguous" principle, leave the syllables Suno gets right untouched. `ad infinitum` doesn't need `ad` and `tum` respelled — only the broken `nih` syllable.

**Capitalization on phonetic anchors:** ALL CAPS on a phonetic-anchor syllable adds delivery loudness/intensity per the Capitalization Effects section above, not a different pronunciation. `nigh` and `NIGH` are pronounced the same; `NIGH` just gets sung louder. Use ALL CAPS on the phonetic anchor only when (a) the syllable is naturally stressed in correct pronunciation AND (b) the loudness boost serves the section's dynamic (not, e.g., a quiet verse where one boosted syllable would be jarring).

**Distinct from Stretched Words guidance** (next section): that guidance covers DRAMATIC ELONGATION via hyphenated repeated letters (`to-o-o-lling`); this guidance covers NON-STRETCHED mid-word fixes for normal-tempo delivery. Both use the principle of substituting unambiguous English-word fragments, but apply in different contexts.

### Ghost Vocals on Instrumental Tracks — Two Layered Defences (COMMUNITY)

Instrumental generations frequently come back with wordless vocal texture ("ghost vocals") even when nothing asks for it. Two approaches, both reported to work; the second is the belt-and-suspenders version:

1. **Use the Lyrics box as a wordless structural timeline** — section tags only, no words at all (`[Intro]`, `[Verse]`, `[Solo]`, `[Outro]`, `[End]`). Suno still gets the structure, but there is nothing to sing. This also solves the "instrumental sections are dangerous" problem below by bounding each section.
2. **Triple-layer it** — `instrumental, no vocals` in the Style field **+** `[Instrumental]` in the Lyrics field **+** exclusions covering `voice, singing, chanting, vocal samples`. The exclusion list matters because Suno's default vocal texture is not always "singing": excluding only "vocals" can leave chanting or sampled voices in.

Note that both defences are prompt-side probability work, not switches — a paid-tier user also has the Instrumental toggle, which is the reliable control (on the reworked v6 Create sidebar, one user found no Instrumental toggle as of 2026-10-05 — if it isn't there, leave Lyrics empty and let the exclude list carry the anti-vocal load).

**⚠ Put the negation in the right place.** Write `instrumental, no vocals` in the **Style** field and the unwanted elements in **Exclude Styles** — do **not** write `[no vocals]` as a standalone bracket tag in the lyrics. See "Negation Inside Standalone Brackets Backfires" under Per-Section Instrument Control: a bare `[no vocals]` can *invite* the thing it names.

**The mumbling mechanism (ANECDOTAL, but the most mechanistic account available — 2026-08).** The specific failure where an instrumental comes back with smeared, wordless muttering has a reported root cause: **atmospheric wording in the style prompt plus lyrics anywhere in the sheet.** Words like "atmospheric," "FX only," "pads," "textures" tell the model to build background texture; if any lyric text is present, it time-stretches and reverb-smears **the user's own lyric fragments** into that texture. Three reported fixes, which stack:

1. **Keep lyrics strictly inside Verse/Chorus blocks** — stray lines floating outside a section block are the raw material the smearing feeds on.
2. **Name the atmosphere source explicitly** — "atmosphere created by pads, noise, reverb tails — not vocals." Filling the texture role with named instruments leaves nothing for voice to fill it with.
3. **Ban the vocal-as-instrument treatments by name in the style prompt** — "no vocal chops, no mumbled speech textures, no formant-shifted vocals used as instruments."

**Dots-as-lyrics instrumental trick (COMMUNITY, partial reliability).** Keeping section headers intact but filling the lyric blocks with lines of periods (`. . . .`) is reported to render the vocal melody **on an instrument** instead of a voice — an instrumental that keeps the topline. Multiple confirmations, with caveats: one user needed Audio Influence around 50%, and one reported it working once and then not. Worth trying when a wordless structural timeline leaves the arrangement feeling melody-less; not something to promise.

### Open-Ended Instrumental Sections Are Dangerous
Instrumental tags without clear boundaries cause Suno to generate excessive instrumental content:

- `[Guitar Solo]` works if followed by more vocals or `[End]`.
- `[Instrumental section — full prog, complex]` = Suno noodles indefinitely.
- Multiple `[Instrumental break]` tags = the song becomes mostly instrumental.
- **Always put `[End]` hard after the final vocal section or solo** to prevent trailing generation.

## Placement Rules

1. **Global descriptors** at the top of the lyrics — these set the overall tone
2. **Section-specific descriptors** right before the section they apply to — these override/refine the global
3. Section-specific tags are more effective than global tags
4. Don't over-tag — 1-2 descriptors per section maximum, fewer is often better
5. Metatags work best when short: 1-3 words, not full sentences
6. Tags are most impactful in the first 20-30 words and around section changes

## Formatting Rules

- Blank line between every section (including between tag and previous section)
- No style descriptions inside lyrics text (those go in the style prompt)
- No asterisks or markdown formatting in lyrics (exception: `*text*` for inline sound effects — see Asterisk Inline Sound Effects)
- Commas create breath pauses, dashes create connected delivery, ellipses create micro-pauses — use intentionally
- **Exclamation points trigger bark/attack delivery** — avoid in clean sections
- **ALL CAPS sets the loudness ceiling** — save for peak moments only
- **Parentheses signal backing vocals** — not lead melody (but also used for inline performance modifiers like `(breathy)`, `(belt)` — see Inline Performance Modifiers section)
- Consistent line lengths within a section improve phrasing stability
- Line density (short vs long lines) is the primary tempo control mechanism

## Example with Instrumental Sections

```
[Mood: bittersweet]
[Vocal Style: intimate]

[Intro]

[Verse 1]
Walking through the fog of early morning light
Counting all the windows still awake
Every shadow holds a name I used to know
Every corner bends but doesn't break

[Pre-Chorus]
And I keep reaching for the thread
That ties me to some other when

[Chorus]
[Belted]
Come undone, come undone
Let the weight fall where it may

[Interlude]
[Guitar Solo]

[Verse 2]
[Whispered]
Fingerprints on glass that someone cleaned away
Letters folded into paper cranes

[Chorus]
Come undone, come undone
Let the weight fall where it may

[Bridge]
[Energy: stripped back]
Maybe what we lost was just the frame
And the picture's hanging somewhere still

[Final Chorus]
[Energy: building]
[Belted]
Come undone, come undone
Let the weight fall where it may
We were never meant to stay

[Outro]
[Hummed]
We were never meant to stay
[End]
```

## Sources

Where the outside findings came from. Reddit was blocked to the research crawler, so Reddit-attributed items marked from an aggregation arrived secondhand; the primary-source pass (r/SunoAI, 2026-08-14) gathered individual user reports, not controlled tests. Findings marked LOCAL come from this module's own production testing, and nothing external replicates the `[Refrain]` retag or the repeated-vocable rule.

- [Suno Help: How long will my song be?](https://help.suno.com/en/articles/2409473)
- [HookGenius: All Suno Metatags Complete List (2026)](https://hookgenius.app/learn/suno-metatags-complete-list/)
- [HookGenius: The Art of Prompting Suno](https://hookgenius.app/learn/art-of-prompting-suno/)
- [HookGenius: Suno Negative Prompting Guide](https://hookgenius.app/learn/suno-negative-prompting/)
- [HookGenius: Suno v5 Complete Guide](https://hookgenius.app/learn/suno-v5-complete-guide/)
- [HookGenius: Suno Character Limits](https://hookgenius.app/learn/suno-character-limits/)
- [Musci.io: Suno Tags List Complete Guide (2026)](https://musci.io/blog/suno-tags)
- [Suno Wiki: List of Metatags](https://sunoaiwiki.com/resources/2024-05-13-list-of-metatags/)
- [SunoMetaTagCreator: Complete Guide (1000+ tags)](https://sunometatagcreator.com/metatags-guide)
- [OpenMusicPrompt: 500+ Pro Tags & Templates (2026)](https://openmusicprompt.com/blog/suno-ai-metatags-guide)
- [BlakeCrosley: Suno AI Definitive Technical Reference](https://blakecrosley.com/guides/suno)
- [Lilys/Suno Prompting Secrets](https://lilys.ai/notes/en/suno-ai-v5-20251020/suno-prompting-secrets-powerful-metatags)
- [StokeMcToke: Complete Suno AI Meta Tags Guide](https://stokemctoke.com/the-complete-suno-ai-meta-tags-guide/)
- [JackRighteous: Suno AI Meta Tags Guide](https://jackrighteous.com/en-us/pages/suno-ai-meta-tags-guide)
- [CometAPI: How to Instruct Suno v5 with Lyrics](https://www.cometapi.com/how-to-instruct-suno-v5-with-lyrics/)
- [MusicSmith: AI Music Generation Prompts Best Practices](https://musicsmith.ai/blog/ai-music-generation-prompts-best-practices)
- [howtopromptsuno.com: Voice Tags Guide](https://howtopromptsuno.com/making-music/voice-tags)
- [Plain English: 10 Suno v5 Prompt Patterns That Never Miss](https://plainenglish.io/blog/i-made-10-suno-v5-prompt-patterns-that-never-miss)
- [HookGenius: Suno v5.5 Guide — Voices, Custom Models & My Taste](https://hookgenius.app/learn/suno-v5-5-guide/)
- [HookGenius: 300+ Suno Style Tags That Actually Work (2026)](https://hookgenius.app/learn/suno-style-tags-guide/)
- [HookGenius: Suno Prompts Complete Guide](https://hookgenius.app/learn/suno-prompts-complete-guide/)
- [Suno API Docs: Character Limits by Model (sunoapi.org)](https://docs.sunoapi.org/suno-api/generate-music)
- [iFlow.bot: Suno v5 Secrets](https://iflow.bot/suno-v5-secrets-crafting-ai-generated-songs/)
- [HookGenius: Suno Vocal Effects — Harmonies, Layers & More](https://hookgenius.app/learn/suno-vocal-effects/)
- [Jack Righteous: Add Sound Effects Using Asterisks](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-sound-effects-asterisks)
- [Jack Righteous: Mastering Suno V5 Meta Tags — 2nd Edition](https://jackrighteous.com/en-us/blogs/jack-righteous-updates/mastering-suno-v5-meta-tags-2nd-edition-update-how-to-use)
- [James 99/Medium: Ultimate Guide to Suno AI Metatags](https://james-palm.medium.com/stop-wasting-your-credits-the-ultimate-guide-to-suno-ai-metatags-verse-chorus-and-drop-57e209a0e5d8)
