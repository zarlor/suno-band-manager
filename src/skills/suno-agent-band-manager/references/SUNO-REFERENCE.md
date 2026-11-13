# Suno Platform Reference

The one home for Suno's plan and model facts: the model line-up, what each plan includes, credit and download counts, where each package field goes, and what changed when. Post-generation editing tools are in `references/STUDIO-EDITOR-REFERENCE.md`, which Refine Song loads by section. How to word a style prompt or tag a lyric is the pipeline skills' knowledge, not this file's.

## How to Load This File

This file is too large to read whole. List the headings with `grep -n '^##' {skill-root}/references/SUNO-REFERENCE.md` and read from the section's heading to the next `## ` heading. The topical sections say what is true now and are kept in step with the dated ones; each "Platform Changes" section is the change log for its date, newest first, with the source and grade of every claim.

| When | Load |
|------|------|
| Which models exist, which are retired, character limits, what a Voice, Custom Model or My Taste does | Model Comparison |
| What a plan includes, credits per Create, download allowances and what counts as one download, prices, slider and Controls availability by tier | Plan Comparison |
| A claim is time-sensitive, or the owner asks what changed lately | The newest Platform Changes section, then older ones as the question reaches back |
| A spoken piece (Speech), a Persona with a Voice, Custom Models on v6, the Exclude Styles cap | Platform Changes — 2026-10-03 |
| MIDI upload in Create or the Suno MCP as launched, Studio Chat, Speech plans, how many people a Workspace or Custom Model can be shared with | Platform Changes — 2026-11-13 |
| Publishing an album, sharing a Workspace or a Custom Model, Exclude or Remaster misbehaving on v6 | Platform Changes — 2026-10-15 · Platform Changes — 2026-10-28 |
| The v6 Create screen layout, where section editing lives, what v6 added | Platform Changes — 2026-09-09 (v6) |
| Download rules, commercial rights, watermarking, Lyricist, My Taste controls, the artist-name policy, the API | Platform Changes — 2026-08-13 |
| Where a package field goes on the Create screen | Package Field Mapping |
| A take has a problem that is Suno's, not the package's | Troubleshooting Suno Issues |
| A Cover, Extend, Remix or Inspo is being considered | Covers, Remixes, and Inspo |
| The user has written music (a MIDI file, a part, a guide track) for Suno to follow, or an upload was flagged | MIDI and Audio Guides |
| The user has Suno connected to an assistant, or asks what the Suno MCP does, costs or cannot do | Suno MCP (beta) |
| Where a claim came from | Community Research Sources & Further Reading |

