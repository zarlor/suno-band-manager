# Safety Tables

The one home for the style-prompt gotchas: artist names, the vocal and arrangement triggers, prompt-wide rules, the exclude rule and the per-song slider rule. `scripts/validate-prompt.py` flags the enumerable words (its lists match this file); the substitution and every judgment call come from here.

When the validator can't run, check by hand: the model's character limit (1,000; 200 on the retired v4 Pro), genre, mood and vocal essentials in the first 200 characters, no section tags or asterisks, no artist names, and every word in the trigger lists below.

## Artist and Song Names

Suno strips artist names from prompts by policy (OFFICIAL) and redirects them to generic characteristics, so a name, an album or a song title spends budget and steers nothing. Decompose the reference into concrete sonic descriptors: genre, era and production, vocal character, signature instruments, energy, emotional tone. Decompose only an artist you confidently know; otherwise web-search their sound first, or, with no search, ask the user what they like about it. A wrong decomposition produces a prompt that sounds nothing like the intent, and the user can't tell why. A decomposition can carry a trigger of its own ("thrash", "doom", "anthemic"), so check its words against the lists below.

## Vocal Triggers

### Scream/Harsh Vocal Triggers

Certain words reliably trigger unwanted screaming or harsh vocals, even when the intent is melodic:

- `metal`, `sludge`, `doom`, `death`, `thrash` and `black` as genre modifiers, on their own (without melodic vocal guidance)
- `!` in the prompt or the lyrics (exclamation marks push vocal delivery toward shouting/screaming)

**Fix:** Always pair heavy genre terms with explicit positive vocal instructions. For example, `heavy swamp metal, raw melodic singing` or `sludge metal, gritty male vocals` (plus "screaming" in Exclude Styles — on v6 the negative goes only there, never inline). Telling Suno what you DO want from the vocals is more reliable than only excluding what you don't. For heavy without the word, use `progressive heavy groove` or `heavy groove`. An instrumental has no vocal to protect, so it skips the pairing.

**On v6, choruses belt by default** (COMMUNITY, 17 users, 2026-10): "it's literally ALL CAPS IN THE CHORUS". `epic`, `cinematic`, `power ballad` and `post-hardcore` are reported to bring belting or screams (3 users, low confidence; production testing here uses `power ballad` as the rock-opera substitute below, and that stands). For a clean or soft lead, keep those words out and put `yelling, screaming, shouting, belting` in Exclude Styles, which fixed it for one user.

### The "live" Word Family Triggers Crowd Noise (LOCAL-CONFIRMED, recurring)

**Any** form of the word — `live-band drums`, `live recording`, `live energy`, `live in the room` — pulls audience noise, crowd texture and crowd-vocal bleed, even when the intent is band-in-a-room energy: the word carries "live album" as its dominant association, and one instance is enough. Community reports agree (COMMUNITY, 10 users, 2026-10): "live", "live drums" and "unplugged" bring crowd noise or a singalong, "Never ever ever use the term live drums unless you want crowd noise and cheers"; two say "live" no longer does.

**Say the quality, not the venue.** `unpolished room sound`, `natural room ambience`, `single-take band performance`, `minimal overdubs`, `dry close-mic drums with room bleed` all get the intended texture without the word.

### Crowd, Choir, and Extra-Vocal Avoidance

When the song needs **one singer** and nothing else, three layers work together. Any one alone leaks.

1. **Positive solo-singer language in the style prompt** — "solo lead vocal, one singer only," and where the energy is supposed to come from instead: "chorus energy from instruments and arrangement, one voice throughout" (phrased positively: "not extra voices" is an inline negative, which hands Suno "extra voices"). Filling the role is stronger than forbidding the filler.
2. **Excludes covering the whole family** — `choir, backing vocals, gang vocals, layered vocals, crowd chants`. With a Voice attached, this is a second step, not a first build's default: v6 doubles a Voice on its own, and excluding backing vocals for it is untested, so add the family only after a take doubled too much, and say so in its rationale. Excluding "choir" alone leaves gang vocals and stacked doubles untouched; they are different arrangement conventions and Suno reaches for whichever one the genre suggests.
3. **Avoid the trigger words entirely** — `anthemic`, `festival`, `stadium`, `concert`, `crowd`, `audience`, and **the whole "live" family** invite group vocals and audience texture by association. Excludes cannot reliably override a prompt that is asking for group energy in its adjectives.

The lyric side of this stack — section-tag wording that invites choirs, and the anti-choir tag forms — is the `suno-lyric-transformer` skill's job; when one singer matters, say so in the handoff notes.

## Prompt-Wide Rules

### No Inline Negatives

