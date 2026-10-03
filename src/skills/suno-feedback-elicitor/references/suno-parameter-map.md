# Suno Parameter Map

> **Related references:** For the complete delivery metatag catalog, section tag behavior, and experimental tags, see the suno-lyric-transformer skill's `references/metatag-reference.md`. For section emotional roles and poem-to-song structure decisions, see the suno-lyric-transformer skill's `references/section-jobs.md`.
>
> **Critical zone:** The first ~200 characters of a style prompt carry disproportionate influence on generation. When recommending additions, prioritize the most impactful descriptors for the critical zone. Supplementary descriptors go after. The style prompt limit is 1,000 characters (200 on the retired v4 Pro) and exclusions aim for ~200 — community-attested figures, not officially documented by Suno; `scripts/map-adjustments.py` and the suno-style-prompt-builder skill's `scripts/validate-prompt.py` enforce them.
>
> **Last validated:** August 13, 2026 against v5.5, v5, and v4.5-all — models that can no longer generate since the v6 family launched (2026-09-09). Re-check model-specific advice on v6 before relying on it.
>
> **Elsewhere in this skill:** v6 controls, Voices/Custom Models and per-model patterns are in `references/model-controls.md`; artifacts, editor/Studio paths, length and genre drift are in `references/technical-resolution.md`.

Maps feedback dimensions and emotional vocabulary to concrete Suno parameter adjustments.

## Style Prompt Mechanics

### Genre Keyword Ordering

Front-loaded terms in the style prompt dominate generation output — the first ~200 characters are the critical zone. When feedback suggests a genre element is too dominant, move that keyword later in the prompt rather than removing it. For secondary influences, use softening formulations like "with [genre] accents" or "[genre] undertones" to reduce their weight without eliminating them.

### Dynamic Arc Mismatch

When the user reports that the ending or energy arc doesn't match their intent, the style prompt likely contains unidirectional language that only describes one direction of movement. The style prompt must describe the full arc.

| Feedback Pattern | Style Prompt Problem | Fix |
|-----------------|---------------------|-----|
| "Too loud at the end" | "crescendo dynamics" or similar build-only language | Replace with "dynamic shifts loud to quiet" |
| "Builds but doesn't resolve" | "build to climax" with no release language | Replace with "slow build then fade" |
| "Ending stays loud despite descent language" | Dynamic descent stated only once | A single mention of descent isn't enough — Suno latches onto the loudest directive. State the arc TWICE: both `building from gentle to crushing then returning to gentle` AND `dynamic arc quiet to massive to quiet` |
| "All one energy level" | No dynamic language at all | Add explicit dynamic descriptors: "dynamic shifts", "quiet verses explosive chorus", etc. |

### Perceived Tempo Control (BPM Tags Are Ineffective)

**Suno does NOT actually shift tempo within a song.** "Tempo changes" or "tempo shifts" in style prompts produce *arrangement-density variation* (instrumentation pullback for halftime feel, compression for double-time feel), not actual BPM change. Underlying tempo stays constant; the felt-shift is dynamic/arrangement-driven. Asking for tempo journey in the style prompt is not a path to actual BPM movement — direct the perceived tempo through lyric density and rhythm-noun metatags instead.

**BPM tags in lyrics have ZERO detectable effect on Suno's actual output** — confirmed by librosa analysis across 31 songs. Suno picks a single steady tempo per song regardless of any BPM tags. Do not recommend BPM tags in lyrics as a solution for tempo issues.

**v5 alternative:** BPM and key specified in the style prompt (not lyrics) may be more effective in v5: e.g., `"deep house, 122 BPM, A minor, hypnotic groove"`. This is not confirmed as reliable but is worth trying when perceived tempo techniques alone are insufficient.

**"Felt BPM" vs. measured BPM:** When users report tempo issues, their perception reflects felt BPM (human-perceived tempo), not what librosa measures. librosa has genre-specific biases: reads half-time on speed metal (~50% of actual), double-time on doom/sludge (~200% of actual). ~19% of tracks have significant misreads. Always interpret tempo feedback against felt BPM and genre context, not raw librosa numbers.

