# Map: Controls, Sliders and Exclude Styles

Many v6 complaints trace to a control, not to wording, so check these before rewording. The v6 rows are launch-period guidance from Suno's docs, vendor tests and community reports, mostly unconfirmed by this module's production testing. Grades: COMMUNITY is several users, ANECDOTAL one report, LOCAL this module's own renders.

## v6 controls

| Feedback | First check | Then |
|---|---|---|
| "It changed my style prompt" / "it keeps adding things I removed" / "the song page says X but it doesn't sound like X" | **Variety** above *Exact style* rewrites the style prompt before generating (OFFICIAL); prohibitions and vague voice words drop out, while Exclude Styles came through unchanged in 155 of 156 pairs (ANECDOTAL-controlled). The song page shows the input or the rewrite, not what landed: trust the audio and the user's ear over the displayed text | Variety to *Exact style*, regenerate, and keep negatives in Exclude Styles |
| "The prompt is being ignored" / "it came out generic" | **Style Influence** reportedly defaults to 50 (VENDOR ×2) | Raise to ~80–90 with Variety at *Exact*. Community obedience settings: Variety 0 · Weirdness ~20–50 · Style Influence 80–95 |
| "It sounds like someone else's taste" | **Personalize** on | Turn it off |
| "Great start, falls apart by the end" | Song length and **Max Mode** | Max Mode is applied at generation (2× credits), so a finished take can't be upgraded; this module's v6 tests found it the difference between usable and unusable takes, but many users say it doesn't cure late-song degradation — keep it on for adherence. Late-song repairs are a technical path |
| "The two takes are nothing alike" | Normal on v6: take-to-take spread can exceed a prompt edit's effect (VENDOR; ANECDOTAL-controlled) | Judge both takes before changing anything, and change one control per generation. For a one-change test suggest about 4 takes (two Creates) per variant, since the ranking flipped between 2 and 4 takes in one measured series. How many to run is the user's call |

## Sliders (Pro and Premier)

Sliders control predictability (Weirdness) and prompt adherence (Style Influence), not tempo, dynamics or vocal delivery; don't offer them as fixes for those. The builder holds goal-keyed slider recipes and applies them when it rebuilds; where they differ from these tables, these win, because these are measured on this catalog.

**Weirdness (0–100, default 50):**

| Current feel | Direction | Target |
|---|---|---|
| Too generic / predictable | ↑ | 60–80 |
| Too strange / unfocused | ↓ | 25–40 |
| Good but could explore | slight ↑ | +10–15 from current |

- **Ceiling:** 75 is the practical ceiling for songs that must keep their structure. At 85 the structure breaks down: `[End]` is ignored and songs run past the lyrics into instrumental or gibberish meandering, worst in longer songs (shorter songs or strong repeating choruses survive higher). Community reports put the danger zone as low as 78. Reserve 80+ for jam or experimental work, and pair high values with `[Fade Out]` + `[End]` (reported as a better stop signal than `[End]` alone, though some users report `[Fade Out]` working in no configuration) and expect to crop.
- Weirdness 60–65 gave more rhythmic and arrangement variation than 50 on multi-tempo songs (the BPM itself doesn't change; observed on a retired model, untested on v6).

**Style Influence (0–100, defaults to ~50):**

| Current feel | Direction | Target |
|---|---|---|
| Doesn't match the prompt | ↑ | 65–80 |
| Too literal / constrained | ↓ | 25–40 |
| Prompt vague, output scattered | ↑ and rewrite the prompt | 60–70 |

It plateaus in the 80s: 100 did no better than 85 on v6 (ANECDOTAL-controlled). 70 gave metal weight while staying in the genre lane; 45–65 allowed more interpretation on bridges and contrasting sections.

**Production-tested combinations:**

| Song type | Weirdness | Style Influence | Notes |
|---|---|---|---|
| Structured (chorus, clear sections) | 50–55 | 75–80 | Higher SI keeps sections defined |
| Through-composed with feel shifts | 55–60 | 70–75 | Looser for variation |
| Funk-forward | 60 | 65–70 | Funk needs room |
| Post-metal / atmospheric | 60–65 | 65 | Exploration with genre grounding |
| Prog with odd meters | 65–75 | 65 | Higher Weirdness helps non-standard meters |
| Circular / agitated | 75 | 65 | At the ceiling: use `[End]` tags |
| Acoustic | 40 | 80 | Audio Influence 25% |

**Per section** (Replace Section at Pro and Premier; Studio at Premier only): Verse W 35–50 / SI 55–70 · Chorus W 25–40 / SI 70–85 · Bridge W 55–70 / SI 45–65 · Intro/Outro W 40–60 / SI 50–65 · Breakdown W 60–80 / SI 35–55.

**Audio Influence with a Persona (default 25%):** effective range 15–25%; above 25% the take gets no more Persona-like while the prompt loses influence, and below 15% the Persona adds little. Standard and acoustic tracks 25% (a Persona is safe at full Audio Influence when the prompt clearly defines a non-heavy genre); genre-pushing tracks 20%; era mismatch 10–15%. Never omit it from a package with a Persona. A Voice runs much higher (start around 50%).

**Style Influence and Audio Influence compete** (COMMUNITY): never both at 100. If both are high and the output is incoherent, unwind that first: sample-primary work sits around AI 60–70 / SI 30–40, tags-primary around AI 30–40 / SI 60–70.

## Exclude Styles (Pro and Premier)

Prioritize 2–3 specific items over filling the field; too many destabilize the arrangement. Excludes reduce probability rather than ban, so an excluded element may still appear and regeneration may be needed. On Free there is no field: carry the intent as positive phrasing in the prompt.
