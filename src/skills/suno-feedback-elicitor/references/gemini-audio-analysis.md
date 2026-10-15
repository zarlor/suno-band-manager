# Listening Analysis with Gemini and ChatGPT

For a deeper listen to one track than the scripts give: instrument presence, the dynamic arc, mood and energy, and how far the render matches its style prompt. The user runs these tools and pastes the result; you set it beside their ear.

## Trust by field

- **Measurable fields (BPM, key, energy, section boundaries, spectral balance):** the scripts are primary — they measure the waveform, their quirks are predictable, and they don't hallucinate content. For BPM take the scripts' tempo (Beat This! when the PyTorch audio tools are on, librosa otherwise); LLM BPM estimates are rough and diverge between tools, and Gemini may read subdivisions as the pulse. For key, Gemini tends to read minor where librosa reads major on the same track; without ground truth neither wins, so use the lyric and emotional context as a tiebreaker or record both readings.
- **Instruments:** the basic rhythm section and lead vocal (guitar, bass, drums, vocals) are reliable from either tool. Hold anything beyond it (brass, strings, synths, pads, extra percussion) loosely and verify it against the audio: reverb tails, delays and ambient swells get reported as instruments, and atmospheric production words in the style prompt ("cathedral roominess", "wide analog stereo with shimmer") raise that risk.
- **Mood and whether a track lands:** the human ear is primary. An AI's mood reading follows the prompt's framing, and it reads heaviness as aggression by default, missing playful or ironic energy.

These calibrations hold across catalogs; don't relitigate them per track.

## ChatGPT: a blind first listen

Upload the MP3 with no style prompt or context and ask what it hears (genre, instruments, mood, vocal style, production): a model shown the prompt tends to hear the prompt. Then share the prompt and ask it to compare intent with result. Its audio analysis is inconsistent across tracks — accurate on one, unrelated on another — so treat it as a supplementary data point: when it agrees with the scripts it's likely right; when it's off by a genre family or by more than 30% on BPM, discard it.

## Gemini

**Setup:** Google AI Studio rather than the Gemini web app, a Pro model, Thinking high, **temperature 0.5** (a blind first pass at 0.5 beat 0.3 with the style prompt: better genre description, more accurate instruments, fewer hallucinations), everything else off (no grounding, search, code execution or structured output). Export the MP3 from Suno (WAV adds nothing). A new context per song. The web app's rate limit is separate from AI Studio's; alternate when a daily limit hits.

**Two passes for fusion genres:** the first pass flattens a fusion to its nearest pure genre ("NOLA brass-metal" → "ska-punk"). The follow-up in the same context is what surfaces the real fusion, bass technique and dynamics. Keep follow-ups neutral: asking about a specific instrument can trigger a hallucination where the first pass was right, and leading framings ("this band plays genre fusion") prime invented content.

**Reliable:** the basic stack, macro genre family, the Style Prompt Accuracy section (the most valuable output), timestamped structure, stereo placement when asked. **Unreliable:** fusion on the first pass, volume dynamics on the first pass (it calls a track "consistently dense"), bass technique until asked, the last 10 seconds, intros.

### First Pass — Structured Blind Analysis

Use this for the initial analysis. For a diagnosis (why a song sounds wrong), remove the Style Prompt Accuracy section and share the prompt in a follow-up; for cataloging, keep it for the comparison in one pass.

