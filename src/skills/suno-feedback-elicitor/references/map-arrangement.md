# Map: Instruments and Arrangement

Instrument balance, arrangement density, an instrument that dominates or goes missing, and genre words that pull the wrong arrangement. Grades: COMMUNITY is several users, ANECDOTAL one report, LOCAL this module's own renders.

## Style prompt adjustments

| Feedback | Add to style prompt | Add to Exclude Styles |
|----------|--------------------|--------------------|
| "Too busy / cluttered" | "minimal arrangement, sparse instrumentation" | "dense layering, wall of sound" |
| "Too empty / thin" | "lush arrangement, layered instrumentation, full sound" | — |
| "Guitar too loud" | "subtle guitar, background guitar" | "guitar solo, heavy guitar" |
| "Needs more guitar" | "prominent guitar, guitar-driven" | — |
| "Too electronic" | "organic, acoustic instruments, natural room sound" | "synthesizer, electronic beats" |
| "Too acoustic" | "electronic elements, synth textures, modern production" | — |
| "Drums overpower" | "soft percussion, gentle drums, restrained beat" | "heavy drums, pounding drums" |
| "Needs more drums" | "driving drums, prominent beat, rhythmic" | — |
| "Piano feels wrong" | — | "piano" (or narrower: "classical piano") |
| "Bass too heavy" | "light bass, subtle low end" | "heavy bass, bass drops" |
| "Second line drums sound like hip-hop" | "second line drums" lands as a NOLA parade groove only in an up-tempo, energetic, celebratory context; add "New Orleans parade", "celebratory", "up-tempo" | — |

## Diagnostics with non-obvious causes

Check the named source before rewording.

| Feedback | Check first | Cause and fix |
|---|---|---|
| "The band disappears under the vocal" / "dead verse" | The prompt describes a sound, not what each instrument does in each section | Rewrite as instrument-by-section direction ("the riff continues under the verse vocal, palm-muted, never stops"), and restate the key instruction as a short cue at the top of that section in the lyrics |
| "Guitar dominates / bass not prominent enough" (rock, metal) | Genre and the instrumental sections | Bass-forward rock or metal is a known Suno limitation, not reliably achievable: Style Influence 85 didn't force it, and low Audio Influence (15%) shifted era feel instead. Worth trying: drop "guitar" from the prompt, add guitar to Exclude Styles, `[Instrument: bass]` tags (unreliable) |
| "Wrong bass tone" | "funk" in the prompt | "funk" pulls slap/pop bass; for overdriven fingerstyle bass remove "funk" entirely |
| "Too theatrical" / "too many keyboards" / "light strings, not heavy orchestra" | `baroque` (Disney/theatrical), `rock opera` (keyboard-heavy), `cinematic` (soundtrack feel), `orchestral` (light strings and flutes) | Describe the qualities without those words and name the instruments ("cello, heavy strings, kettle drums"); "power ballad" gives rock-opera dynamic range without the keyboards |
| "Heavy guitars sound synthetic" (metal, high gain) | Genre — the most-reported v6 weakness (COMMUNITY) | Try v6-wild; name the kit and room ("acoustic drum kit in a room"); expect more generations than lighter genres need. Personas and Voices are reported to intensify the synthetic timbre in high-gain lanes |
| "The band dropped out for the last chorus" | Reported by 4 users as a v6 default after the bridge, wording didn't stop it (COMMUNITY); production testing hasn't shown it (n=10 full-cued final choruses, none stripped) | On a near-keeper: Extend from just before the last chorus and re-roll from there, then "get full song" (ANECDOTAL, untested here) |
| "There's a guitar solo I didn't ask for" | Suno adds unscripted guitar solos regularly | "guitar solo" in Exclude Styles; give the guitar a stated job in that section |
