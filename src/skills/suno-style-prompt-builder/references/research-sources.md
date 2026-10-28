# Research Sources

> Provenance for `references/v6-build-core.md`, `references/model-prompt-strategies.md`, `references/safety-tables.md` and `references/retired-model-strategies.md`. Not read at runtime.

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

## v6 evidence narrative (moved from model-prompt-strategies.md, 2026-10-15)

The every-build rules distilled from this evidence are in `references/v6-build-core.md`; this is the record of where they came from, kept verbatim as of the move. Not read at runtime.

#### Validation history
> **Last validated:** September 12, 2026 (Suno **v6 family** — v6, v6-wild, v6-mini — launched 2026-09-09, when Suno retired every earlier model; the v6 section below is **PREVIEW** guidance). The v6 guidelines and measured outside evidence were added from the 2026-09-23 and 2026-10-03 research sweeps; as of 2026-10-03 Suno had not changed the model since launch. The retired-model prompt strategies (v5.5 Pro, v5 Pro, v4.5-all, v4.5 Pro, v4.5+ Pro, v4 Pro) were last validated August 13, 2026 and live in `references/retired-model-strategies.md` for older records and `:migrate`. Suno updates models and prompt behavior frequently — use web search to verify strategies against current documentation when uncertain.
>
> **Every pre-v6 model is retired (OFFICIAL, 2026-09-09).** "All models prior to v6 have been retired" — they can no longer generate; existing songs stay playable, and any new iteration of an older song (Extend, Cover, Remaster, remix) runs on v6 and may sound different. Custom Models were upgraded to v6 automatically. Suno has published nothing on how Voices and Personas built before v6 carry over. Sources: [v6 FAQ](https://help.suno.com/en/articles/13924481), [Current Models: v6](https://help.suno.com/en/articles/13924737), [What's new in v6](https://help.suno.com/en/articles/13924801).

> **Status: PREVIEW.** v6 launched 2026-09-09 and retired every earlier model. This section is compiled from Suno's v6 help articles, day-one vendor testing, and the first week of community reports. Items graded **LOCAL-OBSERVED** come from this module's own first v6 renders (small samples, one Professional Voice); everything else is still unconfirmed here. Grades: OFFICIAL (Suno-documented), VENDOR (guide sites reporting their own tests), COMMUNITY (several independent users), ANECDOTAL (one report), LOCAL-OBSERVED (this module's own renders, measured). Where this section conflicts with the retired-model findings (here and in `references/retired-model-strategies.md`), it wins for v6; where it is silent, the older findings are hypotheses to re-test on v6, not rules. **Treat anything dated before v6's 2026-09-09 launch — guides, community reports, this file's own retired-model findings — as a mild suggestion at best; v6 was a wholesale change, and pre-v6 evidence should never veto a v6 test.**

#### The three models

| Model | Tier | Suno's framing (OFFICIAL) | When to reach for it |
|---|---|---|---|
| `v6` | Pro/Premier | "reliable, precise"; "stronger control and precision" | The default for any fully specified package |
| `v6-wild` | Pro/Premier | "built for experimentation… less predictable directions" | Exploratory takes. One wild-card route is the *unchanged* primary prompt run here; a rewritten wild-card prompt belongs on v6, with the same sliders. Several users say it carries more of the older models' character; it is the only v6 model reported to render some grooves at all (COMMUNITY) |
| `v6-mini` | All tiers (Free) | "faster, more efficient" | Free-tier work. Some experienced users rate it highly for following performance prompts and for extending a song's back half (ANECDOTAL) |

The style field stays at 1,000 characters and lyrics at 5,000 (VENDOR, day-one test). A generation can run up to 8 minutes (OFFICIAL). A Create still costs 10 credits for two songs; Max Mode doubles it (OFFICIAL).

#### Prompt style: production direction, not a descriptor list

v6 is reported to follow the style field more literally than v5.5 did — "it wants to be directed exactly what to do" — and to fill anything the prompt leaves unspecified with its safest default (COMMUNITY, many reports). A v5-style film-brief list ("big riffs, punchy drums") tends to deliver an intro that matches and then a band that thins out under the vocal. The prompts that work share six habits:

1. **An order:** Genre → Vocals → Drums → Guitars → Bass → Other instruments → Arrangement/Energy → Production → Ending. Several users credit this order with fixing flat choruses. The mechanism is unproven, and the order costs nothing (COMMUNITY).
2. **Each instrument gets a job per section, stated with verbs** — "the intro riff continues under the verse vocal, palm-muted and lower, never stops," not "big riffs." A section the prompt says nothing about is a section where the model drops out (COMMUNITY + VENDOR).
3. **Place the vocal instead of praising it** — "vocal in front of the band, close-mic'd and dry, the loudest element; instruments sit behind and below the voice" beats "crisp, clear, professional mix." Thinning the arrangement under the verse vocal is the most-reported fix for a buried vocal (VENDOR + COMMUNITY).
4. **State both edges, with lengths** — "4-bar guitar intro, instrumental only"; "ends on a hard stop after the final chorus." An unspecified intro tends to come back as humming or ad-libs; an unspecified ending vamps, or cuts off mid-lyric (VENDOR + COMMUNITY). One circulating form: "complete every written lyric before a short instrumental outro and final hard stop."
5. **Positive text only; every negative goes in Exclude Styles.** Inline negation reads as inclusion — the model keeps the noun and drops the "no" (VENDOR ×2 + COMMUNITY). Say what you want instead ("dry, close-mic'd" rather than "no reverb").
6. **A short production clause helps; mastering words don't.** "High-fidelity studio production, close-mic vocals, crisp transients, clear instrument separation" is the reported form (COMMUNITY). "Mastered, radio-ready, -14 LUFS" has no reported effect — master after generation.

Front-loading and the critical zone still apply. The 5-8 descriptor sweet spot was a v5/v5.5 finding: the v6 prompts that work are longer, sentence-shaped, and specific.

#### The Controls panel (formerly More Options)

| Control | What it does | Default for a pipeline-built package |
|---|---|---|
| **Variety** — notches *Exact style*, *Balanced variety*, *Distinct styles*, *Bold exploration*, *Unreasonably varied* | Above *Exact style* it **rewrites the style prompt before generating** — "adjusting and updating your style prompts… reduce the Variety slider to 0" to keep full control of your tags (OFFICIAL). Users who found their style box rewritten traced it here (COMMUNITY). **LOCAL-OBSERVED (2 songs):** the finished song's page shows the rewritten style, not what was typed. The rewrite turned sentences into production-term lists, stripped artist names, turned negatives into positives, dropped mood prose, invented arrangement details, and drifted (warm → raw, grit moved into the genre line, "metal" put at the head). It also appeared to pull terms from the lyric tags. The slider shows shorthand labels (reported: "High" = *Distinct styles*, "Extra" = *Bold exploration*) One vendor's counted test (VENDOR, 2026-10-22): at Off the style text was stored exactly as pasted on 52 of 54 takes, and at Normal all 30 takes of one batch came back rewritten (the two conditions weren't matched; the vendor sells a songwriting app). | **Exact style.** Anything higher means the validated prompt is not what generates. Raise it deliberately to explore — one careful tester found *Bold* better than 0 on a ballad (ANECDOTAL) |
| **Max Mode** | "Uses more compute to maximize consistency throughout the song"; **2× credits**. Suno positions it for songs over two minutes, faithful covers, and style transfer (OFFICIAL) | **On for any generation you might keep** — it's applied at generation, so a finished take can't be upgraded to Max. Off only for throwaway style-feel sketches. Field report from this module's own v6 testing: Max was the difference between usable and unusable takes. Community reports on whether it fixes late-song degradation are mixed |
| **Personalize** | Applies the account's My Taste profile | **Off** — keeps the package reproducible across accounts |
| **Duration** | Auto, or a Custom target from 0:10 to 6:00 | **Auto** unless the length is a real requirement (see "Duration Slider"). **LOCAL-OBSERVED:** on short lyric sheets Auto pads the ending with a long instrumental tail — about a minute on one song, even with `[Hard Stop][End]` and no outro tag; 47 s on another with an outro tag. Auto stays the default. Custom is the lever when a take runs long: set it to about the sung length plus 15–20 s. An exact target can also sound forced on a sung track — the vocal rushing in, or the ending stretched (ANECDOTAL) — another reason Auto stays the default |
| **Style Influence** | Loose ↔ Strong prompt adherence (OFFICIAL) | Reported to **default to 50** on v6 (VENDOR ×2) — check it before judging a prompt. Community settings for obedience converge on **Variety 0 · Weirdness ~20-50 · Style Influence 80-95** (COMMUNITY, 4+ reports) |
| **Weirdness** | Safe ↔ Chaos, 50 = normal (OFFICIAL) | Chosen per song as always. The 60-75 counter-genre range and the ~80 cliff in the Slider Guidelines were v5.5 findings, untested on v6 |
| **Audio Influence** | Appears only with audio attached — upload, Voice, or Persona (OFFICIAL) | Re-profile per voice on v6 rather than carrying a v5.5 number over |

#### Tempo and section contrast (PREVIEW)

- **A generation tends to keep one tempo grid.** "Suno doesn't reliably support tempo changes within a single generation" (VENDOR, **pre-v6**). **LOCAL-OBSERVED, one render:** a song whose lyric tags asked for 65 → 150 → 65 → 150 → 85 BPM came back on one flat grid. That render had no feel language, and Variety was rewriting its style prompt at the time, so it's a hint, not a finding. **LOCAL-OBSERVED, clean test:** the same song rebuilt with Variety Off, Max Mode on, and BPM + feel figures and scene names word for word in both fields got its dynamics (the chorus lifted), but the fast verse never went double-time on that take. Other v6 generations *have* switched between half-time and double-time (owner report), so a feel switch is possible but unreliable. Make it as easy as you can: one stated BPM for the whole song, with the contrast carried by repeated half-time / double-time / standard-time feel words tied to drum jobs. Treat an edit or a splice as the fallback.
- **Write the contrast as feel over one pulse.** Use half-time vs double-time drum feel, sparse vs dense arrangement, and each instrument's job per section ("a 140 BPM track can feel closer to 70", VENDOR, pre-v6). **LOCAL-OBSERVED:** reframing the same song this way was heard as "a LOT better", with some of the section changes landing.
- **BPM is soft conditioning — pair every number with feel words,** e.g. "72 BPM feel with a slow heavy backbeat and double-time hi-hat grid" (COMMUNITY compiled v6 guide: "BPM is a hint, not a transport control"). A bare number is often ignored. The same guide treats bracket tags as soft conditioning too, so mirroring the style field's BPM figures in the matching lyric cues is a reasonable reinforcement to test.
- **Reinforce with the same words in both fields, and name the scene.** The style prompt's section map and the lyric section cues should use identical phrases, and each phrase should say what the section *is* as well as how it moves: "closing time, the harbor wakes up: fast driving double-time build" rather than "fast section". v6 reads plain language and resolves contradictions between the fields by thinning the band (VENDOR + COMMUNITY). The payoff of naming the scene is under test here.

#### Mood from the prompt (was under Mix balance)

- **v6 takes mood from the prompt, not the lyrics** (COMMUNITY, 2+ reports: it "no longer improvises based on the emotional tone and imagery of the lyrics"). State the emotional direction explicitly — in the style field and in the section cues — instead of relying on the lyric to set it.

#### v6 prompt guidelines from production testing and the 2026-09 / 2026-10 research sweeps

These are **guidelines, not laws**. Each carries its scope and its evidence grade. Some are just things to try: Suno doesn't always do what a prompt asks, so a song sometimes needs more than one way of asking. A song that wants otherwise wins.

**Use generally** (2026-09-23; each still gives way when a song wants otherwise):
1. **Describe the band's part instead of song-wide gravity words.** `heavy`, `doom`, `crushing`, `massive`, `oppressive`, `screaming`, `epic`, `cinematic` and `industrial` are reported to pull stock conventions (COMMUNITY). In production testing, songs with song-wide escalation words measured the vocal under the band. The one song that put weight only on specific moments had the vocal above it (LOCAL-OBSERVED, small n). Say what the instruments do, and put the weight on moments. Keep a gravity word when the song wants that pull.
2. **Choose the era anchor for its production.** The decade word brings its production habits with it. One report: `80s hair metal` brought a gated snare that `70s hard rock` didn't (ANECDOTAL). Where the guitar sound matters, name the amp or the tone character rather than "distortion". Equipment and room words (a named mic, a vintage compressor) are reported to work the same way (ANECDOTAL ×3, "only a hypothesis").

**Only where the song calls for it:**
3. **A band-side vocal-space clause** when the vocal needs to get in front, e.g. *rhythm guitars leave midrange space for the lead vocal* (2026-09-23). A second option (2026-10-03) is *the band builds beneath the vocal without obscuring it*. It adapts phrasing from Suno's own caption writer (VENDOR-relayed) and is untested on songs. So far in production testing, no song-wide phrase has lifted the vocal by itself; the arrangement decides.
4. **An ending written as the singer's action plus the band leaving**, with no instrumental figure at the close (2026-09-23). Use it for songs that call for the band leaving, or that need to avoid a long instrumental tail, not for every ending. In the first test (n=1) it shaped the last line, but a 24 s instrumental tail still followed and was the song's energy peak. So far it steers the line, not the tail.
5. **Check the style field for a bare "vocal"** when a wordless "ooooh" intro would hurt (n=1 report). Open the lyrics on a lyric line when no long intro is wanted (2026-09-23).
6. **Write a heavy chorus's job, not its feeling** (2026-10-03), e.g. *choruses stay rhythmically driving and hit harder than the verses*. Avoid "big", "emotional" or "epic" as the chorus instruction. Several rock and metal users report those words read as "slow everything down and make it dramatic", turning the chorus into a ballad (COMMUNITY). This extends guideline 1.
7. **`key change` in Exclude Styles when the song has to hold its key** (2026-10-03). v6 is reported to insert unrequested key changes in some genres, "usually at 3rd verse", and to ignore an inline "no key changes" (ANECDOTAL, n=1). A late modulation also turned up in a heavy lane in production testing, so "never for metal" isn't absolute. Untested. Leave it out where a modulation would be welcome. For a *requested* change, "key change" alone is often ignored; putting it inside a labelled section is the vendor advice (VENDOR, generic, untested).
8. **With a Voice attached, don't add vocal character the Voice doesn't naturally have** (e.g. "gritty") (2026-10-03). One outside user: *"remove anything that talks about your singer in styles, since style can influence how they sound"* (ANECDOTAL). This matches production testing, where grit and genre words pulled texture onto a Voice (see "Voices on v6"). Both things can be true, though. Words that reinforce character the Voice *does* have may help push it toward the singer's real sound when needed. Range and placement guards stay.

**A thing to try:**
9. **Carry "unresolved" as harmony, not as a mood** (2026-10-03), e.g. *ends off the home chord*. Keep emotion tags off a section meant to be bare. In production testing (n=1), a section tag reading "unresolved tension" on a final verse meant to be bare came out as the loudest section of the song: the mood word seems to have been read as intensity. Outside rule sets warn that "powerful, intense, bigger" may raise loudness (ANECDOTAL). Inference, untested. The lyric side (no emotion word in a bare section's tag) is the `suno-lyric-transformer` skill's job.

**Measured outside evidence that bears on prompting** (2026-10-03 sweep; one note.com author with stems, pitch tracking and ≥4 takes per condition. ANECDOTAL-controlled, one channel, stock voices, Variety left at its default):
- **Style Influence 100 tested no better than 85.** 6 of 12 vs 7 of 12 takes followed the instruction. An early 4-vs-4 had pointed the other way. This fits "Style Influence above ~80 plateaus" (see "Slider Guidelines"). One untested claim says the opposite (ANECDOTAL).
- **Variety above Exact style rewrites each take differently.** The two takes of one submission showed the same style text in 4% of pairs on v6, against 100% on v5.5. Prohibitions and vague voice words dropped out ("no 16th cutting" 0 of 12; "moderately bright", "mature and elegant" 0 of 4). Concrete words survived ("warm clear", "behind the beat", 4 of 4). **Exclude came through unchanged in 155 of 156 pairs.** The author's hedge: whether the displayed text is what generated is unknown. This adds to the reasons for Variety at Exact style and for putting every negative in Exclude Styles.
- **Level matters more than brightness.** "Moderately bright" in the style didn't brighten the vocal. The vocal sat about 2 dB further under the band on v6 than on v5.5, which matches production-testing readings.
- **Take-to-take spread was bigger than the effect of rewording,** and the ranking of variants flipped between 2 and 4 takes (see "Iteration Best Practices").

#### First-Genre Dominance — Quantifying the Anchor

Community research is sharper than "first matters": **genre and subgenre tags collectively determine ~60-70% of arrangement output, with the first-position term holding the strongest single signal** (HookGenius 1000+ prompt analysis, 2026). A three- or four-genre fusion prompt is not a balanced stew. It's a dominant anchor in position one with increasingly faint color pulls from each subsequent term.

**Why this matters for counter-genre work:** When you're trying to push against a genre's gravity — accessible textures inside a heavy lane, slow pace inside a driving lane, acoustic framing under an electric identity — the counter-target genre has to occupy position one. Burying it at position 3 or 4 gives the counter-lane negligible arrangement influence, and Suno defaults to the first-position genre's conventions.

**Example:** `progressive metal, heartland rock, acoustic singer-songwriter` will read as progressive metal with trace heartland influence — the acoustic anchor contributes almost nothing. To actually produce an acoustic-leaning track, the compound must open `acoustic singer-songwriter, ...` with metal and heartland demoted behind it.

**Practical rule:** If you want genre X to drive the arrangement, X is position one. "Accents" / "undertones" / "influences" demote later terms but don't promote earlier ones — there is no way to get a buried genre to lead.
