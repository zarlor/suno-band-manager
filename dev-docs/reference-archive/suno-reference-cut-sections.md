# SUNO-REFERENCE.md — sections cut from the installed bundle

Taken out of `src/skills/suno-agent-band-manager/references/SUNO-REFERENCE.md` on 2026-11-12. The Band
Manager never hand-builds a style prompt or tags lyrics, so these two sections duplicated craft knowledge
that belongs to the `suno-style-prompt-builder` and `suno-lyric-transformer` skills. Each was replaced in
the reference by a one-line pointer to the skill. Nothing in the module loads this file; it is a record
for maintainers.

Before the cut, every bullet and table row was checked against the sibling skills' references. The first
part of this file lists the facts that were found only in the cut text. The second part keeps both
sections word for word.

## Facts found only in the cut sections

Facts 1 and 3 below were then added to `suno-lyric-transformer/references/metatag-reference.md` (Ending Control) and fact 2 to `suno-feedback-elicitor/references/technical-resolution.md` (Extend and genre drift), so none is lost from the installed skills.

Checked against `suno-style-prompt-builder/references/` (`v6-build-core.md`, `safety-tables.md`,
`model-prompt-strategies.md`, `retired-model-strategies.md`), `suno-lyric-transformer/references/`
(`metatag-reference.md`, `section-jobs.md`) and `suno-feedback-elicitor/references/technical-resolution.md`.

Not found in any sibling reference:

1. **Unscripted solos, the count and the countermeasure.** "Three of four analyzed tracks had solos not in
   the lyrics. Plan for this or use `[End]` tags to prevent post-vocal noodling." The builder's
   `model-prompt-strategies.md` keeps the observation (Suno adds unscripted guitar solos) without the count
   or the `[End]` advice.
2. **Personas with Extend.** "Personas historically cannot be used reliably with Extend — using Extend to
   keep generating with the same Persona has been unstable. Reuse exact vocal descriptor tags from the
   original prompt alongside the Persona to reinforce consistency." The siblings only say high Weirdness
   during Replace Section can shift a Persona's identity.
3. **The noodling-prevention combination.** "`[Outro] long instrumental outro, soft keys, slow fade [End]`
   — stacking both 'winding down' and 'stop here' signals is more effective than either alone." The
   transformer's catalog states the principle (`[Outro]` + `[End]` paired, neither alone does as well) but
   not this worded example line.
4. **`[Fade Out]` as a "weak signal; never use alone".** The transformer's catalog goes further (the tag
   doesn't produce a fade), so the weaker wording is superseded rather than lost.
5. **Pre-v6 inline negatives as a fallback.** "In-prompt negatives ('no [element]' at the end) also work as
   a fallback" and "'no [element]' at the end of the style prompt worked as a supplement". Superseded: on v6
   the siblings say an inline negative reads as inclusion.
6. **Exclude Styles is in Early Access Beta** "and may not be 100% reliable for all instrument exclusions".
   The beta label stays in the reference's Plan Comparison table; the siblings carry the v6 reliability
   reports instead.

Found in the sibling skills, but not in the three files the cut was first compared against
(`v6-build-core.md`, `safety-tables.md`, `metatag-reference.md`): the pre-v6 style bullets (5-8 descriptors
and the HookGenius counts, the critical zone, the Genre > Mood/Energy > Instruments > Vocals > Production
priority order, hyper-specific examples, BPM and key on v5, production descriptors, the dynamic-arc and
three-phase double-stating rules, bass-forward rock and metal, Personas anchoring to their source era,
"cinematic" as a universal quality modifier, conflicting tags, section-by-section directions being ignored,
the 2-3 exclusion limit and the 1,000-character Exclude cap) are in `model-prompt-strategies.md`; instrument
position in the prompt (early is global, last is section-leaning when an `[Instrument: ...]` tag reinforces it)
is the transformer's "Strategy 2: Style Prompt Instrument Ordering"; the Extend
toolkit (anchor note, forbidden-element phrasing, the 2-3 extension limit, Cover as a signal cleaner) is in
the feedback elicitor's `technical-resolution.md`.

---

## The cut sections, verbatim

### Style Prompt Best Practices (was a `##` section)

