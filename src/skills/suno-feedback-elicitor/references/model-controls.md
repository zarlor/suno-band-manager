# Model Controls

> **Last validated:** September 12, 2026; v6 rows added from the 2026-10-03 research sweep (no model change since launch) — **Suno v6 family (launched 2026-09-09; every earlier model retired)**; the v6 section is PREVIEW guidance. Retired-model notes were validated August 13, 2026 and stay for reading older songbook entries.

Model-level controls, Voices and Custom Models, and per-model feedback patterns. Check these before touching prompt wording — many v6 complaints trace to a control.

## v6 Controls and Symptoms (PREVIEW, 2026-09-12)

Launch-week guidance — compiled from Suno's v6 docs, vendor day-one testing, and community reports; not yet confirmed by this module's production testing. Full context: the suno-style-prompt-builder skill's `references/model-prompt-strategies.md` → "Suno v6 Family."

**Check the new controls before touching the prompt.** Several of the most common v6 complaints trace to a control, not to wording:

| Feedback | First check | Then |
|---|---|---|
| "It changed my style prompt" / "it keeps adding things I removed" | **Variety** above *Exact style* rewrites the style prompt before generating (OFFICIAL). The song page shows the rewritten style — compare it with what was typed (LOCAL-OBSERVED). At the default notch each take gets its own rewrite; prohibitions and vague voice words drop out, while Exclude came through unchanged in 155 of 156 pairs (ANECDOTAL-controlled, 2026-10-03) | Set Variety to *Exact style*, regenerate, and keep negatives in Exclude Styles |
| "The tempo changes didn't happen" | A generation tends to keep one tempo grid (VENDOR, pre-v6). Bare lyric BPM tags didn't move it in one confounded v6 render (LOCAL-OBSERVED, n=1) | Rewrite the contrast as feel over one pulse (half-time/double-time, sparse vs dense), naming each section's scene in identical words in the style map and the lyric cue. Add BPM + feel words in the style field, mirrored in the matching lyric cue, as soft reinforcement. One clean v6 test with all of that still didn't switch, though other v6 takes have switched feel (LOCAL-OBSERVED) — possible, not reliable. One stated BPM, with contrast carried by repeated half-time / double-time / standard-time words, gives it the clearest shot. For a true change: Replace section on that span (song's ⋯ More Actions → Edit → Replace Section, which opens the Create form) with a short style prompt describing only that span at its new tempo, Extend from the boundary with a new style, or splice |
| "Too many backing vocals" / "it doubles everything" | v6 adds doubling and backing without being asked (LOCAL-OBSERVED) — remove any dual/harmony asks first | Then test "backing vocals" in Exclude Styles, changing nothing else |
| "My voice sample sounds grittier than it should" | Grit, gravel or rasp words near the vocal description or the genre head (LOCAL-OBSERVED) | Move the grit onto instrument descriptors and keep the vocal line clean |
| "The prompt is being ignored" / "it came out generic" | **Style Influence** — reportedly defaults to 50 on v6 (VENDOR ×2) | Raise to ~80-90 with Variety at *Exact*; community obedience settings: Variety 0 · Weirdness ~20-50 · SI 80-95 |
| "It sounds like someone else's taste" | **Personalize** on | Turn it off |
| "Great start, falls apart / gets muffled by the end" | Song length and **Max Mode**. Others' descriptions as of 2026-10-03 are in `references/technical-resolution.md` → "Late-song degradation" | Max Mode on when generating (2× credits; applied at generation, so it can't be added to a finished take; field reports are mixed, but this module's own v6 tests found it the difference between usable and unusable takes); a shorter song; extend the back half with v6-mini (ANECDOTAL); Song Editor re-roll of the late section. Late-song degradation is the most-replicated v6 complaint (COMMUNITY). Max Mode mostly doesn't fix it, per many users (2026-10-03); keep it on for adherence, not as a cure |
| "The band disappears under the vocal" / "dead verse" | The style prompt describes a sound, not what each instrument does in each section | Rewrite as instrument-by-section direction ("the riff continues under the verse vocal, palm-muted, never stops"), and restate the key instruction as a short cue at the top of the section in the lyrics |
| "The vocal is buried / muffled" | Arrangement density under the vocal; vocal never placed | Thin the verse arrangement; place the vocal ("in front of the band, close-mic'd, dry, loudest element"). For heavy guitar material, add the mix-relationship block from the suno-style-prompt-builder skill's `references/model-prompt-strategies.md` → "Mix balance for heavy material" (COMMUNITY). If the dullness is there from the first bar, it is the render — regenerate or try v6-wild; adjectives will not add top end |
| "It reads instead of sings" / "rushed, no held notes" | Lyric density and missing delivery direction | Fewer syllables per line; write the holds on the page (`sta-a-ay`); describe the performance in the style field; `[Silence]` at the end of each line has one careful tester's backing (see the metatag reference, v6 section) |
| "Humming / ad-libs at the start" | Unspecified intro | State the intro in positive terms with a bar count ("4-bar guitar intro, instrumental only"), and put `humming, vocal intro` in Exclude Styles — never "no humming" in the style field |
| "It vamps forever" / "it cut off mid-line" | Unspecified ending | State the ending and its length; land the lyric on `[Instrumental Outro]` `[Hard Stop]` `[End]` |
| "Heavy guitars sound synthetic" (metal, high gain) | Genre — the most-reported v6 weakness (COMMUNITY) | Try v6-wild; name the kit and room ("acoustic drum kit in a room"); expect more generations than for lighter genres. Users report Personas and Voices intensify the synthetic timbre in high-gain lanes |
| "The two takes are nothing alike" | Normal on v6 — take-to-take variance can exceed a prompt edit (VENDOR). A measured outside series saw the spread between takes beat the effect of rewording (ANECDOTAL-controlled, 2026-10-03) | Judge both takes before changing anything; change one control per generation. For a one-change test, suggest about 4 takes (two Creates) per variant, and give the reason: in that series the ranking flipped between 2 and 4 takes. How many takes to run is the user's call |
| "The chorus went slow and dramatic" / "it turned into a ballad" (rock, metal) | Feeling words as the chorus instruction: "big", "emotional", "epic". Several users report v6 reads them as "slow everything down and make it dramatic" (COMMUNITY, 2026-10-03) | Where a heavy chorus has to hit, write its job instead: *choruses stay rhythmically driving and hit harder than the verses*. Any "no tempo drop" goes in Exclude Styles, not inline. See the suno-style-prompt-builder skill's `references/model-prompt-strategies.md` → "v6 prompt guidelines" |
| "The band dropped out for the last chorus" / "the final chorus is stripped" | Reported by 4 users in 4 threads as a v6 default after the bridge; prompt and cue wording didn't stop it for them (COMMUNITY, 2026-10-03). Production testing hasn't shown it so far (n=10 full-cued final choruses, none stripped) | On a near-keeper, the one fix offered is to Extend from just before the last chorus and re-roll from there, then use "get full song" (ANECDOTAL, untested here). See the repair ladder in `references/technical-resolution.md` |
| "It changed key out of nowhere" | v6 is reported to add unrequested key changes in some genres, "usually at 3rd verse", and to ignore an inline "no key changes" (ANECDOTAL, n=1) | Where the song has to hold its key, try `key change` in Exclude Styles on the next generation (untested). Leave it alone if the modulation works |
| "The male vocal sounds generic" / "autotuned" (stock voice, no Voice attached) | v6's stock male voices are widely reported as generic or glossy unless steered hard (COMMUNITY, 6+ users, with counter-examples). Stock voices also measured about a semitone lower and darker on v6 (ANECDOTAL-controlled) | Reported fixes (ANECDOTAL): generate the vocal a cappella first, then Cover it with the band (2 users); a detailed vocal description at Weirdness 0, Variety at *Exact style*, Style Influence 100 (1 user). A saved Voice avoids the stock voice altogether |
| "The Voice sounds like someone else" / "it added grit I don't have" (Voice attached) | Vocal character words in the style field that the Voice doesn't naturally have. One user: *"style can influence how they sound"* (ANECDOTAL, 2026-10-03) | Take out character the Voice doesn't have (e.g. "gritty"). Words that reinforce character it *does* have may help push it toward the singer's real sound, so both can be true. Keep range and placement guards |

