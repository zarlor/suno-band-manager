# Technical Resolution

> **Before recommending a download-consuming fix:** from 2026-09-03 downloads are capped (Free 7 lifetime, Pro 20/month, Premier 60/month; Studio exports exempt). Iterating is still free — *keeping* the result is what costs. When a refinement path ends in "export and fix it in a DAW," say that it spends one of the user's downloads.

> **Last validated:** August 13, 2026 (Studio 2.0 and the Song Editor); download cap 2026-09-03; v6 repair ladder and late-song reports from the 2026-10-03 research sweep.

Resolution paths for technical and quality feedback: artifacts, editor and Studio tools, song length, and genre drift. Most of these are generation-specific, so regeneration or a post-generation edit usually beats a prompt change.

## Generate → Inspect → Refine Workflow (v5.5 onward, including v6)

Since v5.5, Suno has favored an iterative **generate -> inspect -> section replace -> refine** workflow over full regeneration. This preserves good material and spends fewer credits.

### Recommended Workflow

1. **Generate** the initial output from the song package
2. **Inspect** the full result — evaluate structure, melody, emotional angle, and production
3. **Section replace** any sections that need work (preserve sections that are good)
4. **Refine** with targeted adjustments (delivery metatags, slider tweaks, specific prompt edits)

### Critical Checkpoint Questions

Before spending credits on regeneration or further iteration, ask:

- **Is the structure correct?** If yes, do NOT regenerate from scratch — use section replacement.
- **Is the melody usable?** A good melody with flawed production is worth refining. A bad melody needs regeneration.
- **Does the emotional angle justify more credits?** If the song is fundamentally heading in the right direction, refine. If the emotional core is wrong, regenerate.

### When to Use Section Replacement vs. Full Regeneration

| Situation | Recommendation |
|-----------|---------------|
| Structure and melody are good, one section has bad vocals | Section replacement |
| Structure is good, multiple sections need different fixes | Sequential section replacements |
| Melody is wrong throughout | Full regeneration |
| Overall vibe/genre is off | Full regeneration with revised style prompt |
| Good material but wrong emotional direction | Full regeneration — emotional direction is global |

## Audio Quality & Artifacts

Common quality issues that cannot be resolved through style prompt changes alone.