- **On v6, write the style prompt as ordered production direction** — each instrument's job per section, the vocal placed rather than praised, both edges stated, negatives only in Exclude Styles. PREVIEW guidance, applied by the suno-style-prompt-builder skill. The bullets below were written against the retired models; re-check each on v6.
- **1,000-character limit** (200 for v4 Pro) -- content beyond this is silently truncated. The first ~200 chars are the "critical zone" where front-loaded terms have strongest influence. Content beyond ~200 is supplementary, not wasted — v5.5 may interpret more effectively. **5-8 descriptors is the sweet spot** (HookGenius 1000+ prompt analysis, April 2026 — fewer than 4 produces generic results; exceeding 10 causes conflicting signals and quality degradation).
- **Word order is weighted** -- front-loaded terms dominate. Priority order: Genre > Mood/Energy > Instruments > Vocals > Production. Treat the first ~200 characters as the "critical zone."
- **Hyper-specific beats generic** -- "1980s synth-pop" not "pop"; "distorted electric guitar, power chords" not "guitar"
- **BPM and key in style prompt (v5)** -- may work better in v5 than in lyric tags: `deep house, 122 BPM, A minor, hypnotic groove`. Still ineffective in v4/v4.5.
- **Production descriptors (v5)** -- "radio-ready mix, punchy drums, wide stereo field, crisp high-end, warm bass" are effective in v5
- **Never put artist names in the style prompt** -- Suno does not reliably replicate named artists. Decompose into concrete sonic descriptors instead.
- **Never put sound cues, asterisks, or style descriptions inside lyrics** -- the style prompt and lyrics are separate inputs
- **Negative/exclusion prompts go in the Exclude Styles field**, not in the main style prompt. In-prompt negatives ("no [element]" at the end) also work as a fallback. On v6, Exclude itself misses some elements (see "Platform Changes — 2026-10-15").
- **Style prompt sets ONE overall mood** -- Suno does NOT actually shift tempo within a song. "Tempo change" / "tempo shift" prompts produce arrangement-density variation (instrumentation pullback for halftime feel, compression for double-time feel), not actual BPM change. Underlying tempo stays constant; felt-shift is dynamic/arrangement-driven. Use lyric density and rhythm noun metatags (`[Heavy: halftime]`, `[Double Time]`) for perceived section-level tempo changes.
- **Negative prompts are unreliable** -- "no screaming" in the style prompt often gets ignored. Use the Exclude Styles field (Pro/Premier) or translate to positive instructions ("clean singing with grit on peaks").
- **Genre keyword ordering matters** -- front-loaded terms dominate. Whatever appears first sets the primary sound. When a genre should be secondary/flavoring, use "accents" or "undertones": e.g., `atmospheric swamp metal accents`.
- **Genre words trigger specific behaviors** -- "metal" alone triggers screaming, "sludge" triggers harsh vocals, "doom" risks harsh vocals. Always pair heavy genre terms with explicit positive vocal instructions ("clean singing with grit", "raw melodic singing"). Use alternatives ("progressive heavy groove") when screaming is not desired.
- **Style prompt controls the full dynamic arc** -- `slow massive build to crushing climax` makes Suno build ALL the way through, ignoring quiet tags at the end. If the song needs to come down, the style prompt MUST acknowledge the descent: `slow build then fade`, `dynamic shifts loud to quiet`.
- **Rhythm nouns beat tempo adjectives** -- "halftime groove", "double-time driving", "shuffle", "breakbeat" lock feel better than "slow" or "fast". These describe specific drum patterns Suno can interpret.
- **Never use BPM values in style prompts or lyrics** -- BPM tags have ZERO detectable effect on Suno's output (confirmed by librosa analysis: a song tagged 60 BPM was delivered at 95.7 BPM; a song tagged 65-150 BPM across sections was delivered at a steady 123 BPM). Suno picks its own tempo. Use rhythm nouns and lyric density instead.
- **Perceived tempo is controlled through lyrical density, not BPM** -- Suno delivers a single steady BPM per song. Short fragmented lines (1-3 words) = slower perceived delivery. Long packed lines with many syllables = faster perceived delivery. Half-time/double-time drum feel (`[Heavy: halftime]`, `[Double Time]`) and arrangement density changes provide additional perceived tempo control.
- **Instrument ordering matters** -- instruments in the first ~200 chars appear globally; instruments at the end of the prompt are more section-specific when reinforced with `[Instrument: ...]` metatags in lyrics.
- **Bass-forward rock/metal is a known limitation** -- Suno cannot reliably produce bass-led sound in rock/metal context. Even "bass and drums only, no guitar" with guitar in excludes still produces guitar. "Funk metal" triggers slap/pop bass (Flea), not overdriven fingerstyle (Geddy Lee).
- **Personas anchor to their source era** -- a persona sourced from a modern song will pull "late 1970s" prompts toward a modern sound. Reduce Audio Influence to 10-15% or generate without a persona for era-specific pieces.
- **"Baroque" triggers Disney** -- do NOT use the word "baroque" in style prompts. Suno maps it to light, Disney-esque orchestration. Describe the qualities instead: `intricate interlocking guitar and bass melodies`, `dark minor key, precise and ornate`. Specify heavy orchestral instruments by name (`cello, heavy strings, kettle drums`) -- the word `orchestral` alone defaults to light/cinematic.
- **"Rock Opera" and "Cinematic" are keyboard triggers** -- both terms pull keyboard/synth arrangements into the mix. Use `power ballad`, `dynamic shifts` instead when you want drama without keyboards. **Exception:** "cinematic" is also a **universal quality modifier** — HookGenius's 1000+ prompt analysis found it consistently elevates production quality results across every tested genre. If keyboards aren't a concern, it's the single most versatile tag for enhancing output.
- **Production tags are the most underused category** — HookGenius analysis found that adding even one production descriptor ("radio-ready mix", "punchy drums", "wide stereo") meaningfully improves output distinctiveness. Most users rely only on genre + mood.
- **Conflicting tags produce bland compromise, not interesting hybrids** — "aggressive, peaceful" or similar contradictions cause Suno to default to a generic middle ground. Opposing descriptors cancel out rather than creating creative tension.
- **Three-phase dynamic arc needs double-stating** -- songs that go quiet → massive → quiet need the arc stated TWICE in the style prompt: once as a narrative description (`building from gentle to crushing then returning to gentle`) and once as a shorthand (`dynamic arc quiet to massive to quiet`). A single mention is not enough — Suno tends to flatten or ignore the return to quiet without the reinforcement.
- **Suno adds unscripted guitar solos regularly** -- three of four analyzed tracks had solos not in the lyrics. Plan for this or use [End] tags to prevent post-vocal noodling.
- **Anchor note restating during Extend** — always restate genre, mood, key, and instrument palette in a 1-2 sentence anchor note with each extension. Example: 'Keep the exact current groove, instrument palette, key, and tempo. Do not introduce new drums or leads.'
- **Forbidden element phrasing** — stating what NOT to add during Extend is more effective than positive instruction alone: 'No new hooks,' 'No new drums,' 'No new riffs,' 'no risers'
- **Limit extension chains to 2-3 maximum** — beyond that, audio quality degrades ('muddy' or 'lo-fi' artifacts). If quality degrades, use the **Cover feature** to re-synthesize the audio from scratch, effectively 'cleaning' the signal path.
- **Personas historically cannot be used reliably with Extend** — using Extend to keep generating with the same Persona has been unstable. Reuse exact vocal descriptor tags from the original prompt alongside the Persona to reinforce consistency.
- **Section-by-section instructions in style prompts are largely ignored** -- Suno delivered consistently fast, dense tracks despite detailed per-section directions (slow intro, tempo drops, sparse bridge). Style prompt sets overall mood; metatags handle sections (imperfectly).