When the user reports tempo issues, the recommended adjustment path uses perceived tempo techniques:

1. **Word/line density (PRIMARY):** Restructure lyrics — short fragmented lines (1-3 words) for slower perceived delivery, long packed lines with many syllables for faster perceived delivery. This is the most reliable single technique.
2. **Half-time / double-time drum feel:** Add rhythm noun metatags like `[Heavy: halftime]` or `[Double Time]` in the lyrics. Creates perception of halved or doubled tempo without actual BPM change.
3. **Instrumental density / arrangement dropout:** Use `[Energy: stripped, minimal]` to create space that feels slower. Use `[Energy: massive]` for density that feels faster.
4. **Line breaks as breath points:** More line breaks = more pauses = slower perceived delivery. Fewer breaks = longer phrases = faster feel.
5. **Rhythm nouns in style prompt:** "Halftime groove," "double-time driving," "shuffle," "breakbeat" lock feel better than "slow," "fast," or "upbeat."

Try restructuring the lyrics first (techniques 1 and 4) before modifying the style prompt or metatags.

## Descriptor Families as Adjustment Targets

Beyond `[Mood: ...]`, `[Energy: ...]`, `[Vocal Style: ...]`, and `[Instrument: ...]`, these additional descriptor families are available as adjustment targets in the lyrics field:

| Descriptor Family | Examples | Use When Feedback Says |
|-------------------|---------|----------------------|
| `[Atmosphere: ...]` | `[Atmosphere: Dreamy]`, `[Atmosphere: Cyberpunk]`, `[Atmosphere: Medieval]` | "The vibe/setting feels wrong", "needs more atmosphere" |
| `[Texture: ...]` | `[Texture: Grainy]`, `[Texture: Velvet]` | "The sound quality/feel is wrong", "too smooth/rough" |
| `[Effect: ...]` | `[Effect: Lo-fi]`, `[Effect: Reverb: Hall]`, `[Effect: Delay: Ping-pong]`, `[Effect: Distortion]`, `[Effect: Sidechain]`, `[Effect: Radio Filter]` | "Too much/little reverb", "needs effects", "too dry/wet" |

These families provide more targeted control than style prompt descriptors alone. Place them before the section they should affect.

## Parameterized Section Tags

Section tags can include per-section arrangement instructions using colon (`:`) or pipe (`|`) syntax. This enables per-section fixes without changing the overall style prompt.

```
[Verse: whispered vocals, acoustic guitar only]
[Chorus: full band, powerful vocals]
[Bridge: stripped back, piano only]
[Chorus | Half-Time]
[Chorus | Double-Time]
```

| Feedback | Parameterized Section Tag Fix |
|----------|-------------------------------|
| "The verse is too loud/busy" | `[Verse: stripped back, minimal arrangement]` |
| "The chorus doesn't hit hard enough" | `[Chorus: full band, powerful vocals, high energy]` |
| "The bridge needs a different feel" | `[Bridge: acoustic guitar only, intimate]` |
| "The chorus tempo feels wrong" | `[Chorus | Half-Time]` or `[Chorus | Double-Time]` |

This is often more effective than global style prompt changes when the issue is section-specific.

## Inline Performance Modifiers

Parenthetical cues placed after lyric lines control vocal delivery on a per-line basis. Distinct from the backing-vocal parentheses technique — these are performance directions.

```
I can't stop thinking about you (breathy)
HOLD ON (belt)
wait for me... (breath)
stay with me (hold)
```

| Feedback | Inline Modifier |
|----------|----------------|
| "Vocals too forceful on this line" | Add `(breathy)` or `(soft)` after the line |
| "This line needs more power" | Add `(belt)` after the line |
| "Needs a pause/breath feel here" | Add `(breath)` after the line |
| "The note should sustain longer" | Add `(hold)` after the line |

Use sparingly — these are line-level adjustments, not section-level.

