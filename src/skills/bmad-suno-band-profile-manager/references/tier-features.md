# Suno Tier Feature Matrix

> **Last validated:** March 2026 (Suno Free, Pro, Premier plans). Suno updates pricing, features, and tier boundaries frequently — use web search to verify against current Suno pricing page when uncertain.

**Note:** The `./scripts/tier-features.py` script is the authoritative source for this data. This reference file is provided for human readability. When updating, update the script first.

## Plan Comparison

| Feature | Free ($0) | Pro ($10/mo, $8/mo annual) | Premier ($30/mo, $24/mo annual) |
|---------|-----------|----------------------------|----------------------------------|
| **Model Access** | v4.5-all only | All models incl. v5, v5.5 | All models incl. v5.5 + Studio |
| **Credits** | 50/day (~10 songs) | 2,500/mo (~500 songs) | 10,000/mo (~2,000 songs) |
| **Credit Cost** | 10/song, 5/extend | 10/song, 5/extend | 10/song, 5/extend |
| **Song Length** | Determined by model — v4.5-all supports up to ~8 min | Determined by model — v4.5/v5 support up to ~8 min | Determined by model — v4.5/v5 support up to ~8 min |
| **Download Quality** | 128kbps MP3 | 320kbps MP3 + WAV | 320kbps MP3 + WAV |
| **Commercial Use** | No | Yes (new songs) | Yes (new songs) |
| **Personas** | No | Yes (v4.5/v5 only; replaced by Voices in v5.5) | Yes (v4.5/v5 only; replaced by Voices in v5.5) |
| **Voices** | No | Yes (v5.5 voice cloning) | Yes (v5.5 voice cloning) |
| **Custom Models** | No | Yes (up to 3 models) | Yes (up to 3 models) |
| **My Taste** | Yes (passive) | Yes (passive) | Yes (passive) |
| **Weirdness Slider** | No | Yes (0-100) | Yes (0-100) |
| **Style Influence Slider** | No | Yes (0-100) | Yes (0-100) |
| **Audio Influence Slider** | No | Yes (0-100, with audio upload) | Yes (0-100, with audio upload) |
| | | *10-15% reduces persona era-anchoring* | *10-15% reduces persona era-anchoring* |
| **Add Vocals/Instrumental** | No | Yes | Yes |
| **Stems** | No | Up to 12 | Up to 12 |
| **Audio Upload** | 1 min | 8 min | 8 min |
| **Advanced Editing** | No | Yes | Yes |
| **Studio** | No | No | Yes |
| **Studio 1.2 Features** | No | No | Yes (Warp Markers, Remove FX, Alternates, Time Signature) |
| **MIDI Export** | No | No | Yes |
| **Queue Priority** | Shared | Priority, 10 at once | Priority, 10 at once |
| **Add-on Credits** | No | Yes | Yes |

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

## Profile Implications by Tier

**Free tier profiles should:**
- Set `model_preference` to "v4.5-all" (only available model)
- Omit or zero out `sliders` (not available)
- Not reference Personas or Voices (not available)
- Focus style_baseline on conversational descriptions (v4.5-all strength)
- My Taste is active passively — no profile configuration needed

**Pro tier profiles can:**
- Use any model including v5 Pro and v5.5
- Set Weirdness and Style Influence sliders
- Reference Suno Personas for vocal consistency (v4.5/v5 models)
- Use Suno Voices for vocal consistency (v5.5 model — replaces Personas)
- Use Custom Models (up to 3, trained on 6+ original tracks, 2-5 min training time)
- Use crisp, descriptor-focused style for v5 Pro
- Use Audio Influence slider to manage persona era-anchoring (reduce to 10-15% when the persona's source era conflicts with the desired sound)
- When a Voice is configured, omit gender vocal descriptors from style_baseline — the Voice defines the vocal identity

**Premier tier profiles can:**
- Everything Pro can do, plus Studio features
- Set studio_preferences (BPM, key, time signature)
- Stems separation for production work
- MIDI export for DAW integration
- Voices and Custom Models (same as Pro)

## Production Notes

**Audio Influence as Era Control (Pro/Premier):** When a persona's era-anchoring conflicts with the desired era for a track, reducing Audio Influence from the default 25% to 10-15% helps pull the sound away from the persona's source era. This doesn't fully eliminate the anchoring — for strong era shifts, consider generating without a persona or creating an era-specific persona from an era-appropriate source song.

**Audio Influence Effective Range (Pro/Premier):** The practical range for Audio Influence is 15-25%. Values above 25% show diminishing returns — tested at 40%, it did not override an incompatible style prompt. The slider shapes the persona's contribution but cannot force the persona's character over a conflicting style direction.

**Acoustic/Ballad Tracks and Audio Influence (Pro/Premier):** When the style prompt clearly defines a non-heavy genre (ballad, acoustic, stripped-back), the persona contributes only vocal identity — it does not drag in unwanted instrumentation. Do NOT reduce Audio Influence for ballads or stripped tracks; keep it at the normal working range. The style prompt governs the arrangement; the persona governs the voice.

**Exclude Styles — Known Limitations:** The Exclude Styles field helps shape tone but does not reliably remove instruments entirely. For example, even with "guitar" in Exclude Styles, Suno still produces guitar in rock/metal contexts. Treat Exclude Styles as a nudge toward the desired balance rather than a hard instrument filter.

**Personas to Voices Transition (v5.5):** Personas are replaced by Voices in v5.5. Existing Personas still work on v4.5 and v5 models. For v5.5 generation, use a Voice instead. Voices are created from a 15-second to 4-minute audio sample and include anti-deepfake verification. Voices are private to the account that created them.

**Voices and Vocal Descriptors (v5.5, Pro/Premier):** When a Voice is active, the Voice defines the vocal identity — gender, tone, and character come from the audio sample. Omit gender vocal descriptors from the style prompt to avoid conflicts. Other vocal direction (delivery, energy, diction) can still shape performance.

**Custom Models (v5.5, Pro/Premier):** Custom Models are trained on 6 or more original tracks and take 2-5 minutes to train. Up to 3 Custom Models per account. They capture a production style and sound signature. When a Custom Model is active, it shapes the overall production character — the style prompt should complement rather than fight the model's learned style.

**My Taste (v5.5, All Tiers):** My Taste is passive personalization derived from the user's generation history. It requires no configuration and works across all tiers including Free. It subtly shapes generation output based on patterns in what the user has created and liked.
