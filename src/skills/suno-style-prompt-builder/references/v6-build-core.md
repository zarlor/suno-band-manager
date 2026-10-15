# v6 Build Core

Every-build rules for the v6 family (v6, v6-wild, v6-mini). Grades: OFFICIAL (Suno's docs), VENDOR (guide sites' tests), COMMUNITY (several users), ANECDOTAL (one report), LOCAL (this module's renders, small samples). Pre-v6 evidence is a mild suggestion, never a veto on a v6 test.

## The prompt: ordered production direction

v6 follows the style field literally and fills whatever it leaves unsaid with its safest default (COMMUNITY): a v5-style descriptor list gets a matching intro, then a band that thins out under the vocal. Six habits:

1. **An order:** Genre → Vocals → Drums → Guitars → Bass → Other instruments → Arrangement/Energy → Production → Ending (COMMUNITY; unproven, costs nothing).
2. **Each instrument gets a job per section, in verbs:** "the intro riff continues under the verse vocal, palm-muted and lower", not "big riffs". A section the prompt skips is one where the instrument drops out (COMMUNITY + VENDOR).
3. **Place the vocal instead of praising it:** "vocal in front of the band, close-mic'd and dry, the loudest element; instruments sit behind and below the voice"; thinning the arrangement under the verse is the most-reported fix for a buried vocal (VENDOR + COMMUNITY).
4. **State both edges, with lengths:** "4-bar guitar intro, instrumental only"; "ends on a hard stop after the final chorus". Unstated, the intro comes back as humming and the ending vamps or cuts off mid-lyric (VENDOR + COMMUNITY).
5. **Positive text only;** every negative goes in Exclude Styles (VENDOR ×2 + COMMUNITY).
6. **A short production clause helps; mastering words don't:** "high-fidelity studio production, close-mic vocals, crisp transients, clear instrument separation" (COMMUNITY); "radio-ready, -14 LUFS" does nothing.

**Genre dominance.** The first genre term is the anchor: genre tags carry most of the arrangement (~60–70%, VENDOR) and each later genre is fainter color. Put the genre that should drive the arrangement first and demote the rest with "accents", "undertones" or "influences"; nothing promotes a buried genre to lead. Genre, mood and vocal go in the first ~200 characters. Working v6 prompts are longer and more sentence-shaped than v5's 5–8 descriptors.

**Mood comes from the prompt, not the lyrics** (COMMUNITY): state the emotional direction in the style field.

**Tempo as feel.** State one BPM for the whole song and pair every number with feel words ("72 BPM feel with a slow heavy backbeat"), since a bare number is often ignored (COMMUNITY). Carry section contrast as half-time or double-time drum feel and sparse or dense arrangement over that pulse, in the same scene-naming phrases in the style prompt and the lyric section cues (VENDOR + COMMUNITY; LOCAL: heard as "a LOT better"). A feel switch lands sometimes, not reliably.

## Controls, top to bottom on the Create form

| Control | Package default | Why |
|---|---|---|
| Vocal Gender | Empty with a Voice or an instrumental | The Voice defines the singer; a setting can fight it |
| Duration | Auto | Custom when length is a requirement, or at sung length + 15–20 s when Auto pads a long tail (LOCAL) |
| Max Mode | On for any take the user might keep | Applied at generation, so a finished take can't be upgraded; 2× credits (OFFICIAL). LOCAL: it separated usable takes from unusable |
| Weirdness | Chosen per song (safety tables) | Safe ↔ Chaos, 50 normal (OFFICIAL). v5.5's 60–75 counter-genre range and ~80 cliff are untested on v6 |
| Style Influence | Chosen per song (safety tables) | Defaults to 50 (VENDOR ×2), so set it. Plateaus above ~80: 100 did no better than 85 (ANECDOTAL, controlled) |
| Audio Influence | Persona 15–25%, Voice 35–95% | Only with audio attached; a value from the other slot's range is an error. Profile each voice on v6 |
| Variety | Exact style | Any higher notch rewrites the prompt before generating (OFFICIAL; LOCAL: negatives flipped, details invented) |
| Personalize | Off | My Taste makes the package irreproducible across accounts |

Exclude Styles, the panel's first row, survives the Variety rewrite intact (155 of 156 pairs, ANECDOTAL, controlled). It still steers rather than mutes: on v6, users report the bass kick, vocal gender, vocal repeats, synth loops and the opening swell coming through anyway (COMMUNITY, 2026-10). Keep negatives there, and for an element the song can't have, also say in the style what plays instead.

## Guidelines from testing

Guidelines, not laws: a song that wants otherwise wins.

Use generally:

1. **Describe the band's part, not song-wide gravity words:** `heavy`, `doom`, `crushing`, `massive`, `epic`, `cinematic` and `industrial` pull stock conventions (COMMUNITY) and measured the vocal under the band (LOCAL, small n). Put the weight on moments.
2. **Choose the era anchor for its production habits** (`80s hair metal` brought a gated snare, ANECDOTAL); name an amp or tone character over "distortion" (ANECDOTAL ×3).

Where the song calls for it:

3. **A band-side vocal-space clause** when the vocal must get in front: "rhythm guitars leave midrange space for the lead vocal" (LOCAL: no phrase alone has lifted a vocal; the arrangement decides).
4. **An ending written as the singer's action plus the band leaving,** when a long instrumental tail must be avoided (LOCAL, n=1: it steered the last line, not the tail).
5. **No bare "vocal" in the style field** when a wordless "ooooh" intro would hurt (ANECDOTAL, n=1); open the lyrics on a sung line.
6. **A heavy chorus gets its job, not its feeling:** "big", "emotional" and "epic" slow it into a ballad (COMMUNITY; the rewrite is in the trigger table).
7. **`key change` in Exclude Styles when the song must hold its key:** v6 adds unrequested modulations in some genres (ANECDOTAL). Leave it out where one would be welcome.
8. **With a Voice attached, add no vocal character the Voice lacks** ("gritty"): style words reshape the clone (ANECDOTAL + LOCAL). Words matching its real character may help.

To try:

9. **Carry "unresolved" as harmony** ("ends off the home chord"), not as a mood word: a mood tag on a bare verse made it the loudest section (LOCAL, n=1).
