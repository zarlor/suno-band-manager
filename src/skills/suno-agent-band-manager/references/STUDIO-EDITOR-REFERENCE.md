# Suno Studio & Editor Reference

Suno's post-generation editing tools: the **Song Editor / Legacy Editor** (Pro and Premier, section-level), **Suno Studio 2.0** (Premier-only generative DAW), stems, Remaster, Add Vocals / Add Instrumental and Covers. Models, plans and generation are in `references/SUNO-REFERENCE.md`.

## How to Load This File

This file is too large to read whole. Refine Song loads a section when a take needs an edit in Suno rather than a new generation, or when the owner asks how one of these tools works. List the headings with `grep -n '^##' {skill-root}/references/STUDIO-EDITOR-REFERENCE.md` and read from the section's heading to the next heading of the same level; a `##` section comes with its `###` subsections.

| When | Load |
|------|------|
| One section of a take needs replacing, a seam needs smoothing, or a sung word is wrong | Replace Section (Inpainting) |
| The take ends too soon or needs a continuation | Extend |
| An ending trails or stops wrong, or an intro or tail needs trimming | Crop / Remove · Fade In / Fade Out |
| Sections need reordering, or the displayed lyrics need correcting | Rearrange · Split · Edit Displayed Lyrics |
| A Premier owner asks what Studio can do, or a fix needs Studio | Two Editing Environments · Suno Studio 2.0 · Studio updates since 2.0 shipped |
| An instrument must leave one section, or the owner wants stems or a DAW mix | Stems |
| The mix is rough and a Remaster is being considered | Remaster |
| A vocal over an instrumental, or a backing over a vocal | Add Vocals / Add Instrumental |
| A Cover is being considered (a restyle, or a seamless re-render after a failed edit) | Covers in Editor Context |
| Deciding whether to keep editing or regenerate, or how many credits a song has absorbed | Editing Workflow Paradigm |
| Which plan has a tool | Tier Summary |
| An edit came back wrong | Troubleshooting |
| Whether an export counts against the download cap | Downloads Are Capped — and Studio Is the Exemption |
| Slider values for a generation inside Studio | Creative Sliders in Studio Context |
| Where a claim came from | Sources |

> **Last validated:** August 14, 2026 for the body of this file (Suno Studio **2.0**, Song Editor / Legacy Editor, v5.5 Pro; day-one primary-source field reports folded in), plus **Suno's September and October 2026 Studio release notes (latest added 2026-10-15)** and a v6 Remaster community note — see "Studio updates since 2.0 shipped" below. **Since 2026-09-09 every generation — including edits and extends of older songs — runs on the v6 family**; see "Editing Workflow Paradigm" for what v6 adds. Suno updates Studio features frequently — use web search to verify capabilities against current documentation when uncertain.

