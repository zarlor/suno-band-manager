# Suno Platform Reference

Quick-reference for Suno models, plans, parameters, metatags, and common pitfalls. This is a companion to the [Usage Guide](./USAGE.md) (how to use Mac), the [Studio & Editor Reference](../../_shared/references/STUDIO-EDITOR-REFERENCE.md) (post-generation editing tools), and covers *how Suno works* for generation.

> **Platform state as of 2026-08-13.** Four things changed since this file was last validated, and all four change advice rather than just facts: **(1) downloads are capped from 2026-09-03** and commercial rights now attach to the download rather than the subscription; **(2) all current models are slated for retirement** with no versions or dates published; **(3) Studio 2.0** shipped, Premier-only, and the Studio 1.x feature names are archived; **(4) a Duration slider** landed on web for v5.5. Details in "Platform Changes — 2026-08-13" below. Verify anything time-sensitive against [suno.com/release-notes](https://suno.com/release-notes) before telling a user.

---

## Model Comparison

| Model | Style | Character Limit | Best For | Tier |
|-------|-------|----------------|----------|------|
| **v4.5-all** | Conversational descriptions | 1,000 | Free users, heavier/faster genres, longer songs (~8 min) | Free |
| **v4 Pro** | Simple descriptors | 200 | Straightforward, shorter prompts | Paid |
| **v4.5 Pro** | Conversational descriptions | 1,000 | Intelligent prompts, narrative style | Paid |
| **v4.5+ Pro** | Conversational descriptions | 1,000 | Advanced creation methods | Paid |
| **v5 Pro** | Crisp film-brief (5-8 descriptors) | 1,000 | Authentic vocals, superior audio quality, section editing | Paid |
| **v5.5 Pro** | Crisp film-brief (5-8 descriptors) | 1,000 | Most expressive model, better subtle descriptor handling, Voices, Custom Models, My Taste | Paid |

**Character limit details** (community-attested, **not** officially documented — a full review of help.suno.com on 2026-08-13 found no Suno article stating these numbers, and nothing official contradicting them either; keep enforcing them, don't cite them as platform documentation):
- **v4 Pro:** 200 chars (hard limit, silently truncated)
- **v4.5+ / v5 / v5.5:** 1,000 chars. Front-loaded terms dominate -- the first ~200 chars are the "critical zone" with strongest influence on generation. Content beyond ~200 chars is supplementary but not wasted; v5.5's improved descriptor interpretation may extend the effective window. 5-8 descriptors is the sweet spot.

**Key differences:**
- **v4.5-all** wants flowing, conversational sentences. Example: "Create a melodic, emotional deep house song with organic textures and hypnotic rhythms."
- **v5 Pro** wants crisp descriptors and emotional language over technical. Example: "raw indie folk, yearning vocals, acoustic guitar, lo-fi tape warmth, intimate"
- **v4 Pro** has a hard 200-character limit, not 1,000.

**v5-specific behaviors:**
- Full negative prompting support (v4.5 had limited support)
- Better BPM and key recognition in style prompt (e.g., `deep house, 122 BPM, A minor`)
- Production-quality descriptors more effective (e.g., "radio-ready mix, punchy drums, wide stereo field")
- Composition-aware architecture -- uses early style/genre info for coherent section transitions
- Existing v4 prompts often work "even better" on v5

**v5.5-specific behaviors (additive update over v5):**
- Same audio engine, metatags, and character limits as v5 -- all v5 prompts work identically, often with better results
- 48kHz sample rate, up to 8 min generation, internal codename "chirp-fenix" (v5 was "chirp-crow")
- Most expressive model yet -- better at interpreting subtle and nuanced descriptors
- More varied output per generation -- each Create produces 2 songs; 2-3 Creates (20-30 credits) gives 4-6 takes to pick from
- v5.5-optimized prompts can be more specific: "deep sub 808s, glitchy hi-hat rolls, pitched vocal chops" where v5 would use simpler "808s, hi-hats"
- **Voices** (a distinct feature alongside Personas — Personas were **not** removed, they live inside the Voices menu): actual voice cloning with anti-deepfake verification, 15s-4min audio sample required. Clone creation and use are Pro/Premier; since 2026-08-07 the feature is on iOS and Android and "available to try on free plans," with more on paid plans — the free/paid line is not documented, so check the live UI rather than promising a free user what they can do. **Skill Level dropdown** (Beginner/Intermediate/Advanced/Professional) actively reshapes how the model interprets your voice — always select **Professional** regardless of actual ability for the most stable, usable results.
- **Custom Models**: train on 6+ original tracks, 2-5 min training time, up to 3 custom models. Pro/Premier only. **Privacy/consent note (AudioNewsRoom):** consent grants Suno permission to use your data for training their global models — not optional, not a private silo.
  - **Training data:** WAV at 44.1kHz preferred (Suno auto-normalizes with RMS leveling, DC offset removal, spectral masking, onset detection, key/scale estimation). 8-12 stylistically consistent tracks is the inferred sweet spot. Dynamic range preservation matters more than loudness since the system normalizes internally.
  - **Overfitting risk:** Training data too narrow/homogeneous produces repetitive output. Include variety within your style lane — different tempos, moods, arrangements.
  - **Prompt strategy shift with Custom Models:** Priority order changes from genre-first to **mood/production-first** since genre is already encoded in the model. Simpler natural-language prompts may outperform tag-heavy prompts because the model handles the foundational style. Core formula: MOOD + PRODUCTION TEXTURE + ENERGY/TEMPO + INSTRUMENTS + VOCAL DIRECTION.
- **My Taste**: passive personalization that shapes generation defaults based on your listening/generation history. All tiers. Takes 20-30 generations to settle. The **pencil-and-stars button** on the Styles field (hover: "Personalize style prompt to match your taste") triggers Style Augmentation — it **pre-fills the Styles field with ordinary editable text** derived from your My Taste profile (verified in live UI (Pro account, 2026-08-14)), so the user can rewrite any of it before generating. Detailed manual prompts always override it, and the wand is a drafting shortcut rather than a hidden generation-time layer. Can be viewed, edited, or disabled from avatar menu > "My Taste." No documented reset mechanism beyond disable/re-enable.
- **Workflow paradigm shift:** v5.5 encourages generate -> inspect -> replace sections -> refine (not regenerate from scratch)

**v5.5 Personalization Stack** (layers from broadest to most specific):
1. **My Taste** -- shapes generation defaults passively
2. **Custom Model** -- sets production DNA and sonic identity
3. **Voice** -- applies a specific vocal tone and character
4. **Prompt** -- steers the specific song (always the most important layer)

---

## Plan Comparison

| Feature | Free ($0) | Pro ($8/mo displayed) | Premier ($24/mo displayed) |
|---------|-----------|---------------------|--------------------------|
| **Model access** | v4.5-all only | v5.5 + legacy v4/v4.5/v4.5+/v5 | Same as Pro |
| **Credits** | 50/day (~10 songs) | 2,500/mo (~500 songs) | 10,000/mo (~2,000 songs) |
| **Credit cost** | 10 credits per Create (produces 2 songs) | Same | Same |
| **Song downloads** (from 2026-09-03) | 7 lifetime trial downloads | 20/month | 60/month, Studio exports exempt |
| **Commercial use** | No | Yes — only for outputs obtained as a permitted download | Same as Pro |
| **Weirdness slider** | No | Yes (0-100) | Yes (0-100) |
| **Style Influence slider** | No | Yes (0-100) | Yes (0-100) |
| **Audio Influence slider** | No | Yes (0-100, with Persona or audio upload) | Yes (0-100, with Persona or audio upload) |
| **Exclude Styles field** | No | Yes (Early Access Beta) | Yes (Early Access Beta) |
| **Inspo** | No | Yes (v4.5+ Pro) | Yes |
| **Song Editor / Legacy Editor** | No | Yes (section replace, rearrange, crop, fade) | Yes |
| **Personas** | No | Yes (v4.5/v5/v5.5 — inside the Voices menu, not removed) | Same |
| **Voices** | No | Yes (v5.5 cloning; recording entry point now also on free) | Same |
| **Custom Models** | No | Yes (up to 3) | Yes (up to 3) |
| **My Taste** | Yes (passive) | Yes (passive) | Yes (passive) |
| **Stem separation** | No | Auto Split (up to 12, 50 cr), Split from Mix (20 cr) | + Advanced Split (~100 instruments, Premier only) |
| **Audio upload** | 8 min | 30 min | 30 min |
| **Add Vocals/Instrumental** | No | Yes | Yes |
| **Studio 2.0** | No | **No** | Yes |
| **Queue** | Shared | Priority | Priority, 10 concurrent |
| **Add-on credits** | No | Yes | Yes |

**Pricing display:** the pricing page shows $8 / $24 with a "Monthly / Annual save 20%" toggle, while press consistently reports $10 / $30 month-to-month. The likely reading is annual-vs-monthly, but two fetches on 2026-08-13 did not confirm it — quote the displayed figure and the toggle, don't assert a single monthly price.

**Credit model:** Every press of the Create button costs **10 credits** and produces **2 songs** (a pair to choose from — Suno always generates two takes for variety). This means: 50 credits/day = 5 Creates = 10 songs to evaluate. 2,500 credits/mo = 250 Creates = 500 songs. When budgeting credits for a session, count in **Creates (10 credits each)**, not individual songs. Replace Section and Extend also cost credits (amount varies by section length). **When daily credits run low:** Suno provides 50 bonus credits per day on all tiers, refreshing daily.

Free-tier "More Options" includes: Vocal Gender, Manual/Auto Lyrics mode, Song Title only.

Pro/Premier "More Options" additionally includes: Weirdness slider, Style Influence slider, Audio Influence slider (with Persona or audio upload), Exclude Styles, Personas, Inspo, and the Legacy Editor for section-level editing.

**Vocal consistency across songs:** Suno interprets the same style prompt differently on every generation. Descriptive prompt language (e.g., "breathy female vocal with indie folk phrasing") gets you in the right neighborhood but not an exact match. The **Persona** feature (Pro/Premier) is the only reliable way to lock in a consistent vocal identity across songs -- it reuses the vocal character from a source generation. If you are working on an album or project where songs need to sound like the same singer, Personas are essential.

**Voices (v5.5) — alongside Personas, not instead of them:** In v5.5, the **Voices** feature is the stronger tool for vocal consistency. Key differences: Voices is actual voice cloning (from a 15s-4min audio sample with anti-deepfake verification), while Personas was style essence capture from a source generation. **Style Personas are NOT gone** — they are integrated into the Voices tab in v5.5; the button changed but both features coexist. Personas still work on v4.5/v5/v5.5. Pro/Premier only.

**Voices Skill Level dropdown:** When setting up a Voice, you select Beginner, Intermediate, Advanced, or Professional. This is **NOT cosmetic** — it actively reshapes how the model interprets your voice. Testing found Professional produced the most stable, consistent, most usable results across every test. **Always set to Professional** regardless of actual singing ability.

**Voices limitations:** Voices is directional influence, not true vocal reproduction — the output drifts across generations and lacks true identity consistency (JG BeatsLab testing). Realistic for demo vocals, pre-production emotional direction, and hearing yourself in new compositions. **Not suitable for** final release vocal identity branding, or spoken word/narration (Voices drifts toward singing patterns, inconsistent tone between sections, unnatural pacing in longer spoken passages — Suno remains music-first).

**Audio Influence — two different slider behaviors depending on what is loaded.** The **Persona** slot has a narrow effective range (**15-25%**, 25% default); the **Voice** slot runs much higher and is goal-dependent. Start a Voice around **50%** and iterate in 5-10% increments.

Community testing (JG BeatsLab, March 2026) puts diminishing returns past ~70%, but that is **general guidance, not a ceiling** — Suno's own escalation for a clone that doesn't sound right is to *raise* Audio Influence first and rebuild the profile from a clean acapella second, and module production profiling of one voice found clean results at 85% where 55% showed artifacts. Profile per voice.

**The full table, the official escalation path, the local per-voice finding, and the intent-split values (70+ to preserve source character, 80 to stop invented intros on covers, 50+ to stop invented lyrics, 30-40 to let a strong style prompt through) live in one place — `suno-style-prompt-builder/references/model-prompt-strategies.md` → "Voices". Do not restate ranges from memory; read that section.**

---

## Platform Changes — 2026-08-13

Everything in this section is OFFICIAL unless graded otherwise. Confidence grades follow the module convention: OFFICIAL = Suno-documented, COMMUNITY = multi-source replicated, ANECDOTAL = single source.

### Downloads are capped from 2026-09-03 — and that changes the workflow, not just the plan

Sources: [Download limits FAQ](https://help.suno.com/en/articles/13614785), [ToS update blog](https://suno.com/blog/suno-updates-tos) (2026-08-10), [Terms effective Sept 3 2026](https://suno.com/terms-september-2026).

- Free: **7 lifetime** trial downloads, personal and non-commercial, no reset. Pro: **20/month**. Premier: **60/month**. Allowances reset on the billing date with **no carryover**; extra downloads are purchasable. **Studio exports are exempt** (Premier).
- **Retroactive to the entire back catalogue** — the cap applies to songs made before September 3 too.
- One song counts once regardless of format or repeat downloads; **all stems of a song are part of that song's single download**; failed downloads don't count. Streaming and on-platform sharing stay unlimited.
- **Commercial rights now attach to the download, not the tier.** The new ToS permits commercial exploitation only of outputs obtained through a permitted download; obtaining a copy any other way is prohibited, and so is removing or obscuring fingerprints, watermarks, or metadata. Downloaded outputs keep perpetual commercial rights even after a downgrade.
- **Remixes are jointly owned and non-commercial on every tier** — "a joint work owned jointly and equally by you and the Remixer," for "personal and non-commercial purposes" only.

**What Mac should do differently:** treat downloads as a budget the user spends, not a free action at the end. Selection moves *before* download — audition takes on-platform, then download the keeper. Say so plainly when a user is on Pro and iterating hard: twenty a month goes fast when a song takes four Creates. Don't suggest downloading every take "just in case." And never suggest anything that strips or defeats watermarking or fingerprinting — that is a ToS violation as of September 3, regardless of how it is framed.

### All current models are slated for retirement — versions and dates are NOT published

Sources: same as above, plus [BMG partnership](https://suno.com/blog/suno-partnership-bmg) (2026-08-12).

- "New models launching soon will retire older versions." Retiring means you can no longer generate *new* songs with that model; existing songs stay playable and shareable exactly as they are.
- **No official source names which versions or when.** Third-party outlets claim v3.5/v4/v4.5/v5 are going; that is not confirmed — do not repeat it as fact.
- **Extends, Covers, and remixes of existing songs will run on the NEW models** — "results may sound different from the original generation." Flag this to a user planning to Extend or Cover an older catalog track.
- The successor is "our first music model developed with the music industry" (BMG global deal). No name, date, or tier gating announced.
- **VERIFIED-ABSENT: nothing official says what happens to Voices, Custom Models, or Style Personas built on retired models.** The FAQ is silent. If a user asks whether their Voice survives, the honest answer is that Suno hasn't said — and that the band profile's recorded recipe (source song, model version, settings) is what makes a rebuild possible if it doesn't.
- **Suno's own "Model Information" help category is stale** — articles from Sept 2025 still call V4 "the latest model." Do not cite it as current: [help.suno.com/en/categories/1752193](https://help.suno.com/en/categories/1752193).

### Studio 2.0 (2026-08-13, Premier-only)

Studio was "totally overhauled": MIDI import/record/edit with piano roll and audio-to-MIDI, MIDI-as-prompt, a session-aware chat bar that generates instruments, vocals, and custom plugins, a wavetable synth, audio effects including sidechain compression and convolution reverb, automation curves, and 32-bit/48kHz multitrack export. **Nothing in Studio 2.0 reaches Pro.** The Studio 1.x feature names (Warp Markers, Remove FX, Alternates, EQ, Context Window, Sounds Mode, Stem Cover, Heal Edits, MILO-1080) are **not in current official copy** — Suno moved those articles into a "Studio Archive." No community field-testing exists yet. Full detail: [STUDIO-EDITOR-REFERENCE.md](../../_shared/references/STUDIO-EDITOR-REFERENCE.md).

**VERIFIED-ABSENT:** nothing states that Studio 2.0 replaces or deprecates the Song Editor / Legacy Editor. Replace Section is documented live at Pro today. Assume coexistence.

### Duration slider (2026-07-20, web, v5.5 only)

A Duration slider in the web Create form sets target song length. Suno published no range, but the endpoints — **10 seconds to 6:00** — are verified in live UI (Pro account, 2026-08-14); the 5-second step granularity is COMMUNITY-attested and unverified. Pre-generation only, **and it requires Style set to Custom**. Characteristic failures run in both directions: a hard cutoff at the target; rushed delivery or skipped sections on short targets (the model bends BPM and crams syllables to hit the number); and on long targets a **premature end followed by a restart** rather than trailing silence. **Adherence is inconsistent and the reports are starkly split** — one controlled batch matched 4 of 40, other users report near-perfect adherence, and nobody has explained the variance. It is worst on covers, remixes, extends, and custom models. Recommended handling: run **Auto** first to find the natural length, then set Custom at natural **+10-15s**, and always pair it with an explicit `[Outro]`. The "How long will my song be?" help article was not updated and still documents only Extend and the ~8-minute cap. See `suno-style-prompt-builder/references/model-prompt-strategies.md` → "Duration Slider."

### Lyricist (shipped 2026-07-09) — present at Pro; free-tier gating still UNVERIFIED

"A Persona for words": paste lyrics you own, save them as a named profile, apply that profile to new drafts. It captures tone, phrasing, and themes — **not** vocal delivery or production. It shipped with the lyrics-editor overhaul (natural-language editing, rhyme/rephrase highlighting, variations and references, full-screen editor, structure labels, autosave). COMMUNITY.

- **Present at Pro** — verified in live UI (Pro account, 2026-08-14). **Where to find it:** song-creation view → the lyrics panel → **"Help me write lyrics"** → the chat helper's **"+" quick-add items** → **"+Lyricist"**, which opens the Lyricist pop-up. It is a sub-feature *inside the lyrics chat helper*, not a standalone surface — worth saying explicitly, because a user hunting for a top-level "Lyricist" button will not find one.
- **Free-tier gating remains unverified.** No official or community source states which tiers get Lyricist, and observation at Pro says nothing about Free. The only pricing-page signal is Free = "Standard features only" vs Pro = "Standard + Pro features (personas and advanced editing)." **Do not tell a free-tier user whether they have it.**
- **Open question that matters for our writer-voice work:** nobody has published whether Lyricist copies source phrasing or abstracts the writing style. That distinction is the whole question for a user whose band profile already carries a writer-voice analysis — an abstraction layer would complement it, a phrasing-copier would compete with hand-written lyrics. Unanswered; do not assume.
- Rights caveat (ANECDOTAL): build Lyricist profiles only from lyrics you own.
- No updates since launch as of 2026-08-13, and a primary-source pass on 2026-08-14 found **near-zero community discussion** of it. That is a data point about adoption, not about existence — Lyricist is officially documented and shipped; almost nobody is talking about it. (One research pass in this sweep mistakenly concluded from that silence that the feature does not exist. It does. Absence of discussion is not absence of feature.)
- **Adjacent finding from the same discussions (COMMUNITY):** users report that **lyrics dominate the output more than the style prompt does** — "that's why it's essential to write your own lyrics." Consistent with everything in this module about lyric-side control being the stronger lever.

### Watermarking, guidelines, and the artist-name rule

- **Watermarking and fingerprinting are rolling out**, alongside transparency tools and screening partners (Audible Magic, Musixmatch). Source: [Building the future of music responsibly](https://suno.com/blog/building-the-future-of-music-responsibly) (2026-08-06). Removing or obscuring them violates the Sept 3 ToS. Tooling that claims to strip provenance marking exists and circulates in stem-workflow content; it is **not** a recommendation and Mac should never route a user to it.
- **Community Guidelines updated 2026-08-06** with explicit prohibitions on reproducing existing songs, using a real person's voice or likeness without permission, deceptive audio presented as real, and scams/spam/fake engagement/ban evasion. Stage names remain allowed. [Community Guidelines](https://suno.com/community-guidelines).
- **The artist-name guardrail is now officially backed:** "We have never allowed prompts for specific artists or copyrighted songs"; artist names are removed from prompts and redirected "toward descriptive musical characteristics," and are excluded from training metadata. Our rule was already right — now it has a citation, and the reason is stronger than "it doesn't work well": the name is stripped and the characters are wasted.

### Five identity layers now exist

Style Persona, Voice, Lyricist, Custom Model, and My Taste are five distinct identity layers, and **stacking them creates conflict rather than control** (ANECDOTAL, single authoritative source rebuilt 2026-08-01). Practical reading for Mac, consistent with the one-variable-at-a-time rule: decide which layer carries the identity for this song, and leave the others out of the decision. Recording the full recipe — source song, model version, settings — is what makes any of them reproducible later, which is exactly what a band profile is for.

**My Taste is the always-on layer — but it CAN be turned off** (COMMUNITY, primary-source verified 2026-08-14). It is built from history, likes, and skips, bites after roughly 20-30 generations, and shapes defaults and "subtle generation tendencies" on all tiers. Suno's stated boundary is that it "influences defaults, not your explicit prompts. A detailed style prompt always overrides My Taste preferences."

Three user-verified counteractions: **delete individual entries**, **deactivate the feature**, and **write `...` into the taste board**. The controls live in the **desktop browser only** — expand the nav, three dots, My Taste. **The magic wand has a separate toggle** to disregard the profile, and it has to be switched off independently, so a user who disabled My Taste and still sees its fingerprints has probably left the wand on. If contamination is the complaint (a stray sound, another language, elements appearing despite being in Exclude Styles), check the wand, then the profile contents — an experienced-user recommendation is to keep genres and specific instruments out of the profile entirely and leave only qualities, moods, and vocal generalities (ANECDOTAL) — but note that is advice for **hand-editing** the profile: Suno's own wand pre-fill routinely contains genres, named instruments, and a numeric BPM (verified in live UI (Pro account, 2026-08-14)), so a genre-heavy pre-fill is normal output, not a symptom.

The profile-edit screen also exposes a **"Genre Overrides" free-text field** (observed in live UI (2026-08-14); untested): it looks like it wants genre tags but accepts free text, and whether non-genre values do anything is **untested** — mention it as existing, don't promise behavior.

Consequence for packages: vague prompts are no longer reproducible across accounts, detailed ones are — an argument for the fully-specified package, not against it. If a whole catalog starts sounding same-y and the My Taste controls don't help, one competing hypothesis with community support is **per-workspace accumulation** — a fresh workspace is reported to restore variety (mechanism unverified).

### Ecosystem: still no public API

Suno announced on 2026-07-01 that it is "exploring a developer API" beginning with a curated partner group, with an interest intake form. As of 2026-08-13 there is **no public launch date, pricing, portal, endpoint list, or documentation**. COMMUNITY. Every "Suno API" sold today is a third-party wrapper with no official standing — do not present one as a supported integration path.

---

## Package Field Mapping

Where each component of Mac's output package goes in Suno's Custom Mode:

| Component | What It Is | Where It Goes in Suno |
|-----------|-----------|----------------------|
| **Persona** (Pro/Premier) | Vocal identity from a source song | Persona selector (if applicable) |
| **Inspo** (v4.5+ Pro) | Playlist analysis for vibe channeling | Inspo feature (if applicable) |
| **Lyrics** | Structured text with metatags | Lyrics field (Custom Mode) |
| **Style Prompt** | Sound description optimized for your model | Style of Music field |
| **Exclude Styles** (Pro/Premier) | Comma-separated list of what to avoid | Exclude Styles field |
| **Vocal Gender** | Male/Female voice selection | Under More Options |
| **Lyrics Mode** | Manual (your lyrics) or Auto (Suno generates) | Lyrics toggle |
| **Weirdness** (Pro/Premier) | Creative deviation: lower = safer, higher = experimental | Under More Options |
| **Style Influence** (Pro/Premier) | Prompt adherence: lower = looser, higher = tighter | Under More Options |
| **Audio Influence** (Pro/Premier) | Persona/upload resemblance (appears with Persona or audio upload) | Under More Options |
| **Song Title** | Title for the generation | Title field |
| **Wild Card Variant** | An experimental alternative style prompt | Optional -- try it if you want |

---

## Style Prompt Best Practices

- **1,000-character limit** (200 for v4 Pro) -- content beyond this is silently truncated. The first ~200 chars are the "critical zone" where front-loaded terms have strongest influence. Content beyond ~200 is supplementary, not wasted — v5.5 may interpret more effectively. **5-8 descriptors is the sweet spot** (HookGenius 1000+ prompt analysis, April 2026 — fewer than 4 produces generic results; exceeding 10 causes conflicting signals and quality degradation).
- **Word order is weighted** -- front-loaded terms dominate. Priority order: Genre > Mood/Energy > Instruments > Vocals > Production. Treat the first ~200 characters as the "critical zone."
- **Hyper-specific beats generic** -- "1980s synth-pop" not "pop"; "distorted electric guitar, power chords" not "guitar"
- **BPM and key in style prompt (v5)** -- may work better in v5 than in lyric tags: `deep house, 122 BPM, A minor, hypnotic groove`. Still ineffective in v4/v4.5.
- **Production descriptors (v5)** -- "radio-ready mix, punchy drums, wide stereo field, crisp high-end, warm bass" are effective in v5
- **Never put artist names in the style prompt** -- Suno does not reliably replicate named artists. Decompose into concrete sonic descriptors instead.
- **Never put sound cues, asterisks, or style descriptions inside lyrics** -- the style prompt and lyrics are separate inputs
- **Negative/exclusion prompts go in the Exclude Styles field**, not in the main style prompt. In-prompt negatives ("no [element]" at the end) also work as a fallback.
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

### Exclude Styles (Pro/Premier)

The Exclude Styles field is a dedicated exclusion input separate from the style prompt. It functions as **probability reduction** -- guidance, not a hard ban.

- Format as a **comma-separated list** for easy copy-paste: `screaming vocals, steel guitar, autotune`
- Be specific: "screaming vocals" is better than "screaming"
- **Limit to 2-3 most important exclusions** -- too many destabilizes the arrangement
- In-prompt negatives also work: add "no [element]" at the end of your style prompt as a supplement
- With Exclude Styles handling exclusions, the style prompt can focus entirely on POSITIVE instructions
- Heavier genre words ("metal", "sludge") become usable in the style prompt when the Exclude Styles field blocks their unwanted defaults
- **Note:** Exclude Styles is currently in Early Access Beta and may not be 100% reliable for all instrument exclusions

**Free tier:** No Exclude Styles field. Translate exclusion intentions into positive style prompt language -- "clean singing with grit on peaks" instead of "no screaming."

---

## Metatag Reference

> This is Mac's quick reference. For comprehensive metatag documentation, consult the Lyric Transformer's detailed references — invoke `suno-lyric-transformer` or read its reference files directly:
> - **Full metatag catalog:** `suno-lyric-transformer/references/metatag-reference.md` — all known tags with confidence levels, production findings, and detailed usage notes
> - **Section job framework:** `suno-lyric-transformer/references/section-jobs.md` — what each section does emotionally, poem-to-song mapping guide, structural metaphor techniques

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
| `[Interlude]` | Transitional palette cleanser -- defaults instrumental, lighter treatment if lyrics provided |
| `[Solo]` / `[Guitar Solo]` | Instrumental solo section |
| `[Break]` | Brief pause or stripped-back moment. Useful as energy-bleed buffer between aggressive and clean sections |
| `[Drop]` | Sudden energy release (EDM/electronic) |
| `[Hook]` | Short catchy phrase or motif |
| `[Fade Out]` | Gradual volume decrease — **weak signal**; never use alone, and primary-source users report it working in no configuration. Apply real fades in the editor |
| `[End]` | Signal to stop the song — place on the absolute last line, nothing beneath it |

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

See `suno-lyric-transformer/references/metatag-reference.md` "Dual Vocals" section for full workarounds and ranked reliability.

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

---

## Troubleshooting Suno Issues

This table covers problems with Suno's output. For issues with Mac itself (wrong mode, missing profiles, skill errors), see the [Usage Guide Troubleshooting](./USAGE.md#9-troubleshooting).

### Prompt and Formatting Issues

| Issue | What Happens | Fix |
|-------|-------------|-----|
| **Silent truncation** | Style prompts over the character limit are cut off without warning | Keep within limits; front-load important content |
| **"Metal" in style prompt** | Triggers screaming/harsh vocals by default | Use "progressive heavy groove" if screaming not desired |
| **Negative prompts ignored** | "No screaming" in style prompt is unreliable | Use Exclude Styles field (Pro) or positive language |
| **Brass/instrument bleed** | Instruments in style prompt appear globally | Move section-specific instruments to end of prompt; use `[Instrument: ...]` metatags |
| **Exclamation points** | `!` triggers bark/attack vocal delivery | Remove from clean sections; bleeds into following sections |
| **ALL CAPS everywhere** | Sets loudness ceiling in early sections | Use sentence case; save caps for one peak moment |
| **Dense punctuation** | Heavy punctuation confuses vocal cadence | Simplify; use commas and dashes intentionally |
| **Scream bleed-through** | Aggressive vocals carry into subsequent sections | Add `[Vocal Style: whispered]` reset after aggressive sections |
| **Sections sound flat despite energy tags** | Energy metatags alone don't drive tempo changes | Combine with line density changes (short lines = slow, packed lines = fast), half-time/double-time drum metatags (`[Heavy: halftime]`, `[Double Time]`), arrangement density changes, and Weirdness slider. Do NOT use BPM tags — they are confirmed ineffective. |
| **Persona style conflicts** | Persona's auto-style clashes with your style prompt | Persona auto-fills Style of Music -- keep additions simple (1-2 genres, 1 mood, 2-4 instruments max). Change ONE variable at a time (music direction OR Persona, not both). |
| **Unwanted instrument in wrong section** | Suno's style prompt is global | Move section-specific instruments to end of prompt, use `[Instrument: ...]` metatags, or generate sections separately via Legacy Editor (Pro) |

### Audio Quality Issues

| Issue | What Happens | Fix |
|-------|-------------|-----|
| **Vocal artifacts** | Robotic or glitchy vocals | Try v5 Pro (better vocal nuance), or regenerate |
| **Audio artifacts or glitches** | Random audio issues | Regenerate 3-5 times with the same prompt. If persistent, simplify the style prompt. |
| **Pronunciation issues** | Words sung incorrectly | Add phonetic hints in lyrics or use the `[Spoken Word]` metatag |
| **Timing feels wrong** | Rhythm or pacing issues | Premier: fix in Studio (Warp Markers were the Studio 1.x tool for this and are not in current Studio 2.0 copy — check the live UI). Pro: Replace Section on the offending span, or export stems and correct timing in a DAW |
| **Long song degradation** | Quality drops in extended generations | Generate shorter segments and use Extend carefully |
| **Voices spoken word/narration** | Voice drifts toward singing, inconsistent tone between sections, unnatural pacing | Suno remains music-first. Voices is not suitable for spoken word or narration — consider narration as a separate recording edited in via DAW |
| **Voices vocal artifacts at high Audio Influence** | Shimmer, warble, or robotic quality at the top of the range | Try 40-60% — but this is voice-dependent, not a rule: some voices are clean at 85%. If the complaint is "it doesn't sound like me" rather than "it sounds artefacty," Suno's official path is to RAISE it first, then rebuild the profile from a clean acapella. See `suno-style-prompt-builder/references/model-prompt-strategies.md` → "Voices" |

### Creative Issues

| Issue | What Happens | Fix |
|-------|-------------|-----|
| **Single Create** | One Create (2 songs) rarely nails it | 2-3 Creates (4-6 songs, 20-30 credits) is the practical minimum for finding a keeper |
| **Same prompt, wildly different results** | Normal Suno behavior | This is expected — each Create produces 2 different takes from the same inputs. Budget accordingly. |
| **Cliche amplification** | Subtle lyrical cliches become obvious when sung | Run cliche detection before submitting lyrics |
| **`[Intro]` unreliability** | Suno's `[Intro]` tag often produces unexpected results | Regenerate just the first 10 seconds, or skip the tag |
| **"Not what I imagined"** | Output doesn't match your vision | Use the Refine Song flow (RS). Mac's feedback elicitation helps you articulate what needs to change. |

---

## Covers, Remixes, and Inspo

### Cover Feature
- Cover re-performs an existing song in a new style while preserving melody, lyrics, and structure
- Works with any Suno-generated song, uploaded audio, instrumentals or vocal tracks
- Step-by-step: three-dot menu → Create → Cover Song → describe the new style → generate
- **CRITICAL: Covers are NOT eligible for commercial use** — even on your own songs. For commercial releases, use the original lyrics and create a fresh generation instead.
- Stacking Covers (re-covering within the same genre) can smooth cohesion

### Remix Umbrella — Four Workflows
- **Cover** — re-sing in a different style/genre (preserves melody)
- **Extend** — add more to an existing song
- **Reuse** — reuse the prompt/settings from an existing song
- **Speed** — adjust playback speed

### v4.5+ Pro Additional Tools
- **Instrumental Flip** — rebuilds backing track while preserving vocal structure
- **Vocal Swap** — changes vocal persona while retaining melody and timing
- **Spark from Playlist** — uses a reference playlist to shape mood/tempo/instrumentation

### Cover vs Remix vs Inspo Decision Matrix

| Tool | Use When | What It Does |
|------|----------|-------------|
| Cover | "Play this same song in a different style" | Re-performs with new style, keeps melody/lyrics/structure |
| Remix (general) | "Tweak/transform this song" | Various transformations within same song identity |
| Inspo | "Make something NEW inspired by these" | Analyzes a playlist, generates entirely new material |

---

## Community Research Sources & Further Reading

> **Last updated:** August 13, 2026. These sources informed the findings in this reference. Suno evolves fast — verify claims against current platform behavior.

### Official Suno Documentation — 2026-08-13 sweep

- [Release notes](https://suno.com/release-notes) — Duration slider (Jul 20), cover art (Jul 31), Voices to mobile + free (Aug 7), Studio 2.0 (Aug 13)
- [Download limits FAQ](https://help.suno.com/en/articles/13614785) · [ToS update blog](https://suno.com/blog/suno-updates-tos) · [Terms effective Sept 3 2026](https://suno.com/terms-september-2026)
- [Studio 2.0 release note](https://suno.com/release-notes/studio-2) · [Studio 2.0 blog](https://suno.com/blog/studio-2) · [Studio help category (2.0 vs Archive)](https://help.suno.com/en/categories/1708865)
- [Stem separation modes and credits](https://help.suno.com/en/articles/12702337) · [Replace Section](https://help.suno.com/en/articles/3271873) · [Studio is Premier-only](https://help.suno.com/en/articles/8333825)
- [Building the future of music responsibly](https://suno.com/blog/building-the-future-of-music-responsibly) (artist-name policy, watermarking) · [Community Guidelines](https://suno.com/community-guidelines) · [BMG partnership](https://suno.com/blog/suno-partnership-bmg)
- [Pricing](https://suno.com/pricing) · [Credits](https://help.suno.com/en/articles/2417089)
- **Stale, do not cite as current:** [Model Information help category](https://help.suno.com/en/categories/1752193) (Sept 2025 articles still call V4 "the latest model")

### Official Suno Documentation — earlier
- [What's New in v5.5](https://help.suno.com/en/articles/11362305)
- [Voices: Use Your Voice in Suno](https://help.suno.com/en/articles/11362369)
- [Voices FAQ](https://help.suno.com/en/articles/11362433)
- [Custom Models in v5.5](https://help.suno.com/en/articles/11362497)
- [My Taste](https://help.suno.com/en/articles/11362561)
- [Creative Sliders](https://help.suno.com/en/articles/6141377)

### Independent Testing & Analysis
- [JG BeatsLab: Voices Day One Testing](https://www.jgbeatslab.com/ai-music-lab-blog/suno-v5-5-voices-tested) — Voices Audio Influence real-world ranges, Skill Level dropdown impact, vocal resemblance ceiling findings
- [HookGenius: Suno v5.5 Guide](https://hookgenius.app/learn/suno-v5-5-guide/) — Comprehensive v5.5 feature walkthrough
- [HookGenius: 1000+ Prompt Analysis](https://hookgenius.app/learn/suno-style-tag-research/) — Data-driven findings on tag count sweet spots, "cinematic" as universal modifier, production tag underuse, conflicting tag behavior
- [AudioNewsRoom: What You Give Up to Make It Yours](https://audionewsroom.net/2026/03/suno-v5-5-what-you-give-up-to-make-it-yours.html) — Privacy/consent analysis for Voices and Custom Models
- [JackRighteous: How Has v5.5 Gone For You](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/how-has-suno-v5-5-update-gone-for-you) — Genre-specific slider ranges, section-specific strategy
- [JackRighteous: Creative Control Sliders in v5](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/creative-control-sliders-suno-v5) — Detailed slider behavior analysis
- [JackRighteous: v5.5 Features Explained](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-v5-5-features-explained-workflow-changes-studio-editing-creator-guide) — Workflow paradigm shift documentation
- [JackRighteous: Spoken Narration Workflow](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-spoken-narration-workflow) — Spoken word limitations with Voices
- [Suno v5 vs v5.5 Comparison](https://suno-v5.com/blog/suno-v5-5-vs-v5-what-actually-changed) — What actually changed between versions

### API Reference
- [CometAPI: v5.5 API Guide](https://www.cometapi.com/suno-v5-5-what-is-new-and-how-to-use-it-via-api--studio/) — API model parameter `mv: "chirp-fenix"` for v5.5
