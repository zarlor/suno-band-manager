# Feedback Triage Guide

Classify the feedback, then work it by its type. Mixed feedback can carry several types; each complaint is worked by its own.

## Types

**Clear** — specific nouns (guitar, vocals, drums, tempo), comparatives ("too much", "louder"), direct requests ("add", "remove"). *"The electric guitar is too prominent." "I need a bridge before the outro." "The drums overpower everything."*
Map directly, no elicitation, and explain each move concretely: "To pull the guitar back, I'd add 'subtle guitar, background guitar' and put 'guitar solo, heavy guitar' in Exclude Styles."

**Positive** — approval ("love it", "nailed it"), evolution asks ("can we try", "now make it"), preservation ("keep the..."). *"Love the vocals — can we try a darker instrumental?"*
Lead with the win, not a manufactured problem. Satisfied with no evolution ask: celebrate, offer to bank the winning settings to the band profile, and hand off; pushing "change one thing" on someone who's happy costs their trust. Wants to evolve: ask what to keep and what to push, lock the keepers as the anchor, map the rest.

**Vague** — feeling words without specifics ("off", "something's missing", "the vibe is off"), hedging ("hard to explain"), negation without an alternative ("that's not it"). *"It doesn't feel like what I imagined." "It's close but not there yet."*
Narrow from broad dimensions to one concrete anchor with the techniques below, starting wherever the user's awareness already is, one question at a time. Zero awareness ("all of it is off") goes straight to a reference: "Point me at anything that sounds like what you wanted — a song, an artist, a movie scene, or just a feeling." Propose no changes until a dimension and direction are confirmed; summarize the anchor and confirm it before mapping.

**Contradictory** — opposing descriptors ("more energetic but more relaxed", "raw and lo-fi but radio-ready"), reversals, wanting everything changed and nothing changed.
First check for dynamic contrast: "Sounds like you might want quiet verses building to powerful choruses — is that it?" If yes, it's section work (`[Energy: Low]` verse, `[Energy: High]` chorus). If it's genuinely contradictory, name the tension without judgment and use the first-principles fallback. When it spans arrangement, lyrics and delivery at once, change in three passes rather than all together, so each pass shows what it fixed or broke: (1) concept, mood and genre in the style prompt; (2) lyrics with structural and section tags and arrangement cues; (3) performance — inline delivery cues, energy tags, dynamics metatags.

**Technical** — quality words ("glitchy", "robotic", "clipping", "cuts off", "muffled", "tinny"), timestamps ("at 1:23"), mispronunciations: generation-specific issues distinct from creative direction.
Set expectations first: "Audio artifacts are usually specific to a particular generation, not the prompt itself." Then resolve each issue by the technical paths: regeneration first, editor or Studio by tier, and the prompt-fixable part of a dual-path issue mapped alongside. Two v6 habits arrive sounding like creative feedback but triage as technical: an excluded element that plays anyway ("I excluded it and it's still there") and the stock opening swell or an intro that won't stay drums-only — Exclude is guidance on v6, not a mute, so route both to the technical paths rather than adding more excludes.

## Elicitation techniques

**Binary narrowing** — quick A/B questions that find the dimension in under five: music and production versus vocals; energy (too high, too low, right); structure (sections, flow, length); lyrics (content, delivery, phrasing); overall mood (right neighborhood or wrong direction). One question at a time; "kind of both" is signal; once it's down to one dimension, move to anchoring.

**Comparative anchoring** — reference points the user already knows: a song with the feel they want; where it sits now and where they want it between two named extremes; two contrasting descriptions to choose between; "the last song that made you feel the way this one should". No musical knowledge required ("a movie scene" or "a feeling" works). Decompose a reference into concrete audio traits: instrumentation, tempo, vocal style, production, energy. A reference is often easier for a non-musician than dimensional questions, so pivot to one when narrowing stalls.

**Emotional vocabulary bridge** — map the feeling to Suno words. Offer only the pairs relevant to the narrowed dimension, and ask where the take sits now and where they want it; the gap sets the size of the change.

| Pair | Toward the first → Suno | Toward the second → Suno |
|------|----------------|-----------------|
| Heavy ↔ Light | Dense instrumentation, layered, bass-heavy, thick | Sparse arrangement, airy, minimal, delicate |
| Fast ↔ Slow | Driving rhythm, uptempo, energetic beat | Slow tempo, laid-back groove, gentle pace |
| Polished ↔ Raw | Radio-ready mix, clean production, crisp | Lo-fi, organic, rough edges, imperfect |
| Familiar ↔ Weird | Classic genre conventions, traditional | Experimental, unexpected, genre-bending (↑ Weirdness) |
| Warm ↔ Cold | Analog warmth, rich tones, close mics | Crystalline, digital, distant, sterile |
| Intimate ↔ Epic | Close, quiet, small room, whispered | Wide stereo, big reverb, anthemic, soaring |
| Smooth ↔ Gritty | Clean vocals, flowing melody, polished | Raspy, distorted, textured, rough |
| Bright ↔ Dark | Major key feel, uplifting, shimmering | Minor key feel, moody, deep, shadowy |
| Tight ↔ Loose | Precise timing, quantized, controlled | Swing, human feel, organic timing, relaxed |
| Simple ↔ Complex | Minimal arrangement, few instruments | Layered, intricate arrangement, multiple textures (↑ Weirdness) |
| Organic ↔ Synthetic | Acoustic instruments, natural, analog warmth | Electronic, digital, synthesized, programmed beats |
| Atmospheric ↔ Punchy | "atmospheric": reverb, space, ambient pads | "punchy": low-end presence, tight transients |
| Lo-fi warmth ↔ Polished radio-ready | "lo-fi warmth": vintage character, low-pass filtering | "polished radio-ready": clean, modern, commercial mix |
| Driving ↔ Lush | "driving": forward momentum, energetic basslines | "lush": layered pads, dense production |
| Unpolished ↔ Produced | "unpolished room sound", "natural room ambience", "single-take band performance": less processed | "wide stereo", spatial separation, processed |

Never use the word "live" in any form (`live recording`, `live-band drums`, `live energy`): it pulls crowd and audience noise (LOCAL-CONFIRMED, recurring). Use the room-sound phrases above.

**First-principles fallback** — for contradictory feedback, or elicitation that isn't converging. Ask: "If you could only keep one thing about this song exactly as it is, what would it be?" Lock that anchor; for each remaining dimension offer two options built around it, layer by layer, checking for contradiction at each step; reframe a new contradiction as structural contrast (verse versus chorus, intro versus drop).
