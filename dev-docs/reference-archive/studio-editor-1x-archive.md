# Suno Studio 1.x Archive

Taken out of the installed skill bundle on 2026-11-12. These sections were in
`src/skills/suno-agent-band-manager/references/STUDIO-EDITOR-REFERENCE.md` and are kept here word for word, in
their original order. They document Studio 1.1 and 1.2 features whose names no longer appear in Suno's
current Studio 2.0 copy. Nothing in the module loads this file; it is a record for maintainers.

The installed reference keeps a short "Take Lanes and comping" subsection under Studio 2.0, because that
capability is still current; its text overlaps the "Alternates / Take Lanes" section below.

---

## Studio 1.x Archive (pre-2026-08-13 — verify before relying on)

> **Everything from here to the end of the Studio section is archived.** These features were documented for Studio 1.1/1.2. After the 2026-08-13 overhaul, **Remove FX, Alternates, Quick Replace, 12-track stem export, EQ, Warp Markers, Context Window, Sounds Mode, Stem Cover, Heal Edits, and MILO-1080 do not appear in current official Studio 2.0 copy**, and Suno moved their articles into a "Studio Archive" help category. **Take Lanes and comping are the exception — they SURVIVED into the current Studio docs and are not archived**; so did multitrack editing, AI stem generation, and the Full Song / Selected Time Range / Multitracks export set. Note the split inside the old "Alternates / Take Lanes" pairing: *Alternates* (and *Quick Replace*) are archived names, *Take Lanes* and comping are current. Treat the rest as unverified: it may have been removed, renamed, or folded into the new effects and chat surfaces. Do not recommend an archived feature by name without checking the live UI first.

### Access (1.x)

Select the **Studio** icon under **Create** in the left sidebar at suno.com. Desktop only.

### What It Is

A browser-based multitrack workspace that merges traditional DAW functionality with AI-powered generation. Built on technology from WavTool (acquired by Suno in June 2025). Think of it as a DAW where your instruments are AI generators, recordings, uploads, and stems.

### Interface Overview

- **Timeline**: Main multitrack workspace. Spacebar = play/pause.
- **Context Bar** (bottom): Dynamic toolbar — Create Panel (generate new), Library Panel (import existing), Upload Audio (import files).
- **Details Panel** (right side): Opens when selecting items. Remix/Edit options, individual stem insertion controls, Clip Settings.
- **Transport Bar** (bottom): Playback controls, record functionality, upload options.

### Clip Settings

When selecting a clip in Studio, the Details Panel offers:
- **Color**: Visual organization
- **On Beat** toggle: Locks clip to grid tempo vs. original timing
- **Transposition**: Semitone adjustments (pitch shift)
- **Speed**: Playback speed adjustment
- **Volume**: Per-clip volume control

### Context Window (v1.1)

A visually marked region above tracks that determines what audio Suno considers when generating new clips. Content outside this region is ignored.

**How to use:** Drag edges to expand or shrink the context region. On Mac, hold modifier key to disable snap-to-grid for precise adjustments.

**Why it matters:** This is critical for targeted generation — you can generate a drum variation that only listens to a specific bar, or protect earlier sections from influencing later generations. Without understanding the Context Window, users may get unexpected results from Studio generation.

### Automatic Saving

Studio auto-saves projects with timestamped **Versions** accessible through the Project Menu. No manual saves needed.

---

## Studio Features (1.x Archive — names not in current Studio 2.0 copy)

### Warp Markers (Studio v1.2, Premier)

Enables timing adjustments on audio clips with minimal distortion via time-stretching. Corrects drift, tightens choruses, aligns phrasing — all without regeneration and without altering pitch.

**How to use:**
1. Enable **Edit Mode** on a clip
2. Click the waveform to add markers at points you want to adjust
3. Drag markers to shift audio timing at that specific point

**Modes:**
- **Manual**: Click directly on the waveform at the adjustment point
- **Auto**: Automatically sets markers on each transient (beat/hit)

**Quantize**: After placing warp markers, use the **Quantize** function to lock timing to the grid so everything aligns to the tempo.

**Best use cases:**
- Tightening a chorus by locking drums and bass to the grid
- Fixing gradual tempo drift or slip
- Correcting rushed vocals with subtle nudges
- Groove shaping (use cautiously — artifacts expose here)

**Limitations:**
- Time-stretching creates artifacts, especially with extreme corrections or sharp transients
- Start conservative and audition before exporting
- If corrections are extreme, regeneration is better than warping

**Genre-specific quantize guidance:**

| Genre | Tightness | Approach |
|-------|-----------|----------|
| EDM | Very tight | Medium-to-strong quantize OK |
| Trap | Medium | Maintain bounce; avoid full lock |
| Afrobeat | Light-medium | Small warp edits; preserve groove |
| Soul/R&B | Light | Prioritize feel; minimal changes |

Source: [Fix Timing with Warp + Quantize — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/fix-timing-warp-quantize-suno-studio-1-2)

**Decision rule:** Edit timing if the musical idea works but the execution fails. Regenerate if the concept itself is wrong.

