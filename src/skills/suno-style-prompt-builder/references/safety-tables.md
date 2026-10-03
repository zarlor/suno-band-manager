# Safety Tables — Reload Before Every Build and Refine

These are the load-bearing gotchas for style-prompt building, gathered in one short file so they can be reread before every build and every refine generation. A long session or refine loop can compact them out of context, and a prompt built from memory of them can ship "metal" without a vocal pairing, a keyboard-pulling word, a crowd-noise word, an exclude that defends against nothing, or a slider anchored to a profile default. `scripts/validate-prompt.py` flags the enumerable words; the substitution and every judgment call come from here.

Everything else — v6 prompt architecture, sliders beyond the song-type table, Voices, Personas, counter-genre technique — lives in `references/model-prompt-strategies.md`.

## Vocal Triggers

### Scream/Harsh Vocal Triggers

Certain words reliably trigger unwanted screaming or harsh vocals, even when the intent is melodic:

- `metal` on its own (without melodic vocal guidance)
- `sludge`
- `doom`
- `!` in lyrics (exclamation marks push vocal delivery toward shouting/screaming)

**Fix:** Always pair heavy genre terms with explicit positive vocal instructions. For example, `heavy swamp metal, raw melodic singing` or `sludge metal, gritty male vocals` (plus "screaming" in Exclude Styles — on v6 the negative goes only there, never inline). Telling Suno what you DO want from the vocals is more reliable than only excluding what you don't.

### The "live" Word Family Triggers Crowd Noise (LOCAL-CONFIRMED, recurring)

 Module production testing has hit this repeatedly on v5.5: **any** form of the word — `live-band drums`, `live recording`, `live energy`, `live in the room` — pulls audience-noise rendering, crowd texture, and crowd-vocal bleed, even when the intent is plainly band-in-a-room performance energy rather than a concert. The word appears to carry "live album" as its dominant training association, and a single instance is enough. The v5-era descriptor-effects table (in `references/model-prompt-strategies.md`) used to recommend `raw live recording` as a production descriptor; that recommendation was wrong and has been replaced.

**Say the quality, not the venue.** `unpolished room sound`, `natural room ambience`, `single-take band performance`, `minimal overdubs`, `dry close-mic drums with room bleed` all get the intended texture without the word. External sources do not list "live" among crowd-risk terms — this is our own finding, and it is one of the more reliable ones we have.

### Crowd, Choir, and Extra-Vocal Avoidance

When the song needs **one singer** and nothing else, three layers work together. Any one alone leaks.

1. **Positive solo-singer language in the style prompt** — "solo lead vocal, one singer only," and where the energy is supposed to come from instead: "chorus energy from instruments and arrangement, not extra voices." Filling the role is stronger than forbidding the filler.
2. **Excludes covering the whole family** — `choir, backing vocals, gang vocals, layered vocals, crowd chants`. Excluding "choir" alone leaves gang vocals and stacked doubles untouched; they are different arrangement conventions and Suno reaches for whichever one the genre suggests.
3. **Avoid the trigger words entirely** — `anthemic`, `festival`, `stadium`, `crowd`, and **the whole "live" family** (see the section above) invite group vocals and audience texture by association. Excludes cannot reliably override a prompt that is asking for group energy in its adjectives.

The lyric side of this stack — section-tag wording that invites choirs, and the anti-choir tag forms — lives in `suno-lyric-transformer/references/metatag-reference.md`.

## Arrangement Triggers

### Dangerous Words and Keyboard Triggers

Certain words reliably pull Suno into unwanted instrumental territory — typically theatrical, keyboard/synth-heavy, or cinematic-light arrangements. Avoid these when guitars and bass should lead.