## Confirmed Descriptor Effects

These style prompt descriptors have confirmed, predictable effects on Suno output:

| Descriptor | Produces |
|-----------|----------|
| "atmospheric" | Reverb, space, ambient pads |
| "airy" | Reverb/space on vocals |
| "lo-fi warmth" | Vintage character, low-pass filtering |
| "polished radio-ready" | Clean, modern, commercial mix |
| "unpolished room sound" / "natural room ambience" | Less processed, room sound. **Do not use the word "live"** in any form — `live recording`, `live-band drums`, `live energy` all pull crowd/audience noise on v5.5 (LOCAL-CONFIRMED, recurring) |
| "driving" | Forward momentum, energetic basslines |
| "lush" | Layered pads, dense production |
| "punchy" | Low-end presence, tight transients |
| "wide stereo" | Spatial separation |
| "gated drums" | 80s-style drum processing |
| "vintage Rhodes" | More specific/effective than "piano" |

Use these as precise adjustment tools when feedback maps to one of these effects.

## Three-Pass Layered Prompting

For complex adjustments that touch multiple dimensions (arrangement, lyrics, and delivery), use a three-pass approach rather than trying to fix everything at once:

1. **Idea pass** — adjust the concept, mood, and genre in the style prompt
2. **Lyric pass** — revise lyrics with structural tags, section tags, and arrangement cues
3. **Performance pass** — add vocal delivery cues (inline modifiers), energy tags, and dynamics metatags

This reduces the chance of conflicting instructions and makes it easier to isolate which change fixed (or broke) something.

## Style Prompt Adjustment Patterns

### Instrumentation & Arrangement

| Feedback | Add to Style Prompt | Add to Exclusions |
|----------|--------------------|--------------------|
| "Too busy/cluttered" | "minimal arrangement, sparse instrumentation" | "no dense layering, no wall of sound" |
| "Too empty/thin" | "lush arrangement, layered instrumentation, full sound" | — |
| "Guitar too loud" | "subtle guitar, background guitar" | "no guitar solo, no heavy guitar" |
| "Needs more guitar" | "prominent guitar, guitar-driven" | — |
| "Too electronic" | "organic, acoustic, live instruments" | "no synthesizer, no electronic beats" |
| "Too acoustic" | "electronic elements, synth textures, modern production" | — |
| "Drums overpower" | "soft percussion, gentle drums, restrained beat" | "no heavy drums, no pounding drums" |
| "Needs more drums" | "driving drums, prominent beat, rhythmic" | — |
| "Second line drums sound like hip-hop" | "second line drums" only produces NOLA parade groove when the surrounding context is up-tempo + energetic + celebratory. Without that context, Suno defaults to hip-hop patterns. Add "New Orleans parade", "celebratory", "up-tempo" to the style prompt. | — |
| "Piano feels wrong" | — | "no piano" (or specify: "no classical piano") |
| "Bass too heavy" | "light bass, subtle low end" | "no heavy bass, no bass drops" |

**Keyword Triggers to Avoid**

Certain style prompt keywords reliably trigger unwanted arrangement choices. When the user reports theatrical, keyboard-heavy, or orchestral results they didn't want, check for these first.

| Keyword | What Suno Produces | Alternative Approach |
|---------|--------------------|---------------------|
| "baroque" | Disney/theatrical arrangements | Describe desired qualities directly; specify instruments by name |
| "rock opera" | Keyboard-heavy, theatrical arrangements | Use "power ballad" for dynamic range without keyboards |
| "cinematic" | Orchestral/soundtrack feel | Specify desired instruments by name (cello, heavy strings, kettle drums) |
| "orchestral" | Light strings/flutes, not the heavy orchestral sound users typically intend | Name the specific orchestral instruments desired (cello, heavy strings, kettle drums) |

### Vocal Direction

