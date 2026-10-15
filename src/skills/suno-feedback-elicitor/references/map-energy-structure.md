# Map: Energy, Tempo and Structure

The dynamic arc, energy, tempo and feel, sections, intros and endings, and lyric-side metatags. Lyric changes go to the Lyric Transformer as an adjustment spec; it holds the full metatag catalog. Grades: COMMUNITY is several users, ANECDOTAL one report, LOCAL this module's own renders.

## Dynamic arc

The style prompt has to describe the whole arc; build-only language gets a song that never comes down.

| Feedback | Prompt problem | Fix |
|---|---|---|
| "Too loud at the end" / "doesn't come back down" | "crescendo dynamics", "build to crushing climax" | "dynamic shifts loud to quiet" or "slow build then fade" |
| "Ending stays loud despite descent language" | Descent stated once — Suno latches onto the loudest directive | State the arc twice: `building from gentle to crushing then returning to gentle` and `dynamic arc quiet to massive to quiet` |
| "All one energy level" | No dynamic language | "dynamic shifts", "quiet verses explosive chorus" |
| "The chorus went slow and dramatic" / "it turned into a ballad" (rock, metal) | Feeling words as the chorus instruction: "big", "emotional", "epic" read as "slow down and make it dramatic" (COMMUNITY) | Write the chorus's job: *choruses stay rhythmically driving and hit harder than the verses*; any "tempo drop" goes in Exclude Styles. A mood tag on a section meant to be bare may read as intensity (n=1): describe its job, harmony or arrangement instead |

## Tempo and feel

Suno holds one tempo per song. "Tempo changes" in a style prompt produce arrangement-density variation (pullback for a half-time feel, compression for double-time), not a BPM change. Bare BPM tags in the lyrics had no detectable effect across 31 measured songs (LOCAL), so don't recommend them; one stated BPM in the style field, paired with feel words, is soft reinforcement at most. Judge a tempo complaint against the felt tempo and the genre, not a raw measurement.

Perceived-tempo levers, lyrics first:

1. **Word and line density** (the most reliable): short fragmented lines (1–3 words) feel slower; long packed lines feel faster. More line breaks are more breath points.
2. **Half-time / double-time feel:** `[Heavy: halftime]`, `[Double Time]`, `[Chorus | Half-Time]` in the lyrics; "halftime groove", "double-time driving", "shuffle", "breakbeat" in the style prompt lock feel better than "slow" or "fast".
3. **Density:** `[Energy: stripped, minimal]` feels slower; `[Energy: massive]` feels faster.

**"The tempo changes didn't happen" (v6):** carry the contrast as feel over one pulse (half-time / double-time / standard-time, sparse versus dense), naming each section's scene in identical words in the style prompt and the lyric cue. Possible, not reliable (LOCAL-OBSERVED). For a true change: Replace Section on that span with a short style prompt describing only it at its new tempo, Extend from the boundary with a new style, or splice.

## Energy table

| Feedback | Add to style prompt | Slider |
|---|---|---|
| "Too fast" | "halftime groove, laid-back, relaxed groove"; restructure the lyrics (short lines, more breaks) | — |
| "Too slow" | "double-time driving, driving rhythm, energetic pace"; pack more syllables per line | — |
| "Not energetic enough" | "high energy, powerful, dynamic, driving" | Style Influence ↓ |
| "Too intense" | "gentle, soft, understated, subtle" | — |
| "Energy is flat" | "building energy, dynamic shifts" | Weirdness ↑ slightly |
| "Feels monotonous" | "dynamic arrangement, shifting textures, varied sections" | Weirdness ↑ |

## Sections

Parameterized section tags fix one section without touching the global prompt, and often work better than a global change when the issue is section-specific: `[Verse: whispered vocals, acoustic guitar only]`, `[Chorus: full band, powerful vocals, high energy]`, `[Bridge: stripped back, piano only]`, `[Verse: stripped back, minimal arrangement]`. Structural or section directions buried in a long style prompt are largely ignored; sections live in the lyrics.

| Feedback | Lyric adjustment |
|---|---|
| "Chorus doesn't hit hard enough" | `[Energy: High]` before it; a `[Build-Up]` section ahead of it |
| "Verse feels wrong" / "phrasing unnatural" | Even out syllable counts and line lengths within the section; a `[Mood: ...]` descriptor |
| "Structure feels off" | Reorder sections; add or remove a Pre-Chorus or Bridge |
| "Vocals change style mid-song" / "style changed mid-song" | Consistent `[Vocal Style: ...]`, `[Mood: ...]`, `[Energy: ...]` tags before each section |
| "Middle section drags" | `[Energy: building]` tags; shorten the section; a `[Breakdown]` or `[Build-Up]` for variety |
| "Instrumental section too long / short" | Adjust `[Intro]`, `[Breakdown]` or `[Outro]` placement and content |
| "Song loops" / "too much instrumental filler" | Short lyrics (under ~15 lines) cause looping and filler: repeat verses with variation, repeat the chorus, or place a hard `[End]` |
| "It changed key out of nowhere" | v6 is reported to add unrequested modulations in some genres and to ignore an inline "no key changes" (ANECDOTAL, n=1): try `key change` in Exclude Styles where the song must hold its key (untested); leave a welcome modulation alone |

## Edges: intro and ending (next generation)

| Feedback | Fix |
|---|---|
| "Humming / ad-libs at the start" | State the intro in positive terms with a bar count ("4-bar guitar intro, instrumental only"); `humming, vocal intro` in Exclude Styles, never "no humming" in the style field |
| "Intro goes on too long" | Shorten or remove `[Intro]` content and start `[Verse 1]` earlier (`[Intro]` is notoriously unreliable) |
| "It vamps forever" / "it cut off mid-line" | State the ending and its length; land the lyric on `[Instrumental Outro]` `[Hard Stop]` `[End]` |
| "Outro cuts off abruptly" | An explicit `[Outro]` of 2–4 lines |

Ending tags, by community consensus: `[Outro]` and `[End]` paired, `[End]` on the absolute last line with nothing beneath it, `[Fade Out]` never alone. Expect to crop: it is the only deterministic ending. Repairing an ending on a take that already exists is a technical path (crop, fade, extend).