#### Exclude Styles (Pro/Premier)

The Exclude Styles field is a dedicated exclusion input separate from the style prompt. It functions as **probability reduction** -- guidance, not a hard ban.

- Format as a **comma-separated list** for easy copy-paste: `screaming vocals, steel guitar, autotune`
- Be specific: "screaming vocals" is better than "screaming"
- **Limit to 2-3 most important exclusions** -- too many destabilizes the arrangement
- **On v6, negatives go only in this field.** Inline "no [element]" reads as inclusion, and Variety's rewrite drops "no X" phrases while Exclude survives intact (VENDOR + COMMUNITY + ANECDOTAL-controlled). *(Pre-v6: "no [element]" at the end of the style prompt worked as a supplement.)*
- Length cap: 1,000 characters (page markup, 2026-10-03)
- With Exclude Styles handling exclusions, the style prompt can focus entirely on POSITIVE instructions
- Heavier genre words ("metal", "sludge") become usable in the style prompt when the Exclude Styles field blocks their unwanted defaults
- **Note:** Exclude Styles is currently in Early Access Beta and may not be 100% reliable for all instrument exclusions

**Free tier:** No Exclude Styles field. Translate exclusion intentions into positive style prompt language -- "clean singing with grit on peaks" instead of "no screaming."

---