| Feedback | Add to Style Prompt | Add to Exclusions |
|----------|--------------------|--------------------|
| "Vocals too polished" | "raw vocal, imperfect delivery, organic phrasing" | "no perfect pitch, no overproduced vocals" |
| "Vocals too rough" | "polished vocal, smooth delivery, clean singing" | "no raspy vocals, no rough vocals" |
| "Voice doesn't match" | Specify: "male/female voice, [age] years old, [tone] delivery" | Exclude the unwanted: "no [gender] vocals" |
| "Too much vibrato" | "steady vocal, straight tone" | "no heavy vibrato" |
| "Vocals too quiet" | "prominent vocals, voice-forward mix" | — |
| "Vocals too loud" | "balanced mix, instrument-forward" | — |
| "Singing sounds robotic" | "natural phrasing, breathy, human vocal" | "no robotic vocals" |
| "Want harmonies" | "vocal harmonies, layered vocals, backing harmonies" | — |
| "Too much harmony" | "solo vocal, single voice, unison" | "no harmonies, no backing vocals" |

### Energy & Tempo

| Feedback | Add to Style Prompt | Slider Adjustment |
|----------|--------------------|--------------------|
| "Too fast" | "halftime groove, laid-back, relaxed groove" (also restructure lyrics: short fragmented lines, more line breaks — see Perceived Tempo Control above). Do NOT add BPM tags — they have no effect. | — |
| "Too slow" | "double-time driving, driving rhythm, energetic pace" (also restructure lyrics: pack more syllables per line, fewer line breaks — see Perceived Tempo Control above). Do NOT add BPM tags — they have no effect. | — |
| "Not energetic enough" | "high energy, powerful, dynamic, driving" | Style Influence ↓ (loosen) |
| "Too intense" | "gentle, soft, understated, subtle" | — |
| "Energy is flat" | "building energy, dynamic shifts, crescendo" | Weirdness ↑ slightly |
| "Feels monotonous" | "dynamic arrangement, shifting textures, varied sections" | Weirdness ↑ |

### Production & Mix

| Feedback | Add to Style Prompt | Slider Adjustment |
|----------|--------------------|--------------------|
| "Too polished" | "lo-fi, raw production, analog warmth, rough edges" | Weirdness ↑ |
| "Too rough/lo-fi" | "radio-ready mix, clean production, crisp, polished" (v5 responds well to production-quality descriptors like "punchy drums, wide stereo field, crisp high-end, warm bass") | Weirdness ↓ |
| "Sounds compressed" | "dynamic range, open mix, breathing room" | — |
| "Too much reverb" | "dry mix, close mic, intimate" | — |
| "Too dry" | "spacious, reverb, ambient, atmospheric" | — |
| "Stereo feels narrow" | "wide stereo field, panoramic, expansive" | — |
| "Sounds dated" | "modern production, contemporary sound, current" | — |

### Mood & Vibe

| Feedback | Add to Style Prompt | Slider Adjustment |
|----------|--------------------|--------------------|
| "Too happy/upbeat" | "melancholic, bittersweet, minor key, moody" | — |
| "Too dark/sad" | "uplifting, bright, major key, hopeful" | — |
| "Too generic" | "distinctive, unique, unconventional" | Weirdness ↑ (65-80) |
| "Too weird" | "familiar, classic, conventional, straightforward" | Weirdness ↓ (25-35) |
| "Not emotional enough" | "emotional, yearning, deeply felt, passionate" | Style Influence ↑ |
| "Too dramatic" | "understated, subtle, restrained, casual" | — |

**v6 caution on feeling words (2026-10-03):** "big", "emotional" and "epic" as a heavy chorus's instruction are reported to slow it into a ballad (COMMUNITY). A mood tag on a section meant to be bare may be read as intensity (n=1, a thing to try). For those cases, describe the section's job, harmony or arrangement instead of its feeling. See the suno-style-prompt-builder skill's `references/model-prompt-strategies.md` → "v6 prompt guidelines".

## Confirmed Suno Behavior

