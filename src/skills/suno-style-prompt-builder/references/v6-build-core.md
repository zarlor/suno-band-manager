# v6 Build Core

Every-build rules for the v6 family (v6, v6-wild, v6-mini). Grades: OFFICIAL (Suno's docs), VENDOR (guide sites' tests), COMMUNITY (several users), ANECDOTAL (one report), LOCAL (this module's renders, small samples). Pre-v6 evidence is a mild suggestion, never a veto on a v6 test.

## The prompt: ordered production direction

v6 follows the style field literally and fills whatever it leaves unsaid with its safest default (COMMUNITY): a v5-style descriptor list gets a matching intro, then a band that thins out under the vocal. Six habits:

- **An order:** Genre → Vocals → Drums → Guitars → Bass → Other instruments → Arrangement/Energy → Production → Ending (COMMUNITY; unproven, costs nothing).
- **Each instrument gets a job per section, in verbs:** "the intro riff continues under the verse vocal, palm-muted and lower", not "big riffs". A section the prompt skips is one where the instrument drops out (COMMUNITY + VENDOR).
- **Place the vocal instead of praising it:** "vocal in front of the band, close-mic'd and dry, the loudest element; instruments sit behind and below the voice"; thinning the arrangement under the verse is the most-reported fix for a buried vocal (VENDOR + COMMUNITY).
- **State both edges, with lengths:** "4-bar guitar intro, instrumental only"; "ends on a hard stop after the final chorus". Unstated, the intro comes back as humming and the ending vamps or cuts off mid-lyric (VENDOR + COMMUNITY).
- **Positive text only;** every negative goes in Exclude Styles (VENDOR ×2 + COMMUNITY). Negatives in the style text backfired for 8 users: "'No drums' = you're getting drums" (COMMUNITY, 2026-11).
- **A short production clause helps; mastering words don't:** "high-fidelity studio production, close-mic vocals, crisp transients, clear instrument separation" (COMMUNITY); "radio-ready, -14 LUFS" does nothing.

**Genre dominance.** The first genre term is the anchor: genre tags carry most of the arrangement (~60–70%, VENDOR) and each later genre is fainter color. Put the genre that should drive the arrangement first and demote the rest with "accents", "undertones" or "influences"; nothing promotes a buried genre to lead. Genre, mood and vocal go in the first ~200 characters.

**Length is contested.** 18 users report better results from short, sparse style prompts and 12 from long, detailed ones, and nobody has run a controlled comparison (COMMUNITY, 2026-11). Neither is the v6 default. The six habits produce the detailed kind; when a take ignores a prompt of one length, the same content at the other length is a one-variable test.

**Mood comes from the prompt, not the lyrics** (COMMUNITY): state the emotional direction in the style field.

**Tempo as feel.** State one BPM for the whole song and pair every number with feel words ("72 BPM feel with a slow heavy backbeat"), since a bare number is often ignored (COMMUNITY; in 2026-11, 5 users report a requested BPM not held and 4 report it held). Carry section contrast as half-time or double-time drum feel and sparse or dense arrangement over that pulse, in the same scene-naming phrases in the style prompt and the lyric section cues (VENDOR + COMMUNITY; LOCAL: heard as "a LOT better"). A feel switch lands sometimes, not reliably.

## Controls, top to bottom on the Create form

| Control | Package default | Why |
|---|---|---|
| Vocal Gender | Empty with a Voice or an instrumental | The Voice defines the singer; a setting can fight it |
| Duration | Auto | Custom when length is a requirement, or at sung length + 15–20 s when Auto pads a long tail (LOCAL). A set duration is a target: 4 users report it not held (COMMUNITY, 2026-11) |
| Max Mode | On for any take the user might keep (Pro/Premier; Free has no Max Mode, Variety or Personalize control: `v6_options` values are `null` there) | Applied at generation, so a finished take can't be upgraded; 2× credits (OFFICIAL). LOCAL: it separated usable takes from unusable. Users split: 18 credit it, 15 report no gain or harm (COMMUNITY, 2026-11), so weigh the doubled cost |
| Weirdness | Chosen per song (safety tables) | Safe ↔ Chaos, 50 normal (OFFICIAL). v5.5's 60–75 counter-genre range and ~80 cliff are untested on v6. On v6, 19 users keep it low (0–35) and 8 run it high (COMMUNITY, 2026-11) |
| Style Influence | Chosen per song (safety tables) | Defaults to 50 (VENDOR ×2), so set it. Plateaus above ~80: 100 did no better than 85 (ANECDOTAL, controlled). Users set it high for new songs (10) and low for Covers (6); 3 report it barely moves v6 output (COMMUNITY, 2026-11) |
| Audio Influence | Persona 15–25%, Voice 35–95% | Only with audio attached; a value from the other slot's range is an error. Profile each voice on v6. To hold an upload, a Cover source or a Voice, 25 users run 75–100 and 7 report limits (COMMUNITY, 2026-11) |
| Variety | Exact style | Any higher notch rewrites the prompt before generating (OFFICIAL; LOCAL: negatives flipped, details invented). 24 users report the rewrite and that 0 keeps the prompt as typed, 5 the opposite (COMMUNITY, 2026-11); 7 note the rewritten text can be read on the finished song |
| Personalize | Off | My Taste makes the package irreproducible across accounts; 6 users turn it off to stop the same style rewriting (COMMUNITY, 2026-11) |

Exclude Styles, the panel's first row, survives the Variety rewrite intact (155 of 156 pairs, ANECDOTAL, controlled). It still steers rather than mutes: on v6, users report the bass kick, vocal gender, vocal repeats, synth loops and the opening swell coming through anyway. It is unreliable for 16 users and works for 9 (COMMUNITY, 2026-11; about 21 against 6 in 2026-10, those six all with short, concrete lists): "yelling, screaming, shouting, belting" removed a strained vocal, and "oohs, aahs, yeahs, humming intro, hum, humming, vocalise…" cut intro humming. A broad list misses: "orchestral, percussion, cinematic, harp, piano" still left harp in a sparse cello-and-flute piece. Five users write the list as bare words, not "no X" (COMMUNITY, 2026-11, no tested outcome), and one finds an exclude loses when a related word sits in the style prompt (ANECDOTAL, 2026-11). Keep negatives there, short and concrete, and for an element the song can't have, also say in the style what plays instead.

## Guidelines from testing

Guidelines, not laws: a song that wants otherwise wins.

Use generally:

- **Describe the band's part, not song-wide gravity words:** `heavy`, `doom`, `crushing`, `massive`, `epic`, `cinematic` and `industrial` pull stock conventions (COMMUNITY) and measured the vocal under the band (LOCAL, small n). Put the weight on moments. Single words are read literally: `crowd`, `arena`, `live instrumentation`, `epic`, `cinematic` and `stadium` brought crowds or a huge room (COMMUNITY, 8 users, 2026-11); the crowd and "live" lists are in `references/safety-tables.md`.
- **Name the sounds, not just the genre or the mood:** describing the sound or the recording situation beat a bare genre label for 9 users against 1 (COMMUNITY, 2026-11; 13 users, all genres, 2026-10). Name signature sounds, instruments, drum patterns and textures ("squelchy 303 bassline, 909 drums"); "'303 bassline' or 'chord stabs' tells the model far more than 'dark' or 'energetic'." Users split on prompt length (above); most agree on specific words. Choose the era anchor for its production habits (`80s hair metal` brought a gated snare, ANECDOTAL), knowing era styles often come out modern (Genre notes); name an amp or tone character over "distortion" (ANECDOTAL ×3).

Where the song calls for it:

- **A band-side vocal-space clause** when the vocal must get in front: "rhythm guitars leave midrange space for the lead vocal" (LOCAL: no phrase alone has lifted a vocal; the arrangement decides).
- **An ending written as the singer's action plus the band leaving,** when a long instrumental tail must be avoided (LOCAL, n=1: it steered the last line, not the tail).
- **No bare "vocal" in the style field** when a wordless "ooooh" intro would hurt (ANECDOTAL, n=1); open the lyrics on a sung line.
- **A heavy chorus gets its job, not its feeling:** "big", "emotional" and "epic" slow it into a ballad (COMMUNITY; the rewrite is in the trigger table).
- **`key change` in Exclude Styles when the song must hold its key:** v6 adds unrequested modulations in some genres (ANECDOTAL). Pair it, like every exclude, with a positive line in the prompt ("stays in one key to the end"). Leave it out where one would be welcome.
- **With a Voice attached, add no vocal character the Voice lacks** ("gritty"): style words reshape the clone (ANECDOTAL + LOCAL). Words matching its real character may help.

To try:

- **Carry "unresolved" as harmony** ("ends off the home chord"), not as a mood word: a mood tag on a bare verse made it the loudest section (LOCAL, n=1).
- **For distorted guitars, spend the words on guitar tone, not on the genre label** (ANECDOTAL, one tester, 2026-10; another user in the same thread found the opposite): drums responded to prompting and exclusions where distorted guitars mostly didn't, and a detailed guitar-tone description kept the guitars intact through mid-song better than "modern heavy metal" did. Both still degraded toward the end (late-song degradation, which the `suno-feedback-elicitor` skill diagnoses).

## Genre notes (few reports)

COMMUNITY or ANECDOTAL, 2026-10 and 2026-11; things to try.

- **Metal and hard rock:** still v6's weakest area (COMMUNITY, 18 users against 9, 2026-11): one drum and guitar sound across sub-genres. Three recipes, each one user's outcome (ANECDOTAL): start in another genre and remix to metal; make a "live" Cover of the song; build breakdowns as separate generations.
- **Era and period styles:** come out modern (COMMUNITY, 9 users against 2, 2026-11).
- **Styles outside the mainstream:** 11 users prefer v6-wild or v6-mini there; 3 report the opposite (COMMUNITY, 2026-11).
- **Ambient:** describe the texture, not the genre; "cyberpunk" pulls in a beat (COMMUNITY, 8 users).
- **Orchestral and cinematic:** sparse beats dense, "The less sound density, the better" (COMMUNITY, 5 users). One user keeps orchestras dry ("close mic, dry") because "orchestras drown in reverb" (ANECDOTAL). With rock, "chamber music" in place of "symphonic rock" gave "MUCH MUCH better results" (ANECDOTAL, one user, 2026-11).
- **Solo piano** (ANECDOTAL, two prompts with outcomes): "solo cinematic piano, expressive, film score, melancholic, minimalist, pure acoustic"; "Dry Close-Mic Upright Piano… Zero Electronic Elements, 96 Bpm".
- **Classical and Baroque:** classical and orchestral from text are thin and mixed (8 single reports, 2026-11); from audio, v6 was judged poor by 2 users and good by 1. Baroque, harpsichord and counterpoint have no community prompting report at all in the 2026-11 sweep, and none with a working method before it; the one earlier note is that in counterpoint "the '2nd melody' dies" (one report, 2026-10).