Suno keeps the noun and drops the negation, so "no screaming" or "without reverb" asks for screaming and reverb. Write what you want instead ("raw melodic singing", "dry, close-mic'd") and put the negative in Exclude Styles. The validator flags "no X" and "without X" as high, and "not X", "avoid X" and "don't X" as medium. Persistence phrasing ("the riff continues under the verse, never stops") is direction, not a negative.

### One Tempo Per Song

Suno doesn't shift BPM within a song: a "tempo change" or "dynamic pacing" prompt produces arrangement-density changes (pull back for a halftime feel, compress for double-time) over one steady tempo. Plan one underlying BPM, and use rhythm nouns (`halftime groove`, `double-time driving`, `shuffle feel`) over "slow" and "fast" to vary the felt pace.

### The Instrument Palette Is Global

Instruments named anywhere in the style prompt bleed into every section; section tags can only emphasize what the prompt already names, never add an instrument it lacks. "Accents" after an instrument name and placing it last reduce the bleed without removing it. When an instrument has to stay out of a section, leave it out of the prompt, or generate with it and remove it from that section with stems.

## Arrangement Triggers

### Dangerous Words and Keyboard Triggers

Certain words reliably pull Suno into unwanted instrumental territory — typically theatrical, keyboard/synth-heavy, or cinematic-light arrangements. Avoid these when guitars and bass should lead.

| Word/Phrase | What Suno Does | Fix |
|---|---|---|
| `baroque` | Maps to theatrical/classical keyboard territory — Disney-adjacent | Describe Baroque qualities without the word: Bach counterpoint = `intricate interlocking guitar and bass melodies`; minor key ornamentation = `dark minor key, precise and ornate` |
| `orchestral`, `orchestral accents` | Defaults to light/cinematic strings, not heavy | Specify HEAVY orchestral instruments explicitly: `cello, heavy strings, kettle drums` — these live in metal's frequency range |
| `cinematic` | Pulls keyboard/synth-heavy arrangements | Use `dynamic shifts`, `building from gentle to crushing` instead |
| `rock opera` | Pulls keyboard/synth-heavy, theatrical arrangements | Use `power ballad`, `dynamic shifts`, `building from gentle to crushing` instead |
| `big`, `emotional`, `epic` as the **chorus** instruction (v6) | Rock and metal choruses slow into a dramatic ballad (COMMUNITY) | Write the chorus's job: `choruses stay rhythmically driving and hit harder than the verses` |

**"Baroque" workaround in detail:** If the song concept calls for Baroque-influenced metal, never use the word. Instead, describe the specific qualities you want — `intricate interlocking guitar and bass melodies` for counterpoint, `dark minor key, precise and ornate` for ornamentation. For orchestral weight, specify instruments that live in metal's frequency range: `cello, heavy strings, kettle drums`. Avoid `orchestral` as a standalone descriptor.

### Genre Term Behavior Table

What Suno generates for common genre keywords, from production testing.

| Genre Term(s) | What Suno Produces | Notes |
|---|---|---|
| `progressive metal` | Dream Theater-style technical shred | Avoid unless you specifically want technical wankery |
| `progressive groove metal` | Mastodon-adjacent pocket grooves | Better choice for most prog-metal needs |
| `prog rock` | Softer, more atmospheric progressive sound | Good for builds, dynamics, and patient arrangements |
| `heavy swamp metal` | Down/Crowbar-style low-end weight | Reliable for southern heaviness |
| `heavy swamp metal power ballad` | Gentle verses that build to heavy | Communicates "power ballad with weight" without invoking theatrical/keyboard territory |
| `dark alternative rock, slow and heavy, raw emotional weight, spacious oppressive mix, claustrophobic atmosphere` | Non-metal heaviness with emotional devastation | Good for pushing a metal band into non-metal territory; works for songs about powerlessness rather than power |
| `post-metal, post-hardcore` | Isis/Cult of Luna patient builds | Adding post-hardcore introduces off-tempo, prog-adjacent moments |
| `speed metal` | Fast, aggressive, thrash-adjacent | Straightforward — does what it says |
| `hard rock` | Straightforward driving energy | Clean, uncomplicated rock foundation |
| `hard rock` + `NOLA second line groove` + `brass band accents` | NOLA parade groove with rock weight | The combination pulls toward parade-style rhythms |
| `slow heavy swamp metal` + `pounding heartbeat kick drum` | Heavy, deliberate, single-tempo weight | Stacking slow/heavy modifiers locks Suno into a plodding pace |
| `prog rock` + `slow build then fade` | Atmospheric with proper decrescendo | One of the few reliable ways to get Suno to actually come back down |
| `Acoustic, intimate, solo voice with gentle guitar, bluesy, swampy, sparse and warm, quiet reflection, raw clean vocals, stripped down, empty room atmosphere` | Acoustic track that retains band identity | `bluesy, swampy` keeps NOLA identity; `empty room atmosphere` = reverb/space; explicitly exclude `heavy guitars, drums` in Exclude Styles |
| `heartland rock` | Accessible mid-tempo rock with Petty/Mellencamp/Springsteen character — chimey or mid-gain driven electric guitars, rock-forward without metal weight | **Safe rock term for Voice tracks** — no harsh vocal trigger. Good starting point when a clean-voice Voice clone needs rock energy without metal pull |
| `southern rock` | Rootsy rock with Allman/Skynyrd character — can pull slide/steel guitar as a byproduct of the genre association | Safe vocal-wise (no harsh-vocal triggers). Exclude `steel guitar` if you want to avoid the slide side. Pairs well with `heartland` to anchor toward the accessible end rather than jam-band end |
| `heartland southern rock` | Combined — intersection of accessible singer-songwriter rock with rootsy grit and drive | **Validated on Voice tracks** — clean folk-tagged Voice with "overdriven rhythm guitar with crunch" + "driving mid-tempo rock groove" as reinforcement produces rock presence without metal pull. Good for confessional rock songs that need both weight and accessibility |