### Metatag Reference (was a `##` section)

> This is Mac's quick reference. The full metatag catalog (confidence levels, production findings) and the section-job framework belong to the suno-lyric-transformer skill — invoke it for lyric work rather than tagging by hand.

### Section Tags

**Only use recognized tags.** Custom tags like `[The Questions]` or `[Reflection]` are ignored or **sung as lyrics**. Map non-standard sections to recognized tags and use parameterized syntax to shape the feel.

| Tag | Job |
|-----|-----|
| `[Intro]` | Opening (unreliable -- may need regeneration) |
| `[Verse]` | Setup -- establishes story, scene, or emotion |
| `[Pre-Chorus]` | Lift -- builds tension/anticipation before chorus (2-4 lines). Creates a distinct musical moment with added percussion and vocal intensity |
| `[Chorus]` | Payoff -- the hook, the memorable part |
| `[Post-Chorus]` | Extension or cooldown after chorus. Best in pop/EDM; may blend with chorus in rock/metal |
| `[Bridge]` | Something NEW -- new chords, new melody, new perspective. Introduces harmonic content the song hasn't heard yet |
| `[Breakdown]` | Something LESS -- strips instruments, spotlights vocals or a motif. In metal, forces tempo drop and heavy rhythm. Creates maximum contrast before a high-energy section |
| `[Build-Up]` / `[Build]` | Escalation -- increases energy toward a peak |
| `[Final Chorus]` | Closing payoff -- often bigger than earlier choruses |
| `[Outro]` | Resolution -- brings the song to a close |
| `[Instrumental]` | Instrumental section -- no vocals |
| `[Instrumental Break]` | A mid-song instrumental passage, often a solo or riff. Use one at most, and keep it out of a short poem: the tag invites Suno to noodle, and several of them, or one in a short lyric, can turn the song mostly instrumental. Naming the instrument (`[Guitar Solo]`) is the tighter ask |
| `[Interlude]` | Transitional palette cleanser -- defaults instrumental, lighter treatment if lyrics provided |
| `[Solo]` / `[Guitar Solo]` | Instrumental solo section |
| `[Break]` | Brief pause or stripped-back moment. Useful as energy-bleed buffer between aggressive and clean sections |
| `[Drop]` | Sudden energy release (EDM/electronic) |
| `[Hook]` | Short catchy phrase or motif |
| `[Fade In]` | Gradual volume increase at the start. **Untested here, and no first-hand reports either way.** The dependable fade in is the editor's Fade In on a finished take (see "Fade In / Fade Out" under Platform Changes — 2026-09-09 above, and the Studio editor reference) |
| `[Fade Out]` | Gradual volume decrease — **weak signal**; never use alone, and primary-source users report it working in no configuration. Apply real fades in the editor |
| `[End]` | Signal to stop the song — place on the absolute last line, nothing beneath it |
| `[Reprise]` | A return to an earlier section, often the chorus or intro theme. Guide-sourced, untested on v6. Repeating the earlier lines under the tag tells Suno what is coming back; a cue (`[Reprise: quieter]`) can set how |
| `[Coda]` | An extended ending or **epilogue** section. This can prompt Suno to add a concluding musical phase beyond the last chorus/outro. Guide-sourced, untested on v6. Use it when the song wants a longer close, not to stop one: an ending that plays out a conclusion is what buys the long tail (see the ending recipes in the lyric transformer's `metatag-reference.md`). Pair with `[End]` and expect to crop |

**Bridge vs Breakdown:** Bridge gives you something NEW (new chords, perspective). Breakdown gives you LESS (strips arrangement). Need both? Use `[Bridge | Half-Time]` + `[Energy: stripped, minimal]`.

### Dual Voices — Known Limitation

Suno v5/v5.5 cannot reliably produce two genuinely distinct male voices trading lines in a single generation. `[Duet]`, voice numbering tags (`[Voice 1]`/`[Voice 2]`), and descriptive "dual male vocals trading" in the style prompt all fail to produce true voice separation — you get doubling, harmonizing, or one voice averaged from the descriptors. Personas actively lock single-voice consistency (that's their design purpose).

**Workarounds for songs that need distinct dual voices:**
1. **Persona OFF is mandatory** — rebuild the band sound from scratch in the style prompt
2. **Multi-stage Studio Replace Section** — generate with main voice only, Replace Section each intrusive part with different vocal character prompts (most reliable)
3. **Nu-metal/rapcore framing** — Mr. Bungle / System of a Down / Mike Patton territory tolerates rapid vocal-character shifts. Best aesthetic match for "manic/unhinged" intrusive characters
4. **Metalcore clean/harsh** — `[Clean Vocal]` / `[Harsh Vocal]` contrast works but produces scream not manic speech
5. **Lead + Adlibs** — main voice dominant, intrusive voice as 3-6 word interjections max with `[adlibs: ...]` tags

**Gender contrast is the easiest path** — `[Male]`/`[Female]` per-line is the only reliably working duet technique. Same-gender dual voicing is the hardest case. For songs that genuinely need male/male dual distinct voices, plan for multi-stage Studio workflow from the start.

The suno-lyric-transformer skill holds the full workarounds, ranked by reliability, and applies them when it transforms a duet.

### Parameterized Section Tags

Section tags can include per-section arrangement instructions using colon or pipe syntax:

- `[Verse: whispered vocals, acoustic guitar only]`
- `[Chorus: full band, powerful vocals]`
- `[Bridge: stripped back, piano only]`
- `[Chorus | Half-Time]`

This allows section-specific arrangement control directly in the tag itself, rather than relying solely on separate descriptor tags.

### Descriptor Tags

`[Mood: ...]`, `[Energy: ...]`, `[Vocal Style: ...]`, `[Instrument: ...]`

### Key Rules

- Keep metatag text short: 1-3 words
- Tags at the **top** of lyrics are global; tags **right before** a section are local (and more effective)
- Blank lines between sections improve parsing
- Consistent line lengths and syllable counts improve vocal phrasing stability
- Short repeated hooks sing better than long novel choruses
- Commas create breath pauses; dashes create sharp breaks; ellipses create trailing delivery
- Suno lyrics field has a hard limit of **5,000 characters** on v4.5+/v5/v5.5 (3,000 on v4). Silently truncated beyond the limit. **Quality budget: ~3,000 chars** — beyond this, Suno may rush through sections or cut content. Treat 3,000 as the practical working ceiling. (Like the style-prompt limits, these figures are community-attested — **no official Suno article documents them**, and community reports of the v4-vs-v5 split are inconsistent. Enforce them; don't cite them as documented.)

### Formatting as Suno Controls

- `!` (exclamation) = bark/attack trigger -- bleeds forward into subsequent sections. Avoid in clean/quiet sections.
- ALL CAPS = loudness ceiling -- save for the absolute peak moment only
- `(parentheses)` = backing vocals/texture, not lead melody
- Short lines (1-3 words) = slower delivery; long packed lines = faster delivery (PRIMARY tempo control — more reliable than any tag or slider). Line breaks act as breath points: more breaks = slower feel, fewer breaks = faster feel.
- Half-time / double-time drum feel via metatags (`[Heavy: halftime]`, `[Double Time]`) creates perceived tempo shifts without actual BPM change
- **BPM tags are confirmed ineffective** — do not use `[Verse: 65 BPM]` or similar tags. They have zero effect on output (librosa-confirmed).
- `[Instrument: ...]` before a section specifies instruments for that section -- use to crowd out unwanted instruments rather than trying to exclude them
- `[Soft End]`, `[Dramatic End]`, `[Instrumental End]` — ending style variants
- `[Slow Fade Out]`, `[Fast Fade Out]`, `[Instrumental Fade Out]`, `[Cinematic Fade Out]` — fade style variants (genre-specific: Slow for ambient/cinematic, Fast for dance/shortform, Instrumental for pop, Cinematic for orchestral)
- **Noodling-prevention combo**: `[Outro] long instrumental outro, soft keys, slow fade [End]` — stacking both 'winding down' and 'stop here' signals is more effective than either alone