> **Platform state as of 2026-11-13** (the date of the newest "Platform Changes" section; no model change announced since v6 launched; Speech beta 2026-10-01, Albums 2026-10-05, Workspace and Custom Model sharing 2026-10-15, Suno MCP beta 2026-10-28, MIDI upload in Create 2026-11-04 — see "Platform Changes — 2026-11-13", "— 2026-10-28", "— 2026-10-15" and "— 2026-10-03"). **Suno launched the v6 family (v6, v6-wild, v6-mini) on 2026-09-09 and retired every earlier model.** The v6 Controls panel (formerly "More Options") adds **Max Mode**, **Variety**, and **Personalize** alongside Duration, and v6 is reported to want a different prompt shape — see "Platform Changes — 2026-09-09 (v6)" below; the suno-style-prompt-builder skill carries the v6 prompting guidance (**PREVIEW**). Earlier changes still in force: **downloads capped from 2026-09-03** with commercial rights attached to the download; **Studio 2.0** Premier-only. Verify anything time-sensitive against [suno.com/release-notes](https://suno.com/release-notes) before telling a user.

---

## Model Comparison

| Model | Status | Style | Character Limit | Tier |
|-------|--------|-------|----------------|------|
| **v6** | **Current** | Ordered production direction (PREVIEW) | 1,000 | Pro/Premier |
| **v6-wild** | **Current** — the exploratory sibling | Same as v6 | 1,000 | Pro/Premier |
| **v6-mini** | **Current** — the Free model | Same as v6 | 1,000 | All tiers |
| v5.5 Pro | Retired 2026-09-09 | Crisp film-brief (5-8 descriptors) | 1,000 | — |
| v5 Pro | Retired 2026-09-09 | Crisp film-brief (5-8 descriptors) | 1,000 | — |
| v4.5-all / v4.5 Pro / v4.5+ Pro | Retired 2026-09-09 | Conversational descriptions | 1,000 | — |
| v4 Pro | Retired 2026-09-09 | Simple descriptors | 200 | — |

**Retired models still matter in two places:** older band profiles and songbook entries name them (the module still recognizes those names and flags them for update), and any Extend, Cover, or Remaster of a song made on one now runs on v6.

**Character limit details** (community-attested, **not** officially documented — a full review of help.suno.com on 2026-08-13 found no Suno article stating these numbers, and nothing official contradicting them either; keep enforcing them, don't cite them as platform documentation):
- **v6 family:** 1,000 chars for the style prompt and for Exclude Styles, 5,000 for lyrics — unchanged from v5.5 (VENDOR, day-one test; the Exclude cap from the live page markup, 2026-10-03). Past about 3,000 characters of lyrics Suno may rush or cut sections, so the pipeline treats 3,000 as the working ceiling.
- **v4 Pro (retired):** 200 chars (hard limit, silently truncated)
- **v4.5+ / v5 / v5.5 (retired):** 1,000 chars. Front-loaded terms dominate -- the first ~200 chars are the "critical zone" with strongest influence on generation. Content beyond ~200 chars is supplementary but not wasted; v5.5's improved descriptor interpretation may extend the effective window. 5-8 descriptors is the sweet spot.

**Key differences:**
- **v4.5-all** wants flowing, conversational sentences. Example: "Create a melodic, emotional deep house song with organic textures and hypnotic rhythms."
- **v5 Pro** wants crisp descriptors and emotional language over technical. Example: "raw indie folk, yearning vocals, acoustic guitar, lo-fi tape warmth, intimate"
- **v4 Pro** has a hard 200-character limit, not 1,000.

**v5-specific behaviors (retired model — kept as history):**
- Full negative prompting support (v4.5 had limited support)
- Better BPM and key recognition in style prompt (e.g., `deep house, 122 BPM, A minor`)
- Production-quality descriptors more effective (e.g., "radio-ready mix, punchy drums, wide stereo field")
- Composition-aware architecture -- uses early style/genre info for coherent section transitions
- Existing v4 prompts often work "even better" on v5

**v5.5-specific behaviors (retired 2026-09-09; the Voices, Custom Models, and My Taste notes still describe features that exist on v6):**
- Same audio engine, metatags, and character limits as v5 -- all v5 prompts work identically, often with better results
- 48kHz sample rate, up to 8 min generation, internal codename "chirp-fenix" (v5 was "chirp-crow")
- Most expressive model yet -- better at interpreting subtle and nuanced descriptors
- More varied output per generation -- each Create produces 2 songs; 2-3 Creates (20-30 credits) gives 4-6 takes to pick from
- v5.5-optimized prompts can be more specific: "deep sub 808s, glitchy hi-hat rolls, pitched vocal chops" where v5 would use simpler "808s, hi-hats"
- **Voices** (a distinct feature alongside Personas — Personas were **not** removed, they live inside the Voices menu): actual voice cloning with anti-deepfake verification, 15s-4min audio sample required. Clone creation and use are Pro/Premier; since 2026-08-07 the feature is on iOS and Android and "available to try on free plans," with more on paid plans — the free/paid line is not documented, so check the live UI rather than promising a free user what they can do. **Skill Level dropdown** (Beginner/Intermediate/Advanced/Professional) actively reshapes how the model interprets your voice — always select **Professional** regardless of actual ability for the most stable, usable results.
- **Custom Models**: train on 6+ tracks (UI: "Upload 24+ songs for best results"; per-account maximum, 100 by default), **100 credits per model**, 2-5 min training time, up to 3 at a time. Pro/Premier only. Existing Custom Models were upgraded to v6 automatically (2026-09-09), and Premier can share one with up to 10 people (2026-10-15; the limit from Suno's help article, 2026-11-06). Created from the Create form's model picker ("Create Custom Model"); the user's own Suno songs count as eligible, but the picker lists only uploaded songs, so generated songs have to be downloaded and re-uploaded, which spends one download per song. How to make one and when it's worth it: the suno-style-prompt-builder's strategies, "Custom Models". **Privacy/consent note (AudioNewsRoom):** consent grants Suno permission to use your data for training their global models — not optional, not a private silo.
  - **Training data:** WAV at 44.1kHz preferred (Suno auto-normalizes with RMS leveling, DC offset removal, spectral masking, onset detection, key/scale estimation). 8-12 stylistically consistent tracks is the inferred sweet spot. Dynamic range preservation matters more than loudness since the system normalizes internally.
  - **Overfitting risk:** Training data too narrow/homogeneous produces repetitive output. Include variety within your style lane — different tempos, moods, arrangements.
  - **Prompt strategy shift with Custom Models:** Priority order changes from genre-first to **mood/production-first** since genre is already encoded in the model. Simpler natural-language prompts may outperform tag-heavy prompts because the model handles the foundational style. Core formula: MOOD + PRODUCTION TEXTURE + ENERGY/TEMPO + INSTRUMENTS + VOCAL DIRECTION.
- **My Taste**: passive personalization that shapes generation defaults based on your listening/generation history. All tiers. Takes 20-30 generations to settle. The **pencil-and-stars button** on the Styles field (hover: "Personalize style prompt to match your taste") triggers Style Augmentation — it **pre-fills the Styles field with ordinary editable text** derived from your My Taste profile (verified in live UI (Pro account, 2026-08-14)), so the user can rewrite any of it before generating. Detailed manual prompts always override it, and the wand is a drafting shortcut rather than a hidden generation-time layer. Can be viewed, edited, or disabled from avatar menu > "My Taste" (desktop browser only; the wand has its own toggle, and on v6 the **Personalize** control applies the profile to a Create — the counteractions are under "Five identity layers now exist", Platform Changes — 2026-08-13). No documented reset mechanism beyond disable/re-enable.
- **Workflow paradigm shift:** v5.5 encourages generate -> inspect -> replace sections -> refine (not regenerate from scratch)

**Personalization Stack** (introduced with v5.5 and unchanged on v6; layers from broadest to most specific):
1. **My Taste** -- shapes generation defaults passively
2. **Custom Model** -- sets production DNA and sonic identity
3. **Voice** -- applies a specific vocal tone and character
4. **Prompt** -- steers the specific song (always the most important layer)

A Style Persona and Lyricist are identity layers too, and stacking layers creates conflict rather than control: decide which layer carries the identity for a song and leave the others out ("Five identity layers now exist", Platform Changes — 2026-08-13).

---

## Plan Comparison

| Feature | Free ($0) | Pro ($8/mo displayed) | Premier ($24/mo displayed) |
|---------|-----------|---------------------|--------------------------|
| **Model access** | v6-mini | v6 and v6-wild (plus v6-mini) — every pre-v6 model retired 2026-09-09 | Same as Pro |
| **Credits** | 50/day (~10 songs) | 2,500/mo (~500 songs) | 10,000/mo (~2,000 songs) |
| **Credit cost** | 10 credits per Create (produces 2 songs) | Same | Same |
| **Song downloads** (from 2026-09-03; a song counts once, whatever the files or formats) | 7 lifetime trial downloads | 20/month | 60/month, Studio exports exempt |
| **Commercial use** | No | Yes — only for outputs obtained as a permitted download | Same as Pro |
| **Weirdness slider** | No | Yes (0-100) | Yes (0-100) |
| **Style Influence slider** | No | Yes (0-100) | Yes (0-100) |
| **Audio Influence slider** | No | Yes (0-100, with a Persona, Voice or audio upload) | Yes (0-100, with a Persona, Voice or audio upload) |
| **Exclude Styles field** | No | Yes (Early Access Beta; 1,000-character cap; on v6 it steers rather than mutes) | Same as Pro |
| **Inspo** | No | Yes (unverified on v6) | Same as Pro |
| **Song Editor / Legacy Editor** | No | Yes (section replace, rearrange, crop, fade) | Yes |
| **Personas** | No | Yes (inside the Voices menu, not removed; how a pre-v6 Persona carries over to v6 is undocumented) | Same |
| **Voices** | No | Yes (voice cloning; works on v6 in this module's testing, though Suno's FAQ still documents v5.5 only; recording entry point now also on free) | Same |
| **Custom Models** | No | Yes (up to 3; 100 cr to train) | Yes (up to 3; 100 cr to train); shareable with up to 10 people per model |
| **Shareable Workspaces** (from 2026-10-15) | No | Yes (up to 10 collaborators) | Same as Pro |
| **MIDI upload in Create** (from 2026-11-04) | No | Yes (Simple mode, v6-wild, desktop web) | Same as Pro |
| **Speech (beta)** | Yes | Yes | Yes |
| **Suno MCP (beta)** | Yes (early-access sign-up; songs use credits) | Same | Same |
| **My Taste** | Yes (passive) | Yes (passive) | Yes (passive) |
| **Stem separation** | No | Auto Split (up to 12), Split from Mix — credit costs are in the Studio & Editor reference, "Stems" | + Advanced Split (~100 instruments, Premier only) |
| **Audio upload** | 8 min | 30 min | 30 min |
| **Add Vocals/Instrumental** | No | Yes | Yes |
| **Studio 2.0** | No | **No** | Yes |
| **Queue** | Shared | Priority | Priority, 10 concurrent |
| **Add-on credits** | No | Yes | Yes |

**Pricing display:** the pricing page shows $8 / $24 with a "Monthly / Annual save 20%" toggle, while press consistently reports $10 / $30 month-to-month. The likely reading is annual-vs-monthly, but two fetches on 2026-08-13 did not confirm it — quote the displayed figure and the toggle, don't assert a single monthly price. On 2026-11-13 the page newly shows $10 and $30 beside the yearly-billed $8 and $24 (OFFICIAL, [pricing](https://suno.com/pricing)).

**Credit model:** Every press of the Create button costs **10 credits** and produces **2 songs** (a pair to choose from — Suno always generates two takes for variety). This means: 50 credits/day = 5 Creates = 10 songs to evaluate. 2,500 credits/mo = 250 Creates = 500 songs. When budgeting credits for a session, count in **Creates (10 credits each)**, not individual songs. Replace Section and Extend also cost credits (amount varies by section length). On v6, Max Mode doubles the cost of a Create, and image or video inputs can cost more. **When daily credits run low:** Suno provides 50 bonus credits per day on all tiers, refreshing daily.

**What counts as one download** (OFFICIAL, [What counts as one download?](https://help.suno.com/en/articles/13926145), edited 2026-09-09): *"One song counts as one download, regardless of how many files or formats you download for that song."* *"Once a song has counted toward your download allowance, you can download it again without using another download."* A song's stems are part of the same download. Suno states no time window for the re-download. So the allowance counts songs, not files: a second format, a repeat download or the stem set of a song already downloaded uses nothing further, while each different song uses one. A download made through the Suno MCP is covered under "Suno MCP (beta)".

Free-tier Controls panel (formerly "More Options") includes: Vocal Gender, Manual/Auto Lyrics mode, Song Title only.

Pro/Premier Controls panel additionally includes: Weirdness slider, Style Influence slider, Audio Influence slider (with Persona, Voice, or audio upload), Exclude Styles, Personas, Inspo, and the Legacy Editor for section-level editing. **On v6 it also carries Duration (Auto or 0:10-6:00), Max Mode (2× credits), Variety (*Exact style* through *Unreasonably varied*; above *Exact* it rewrites the style prompt), and Personalize (applies My Taste)** — observed at Pro 2026-09-12; Free-tier availability not verified.

**Vocal consistency across songs:** Suno interprets the same style prompt differently on every generation. Descriptive prompt language (e.g., "breathy female vocal with indie folk phrasing") gets you in the right neighborhood but not an exact match. The **Persona** feature (Pro/Premier) is the only reliable way to lock in a consistent vocal identity across songs -- it reuses the vocal character from a source generation. If you are working on an album or project where songs need to sound like the same singer, Personas are essential.

**Voices — alongside Personas, not instead of them:** the **Voices** feature (introduced with v5.5) is the stronger tool for vocal consistency. Key differences: Voices is actual voice cloning (from a 15s-4min audio sample with anti-deepfake verification), while a Persona captures the style essence of a source generation. **Style Personas are not gone** — they live inside the Voices menu, and Suno's Voices page says the two "work together: pick a Persona for the sound and your Voice for the vocal" (whether the Create form takes both at once on v6 is unverified). Nothing official says how a pre-v6 Voice or Persona carries over to v6, so re-check one on v6 before relying on it. Pro/Premier only.

**Voices Skill Level dropdown:** When setting up a Voice, you select Beginner, Intermediate, Advanced, or Professional. This is **NOT cosmetic** — it actively reshapes how the model interprets your voice. Testing found Professional produced the most stable, consistent, most usable results across every test. **Always set to Professional** regardless of actual singing ability.

**Voices limitations:** Voices is directional influence, not true vocal reproduction — the output drifts across generations and lacks true identity consistency (JG BeatsLab testing). Realistic for demo vocals, pre-production emotional direction, and hearing yourself in new compositions. **Not suitable for** final release vocal identity branding, or spoken word/narration (Voices drifts toward singing patterns, inconsistent tone between sections, unnatural pacing in longer spoken passages — Suno remains music-first).

**Audio Influence — two different slider behaviors depending on what is loaded.** The **Persona** slot has a narrow effective range (**15-25%**, 25% default); the **Voice** slot runs much higher and is goal-dependent. Start a Voice around **50%** and iterate in 5-10% increments.

Community testing (JG BeatsLab, March 2026) puts diminishing returns past ~70%, but that is **general guidance, not a ceiling** — Suno's own escalation for a clone that doesn't sound right is to *raise* Audio Influence first and rebuild the profile from a clean acapella second, and module production profiling of one voice found clean results at 85% where 55% showed artifacts. Profile per voice.

**Intent-split values:** 70+ to preserve source character, 80 to stop invented intros on covers, 50+ to stop invented lyrics, 30-40 to let a strong style prompt through. The suno-style-prompt-builder skill holds the full table and returns the value for a package; use what it returns rather than a range from memory.

---

## Platform Changes — 2026-11-13 (week-ten check)

Graded as elsewhere in this file; SECONDHAND marks a claim one user relays from someone else. What users report about the two new features is in "MIDI and Audio Guides" and "Suno MCP (beta)".

- **No model change announced** (OFFICIAL, by absence): the release notes from 2026-10-28 to 11-13 are Suno MCP (10-28), a Studio update (10-29) and the Daily Song Challenge (11-06) — no new model, no deprecation. The Terms are unchanged (last revised 2026-08-10, effective 2026-09-03).
- **MIDI upload in Create, 2026-11-04** (OFFICIAL, [blog](https://suno.com/blog/MIDI-in-create), [help](https://help.suno.com/en/articles/14594177)): a `.mid` or `.midi` file starts a song. *"At launch, MIDI uses Simple Create mode with v6-wild"*; it is *"available to all Pro and Premier subscribers"*, and *"MIDI upload is available on desktop web"*. *"Your MIDI shapes the bones of the song. Your prompt shapes everything else."* *"We plan to expand MIDI capabilities over time"*. No release note covers the launch. See "MIDI and Audio Guides".
- **Suno MCP (beta), 2026-10-28** (OFFICIAL, [help](https://help.suno.com/en/categories/2817153-suno-mcp-beta), [suno.com/mcp](https://suno.com/mcp)): *"Connect Suno to Claude, ChatGPT, Claude Code and other MCP clients"*. *"Available on all Suno plans. Songs use your credits."* Access is by *"Sign up for early access"*. The server is `https://api.suno.com/mcp`, with an OAuth sign-in and no API key; in Claude Code, `claude mcp add --transport http suno https://api.suno.com/mcp`, then `/mcp`. See "Suno MCP (beta)".
- **Studio, 2026-10-29** (OFFICIAL, release note): Clip Settings sidebar, Clip Info panel, auto-stretch of added audio, fine pitch in semitones and cents, show/hide tracks, grid density — all Studio, so Premier only. **Studio Chat** got a blog post the same day: [Meet Chat: Our In-house Studio Assistant](https://suno.com/blog/studio-chat-assistant). See the Studio & Editor reference, "Studio updates since 2.0 shipped".
- **Speech (beta) is on all plans** (OFFICIAL, [help](https://help.suno.com/en/articles/14617089)). Speech now has help articles (new 2026-11-06 to 11-07), which replaces the 2026-10-28 note that it had none.
- **Shareable Workspaces** (OFFICIAL, [help](https://help.suno.com/en/articles/14616961)): up to 10 collaborators. Sharing one still takes Pro or Premier.
- **Custom Model sharing** (OFFICIAL, [help](https://help.suno.com/en/articles/14616897), 2026-11-06): Premier only, up to 10 people per model. The [Custom Models page](https://suno.com/custom-models) still says models *"can't be shared"*, and *"2x the inputs"* is still explained nowhere — don't quote a number for it.
- **Pricing and download caps unchanged** (OFFICIAL, [pricing](https://suno.com/pricing), page captures 2026-10-25 to 11-13): Pro 2,500 credits and 20 downloads a month, Premier 10,000 and 60. What counts as one download is under "Plan Comparison".
- **No official text names a v6 model for Voices** (OFFICIAL, by absence): the [Voices FAQ](https://help.suno.com/en/articles/11362433) (edited 2026-03-26) still says v5.5, and ["How do I change models?"](https://help.suno.com/en/articles/13924993) (edited 2026-11-06) says only *"make sure you're on a compatible model"*.
- **Watch items — user reports, not announcements** (2026-11, low confidence): users report new model names in the front end ("junco", "junco wild", "v6-i"); one relayed claim speaks of a *"silent update within the v6 family"* (SECONDHAND); and Studio V1 is said to close in December (SECONDHAND). Suno has announced none of them. **For Mac:** don't state any of these as fact. If a user asks whether the model changed, say Suno has announced nothing, say what users report, and point to the [release notes](https://suno.com/release-notes).

## Platform Changes — 2026-10-28 (week-eight check)

Graded as elsewhere in this file.

- **No model change** (OFFICIAL, by absence): no new model or deprecation, and no change to pricing (the pricing page text is identical from 2026-10-14 to 10-28), the Create page, or the help center beyond one playback-only article (iOS AirPlay, 2026-10-23). Speech still has no help article or published terms.
- **Sharing, read from the release note's raw text** (OFFICIAL, [release note](https://suno.com/release-notes/collaboration-on-suno)): shareable Workspaces are *"Pro and Premier users only"*; shareable Custom Models *"Now, with 2x the inputs. Premier users only."* The Custom Models help article, the [suno.com/custom-models](https://suno.com/custom-models) FAQ (*"can't be shared, published or selected by other creators"*) and the Workspaces help article (no sharing language) all still lag it. On Pro, only Workspaces sharing applies.
- **Voices FAQ is stale** (OFFICIAL, [Voices FAQ](https://help.suno.com/en/articles/11362433), last edited 2026-03-26): it still says to select v5.5 and that *"Other models do not support"* Voices, while every pre-v6 model is retired. Official v6 support for Voices is therefore undocumented; Voices work on v6 in this module's own testing. See "Voices on v6" in the style prompt builder's `model-prompt-strategies.md`.
- **Studio 2.0 video, 2026-10-19** (OFFICIAL): automation, the expanded wavetable synth, and the gate — all Studio, so Premier only.
- **Uploads of the user's own recordings can be flagged as copyrighted** (COMMUNITY, 24 users, 2026-10; support replies SECONDHAND), hums included; re-uploaded Suno songs get flagged too. Support, as one user relays it: *"there is no way for us to manually clear the flag on a per-upload basis right now"*. **For Mac:** when a package starts from an upload, say it may be flagged, and plan for a re-record; a wrongful flag goes to support. The feedback elicitor's `technical-resolution.md` carries this for its upload-based repairs.
- **For Mac:** when a help article and a release note disagree, the release note is the newer source. Say which one a claim comes from, with its date.

## Platform Changes — 2026-10-15 (week-six check)

Graded as elsewhere in this file. The repair guidance from this check lives in the feedback elicitor and the style prompt builder.

- **No model change** (OFFICIAL, by absence): no new model or deprecation, and no change to pricing, the Create page, or Replace Section since 2026-10-05. Every pre-v6 model is retired; v6 and v6-wild are Pro and Premier, v6-mini is every plan.
- **Albums, 2026-10-05** (OFFICIAL, [Albums FAQ](https://help.suno.com/en/articles/14227009); VENDOR for the publish screen): an album holds only your own songs; LP or EP is just a label; tracks, order, title, description and cover stay editable after publishing. **Publishing an album publishes every unpublished song in it**, and the publish screen says this *"can't be undone"*. No streaming distribution, and no published track limit or plan requirement.
  - **For Mac:** sequence and choose the songs before an album is published, since publishing makes every track public at once. The suno-playlist-sequencer skill orders the tracks; Suno's Albums is where the result can be published.
- **Sharing, 2026-10-15** (OFFICIAL, [release note](https://suno.com/release-notes/collaboration-on-suno)): Workspaces can be shared with invited people (Pro and Premier); Custom Models can be shared with collaborators, *"Now, with 2x the inputs"* (Premier only). Suno's Custom Models help page still says models *"cannot be shared"*, and nothing official defines "2x the inputs" — don't quote a number. The live UI text does give the mechanics: collaborators generate on their own credits, can't edit, delete or re-share, never see the training songs, and keep songs they made after removal.
- **Studio, 2026-10-08** (OFFICIAL): timing, clip-stretch and fade-curve update — see the Studio & Editor reference, "Studio updates since 2.0 shipped".
- **Exclude misses things on v6** (COMMUNITY, four or more users, 2026-10-10 to 10-15): the bass kick, vocal gender ("no female vocals"), vocal stutters and repeats, a synth loop, and the opening swell all reported coming through anyway. A support bot reply, as one user reports it, calls ignored vocal gender and *"broken negative prompts"* *"known limitations"*. Negatives still belong in Exclude — the one exception reported since is a v6-wild Cover user's natural-language negatives (ANECDOTAL, 2026-10-28 sweep) — but tell the user it is guidance, not a mute, and plan a fallback (regenerate, then Replace Section or crop).
- **Remaster makes v6 songs worse** (COMMUNITY, five or more users): artifacts, noise, or lost crispness. See the Studio & Editor Reference → Remaster.

## Platform Changes — 2026-10-03 (week-five check)

Graded as elsewhere in this file. The full prompting and repair guidance from this sweep lives in the skills that apply it (listed at the end of this section).

- **No model change since launch** (OFFICIAL, by absence, checked 2026-10-03). There's no v6.1. The newest help-article edit is 2026-09-09; the app builds since then say only "bug fixes and performance improvements". The v6 guidance in this module is now about three weeks old.
- **Speech (beta), 2026-10-01** (OFFICIAL): a separate spoken-word model that *"generates voice and music together as one cohesive track."*
  - It has a **Custom Script** box (the words) and a **Style** box (the delivery and the music). Advanced mode adds Variety, vocal gender and a background-music switch (on by default). Length is *"up to around 8 minutes"*.
  - Script advice: *"Plain paragraphs work best"* with no lyric formatting or bracketed section tags. That applies to Speech only; song cues don't change.
  - Suno names *"poetry, a monologue, narration"* as uses. One known issue: *"Dramatic pauses may be very dramatic."*
  - **Not stated:** credit cost, tier limits, and whether Voices work with it. Early Reddit reaction is mostly negative (mispronunciations, gasping breaths) (COMMUNITY).
  - **For Mac:** a possible route for a spoken piece, as an alternative to `[Spoken Word]` inside a song. **Untested here.** Offer it as an option, and say so. The song pipeline (style builder, lyric transformer) is built for songs, so a Speech script is plain paragraphs, not a transformed lyric sheet.
- **A Persona and a Voice "work together"** (OFFICIAL, Suno's Voices page, undated, first archived 2026-09-25): *"Does Voices replace Personas? No… They work together: pick a Persona for the sound and your Voice for the vocal."* This contradicts an earlier vendor compile ("Personas are now Voices"). **Whether the Create form takes both at once on v6 is unverified in the UI.** The "Persona = sound" wording is marketing copy, not tested behaviour. The same page says *"a clean acapella gives the best results."*
- **Custom Models picked up v6 automatically** (OFFICIAL, Suno's Custom Models page): *"including its section editing and multimodal inputs."* They need at least six songs, cost 100 credits to train, train in about 2–5 minutes, and Pro and Premier hold up to three. Feature support is per model: if an attachment isn't supported, the form switches the model or drops the attachment, so check the picker. Results for heavy lanes are split (ANECDOTAL ×3).
- **Exclude Styles cap: 1,000 characters** (the live page markup, `maxlength="1000"`). The form's own counter is the final word. An earlier "no cap" claim doesn't hold for the web form.
- **Suno's EQ blog** (OFFICIAL, 2026-09-29, Studio): a muddy vocal *"is fighting other instruments in the same frequency range"*; the fix is a low-mid cut (*"start with -6dB at 400Hz"*). That's a **mix-stage fix, not a prompt lever**, and Studio is Premier-only. It frames the problem the way this module does: the band competing with the voice. On the prompt side, the answer is giving the band a job that leaves the voice room.
- **"Premier gets better models than Pro"** was claimed and refuted (COMMUNITY): *"The differences are all outside of the models."*

**Where the rest of this sweep went:**
- Style-side guidelines (the band's job instead of gravity words, chorus job vs feeling, vocal-space phrasing, `key change` in Exclude, Voice character words) and the measured outside evidence (Style Influence 100 = 85; Variety's per-take rewrite, which Exclude survives): the suno-style-prompt-builder skill applies them.
- Lyric-side items (mood tags on bare sections, `[Silence]` on rushing lines, line-start duet tags, spoken drift, `[Instrument: X In/Out]`): the suno-lyric-transformer skill applies them.
- Reading results and repairing a near-keeper (trust the audio over the song page, tempo miss as a listening cue, the repair ladder, late-song degradation reports, the stripped final chorus): the suno-feedback-elicitor skill applies them when it diagnoses a take.

## Platform Changes — 2026-09-09 (v6)

OFFICIAL unless graded otherwise. Sources: [v6 FAQ](https://help.suno.com/en/articles/13924481), [Current Models: v6](https://help.suno.com/en/articles/13924737), [What's new in v6](https://help.suno.com/en/articles/13924801), [Introducing v6](https://suno.com/release-notes/introducing-v6).

- **Three models:** `v6` ("reliable, precise") and `v6-wild` ("built for experimentation", less predictable) for Pro and Premier; `v6-mini` for everyone, including Free.
- **Every pre-v6 model is retired.** Existing songs stay playable; new iterations of them run on v6. **Custom Models were upgraded to v6 automatically.** Nothing official says how pre-v6 Voices and Personas carry over — early user reports are split, so re-check a clone on v6 before relying on it.
- **Credits unchanged:** a Create is still 10 credits for two songs (image/video inputs can cost more). **Max Mode costs 2×.**
- **Up to 8 minutes per generation.** Style and lyrics limits unchanged at 1,000 / 5,000 (VENDOR, day-one test).
- **New capabilities:** plain-language section editing, single-lyric or single-word updates without regenerating, multi-source mashups, sample-isolate-build, and starting from text, audio (voice memos), images, or video. Launch-week reports say section edits are uneven — some come back as a different take — so the Song Editor's trim and replace stay the deterministic path (COMMUNITY).
- **v6 Create sidebar layout (live UI screenshots, Pro, 2026-09-17 — the Controls panel replaced "More Options"):** top to bottom — Song / Sounds toggle with the model picker (v6) at top right; a **"Describe your song"** text box with a "Controls" chip (the natural-language prompt; leave it empty for a custom lyrics-plus-style package); **Optional controls** chips: + Audio, + Voices, + Inspo; **+ Lyrics** (expands); **Styles** (a tag-chip field with a library button, a magic-wand suggest button and a refresh); a **Controls** panel: Exclude styles, Vocal Gender (Male / Female), Duration (Custom / Auto), Max Mode (Off / On), Weirdness, Style Influence, Audio Influence (appears when a Voice or Audio is loaded), Variety (leftmost notch "Off", with a reset icon), Personalize (My Taste, Off / On); then **Song Title (Optional)** and **Save to…** (a workspace/folder picker — send the take to that band's own workspace so it lands with the rest of that band's songs; e.g. a band with its own workspace gets a package Save to line naming that workspace); then the Create button. Defaults seen: Weirdness 50, Style Influence 50, Variety Off, Personalize Off, Max Mode Off, Duration Auto. **Interface in flux (observed 2026-09-17):** the "+" at the bottom-left of the Describe box opens a drop-down listing much the same controls as the advanced fields, so Suno may be moving toward the single Describe box as the main entry point. Until that settles, packages keep the Lyrics / Styles / Controls workflow as documented here.

- **The "+" attachment menu (live UI screenshots, Pro, 2026-09-17).** The "+" at the bottom-left of the Describe box opens: **Lyrics ▸ · Styles ▸ · Playlist · Image · Video · Audio ▸ · Voices ▸** (Voices expands to *Use Voice* / *Add new*; the ▸ items open submenus). Notes:
  - **The order is not the sidebar's order**, and it carries three inputs the Controls sidebar has no row for: **Playlist, Image, Video**. Image and Video are presumably the multimodal inputs v6's launch copy advertised ("create with text, audio, images and video"); what **Playlist** does as an input is unknown — it may attach a playlist as reference material or set where the song saves. Untested.
  - **Mac's package order does not change.** Keep presenting Voice → Lyrics → Style → Exclude → Settings → Title → Save to → Wild Card, which follows the sidebar. For a user who works from the "+" menu instead, the same fields are reached in that menu's order — name the field, not the position, if they ask where something goes.
  - The Lyrics field's own placeholder confirms the instrumental route: *"leave this empty for instrumental."*
- **Where section editing lives (v6, observed in the live UI 2026-09-12):** open the finished song's ⋯ **More Actions** menu → **Edit** → **Replace Section**. That opens the **Create form** with the song attached as **Audio** and the panel's mode dropdown set to **Replace section**. Select the span on the waveform, or type start and end times. The span can run anywhere up to the whole song, and lining it up precisely is fiddly. The Voice, the **full** Lyrics box, the **full** Styles box and the Controls panel all stay editable, and there's **no separate plain-language instruction box**. The launch note's "edit… using plain language" most plausibly means editing the Styles and Lyrics boxes for the replaced span (inference, untested). Suno's older help text describes a lyrics-only box; treat that detail as pre-v6. One early report says edits still shift voice and melody (ANECDOTAL), so judge the seams by ear.
- **Plain-language editing is a Simple-mode feature** (VENDOR ×2, quoting Suno's announcement): "In Simple mode, the model works out which creation or editing operation the instruction calls for, reducing the need to choose separately between tools such as Cover, Remix and Extend." Suno's examples are "Change the chorus so it's sung by a gospel choir" and "Change the lyric from 'love' to 'light.'" This is why the Advanced/Custom Replace-section view has no instruction box. The route is untested here, and section edits reportedly can rewrite more than requested.
- **Cover vs. Inspiration for re-cutting your own songs:** a Cover tracks the original closely. Some users prefer the Inspiration option instead, believing Covers limit re-use and monetization (unverified — check Suno's current terms). A sound workflow: generate fresh first, and reach for Inspiration only if the original is far better than anything new.
- **Fade In / Fade Out** (observed on Pro, 2026-09-12; how-to 2026-09-14): a finished song's Edit menu has Fade In and Fade Out options. On v6 the fade is set in an expandable Fade Out section of the song's Create panel, and hitting Create makes a new, faded version. To end on a chosen chord, Crop first (a new version), then Fade Out that cropped version. See the Studio editor reference. Use them after generation to fix an ending that trails or stops wrong, rather than re-rolling or fighting it with end tags.
- **Training data:** "trained from the ground up… on a new set of data" — licensed music from Warner Music Group and BMG, participating Believe/TuneCore artists, and user data. Which catalogs, and how much, is undisclosed.
- **How it prompts (PREVIEW):** production direction rather than a descriptor list; negatives only in Exclude Styles; **Variety at *Exact style*** unless you want the prompt rewritten; Style Influence reportedly defaults to 50. The suno-style-prompt-builder skill applies the full treatment.
- **Where it struggles (COMMUNITY):** late-song degradation in longer tracks, and the heavier genres — metal and high-gain guitar above all. Fidelity is widely described as cleaner than v5.5 while character is described as flatter; results are strongly genre-dependent.

**What Mac should do differently:** build every package for v6. The wild card stays on v6 with the same sliders and inside the band's core sound; running the unchanged primary prompt on v6-wild is an optional alternative wild card. put Variety, Max Mode, Duration, and Personalize in the Settings block, and treat the rest of this file's model-specific advice as history until it is re-confirmed on v6. Tell a user plainly that v6 guidance is still young (the model hasn't changed since launch, as of 2026-10-03).

## Platform Changes — 2026-08-13

Everything in this section is OFFICIAL unless graded otherwise. Confidence grades follow the module convention: OFFICIAL = Suno-documented, COMMUNITY = multi-source replicated, ANECDOTAL = single source.

### Downloads are capped from 2026-09-03 — and that changes the workflow, not just the plan

Sources: [Download limits FAQ](https://help.suno.com/en/articles/13614785), [ToS update blog](https://suno.com/blog/suno-updates-tos) (2026-08-10), [Terms effective Sept 3 2026](https://suno.com/terms-september-2026).

- Free: **7 lifetime** trial downloads, personal and non-commercial, no reset. Pro: **20/month**. Premier: **60/month**. Allowances reset on the billing date with **no carryover**; extra downloads are purchasable. **Studio exports are exempt** (Premier).
- **Retroactive to the entire back catalogue** — the cap applies to songs made before September 3 too.
- One song counts once regardless of format or repeat downloads; **all stems of a song are part of that song's single download**; failed downloads don't count. Streaming and on-platform sharing stay unlimited. Suno's own wording, from [What counts as one download?](https://help.suno.com/en/articles/13926145) (edited 2026-09-09): *"One song counts as one download, regardless of how many files or formats you download for that song."* and *"Once a song has counted toward your download allowance, you can download it again without using another download."* No time window is stated.
- **Commercial rights now attach to the download, not the tier.** The new ToS permits commercial exploitation only of outputs obtained through a permitted download; obtaining a copy any other way is prohibited, and so is removing or obscuring fingerprints, watermarks, or metadata. Downloaded outputs keep perpetual commercial rights even after a downgrade.
- **Remixes are jointly owned and non-commercial on every tier** — "a joint work owned jointly and equally by you and the Remixer," for "personal and non-commercial purposes" only.

**What Mac should do differently:** treat downloads as a budget the user spends, not a free action at the end. Selection moves *before* download — audition takes on-platform, then download the keeper. Say so plainly when a user is on Pro and iterating hard: twenty a month goes fast when a song takes four Creates. Don't suggest downloading every take "just in case." And never suggest anything that strips or defeats watermarking or fingerprinting — that is a ToS violation as of September 3, regardless of how it is framed.

### All current models are slated for retirement — versions and dates are NOT published *(superseded 2026-09-09: every pre-v6 model is now retired — see "Platform Changes — 2026-09-09 (v6)")*

Sources: same as above, plus [BMG partnership](https://suno.com/blog/suno-partnership-bmg) (2026-08-12).

- "New models launching soon will retire older versions." Retiring means you can no longer generate *new* songs with that model; existing songs stay playable and shareable exactly as they are.
- **No official source names which versions or when.** Third-party outlets claim v3.5/v4/v4.5/v5 are going; that is not confirmed — do not repeat it as fact.
- **Extends, Covers, and remixes of existing songs will run on the NEW models** — "results may sound different from the original generation." Flag this to a user planning to Extend or Cover an older catalog track.
- The successor is "our first music model developed with the music industry" (BMG global deal). No name, date, or tier gating announced.
- **VERIFIED-ABSENT: nothing official says what happens to Voices or Style Personas built on retired models.** (Custom Models are covered: Suno upgraded them to v6 automatically — see "Platform Changes".) The FAQ is silent. If a user asks whether their Voice survives, the honest answer is that Suno hasn't said — and that the band profile's recorded recipe (source song, model version, settings) is what makes a rebuild possible if it doesn't.
- **Suno's own "Model Information" help category is stale** — articles from Sept 2025 still call V4 "the latest model." Do not cite it as current: [help.suno.com/en/categories/1752193](https://help.suno.com/en/categories/1752193).

### Studio 2.0 (2026-08-13, Premier-only)

Studio was "totally overhauled": MIDI import/record/edit with piano roll and audio-to-MIDI, MIDI-as-prompt, a session-aware chat bar that generates instruments, vocals, and custom plugins, a wavetable synth, audio effects including sidechain compression and convolution reverb, automation curves, and 32-bit/48kHz multitrack export. **Nothing in Studio 2.0 reaches Pro.** The Studio 1.x feature names (Warp Markers, Remove FX, Alternates, EQ, Context Window, Sounds Mode, Stem Cover, Heal Edits, MILO-1080) are **not in current official copy** — Suno moved those articles into a "Studio Archive." No community field-testing exists yet. The current Studio and editor tools are in `references/STUDIO-EDITOR-REFERENCE.md`.

**VERIFIED-ABSENT:** nothing states that Studio 2.0 replaces or deprecates the Song Editor / Legacy Editor. Replace Section is documented live at Pro today. Assume coexistence.

### Duration slider (2026-07-20, web, v5.5 only)

A Duration slider in the web Create form sets target song length. Suno published no range, but the endpoints — **10 seconds to 6:00** — are verified in live UI (Pro account, 2026-08-14); the 5-second step granularity is COMMUNITY-attested and unverified. Pre-generation only, **and it requires Style set to Custom**. Characteristic failures run in both directions: a hard cutoff at the target; rushed delivery or skipped sections on short targets (the model bends BPM and crams syllables to hit the number); and on long targets a **premature end followed by a restart** rather than trailing silence. **Adherence is inconsistent and the reports are starkly split** — one controlled batch matched 4 of 40, other users report near-perfect adherence, and nobody has explained the variance. It is worst on covers, remixes, extends, and custom models. Recommended handling: run **Auto** first to find the natural length, then set Custom at natural **+10-15s**, and always pair it with an explicit `[Outro]`. The "How long will my song be?" help article was not updated and still documents only Extend and the ~8-minute cap.

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

### Ecosystem: still no public API *(2026-10-28: an official MCP connection now exists — see "Suno MCP (beta)")*

Suno announced on 2026-07-01 that it is "exploring a developer API" beginning with a curated partner group, with an interest intake form. As of 2026-08-13 there is **no public launch date, pricing, portal, endpoint list, or documentation**. COMMUNITY. Every "Suno API" sold today is a third-party wrapper with no official standing — do not present one as a supported integration path.

**Update, 2026-11-13 check:** the paragraph above is the 2026-08-13 state, kept as history. On 2026-10-28 Suno shipped the **Suno MCP (beta)**: an official server that MCP clients connect to with an OAuth sign-in on the user's own account and no API key (OFFICIAL). That is now the supported way for an assistant to act on a Suno account — see "Suno MCP (beta)". This check did not revisit the developer API or the third-party wrappers.

---

## Package Field Mapping

Where each component of Mac's output package goes in Suno's Custom Mode:

| Component | What It Is | Where It Goes in Suno |
|-----------|-----------|----------------------|
| **Voice** (Pro/Premier) | A cloned voice | + Voices chip (if applicable) |
| **Persona** (Pro/Premier) | Vocal identity from a source song | Inside the Voices menu (if applicable) |
| **Inspo** (Pro/Premier; unverified on v6) | Playlist analysis for vibe channeling | + Inspo chip (if applicable) |
| **Lyrics** | Structured text with metatags | + Lyrics field (leave it empty for an instrumental) |
| **Style Prompt** | Sound description optimized for your model | Styles field (formerly "Style of Music") |
| **Exclude Styles** (Pro/Premier) | Comma-separated list of what to avoid | Controls panel, first row |
| **Vocal Gender** | Male/Female voice selection | Controls panel |
| **Lyrics Mode** | Manual (your lyrics) or Auto (Suno generates) | Lyrics toggle |
| **Weirdness** (Pro/Premier) | Creative deviation: lower = safer, higher = experimental | Controls panel |
| **Style Influence** (Pro/Premier) | Prompt adherence: lower = looser, higher = tighter | Controls panel |
| **Audio Influence** (Pro/Premier) | Resemblance to the attached Voice, Persona or upload (appears only with one attached) | Controls panel |
| **Model** | v6 (default), v6-wild (exploratory), or v6-mini (Free) | Model selector |
| **Variety** (v6) | How far Suno may rewrite the style prompt — *Exact style* keeps it as written. The slider shows shorthand labels — the leftmost notch reads **"Off"** (= *Exact style*) — and a finished song's page shows the rewritten style | Controls panel |
| **Max Mode** (v6) | Extra compute for consistency through the song; 2× credits | Controls panel |
| **Duration** | Auto, or a Custom target (0:10-6:00) | Controls panel |
| **Personalize** (v6) | Applies your My Taste profile | Controls panel |
| **Song Title** | Title for the generation | Title field |
| **Save to** | The band's workspace or folder, so the take lands with that band's songs | Save to… picker |
| **Wild Card Variant** | An experimental alternative style prompt | Optional -- try it if you want |

---

## Style Prompt Best Practices

Invoke the `suno-style-prompt-builder` skill: it holds the style-prompt, Exclude Styles and slider guidance and applies it when it builds a prompt, so a question about how to word a style prompt is answered by running it, not from this file.

---

## Metatag Reference

Invoke the `suno-lyric-transformer` skill: it holds the metatag catalog and the section-job framework and applies them when it tags lyrics, so a question about a tag is answered by running it, not from this file.

---

## Troubleshooting Suno Issues

This table covers problems with Suno's output, not with Mac himself.

### Prompt and Formatting Issues

| Issue | What Happens | Fix |
|-------|-------------|-----|
| **Silent truncation** | Style prompts over the character limit are cut off without warning | Keep within limits; front-load important content |
| **"Metal" in style prompt** | Triggers screaming/harsh vocals by default | Use "progressive heavy groove" if screaming not desired |
| **Negative prompts ignored** | "No screaming" in style prompt is unreliable | Use the Exclude Styles field (Pro/Premier) or positive language. On v6 Exclude itself steers rather than mutes, so plan a fallback: regenerate, then Replace Section or crop |
| **Brass/instrument bleed** | Instruments in style prompt appear globally | Move section-specific instruments to end of prompt; use `[Instrument: ...]` metatags |
| **Exclamation points** | `!` triggers bark/attack vocal delivery | Remove from clean sections; bleeds into following sections |
| **ALL CAPS everywhere** | Sets loudness ceiling in early sections | Use sentence case; save caps for one peak moment |
| **Dense punctuation** | Heavy punctuation confuses vocal cadence | Simplify; use commas and dashes intentionally |
| **Scream bleed-through** | Aggressive vocals carry into subsequent sections | Add `[Vocal Style: whispered]` reset after aggressive sections |
| **Sections sound flat despite energy tags** | Energy metatags alone don't drive tempo changes | Combine with line density changes (short lines = slow, packed lines = fast), half-time/double-time drum metatags (`[Heavy: halftime]`, `[Double Time]`), arrangement density changes, and Weirdness slider. Do NOT use BPM tags — they are confirmed ineffective. |
| **Persona style conflicts** | Persona's auto-style clashes with your style prompt | Persona auto-fills the Styles field -- keep additions simple (1-2 genres, 1 mood, 2-4 instruments max). Change ONE variable at a time (music direction OR Persona, not both). |
| **Unwanted instrument in wrong section** | Suno's style prompt is global | Move section-specific instruments to end of prompt, use `[Instrument: ...]` metatags, or generate sections separately via Legacy Editor (Pro) |

### Audio Quality Issues

| Issue | What Happens | Fix |
|-------|-------------|-----|
| **Vocal artifacts** | Robotic or glitchy vocals | Regenerate; the older advice to switch to v5 Pro no longer applies, since every pre-v6 model is retired |
| **Audio artifacts or glitches** | Random audio issues | Regenerate 3-5 times with the same prompt. If persistent, simplify the style prompt. |
| **Pronunciation issues** | Words sung incorrectly | Add phonetic hints in lyrics or use the `[Spoken Word]` metatag |
| **Timing feels wrong** | Rhythm or pacing issues | Premier: fix in Studio (Warp Markers were the Studio 1.x tool for this and are not in current Studio 2.0 copy — check the live UI). Pro: Replace Section on the offending span, or export stems and correct timing in a DAW |
| **Long song degradation** | Quality drops in extended generations | Generate shorter segments and use Extend carefully |
| **Voices spoken word/narration** | Voice drifts toward singing, inconsistent tone between sections, unnatural pacing | Suno remains music-first. Voices is not suitable for spoken word or narration — consider narration as a separate recording edited in via DAW |
| **Voices vocal artifacts at high Audio Influence** | Shimmer, warble, or robotic quality at the top of the range | Try 40-60% — but this is voice-dependent, not a rule: some voices are clean at 85%. If the complaint is "it doesn't sound like me" rather than "it sounds artefacty," Suno's official path is to RAISE it first, then rebuild the profile from a clean acapella. |

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
- **Covers have been documented as not eligible for commercial use** — even of your own songs. That was not re-checked against the September 2026 terms (which make Remixes non-commercial on every tier), so have the owner check Suno's current terms before a commercial release, and prefer a fresh generation from the original lyrics.
- Stacking Covers (re-covering within the same genre) can smooth cohesion
- To carry music written in advance (a MIDI part rendered to audio) through a Cover, see "MIDI and Audio Guides" below

### Remix Umbrella — Four Workflows
- **Cover** — re-sing in a different style/genre (preserves melody)
- **Extend** — add more to an existing song
- **Reuse** — reuse the prompt/settings from an existing song
- **Speed** — adjust playback speed

### Additional Tools (documented for the retired v4.5+ Pro; unverified on v6)
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

## MIDI and Audio Guides

For a user who has already written the music — a melody, a part, a pattern — and wants Suno to follow it. There are two routes: upload the MIDI file in Create, or render the part to audio and Cover it. On the 2026-11 evidence the audio route is the one more users report working, and both rest on a handful of users, so offer them as options to test, not as settled practice.

### MIDI upload in Create (OFFICIAL, 2026-11-04)

Sources: [Start Songs with MIDI](https://suno.com/blog/MIDI-in-create) (blog), [Using MIDI files in Create](https://help.suno.com/en/articles/14594177) (help).

- **Limits at launch:** *"At launch, MIDI uses Simple Create mode with v6-wild"*; *"available to all Pro and Premier subscribers"*; *"MIDI upload is available on desktop web"*. Upload a `.mid` or `.midi` file, or drag it onto the Create form, then write a plain-language prompt.
- *"Your MIDI shapes the bones of the song. Your prompt shapes everything else."* The prompt sets how closely the file is followed, from *"play your notes exactly as you wrote them"* to *"take a motif from the file and develop it into something new"*.
- Suno calls it *"different from existing Create modes, such as using Remix or Cover to adapt an uploaded audio (WAV or MP3) file"*, and says *"We plan to expand MIDI capabilities over time"*.
- **Not stated:** neither page mentions tempo, tempo changes, time signature, key, markers, velocities (beyond a generic "how hard"), lyrics, vocals, sliders or any file limit.
- **Not the same as MIDI in Studio**, which is Premier only: see the Studio & Editor reference, "Suno Studio 2.0" → "MIDI".

### What users report about MIDI upload (2026-11)

- **No Advanced mode, no sliders, no Custom Models** (COMMUNITY, 4 users, 2026-11). It is locked to v6-wild (2 first-hand users, 1 relaying), and *"Variety appears to be off by default"* (ANECDOTAL, one user).
- **Original files are often flagged** (COMMUNITY, 3 first-hand users, 2026-11): *"Most of them were flagged"*; *"every single original MIDI file flagged"*; and *"Our system matched this upload to a known recording"* on a file that had never been rendered to audio. No reported workaround for a flagged `.mid` states its result.
- **Outcomes are one user each** (ANECDOTAL, 2026-11). Short single-instrument patterns (40–60 second stems, no vocals) gave *"the best adherence I've seen in v6 so far"*. In a full song, another user *"cannot even hear the original midi itself"* and found Voices ignored. A third preferred running the MIDI through a soundfont and uploading the audio.
- **Through the Suno MCP** (ANECDOTAL, one user, one take measured): a 32-note melody uploaded as MIDI passed a copyright check and came back as two short instrumentals; all 32 notes sounded in order at pitch, plus 2 extra notes.
- **Nobody has reported** trying a tempo-only, marker-only or click-track file, how closely the notes are followed in general, or any size or length limit.

### Render the part to audio, then Cover it

Render the MIDI part to audio, upload it, and Cover it. This route keeps Advanced mode and the sliders (COMMUNITY, 4 users report it working and give results; 1 reports the opposite for orchestral music; 2026-11).

- **One user's settings** (ANECDOTAL): Weirdness 0, Audio Influence 85, Variety Off, with the note *"You don't need a full studio quality for input"*. In the same user's comparison this route kept their Voice where MIDI upload did not.
- **Audio rendered from MIDI gets flagged too** (COMMUNITY, 4 users, 2026-11), so the route doesn't avoid the upload filter.

### When an upload is flagged

Upload false flags are widely reported (COMMUNITY, 31 users; 3 report the opposite; 2026-11). Workarounds whose reporters state the result:

- **Trim the file, or retry the upload:** worked for 2 users.
- **Change the instrument sounds:** worked for one user, who gives only their own theory of the cause.
- **Chunk the file and rejoin the pieces** (contested): 1 user for, 1 against.

Suno's support, as one user relays it (SECONDHAND): *"There's no way to manually clear the flag for a specific upload right now."*

**For Mac:** offer the two routes with their evidence and let the user choose. Say that MIDI upload gives up Advanced mode and the sliders by users' accounts, and the Voice for the one user who compared. Don't promise that Suno reads a tempo map or a click track: nobody has reported trying one. Either upload may be flagged, so plan for a second attempt.

---

## Suno MCP (beta)

An official connection that lets an MCP client (an AI assistant) act on a Suno account, launched 2026-10-28. **The user connects their own Suno account from their own client.** Suno publishes no tool list, parameter schema, limits or download rule, and users saw the surface change twice between 2026-10-28 and 11-13. So read the tools and their parameters from the connected server, and treat every user-reported line below as a dated snapshot, not as documentation.

### What Suno states (OFFICIAL)

Sources: [Suno MCP (Beta) help articles](https://help.suno.com/en/categories/2817153-suno-mcp-beta), [suno.com/mcp](https://suno.com/mcp), the 2026-10-28 release note.

- *"Connect Suno to Claude, ChatGPT, Claude Code and other MCP clients"*. *"Available on all Suno plans. Songs use your credits."* Access is by *"Sign up for early access"*.
- **Server:** `https://api.suno.com/mcp`. Sign-in is OAuth; there is no API key. In Claude Code: `claude mcp add --transport http suno https://api.suno.com/mcp`, then `/mcp`.
- **Stated abilities:** songs from ideas, lyrics and conversation; covers, extends and mashups; speech; *"Upload audio and build on it"*; *"Check your plan and remaining credits"*; saved Voices.
- **Scopes** in the server's OAuth discovery document (read 2026-11-13): `api:v0`, `credits:spend`, `download`, `library:read`, `library:search`, `library:write`, `offline_access`, `profile:read`.

### Getting access (user reports, 2026-11)

The sign-up is a real gate (COMMUNITY): 6 users report getting in after signing up, one of them about a day later; 3 report no reply or no working connection. For one more user, account linking failed until Suno's acceptance email arrived (ANECDOTAL).

### What users report it exposes (2026-11)

- **A create tool** taking model, Voice, style, negative style, lyrics and sliders — one of 32 tools that one user's assistant listed on 2026-11-04 (ANECDOTAL, one user). Sliders take exact numbers (COMMUNITY, 2 users, 2026-11). For one user, separate lyrics and style with a named Voice worked in one call, and it made one song instead of two when asked (ANECDOTAL).
- **Variety** was absent on 2026-11-04 and present by 11-06 as a whole number from 0 to 4. **Max Mode** was missing from the 11-04 list, yet worked for one user at double the cost (ANECDOTAL, one user, about 150 clips). **Personalize (My Taste)** is absent in every report.
- **Edits, by 2026-11-07:** replace a lyric line, regenerate or add a section, remove an instrument, stems, MIDI. One user's outcomes (ANECDOTAL): replacing a line and adding a section worked; regenerating a 15-second section damaged the song; removing an instrument did not work; the four edits cost 75 credits.
- **Read-backs** of BPM, key, beats, sections, audio-derived tags and word timings (COMMUNITY, 3 users, 2026-11), free according to one of them. Their limits: the confidence value is always 1, beat numbering breaks, and the key may come back as the relative major. Word timings are contested: one user says they merely align the submitted lyrics to the audio; another says they *"show what was actually sung"*, including added lines.
- **A free "listen" tool** — Suno's agent answering questions about a clip — is inconsistent (COMMUNITY, 2 users, 2026-11). It *"contradicted itself between two listens of the same clip"*, and over ten runs it called a straight 88 BPM beat halftime eight times, while the measured BPM and key read-backs did not change.
- **How well a request is met** (ANECDOTAL, one user, about 150 clips): a requested tempo about 70% of the time, a requested key about 25%.

### What it costs (user reports, 2026-11)

- **Credits** (ANECDOTAL, one user's figures; a second user's 5 credits per song is the same rate): 10 credits a job for two clips whatever the length; 20 in Max Mode; joins and the listen tool free; stems and MIDI 10 each.
- **MIDI export is plan-gated for at least one user.** Of the 3 users who report exporting MIDI through it, the one who gives a cost paid 10 credits, on Premier. Another user, on Pro, was refused MIDI export as a Premier feature (ANECDOTAL).
- **Bad requests are run and charged** (ANECDOTAL, one user): a retired model, and an impossible extend point.
- **A download uses the download allowance, and the connector asks first** (COMMUNITY, 3 independent users, 2026-11): *"It can't stream or fetch audio, so anything that needs the actual file costs a download credit"*. One user's stem downloads did not reduce the allowance (ANECDOTAL). Suno states no download rule for the MCP, so how the one-song-one-download rule ("Plan Comparison") applies to a song downloaded through it is not established.

### What it cannot do (user reports, 2026-11)

- **Clips keep no record of what was sent** (COMMUNITY, 3 users): not the model, the sliders or the Exclude Styles. *"Keep your own log of what you sent"* — the package is that log.
- **No Studio access** (COMMUNITY, 2 users).
- **Excludes sent through it are not reliably honoured** (COMMUNITY, 3 users).
- **Uploads:** the upload filter applied through it for one user; one unverified report says uploads go through.
- **Assistants misread results** (ANECDOTAL, one user): one treated the prompt as the truth and called the audio wrong.

**For Mac:** when a user has this connected, list the server's tools before naming one, and say that the detail above is user-reported and dated. Keep the package as the record of what was sent, since the clip won't hold it. Use the read-backs (free, by one user's account) before anything that spends a download, and don't rest a diagnosis on a single listen-tool answer.

---

## Community Research Sources & Further Reading

> **Last updated:** November 13, 2026 (the newest source list below; the 2026-10-15 and 2026-10-28 checks cite their sources inline in their Platform Changes sections). These sources informed the findings in this reference. Suno evolves fast — verify claims against current platform behavior.

### Official Suno Documentation — 2026-11-13 check

- [Start Songs with MIDI (blog)](https://suno.com/blog/MIDI-in-create) · [Using MIDI files in Create](https://help.suno.com/en/articles/14594177) · [Suno MCP (Beta) help articles](https://help.suno.com/en/categories/2817153-suno-mcp-beta) · [Suno MCP page](https://suno.com/mcp)
- [What counts as one download?](https://help.suno.com/en/articles/13926145) · [Sharing Custom Models](https://help.suno.com/en/articles/14616897) · [Shareable Workspaces](https://help.suno.com/en/articles/14616961) · [Speech (beta)](https://help.suno.com/en/articles/14617089) · [How do I change models?](https://help.suno.com/en/articles/13924993)
- [Meet Chat: Our In-house Studio Assistant (blog)](https://suno.com/blog/studio-chat-assistant) · [Release notes](https://suno.com/release-notes) (Suno MCP 10-28, Studio 10-29, Daily Song Challenge 11-06) · [Pricing](https://suno.com/pricing)

### Official Suno Documentation — 2026-10-03 check

- [Introducing Speech (beta)](https://suno.com/release-notes/introducing-speech-beta) · [Voices page](https://suno.com/voices) · [Custom Models page](https://suno.com/custom-models) · [Suno blog: EQ](https://suno.com/blog/about-eq)

### Official Suno Documentation — v6 (2026-09-12)

- [v6 FAQ](https://help.suno.com/en/articles/13924481) · [Current Models: v6](https://help.suno.com/en/articles/13924737) · [What's new in v6](https://help.suno.com/en/articles/13924801) · [Introducing v6](https://suno.com/release-notes/introducing-v6)
- Day-one testing: [HookGenius v6 guide](https://hookgenius.app/learn/suno-v6-guide/) · [Jack Righteous — confirmed so far](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-next-music-industry-model-confirmed-so-far) · [Jack Righteous — problems](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-v6-reviews-problems-whats-next)

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