| Feedback | Resolution Path |
|----------|----------------|
| "Sounds robotic/glitchy" | Regenerate (try 3-5 times with same prompt); if persistent, simplify style prompt or switch models |
| "Audio quality drops at the end" | On v6, see "Late-song degradation" below for how others describe it now and the repairs they report. *(Pre-v6, 2026-08 sweep, mild: vocals reported losing timbre in the 2-4 minute range; the advice was sub-2:00 segments stitched together, or Replace Section on the late material.)* |
| "Weird artifacts/noise" | Regenerate; if persistent, remove problematic descriptors from style prompt |
| "Pronunciation is wrong" | Add phonetic hints in lyrics, or use `[Spoken Word]` metatag for problem lines |
| "Vocals sound auto-tuned" | Add "natural vocal, organic phrasing, imperfect delivery" to style prompt; add "auto-tune" to exclusions. On v6 with a stock male voice, see the "generic / autotuned" row in `references/model-controls.md` |
| "Clipping/distortion (unwanted)" | Add "clean mix, headroom, dynamic range" to style prompt; reduce layering descriptors |
| "Frequency mud / sounds muffled" | Suno's own EQ post (OFFICIAL, 2026-09-29, Studio) frames a muddy vocal as the band competing in the same frequency range, and fixes it at the mix stage (a low-mid cut, starting around −6 dB at 400 Hz). That's a mix fix, not a prompt lever, and Studio is Premier-only. On the prompt side, give the band room (see the vocal-space options in the suno-style-prompt-builder skill's "v6 prompt guidelines"). Older advice: add "crisp, clear mix, defined frequencies" to style prompt; Premier users can also work the mix in Studio (the 1.x "Remove FX" tool is archived — check the live UI), or export stems and EQ in a DAW |
| "Timing drifts / feels off the grid" | Premier: fix it in Studio before regenerating (Warp Markers was the Studio 1.x tool and is not in current Studio 2.0 copy — check the live UI). Pro: Replace Section on the offending span, or export stems and correct timing in a DAW |
| "An instrument bleeds into sections where it shouldn't be" | A fundamental Suno limitation: style-prompt instruments apply to the whole song. Generate with all instruments, then extract stems (Auto Split or, at Premier, Advanced Split) and remove the instrument per section in a DAW. One-way — finish all Suno editing first. From 2026-09-03 the whole stem set counts as that song's single download |

**External DAW editing (Audacity, etc.) is a one-way operation** — once you edit outside Suno, you lose Suno's editing capabilities on that version. Always keep the original Suno generation as a source of truth.

### Late-song degradation (v6) — others' reports, 2026-10-03 sweep

The most common v6 complaint on Reddit. These are other users' descriptions and repairs, not this module's measurements. Production testing hasn't found late high-frequency loss so far, but it hasn't measured stereo width or level in 30-second steps either.

- **How it's described** (COMMUNITY, 15+ threads): *"like switching from stereo to mono"* (4 users); steps *"every 30 seconds"* (several; the "chunked decoding" explanation is unverified); two choruses that sound mastered differently; drums going *"tinny"* or *"electric"* in the last third; the level rising across the song (*"20% from start to finish"*, 1 user). It's worst in dense, distorted mixes. Several users never hear it.
- **Max Mode mostly doesn't fix it** (many users; 2 say it helps). Keep it on for adherence.
- **Repairs reported** (ANECDOTAL unless marked; untested here): Extend from the last clean point (COMMUNITY, 3+; one counter-report says the decline is gradual, so extending won't help); split the song, Cover the back half at Audio Influence 85–100 and stitch (the split needs Studio, so Premier); a 100→80% gain fade across the track; Cover or extend with v6-mini; even out a kept take's level, then Cover it at AI 60–80+. One prompt-side claim, `ritardando` against the loud end-of-song push, also slows the ending (untested). Keeping heavy songs under about 3 minutes is still the common advice.

When a user names one of these symptoms, say these are others' reports and offer the repairs as things to try.

**Key principle:** Audio quality issues are often generation-specific, not prompt-specific. Always try regenerating 3-5 times before modifying the prompt. Suno's randomness means the same prompt can produce both clean and artifact-heavy outputs.

## Editor and Studio Resolution Paths

When feedback maps to post-generation tools rather than prompt changes. **Check the user's tier first** — the split below is the one that matters, and it did not change with Studio 2.0. On the Free tier, regeneration is the primary path.

### Available at Pro and Premier (Song Editor / Legacy Editor)

| Feedback Pattern | Feature | How |
|-----------------|---------|-----|
| "Verse 2 vocals are bad but the rest is great" | Replace Section | Regenerate only the problem section, preserving everything else. Availability at Pro re-confirmed official 2026-08-13, no deprecation announced |
| "The song is great but I want to try different words" | Replace Section + Lyrics edit | Change lyrics for specific sections while preserving melody |
| "The vocal melody is great but the lyrics are wrong" | Add Vocals | Generate new vocals over the existing instrumental |
| "I need the instrumental without vocals" | Stems | **Auto Split** (up to 12 stems, 50 credits) or **Split from Mix** (20 credits total) |
| "The mix feels rough but the song is right" | Remaster | Subtle/Normal/High. Does NOT change style, vocalist, or arrangement — use Cover for those |
| Ending problems | Crop / Fade Out / Extend | See the ending-repair decision tree under "Song Length & Pacing" |

**Using Replace Section:** select the problem region and hit Replace to get alternatives while keeping the rest. **Keep Duration** on matches the original length; off gives room for solos and breaks. **Instrumental Mode** removes vocals; **Replace Lyrics** edits the selected region only. It works best on 10-30 second selections and typically takes 2-5 attempts for a clean transition.

**Local caveat that outranks the availability line:** our own production test (2026-04-29) found Replace Section produces **audible transition seams** even at the documented sweet-spot scale — it fixed the targeted word and left an obvious join. Availability is not viability. When recommending it, say that transition quality has to be evaluated alongside content correctness, and that Cover or a full re-gen produce seamless audio where Replace Section cannot.

### Premier only (Suno Studio 2.0)

Studio 2.0 shipped 2026-08-13 and **nothing in it reaches Pro**. Current capabilities: MIDI import/record/edit and audio-to-MIDI, MIDI-as-prompt, a session-aware chat bar that generates instruments, vocals, and custom effect plugins, a wavetable synth, built-in effects (compressor, convolution reverb, delay, distortion, EQ, gate, reverb), automation curves, and 32-bit/48kHz multitrack export that is **exempt from the download cap**. Premier also gets **Advanced Split** stems (~100 instruments).

**Archived — do not recommend by name without checking the live UI.** Warp Markers, Remove FX, Alternates, Quick Replace, the 6-band EQ page, Context Window, Sounds Mode, Stem Cover, Heal Edits, and MILO-1080 were Studio 1.x features and **do not appear in current official Studio 2.0 copy**; Suno moved their help articles into a "Studio Archive."

**Take Lanes and comping are the exception — still current.** They remain in the underlying Studio docs, so "I want to hear different versions of this section and keep the best bits" can still be routed to Take Lanes and comping at Premier. It is the *Alternates* name that is archived, not the capability. For everything else on the archived list (timing correction, FX stripping), route to the *outcome* — "fix this in Studio, or export stems and fix it in your DAW" — rather than naming a tool that may not be there.

**Time Signature:** documented for Studio 1.2 as grid/metronome alignment only, "not yet sent to generative models." That claim is now **unverified for Studio 2.0** — no 2.0 article restates or retracts it. Either way, prompt for the desired meter rather than relying on the picker.

**For complete Studio & Editor workflows, tips, and troubleshooting:** see `references/STUDIO-EDITOR-REFERENCE.md` in the suno-agent-band-manager skill (the module's canonical Studio/Editor reference).

## Song Length & Pacing

### Duration Slider — a pre-generation parameter (v5.5 web; carried onto v6, Auto or 0:10–6:00)

Shipped 2026-07-20 (OFFICIAL, [release note](https://suno.com/release-notes/duration-slider-on-web)). It is **pre-generation only** — it cannot fix a song that already exists, so it belongs in the "next generation" half of a refinement plan, never in the "repair this take" half. Suno published no range. The endpoints — **10 seconds to 6:00** — are verified in live UI (Pro account, 2026-08-14); the **5-second increment granularity is COMMUNITY-attested** and not part of that observation. Auto or Custom, web only, mobile unconfirmed. It also **requires Style set to Custom**, and it is **unavailable or unreliable for covers, remixes, extends, and custom models** — do not offer duration targeting as a fix on a derivative operation.

**Adherence is inconsistent and the reports are starkly split** (COMMUNITY): a controlled batch matched the target in 4 of 40 generations, while other users report near-perfect adherence. Nobody has explained the variance, so treat a missed target as expected behavior rather than as a user error worth debugging.

| Feedback | Duration-slider response |
|----------|--------------------------|
| "It ends too abruptly / just stops" | **A hard cutoff at the target is the slider's signature failure.** If a Custom duration was set, that is the first suspect. Re-run with Auto to find the natural length, then set Custom at natural **+10-15s**, and add an explicit `[Outro]` |
| "Suno rushed through the lyrics / skipped a section" | Short target against heavy lyrics. Raise the target or cut lyric content — the slider will not politely compress |
| "It ends, then starts over" | **Premature-end-then-restart** is the reported long-target failure — the song finishes around 3:05 and restarts to fill a 5:30 target. Lower the target toward the Auto length |
| "There's dead air / silence at the end" | Same root cause as above (an earlier account described silence padding; primary sources describe end-then-restart). Lower the target |
| "I need it to be exactly N seconds" | Set it, but expect a target rather than a contract, and plan to Crop |

**Reported golden length: 2:00-3:30** (COMMUNITY). Recommended default workflow: **Auto first, then Custom at natural +10-15s.** The slider raises the value of explicit `[Outro]` tagging rather than replacing it — "a production decision, not a repair button" (ANECDOTAL).

### Post-Generation Ending Repair — Decision Tree

Don't regenerate a whole song over a bad ending. Match the symptom (ANECDOTAL, but it matches how we already triage):

| Symptom | Fix |
|---------|-----|
| Trailing instrumental / noodling after the last vocal | **Crop** |
| Abrupt final second, otherwise fine | **Fade Out** in the editor |
| Section repeats or stumbles mid-song | **Replace Section** |
| Song has no ending at all — it just stops mid-idea | **Extend**, then Crop |

Ending *tags* for the next generation are a separate lever: community consensus is `[Outro]` + `[End]` paired, `[End]` on the absolute last line with nothing beneath it, `[Fade Out]` never alone. See the suno-lyric-transformer skill's `references/metatag-reference.md` → "Ending Control."

### Repair Ladder for a Near-Keeper — Things to Try Before a Full Re-Roll (v6, 2026-10-03)

Use this when a take is nearly right but its ending, final chorus or vocal level lets it down. It applies **only before the take is handed over** (the delivered take is the master). Each step is ANECDOTAL or VENDOR, n=1, and unmeasured in this module's testing, so offer them as things to try, in roughly this order of cost:

1. **Extend from just before the last section** to re-roll only the ending, or a stripped final chorus. Use "get full song" afterwards.
2. **Sample the good part, then regenerate with a Custom Duration shorter than the Auto take** (it cleared end clicks for one user).
3. **Fade Out**, or **Crop then Fade Out**, for a tail that runs on.
4. **Remaster at Variation Subtle with Style Clarity** for a buried vocal (VENDOR-relayed, partly contradicted by another creator).

If none of these works, a full re-roll is the next step. Custom Duration stays a last resort: too much of it filled a regenerated last minute with repeated endings in one controlled test.

### Length and Pacing Adjustments

| Feedback | Adjustment |
|----------|-----------|
| "Song is too short" | Use Suno's extend feature; or add sections in lyrics (additional verse, bridge, instrumental break). On v5.5 web, a higher Duration target is the pre-generation lever |
| "Song is too long" | Remove repeated sections in lyrics; trim `[Outro]` content; remove `[Breakdown]` if not essential; or set a Custom duration on the next generation |
| "Intro goes on too long" | Shorten or remove `[Intro]` lyrics content; add `[Verse 1]` tag earlier; note: `[Intro]` tag is notoriously unreliable |
| "Outro cuts off abruptly" | Add explicit `[Outro]` section with 2-4 lines; add `[Fade Out]` descriptor metatag |
| "Middle section drags" | Add `[Energy: building]` metatags; shorten the dragging section; consider adding a `[Breakdown]` or `[Build-Up]` for variety |
| "Energy drops in extended sections" | Known limitation — 62% of extended tracks drift from original prompt. **Weirdness is strongest during Extend and Bridge generation** — this is the primary drift cause. Keep Weirdness conservative during Extend. Use callback phrasing ("continue same chorus energy") and re-inject genre/mood every 1-2 extends. |

## Genre Drift & Consistency

Genre drift is one of the most common issues — 62% of extended Suno tracks deviate from the original prompt. **The Weirdness slider has the strongest destabilizing effect during Extend and Bridge generation** — high Weirdness during Extend is more disruptive than during initial generation.

| Feedback | Adjustment |
|----------|-----------|
| "Style changed mid-song" | Add consistent genre anchoring via `[Mood: ...]` and `[Energy: ...]` metatags before each section in lyrics |
| "Extended section sounds different" | Regenerate the extension; use Replace Section (Pro and Premier); keep Weirdness conservative during Extend; use callback phrasing ("continue same chorus energy") and re-inject genre/mood every 1-2 extends |
| "Genre fusion went wrong" | Simplify to single dominant genre; move secondary genre influence to later in style prompt (after critical zone) |
| "Sounds like a different band in the second half" | Add `[Vocal Style: ...]` tags before each section; increase Style Influence slider (65-80) for tighter adherence |
| "Voice/Persona shifted during Replace Section" | Keep Weirdness conservative during Replace operations — high Weirdness can cause Persona/Voice identity shifts |

**Prevention tips:** Front-load genre identity in the first 200 chars of style prompt. Use per-section metatags. Generate 3-5 versions and cherry-pick. For extensions, match the style prompt exactly, keep extensions short (30s-1min increments), and **keep Weirdness lower during Extend than during initial generation**. Use callback phrasing ("continue same chorus energy", "maintain verse mood") to anchor the extension to the existing material.

### Extend Anti-Drift Toolkit

Techniques for maintaining consistency during Extend operations, ordered by effectiveness:

1. **Anchor note restating** — restate genre, mood, key, and instrument palette with each extension in 1-2 sentences. Example: 'Keep the exact current groove, instrument palette, key, and tempo.'
2. **Forbidden element phrasing** — 'No new hooks,' 'No new drums,' 'No new riffs,' 'no risers.' Negative constraints are more effective than positive instruction alone during Extend.
3. **Structural metatag at start** — include `[Chorus]`, `[Bridge]`, `[Outro]` etc. at the beginning of every extension prompt to guide section type.
4. **Energy alignment** — specify energy relative to existing material: 'Bridge energy: 80% of chorus; lower drums...'
5. **Short blocks (30 seconds preferred)** — catch drift before it compounds. Limit to 2-3 extensions maximum per song.
6. **Cover as signal cleaner** — if quality degrades after multiple extensions, use Cover to re-synthesize the audio from scratch, resetting the signal path.
7. **Custom Extend over Quick Extend** — always use Custom Extend for anything you care about. Quick Extend is for rapid prototyping only.

**Verification:** Loop playback at 2x speed to confirm join seams and style consistency.

**Genre-specific outro templates:**
- Gospel/Worship: soft organ and distant choir pad
- Rock/Anthem: final guitar sustain and cymbal swell
- Lo-fi: soft piano motif and vinyl texture
- EDM: filtered synth tail
- Reggae: softening skank guitar

Sources: [Suno 4.5 Plus Extend — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-45-plus-extend-tool) | [Outro Prompts — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-outro-prompt-guide) | [End Prompts — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-end-prompt-guide) | [Fade Out Prompts — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-fade-out-prompt-guide)
