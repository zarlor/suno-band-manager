# Suno Tier Feature Matrix

> **Last validated:** August 13, 2026 (Suno Free, Pro, Premier plans; Studio 2.0; Sept 3 2026 download caps and ToS). Suno updates pricing, features, and tier boundaries frequently — use web search to verify against the current Suno pricing page when uncertain.

**Note:** The `scripts/tier-features.py` script is the authoritative source of this data for headless flows; this reference file is its human-readable twin. **The two agree as of 2026-08-13** — the script now carries the download caps, download-bound commercial rights, the three stem modes with credit costs, Studio 2.0 as Premier-only, and the archived Studio 1.x names (exposed as an explicit `notes.studio_1x_archived` list rather than as available features). Its `download_quality` field is gone: downloads are gated by count, not bitrate. **When updating, change the script first and mirror it here.**

## Plan Comparison

| Feature | Free ($0) | Pro ($8/mo displayed) | Premier ($24/mo displayed) |
|---------|-----------|----------------------------|----------------------------------|
| **Model Access** | v4.5-all only | v5.5 plus legacy v4, v4.5, v4.5+, v5 | Same as Pro |
| **Credits** | 50/day, renew daily (~10 songs) | 2,500/mo (~500 songs) | 10,000/mo (~2,000 songs) |
| **Credit Cost** | 5 credits/song — 10 credits per generation produces 2 songs | Same | Same |
| **Song Length** | Determined by model — v4.5-all supports up to ~8 min | Determined by model — v4.5/v5/v5.5 support up to ~8 min. Duration slider (web, v5.5) targets 10s–6:00 | Same as Pro |
| **Song downloads** (from 2026-09-03) | **7 total lifetime trial downloads**, personal/non-commercial | **20 per month** | **60 per month** (Studio exports exempt) |
| **Commercial Use** | No | Yes — but only for outputs obtained as a permitted download | Yes — same mechanism |
| **Personas** | No | Yes (v4.5/v5/v5.5 — live inside the Voices menu, not removed) | Same |
| **Voices** | No | Yes (v5.5 voice cloning) | Yes (v5.5 voice cloning) |
| **Voice recording entry point** | Yes — "available to try on free plans" (limited) | Yes, expanded | Yes, expanded |
| **Custom Models** | No | Yes (up to 3 models) | Yes (up to 3 models) |
| **My Taste** | Yes (passive; can be disabled) | Yes (passive) | Yes (passive) |
| **Weirdness Slider** | No | Yes (0-100) | Yes (0-100) |
| **Style Influence Slider** | No | Yes (0-100) | Yes (0-100) |
| **Audio Influence Slider** | No | Yes (0-100, with Voice/Persona or audio upload) | Yes (0-100, with Voice/Persona or audio upload) |
| | | *10-15% reduces persona era-anchoring* | *10-15% reduces persona era-anchoring* |
| **Add Vocals/Instrumental** | No | Yes (beta) | Yes (beta) |
| **Covers** | No | Yes (beta) | Yes (beta) |
| **Remaster** | No | Yes | Yes |
| **Stem separation** | No | 2 modes: Auto Split, Split from Mix | 3 modes: + Advanced Split (~100 instruments) |
| **Audio Upload** | 8 min | 30 min | 30 min |
| **Replace Section / Song Editor** | No | Yes | Yes |
| **Suno Studio 2.0** | No | **No** | Yes |
| **Studio downloads** | — | — | Unlimited, exempt from the monthly cap |
| **Queue Priority** | Shared | Priority | Priority, 10 concurrent |
| **Add-on Credits** | No | Yes | Yes |