## Voices & Custom Models

### Voices (User-Uploaded Vocal Identity)

When the user has a Voice active, the Voice provides the vocal identity (timbre, character, tone). Vocal *delivery* adjustments should use **delivery metatags** in the lyrics field, NOT style prompt vocal descriptors.

| Adjustment | Use This (Delivery Metatag) | NOT This (Style Prompt) |
|------------|----------------------------|------------------------|
| Softer delivery | `[Whispered]`, `[Soft]` | "whispered vocals" in style prompt |
| Powerful delivery | `[Belted]`, `[Powerful]` | "powerful singing" in style prompt |
| Emotional delivery | `[Tender]`, `[Yearning]` | "emotional vocals" in style prompt |
| Aggressive delivery | `[Aggressive]`, `[Screamed]` | "aggressive vocal style" in style prompt |

**Audio Influence with Voices — use-case dependent, and voice-dependent.**

The **Persona** slot and the **Voice** slot behave differently: Personas have a narrow 15-25% effective range, Voices run much higher. For a Voice, start around **50%** and move in 5-10% increments against the user's actual complaint.

Community testing puts diminishing returns past ~70%, but treat that as general guidance rather than a ceiling — one profiled voice was clean at 85% where 55% showed artifacts, and Suno's official escalation for "it doesn't sound like me" is to **raise** Audio Influence first, then rebuild the voice profile from a clean acapella. Match the number to the complaint: identity loss argues up, artefacts argue down.