| Word/Phrase | What Suno Does | Fix |
|---|---|---|
| `baroque` | Maps to theatrical/classical keyboard territory — Disney-adjacent | Describe Baroque qualities without the word: Bach counterpoint = `intricate interlocking guitar and bass melodies`; minor key ornamentation = `dark minor key, precise and ornate` |
| `orchestral`, `orchestral accents` | Defaults to light/cinematic strings, not heavy | Specify HEAVY orchestral instruments explicitly: `cello, heavy strings, kettle drums` — these live in metal's frequency range |
| `cinematic` | Pulls keyboard/synth-heavy arrangements | Use `dynamic shifts`, `building from gentle to crushing` instead |
| `rock opera` | Pulls keyboard/synth-heavy, theatrical arrangements | Use `power ballad`, `dynamic shifts`, `building from gentle to crushing` instead |
| `big`, `emotional`, `epic` as the **chorus** instruction (v6) | Rock and metal choruses reported slowing into a dramatic ballad (COMMUNITY, 2026-10-03 sweep) | Write the chorus's job: `choruses stay rhythmically driving and hit harder than the verses`. Where a heavy chorus has to hit |

**"Baroque" workaround in detail:** If the song concept calls for Baroque-influenced metal, never use the word. Instead, describe the specific qualities you want — `intricate interlocking guitar and bass melodies` for counterpoint, `dark minor key, precise and ornate` for ornamentation. For orchestral weight, specify instruments that live in metal's frequency range: `cello, heavy strings, kettle drums`. Avoid `orchestral` as a standalone descriptor.

### Genre Term Behavior Table

Specific genre terms produce specific results. This table documents what Suno actually generates for common genre keywords, based on production testing.

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
| `crushing slow heavy swamp metal` + `pounding heartbeat kick drum` | Heavy, deliberate, single-tempo weight | Stacking slow/heavy modifiers locks Suno into a plodding pace |
| `prog rock` + `slow build then fade` | Atmospheric with proper decrescendo | One of the few reliable ways to get Suno to actually come back down |
| `Acoustic, intimate, solo voice with gentle guitar, bluesy, swampy, sparse and warm, quiet reflection, raw clean vocals, stripped down, empty room atmosphere` | Acoustic track that retains band identity | `bluesy, swampy` keeps NOLA identity; `empty room atmosphere` = reverb/space; explicitly exclude `heavy guitars, drums` in Exclude Styles |
| `heartland rock` | Accessible mid-tempo rock with Petty/Mellencamp/Springsteen character — chimey or mid-gain driven electric guitars, rock-forward without metal weight | **Safe rock term for Voice tracks** — no harsh vocal trigger. Good starting point when a clean-voice Voice clone needs rock energy without metal pull |
| `southern rock` | Rootsy rock with Allman/Skynyrd character — can pull slide/steel guitar as a byproduct of the genre association | Safe vocal-wise (no harsh-vocal triggers). Exclude `steel guitar` if you want to avoid the slide side. Pairs well with `heartland` to anchor toward the accessible end rather than jam-band end |
| `heartland southern rock` | Combined — intersection of accessible singer-songwriter rock with rootsy grit and drive | **Validated on Voice tracks** — clean folk-tagged Voice with "overdriven rhythm guitar with crunch" + "driving mid-tempo rock groove" as reinforcement produces rock presence without metal pull. Good for confessional rock songs that need both weight and accessibility |

## Exclude Styles

### Excludes Defend Against Drift From the CURRENT Prompt ONLY

**Suno is stateless. It has zero knowledge of:**
- Prior generations of this song (regen iterations, earlier versions, previous Creates)
- Other bands' renderings of the same lyrics (e.g. if the user keeps both a metal-lane version and a folk-lane version of the same poem, Suno generating one knows nothing about the other)
- The user's broader catalog, band profiles, genre lanes, or historical patterns
- Any context that isn't in the style prompt, Exclude Styles, lyrics, sliders, voice selection, or persona/audio input for this specific generation

**The ONLY inputs that influence Suno's output are the ones submitted with the current Create.** The Exclude Styles list should defend against drift risks that the CURRENT style prompt's own descriptors might introduce. Nothing else.