**Troubleshooting:** "After quantize, sounds weird" → Undo, re-quantize lighter, target only the worst region, use manual markers for specific hits, or regenerate and audition alternates.

### Alternates (archived name) / Take Lanes and comping (still current) — Premier

> **Split status.** This section was written for Studio 1.2, but only half of it is archived. **Take Lanes and comping remain in the current Studio docs** — the capability and those names are safe to use. **"Alternates" and "Quick Replace" are the archived names** and do not appear in current official Studio 2.0 copy. The mechanics below still describe how per-take auditioning works; treat the *Alternates* label, not the workflow, as the stale part.

An improved system for creating, previewing, and selecting between multiple generated variations of a section on a single track.

**How to use:**
1. Generate new content — two versions appear as **Take Lanes**
2. The main track shows Version 1
3. Use speaker icons to audition alternatives
4. Preview alternates in the Edits Library on the right
5. Click "Generate More" for additional options

**Comping:** Select preferred portions from each take version. Copy chosen edits to the Main Track. This allows combining the best parts of different takes.

**Best practices:**
- Generate 2-6 alternates with **one controlled change each** (e.g., "bigger melody / simpler drums" or "same hook / stronger rhythm")
- Audition in context (not solo) for the best selection
- Select the best overall take, then comp micro-details if needed
- Single-change alternates prevent losing song identity during comping
- "Too many versions, stuck?" → Choose the version that best supports the song's message, not the coolest individual detail. Commit and move forward.

### Remove FX (Studio v1.2, Premier)

Strips reverb and delay effects from audio clips, generating a dry version placed on the timeline.

**How to use:** Right-click any clip in Studio → select **"Remove FX"**

**Best use cases:**
- Wet vocal rescue when reverb drowns clarity
- Stem cleanup before mastering in an external DAW
- Rebuilding space with your own reverb/delay settings for emotional control
- "Dry first, then add space" workflow

**Limitations:**
- Results vary — heavily "printed" character from generation may partially persist
- Sometimes sounds thinner (spatial effects add perceived body)
- Works best on clips where effects were added during generation rather than being baked into the performance character
- **Can increase loudness by up to 5 LUFS** — check clip levels after applying to avoid clipping
- **Recommended workflow**: 'Prompt moderately dry, Remove FX only where needed, export multitrack, rebuild FX chain intentionally' (Jack Righteous)

**Troubleshooting:** "Remove FX sounds thinner" → Expected sometimes. Export and rebuild with EQ, compression, and custom reverb in your DAW. Or blend the original (wet) with the cleaned (dry) clip.

### EQ (Studio v1.1, Premier)

6-band per-track parametric equalizer for tonal shaping without leaving Studio.

**How to access:** Select a track → click **"Track"** in the Details Panel → EQ controls.

**Specifications:**
- 6 selectable bands (numbered 1-6), individually enable/disable
- Toggle switch (top-left) enables/disables EQ processing
- Frequency response graph with draggable control points
- Live spectrum analyzer
- 11 presets: Flat/Reset, High-pass, Vocal, Warm, Presence, Bass Boost, Air, Clarity, Fullness, Lo-fi, Modern

**Filter types:** Bell/Peak, High-pass, Low-pass, High-shelf, Low-shelf, Notch

**Parameters per band:**
- **Freq**: Center frequency
- **Gain**: -12dB to +12dB
- **Res (Q Factor)**: Narrow (surgical) to wide (musical)

**Tips:**
- Start with subtle adjustments (+/-3dB)
- Prefer cuts over boosts for natural results
- Common moves: cut 200-400Hz for mud, boost 2-5kHz for presence, cut 3-4kHz for harshness, boost >10kHz for air
- **AI shimmer artifacts**: Roll off ultra-highs on stems where noticeable — Suno's generation can produce high-frequency shimmer that EQ can tame
- Use the Vocal preset as a starting point for vocal clarity, then fine-tune

### Time Signature (Studio v1.2, Premier)

Allows composing beyond standard 4/4 time. Supports signatures like 6/8, 7/8, 11/4, and other meters.

**How to access:** Time signature picker in the bottom info panel of Studio. Set numerator (1-99 beats per bar) and denominator (beat duration).

**Limitation — now UNVERIFIED for Studio 2.0, previously confirmed for 1.2.** The Studio 1.2 article still carries the line verbatim: the setting is "not yet sent to generative models," affecting grid, metronome display, and editing alignment but not AI generation. **That article now sits in Suno's "Studio Archive" and describes Studio 1.2; none of the 11 Studio 2.0 articles restate or retract it** ([help.suno.com/en/articles/10625089](https://help.suno.com/en/articles/10625089), [category index](https://help.suno.com/en/categories/1708865), checked 2026-08-13). Treat the claim as unverified for 2.0 rather than confirmed — and keep prompting for the desired meter via style prompt or lyric metatags, which is the behavior that holds either way.

**Best practices:**
- Set meter early so edits and quantize decisions stay coherent
- Useful for: 6/8 worship feels, odd-meter tension (7/8, 11/4), syncopated hooks where grid precision matters