> **Studio 2.0 shipped 2026-08-13, and the Studio 1.x features are no longer documented here.** Suno "totally overhauled" Studio on 2026-08-13 ([release note](https://suno.com/release-notes/studio-2), [blog](https://suno.com/blog/studio-2) — OFFICIAL). Suno's own help centre now splits into a **"Studio 2.0"** category (11 articles) and a **"Studio Archive"** (14 articles) — [help.suno.com/en/categories/1708865](https://help.suno.com/en/categories/1708865). The Studio 1.x features (Warp Markers, Remove FX, Alternates, Quick Replace, EQ, Context Window, Sounds Mode, Stem Cover, Heal Edits, MILO-1080, 12-track stem export) **no longer appear in current official Suno copy**, so this file describes only what is current. **Take Lanes and comping are the exception — they survived into the current docs and are safe to recommend**; only the *Alternates* / *Quick Replace* names went away. If the owner asks for a 1.x feature by name, say it is not in Suno's current documentation and have them check the live UI before relying on it. **Field evidence is day-one only** — a primary-source pass on 2026-08-14 captured first user reports (see "Day-one field reports" below), but the software was hours old. Re-verify in a few weeks; this remains the highest-value open question in the module's Suno knowledge.

---

## Two Editing Environments

Suno provides two distinct editing tools:

| Environment | Tier | Purpose |
|-------------|------|---------|
| **Song Editor** (a.k.a. Legacy Editor) | Pro + Premier | Section-level waveform editor for quick fixes — replace, extend, crop, fade, rearrange |
| **Suno Studio 2.0** | Premier only | Full browser-based generative DAW — multitrack timeline, MIDI, AI generation, custom plugins, mixing, export |

**Key distinction:** The Song Editor works on individual songs. Studio works on multitrack projects with multiple clips, stems, and recordings on a timeline. Most Pro-tier users will use the Song Editor; Premier users get both.

**VERIFIED-ABSENT — does Studio 2.0 replace the Song Editor?** No official statement says it does. The Studio 2 blog, the Studio 2 release note, and help's "Introduction to Studio" were all checked on 2026-08-13 and none announce deprecation of the Song Editor / Legacy Editor; Replace Section is documented live at Pro today. The safe reading is **coexistence**. This is a verified absence of a claim, not positive confirmation.

**Tier availability is unchanged: Studio is Premier-only.** "Studio 2.0 is available exclusively to Premier tier subscribers" ([help](https://help.suno.com/en/articles/13670529)); "Available now for Premier subscribers" ([blog](https://suno.com/blog/studio-2)). **Nothing in Studio 2.0 reaches the Pro tier.** OFFICIAL.

---

## Downloads Are Capped — and Studio Is the Exemption

Effective **2026-09-03**, downloads are metered on every plan (the allowances are in `references/SUNO-REFERENCE.md` → "Plan Comparison", the "Song downloads" row), resetting on the billing date with no carryover, retroactive to the whole back catalogue. One song counts once regardless of format or re-downloads, and **all stems from a song are part of that song's single download**. Commercial rights attach only to outputs obtained as a permitted download, and stripping watermarks, fingerprints, or metadata is prohibited. OFFICIAL — [download limits FAQ](https://help.suno.com/en/articles/13614785), [ToS update](https://suno.com/blog/suno-updates-tos) (2026-08-10), [terms effective Sept 3 2026](https://suno.com/terms-september-2026).

**Studio is explicitly exempt:** Premier users "will still be able to download their work from Studio without limitation," and Studio exports 32-bit/48kHz multitracks and stems "without limitations." (Note for expectation-setting: Studio outputs are still watermarked — the exemption is from the *count*, not from provenance marking.) This changes the economics of the workflows in this file — for a Premier user, finishing inside Studio and exporting from Studio costs nothing against the cap, while exporting the same material from the Library does. COMMUNITY commentary notes the exemption sits awkwardly with the stated anti-mass-export rationale; that is context, not guidance.

---

## Song Editor / Legacy Editor (Pro + Premier)

### Access

From Library or Create view, click the three-dot menu (...) on any song → select **Edit**.

### Replace Section (Inpainting)

The most important editing feature. Regenerates a selected portion while preserving the rest. Suno uses surrounding audio context to blend new content seamlessly.

**How to use:**
1. Highlight a region on the waveform (see Tips below for the 15-20 second sweet spot)
2. Optionally modify lyrics in the Replace Lyrics box
3. Click "Replace Section" / "Recreate Section"
4. Two alternate versions appear in the Edits Library
5. Fine-tune transitions by dragging boundary lines on the waveform
6. Click "Generate More" for additional options

**Settings:**
- **Keep Duration / Make Same Length**: Toggle. ON = replacement matches original length. OFF = Suno has creative flexibility to extend or shorten — useful for adding solos, breaks, or drum fills.
- **Instrumental Mode**: Toggle. Removes vocals while preserving the music in the replacement.
- **Replace Lyrics**: Edit the lyrics for just the selected region.

**Tips:**
- **15-20 seconds** is the sweet spot for section length — under 5 seconds produces disjointed transitions, over 30 seconds and the model loses the melodic thread. 10-30 seconds works, but 15-20 is optimal (community consensus).
- Replace typically requires **2-5 attempts** for seamless transitions — generate multiple alternates
- Replaced sections may feel tonally mismatched; fine-tune by adjusting boundary lines
- Produces **higher vocal clarity** than Extensions due to enhanced internal blending
- "Prompt for identity, edit for reality" — prompts set genre/emotion/structure; edits fix timing, sections, and version selection
- Write 2-3 alternate lyric versions, then use Replace to hear each in context

**When to use Replace vs. full regeneration:**

| Situation | Recommendation |
|-----------|---------------|
| Structure and melody are good, one section has bad vocals | Replace Section |
| Structure is good, multiple sections need different fixes | Sequential replacements |
| Melody is wrong throughout | Full regeneration |
| Overall vibe/genre is off | Full regeneration with revised style prompt |
| Good material but wrong emotional direction | Full regeneration — emotion is global |

**Production-Tested Limitation (2026-04-29 — single-word fix attempt):**

Even at the documented sweet-spot scale (single-word / short-phrase target), Replace Section can produce **audible transition seams at the section boundaries**. Module production fix attempt: targeted a single word (`-ing` suffix dropped on "They call it living") with phonetic anchor `They call it liv-ing` in the Replace Lyrics box. **Both returned variations correctly fixed the targeted word** but **both also produced obviously audible joins** where the new replacement section met the surrounding original audio. Replace Section's localized-fix value is therefore bounded by transition-quality, not just by section size.

**Practical takeaway:** Even within Replace Section's documented sweet-spot, expect to evaluate transition smoothness alongside content correctness. If the fix lands the content but the seams are obvious, the song-level result may not be acceptable — fall back to Cover (full re-render preserving structure) or full re-gen with phonetic anchor in lyric source. Cover and re-gen produce single-coherent audio without seams; Replace Section's localized scope means transition seams are an inherent risk.

**Cost:** Pro and Premier currently receive free replacements up to 1,000 sections daily. After promotional period, each replacement costs 5 credits per Suno's documentation (4 credits / 2 variations observed in production 2026-04-29 — verify current cost via Suno UI before estimating credit budget).

### Extend

Adds new musical content as a continuation of the existing track.

**How to use:**
1. Click the plus icon at the far right of the track
2. Enter a custom prompt or select "Quick Extend" for seamless continuation
3. Use structural metatags (`[Chorus]`, `[Outro]`, `[Bridge]`) to guide what type of section is generated

**Tips:**
- Extensions generate ~30-60 seconds of additional content
- Extend first, then refine problem areas using Replace Section
- **62% of extended tracks drift from the original prompt** — keep extensions short (30s-1min increments) and match the style prompt exactly
- Include metatags to control section type

### Crop / Remove

Trims songs by selecting waveform ranges. Does NOT regenerate audio — it only removes portions.

**How to use:** Three-dot menu → Edit → Crop Song. Click and drag to highlight the portion to keep, then click "Crop Song." Edited version auto-saves to Library.

**Tips:**
- Good for removing long intros/outros, isolating sections, creating short-form clips
- Auto-fade is applied when cropping the end of a song
- Non-destructive to original — a new version is created

### Fade In / Fade Out

**How to use (v6, observed on Pro, 2026-09-14):** the song's Create panel has an expandable **Fade Out** section. Set the fade there and hit **Create**. Suno makes a new version with the fade applied; the original is untouched. Fade In presumably works the same way at the start of the song (not yet tried).

**Ending a take on a chosen chord (crop, then fade):** it's two steps, and each makes a new version.
1. **Crop** the song to just past the chord you want to end on (see Crop / Remove above). The cropped copy is a new version.
2. On **that cropped version**, apply Fade Out and hit Create.

The fade is what makes the crop sound natural instead of cut off. In production testing it worked on a take where a 25 s band tail followed the last sung line and there was no clean cut point without a fade.

*Pre-v6 description (validated 2026-08-14, may no longer match the UI):* Fade In/Out icons in the bottom corners of the first and last sections; click once to create a fade, hover to highlight the faded area, drag to adjust length.

**Tips:**
- A fade cannot be built in at generation: the `[Fade Out]` tag produces no fade, alone or paired with `[End]`. End the lyrics on `[End]` and apply the fade here
- Editor fades are applied post-generation and are more controllable

### Rearrange

**How to use:** Hover over a section name to see the grab tool, then click and drag to move the section. A plus icon between sections creates new content areas.

**Tips:**
- Good for swapping verses, moving choruses, reordering bridges
- Transitions may sound rough after rearranging — use Replace Section on the transition points to smooth them

### Split

Available via the More Actions button (three dots) on any section. Splits a section at a specific point, allowing independent editing of each half.

### Edit Displayed Lyrics

Controls publicly visible lyrics without changing audio. Fixes transcription errors, removes duplicated lines, cleans formatting. Typically a final polish step.

### Edits Library

The right panel that collects all alternate versions generated during editing. Browse, preview, and select the best take for each section. Click "Generate More" to create additional options.

---

## Suno Studio 2.0 (Premier Only) — CURRENT

Launched **2026-08-13**: "We have totally overhauled Suno Studio, our browser-based generative DAW, with features including MIDI, audio effects, built-in synths, and more." OFFICIAL — [release note](https://suno.com/release-notes/studio-2), [blog](https://suno.com/blog/studio-2), [help](https://help.suno.com/en/articles/13670529).

### Access

Select the **Studio** icon under **Create** in the left sidebar at suno.com. Desktop only. **Browser constraint:** Safari does not implement Web MIDI — Suno recommends Chrome ([help](https://help.suno.com/en/articles/13670593)).

### MIDI (the headline addition)

- Import, record, and edit MIDI on the timeline, with a piano-roll editor.
- **Audio-to-MIDI transcription** of existing clips.
- Web MIDI hardware controllers, plus **musical typing** with arpeggiator and chord mode.
- **MIDI as prompt:** a played or imported MIDI clip can be used as the prompt for a new audio generation, in place of text. This appears in the release note and blog but is *not* repeated in the MIDI help article. Suno's own framing de-emphasizes text prompting here ("no substitute" for playing the part) — vendor claim, ANECDOTAL as to how well it works, since no field testing exists yet.

### Chat bar

A session-aware chat bar that can "generate instruments and vocals, create new and totally unique plugins and synth presets." It is grounded in context (the focused track, the current selection, the project tempo), every chat edit is undoable, and chat history persists per project ([help](https://help.suno.com/en/articles/13670721)).

**VERIFIED-ABSENT:** no model name, credit cost, or usage limit is published for Studio Chat.

### Audio effects and custom plugins

- Built-in effects: Compressor, Convolution, Delay, Distortion, EQ, Gate, Reverb — the two Suno highlights are **sidechain compression** and **convolution reverb**.
- **Custom plugin generation via chat** — describe an effect ("warm tape saturation with a wobble") and it is generated, saved to a personal library, and supports presets and automation.
- **No VST or third-party plugin support** — only Suno's own synth and effects. COMMUNITY.
- **Plugin creation is credit-free "at launch,"** with a future credit structure signalled; multiple outlets flag the hedge. COMMUNITY — do not promise it stays free.

### Synth, automation, and mixing

- **Wavetable synth:** two oscillators, three envelopes, four LFOs.
- **Automation:** drawable curves for track and plugin parameters; MIDI Learn for hardware.

### Take Lanes and comping

Still in the current Studio docs (the 1.x names *Alternates* and *Quick Replace* are not). New content arrives as two versions in **Take Lanes** on one track: the main track shows Version 1, the speaker icons audition the others, and "Generate More" adds options. **Comping** selects the preferred portions of each take and copies them to the Main Track, so the best parts of different takes combine.

- Generate 2-6 takes with **one controlled change each** ("bigger melody / simpler drums", "same hook / stronger rhythm"); single-change takes keep the song's identity through comping.
- Audition in context, not solo. Pick the best overall take, then comp small details if needed.
- With too many versions to choose from, take the one that best supports the song's message rather than the coolest single detail, and move on.

### Export

Full song, selected time range, or multitrack, in **32-bit WAV or MP3**; individual stems as WAV ([help](https://help.suno.com/en/articles/13670529)). Suno's copy: 32-bit/48kHz multitracks and stems "without limitations." Studio exports do **not** count against the Sept 3 download cap.

### Day-one field reports (COMMUNITY / ANECDOTAL, 2026-08-13-14)

First-hand user reports from launch day. Small sample, hours-old software — but this is the only field evidence that exists, and some of it contradicts the marketing.

- **MIDI extraction is real and standard-format** — right-click a stem, "Get MIDI"; staff confirm the files import into other DAWs (Reaper named). ANECDOTAL, officially sourced.
- **The chat bar executes but misfires.** Three users independently critical, with verbatim failures: a mid-run stop ("Nothing in the selected area on this track to transform"), generated takes not surfacing in the UI, and the assistant denying the existence of a chat-history button that is on screen. One comparison: "a communication mess." COMMUNITY.
- **Markedly faster and snappier than the laggy 1.x** — two independent users. COMMUNITY. This is the clearest win reported.
- **Stem quality appears unchanged despite the upgraded-splitter framing** — a vocal stem "sounding nothing like the singer," out of sync, with audio bleed after the first hook. OP plus one confirmation. COMMUNITY. If a user upgrades expecting better stems, set expectations accordingly.
- **Hands-on regressions:** dB adjustments are integer-only by mouse, and the public-facing style description is hard to edit (you get either a rigid summary or the entire prompt string). Gains in the same report: a full effects suite including a limiter, and preset saving. ANECDOTAL.
- **In-Studio generation length: drag-select up to 8 minutes** (1.x capped stems at 4). Staff statement, unconfirmed. ANECDOTAL.
- **The synth accepts user one-shot samples** (about one per track), savable as presets. ANECDOTAL. Same thread reports the copyright filter firing on an *uploaded pure sine wave* ("Audio Matches an existing recording") — consistent with a month of upload-flagging complaints including a self-recorded improvisation.
- **Studio outputs are still watermarked** — reported even for original music with original lyrics through a custom model. Relevant because Studio's download exemption is sometimes read as an unrestricted export path; the provenance marking is still applied, and removing it violates the Sept 3 ToS.
- **The Studio download exemption caused real confusion on launch day** ("No download limit with studio 2.0" versus "documentation still says 60/mo — what am I missing?"). The official answer settles it: Studio exports are exempt, Library downloads are not.

### Quality caveats — carried forward from Studio 1.x, NOT re-tested on 2.0

MusicTech's 6/10 review of the Studio 1.x beta (2026-01-13) reported smeared transients, over-reverbed and over-polished vocals, "generic" Persona voices, a pull toward over-produced EDM, unpredictability despite detailed prompting, and credits burned on unusable regenerations; its conclusion was to use Studio as a **stem-and-MIDI source feeding a real DAW**. ANECDOTAL, and pre-2.0 — the overhaul may have changed some or all of it. Worth knowing before recommending Studio as a finishing environment; not worth asserting as current behavior. Source: [musictech.com Suno Studio review](https://musictech.com/reviews/digital-audio-workstations/suno-studio-review/).

---

## Studio updates since 2.0 shipped (OFFICIAL release notes; not testable here)

**Read this as vendor copy, not field evidence.** The entries below come from [Suno's release notes](https://suno.com/release-notes). **This module's own testing is on Pro, where Studio is not available** — nothing here has been verified in a live session, and no Studio claim should be presented to a user as confirmed. Suno's blog carries no Studio post after the 2026-08-13 Studio 2.0 launch.

### "Tighter timing, clip stretching and fade curves" — 2026-10-08 (Improvement / Bug Fix; Studio, Performance, Web)

- **Downbeat detection** is better, so clip timing is more accurate — including on a cappella vocals.
- **Clip stretching:** Shift-click-drag time-stretches a clip to the project tempo.
- **Fade curves:** fades can now be exponential or logarithmic; drag the node on the fade icon.
- **Pop-out windows** for the wavetable synth, the musical typing keyboard and expanded plug-in views.

**Why it matters for this module:** time-stretch to project tempo and shaped fades are the Studio route for a drum-only intro spliced in front of a take, or a tail that needs a gentler or faster fade than the Song Editor's — the prompt can't reliably produce either on v6 (see the feedback elicitor's technical resolution).

### "Suno Studio: Improved MIDI and more" — 2026-09-17 (New Feature / Improvement / Bug Fix; Studio, Web, Performance)

- **MIDI-to-audio transcription** is "faster, has more musical context, and is more accurate to the original."
- **Generate audio stems from MIDI via the chat bar** — ask the chat to turn a MIDI file into new audio stems, reported as giving precise results.
- **Bring in outside compositions:** upload work written outside Suno and reimagine it — Suno's example is converting a synth part into a different instrumental arrangement.
- **Clip renaming:** rename clips individually, or through the chat bar in bulk (e.g. "rename all my clips to reflect the track names").

**Why it matters for this module:** the MIDI path is the one route that takes a user's own composition *into* Suno's generative stack rather than editing what Suno produced. For a user who writes parts, this is the closest thing to arrangement control that exists — worth naming when a Premier user asks about getting their own musical ideas (not just prompts) into a track.

### "Updates to Suno Studio" — 2026-09-02 (Improvement / Bug Fix; Studio, Web, Performance)

- **Chat bar:** understands **tempo changes**; more reliable, with undo for prompt edits.
- **Plugins:** drag-and-drop between tracks; duplicate with cmd-D / ctrl-D.
- **Wavetable synth:** aliasing removed at high frequencies — "cleaner and more detailed synth sounds."
- **Performance:** faster audio playback, quicker project loads.
- **Bug fixes:** missing MIDI/MP3 files in exports, stuck MIDI notes, reversed-clip display.

**Note on the chat bar and tempo:** a Studio chat that understands tempo changes is the only place in the Suno stack where a mid-song tempo change is addressable at all — every text-prompt attempt at in-song half-time/double-time switching in this module's testing has failed on both v5.5 and v6. Untested, and Premier-only, but it is the standing answer to "can a song change tempo partway through?"

---

## Stems (Pro + Premier)

### What It Does

AI-powered separation of a mixed track into individual component tracks. Suno exports individual generation layers directly rather than performing post-hoc source separation, yielding cleaner results than third-party tools like LALAL.AI or Demucs.

### Three Modes (current — replaces the old 2-stem / 12-stem framing)

OFFICIAL — [Stem separation](https://help.suno.com/en/articles/12702337), fetched 2026-08-13. The legacy "Vocals + Instrumental" mode was **replaced by Split from Mix**.

| Mode | Output | Tier | Credit cost |
|------|--------|------|-------------|
| **Auto Split** | Up to 12 stems | Pro + Premier | 50 credits per extraction |
| **Split from Mix** | Split derived from the mixed audio — you get the extracted stem plus its complement | Pro + Premier | 10 credits per extraction (20 total for both stems created) |
| **Advanced Split** | ~100 instruments; choose which stems to create | **Premier only** | 10 credits per extraction; **20 total per stem**, because each extraction returns the chosen stem plus its complement (everything except that stem). Budget at 20 per stem. OFFICIAL — [help.suno.com/en/articles/12702337](https://help.suno.com/en/articles/12702337) |

**COMMUNITY:** Advanced Split reportedly regenerates tracks from scratch rather than filtering the mix — the basis for its artifact-free multitrack claim, with reduced noise and phase issues. It does not change how prompts are written.

**Download accounting:** from 2026-09-03, all stems from a song are part of that song's **single** download. Extracting and downloading a full stem set costs one download, not twelve — but it is the *same* download the song itself would have used.

### Auto Split Stem Categories

Vocals, Backing Vocals, Drums, Bass, Guitar, Keys, Strings, **Brass**, Woodwinds, Percussion, Synth, FX.

**Note:** Brass separates well as a dedicated stem — this makes stems the recommended approach for songs requiring section-specific instrumentation (e.g., brass only in the outro).

### How to Access

- **Library/Workspace**: Click More Actions (...) → hover over "Get Stems" → choose the split mode
- **Legacy Editor**: "Get Stems" icon at top right
- **Studio**: Stems panel — click arrow icons next to each stem to add to Timeline. Click three dots next to any stem's arrow for additional options. "Insert All" adds all stems at once.

### Processing

Takes 30-60 seconds depending on track length. Progress indicator shown. After completion, solo/mute individual stems during playback preview.

### Export Formats

- MP3
- WAV
- **Tempo-Locked WAVs** (stems set to average BPM of the song)
- MIDI files (Premier only; the Studio 1.x price of 10 credits per stem is unverified on Studio 2.0, so check the live UI before quoting one)
- WAV + MIDI bundles

### The Stems Workflow for Section-Specific Instrumentation

When a song needs different instruments in different sections and prompting alone can't achieve it:

1. **Generate** with ALL desired instruments in the style prompt (accepting bleed into all sections)
2. **Extract stems** — up to 12 individual tracks
3. **Edit in a DAW** (e.g., Audacity) — mute/remove unwanted instrument stems per section
4. **Export** the final mix

External DAW editing is a one-way operation. Once you edit outside Suno, you lose Suno's editing capabilities (Replace Section, Extend, etc.) on that version. Complete all Suno edits BEFORE exporting to a DAW. Always keep the original Suno generation as a source of truth.

**Mastering note:** Suno applies an aggressive mastering limiter. For professional release, export raw stems and mix in a dedicated DAW for proper EQ, compression, and spatial processing.

---

## Remaster (Pro + Premier)

### What It Does

Generates refined variations of existing clips by adjusting production details (instrument balance, audio effects, mix quality, sonic character, vocal clarity/pronunciation) while preserving core song structure.

### How to Access

Click three-dot menu on any clip → Create → **Remaster**.

### Variation Strength

| Strength | Effect |
|----------|--------|
| **Subtle** | Very close to original — only small acoustic/production details changed |
| **Normal** (default) | Maintains duration and style with minor musical adjustments |
| **High** | More noticeable differences, including possible changes to musical elements and vocals |

### What Remaster Does NOT Do

- Change lyrics
- Drastically alter musical style
- Replace the vocalist (use Cover instead)
- Modify timing or arrangement

### Community Observations

- Remaster is a **full regeneration** using the current model — NOT an EQ pass or filter. Creates 2 new versions and consumes standard credits.
- **'Improved fidelity with reduced soul'** — instrumentals benefit more than vocal tracks. Vocals can lose emotional intensity or edge.
- **Stacking** (remastering remastered tracks): Helpful for instrumentals and ambient/cinematic music. Hurts lead vocal clarity, emotional phrasing, and lyrical intelligibility.
- **Genre softening**: Aggressive styles (metal, punk) may lose their edge after remastering. Minor tonal drift after multiple passes.
- **One pass is usually sufficient.** 'Always trust the version that resonates' — don't chase fidelity at the expense of emotional feel.
- **On v6, Remaster is reported to make songs worse** (COMMUNITY, five or more users, 2026-10-12 to 10-14): added artifacts or noise, a washed-out sound, or lost crispness — "Every combination of remaster options made it sound worse." One user says it was never good in any version, and one says the mobile apps don't show the strength options. The suggested replacement is a **Cover with the same Voice**, but the settings offered conflict (Weirdness 20–30, Style Influence 0, Audio Influence 15–30 with an empty style box, versus Max Mode on, Weirdness 20, Style Influence 20–40, Audio Influence 80), and others say a Cover changes too much. Treat Remaster as the last thing to try on a v6 take, not the first.

Sources: [Suno Remaster Guide — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-remaster-guide-v4)

### Remaster vs. Cover

**Remaster** = subtle production polish (same identity). **Cover** = significant transformation (new genre, vocalist, arrangement).

### When to Use

- The song is 90% there but the mix feels rough
- Vocal clarity or pronunciation needs a nudge
- You want production polish without touching lyrics, melody, or structure
- Before exporting to ensure the best possible audio quality

---

## Add Vocals / Add Instrumental (Pro + Premier, Beta)

### Add Vocals

Layers a custom AI-generated vocal based on lyrics you provide onto an instrumental track.

**How to access:** Library or Workspaces → More Actions (...) on a valid instrumental track → "Add Vocals" → input lyrics → Create.

**Compatible tracks:** Uploaded instrumentals, generated instrumentals (via Instrumental toggle), or stems extracted from existing songs.

**Audio Strength slider** (Advanced Options): Determines how much the new vocal adheres to the existing instrumental. For best results, describe the existing instrumental + desired vocal characteristics in the style box.

### Add Instrumental

Generates instrumentation behind an existing vocal track.

**How to access:** Create → click audio button → upload your vocal track → trim if needed → hover over Remix/Edit → "Add Instrumental."

**Audio Influence** (Advanced Options): Set up to 100% for maximum adherence to original vocals. Suno transcribes lyrics automatically.

---

## Covers in Editor Context (Pro + Premier, Beta)

### Standard Covers

Recreates an existing song in a new musical style while preserving melody and structure. Generates a full re-performance, not a remix of the existing recording.

**How to access:** Three-dot menu → Create → **Cover Song**. Describe the new style. Optionally adjust lyrics.

**Compatible inputs:** Suno-generated songs, uploaded audio (demos, voice memos, loops), instrumentals, vocal tracks.

Covers have been documented as **not eligible for commercial use**, even of your own songs. That was not re-checked against the September 2026 terms, so have the owner check Suno's current terms before a commercial release, and prefer a fresh generation.

**Related, from the Sept 3 2026 ToS (OFFICIAL, [terms](https://suno.com/terms-september-2026)):** **Remixes** — where another user remixes your song or you remix theirs — are a *joint work owned jointly and equally by you and the Remixer* and "may only be used for lawful, personal and non-commercial purposes," on every tier. This is a separate restriction from the Cover limitation above; both point the same way, which is that anything derived from another rendering is off the commercial path.

### Stem Cover (Studio 1.x name)

Studio 1.x could cover an individual stem into a different instrument or sound while keeping its melody and rhythm. The name is not in current Studio 2.0 copy; have a Premier owner check the live UI before planning around it.

---

## Creative Sliders in Studio Context

When generating within Studio, the sliders behave the same as in standard generation but with these practical ranges:

| Slider | Conservative | Balanced | Experimental |
|--------|-------------|----------|--------------|
| **Weirdness** | 35-45 | ~50 | 55-70 |
| **Style Influence** | 70-85 | 60-70 | 45-60 |
| **Audio Influence** | 60-75 (dominant upload) | 40-60 | 20-40 (texture only) |

Audio Influence is only active when an upload or recording is used as a source.

---

## Editing Workflow Paradigm (v5.5 onward, including v6)

**v6 addition (OFFICIAL, 2026-09-09):** plain-language section editing and single-lyric or single-word updates without regenerating the song. Launch-week users report the edits as uneven — some come back as a different take with the same voice, or spill past the selected section (COMMUNITY). The Song Editor's trim and Replace Section stay the deterministic path.

Since v5.5, Suno has favored an iterative **generate → inspect → section replace → refine** workflow over full regeneration. This preserves good material and spends fewer credits.

### Recommended Workflow

1. **Generate** the initial output from the song package
2. **Inspect** the full result — evaluate structure, melody, emotional angle, and production
3. **Section replace** any sections that need work (preserve sections that are good)
4. **Refine** with targeted adjustments (delivery metatags, slider tweaks, specific prompt edits)

### Critical Checkpoint Questions

Before spending credits on regeneration:
- **Is the structure correct?** If yes, do NOT regenerate from scratch — use section replacement.
- **Is the melody usable?** A good melody with flawed production is worth refining. A bad melody needs regeneration.
- **Does the emotional direction justify more credits?** If heading the right way, refine. If the emotional core is wrong, regenerate.

### Credit Waste Prevention

Track your credit spend per song to avoid diminishing returns:
- **0-50 credits**: Learning and experimentation phase — explore freely
- **50-80 credits**: Apply discipline — target specific problems, stop perfection-chasing
- **80+ credits**: Stop editing and export — you're past the point of meaningful improvement

'Prompt for identity, edit for reality' — use generation for genre/emotion/structure, use Studio tools for execution problems (timing, wetness, take selection, arrangement).

Source: [Cut Credit Waste — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-studio-1-2-reduce-credit-waste)

---

## Tier Summary

Current as of 2026-08-13. Prices, credit allowances and download counts are in `references/SUNO-REFERENCE.md` → "Plan Comparison"; stem credit costs are under "Stems" → "Three Modes" above.

| Feature | Free | Pro | Premier |
|---------|------|-------------|------------------|
| **Song Editor / Legacy Editor** (Replace, Extend, Crop, Fade, Rearrange) | No | Yes | Yes |
| **Auto Split stems** (up to 12) | No | Yes | Yes |
| **Split from Mix** | No | Yes | Yes |
| **Advanced Split** (~100 instruments) | No | **No** | Yes |
| **Add Vocals / Add Instrumental** | No | Yes (beta) | Yes (beta) |
| **Covers** | No | Yes (beta) | Yes (beta) |
| **Remaster** | No | Yes | Yes |
| **Suno Studio 2.0** | No | **No** | Yes |
| **Studio MIDI / chat bar / custom plugins / wavetable synth / automation** | No | No | Yes (Studio 2.0) |
| **32-bit multitrack + stem export** | No | No | Yes (Studio 2.0) |
| **Song downloads** (from 2026-09-03) | Capped | Capped | Capped; Studio exports exempt |
| **Commercial use** | No | Yes, via permitted downloads | Yes, via permitted downloads |

**Studio 1.x features** (Warp Markers, Remove FX, Alternates, Quick Replace, EQ, Time Signature control, Context Window, Recording, Loop Recording, Sounds Mode, Stem Cover, Heal Edits, MIDI Export at 10 credits/stem, MILO-1080) were Premier-only when documented and are **not in current official Studio 2.0 copy**. Verify in the live UI before recommending any of them by name. **Take Lanes and comping are NOT archived** — they remain in the current Studio docs, so per-take auditioning and comping stay safe to recommend at Premier.

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Replaced section sounds tonally mismatched | Context blending imperfect | Fine-tune boundary lines; try 2-5 more replacements; reduce section size |
| Extended section drifts from style | 62% of extensions drift from prompt | Keep extensions short (30s-1min); match style prompt exactly; use metatags |
| Cover truncates around 3 minutes | Known Cover limitation | Generate shorter source; use Extend after covering |
| Remaster artifacts persist | Baked-in generation artifacts | Try Remaster at different strength levels; or regenerate from scratch |
| MIDI export doesn't match audio | MIDI extraction is approximate | Use as a starting point; hand-edit in your DAW |
| Time signature doesn't affect generation | Documented for Studio 1.2 as "not yet sent to generative models" — unverified for Studio 2.0 | Prompt for the desired meter via style prompt or lyric metatags either way; treat the picker as grid/editing alignment until re-verified |
| 'Scratched CD' effect — track loops/skips | v5 bug: repetitive loop in first 20 seconds | Regenerate — no known fix beyond regeneration |
| Replace Section lyrics don't update | 'Lyric Cache' bug on subsequent attempts | Use Cover on original source track with Persona selected to reinforce vocal identity, then generate new material |

---

## Sources

### Studio 2.0 and the Sept 2026 policy changes (fetched 2026-08-13)

- [Suno Studio 2.0 — Release Note](https://suno.com/release-notes/studio-2) (2026-08-13)
- [Introducing Suno Studio 2.0 — Suno Blog](https://suno.com/blog/studio-2) (2026-08-13)
- [Studio 2.0 export and tier availability — Suno Help](https://help.suno.com/en/articles/13670529)
- [Studio Chat — Suno Help](https://help.suno.com/en/articles/13670721)
- [Studio browser requirements (Web MIDI) — Suno Help](https://help.suno.com/en/articles/13670593)
- [Studio help category — Studio 2.0 vs Studio Archive](https://help.suno.com/en/categories/1708865)
- [Download limits FAQ — Suno Help](https://help.suno.com/en/articles/13614785)
- [Updates to our Terms of Service — Suno Blog](https://suno.com/blog/suno-updates-tos) (2026-08-10)
- [Terms of Service effective Sept 3 2026](https://suno.com/terms-september-2026)
- [Stem separation modes and credits — Suno Help](https://help.suno.com/en/articles/12702337)
- [Suno Studio 2.0 coverage — MusicTech](https://musictech.com/news/gear/suno-studio-2-0-upgrade-new-features/) (COMMUNITY)
- [Suno Studio review (1.x beta, 6/10) — MusicTech](https://musictech.com/reviews/digital-audio-workstations/suno-studio-review/) (ANECDOTAL, pre-2.0)

### Studio 1.x era (archived — several now live in Suno's "Studio Archive")

- [Introduction to Studio — Suno Help](https://help.suno.com/en/articles/7940161)
- [Introducing Suno Studio 1.2 — Suno Help](https://help.suno.com/en/articles/10625089)
- [How to Use: Song Editor — Suno Help](https://help.suno.com/en/articles/6141505)
- [Editing in Studio — Suno Help](https://help.suno.com/en/articles/8041473)
- [Can I replace a section of a song? — Suno Help](https://help.suno.com/en/articles/3271873)
- [How to use: Stem Extraction — Suno Help](https://help.suno.com/en/articles/6141441)
- [Remaster — Suno Help](https://help.suno.com/en/articles/8105281)
- [Exporting from Studio — Suno Help](https://help.suno.com/en/articles/8128193)
- [How To Use EQ in Studio — Suno Help](https://help.suno.com/en/articles/8935873)
- [Introducing Studio v1.1 — Suno Help](https://help.suno.com/en/articles/8967489)
- [Add Vocals — Suno Help](https://help.suno.com/en/articles/6882817)
- [Suno Sounds: Generate Custom Audio Samples — Suno Help](https://help.suno.com/en/articles/10625537)
- [Recording in Studio — Suno Help](https://help.suno.com/en/articles/8640385)
- [Loop Recording in Studio — Suno Help](https://help.suno.com/en/articles/8936897)
- [How to Use Stem Cover in Studio — Suno Help](https://help.suno.com/en/articles/9819905)
- [What's New in Suno Studio 1.2 — Suno Blog](https://suno.com/blog/studio1_2)
- [Introducing Suno Studio — Suno Blog](https://suno.com/blog/suno-studio)
- [A Whole New Level of Creative Control — Suno Blog](https://suno.com/blog/songeditor)
- [Suno Studio 1.2 Master Guide — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-studio-1-2-master-guide)
- [Suno Studio v5 Complete Guide — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-studio-v5-complete-guide)
- [HookGenius: Suno Studio Tutorial](https://hookgenius.app/learn/suno-studio-tutorial/)
- [Fix Timing with Warp + Quantize — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/fix-timing-warp-quantize-suno-studio-1-2)
- [Cut Credit Waste in Studio 1.2 — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-studio-1-2-reduce-credit-waste)
- [Suno AI Remaster Guide — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-remaster-guide-v4)
- [Suno Studio 1.2 — GenxNotes](https://blog.genxnotes.com/en/suno-studio-1-2-update/)
- [MIDI Export from Studio — GenxNotes](https://blog.genxnotes.com/en/suno-studio-audio-to-midi-function/)
- [How to Actually Use Replace Section — AIDIY](https://www.aidiy.tech/post/how-to-actually-use-suno-s-new-replace-section-feature-instructions-plus-bonus-the-arrow-song)