- "NOLA funk swing" lands as syncopation not true swing; "Odd time signatures" consistently ignored in 4/4 rock/metal context
- Suno adds unscripted guitar solos regularly
- Structural/section directions in long style prompts are largely ignored (style prompt sets overall mood, metatags handle sections imperfectly)

## Exclusion Guidance

Prioritize 2-3 specific exclusions over filling the space. Supported syntax: 'no [element]', 'without [element]', 'exclude [element]', 'avoid [element]'. The Exclude Styles field (Pro/Premier only) and in-prompt negatives both function as **probability reduction, not hard bans** — excluded elements may still appear, and regeneration may be needed. Limit to 2-3 most important exclusions; too many destabilizes the arrangement and reduces overall effectiveness.

## Slider Adjustment Guide

**Goal-based starting points (ANECDOTAL, single source, updated 2026-08):** a set of goal-keyed slider recipes — clean/predictable, strong genre, stable hook with variation, adventurous bridge, uploaded-melody-leads, upload-as-loose-inspiration — is documented in the suno-style-prompt-builder skill's `references/model-prompt-strategies.md` → "Goal-Based Slider Recipes." They don't contradict the production-tested tables below; use them when the user's goal isn't one this file names, especially for uploaded-audio cases. Where they differ from our tables, ours win — ours are measured on this catalog.

**Style Influence and Audio Influence compete — never both at 100** (COMMUNITY). If a user has pushed both high and reports incoherent output, that combination is the first thing to unwind: sample-primary work sits around AI 60-70 / SI 30-40, tags-primary around AI 30-40 / SI 60-70.

### Weirdness (0-100, default 50) — Paid tiers only

| Current Feel | Direction | Target Range | Reasoning |
|-------------|-----------|-------------|-----------|
| Too generic/predictable | ↑ Increase | 60-80 | More unexpected choices |
| Too strange/unfocused | ↓ Decrease | 25-40 | More conventional, familiar |
| Good but could explore | ↑ Slight increase | +10-15 from current | Nudge toward discovery |

**Observations from live testing (not exhaustive — wider range testing needed):**
- Weirdness 50 (default) produced overly steady/predictable results for multi-tempo songs (note: actual BPM does not change — Weirdness affects rhythmic feel and arrangement variation, not tempo)
- Weirdness 60 improved rhythmic variation
- Weirdness 65 produced the best tempo/rhythm variation in testing so far
- Higher values (70+) have not been tested and may produce interesting results for experimental work
- These observations are from v5 Pro with Style Influence 70 — results may differ on other models
- **Sliders don't control tempo, dynamics, or vocal delivery** — they control predictability (Weirdness) and prompt adherence (Style Influence). Don't recommend them as solutions for tempo/vocal issues.

**Confirmed slider combinations by song type (from production use):**

| Song Type | Weirdness | Style Influence | Notes |
|-----------|-----------|-----------------|-------|
| Structured songs (chorus, clear sections) | 50-55 | 75-80 | Higher SI keeps sections well-defined |
| Through-composed with tempo shifts | 55-60 | 70-75 | Slightly looser to allow tempo variation |
| Funk-forward | 60 | 65-70 | Funk needs room to breathe |
| Post-metal / atmospheric | 60-65 | 65 | Balanced exploration with genre grounding |
| Prog with odd time signatures | 65-75 | 65 | High Weirdness helps with non-standard meters |
| Circular / agitated | 75 | 65 | Near the structural ceiling — use [End] tags |
| Acoustic tracks | 40 | 80 | Audio Influence 25%. Persona safe at full AI when style prompt clearly defines non-heavy genre |
| Bass prominence attempts | Any | High SI (85) did not force bass prominence; low Audio Influence (15%) slightly shifted era feel instead | Bass-forward rock/metal remains a Suno limitation |

