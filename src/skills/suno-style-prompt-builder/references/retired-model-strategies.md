# Retired Model Strategies (retired 2026-09-09)

> Loaded by `:migrate` (when the source or target is a retired model) and when a user asks about an older record. Every pre-v6 model is retired: it can no longer generate, and songs made on it stay playable. Current-model guidance is in `references/model-prompt-strategies.md`.

Everything in this file describes models that can no longer generate. It stays because older profiles and songbook entries name these models and because `:migrate` reads it. Findings from this era that still describe features on v6 — the Voice-Character Principle, Custom Models, My Taste, the descriptor findings — live in `references/model-prompt-strategies.md`, and the "live"-family warning in `references/safety-tables.md`. Treat model-specific claims below as history until re-confirmed on v6.

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

## v5 Pro (retired)

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

- **Emotional descriptors beat technical ones:** "raw, yearning" > "120 BPM". Use rhythm nouns instead of BPM values: "halftime groove," "double-time driving," "shuffle feel." (v5 may respond better to BPM in style prompts than v4/v4.5 — see "Universal Rules" in `references/model-prompt-strategies.md` — but rhythm nouns remain more reliable.)
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

**Three-Pass Layered Prompting (v5 technique):**

For complex songs, build the prompt in three conceptual passes rather than trying to specify everything at once:

1. **Idea pass** — define concept, mood, genre (the style prompt core)
2. **Lyric pass** — write/refine lyrics with structural tags
3. **Performance pass** — add vocal delivery cues, energy tags, dynamics

This separates concerns and prevents overloading any single input field.

## v5.5 Pro (retired)

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

- **It corroborates our own bass-forward limitation** (see "Bass Prominence" in `references/model-prompt-strategies.md`). Muted bass is not our prompting failing to land; it is what the field reports as the model's default balance.
- **Counter-programming the defaults is the job.** Production descriptors that fight compression and polish (`dynamic range`, `open mix`, `unpolished room sound`, `breathing room`) earn their place more on v5.5 than they did on v5.

**Within-track degradation past ~2 minutes — the most replicated technical claim in the 2026-08 sweep (4 independent reports).** Vocals lose timbre and turn robotic somewhere past the 2-4 minute mark ("ends up sounding like Alvin the Chipmunk"), and the style prompt reportedly stops being followed after the first 1-2 minutes. The circulating workaround is to **build in sub-2:00 segments and stitch**. This does not overturn our long-form work, but it does mean: when a long generation goes wrong in its back half specifically, suspect the length rather than the prompt, and consider whether the song can be built in two passes. It also raises the value of Replace Section on late material over full regeneration.

**Early-August 2026 wobble cluster (individually ANECDOTAL; the clustering is the signal):** broken composition and off-beat output (08-07), songs cutting off oddly (08-12), and a claimed A/B showing the v5.5 remaster engine adding high-frequency harshness versus native v4.5 even at Subtle strength (08-14). If output quality seems to have changed underneath a known-good prompt, this is a real possibility rather than user error.

### Tips

- All v5 Pro tips above applied -- v5.5 is additive, not a replacement
- Lean into specificity: replace broad descriptors with granular ones where you have a clear sonic vision
- When using Voices, reallocate the characters you save from dropping gender/vocal descriptors toward production detail
- When using Custom Models, reallocate the characters you save from dropping generic production descriptors toward song-specific creative direction
- The generate -> replace sections -> refine loop is more efficient than regenerating from scratch on v5.5

> v5.5's Voices, Custom Models, My Taste and Personalization Stack notes still apply on v6 and live in `references/model-prompt-strategies.md` → "Voices, Custom Models, and My Taste".

## v4 Pro (retired)

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