**Full table, official escalation, and the intent-split values live in one place — the suno-style-prompt-builder skill's `references/model-prompt-strategies.md` → "Voices". Read it rather than restating ranges here.**

### Custom Models (User-Trained Production Models)

When the user has a Custom Model active, the model has learned a production DNA from its training catalog. Generic production adjustments (e.g., "polished production," "raw mix") may have little effect because the model defaults to its trained production style.

| Feedback | Standard Approach (May Not Work) | Custom Model Approach |
|----------|----------------------------------|-----------------------|
| "Production is too heavy" | "lighter production" | Name the specific element: "reduce distorted guitar layers, more acoustic presence" |
| "Mix sounds wrong" | "better mix" | Target specifics: "push vocals forward, pull back drum room reverb" |
| "Doesn't sound like my style" | Adjust style prompt broadly | Retrain model with better-curated catalog; use more specific prompt overrides |

**Key principle:** Adjustments need to be MORE specific to override a Custom Model's defaults. Generic descriptors get absorbed by the model's learned tendencies.

### Voice + Custom Model Combined

When both a Voice and a Custom Model are active, change **ONE variable at a time** to isolate what moved. Changing the style prompt, Voice delivery metatags, and Audio Influence simultaneously makes it impossible to determine which change caused the result.

**Isolation sequence:**
1. Adjust delivery metatags first (least disruptive — only changes vocal performance)
2. Then adjust Audio Influence if voice fidelity is the issue
3. Then adjust style prompt if the production/arrangement needs changing
4. Regenerate and evaluate after each single change

## Model-Specific Feedback Patterns

### v6 family (current — PREVIEW)
- **v6** — the control model. Feedback about ignored instructions is usually a control (Variety, Style Influence) or an unspecified section; see "v6 Controls and Symptoms" above.
- **v6-wild** — suggest it when the complaint is flatness, sameness, or a genre v6 renders poorly ("where the old personality went," per several users).
- **v6-mini** — worth trying for performance-heavy lyrics and for extending a degrading back half (ANECDOTAL).
- Model-specific notes below describe retired models; keep them for reading older songbook entries.

### v4 Pro
- Hard 200-character style prompt limit (silently truncated) — all adjustment text must be extremely concise
- Simpler model — broad genre/mood descriptors work better than nuanced ones
- No slider control, no Persona support
- If feedback requires more nuance than 200 chars allow, suggest upgrading to v4.5+ or higher (1,000-char limit)

### v4.5-all (Free Tier)
- Limited vocal control — voice issues are harder to fix without Persona
- Conversational style prompts work — can be more descriptive in adjustments
- No slider control — all adjustments must go through style prompt and exclusions
- Suggest trying different generation seeds (make again) before changing prompt

### v4.5 Pro / v4.5+ Pro
- Same prompting behavior as v4.5-all but with slider access and Persona support
- Slider adjustments available — use them before expanding the style prompt
- v4.5+ Pro offers advanced creation methods — section-level control improves with this model
- Personas can lock vocal direction more reliably than style prompt alone

### v5 Pro
- Better vocal nuance — vocal adjustments are more likely to work
- Crisp descriptors respond better — keep style prompt adjustments concise
- Section-level editing available — can adjust specific parts without regenerating
- Timing fixes: Premier users fix timing in Studio (Warp Markers were the 1.x tool and are not in current Studio 2.0 copy); Pro users use Replace Section or a DAW
- If vocals are the only issue, suggest "Replace Section" or "Add Vocals" before full regeneration