```
You are analyzing a track from the band [BAND NAME] for cataloging purposes. Listen to the full track carefully before responding.

IMPORTANT LISTENING NOTES:
- Distinguish between tempo changes (BPM actually shifts) and dynamic changes (volume/intensity shifts without tempo change). A song can get quieter or sparser without slowing down. Report both separately.
- Describe the genre or genres you actually hear without assuming a fusion is present. If the track is in a single sub-genre, name that single sub-genre. If you hear multiple genre influences blended together, name all the ingredients you actually hear — but do NOT manufacture a fusion that isn't present in the audio.
- Only describe instruments and elements you can clearly identify. Do NOT manufacture content that isn't there. If you're uncertain whether something is an actual instrument or a production effect (reverb tails, delay echoes, atmospheric pads, ambient swells), describe what you hear without assigning it to a specific instrument category. Reverb-heavy production can sound similar to brass or strings in places — don't guess.
- For BPM, tap along to the most consistent rhythmic pulse (usually kick/snare or hi-hat). Report the underlying quarter-note pulse, not subdivision rates (don't count eighth notes or sixteenths as the BPM). Do NOT adjust your BPM estimate to fit a "feels fast" or "feels slow" impression — report what your tap-along count actually gives you, then separately note if the song feels different from that count.

Provide your analysis in this exact format:

## Technical
- **Estimated BPM:** [BPM or range if it shifts, note where shifts occur]
- **Estimated Key:** [key/scale]
- **Time Signature:** [detected, note any changes with approximate timestamps]
- **Duration:** [mm:ss]

## Sonic Profile
- **Intro (first 15 seconds):** [exactly what instruments enter, in what order, what they're doing]
- **Overall Genre Feel:** [describe the blend of genre influences you hear — this band fuses multiple styles, so name all the ingredients, not just the dominant one]
- **Guitar:** [tone, style, notable techniques — clean/distorted, riff-driven/atmospheric, any solos and where]
- **Bass:** [how prominent, tone, role — following guitar or independent, any standout moments]
- **Drums:** [style, energy, notable fills or pattern changes, cymbal work]
- **Vocals:** [delivery style, grit level, harmonization, how many voices, any spoken/whispered sections]
- **Other Instruments:** [brass, keys, strings, anything else present]

## Dynamic Arc
Describe how the energy moves through the song from start to finish. Note builds, drops, peaks, and transitions with approximate timestamps. Separately note any volume/intensity shifts that occur WITHOUT tempo changes.
- [0:00-0:xx] — [what's happening]
- [0:xx-0:xx] — [what's happening]
(continue through the full track)

## Outro
- **How it ends:** [fade, hard stop, instrumental tail, final hit — be specific about the last 10 seconds]

## Notable Moments
List 3-5 specific timestamps where something musically interesting happens:
- [timestamp] — [what happens and why it's notable]

## Style Prompt Accuracy
Compare what you hear to what was requested in the generation prompt below. Note:
- What the prompt asked for that IS clearly present in the audio
- What the prompt asked for that is NOT present or only weakly present
- Anything notable in the audio that was NOT in the prompt

Style prompt used: "[PASTE STYLE PROMPT]"
Exclude styles requested: "[PASTE EXCLUDES]"
```

### Second Pass — Calibrated Follow-Up (Same Context)

Send this as a follow-up in the same conversation after the first pass:

```
Good analysis. A few areas I'd like you to listen again more carefully for:

1. **Mood/feel vs. heaviness:** How does this track feel — describe what you actually perceive. Heavy instrumentation doesn't predict mood; a heavy song can feel many ways and so can a light one. Don't pick from a suggested list — describe what's there.
2. **Volume/intensity dynamics:** Are there moments where the band gets noticeably quieter or sparser WITHOUT the tempo changing? Describe those shifts.
3. **Bass specifics:** Listen to the bass independently. Is it using any specific techniques — slap/pop, fingerstyle, pick attack, melodic runs independent of guitar? Does it ever take a lead role?
4. **Stereo placement:** Are any instruments panned notably left or right, especially in the intro?
```

### Non-Band-Specific Variant

For songs not part of a band project (solo work, one-offs), replace the opening line:

```
You are analyzing an AI-generated music track for cataloging purposes. Listen to the full track carefully before responding.
```

And adjust the genre note:

```
- Describe the genre or genres you actually hear without assuming a fusion is present. If the track is in a single sub-genre, name that single sub-genre. If you hear multiple genre influences blended together, name them — but do not manufacture a fusion that isn't present in the audio.
```

## Using it in feedback

- Style Prompt Accuracy as a feedback loop: what was prompted against what was heard shows what Suno ignored, misread or added unbidden, and feeds the next adjustment.
- A/B prompt testing: change one variable, generate both, analyze both, compare.
- Per-song measurements (BPM, key, dynamic arc) complement the user's reaction to the track in hand.