**Upper limit findings (from live testing):**
- Weirdness 75 is the practical ceiling for structured songs — still experimental but respects section boundaries and [End] tags
- Weirdness 85 causes structural breakdown: [End] tags ignored, songs continue past lyrics with instrumental/gibberish meandering
- At Weirdness 85, coherence loss increases in longer songs — shorter songs or songs with strong repeating structure (chorus anchors) survive higher Weirdness better
- **Recommendation:** Cap at 75 for songs needing structural compliance. Reserve 80+ for jam/experimental mode only. Community reports put the danger zone as low as 78.
- Use the [Fade Out] + [End] combo at high Weirdness values — reported as a more reliable stop signal than [End] alone, though primary-source users report [Fade Out] working in no configuration at all. Expect to crop; that is the only deterministic ending (see the ending-repair tree under "Song Length & Pacing" in `references/technical-resolution.md`)

### Audio Influence (0-100%, default 25%) — Persona-dependent

Audio Influence controls how much the loaded Persona's source audio shapes the generation. This parameter should never be omitted from song packages when a Persona is active.

| Scenario | Recommended Range | Notes |
|----------|-------------------|-------|
| Standard tracks | 25% | Default. Reliable baseline for most genres. |
| Acoustic tracks | 25% | Persona is safe at full Audio Influence when style prompt clearly defines a non-heavy genre. |
| Genre-pushing tracks | 20% | Drop 5% when pushing outside the Persona's native genre to give the style prompt more room. |
| Era mismatch (song sounds too modern/dated) | 10-15% | High Audio Influence anchors to the Persona's era. Reduce to let style prompt control era feel. |

**Effective range is 15-25%.** Above 25% shows diminishing returns — the generation doesn't become noticeably more Persona-like, but style prompt influence decreases. Below 15%, the Persona contributes minimal character.

### Style Influence (0-100, default ~50-60) — Paid tiers only

| Current Feel | Direction | Target Range | Reasoning |
|-------------|-----------|-------------|-----------|
| Doesn't match the prompt | ↑ Increase | 65-80 | Tighter adherence to style prompt |
| Too literal/constrained | ↓ Decrease | 25-40 | More creative interpretation |
| Prompt is vague, output is scattered | ↑ Increase + rewrite prompt | 60-70 | Better prompt + tighter adherence |

**Observations from live testing:**
- On v6, Style Influence 100 tested no better than 85: 6 of 12 vs 7 of 12 takes followed the instruction (ANECDOTAL-controlled, one outside channel, 2026-10-03). So there's little to gain from pushing past the 80s
- Style Influence 70 gave enough room for metal weight while staying in the genre lane
- Lower values (45-65) allowed more creative interpretation on bridges and contrasting sections
- These are observations from limited testing, not definitive optimal values

### Per-Section Slider Strategy (Replace Section at Pro; Studio at Premier)

Per-section regeneration is available through the Song Editor's Replace Section (Pro and Premier) and inside Studio (Premier only). Different slider values can be applied to different song sections:

| Section Type | Weirdness | Style Influence | Reasoning |
|-------------|-----------|-----------------|-----------|
| Verse | 35-50 | 55-70 | Stable foundation, moderate adherence |
| Chorus/Hook | 25-40 | 70-85 | Tighter adherence for memorable hooks |
| Bridge | 55-70 | 45-65 | More exploration for contrast |
| Intro/Outro | 40-60 | 50-65 | Balanced — sets/closes the tone |
| Breakdown | 60-80 | 35-55 | Looser interpretation for texture |

## Lyric-to-Metatag Feedback Patterns

| Feedback | Lyric Adjustment |
|----------|-----------------|
| "Chorus doesn't hit hard enough" | Add `[Energy: High]` before chorus, consider `[Build-Up]` section before it |
| "Verse feels wrong" | Check syllable count consistency, add `[Mood: ...]` descriptor |
| "Song structure feels off" | Review section ordering, consider adding/removing Pre-Chorus or Bridge |
| "Vocals change style mid-song" | Add consistent `[Vocal Style: ...]` tags before each section |
| "Instrumental section too long/short" | Adjust `[Intro]`, `[Breakdown]`, or `[Outro]` tag placement and content |
| "Phrasing feels unnatural" | Run syllable counter, normalize line lengths within sections |
