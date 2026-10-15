# Map: Production, Mix and Mood

Production character, mix space, era, and mood or vibe. The opposing-pairs table in the triage guide carries the core descriptor mappings (atmospheric, punchy, lush, lo-fi warmth and the rest); this file adds the rows it doesn't.

## Production and mix

| Feedback | Add to style prompt | Slider |
|---|---|---|
| "Too polished" | "lo-fi, raw production, analog warmth, rough edges" | Weirdness ↑ |
| "Too rough / lo-fi" | "radio-ready mix, clean production, crisp, polished"; production-quality words such as "punchy drums, wide stereo field, crisp high-end, warm bass" | Weirdness ↓ |
| "Sounds compressed" | "dynamic range, open mix, breathing room" | — |
| "Too much reverb" | "dry mix, close mic, intimate" | — |
| "Too dry" | "spacious, reverb, ambient, atmospheric" | — |
| "Stereo feels narrow" | "wide stereo field, panoramic, expansive" | — |
| "Sounds dated" | "modern production, contemporary sound" | — |

More descriptors with predictable effects: "airy" puts reverb and space on the vocals; "gated drums" gives 80s drum processing; "vintage Rhodes" is more specific and effective than "piano".

## Descriptor families in the lyrics

Placed before the section they should affect, these give more targeted control than style-prompt words: `[Atmosphere: Dreamy]` (the vibe or setting feels wrong), `[Texture: Grainy]` / `[Texture: Velvet]` (too smooth or too rough), `[Effect: Lo-fi]`, `[Effect: Reverb: Hall]`, `[Effect: Delay: Ping-pong]`, `[Effect: Distortion]`, `[Effect: Radio Filter]` (too dry, too wet, needs an effect).

## Mood and vibe

| Feedback | Add to style prompt | Slider |
|---|---|---|
| "Too happy / upbeat" | "melancholic, bittersweet, minor key, moody" | — |
| "Too dark / sad" | "uplifting, bright, major key, hopeful" | — |
| "Too generic" | "distinctive, unique, unconventional" | Weirdness ↑ (65–80) |
| "Too weird" | "familiar, classic, conventional, straightforward" | Weirdness ↓ (25–35) |
| "Not emotional enough" | "emotional, yearning, deeply felt, passionate" | Style Influence ↑ |
| "Too dramatic" | "understated, subtle, restrained, casual" | — |
| "Too modern / wrong era" with a Persona loaded | Personas anchor the sound to their source song's era | Audio Influence 10–15%, or generate without the Persona |
| "A genre element is too dominant" / "genre fusion went wrong" | Front-loaded terms dominate; the first ~200 characters are the critical zone | Move that keyword later rather than removing it, softened as "with [genre] accents" or "[genre] undertones"; for a fusion gone wrong, one dominant genre first |
