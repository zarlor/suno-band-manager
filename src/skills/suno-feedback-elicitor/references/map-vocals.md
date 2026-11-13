# Map: Vocals

Vocal level, placement, delivery and timbre, and feedback on a Voice, Persona or Custom Model. Grades: COMMUNITY is several users, ANECDOTAL one report, LOCAL this module's own renders. A pair of counts is users reporting the effect against users reporting the opposite.

## Style prompt adjustments

| Feedback | Add to style prompt | Add to Exclude Styles |
|----------|--------------------|--------------------|
| "Vocals too polished" | "raw vocal, imperfect delivery, organic phrasing" | "perfect pitch, overproduced vocals" |
| "Vocals too rough" | "polished vocal, smooth delivery, clean singing" | "raspy vocals, rough vocals" |
| "Voice doesn't match" (no Voice attached) | "male/female voice, [age] years old, [tone] delivery" | the unwanted gender's vocals |
| "Too much vibrato" | "steady vocal, straight tone" | "heavy vibrato" |
| "Vocals too loud" | "balanced mix, instrument-forward" | — |
| "Singing sounds robotic" | "natural phrasing, breathy, human vocal" | "robotic vocals" |
| "Want harmonies" | "vocal harmonies, layered vocals, backing harmonies" | — |
| "Too much harmony" | "solo vocal, single voice, unison" | "harmonies, backing vocals" |

## v6 vocal symptoms

| Feedback | First check | Then |
|---|---|---|
| "The vocal is buried / muffled" / "vocals too quiet" | Arrangement density under the vocal; the vocal never placed | Place the vocal: "in front of the band, close-mic'd, dry, loudest element". Thin the verse arrangement under it, and give the band a job that leaves room: "rhythm guitars leave midrange space for the lead vocal" (LOCAL: no phrase alone has lifted a vocal; the arrangement decides). For heavy guitar material, describe the mix relationships as their own block, never numbers: "In-Your-Face Vocals, Rhythm Guitars EQ-Carved Around Vocals, Reduced Guitar Midrange Masking, Distorted Compressed Rhythm Guitars Pushed Back, Clear Instrument Separation" (COMMUNITY; it may reach into the arrangement, so test it on one Create first). Dullness from the first bar is the render: regenerate or try v6-wild; adjectives will not add top end |
| "It reads instead of sings" / "rushed, no held notes" | Lyric density and missing delivery direction | Fewer syllables per line; write the holds on the page (`sta-a-ay`); describe the performance in the style field; `[Silence]` at the end of each line has one careful tester's backing |
| "Too many backing vocals" / "it doubles everything" | v6 adds doubling and backing unasked (LOCAL-OBSERVED); remove any dual or harmony asks first | Then test "backing vocals" in Exclude Styles, changing nothing else |
| "Vocals are screaming when they shouldn't be" | `metal`, `sludge`, `doom` in the style prompt; `!` or ALL CAPS in the lyrics — scream triggers | Remove the triggers, add a positive instruction ("clean vocals, melodic singing"), and use `[Vocal Style: whispered]` to reset after an aggressive section |
| "The male vocal sounds generic" / "autotuned" (stock voice, no Voice) | v6's stock male voices are widely reported as generic or glossy unless steered hard (COMMUNITY, 6+ users, with counter-examples); they also measured about a semitone lower and darker (ANECDOTAL-controlled) | Generate the vocal a cappella first, then Cover it with the band (2 users); or a detailed vocal description at Weirdness 0, Variety *Exact style*, Style Influence 100 (1 user). The user's own Voice avoids the stock v6 vocal for 12 users; 4 report the opposite (COMMUNITY, 2026-11) |
| "The voice changes partway through" / "it switched from a man to a woman" | The voice or its gender changing mid-song is a v6 report (COMMUNITY, 16 users against 4, 2026-11) | Something to try once, changing nothing else: repeat the voice descriptor in every section tag. 12 users say it helped; 7 say tags don't hold a voice |
| "It stutters on a word" / "it repeats a word" | Line length: word stutter is a v6 report (COMMUNITY, 8 users, 2026-11) | Shorter lines eased it for 5 users |
| "It mispronounces a word" | — | Phonetic respelling in the lyrics fixed pronunciation for 12 users and not for 5 (COMMUNITY, 2026-11) |
| "My voice sample sounds grittier than it should" | Grit, gravel or rasp words near the vocal description or the genre head (LOCAL-OBSERVED) | Move the grit onto instrument descriptors and keep the vocal line clean |

## Inline performance modifiers

Parenthetical cues after a lyric line direct that line's delivery: `(breathy)` or `(soft)` for a line sung too hard, `(belt)` for more power, `(breath)` for a pause, `(hold)` to sustain. Use sparingly; they are line-level, not section-level. Lyric changes go to the Lyric Transformer as an adjustment spec.

## Voices, Personas and Custom Models

**Voice attached:** the Voice supplies identity (timbre, character); delivery changes go in the lyrics as delivery metatags, not style-prompt vocal words: `[Whispered]`/`[Soft]` rather than "whispered vocals", `[Belted]`/`[Powerful]`, `[Tender]`/`[Yearning]`, `[Aggressive]`/`[Screamed]`.

| Feedback | Cause | Path |
|---|---|---|
| "Vocals don't sound like me" | Audio Influence too low, a poor source recording, or style words overriding the Voice | Raise Audio Influence first (Suno's official escalation for this complaint). Start a Voice around 50% and move in 5–10% steps against the complaint: identity loss argues up, artefacts argue down. Community testing puts diminishing returns past ~70%, but one profiled voice was clean at 85% where 55% showed artefacts, so it isn't a ceiling. If raising it doesn't recover identity, Suno's next step is rebuilding the voice profile from a clean acapella. Recommend a direction and a start point; the builder sets the final number |
| "Voice sounds right but delivery is wrong" | Style-prompt vocal descriptors fighting the Voice | Remove them; use delivery metatags |
| "The Voice sounds like someone else" / "it added grit I don't have" | Vocal character words the Voice doesn't have (ANECDOTAL: *"style can influence how they sound"*) | Take out character the Voice lacks ("gritty"); words matching character it has may help. Keep range and placement guards |
| "My old Voice / Persona doesn't sound the same on v6" | Voices and Personas made before v6 no longer match for 9 users; 5 find them better in v6 (COMMUNITY, 2026-11) | Say that both are reported, then work it as "Vocals don't sound like me" above; no fix specific to this is reported |
| "I want two of my Voices on one song" | One song cannot take two Voices (COMMUNITY, 6 users, 2026-11) | Say so before trying prompt changes; no workaround is reported |
| "It won't let me make a Voice from this song" | A Voice cannot be created from a song with an upload in its history (COMMUNITY, 3 users, 2026-11) | Say that this is the reported limit; a song with no upload in its history is the source to try |

**Custom Model:** it has learned a production DNA, so generic descriptors ("polished production", "raw mix") get absorbed. Be more specific: name the element ("reduce distorted guitar layers, more acoustic presence"; "push vocals forward, pull back drum room reverb"). If it consistently misses, retrain on a better-curated catalog (a new model: delete the old one, another 100 credits). If takes echo a melody or chord progression from the training songs, that's the model copying (COMMUNITY): a larger, more varied training set in the same lane reduces it.

**Voice and Custom Model together, or voice and style changing at once:** change one variable per generation so the cause stays visible — delivery metatags first, then Audio Influence, then the style prompt, regenerating after each. A Persona or Voice carries identity; the style prompt carries the producer brief.