### Heal Edits (Premier)

Smooths transitions at edit/cut points where audio clips meet.

**How to use:** Right-click a region → **"Heal Edits"**

**When to use:** After cropping, rearranging, or replacing sections where the transition sounds rough or has artifacts at the cut point.

**Technique:** After committing a Replace Section, apply Heal Edits on the **following** section (not just the edit point) to blend tonal shifts and timbre changes between edited and original audio. If the voice timbre shifts, run Heal Edits and trim its range to target just the boundary area.

**Limitations:** Subtle effect — some users report not noticing a difference. Works best on regions where two different takes/generations meet. Can be targeted to specific parts of regions rather than whole sections.

### Recording (Premier)

Record audio directly into Studio via microphone.

**How to use:**
1. Add a track → select Input → choose microphone
2. Grant browser permissions
3. Use headphones (prevents feedback)
4. Enable metronome if desired
5. Arm track (red Record button) → press Record on Transport
6. Recorded audio uploads to Timeline after recording completes

**Transforms:** Drag recorded audio into the Create panel to generate new material. Example: a sung melody becomes a string orchestra, finger taps become drums. Adjust Audio Influence in Advanced Options to control how closely the generation follows the recording.

### Loop Recording (Studio v1.1, Premier)

Continuous recording of multiple takes over the same time range.

**How to use:**
1. Enable loop icon in transport controls
2. Set loop start and end points
3. Press Record — each pass creates a separate take/layer
4. Access all takes via "Show Take Lanes" icon

**Use cases:** Vocal takes, instrument solos, bass lines, layering multiple performances.

### Sounds Mode (Premier, Beta)

Generate custom sound effects, samples, and loops from text prompts.

**How to access:** Create → Custom mode → select **"Sounds"** from dropdown.

**Settings:**
- **Type**: One Shot vs. Loop
- **BPM**: Lock to tempo
- **Key**: Lock to key

Generates two options per prompt. Categories include: sound effects, ambient backgrounds, foley, animal sounds, musical samples (808 kicks, snares, loops).

### Stem Cover (Premier)

Takes any clip in Studio and covers it into a different sound/instrument while retaining melody and rhythm.

**How to use:** Select a clip in Studio → apply Cover function with desired instrument/sound prompt. Receive two generations per prompt in Take Lanes.

**Example:** Covering finger taps into a 70s soul drum fill. Covering a guitar stem into a synth pad.

**Cover vs. Recreate:** Cover references the original source audio used to generate a clip (even if you cover a guitar stem that came from a ukulele, it references the original ukulele). Recreate uses the currently selected audio as the source — enabling iteration on already-covered stems.

### Studio Export Options

| Export Type | What It Does |
|-------------|-------------|
| **Full Song** | Complete mix of all tracks and processing |
| **Selected Time Range** | Only the chosen timeline section |
| **Multitrack** | All tracks as separate stems within the Studio mix context |
| **Individual Clip** | Right-click any clip → "Download .WAV" |
| **Wave Tempo Locked** | Stems set to average BPM for DAW alignment |
| **WAV + MIDI bundle** | Audio + MIDI data together |

All exports are high-quality WAV files.

### MILO-1080 Step Sequencer (March 2026, Premier)

A 16-track step sequencer and synth designer:
- Text-to-sound generation for creating samples
- Pull clips from Suno track library
- Built-in synth engine for manual sound design
- MIDI input/output for hardware integration
- Targets experienced producers and beatmakers

---

## MIDI Export (Premier Only) — 1.x Archive

> **Archived.** This describes the Studio 1.x "Get MIDI" flow at 10 credits per stem. Studio 2.0 has a much larger MIDI surface (import, record, edit, piano roll, audio-to-MIDI transcription, MIDI-as-prompt, MIDI controllers) and **no credit cost is published** for it. Treat the 10-credits-per-stem figure as unverified and check the live UI before quoting a price.

### What It Does

Extracts MIDI data from audio stems, generating standard MIDI files representing melodic or rhythmic content.

### How to Access

1. Extract stems from your clip using the Stems panel
2. Click on the stem you want
3. Select **"Get MIDI"** from the context menu

### Cost

**10 credits per stem** for MIDI extraction.

### Export Formats

Standard MIDI files compatible with any DAW. Available as standalone MIDI or WAV + MIDI bundles.

### Use Cases

- Recreating melodies with different instruments in your DAW
- Analyzing harmonic progressions
- Building new arrangements from Suno generations
- Hardware integration via MIDI

---

---

## Troubleshooting rows for archived features

These three rows sat in the reference's Troubleshooting table (`| Issue | Cause | Fix |`).

| Issue | Cause | Fix |
|-------|-------|-----|
| Warp markers sound weird after quantize | Over-correction | Undo, re-quantize lighter, target worst region only, use manual markers |
| Remove FX sounds thin | Spatial effects add perceived body | Export and rebuild with your own reverb/EQ in a DAW; blend wet + dry |
| Studio generation ignores earlier sections | Context Window too narrow | Expand the Context Window to include the sections you want Suno to reference |