Sources: [Suno pricing](https://suno.com/pricing) · [Credits & songs](https://help.suno.com/en/articles/2417089) · [Download limits FAQ](https://help.suno.com/en/articles/13614785) · [Stem separation](https://help.suno.com/en/articles/12702337) · [Studio is Premier-only](https://help.suno.com/en/articles/8333825) · [Replace Section](https://help.suno.com/en/articles/3271873) — all OFFICIAL, fetched 2026-08-13.

**Pricing display ambiguity (flagged, not asserted):** The pricing page displays **$8** (Pro) and **$24** (Premier) alongside a "Monthly / Annual save 20%" toggle, while press coverage consistently describes Pro as $8–$10 and Premier as $24–$30. The most likely reading is that $8/$24 are the annual-billing per-month rates and $10/$30 are month-to-month — but two separate fetches on 2026-08-13 did not disambiguate it. Quote the displayed number and the toggle, not a single monthly price. OFFICIAL page + COMMUNITY press ([MBW](https://www.musicbusinessworldwide.com/suno-limits-subscribers-downloads-per-month/)).

## Downloads and Commercial Rights (effective 2026-09-03)

This is the largest change to the tier picture since the module was written, and it reshapes workflow rather than just feature access. OFFICIAL — [Download limits FAQ](https://help.suno.com/en/articles/13614785), [ToS update blog](https://suno.com/blog/suno-updates-tos) (2026-08-10), [Terms effective Sept 3 2026](https://suno.com/terms-september-2026).

- **Downloads are capped:** Free = 7 lifetime trial downloads (personal, non-commercial, they do not reset); Pro = 20/month; Premier = 60/month. Monthly allowances reset on the billing date with **no carryover**; extra downloads are purchasable.
- **Retroactive to the whole back catalogue** — "Download limits apply to all music on Suno starting September 3, including songs created before that date."
- **Accounting:** one song = one download regardless of format or how many times it is re-downloaded; **all stems from a song count as part of that song's single download**; failed downloads do not count.
- **Studio is exempt** — Premier users "will still be able to download their work from Studio without limitation." This makes Premier's value proposition materially different from "Studio is a nicer editor."
- **Streaming, playback, and on-platform sharing stay unlimited** on every plan.
- **Commercial rights are now bound to the download, not the subscription.** The Sept 3 ToS grants commercial exploitation only for outputs obtained as a *permitted download*; obtaining a copy by any other channel is prohibited, as is removing or obscuring fingerprints, watermarks, or metadata. Downloaded outputs keep perpetual commercial rights even after a downgrade.
- **Remixes are jointly owned and non-commercial for everyone**, regardless of tier: "all Remixes shall be a joint work owned jointly and equally by you and the Remixer," usable "only for lawful, personal and non-commercial purposes."
- **Stated rationale:** "limiting downloads will make it harder for bad actors to mass-export music."

**Workflow implication for profiles and song planning:** downloads are now a scarce budget. Selection has to happen *before* download — generate and audition on-platform, then spend a download on the keeper. Pro's 20/month is the binding constraint for most catalog work; a stem set for one song still costs one download, so extracting stems is cheap relative to downloading multiple takes of the same song.

## Stem Separation Modes and Credit Costs

The legacy "Vocals + Instrumental" mode was replaced by **Split from Mix**. OFFICIAL — [Stem separation](https://help.suno.com/en/articles/12702337).

| Mode | Output | Tier | Credit cost |
|------|--------|------|-------------|
| **Auto Split** | Up to 12 stems | Pro + Premier | 50 credits per extraction |
| **Split from Mix** | Two-way split from the mixed audio — the extracted stem plus its complement | Pro + Premier | 10 credits per extraction (20 total for both stems created) |
| **Advanced Split** | ~100 instruments, choose which stems to create | **Premier only** | 10 credits per extraction; **20 total per stem**, because each extraction returns the chosen stem plus its complement (everything except that stem). Budget at 20 per stem. OFFICIAL — [help.suno.com/en/articles/12702337](https://help.suno.com/en/articles/12702337) |

**COMMUNITY:** Advanced Split reportedly *regenerates* tracks rather than filtering the mix, which is the basis for its artifact-free multitrack claim (reduced noise and phase issues). It does not change how prompts are written.

## Free Tier Available Options

- Vocal Gender selection
- Manual/Auto Lyrics mode
- Song Title

## Models

| Model | Tagline | Availability |
|-------|---------|-------------|
| v5.5 | Voices, Custom Models, My Taste | Pro/Premier |
| v5 Pro | Authentic vocals, superior audio quality and control | Pro/Premier |
| v4.5+ Pro | Advanced creation methods | Pro/Premier |
| v4.5 Pro | Intelligent prompts | Pro/Premier |
| v4.5-all | Best free model | All tiers |
| v4 Pro | Improved sound quality (legacy) | Pro/Premier |

**v5.5 is still the top model** (released 2026-03-26). There is no v6. OFFICIAL — [release notes](https://suno.com/release-notes).

### Model retirement is announced — versions and dates are NOT published

OFFICIAL — [ToS update blog](https://suno.com/blog/suno-updates-tos), [FAQ](https://help.suno.com/en/articles/13614785), [BMG partnership](https://suno.com/blog/suno-partnership-bmg) (2026-08-12).

- "New models launching soon will retire older versions." Retiring means *you can't generate new songs with it*; it "doesn't affect anything you've already made" — existing songs stay playable and shareable.
- **No official source names which versions retire or when.** Third-party outlets assert v3.5/v4/v4.5/v5 are going away; that is not officially confirmed and should not be repeated as fact.
- **Extensions, remixes, and covers of existing songs will run on the NEW models** — "results may sound different from the original generation." Any profile whose workflow depends on Extending or Covering older tracks carries that risk.
- The next model is "our first music model developed with the music industry" (BMG global deal, 2026-08-12). No name, date, or tier gating announced.
- **VERIFIED-ABSENT:** no official statement on what happens to Voices, Custom Models, or Style Personas built on retired models. The FAQ is silent. Do not reassure a user either way.
- Suno's **Model Information help category is stale** (articles from Sept 2025 still call V4 "the latest model") — do not cite it as current. [help.suno.com/en/categories/1752193](https://help.suno.com/en/categories/1752193)

## Profile Implications by Tier

**Free tier profiles should:**
- Set `model_preference` to "v4.5-all" (only available model)
- Omit or zero out `sliders` (not available)
- Not reference Personas or Voices for *generation* (not available) — note that the voice **recording** entry point is now available to try on free plans, but clone creation and use in generation remain paid
- Focus style_baseline on conversational descriptions (v4.5-all strength)
- My Taste is active passively — no profile configuration needed
- Plan around **7 lifetime downloads** and no commercial rights: free-tier work is effectively listen-on-platform work

**Pro tier profiles can:**
- Use v5.5 plus the legacy models (v4, v4.5, v4.5+, v5)
- Set Weirdness and Style Influence sliders
- Reference Suno Personas for vocal consistency (Personas were never discontinued — they live inside the Voices menu)
- Use Suno Voices for vocal consistency (v5.5 voice cloning)
- Use Custom Models (up to 3, trained on 6+ original tracks, 2-5 min training time)
- Use crisp, descriptor-focused style for v5 Pro
- Use Audio Influence slider to manage persona era-anchoring (reduce to 10-15% when the persona's source era conflicts with the desired sound)
- When a Voice is configured, omit gender vocal descriptors from style_baseline — the Voice defines the vocal identity
- Use Replace Section / the Song Editor, Auto Split and Split from Mix stems
- Budget **20 downloads/month** — decide which takes are keepers before downloading

**Premier tier profiles can:**
- Everything Pro can do, plus Suno **Studio 2.0** (browser-based generative DAW — MIDI, chat bar, custom plugins, wavetable synth, automation, 32-bit exports)
- Set studio_preferences (BPM, key, time signature) — note the time-signature-to-generator question is now unverified for Studio 2.0, see [STUDIO-EDITOR-REFERENCE.md](../../_shared/references/STUDIO-EDITOR-REFERENCE.md)
- Advanced Split stem separation (~100 instruments) in addition to Pro's two modes
- Voices and Custom Models (same as Pro)
- **Unlimited Studio downloads**, exempt from the 60/month cap — the practical reason to be on Premier if the workflow ends in a DAW

## Production Notes

**Audio Influence as Era Control (Pro/Premier):** When a persona's era-anchoring conflicts with the desired era for a track, reducing Audio Influence from the default 25% to 10-15% helps pull the sound away from the persona's source era. This doesn't fully eliminate the anchoring — for strong era shifts, consider generating without a persona or creating an era-specific persona from an era-appropriate source song.

**Audio Influence Effective Range (Pro/Premier):** The practical range for Audio Influence is 15-25%. Values above 25% show diminishing returns — tested at 40%, it did not override an incompatible style prompt. The slider shapes the persona's contribution but cannot force the persona's character over a conflicting style direction.

**Acoustic/Ballad Tracks and Audio Influence (Pro/Premier):** When the style prompt clearly defines a non-heavy genre (ballad, acoustic, stripped-back), the persona contributes only vocal identity — it does not drag in unwanted instrumentation. Do NOT reduce Audio Influence for ballads or stripped tracks; keep it at the normal working range. The style prompt governs the arrangement; the persona governs the voice.

**Exclude Styles — Known Limitations:** The Exclude Styles field helps shape tone but does not reliably remove instruments entirely. For example, even with "guitar" in Exclude Styles, Suno still produces guitar in rock/metal contexts. Treat Exclude Styles as a nudge toward the desired balance rather than a hard instrument filter.

**Personas and Voices Coexist (correction):** Personas were **never discontinued** — they were relocated into the Voices menu, which is what made them look gone. Personas still work; Voices is a separate, additional feature. The two capture different things: a Persona captures *style essence* from a source generation, a Voice is actual voice cloning from a 15-second to 4-minute audio sample with anti-deepfake verification. Voices are private to the account that created them. Any profile or doc phrased as "Personas were replaced by Voices" is wrong and should be corrected to "relocated inside Voices."

**Five identity layers, and stacking them fights you.** Suno now exposes five distinct identity layers — Style Persona, Voice, Lyricist, Custom Model, and My Taste. Stacking them creates conflict rather than control. ANECDOTAL (single authoritative community source, rebuilt 2026-08-01) — but it matches our own one-variable-at-a-time discipline, so the practical rule stands: pick the layer that carries the identity for this song and leave the others out of the decision.

**My Taste is always on by default — but it can be turned off.** My Taste builds a per-account preference profile from history, likes, and skips (roughly 20-30 generations before it bites), shaping defaults, recommendations, and "subtle generation tendencies" on all tiers including free. Suno's stated boundary: "My Taste influences defaults, not your explicit prompts. A detailed style prompt always overrides My Taste preferences." Primary-source users (2026-08) confirm three counteractions — delete individual entries, deactivate the feature, or write `...` into the taste board — with the controls in the **desktop browser only**, and a **separate toggle for the magic wand** that must be switched off independently. COMMUNITY. (An aggregation-based report in the same sweep claimed it cannot be disabled; primary sources contradict that.) Consequence for profiles: a vague style_baseline is no longer reproducible across accounts, while a fully-specified one is — this argues for *more* specificity in profiles, not less.

**Voices and Vocal Descriptors (v5.5, Pro/Premier):** When a Voice is active, the Voice defines the vocal identity — gender, tone, and character come from the audio sample. Omit gender vocal descriptors from the style prompt to avoid conflicts. Other vocal direction (delivery, energy, diction) can still shape performance.

**Audio Influence with Voices (v5.5, Pro/Premier):** The **Persona** slot has a narrow 15-25% effective range; the **Voice** slot runs much higher and the sweet spot is per-voice. Start around 50% and profile each voice rather than storing a single number as gospel — one profiled voice was clean at 85% where 55% showed artifacts. Adjust up if the voice is unrecognizable, down if quality suffers, and note that Suno's official path for an unrecognizable clone is to raise Audio Influence before concluding the clone is bad. **Canonical ranges, the official escalation path, and the intent-split values live in `suno-style-prompt-builder/references/model-prompt-strategies.md` → "Voices" — profiles should point there rather than duplicating a scale.**

**Custom Models (v5.5, Pro/Premier):** Custom Models are trained on 6 or more original tracks and take 2-5 minutes to train. Up to 3 Custom Models per account. They capture a production style and sound signature. When a Custom Model is active, it shapes the overall production character — the style prompt should complement rather than fight the model's learned style.

**My Taste (v5.5, All Tiers):** My Taste is passive personalization derived from the user's generation history. It requires no configuration and works across all tiers including Free. It subtly shapes generation output based on patterns in what the user has created and liked.

**Song Editor vs. Studio (Pro vs Premier):** Pro users get the Song Editor / Legacy Editor — section-level editing with Replace Section, Extend, Crop, Fade, Rearrange, plus Auto Split and Split from Mix stems. Premier users additionally get **Suno Studio 2.0** — the overhauled browser-based generative DAW (MIDI import/record/edit, chat bar that generates instruments/vocals/plugins, wavetable synth, audio effects, automation curves, 32-bit/48kHz multitrack export, unlimited downloads). The Studio 1.x feature names this file used to list (Warp Markers, Remove FX, Alternates, EQ, Context Window, Sounds Mode, Stem Cover, Heal Edits, MILO-1080) are **not in current official Studio 2.0 copy** — treat them as archived until re-verified. **VERIFIED-ABSENT:** nothing officially states that Studio 2.0 replaces or deprecates the Song Editor; the safe reading is coexistence. For complete editing workflows, see [STUDIO-EDITOR-REFERENCE.md](../../_shared/references/STUDIO-EDITOR-REFERENCE.md).

**Lyricist — present at Pro; free-tier gating unverified.** Lyricist shipped 2026-07-09 with the lyrics-editor overhaul: save lyrics you own as reusable named style templates ("a Persona for words"), natural-language editing, variations and references, full-screen editor, structure labels, autosave. It captures tone, phrasing, and themes — **not** vocal delivery or production. **Confirmed present at Pro** (verified in live UI, Pro account, 2026-08-14), reached through the lyrics panel → "Help me write lyrics" → the chat helper's "+" items → "+Lyricist". It is a sub-feature inside the lyrics chat helper, not a standalone surface. **Free-tier gating remains unverified** — no official or community source states it, and a Pro observation says nothing about Free. The only pricing-page signal is Free = "Standard features only" vs Pro = "Standard + Pro features (personas and advanced editing)". Do **not** assert Lyricist availability for a free-tier profile. Rights caveat (ANECDOTAL): build Lyricist profiles only from lyrics you own.

**Remaster (Pro/Premier):** Generates refined variations adjusting production details (instrument balance, effects, mix quality, vocal clarity) while preserving song structure. Three strength levels: Subtle, Normal, High. Does NOT change lyrics, style, or vocalist — use Cover for those. Good for final polish before export.

**Replace Section Best Practices (Pro/Premier):** Key controls: Keep Duration toggle (ON = match length, OFF = creative flexibility), Instrumental Mode toggle (removes vocals), Replace Lyrics (edit lyrics for just the selected region). Best results with 10-30 second selections; typically requires 2-5 attempts for seamless transitions. Availability is confirmed unchanged at Pro as of 2026-08-13, with no deprecation announced (OFFICIAL, [help.suno.com/en/articles/3271873](https://help.suno.com/en/articles/3271873)) — **but availability is not viability.** Our own production test (2026-04-29) found audible transition seams even at the documented sweet-spot scale; see the local finding in [STUDIO-EDITOR-REFERENCE.md](../../_shared/references/STUDIO-EDITOR-REFERENCE.md).

**v5.5 Editing Paradigm:** v5.5 favors generate → inspect → section replace → refine (not regenerate from scratch). This preserves good material and spends fewer credits. For complete Studio and Editor workflows, see [STUDIO-EDITOR-REFERENCE.md](../../_shared/references/STUDIO-EDITOR-REFERENCE.md).