**Common violations to avoid when building exclusion lists:**

- ❌ "Defend against the metal band's DNA drifting into this folk version" — Suno doesn't know the metal version exists. If metal-coded words aren't in the folk style prompt, metal won't creep in from the parallel rendering.
- ❌ "The earlier generation drifted toward X, so exclude X in the next attempt" — Suno doesn't remember prior generations. If the current prompt still contains descriptors that pull toward X, excluding X is valid. If the current prompt doesn't contain those descriptors, the exclusion is defending against a ghost.
- ❌ "The user's Band A catalog never uses instrument Y, so exclude Y on Band B's version of this song" — Suno doesn't know about Band A. Only exclude Y if the CURRENT prompt might pull it in.

**Genre defaults count as a pull from the current prompt.** For example, v6 is reported to add unrequested key changes in some genres (ANECDOTAL, 2026-10-03). So `key change` in Exclude passes this test when the song has to hold its key: the genre named in this prompt is the pull. Leave it out where a modulation would be welcome.

**The correct question for every exclude candidate:** *"What in my current style prompt could plausibly pull Suno toward this element?"* If the answer is "nothing in this prompt pulls that way," the exclude is wasted exclusion-field budget.

**Parallel-band-rendering work is the highest-risk context for this error.** When a song exists in two band catalogs (same poem, different genre/voice rendering), the temptation is to frame excludes as "defense against the other band's version." That framing is always wrong — Suno cannot be influenced by a version it has no knowledge of. Build excludes fresh for each rendering based on that specific prompt's descriptors.

## Sliders

### Weirdness and Style Influence by Song Type

These are starting-point ranges based on production testing. Adjust per song, but these give a reliable baseline.

**Do NOT anchor slider values to a band profile's stored `sliders:` defaults, nor to "what similar catalog songs used."** A band profile's stored slider values (if present) are not a baseline to nudge up or down from — not even for a quick Demo. For every song, CHOOSE Weirdness and Style Influence fresh from this table + the song's type + counter-genre needs, reasoning from what each slider actually DOES. **The sliders are the deliberate per-song differentiator** — the mechanism for giving distinct feels to songs whose prompts are otherwise similar — so each is a fresh per-song decision, never a band default. (Audio Influence follows its slot instead: a Persona and a Voice have different ranges — see "Audio Influence Slider Behavior" and "Voices" in `references/model-prompt-strategies.md`.) The user directive behind this rule: `docs/mac-preferences.md` → "USE the sliders." A documented failure (2026-06-07): the builder recommended Weirdness 55 by anchoring "above the profile's 45 default" instead of reasoning from behavior — for a dissonant/locked/counter-genre song that actually wanted ~75.

| Song Type | Weirdness | Style Influence | Notes |
|---|---|---|---|
| Acoustic/stripped | 40 | 80 | Lower Weirdness for compliance; high SI to honor the style prompt's genre descriptors |
| Structured songs (verse-chorus) | 50-55 | 75-80 | Higher Style Influence keeps structure tight |
| Dark alternative | 50-55 | 75-80 | Standard settings; may need lower Weirdness for compliance when pushing a metal band into non-metal territory |
| Through-composed | 55-60 | 70-75 | Slightly looser to allow organic flow |
| Funk-forward | 60 | 65-70 | Weirdness adds rhythmic surprise; lower SI lets funk breathe |
| Post-metal | 60-65 | 65 | Needs room for patient builds and textural exploration |
| Prog | 65-75 | 65 | Higher Weirdness encourages unexpected transitions |
| Circular / agitated | 75 | 65 | High Weirdness for unsettling, looping energy |

**General principle:** Weirdness adds unpredictability and non-obvious choices. Style Influence controls how tightly Suno follows the prompt versus doing its own thing. For conventional songs, keep SI high. For experimental work, back SI off and let Weirdness drive.
