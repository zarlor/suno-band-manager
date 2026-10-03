# Research Sources

> Provenance for `references/model-prompt-strategies.md`, `references/safety-tables.md` and `references/retired-model-strategies.md`. Not read at runtime.

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
