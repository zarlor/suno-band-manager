# Model-Specific Prompt Strategies

> **Related references:** Style prompts work in conjunction with lyric metatags — for the full metatag catalog (section tags, vocal delivery, effects, production tags), see `suno-lyric-transformer/references/metatag-reference.md`. For mapping user feedback to style prompt adjustments, see `suno-feedback-elicitor/references/suno-parameter-map.md`.
>
> **Last validated:** August 13, 2026 (Suno v5.5 Pro, v5 Pro, v4.5-all, v4.5 Pro, v4.5+ Pro, v4 Pro; Duration slider; Sept 3 2026 policy changes). Suno updates models and prompt behavior frequently — use web search to verify strategies against current documentation when uncertain.
>
> **Model-retirement caveat (OFFICIAL, 2026-08).** Suno has announced that "new models launching soon will retire older versions" — retirement means you can no longer *generate* with a model; existing songs stay playable. **No official source names which versions retire or when**, and the next model is the unnamed industry-developed model from the BMG partnership. Two consequences for everything below: (1) model-specific strategy in this file has an expiry date that is not yet published, and (2) **Extends, Covers, and remixes of existing songs will run on the NEW models** — "results may sound different from the original generation." A song whose plan depends on Extending an older track carries that risk. Sources: [ToS update](https://suno.com/blog/suno-updates-tos), [FAQ](https://help.suno.com/en/articles/13614785), [BMG partnership](https://suno.com/blog/suno-partnership-bmg).

## Quick Reference

| Model | Style | Sweet Spot | Strengths |
|-------|-------|-----------|-----------|
| v4.5-all (free) | Conversational sentences | Flowing descriptions, natural language | Heavier/faster genres, longer-form (~8 min) |
| v4.5 Pro | Conversational + nuanced | Like v4.5-all with more detail responsiveness | Intelligent prompt enhancement |
| v4.5+ Pro | Advanced conversational | More control over structure | Advanced creation methods |
| v5 Pro | Crisp film-brief | 5-8 descriptors, emotional > technical | Natural vocals, instrument separation, polish |
| v5.5 Pro | Crisp film-brief (same as v5) | 5-8 descriptors, can be more granular | Most expressive, Voices, Custom Models, My Taste |
| v4 Pro | Simple descriptors | Keep it straightforward | Improved sound quality over v3 |

## v4.5 Family (v4.5-all, v4.5 Pro, v4.5+ Pro)

### Prompt Style: Conversational

Write style prompts as flowing, descriptive sentences. The model responds well to narrative descriptions of the sound.

### Construction Pattern

```
[Genre and mood sentence]. [Instrumentation and texture sentence]. [Production and mix sentence]. [Energy and dynamics sentence].
```

### Example Prompts

**Indie folk-rock:**
> Create a melodic, emotional indie folk-rock song with organic textures and warm analog production. Acoustic guitar layered with subtle electronic elements, gentle percussion building through the song. Intimate male vocals with clear diction and restrained delivery, opening up on choruses.

**Upbeat pop:**
> Energetic, feel-good pop with a modern radio-ready sound. Bright synths, punchy drums, and a driving bass line. Female vocals with a confident, playful delivery. Big chorus with layered harmonies and a catchy hook.

**Dark electronic:**
> Deep, brooding electronic track with industrial textures and a slow-burning build. Heavy sub-bass, glitchy percussion, distorted synth drones. Minimal vocals — whispered, processed, barely human. Tension throughout, no release until the final drop.

### Tips

- Can be more verbose than v5 — the model handles longer descriptions well
- Conversational tone works: "Create a..." or "This should sound like..."
- Good for describing energy arcs: "begins with soft ambient layers, builds to..."
- Prompt Enhancement helper available in the UI — mention this to users

## v5 Pro

### Prompt Style: Crisp Film-Brief

Write style prompts as tight, evocative descriptors — like a creative brief for a film soundtrack. Emotional and textural language over technical specifications.

### Construction Pattern

```
[genre], [mood/emotion], [2-3 key sonic textures], [vocal character], [production quality notes]
```

Keep to **5-8 descriptors**. Each one should earn its place.

### Example Prompts

**Indie folk-rock:**
> indie folk-rock, melancholic warmth, acoustic guitar over ambient pads, breathy male vocal, intimate lo-fi mix with wide stereo field

**Upbeat pop:**
> modern pop, confident and bright, punchy drums, sparkling synths, female vocal with playful edge, radio-ready mix, big chorus harmonies

**Dark electronic:**
> dark electronic, industrial tension, sub-bass drones, glitchy percussion, whispered processed vocals, cinematic slow-burn

### Tips

- **Emotional descriptors beat technical ones:** "raw, yearning" > "120 BPM". Use rhythm nouns instead of BPM values: "halftime groove," "double-time driving," "shuffle feel." (v5 may respond better to BPM in style prompts than v4/v4.5 — see Universal Rules — but rhythm nouns remain more reliable.)
- **Production-quality descriptors are highly effective in v5:** "radio-ready mix", "punchy drums", "wide stereo field", "crisp high-end", "warm bass"
- **Include mix notes:** register, tone, phrasing, harmony
- **Vocals sound more natural** in v5 — breaths, phrasing, harmonies are authentic
- **Better instrument separation** — can request specific instrument prominence
- **Composition-aware architecture** — v5 uses early style/genre info to maintain coherent sections throughout the song
- **Better nuanced interpretation** of complex prompts vs. v4.5
- **Full negative prompting support** — v5 handles in-prompt negatives ("no [element]") more reliably than v4.5's limited support
- **Existing v4/v4.5 prompts often work "even better" on v5** — migration is typically seamless
- **Section-level editing** available in editor — structure control shifted from prompt to editor
- Don't waste characters on things the editor handles (song structure, section ordering)

**Tested v5 Pro descriptors (from live testing):**
- "down-tuned" and "crushing" — effective for pushing v5 from rock toward metal weight
- "raw melodic singing" — key phrasing for gritty-but-not-screaming vocals (overcorrects less than "clean singing with grit on peaks")
- "dual gritty male vocals" + "raw melodic singing" — achieved gritty-but-melodic without triggering screaming
- "heavy swamp metal" with Exclude Styles blocking screaming — got heavy without full scream on v5
- NOLA funk elements came through well across multiple sections on v5
- v5 had more dynamism and better section transitions than v4.5+ Pro for complex multi-tempo songs
- "NOLA funk groove" functions as BOTH a genre descriptor AND a rhythmic looseness instruction — NOLA funk and jazz are inherently rhythmically loose (swing, syncopation, playing around the beat). This makes it a better vehicle for odd time signatures and time changes than pure metal, which tends to be metronomically precise. Non-obvious but powerful finding.

**Confirmed Descriptor Effects (from community research):**

These descriptors produce consistent, predictable results across v5 generations:

| Descriptor | What Suno Produces |
|---|---|
| `atmospheric` | Reverb, space, ambient pads |
| `airy` | Reverb/space on vocals |
| `lo-fi warmth` | Vintage character, low-pass filtering |
| `polished radio-ready` | Clean, modern, commercial mix |
| `unpolished room sound`, `natural room ambience` | Less processed, room sound — **use these instead of `raw live recording`**; see the "live"-family warning below |
| `driving` | Forward momentum, energetic basslines |
| `lush` | Layered pads, dense production |
| `punchy` | Low-end presence, tight transients |
| `wide stereo` | Spatial separation |
| `gated drums` | 80s-style drum processing |
| `vintage Rhodes` | More specific/effective than "piano" |

**⚠ The "live" word family triggers crowd noise (LOCAL-CONFIRMED, recurring).** Module production testing has hit this repeatedly on v5.5: **any** form of the word — `live-band drums`, `live recording`, `live energy`, `live in the room` — pulls audience-noise rendering, crowd texture, and crowd-vocal bleed, even when the intent is plainly band-in-a-room performance energy rather than a concert. The word appears to carry "live album" as its dominant training association, and a single instance is enough. This table used to recommend `raw live recording` as a production descriptor; that recommendation was wrong and has been replaced.

**Say the quality, not the venue.** `unpolished room sound`, `natural room ambience`, `single-take band performance`, `minimal overdubs`, `dry close-mic drums with room bleed` all get the intended texture without the word. External sources do not list "live" among crowd-risk terms — this is our own finding, and it is one of the more reliable ones we have.

**Three-Pass Layered Prompting (v5 technique):**

For complex songs, build the prompt in three conceptual passes rather than trying to specify everything at once:

1. **Idea pass** — define concept, mood, genre (the style prompt core)
2. **Lyric pass** — write/refine lyrics with structural tags
3. **Performance pass** — add vocal delivery cues, energy tags, dynamics

This separates concerns and prevents overloading any single input field.

**Confirmed Suno behavior (from Gemini analysis of production outputs):**
- "NOLA funk swing" lands as syncopation, not true swing — Suno interprets swing as a syncopation instruction rather than a jazz swing feel
- "Odd time signatures" is consistently ignored in 4/4 rock/metal context — the strong 4/4 pull of rock and metal genres overrides time signature instructions
- Suno adds unscripted guitar solos regularly — expect them even when not requested, especially in rock/metal genres
- Structural/section directions embedded in long style prompts are largely ignored — Suno treats the style prompt as a tonal palette, not a roadmap. Use metatags and the editor for structural control, not the style prompt.

## v5.5 Pro

### Prompt Style: Same as v5 Pro — Crisp Film-Brief

v5.5 is an additive update over v5. It uses the same audio engine, metatags, and character limits. All v5 prompts work identically on v5.5, often with better results. No migration required.

### What Changed

- **Most expressive model yet** -- better at interpreting subtle, nuanced descriptors that v5 would flatten or ignore
- **More varied output** per generation -- generate 3-5 versions and pick the standout; the spread between "best" and "average" is wider
- **v5.5-optimized prompts can be more specific:** where v5 would use simpler terms like "808s, hi-hats," v5.5 responds well to granular detail: "deep sub 808s, glitchy hi-hat rolls, pitched vocal chops"
- 48kHz sample rate, up to 8 min generation, internal codename "chirp-fenix" (v5 was "chirp-crow")
- **Workflow paradigm shift:** v5.5 encourages generate -> inspect -> replace sections -> refine (not regenerate from scratch)

### What the field says about v5.5 quality (COMMUNITY, 2026-08)

Primary-source characterization of v5.5 is stable and close to unanimous, and it is less flattering than the release framing: **generic pop polish, muted bass, heavy compression, audible "AI hiss," plastic-sounding vocals, and character loss on covers** relative to v4.5 and v5. Genre-specific tells get named too (every v5.5 reggae groove opening with rim shots). Take it as the shape of the model's defaults rather than as a verdict — but two practical consequences:

- **It corroborates our own bass-forward limitation** (see "Bass Prominence" below). Muted bass is not our prompting failing to land; it is what the field reports as the model's default balance.
- **Counter-programming the defaults is the job.** Production descriptors that fight compression and polish (`dynamic range`, `open mix`, `unpolished room sound`, `breathing room`) earn their place more on v5.5 than they did on v5.

**Within-track degradation past ~2 minutes — the most replicated technical claim in the 2026-08 sweep (4 independent reports).** Vocals lose timbre and turn robotic somewhere past the 2-4 minute mark ("ends up sounding like Alvin the Chipmunk"), and the style prompt reportedly stops being followed after the first 1-2 minutes. The circulating workaround is to **build in sub-2:00 segments and stitch**. This does not overturn our long-form work, but it does mean: when a long generation goes wrong in its back half specifically, suspect the length rather than the prompt, and consider whether the song can be built in two passes. It also raises the value of Replace Section on late material over full regeneration.

**Early-August 2026 wobble cluster (individually ANECDOTAL; the clustering is the signal):** broken composition and off-beat output (08-07), songs cutting off oddly (08-12), and a claimed A/B showing the v5.5 remaster engine adding high-frequency harshness versus native v4.5 even at Subtle strength (08-14). If output quality seems to have changed underneath a known-good prompt, this is a real possibility rather than user error.

### v5.5 New Features

**Voices (a distinct feature alongside Personas — Personas were NOT removed):**
- Actual voice cloning from a 15s-4min audio sample with anti-deepfake verification
- Pro/Premier only
- **Skill Level dropdown** (Beginner/Intermediate/Advanced/Professional): NOT cosmetic — actively reshapes model interpretation. **Always select Professional** regardless of actual singing ability. Testing confirmed Professional produces the most stable, consistent results across every test.
- Drop gender descriptors ("male vocals", "female singer") when using Voices -- the Voice already defines these, freeing characters for production detail
- Audio Influence for Voices varies by goal (higher than the 25% default for Personas). Independent testing (JG BeatsLab, March 2026) found the practical ceiling is lower than Suno's UI suggests — at 85%, resemblance only reached ~70% with increasing artifacts:

  | Goal | Range | Notes |
  |------|-------|-------|
  | Voice as subtle flavor | 30-40% | Gentle influence, maximum generation polish |
  | Balanced voice + quality | 40-60% | **Recommended starting point** — recognizable with manageable artifacts |
  | Identity-focused | 60-70% | Quality trade-off begins here |
  | Maximum fidelity (caution) | 70-80% | Diminishing returns; artifacts increase faster than resemblance |

  Start at 50% and iterate in 5-10% increments. **The "above 70% is counterproductive" line is community-tested general guidance, not a ceiling** — see the three qualifications immediately below. Profile per voice rather than treating the table as a law.

  **Official escalation path when a clone doesn't sound right (OFFICIAL):** Suno's own guidance is to **raise Audio Influence first**, and if that doesn't fix it, **rebuild the voice profile from a clean acapella.** That is the opposite direction from the community ceiling, and it is the sequence to follow when the complaint is "this doesn't sound like me" — turn it up before concluding the clone is bad, and re-record from clean source before concluding the feature is.

  **Per-voice profiling can land well above the community range (LOCAL-OBSERVED).** Module production profiling of one voice found **clean results at 85%** where **55% showed artifacts** — the inverse of the table's expectation for that voice. One voice, not a general claim, but it is enough to establish that the ceiling is per-voice rather than platform-wide. Profile each voice: run the same short prompt at 40 / 55 / 70 / 85 and keep the number that voice likes.

  **Values split by intent, not by a single sweet spot (COMMUNITY for the split, ANECDOTAL for each number).** Primary-source users report: **70+** to preserve source character when layering v5.5 polish over older-model structure; **80** to stop invented intros on covers; **50+** to stop invented lyrics; **30-40** when the point is to let a strong style prompt through. **CONTESTED counterpoint** from the same discussions: "doesn't matter what you set influence to — 5.5 sheds way too much character," which is consistent with the broader v5.5 character-loss reports.
- Pairs well with delivery metatags (`[Whispered]`, `[Belted]`, `[Breathy]`, `[Raspy]` etc.) -- Voice sets *who* sings, metatags set *how*
- **Style Personas are NOT gone** — they are integrated into the Voices tab in v5.5. The button changed, but both features coexist. Personas still work on v4.5/v5/v5.5. Key difference: Voices is actual voice cloning, Personas is style essence capture. (Re-confirmed 2026-08: "Personas were never discontinued — they live inside the Voices menu." Correct any doc or profile that says Personas were replaced.)
- **Voices reached mobile and free plans on 2026-08-07** — iOS and Android, "now available to try on free plans. Do more on paid plans." OFFICIAL ([release notes](https://suno.com/release-notes)). The likely reading is that the *recording* entry point is free while clone creation and use stay paid, but that split is **not** stated anywhere — check the live UI before telling a free-tier user what they can do. The Voices FAQ has not been updated for mobile or free access.
- **Five identity layers now exist** — Style Persona, Voice, Lyricist, Custom Model, My Taste — and **stacking them creates conflict, not control** (ANECDOTAL, single authoritative source rebuilt 2026-08-01). Before building on a Persona, that source recommends recognition, controlled-variation, and boundary tests, and recording the source song + model version + full recipe. That last part is exactly what our band profiles are for.

**Getting the best voice clone:**
- **Clean recording matters more than expensive hardware** -- minimal background noise, no heavy reverb. A quiet room with a decent mic beats a studio mic in a noisy space. No compression, no background music. 44.1kHz minimum sample rate. The cleaner the input, the better the clone.
- **Consistency WITHIN a single clip wins** -- pick a part of your recording where you sound most like a single, stable version of yourself. No style switching, no big dynamic swings, no mixed energy levels within ONE sample. JG BeatsLab day-one testing found consistency dramatically outperformed mixed-register clips: "longer, more varied recordings underperformed compared to shorter, focused clips every time."
- **Optimal length is 20-30 seconds of clean consistent content per clip** -- longer samples (3+ min) actively underperformed in testing. Focus beats breadth within a single clip.
- **Variety across MULTIPLE clips, not within one** -- one clip works, three clips across different moods works better for capturing range and character. The resolution to the apparent consistency-vs-variety tension: each clip should be internally consistent (one stable character sustained), variety lives at the profile level by uploading multiple Voice profiles (e.g., "Narrative Rock," "Ballad Intimate," "Speak-Sing Confessional"). When a song is built, pick the Voice profile that matches the target vibe.
- **Natural delivery, not performance** -- Suno captures your natural vocal tone, not a performance. Sing or speak normally. First-take recordings that lean operatic, theatrical, or "poetry-voice" are a documented failure mode — the model captures the affect as character, and Voice generations will deliver that affect back on every generated song. Re-record if the first take feels performative.
- **Preserve vocal quirks, don't smooth them out** -- slight rasp, slide between notes, natural vibrato, sibilant character — the model captures character, and character is what makes a voice recognizable. Don't try to sound "cleaner" than you naturally do. (Sibilance is largely a mic technique issue, not a voice issue — angling the mic 15-30 degrees off-axis reduces direct sibilant hits without changing the voice itself. A pop filter placed further back also helps.)
- **Skill Level: Professional, always** -- JG BeatsLab testing was emphatic: "Professional produced the most stable, most consistent, most usable results across every test. The difference between Beginner and Professional is substantial — it actively reshapes how your voice is interpreted by the model. Set it to Professional. Every time." Not cosmetic. Not optional. Cannot be changed after recording — re-record if your Voice wasn't set to Professional the first time.
- **Range considerations** -- the Voice captures your current range, not your historical peak. If your range has narrowed, song selection for Voice tracks should work within current comfort. Most heartland rock / Americana / singer-songwriter territory doesn't require wide range anyway — it requires conviction.

**The v5.5 Voice-Character Principle:**

v5.5 Voice cloning trains on the user's vocal samples and captures **vocal character** — timbre, lilt, vibrato tendencies, attack patterns, dynamics behavior, mic artifacts. That's the literal training. There is no "trained genre gravity" — Suno adapts the captured character to the genre prompt: a Voice trained on a sample in one style can be used for songs in many styles. Training material genre ≠ output generation genre. (Example: a Voice trained on a Renaissance bawdy-song sample reliably generates folk, soft rock, and belt-forward arrangements depending on the song's prompt direction.)

**What Voice clones actually do:** They carry vocal character — how the singer delivers (breath, attack, held-note dynamics, vibrato tendencies, mic artifacts). This character is genre-neutral in itself. Suno's base model does associate some vocal characters with arrangement-default genres, which can *look* like "gravity" in early generations when the prompt is weak — but the cause is arrangement-default inference from voice character, not genre pre-baking in the clone. At most, the voice NAME itself (a clone called "Rock" vs one called "Soft") can lean Suno's interpretation via name-as-hint, but this is a subtler effect than the "gravity" framing implied. When matching a Voice to a song, frame it as **"the captured character fits X register well"** or **"this character's lineage is compatible with Y lane"** — NOT **"fighting the Voice's trained gravity toward Z."**

**Practical rules when shaping a song with a Voice:**

1. **Drop descriptors that duplicate what the Voice already delivers.** If the Voice captures vulnerable-breathy delivery, don't add "vulnerable delivery," "breathy," "soft male vocal" to the style prompt — they're redundant and can conflict with the captured character Suno will already reproduce. Use that budget for song-specific arrangement direction instead.

2. **Load descriptors that specify what the song needs from the arrangement.** The style prompt drives arrangement (instrumentation, genre, production, dynamics); the Voice provides the vocal character. Be explicit about arrangement — "overdriven rhythm guitar with crunch," "driving mid-tempo rock groove," "intimate fingerpicked acoustic" — rather than redundantly labeling what the Voice does.

3. **Keep Style Influence tight (65+)** so the prompt leads the arrangement firmly. The Voice character will shape the vocal delivery within that arrangement regardless; Style Influence governs how much the prompt directs the band.

4. **Never specify Vocal Gender when a Voice is active** — Voice defines it. Leaving Vocal Gender empty lets the Voice do its job; specifying can fight it.

5. **Voice-aware exclusion strategy** — when the Voice physically cannot produce harsh/screamed vocals (most clean-voice Voice clones can't), harsh-vocal exclusions are wasted Exclude Styles space. Focus exclusions on production and genre-direction protection (`heavy metal, heavy distortion, steel guitar, autotune, pop sheen`) instead of vocal protection. The clean Voice IS the natural guardrail against harsh vocals — trust it and reclaim the exclusion budget for what actually needs protection.

6. **Audio Influence floor caution** — the 30-40% "subtle flavor" range in the table above works with Professional-level Voices. For non-Professional Voices, dropping below ~40% can trigger a robotic-timbre failure mode where Suno's default interpretation bleeds into the Voice character and lands in uncanny valley. If a Voice wasn't set to Professional at recording time, keep Audio Influence at 50%+ until re-recording.

**Practical case study (what it actually validates):** A song written for a vulnerable-folk-leaning Voice clone but styled as heartland southern rock. First attempt used "warm vocals, vulnerable storytelling, clean male delivery" in the style prompt — all descriptors the Voice already delivered — plus "gentle Wurlitzer touches" and Audio Influence 20% (a Persona genre-departure setting, wrong for Voices). Result: robotic timbre, keyboards dominated the mix, too laid-back for the intended rock urgency. Fixed by: (1) dropping all vocal descriptors the Voice already delivered, (2) killing keyboards entirely from the style prompt, (3) loading rock-forward arrangement descriptors ("overdriven rhythm guitar with crunch," "cutting lead guitar accents," "driving mid-tempo rock groove"), (4) raising Audio Influence to 55% (Voice sweet spot), (5) removing harsh-vocal exclusions (the clean Voice couldn't produce them anyway), (6) specifying "heartland southern rock" as the genre anchor. Result: recognizable voice identity with the target rock arrangement.

**What the case study validates:** (a) correct Audio Influence setting for Voices (55% sweet spot), (b) don't duplicate descriptors the Voice already delivers, (c) specify arrangement/production direction explicitly.

**Custom Models:**
- Train on 6+ original tracks, 2-5 min training time, up to 3 custom models per account
- Pro/Premier only
- Drop generic production descriptors your model already knows -- if your Custom Model was trained on lo-fi indie tracks, you don't need "lo-fi warmth" in every prompt
- Think of Custom Model as "producer" and the prompt as "songwriter" -- the model brings the sonic palette, the prompt brings the creative direction
- Train separate models for separate styles -- mixing genres in training data confuses the model

**Training Data Best Practices:**
- **Format:** WAV at 44.1kHz preferred. Heavily compressed MP3 at low bitrates introduces artifacts that interfere with feature extraction.
- **Loudness:** System auto-normalizes (RMS leveling, DC offset removal, spectral masking, onset detection, key/scale estimation). Dynamic range preservation matters more than loudness — streaming-standard ~-14 LUFS is a reasonable baseline. Over-limited/brick-wall-mastered tracks may lose the dynamic character the model is trying to learn.
- **Quantity:** Minimum 6 tracks. 8-12 stylistically consistent tracks is the inferred sweet spot. No documented upper limit. Emphasis from all sources is on stylistic consistency over quantity.
- **Length:** Full-length tracks (3-5 minutes) provide richer training data for arrangement pattern learning. Short clips may not contain enough structural variety.
- **Quality:** Clean, well-mixed audio with minimal background noise and no heavy reverb. The system isolates vocals from mixed audio automatically, but acapella recordings may yield higher quality vocal style capture.

**Overfitting Mitigation:**
- Training data too narrow/homogeneous causes repetitive output with reduced variety
- Include variety within your chosen style lane — different tempos, moods, arrangements, instrumentation variations
- Overly detailed prompts + tightly-trained Custom Model = 'narrow and repetitive as if the AI has fewer options'
- Keep prompts shorter/simpler when using a well-trained Custom Model — it already knows your baseline

**Retraining (documentation gap):** No sources provide clear guidance on updating existing models, deletion workflow, or whether retraining from scratch produces different results. The 3-model limit serves as both a practical constraint and a platform retention mechanism.

Sources: [Custom Models — Suno Help](https://help.suno.com/en/articles/11362497) | [Blake Crosley: Suno Definitive Reference](https://blakecrosley.com/guides/suno) | [AudioNewsRoom: Suno v5.5](https://audionewsroom.net/2026/03/suno-v5-5-what-you-give-up-to-make-it-yours.html)

- **Voice + Custom Model is the most powerful combo:** who sings (Voice) + what style (Custom Model) + detailed prompt (creative direction)
- **Privacy/consent note (AudioNewsRoom):** The consent required to use Voices and Custom Models grants Suno permission to use your data for training their global models. This is NOT optional and NOT a private silo — you are uploading your creative fingerprint to their infrastructure.

**Voices limitations:** Voices is directional influence, not true vocal reproduction — the output drifts across generations and lacks true identity consistency (JG BeatsLab testing). Realistic for demo vocals, pre-production emotional direction, and hearing yourself in new compositions. **Not suitable for** spoken word/narration (Voices drifts toward singing patterns, inconsistent tone between sections, unnatural pacing in longer spoken passages — Suno remains music-first).

**My Taste:**
- Passive personalization that shapes generation defaults based on your listening/generation history
- All tiers (including free), enabled by default
- Takes 20-30 generations to show noticeable influence
- **Magic wand / Style Augmentation:** the **pencil-and-stars button** on the Styles field (hover text: "Personalize style prompt to match your taste") auto-generates a personalized style description from your My Taste profile. This is the primary way My Taste manifests. **It pre-fills the Styles field with ordinary, editable prompt text** (verified in live UI (Pro account, 2026-08-14)) — you can rewrite any part of it before generating. That matters for how you reason about it: the wand is a drafting shortcut, not a hidden layer applied at generation time, which is why explicit prompt content always wins.
- **Detailed manual prompts always override My Taste** — if you provide your own style prompt, My Taste is subordinate. Suno's stated boundary: "My Taste influences defaults, not your explicit prompts. A detailed style prompt always overrides My Taste preferences." The wand's behavior corroborates this mechanically: what it contributes arrives *as prompt text you can edit*, so a prompt you wrote yourself is not competing with anything hidden.
- **Controls: it CAN be turned off.** Avatar menu > "My Taste" to view, edit, or disable. Primary-source users (2026-08) confirm three separate counteractions: **delete individual entries**, **deactivate the feature**, and **write `...` into the taste board** (reported to restore variety). Location detail: **desktop browser only** — expand the nav, three dots, My Taste; on mobile you need browser mode. COMMUNITY.
- **The magic wand has its own toggle.** Turning My Taste off does not stop the wand from using the profile — there is a **separate control to make the wand disregard it**, and it has to be switched off independently. COMMUNITY. If a user says they disabled My Taste and still see its fingerprints, this is the first thing to check.
- **What contamination looks like** (COMMUNITY, concrete user reports): a stray element from the profile — one user's "train wheel foley," another's Swedish-language pull into English songs — appearing across unrelated generations, and profile elements surfacing **despite being listed in Exclude Styles.**
- **Profile-content guidance (ANECDOTAL, single experienced user) — and what it is NOT:** the advice is that a **hand-edited** My Taste profile works better carrying **no genre identifiers and no specific instruments** — only production and sonic qualities, moods, thematic overtones, and vocal qualities stated as universal generalities, because genres and instruments in the profile are what produce cross-genre bleed. **This is editing advice, not a description of what Suno produces.** Suno's own auto-derived wand pre-fill freely includes genre labels, named instruments, and even a numeric BPM (verified in live UI (Pro account, 2026-08-14)). So a pre-fill full of genres is not evidence the profile is misconfigured — it is just what the auto-derivation does.
- **"Genre Overrides" free-text field.** The My Taste profile-edit screen exposes a field labelled **Genre Overrides** — observed in live UI (2026-08-14); untested. It presents as though it expects genre tags, but it accepts free text, and **whether non-genre values (a BPM, a production descriptor, an instrument) do anything at all is entirely untested.** Do not build guidance on it, and do not tell a user it accepts BPM — only that the field exists, takes free text, and has not been tested.
- **Competing explanation worth knowing:** the user who most thoroughly investigated homogenising output tested My Taste on and off, different models, sliders, and browsers, and **nothing fully restored variety**; the hypothesis with support was **per-workspace accumulation** — "a fresh workspace restores variety." COMMUNITY observation, mechanism unverified. If a catalog starts sounding same-y, a new workspace is a cheap thing to try alongside the My Taste controls.

**Reproducibility consequence (COMMUNITY, 2026-08).** Whatever the mechanism, My Taste is a **per-account layer that shapes defaults** — built from history, likes, and skips, biting after roughly 20-30 generations, active on all tiers including free. **The consequence for prompt building: a vague prompt is no longer reproducible across accounts — a detailed one is.** Two people running the same thin prompt on different accounts get different pulls; the same fully-specified prompt lands the same way. This argues directly *for* the fully-specified-package bias this skill already has: specificity is now a reproducibility mechanism, not just a quality one.

*(Provenance note: an aggregation-based report in the same sweep claimed My Taste "cannot be disabled, no off-toggle." Primary sources contradict it directly — deactivation, entry deletion, and the wand toggle are all user-verified. The controls line above is the one to trust.)*

### v5.5 Personalization Stack

Layers from broadest to most specific:
1. **My Taste** -- shapes generation defaults passively
2. **Custom Model** -- sets production DNA and sonic identity
3. **Voice** -- applies a specific vocal tone and character
4. **Prompt** -- steers the specific song (always the most important layer)

### Tips

- All v5 Pro tips above still apply -- v5.5 is additive, not a replacement
- Lean into specificity: replace broad descriptors with granular ones where you have a clear sonic vision
- When using Voices, reallocate the characters you save from dropping gender/vocal descriptors toward production detail
- When using Custom Models, reallocate the characters you save from dropping generic production descriptors toward song-specific creative direction
- The generate -> replace sections -> refine loop is more efficient than regenerating from scratch on v5.5

## v4 Pro

### Prompt Style: Simple Descriptors

Straightforward genre + mood + basic production notes. Less nuanced than v4.5+ models.

**IMPORTANT: v4 Pro has a 200-character hard limit** (not 1,000 like v4.5+/v5). Every word must earn its place.

### Construction Pattern

```
[genre], [mood], [key instruments], [vocal type], [one production note]
```

### Example

> indie folk-rock, melancholic, acoustic guitar and ambient synths, male vocals, warm production

### Tips

- **200-character hard limit** — be extremely concise
- Keep it simpler than v4.5/v5
- Don't over-describe — diminishing returns on detail
- Focus on genre accuracy and mood

## Universal Rules (All Models)

1. **Character limits** — v4 Pro: 200-char hard limit. v4.5+/v5/v5.5: 1,000-char hard limit. All silently truncated at their respective limits.

    **Provenance caveat (added 2026-08-13):** these figures are **community-attested, not officially documented.** A full review of help.suno.com's article index on 2026-08-13 found **no** Suno article stating the 1,000-character style or 5,000-character lyrics limits — only third-party sites and API wrappers assert them. Nothing official contradicts the numbers either; they are neither confirmed nor refuted. Community reporting is also inconsistent (~200 chars for the v4 era vs ~1,000 for v5/v5.5; ~3,000 lyric chars on v4 vs ~5,000 on v5.5) — the v4-vs-v5 split is the coherent reading of that spread and is what we encode. Separately, Reddit-derived consensus suggests **soft** ceilings well below the hard limits: style under ~100 words and lyrics 100-120 words, past which content demotes to "optional suggestions" (ANECDOTAL, conflicts with the character-count figures). Keep enforcing 1,000/200 as the working limit, keep front-loading, and treat the limit as a validated-by-use convention rather than a documented platform fact. Verify in the live UI before changing the numbers.
2. **Critical zone (first ~200 chars)** — front-loaded terms have the strongest influence on generation. Front-load all essential genre, mood, and vocal descriptors within the first ~200 characters. Content beyond ~200 chars is supplementary but not wasted — it adds nuance and specificity. v5.5's improved descriptor interpretation may extend the effective window beyond 200 chars. A concise 100-char prompt can outperform a cluttered 200-char one, but a well-crafted 250-char prompt with specific descriptors can outperform a generic 150-char one. This is a priority guide, not a character limit.
3. **Word order is weighted** — front-loaded terms dominate generation. Priority order: Genre → Mood/Energy → Instruments → Vocals → Production. Whatever appears first sets the primary sound; everything after is progressively more "flavoring."

    **Exception for non-default vocal arrangements:** When the song requires a vocal arrangement that isn't the genre default (group backing vocals throughout a rockabilly or psychedelic-blues song, dual-vocal interplay in a singer-songwriter context, call-and-response in a genre where backing vocals are sparse), promote the arrangement descriptor to **position 1 of the style prompt** ahead of even genre. Example: `group backing vocals throughout, psychedelic swamp voodoo blues, narcotic gris-gris groove, ...`. Production-tested April 2026 on a song where positioning "group backing vocals" at position 3 produced inconsistent backing vocals; moving it to position 1 (combined with lyric-side wordless-chant intro — see lyric transformer's metatag-reference.md "Establishing Non-Default Vocal Arrangements") landed the pattern reliably. The genre signal stays strong enough at position 2 to drive the overall sound; what changes is Suno's pre-commit to the non-default arrangement being part of the song's identity.
4. **5-8 descriptors is the sweet spot** (HookGenius 1000+ prompt analysis, April 2026) — fewer than 4 produces generic results; exceeding 10 causes conflicting signals and quality degradation. Each descriptor should earn its place. **No community consensus exists on this number** (re-checked 2026-08): 4-7, 5-8, and 8-15 all circulate, each ANECDOTAL and none replicated against the others. Our 5-8 sits mid-range and is the most-repeated, so it stays the working default — but treat it as a default, not a finding, and don't argue a prompt down from 9 descriptors on the strength of it alone.
5. **Hyper-specific beats generic** — "1980s synth-pop" not "pop"; "distorted electric guitar, power chords" not "guitar." Era descriptors instead of artist names: "late 70s disco" not an artist name.
6. **Genre and mood always go first** — they're the strongest signal (see rule 3)
7. **Never put style cues inside lyrics** — style prompt and lyrics are separate inputs
8. **No asterisks or special formatting** in style prompts
9. **Never put artist names in style prompts** — Suno does not reliably replicate named artists. Decompose references into concrete sonic descriptors instead. **This is now backed by official policy, not just observed behavior** (OFFICIAL, [Building the future of music responsibly](https://suno.com/blog/building-the-future-of-music-responsibly), 2026-08-06): "We have never allowed prompts for specific artists or copyrighted songs"; artist names are **removed from prompts and redirected "toward descriptive musical characteristics"**; artist names are deliberately excluded from training metadata. So an artist name in the prompt does not merely fail — it is stripped, and the budget it occupied is wasted. Suno's Community Guidelines (updated 2026-08-06) separately prohibit reproducing existing songs and using a real person's voice or likeness without permission; stage names remain allowed.
10. **Negative/exclusion prompts go at the END of the style prompt** — positive descriptors first, cleanup last. "no [element]" is the most reliable in-prompt phrasing. Alternatively, use the separate Exclude Styles field. v5 handles in-prompt negatives better than v4.5.
11. **Comma separation works across all models** — consistent delimiter
12. **Describe, don't command** — "dreamy shoegaze with female vocals" over "Create a dreamy shoegaze song." (v4.5 examples use "Create a..." which matches Suno's own v4.5 docs, but descriptive style generally works better.)
13. **Production tags are the most underused category** (HookGenius analysis) — adding even one production descriptor ("radio-ready mix", "punchy drums", "wide stereo") meaningfully improves output distinctiveness. Most users rely only on genre + mood.
14. **"Cinematic" is a universal quality modifier** — HookGenius's 1000+ prompt analysis found it consistently elevates production quality across every tested genre. Most versatile single tag for enhancing output. (Note: in guitar/bass-led arrangements, "cinematic" can pull keyboard/synth — see the Dangerous Words and Keyboard Triggers table below. It is a texture modifier, not a genre.)
15. **Conflicting tags produce bland compromise** — "aggressive, peaceful" or similar contradictions cause Suno to default to a generic middle ground, not an interesting hybrid. Opposing descriptors cancel out.
16. **Callback phrasing during Replace Section** — when using Replace Section or Extend, re-inject genre/mood and use callback phrases like "continue same chorus energy" every 1-2 extends to prevent drift.
17. **BPM in style prompts — treat numbers as a ballpark at best** — on v4/v4.5, BPM tags have zero detectable effect on Suno's output (confirmed by librosa analysis: songs tagged 60 BPM were delivered at 95.7 BPM; songs tagged 65-150 BPM across sections were delivered at a steady 123 BPM). The claim that v5 handles plain-text BPM better (e.g. `"deep house, 122 BPM, A minor, hypnotic groove"`) is now **contradicted by primary-source reports on v5.5**: users describe Suno using numbers "as a ballpark," a set 92 BPM coming back at 124, and "slow tempo around 85 BPM" returning fast — with **pace words reported to outperform numbers**. (Social note: people still write BPM into prompts by convention, so seeing it in a shared prompt is not evidence it worked.) Rhythm nouns and pace words are the reliable levers; include a number only as a directional anchor, never as a spec.
18. **Use rhythm nouns for tempo feel** — "halftime groove," "double-time driving," "shuffle," "breakbeat" lock rhythmic feel far more reliably than BPM numbers or tempo adjectives like "slow" or "fast." These describe specific drum patterns Suno can interpret.

    **Candidate — "number + pace word."** One publisher recommends pairing the BPM number with a pace word rather than using either alone: `95 BPM, slow and deliberate` over a bare `120 BPM`. ANECDOTAL, single publisher, not replicated. It is consistent with our triple-signal tempo stacking (which already pairs a number with a rhythm noun), so it is worth an internal A/B — but do **not** adopt it as guidance until we have run one, and note the A/B now starts from a **skeptical prior**: primary sources say the number contributes little and the pace word is doing the work (see rule 17). **Bracketed BPM remains prohibited** and was independently debunked again in 2026-07 community work: brackets belong to structure tags in the Lyrics field, and a bracketed BPM in the Style field "is not how the field parses." That reinforces our existing plain-text-BPM baseline.
19. **Perceived tempo is controlled through lyrics, not the style prompt** — Suno delivers a single steady BPM per song. Perceived tempo changes come from lyrical density (short fragmented lines = slower feel, packed lines = faster feel), arrangement dynamics (instrument dropout = slower feel), and half-time/double-time drum patterns. The style prompt can request rhythm nouns and "tempo changes" as priming, but the actual perceived control lives in the lyrics field.

   **Foundational principle (production-confirmed 2026-04-29):** Suno does NOT actually shift tempo within a song. When a style prompt requests "tempo shifts" / "tempo changes" / "dynamic pacing," what Suno produces is **arrangement-density variation** (instrumentation pullback for halftime *feel*, compression for double-time *feel*), not actual BPM changes. Underlying tempo stays absolutely constant. Confirmed across multiple production tracks where the prompt explicitly asked for tempo changes — librosa-measured BPM steady end-to-end despite clear felt-shifts in lucid vs. dense sections. **Practical implication:** "tempo changes" in a style prompt is an *arrangement* directive, not a *tempo* directive. Plan for one underlying BPM per song; use rhythm nouns (`halftime groove`, `double-time driving`) and arrangement framing to vary perceived feel within that fixed tempo. Felt-tempo readings should be taken from the densest section where the pulse is most countable. See `suno-lyric-transformer/references/metatag-reference.md` "Half-Time / Double-Time Drum Feel" for the lyric-side techniques and any project's `docs/audio-analysis-reference.md` Felt BPM Corrections table for catalog examples.

## Duration Slider (v5.5, web only — new control surface, shipped 2026-07-20)

A **Duration slider** now sits in the web Create form: "Drag the new Duration slider in the Create form to pick your song length." OFFICIAL — [release note](https://suno.com/release-notes/duration-slider-on-web). **Web only, V5.5 only.** Suno published no min/max range, and the "How long will my song be?" help article was **not** updated — it still documents only Extend and the ~8-minute one-shot cap ([help](https://help.suno.com/en/articles/2409473)). Mobile support is unconfirmed.

**What the community has established (COMMUNITY unless noted):**

- **Range and mechanics:** Auto (the model picks) or Custom. The range runs **10 seconds to 6:00** — endpoints verified in live UI (Pro account, 2026-08-14), matching what the community reported. The **5-second increment granularity remains COMMUNITY-attested** and was not part of that observation. Set **pre-generation only**. It also **requires Style set to Custom** — if the slider is missing, that is the first thing to check, along with gradual rollout (its absence is not necessarily a bug).
- **Duration is a target, not a contract — and it fails in both directions.** Reported failure modes: a **hard cutoff** at the target with no resolution or fade; **rushed delivery, skipped sections, or mid-phrase termination** when a short target meets heavy lyrics; and, on long targets, a **premature end followed by a restart** — the song finishes around 3:05 and then begins again to fill a 5:30 target. (An earlier report described the long-target failure as trailing dead silence; primary sources describe end-then-restart, which is the more specific account.) The "rushing" is upstream of the arrangement — users describe the model bending BPM and cramming syllables to hit the number.
- **Adherence is genuinely inconsistent, and the reports are starkly split** — a controlled batch found 4 of 40 generations matching the target, while other users report 19 of 20 respected, 6 of 7 exact, and one user never getting past 3:00 in ten tries. COMMUNITY that it is inconsistent; nobody has explained the variance.
- **Worst on covers, remixes, extends, and custom models.** The slider only appears on the regular model, and extends targeted at 1:30-2:15 are reported coming back at 4:00 "with garbled crap after 15 seconds." Treat duration targeting as unavailable for derivative operations.
- **Weirdness at 100 reportedly breaks it** — all outputs 7:59 (ANECDOTAL). Consistent with the Weirdness-cliff findings in the slider section below.
- **Hidden persistence trick (ANECDOTAL, unreplicated):** set the duration on v5.5, then switch to v5 or v4.5 — the slider disappears but the value reportedly stays active. Unverified; do not build a workflow on it.
- **Recommended workflow: Auto first, then Custom.** Run Auto to find the song's natural length, then set Custom at natural **+10-15s** so the ending has room to resolve. Reported "golden length" is **2:00-3:30**.
- **It raises the stakes on explicit `[Outro]` tagging** (ANECDOTAL). An explicit outro is the mitigation for the hard-cutoff failure; the recommended form is `[Outro – short resolved ending]`. Framing worth keeping: the slider is "a production decision, not a repair button."

**How this interacts with what we already do:** our section-jobs discipline already says to let the words decide the length. The slider does not replace that — it constrains it. Use it when the target length is a real requirement (a placement, a playlist slot), set it from an Auto run rather than from a guess, and pair it with an explicit `[Outro]` every time. See `suno-lyric-transformer/references/metatag-reference.md` for the ending-tag mechanics it depends on.

**Related: time-based instructions in the lyrics are not a duration control.** Lines like `lyrics begin at 0:00; instrumental only after 1:45` at the top of the lyrics field are **not reliably parsed** (COMMUNITY, and confirmed in our own use). They are harmless as an extra and must never be load-bearing — a short instrumental intro is Suno-standard, and post-generation crop is the only deterministic way to control where the vocal starts. Full treatment in the metatag reference under "Structural Timing in Lyrics."

## Genre Keyword Ordering

Front-loaded terms dominate the generation. Whatever genre term appears first in the style prompt sets the primary sound — Suno treats it as the anchor, and everything after it is progressively more "flavoring."

When a genre should act as a secondary influence rather than the core sound, append qualifier words like "accents" or "undertones" to push it into the background. For example, `atmospheric swamp metal accents` tells Suno to use swamp metal as coloring rather than the main genre.

**Practical rule:** Put your dominant genre first. Demote secondary genres with "accents," "undertones," "influences," or "elements."

### First-Genre Dominance — Quantifying the Anchor

Community research is sharper than "first matters": **genre and subgenre tags collectively determine ~60-70% of arrangement output, with the first-position term holding the strongest single signal** (HookGenius 1000+ prompt analysis, 2026). A three- or four-genre fusion prompt is not a balanced stew. It's a dominant anchor in position one with increasingly faint color pulls from each subsequent term.

**Why this matters for counter-genre work:** When you're trying to push against a genre's gravity — accessible textures inside a heavy lane, slow pace inside a driving lane, acoustic framing under an electric identity — the counter-target genre has to occupy position one. Burying it at position 3 or 4 gives the counter-lane negligible arrangement influence, and Suno defaults to the first-position genre's conventions.

**Example:** `progressive metal, heartland rock, acoustic singer-songwriter` will read as progressive metal with trace heartland influence — the acoustic anchor contributes almost nothing. To actually produce an acoustic-leaning track, the compound must open `acoustic singer-songwriter, ...` with metal and heartland demoted behind it.

**Practical rule:** If you want genre X to drive the arrangement, X is position one. "Accents" / "undertones" / "influences" demote later terms but don't promote earlier ones — there is no way to get a buried genre to lead.

### Brass-Band Gravity — Aggressive Counter-Emphasis Required

When the prompt includes brass-band genre descriptors (`brass band`, `second-line`, `sousaphone`, `New Orleans funk-rock-brass fusion`, etc.), the brass gravity is exceptionally strong — strong enough that single-mention guitar or rhythm-section descriptors get buried in the gen output even when present in the critical zone.

**Production-confirmed pattern (A/B on a brass-fusion track):**

| Descriptor approach | Result |
|---|---|
| Genre-first + single guitar mention at position 5 (`Modern New Orleans funk-rock-brass fusion, ... electric guitar accents, ...`) | Guitar buried in output; brass dominates the mix |
| `rock-funk fusion, funk, New Orleans second-line, brass-band, swing` (user test) | Brass-heavy output, guitar barely audible |
| Single substantive guitar mention promoted to position 2 (`New Orleans funk-rock-brass fusion, overdriven rhythm guitar with cutting accents, ...`) | Guitar still gets buried in observed gens |
| **`Guitar-driven New Orleans funk-rock with brass band horns, overdriven rhythm guitar with cutting electric lead, ...`** — **THREE explicit guitar mentions in critical zone (Guitar-driven framing + overdriven rhythm guitar + cutting electric lead)** | Guitar finally surfaces in the mix; brass and guitar coexist as intended |

**Why this matters:** Standard guidance (single substantive descriptor at position 2-3 to promote a sub-element) is inadequate for brass-band genre gravity. Brass-band conventions are deeply trained — Suno defaults to brass-led arrangements when any brass-band-genre descriptor appears, and only aggressive counter-emphasis (genre-modifier framing + multiple explicit descriptors in the critical zone) shifts the balance.

**Practical rule:** When prompting for brass-band-fusion genres where guitar (or any non-brass instrument) needs to surface in the mix, treat the counter-element as a genre-modifier first, then reinforce with multiple explicit instrument mentions in the critical zone. Do not assume single-mention promotion will work — it has been observed to fail repeatedly with brass-band gravity.

**Counter-intuitive guidance:** This may LOOK like over-correction (three guitar mentions in 200 chars feels heavy-handed). Production testing confirms it's the right level for brass-band gravity specifically. The over-correction concern is wrong here — brass-band gravity requires it.

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

### Era Tags as Sonic Targets

Era-specific descriptors in the style prompt give Suno a production aesthetic target that single descriptors can't match. Use instead of artist names to evoke a period's sound.

| Era Tag | What Suno Produces | Notes |
|---|---|---|
| `80s synth` | Analog synthesizers, gated reverb, drum machines | Pairs well with synthwave, new wave |
| `90s grunge` | Distorted Seattle-sound guitars, raw production | Alternative rock territory |
| `90s hip-hop` / `90s boom bap` | Golden age sampling, hard drums, vinyl texture | Classic hip-hop production |
| `90s R&B` | New jack swing era production | Smooth, polished, Motown-adjacent |
| `2000s emo` | MySpace-era emotional rock | Pop punk, confessional |
| `2010s trap` | Atlanta trap wave, 808s, hi-hats | Modern hip-hop production |
| `60s psychedelic` | Summer of love sound, analog warmth | Reverb-heavy, experimental |
| `70s disco` / `70s soul` | Dance floor funk, Blaxploitation-era warmth | Groove-heavy, warm production |
| `vintage` / `retro` | General throwback sound | Broad — pair with a decade for specificity |

**Practical rule:** Era tags are stronger than individual production descriptors. `90s R&B` achieves more than listing "smooth, warm, polished, swing drums" individually. Combine era tags with genre for maximum precision: `90s boom bap, conscious rap` or `80s synth, darkwave`.

**Reported v5.5 shift (ANECDOTAL, single publisher, 2026-08):** era tags are said to bias production **more aggressively on v5.5** than on v5 — "1980s" pulling gated reverb and period synths harder — while genre tags have become broader, so a term like `synthwave` now reportedly needs an era tag plus an instrument anchor to land where it used to. Single-source and unreplicated. If a v5.5 generation comes back more period-costumed than intended, this is a plausible first thing to test (drop or soften the era tag); do not pre-emptively strip era tags on its account.

### Dangerous Words and Keyboard Triggers

Certain words reliably pull Suno into unwanted instrumental territory — typically theatrical, keyboard/synth-heavy, or cinematic-light arrangements. Avoid these when guitars and bass should lead.

| Word/Phrase | What Suno Does | Fix |
|---|---|---|
| `baroque` | Maps to theatrical/classical keyboard territory — Disney-adjacent | Describe Baroque qualities without the word: Bach counterpoint = `intricate interlocking guitar and bass melodies`; minor key ornamentation = `dark minor key, precise and ornate` |
| `orchestral`, `orchestral accents` | Defaults to light/cinematic strings, not heavy | Specify HEAVY orchestral instruments explicitly: `cello, heavy strings, kettle drums` — these live in metal's frequency range |
| `cinematic` | Pulls keyboard/synth-heavy arrangements | Use `dynamic shifts`, `building from gentle to crushing` instead |
| `rock opera` | Pulls keyboard/synth-heavy, theatrical arrangements | Use `power ballad`, `dynamic shifts`, `building from gentle to crushing` instead |

**"Baroque" workaround in detail:** If the song concept calls for Baroque-influenced metal, never use the word. Instead, describe the specific qualities you want — `intricate interlocking guitar and bass melodies` for counterpoint, `dark minor key, precise and ornate` for ornamentation. For orchestral weight, specify instruments that live in metal's frequency range: `cello, heavy strings, kettle drums`. Avoid `orchestral` as a standalone descriptor.

## Exclude Styles Field

The Exclude Styles field (Pro/Premier only) is a separate input from the style prompt. Key behaviors:

- **Functions as probability reduction, not a hard ban** — excluded elements are less likely but can still appear. Treat it as strong guidance, not a guarantee.
- **In-prompt negatives also work:** "no [element]" at the end of the style prompt is an alternative or supplement. v5 handles these more reliably than v4.5.
- **Limit to 2-3 most important exclusions** — too many exclusions destabilize the arrangement and produce unpredictable results. Prioritize the exclusions that matter most for the song.
- **Combine with positive instructions** — telling Suno what you DO want is more reliable than only excluding what you don't. Use Exclude Styles as a safety net alongside positive vocal/instrument guidance in the style prompt.
- **Past ~5 exclude terms, output reportedly goes "sparse and thin"** (ANECDOTAL) — a documented ceiling on top of our 2-3 preference. If a list has grown past five, cut it rather than adding.
- **Hyphen-prefix syntax works** (ANECDOTAL leaning COMMUNITY): a minus sign per term — `-oohs, -aahs, -humming, -vocalise, -crowd chants` — is reported working in the Exclude Styles field, and matches the minus-prefix form already used in our own catalog.
- **Weirdness above ~40 may override excludes** (ANECDOTAL, single user, who caps Weirdness at 40 to keep exclude integrity). This sits in direct tension with our production slider table, which routinely runs 50-75 and has not shown wholesale exclude failure — but it is a plausible partial explanation for the known "excludes are probability reduction, not a ban" behavior. **Practical reading:** if an exclusion keeps failing on a high-Weirdness song, try the same prompt at lower Weirdness before concluding the term is unexcludable. Do not lower Weirdness pre-emptively — the counter-genre work in this file depends on 60-70.
- **Never put a negation in a standalone lyric bracket.** `[no vocals]` and its relatives act as *positive* prompts — the model reads the noun and drops the negation. Negatives belong in this field. See the metatag reference, "Negation Inside Standalone Brackets Backfires."

### CRITICAL RULE: Excludes Defend Against Drift From the CURRENT Prompt ONLY

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

**The correct question for every exclude candidate:** *"What in my current style prompt could plausibly pull Suno toward this element?"* If the answer is "nothing in this prompt pulls that way," the exclude is wasted exclusion-field budget.

**Parallel-band-rendering work is the highest-risk context for this error.** When a song exists in two band catalogs (same poem, different genre/voice rendering), the temptation is to frame excludes as "defense against the other band's version." That framing is always wrong — Suno cannot be influenced by a version it has no knowledge of. Build excludes fresh for each rendering based on that specific prompt's descriptors.

## Vocal Behavior and Triggers

### Scream/Harsh Vocal Triggers

Certain words reliably trigger unwanted screaming or harsh vocals, even when the intent is melodic:

- `metal` on its own (without melodic vocal guidance)
- `sludge`
- `doom`
- `!` in lyrics (exclamation marks push vocal delivery toward shouting/screaming)

**Fix:** Always pair heavy genre terms with explicit positive vocal instructions. For example, `heavy swamp metal, raw melodic singing` or `sludge metal, gritty male vocals, no screaming` (plus "screaming" in Exclude Styles). Telling Suno what you DO want from the vocals is more reliable than only excluding what you don't.

### Crowd, Choir, and Extra-Vocal Avoidance

When the song needs **one singer** and nothing else, three layers work together. Any one alone leaks.

1. **Positive solo-singer language in the style prompt** — "solo lead vocal, one singer only," and where the energy is supposed to come from instead: "chorus energy from instruments and arrangement, not extra voices." Filling the role is stronger than forbidding the filler.
2. **Excludes covering the whole family** — `choir, backing vocals, gang vocals, layered vocals, crowd chants`. Excluding "choir" alone leaves gang vocals and stacked doubles untouched; they are different arrangement conventions and Suno reaches for whichever one the genre suggests.
3. **Avoid the trigger words entirely** — `anthemic`, `festival`, `stadium`, `crowd`, and **the whole "live" family** (see the warning under the descriptor table above) invite group vocals and audience texture by association. Excludes cannot reliably override a prompt that is asking for group energy in its adjectives.

The lyric side of this stack — section-tag wording that invites choirs, and the anti-choir tag forms — lives in `suno-lyric-transformer/references/metatag-reference.md`.

### Ad-Lib Suppression (COMMUNITY, 3+ users)

Unrequested ad-libs — improvised runs, "yeah"s, vocal fills — have two reported style-side levers:

1. **Style Influence 80%+.** Tighter prompt adherence leaves less room for the model to add its own vocal decoration.
2. **A denser style prompt with no empty space.** The reported contrast is stark: `Hard Rock, male vocal` is described as near-guaranteed ad-libs, while a ~20-descriptor prompt produces essentially none. The model appears to fill unspecified space with performance decoration.

**Note the tension with our own guidance:** this file documents that Style Influence above ~80 plateaus for genre accuracy and can flatten vocal phrasing variation, and that 5-8 descriptors is our working density. Both can be true — SI 80+ buying ad-lib suppression at the cost of phrasing variety is a trade, not a free win, and a 20-descriptor prompt is well past our conflicting-signals threshold. Reach for the density lever first (more *specific* descriptors, not merely more), and treat SI 80+ as the targeted fix when ad-libs are the specific problem being solved. Parenthetical density in the lyrics is the third contributor — see the parentheses risk note in the metatag reference.

### "Technical" as a Modifier

The word "technical" behaves differently depending on what it modifies:

- `technical guitar riffs` → produces shreddy, noodly guitar work
- `rocking guitar riffs` → better choice for most heavy songs that need energy without wankery
- `driving technical bass` → produces slightly more interesting bass lines without going overboard; worth including as a standard ingredient in bass-heavy arrangements

## Instrument-Specific Guidance

### Drum Programming

Drum descriptors are highly context-dependent — the same term produces different results depending on surrounding genre and energy keywords.

- **"Second line" drums** shift meaning based on context: paired with slow + atmospheric terms, they produce a hip-hop pocket feel; paired with up-tempo + energetic + hard rock terms, they produce a NOLA parade groove
- **Splitting funk from drums:** To get funky bass and guitars without funk drums, describe the funk in the bass/guitar descriptors and keep the drum descriptors in metal territory (e.g., `funky bass groove, driving metal drums`)
- **Swing and groove patterns:**
  - `swinging drums` + `blues-metal intensity` → Bill Ward-style groove (loose, behind-the-beat swagger)
  - `pounding drums` → rigid, mechanical, metronomic feel (use when you want deliberate, machine-like precision)

### Bass Prominence (Working Observation, Suno v5.5)

On Suno v5.5, our prompt approaches have not produced bass-forward rock or metal mixes. Whether this is a model-level limitation or a prompt-strategy limitation we haven't cracked is not yet established. What was tried (extensive iteration on one metal-lane track):

- Requesting "bass-forward" or "prominent bass" in the style prompt produced marginal results at best — bass remained buried in the mix
- `bass and drums only, no guitar` combined with guitar in the Exclude Styles field was the most effective approach found, but this requires removing guitar entirely rather than simply featuring bass
- `funk metal` as a genre term triggered slap/pop bass (Flea-style), NOT overdriven fingerstyle (Geddy Lee-style) — none of the approaches tried produced prominent overdriven bass in a full-band rock/metal context

**Treat bass-forward rock/metal as not-yet-cracked on v5.5.** If a song concept depends on prominent bass, consider the "bass and drums only" approach, try prompt strategies not yet attempted, or accept that bass will sit in a typical supporting-instrument position in the mix. Worth re-testing on future Suno model releases.

### Instrument Bleed-Through

The style prompt sets a GLOBAL instrument palette. Instruments mentioned anywhere in the style prompt bleed into ALL sections regardless of section-level `[Instrument: ...]` tags. This is a fundamental Suno limitation:

- Section-level `[Instrument: ...]` tags CANNOT introduce instruments not in the style prompt — they can only emphasize instruments already in the palette
- Adding "accents" after instrument names (e.g., "brass accents") reduces but does not eliminate bleed
- Placing section-specific instruments at the very END of the prompt minimizes but does not prevent bleed
- **Recommended workflow for section-specific instrumentation:** (1) Generate with all instruments in the prompt (accepting bleed), (2) Extract stems (Suno Pro splits into up to 12 stems including a dedicated brass stem), (3) Mute/remove unwanted instrument stems per section in a DAW like Audacity
- **Note:** External DAW editing is a one-way operation — once you edit outside Suno, you lose Suno's editing capabilities on that version

## Dynamic Control via Style Prompt

Style prompt directives for energy and dynamics override lyric-level energy tags (like `[Building]` or `[Fade]`). This is powerful but requires careful handling.

### Build and Climax

- `slow massive build to crushing climax` makes Suno build ALL the way through the song, steadily increasing intensity. It will ignore any fade or cooldown tags in the lyrics — the style prompt's arc instruction wins.

### Decrescendo and Comedowns

Getting Suno to bring energy back down is harder than building up. Patterns that work:

- `slow build then fade` — tells Suno the arc goes up AND comes back down
- `dynamic shifts loud to quiet` — encourages contrast rather than one-directional energy
- `prog rock` + `slow build then fade` — the prog rock genre context supports patient dynamics, making the fade instruction more effective

**Key insight:** If a song needs to come DOWN after a peak, the decrescendo instruction must be in the style prompt. Lyric tags alone are not enough to counteract a style prompt that implies continuous build.

### Three-Phase Dynamic Arc (Quiet → Massive → Quiet)

Getting Suno to execute a full quiet-to-massive-to-quiet arc requires redundancy. State the arc **twice** in the style prompt using different phrasing: `building from gentle to crushing then returning to gentle` AND `dynamic arc quiet to massive to quiet`. One statement is not enough — Suno latches onto "crushing" and rides it out through the end of the song. The redundancy forces Suno to register the full arc rather than just the peak.

### Brass-Out-At-Outro Limitation (Brass-Band-Fusion Genres)

**Documented platform limitation across v5 Pro and v5.5 Pro: brass-fade-out instructions in section tags or style prompts are unreliably honored for brass-band-fusion genres.**

Two production tests on the same source song confirmed the failure:
- **Heavy-lane rendering on v5 Pro** (swamp-metal + NOLA brass fusion) — used in-bracket per-section instrumentation tags including `[OUTRO — return to slow, sparse intro feel; sung; no brass; only final word whispered]`. Result: horns persisted throughout the song instead of fading at the outro. Documented as the primary failure mode at publish time.
- **Funk-lane rendering on v5.5 Pro** (modern NOLA funk-rock-brass fusion) — used v5.5 Pro's "significantly improved prompt accuracy," in-bracket per-section instrumentation (`[Intro] [Instrument: bare rock guitar, no brass]` ... `[Outro] [Instrument: no brass, bare rock guitar]`), AND stacked absence descriptors at intro/outro in the style prompt. Result: same failure — brass hits persisted into the outro and through the fade.

**Implication for Pro-tier users:** Pro tier DOES include Replace Section (Song Editor / Legacy Editor) and stem extraction (Auto Split, Split from Mix) — these are NOT Premier-only as initially documented, and Replace Section's Pro availability was re-confirmed official on 2026-08-13 with no deprecation announced. However, Replace Section has documented quality limitations that make it a poor fit for the brass-out use case specifically: melody drift on longer sections (10-30s, the size needed to fix a brass-persisting outro), audio degradation when chaining replacements, no way to splice in prior gens, and best-case use is on single-line / short-phrase spots — plus our own production finding of audible transition seams even at sweet-spot scale. Pure prompt-side techniques cannot reliably engineer brass-fade-out for brass-band-fusion genres, and Replace Section's limitations make it an unreliable fallback. Re-rolls don't fix it because the failure is consistent across attempts — Suno's brass-band genre gravity overrides outro fade instructions specifically. **Premier tier (Suno Studio 2.0)** offers more surgical tools — stem extraction with brass muted on the bookends, and multitrack export into a real DAW — but is the higher tier. (The Studio 1.x tool names this section used to cite, "Remove FX" and "Alternates / Quick Replace," are archived and no longer in official Studio copy; do not recommend them by name without checking the live UI.)

**How to architect around this:**
- **Plan for brass-persisting** when building brass-band-fusion songs. Don't expect the bookend-sparse three-act dynamic to land via prompt instructions alone.
- **Lyric-level adaptation:** if the song concept needs a sparse outro, consider whether the song works as a brass-band-fusion at all, or whether a different sub-genre anchor (rock-with-horn-section, NOLA R&B, etc.) would land the dynamic better than brass-band-led territory.
- **Subjective evaluation:** the build-up half of the three-act dynamic (Intro → V1 → Pre-Chorus carnival peak) DOES land cleanly in brass-band-fusion genres on v5.5 Pro. The failure is specifically the back-half release. Songs whose structural success doesn't depend on a sparse outro are unaffected.
- **Pro-tier Replace Section** (available, but with documented quality limitations): can be attempted on the outro section but expect melody drift, audio degradation when chained, and trial-and-error compromise. Documented best-case is single-line / short-phrase replacement; full-outro replacement is not its strength.
- **Premier-tier (Suno Studio 2.0) path** (NOT available to Pro users): post-gen stem extraction allows muting the brass stem on the intro/outro, and Studio's multitrack export carries the result into a DAW without spending a download against the monthly cap.

**The build-peak-elevated-settle dynamic archetype** is a direct consequence of this limitation — the outro can't return to bookend-sparse when brass keeps playing. That archetype emerges from the constraint rather than from a design choice, which is worth naming so it isn't mistaken for a stylistic preference.

## Slider Guidelines

### Weirdness and Style Influence by Song Type

These are starting-point ranges based on production testing. Adjust per song, but these give a reliable baseline.

**Do NOT anchor slider values to a band profile's stored `sliders:` defaults, nor to "what similar catalog songs used."** A band profile's stored slider values (if present) are a weak fallback for a bare Demo ("just make me something") ONLY — they are NOT the per-song anchor and must not be used as a baseline to nudge up/down from. For every real song, CHOOSE Weirdness and Style Influence fresh from this table + the song's type + counter-genre needs, reasoning from what each slider actually DOES. **The sliders are the deliberate per-song differentiator** — the mechanism for giving distinct feels to songs whose prompts are otherwise similar — so each is a fresh per-song decision, never a default. (Audio Influence is the one commonly left at a standard value: ~25% for Personas.) The user directive behind this rule: `docs/mac-preferences.md` → "USE the sliders." A documented failure (2026-06-07): the builder recommended Weirdness 55 by anchoring "above the profile's 45 default" instead of reasoning from behavior — for a dissonant/locked/counter-genre song that actually wanted ~75.

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

### Goal-Based Slider Recipes (ANECDOTAL — single source, consistent with the table above)

The most actionable external slider material found in the 2026-08 sweep (updated Aug 2026, single publisher). The ranges do not contradict our production-tested table; where they differ, ours wins because ours is measured on our own catalog. Useful mainly as a starting point for goals our table doesn't name — especially the upload/Audio-Influence cases.

| Goal | Weirdness | Style Influence | Audio Influence | Named failure mode |
|---|---|---|---|---|
| Clean and predictable | 25-40 | 60-75 | — | "competent but anonymous" |
| Strong genre identity | 25-40 | 75-90 | — | genre cliché |
| Stable hook with variation | 35-50 | 65-80 | — | — |
| Adventurous bridge | 55-70 | 50-65 | — | loses the thread |
| Uploaded melody should lead | 25-40 | 55-70 | 65-85 | — |
| Upload as loose inspiration | 40-55 | 60-75 | 25-45 | — |

Stated principle: "protect the most important result, run a controlled comparison" — i.e. change one slider, regenerate, compare, exactly as our one-variable-at-a-time rule already requires.

**Style Influence and Audio Influence compete — never run both at 100** (COMMUNITY). Reported balances for upload/remix work: sample-primary AI 60-70 / SI 30-40; tags-primary AI 30-40 / SI 60-70; balanced remix both 50-55. Pushing both high produces incoherent output rather than maximum control.

**Upload-context Audio Influence (ANECDOTAL, distinct from our Voice-clone standard):** a ~55% sweet spot for uploaded audio, with sample-length thresholds — under 15s tends to loop the sample verbatim, 30-60s is optimal, over 60s fragments. This is the *upload* case; our Voice-clone Audio Influence guidance in the v5.5 section above is separate and stands.

**Upper-end behavior, re-confirmed by primary sources (2026-08).** Our Weirdness-80 cliff finding holds, and field reports suggest the practical ceiling may be **lower** than 80: an unlistenable second half at 78, excludes reportedly overridden above ~40 (see the Exclude Styles section), and Weirdness at 100 breaking the Duration slider into 7:59 runaways. Our production table's 60-75 counter-genre range is unaffected; treat 78+ as the danger zone rather than 85.

**Weirdness is strongest during Extend and Bridge generation** — this is the primary cause of style drift in extended tracks. High Weirdness during Extend is more destabilizing than during initial generation. Keep Weirdness conservative during Extend operations; too-high Weirdness during Replace Section can also cause Persona/Voice identity shifts. Use callback phrasing ("continue same chorus energy") and re-inject genre/mood every 1-2 extends to prevent drift.

**Style Influence above ~80 plateaus** — increasing further rarely improves genre accuracy, and can reduce vocal phrasing variation especially in vocals.

### Default Weirdness Normalizes Counter-Genre Prompts

JG BeatsLab's v5.5 testing documents a default-Weirdness behavior that matters specifically for counter-genre work: _"v5.5 doesn't refuse niche genres — it reformats them. Give it a dungeon synth prompt and it will accept it, then quietly pull the output toward a polished, cinematic equilibrium."_ JG's practical guidance: _"Increase Weirdness for unusual fusions. The default Weirdness setting tries to normalize everything, which defeats the purpose of genre blending."_

This is the core counter-genre problem. Default Weirdness (50-55) quietly normalizes unusual descriptor combinations back toward Suno's trained equilibrium — polished, cinematic, conventionally-arranged. For prompts that mix against genre gravity (accessible inside heavy, slow inside driving, acoustic inside electric), push Weirdness to **60-70** to give the model permission to honor the unusual combination rather than reformatting it. The accessibility problem isn't Weirdness — it's genre-gravity pulling output back to the first-position anchor's defaults. Higher Weirdness attacks that normalization directly.

**Note:** The Extend-drift caution above still applies — higher Weirdness during Extend is more destabilizing than during initial generation. Use elevated Weirdness at the front end of the song, keep it conservative during Extend operations.

## Counter-Genre Prompting

Counter-genre prompting is when the desired output works **against** the gravity of the named genre — accessible clean guitars in a hard-rock prompt, a slow deliberate pace in a driving prompt, acoustic textures under an electric framing. Suno's default behavior is to honor genre conventions, and every new descriptor you add has to fight the first-position genre's gravity. Three techniques applied together reliably shift the arrangement instead of just decorating it.

### Displacement-Budget Descriptors

Adding `clean guitars` to a heavy-rock prompt doesn't remove the power chords — it just adds cleanness _alongside_ them. The power chords survive because nothing structurally displaces them. To actually displace an unwanted instrument voicing, fill the instrument's role-slot with a **structurally incompatible** descriptor — one that can't coexist with what you're trying to avoid.

| Wanted | Unwanted | Weak ask (doesn't displace) | Strong ask (displaces) |
|---|---|---|---|
| Accessible guitar texture | Power chords | `clean guitars` | `fingerpicked arpeggiated voicings` |
| Spacious feel | Wall-of-sound | `spacious mix` | `sparse instrumentation, single-guitar verses` |
| Restrained dynamics | Full-band bombast | `controlled dynamics` | `subdued mid-range, no full-band payoff` |

Think of the descriptor budget as a **displacement budget**: each descriptor either crowds out its opposite or just sits next to it. Descriptors that occupy the same role-slot and can't structurally coexist are the ones that move the arrangement. Descriptors that name a quality without naming a form are weaker — Suno can honor `clean` while still deploying power chords.

Production observation (single track, folk-lane counter-genre test): `fingerpicked arpeggiated voicings` produced the first fingerpicked section across any iteration of that song. Prior attempts using `clean guitars` had never displaced the power chords. Single-observation data, not A/B — but consistent with the displacement framing.

### Triple-Signal Tempo Stacking

Rhythm nouns (`halftime`, `double-time`, `shuffle`, `breakbeat`) land more reliably than tempo adjectives (`slow`, `fast`) — this is documented above. The counter-genre extension: stack **three aligned signals** simultaneously so genre-gravity can't overpower any single one of them.

1. **Genre with aligned tempo default** — pick a genre whose native tempo already points where you want to go. `slowcore`, `doom`, or `dirge` for slow; `speed metal`, `breakbeat electronica` for fast. Using a counter-tempo genre forces the other two signals to fight it.
2. **Numeric BPM approximation** — give a specific number even though Suno treats it as loose guidance. Numbers anchor the direction; they don't lock the result.
3. **Rhythm noun** — specify the rhythmic feel directly: `halftime feel`, `driving quarter-note pulse`, `swung eighth-note groove`.

Example counter-genre slow prompt against a driving rock identity: `heartland rock at 72 BPM halftime feel with patient southern slow-build dynamics` stacks all three (genre with slower default, BPM number, rhythm noun).

Production observation (same counter-genre test): switching from single-signal (`slow`) to triple-signal stacking dropped felt tempo ~6 BPM, raw tempo ~32 BPM, and improved halftime cleanness from a 2.2× non-clean ratio to a 1.95× near-clean ratio. The strongest confirmed-win technique of the three.

### 6/8 and 12/8 Compound Meter — Buys Feel, Not Meter (LOCAL-CONFIRMED)

Compound meter (6/8, 12/8) subdivides each beat into threes rather than twos, so at the same numeric BPM a 6/8 feel perceptually reads slower than a 4/4 feel — the listener counts triplet subdivisions and the pulse lands as a lilt rather than a drive. That is general music theory, and it is why compound meter looks like a second lever on perceptual tempo when genre-gravity keeps dragging the numeric BPM upward.

**What actually happens on Suno — confirmed across three module production data points (2026-07):** style-side compound-meter signals move **feel and tempo but not meter.** The sway arrives, the tempo drops, and the **subdivision stays 4/4.** This held across the full escalation: genre-lane words with native compound feel, `slow 6/8` front-loaded into the critical zone, triplet-feel descriptors, `[6/8]` tags, and full stacks combining all of them. More signal produced more sway, not more meter.

**This is the same class of behavior as `[Fade Out]`** — the directive reads as *flavor*, not as an instruction the generator executes. It is also consistent with the long-standing finding in this file that "odd time signatures" is ignored in a 4/4 rock/metal context.

**How to prompt given that:**
- **Expect 4/4.** Plan the arrangement, the lyric phrasing, and the felt-tempo target on the assumption that the subdivision will not change.
- **Keep at most one meter signal** — a single `slow 6/8` or `[6/8]`, held as aspiration. Stacking more of them spends critical-zone budget for no additional meter.
- **Spend the freed budget on tempo and feel words that do land** — rhythm nouns, a BPM approximation, `lilting`, `swaying`, `triplet-feel groove`. The sway is genuinely reachable; the meter is not.
- If a song's structural point *depends* on the meter changing, Suno is the wrong tool for that element — build it in a DAW.

**Studio note:** time-signature support arrived with Suno Studio 1.2, whose article stated the picker was "not yet sent to generative models." **That article is now archived** (Suno split its Studio docs into "Studio 2.0" and "Studio Archive" on 2026-08-13) and **none of the Studio 2.0 articles restate or retract the claim** — so it is **unverified for Studio 2.0**, not confirmed. Our finding above is style-side and holds regardless of what the Studio picker does.

### Synthesis — All Three Together

A counter-genre prompt deploying all three techniques in their right slots looks like:

```
acoustic singer-songwriter, heartland rock at 72 BPM halftime feel with patient southern slow-build dynamics,
fingerpicked arpeggiated voicings, subdued mid-range, no full-band payoff, slow 6/8 lilt

Weirdness: 65 | Style Influence: 75
```

- **Position 1 anchor** — `acoustic singer-songwriter` — the counter-lane, not the electric default
- **Triple-signal tempo** — genre (heartland, slower default than prog or speed), BPM (72), rhythm noun (halftime feel) all aligned
- **Displacement descriptors** — `fingerpicked arpeggiated voicings`, `subdued mid-range, no full-band payoff` — occupy role-slots that the unwanted qualities would need
- **One compound-meter signal** — `slow 6/8 lilt` — kept as a single aspirational nudge toward sway. **Expect 4/4 subdivision anyway**; it is here for the feel it reliably buys, not the meter it doesn't (see above). Two meter signals would be waste
- **Elevated Weirdness (65)** — permission for Suno to honor the unusual combination instead of reformatting to polished cinematic defaults

Any one of these alone can fail. Applied together they build redundant pressure against genre gravity — if one signal gets overridden by the anchor, the others hold the line.

## Persona Style Prompt Integration

The Persona auto-populates the Style of Music field. Song-specific prompts should **build on** this base, not replace it. The Style Prompt Builder should assume the Persona's Styles content is already present and add song-specific elements on top. The Persona's Styles field contains universal band DNA — the sonic identity that should be consistent across all songs. Song-specific elements (odd time signatures, tempo changes, brass accents, genre departures) get layered per-song on top of that foundation.

### Persona Bridge — Deriving a Persona From a v5.5 Voice (COMMUNITY)

To carry a v5.5 Voice's character into a Persona-based workflow (for use on models where the Voice isn't available, or where a Persona is the more convenient handle), the reported recipe is:

1. Generate a song with the Voice active at **Weirdness 0, Style Influence 0, Audio Influence 100**.
2. **Create a Persona from that generation.**

The slider extreme is the point: with Weirdness and Style Influence at zero and Audio Influence at maximum, the generation is as close to a pure rendering of the Voice as the platform allows, so the Persona derived from it captures the voice character rather than a prompt's arrangement. Note this deliberately violates the never-both-at-100 balance rule elsewhere in this file — that rule is about *making a good song*; this is about *making a clean capture*, and the output is a means, not a keeper.

**Adjacent workaround (COMMUNITY, 2026-08):** Voices were restricted to v5+ around 2026-07-28. Users report that switching **voice mode to "legacy"** makes v4.5 and v4.5+ work with Voices again — edited into the original thread as the accepted solution. Worth knowing before assuming a Voice is unusable on an older model.

### Persona Interaction Guidelines

- **Edit the auto-filled Style of Music intentionally** — the Persona populates it, but don't just leave it and pile on. Review and trim.
- **Keep style simple when Persona is active:** 1-2 genres, 1 mood, 2-4 instruments max. The Persona already carries vocal identity and character — the style prompt is the producer brief, not the artist identity.
- **Change ONE variable at a time** — adjust either the music direction OR the Persona settings, not both simultaneously. This isolates what's working vs. what's not.
- **Mental model:** Persona = artist identity (vocals, character); Style prompt = producer brief (sonic direction for this specific song).

### Voices and Custom Models (v5.5)

The full treatment of Voices (gender-drop, Audio Influence ranges, delivery-metatag pairing, the 15s-4min + anti-deepfake requirement, the Voice-Character Principle, the case study) and Custom Models (drop-generic-descriptors, train-separate-per-style, the Voice + Custom Model stack, privacy/consent) lives in the **v5.5 Pro** section above — see "Voices (a distinct feature alongside Personas)" and "Custom Models." Don't restate it here. Two style-prompt-construction points specific to *building the prompt* that aren't covered there:

**Prompt strategy shift with Custom Models:** When a Custom Model is active, the priority order changes from genre-first to **mood/production-first** since genre is already encoded in the model. Simpler, more natural-language prompts may outperform tag-heavy prompts because the model already handles foundational style characteristics.

- **Optimal formula with Custom Models:** MOOD + PRODUCTION TEXTURE + ENERGY/TEMPO + SPECIFIC INSTRUMENTS + VOCAL DIRECTION
- **What becomes redundant:** Base genre tags, broad stylistic descriptors matching training data, foundation-level production characteristics. Spend that freed budget on mood modifiers, production specifications, and contextual modifiers like 'cinematic', 'anthemic', 'intimate'.

## Cover Feature

Cover re-performs an existing song in a new style — it preserves the melody, lyrics, and structure while changing genre, instrumentation, vocal character, and production. Cover prompts use production language, clear genre descriptors, and specific instrumentation.

**CRITICAL: Covers are NOT eligible for commercial use — even on your own songs.** For commercial releases, create a fresh generation instead. This is a Suno platform restriction, not a suggestion.

## Persona and Inspo Playlist Behavior

### Inspo Playlist Warning

Using your own songs as Inspo playlist entries homogenizes the sound across generations. Suno pulls tonal and structural patterns from Inspo tracks, which flattens out the distinctiveness of new songs. **Drop Inspo when a song needs its own identity** — particularly for songs that are meant to stand apart from the rest of a catalog.

### Persona / Audio Influence on Era

Personas pull the overall sound toward the era of the source song used to create them. A persona built from a 70s-sounding track will drag new generations toward 70s production aesthetics, even when the style prompt targets a different era.

- Reducing Audio Influence to 10-15% helps but does not fully overcome the era pull
- For era-specific pieces where production style matters, consider generating without a persona entirely
- Alternatively, create era-specific personas — a "modern" persona and a "vintage" persona, for example — rather than fighting a single persona's baked-in era bias

**Note on Voices (v5.5):** Voices is a separate feature that sits alongside Personas — it does **not** replace them (both live in the Voices menu; Personas still work). For era work, prefer a Voice: because Voices is actual voice cloning rather than style essence capture, it carries less era bias — the Voice contributes vocal tone without dragging production aesthetics from a source song.

**When a Voice is active, drop timbre and gender descriptors entirely** (COMMUNITY, sharpened 2026-08 from the earlier "they matter less"). They are redundant — the Voice defines them — so the characters they occupy are pure waste; reclaim that budget for arrangement. **Delivery descriptors still matter** and should stay. The same logic applies to Custom Models: drop what the model already encodes, keep what directs this song.

### Audio Influence Slider Behavior

The Audio Influence slider controls how strongly the persona's source audio shapes the generation. The effective range is **15-25%** — values outside this range are either too detached or produce diminishing returns.

| Audio Influence | Behavior |
|---|---|
| 15% | Nearly loses persona identity — too detached for most uses |
| 20% | Holds identity loosely — allows significant genre departure. Use for experimental tracks or era-specific pieces where the persona's default era would interfere |
| 25% (default) | Strong persona anchor — the standard setting for both typical tracks AND acoustic/stripped songs |
| Above 25% | Diminishing returns — 40% tested, did not override an incompatible style prompt |

**Critical finding:** Acoustic and stripped-down songs can handle full 25% Audio Influence. The style prompt's genre descriptors override the persona's instrumental heaviness — the persona contributes only vocal identity. Only reduce Audio Influence when pushing into a different *heavy* genre where the persona's heaviness would compete with the target genre's heaviness.

## Iteration Best Practices

- **Generate 3-5 versions** per prompt before modifying — v5 produces more varied results than v4.5, and the desired result often appears on the 2nd or 3rd generation
- **Change only 1-2 variables** per iteration — isolate what works vs. what doesn't
- **Style Influence above ~80 plateaus** — increasing further rarely improves genre accuracy
- **For structural problems (wrong arrangement, bad section):** edit rather than re-prompt. At Pro that means the Song Editor's Replace Section plus Auto Split / Split from Mix stems; at Premier it additionally means Studio 2.0. Studio has always been Premier-only — do not offer it to a Pro user

## Reference Track Translation Guide

When a user says "sounds like X meets Y," decompose into concrete attributes. **Never put artist names directly into the style prompt** — describe the sonic qualities of the era and style instead.

### Confidence Check (Critical — Prevents Hallucination)

Before decomposing any reference, honestly assess: **do you confidently know this artist/song well enough to accurately describe their distinctive sonic characteristics?**

- **If confident** — proceed with decomposition using the extraction framework below
- **If uncertain** (obscure artist, very recent release, regional/niche genre, or you're unsure of specific details) — **use web search first** (if a search tool is available) to research the artist's sound, genre, instrumentation, vocal style, and production approach. Then decompose from researched facts, not guesses.
- **If uncertain and no search available** — tell the user honestly: "I'm not confident I know [artist] well enough to describe their sound accurately. Can you tell me what you like about their sound — the vibe, the instruments, the vocals?" Then decompose from the user's description instead.

**Never fabricate sonic details for an artist you don't confidently know.** A wrong decomposition produces a style prompt that sounds nothing like what the user intended — and they won't know why until they hear the result.

### What to Extract from a Reference

- **Genre/subgenre** — what musical tradition?
- **Era/production style** — vintage analog? modern digital? lo-fi?
- **Vocal character** — what makes their voice distinctive?
- **Instrumentation signature** — what instruments define their sound?
- **Energy/dynamics** — how does the song move? build? stay flat? explode?
- **Emotional tone** — what feeling does it evoke?

### Example Decomposition

- "Bon Iver meets Radiohead" → falsetto vocals, ambient electronics, acoustic guitar foundation, experimental song structures, melancholic beauty with electronic tension, lo-fi warmth with glitchy textures
- "Dolly Parton meets Daft Punk" → country storytelling over electronic production, warm female vocals with robotic harmonies, acoustic meets synthesized, playful but polished

Always show the user your decomposition before building the prompt so they can confirm or correct your interpretation.

## Community Research Sources

> **Last updated:** August 13, 2026. These informed the findings above. Verify against current Suno behavior.

### Added in the 2026-08-13 sweep

- [Suno: Duration slider on web](https://suno.com/release-notes/duration-slider-on-web) (OFFICIAL, 2026-07-20) — the slider exists, web + V5.5 only; no range published
- [Suno: Building the future of music responsibly](https://suno.com/blog/building-the-future-of-music-responsibly) (OFFICIAL, 2026-08-06) — artist-name prompts have never been allowed, are stripped and redirected to descriptive characteristics, and are excluded from training metadata; watermarking/fingerprinting rollout
- [Suno Community Guidelines](https://suno.com/community-guidelines) (OFFICIAL, updated 2026-08-06) — no reproducing existing songs, no real-person voice/likeness without permission; stage names still allowed
- [Suno: Updates to our Terms of Service](https://suno.com/blog/suno-updates-tos) + [Terms effective Sept 3 2026](https://suno.com/terms-september-2026) + [Download limits FAQ](https://help.suno.com/en/articles/13614785) (OFFICIAL) — download caps, download-bound commercial rights, model retirement
- [Suno x BMG partnership](https://suno.com/blog/suno-partnership-bmg) (OFFICIAL, 2026-08-12) — next model developed with the music industry; no name or date
- [JackRighteous: Creative Control Sliders](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/creative-control-sliders-suno-v5) (ANECDOTAL, updated 2026-08) — the goal-based slider recipes table
- [aiunfiltered: Suno AI prompt guide 2026](https://aiunfiltered.beehiiv.com/p/suno-ai-prompt-guide-2026) (COMMUNITY, 2026-07-08) — bracketed-BPM debunk; field separation discipline
- **Not found / verified-absent (2026-08-13):** no official documentation of style or lyric character limits; no official prompt best-practices publication since mid-July 2026 (only an Aug 5 short-form *video* guide); no change to the Creative Sliders article (still exactly three sliders, no numeric ranges or defaults, Duration not mentioned there); no change to Exclude Styles; no change to section tags or metatags; no public Suno API.

### Added 2026-08-14 — primary-source pass (r/SunoAI)

A direct primary-source sweep (38 fetches, 22 threads, findings read from post and comment text rather than aggregations) contributed the v5.5 quality characterization, the within-track degradation reports, the duration-slider adherence split and its Custom-style requirement, the intent-split Audio Influence values, the My Taste controls resolution, the ad-lib suppression levers, the negation-in-brackets behavior, the hyphen-prefix excludes, the Weirdness upper-end reports, and the BPM contradiction. These are individual user experiences, not controlled tests — graded inline as COMMUNITY where several independent users agree and ANECDOTAL where one does. Where they contradict an aggregation-based claim (My Taste), the primary source wins.

### Promoted from module production testing (2026-07/08)

Findings previously held only in internal notes, now documented above with their evidence strength: the **"live" word-family crowd-noise trigger** (LOCAL-CONFIRMED, recurring — and the reason the `raw live recording` descriptor was removed from the effects table), **compound meter buying feel but not meter** (LOCAL-CONFIRMED, 3 data points), **per-voice Audio Influence profiling above the community ceiling** (LOCAL-OBSERVED, one voice), and the **anti-extra-vocal stack**. Nothing external replicates these; they are ours and are labelled as such.

### Earlier sources

- [HookGenius: 1000+ Prompt Analysis](https://hookgenius.app/learn/suno-style-tag-research/) — Tag count sweet spot (5-8), "cinematic" modifier, production tag findings, conflicting tag behavior
- [HookGenius: Complete Suno Prompt Guide 2026](https://hookgenius.app/learn/suno-prompt-guide-2026/) — Genre tags carry 60-70% of arrangement influence, first-position dominance rule, descriptor specificity
- [HookGenius: Suno Tempo BPM Guide](https://hookgenius.app/learn/suno-tempo-bpm-guide/) — BPM number as approximate guidance, rhythm-noun vs. adjective, dual specification pattern
- [HookGenius: Negative Prompting Guide](https://hookgenius.app/learn/suno-negative-prompting/) — Exclude Styles behavior and in-prompt negatives
- [JG BeatsLab: 7 v5.5 Behaviors](https://www.jgbeatslab.com/ai-music-lab-blog/suno-v5-5-behaviors-every-creator-needs-to-know) — "Polished cinematic equilibrium" normalization behavior, Weirdness guidance for unusual fusions
- [JG BeatsLab: Voices Day One Testing](https://www.jgbeatslab.com/ai-music-lab-blog/suno-v5-5-voices-tested) — Voices Audio Influence real-world ranges, Skill Level dropdown
- [Blake Crosley: v5.5 Reference (MILO-1080)](https://blakecrosley.com/guides/suno) — Meta tags, Style-of-Music field, numeric BPM as approximate guidance
- [AudioNewsRoom: Voices/Custom Models Consent](https://audionewsroom.net/2026/03/suno-v5-5-what-you-give-up-to-make-it-yours.html) — Privacy analysis
- [JackRighteous: Creative Control Sliders](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/creative-control-sliders-suno-v5) — Genre-specific slider ranges, Extend drift findings
- [Suno Official v5.5 Docs](https://help.suno.com/en/articles/11362305) — What's New, Voices, Custom Models, My Taste
- [Suno Studio 1.2 Release Notes](https://suno.com/blog/studio1_2) — Time Signature support, Warp Markers, Remove FX, Alternates (Feb 2026). **Superseded:** Studio 2.0 shipped 2026-08-13 and Suno moved the 1.x articles into a "Studio Archive"; those feature names are not in current official copy, and the "time signature not sent to generative models" line is unverified for 2.0