## Exclude Styles

### Excludes Defend Against Drift From the Current Prompt Only

Suno is stateless: a Create knows only what is submitted with it — the style prompt, Exclude Styles, lyrics, sliders and any Voice, Persona or audio. It knows nothing of earlier takes of this song, another band's rendering of the same lyrics, or the user's catalog and profiles. So an exclude earns its place only by defending against a pull from this prompt's own descriptors.

**The test for every candidate:** what in this style prompt could plausibly pull Suno toward it? If nothing does, the exclude defends against a ghost and wastes the field.

- **Genre defaults count as a pull from this prompt.** A genre that habitually brings an element (a modulation, steel guitar, a choir) justifies excluding it, because the genre is named here; leave it out where the element would be welcome.
- **Parallel-band renderings** (the same song in two bands' catalogs) are where this goes wrong most: an exclude framed as defense against the other band's version defends against something Suno never sees. Build each rendering's excludes fresh from its own prompt.
- **Refine after drift:** "the last take drifted toward X" justifies excluding X only while this prompt still holds a descriptor, or names a genre, that pulls toward X; changing that descriptor is often the better fix. If nothing in the prompt pulls toward X, take-to-take variance is the likelier cause and the exclude is a ghost.

## Sliders

### Weirdness and Style Influence by Song Type

Choose Weirdness and Style Influence fresh for every song, from this table, the song's type and its counter-genre needs, reasoning from what each slider does. Never start from a band profile's stored `sliders:` values or "what similar songs used", not even for a quick demo: the sliders are the deliberate per-song differentiator that gives songs with similar prompts distinct feels, and the owner's standing direction is to use them. The failure this prevents: Weirdness 55, reasoned as "above the profile's 45", for a dissonant counter-genre song that wanted ~75.

Starting-point ranges from production testing:

| Song Type | Weirdness | Style Influence | Notes |
|---|---|---|---|
| Acoustic/stripped | 40 | 80 | Lower Weirdness for compliance; high SI to honor the style prompt's genre descriptors |
| Structured songs (verse-chorus) | 50-55 | 75-80 | Higher Style Influence keeps structure tight |
| Dark alternative | 50-55 | 75-80 | Standard settings |
| Through-composed | 55-60 | 70-75 | Slightly looser to allow organic flow |
| Funk-forward | 60 | 65-70 | Weirdness adds rhythmic surprise; lower SI lets funk breathe |
| Post-metal | 60-65 | 65 | Needs room for patient builds and textural exploration |
| Prog | 65-75 | 65 | Higher Weirdness encourages unexpected transitions |
| Circular / agitated | 75 | 65 | High Weirdness for unsettling, looping energy |

**Counter-genre builds** (a song pushed against its band's gravity: acoustic from a metal band, slow from a driving one) start Weirdness at 60–70, because default 50–55 quietly normalizes the song back toward the band's sound (model-prompt-strategies → "Default Weirdness Normalizes Counter-Genre Prompts"; v5.5 finding, a starting hypothesis on v6). The rows above are for songs inside their band's own lane. Exclude integrity is not a reason to start lower: lower Weirdness only after an exclude has actually failed on this song.

**General principle:** Weirdness adds unpredictability and non-obvious choices. Style Influence controls how tightly Suno follows the prompt versus doing its own thing. For conventional songs, keep SI high. For experimental work, back SI off and let Weirdness drive.
