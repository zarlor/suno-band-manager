# Research Sources

> Provenance and evidence narrative for the maps, `technical-resolution.md`, `gemini-audio-analysis.md` and `audio-analysis-scripts.md`. Not read at runtime: the facts themselves live in those files.

## Validation dates

- Parameter mappings re-checked against the 2026-08-13 platform sweep (v5.5, v5, v4.5-all — retired since the v6 family launched 2026-09-09). Elicitation techniques are craft-based and need no re-validation; descriptor mappings should be re-checked by web search when Suno behavior changes.
- v6 controls and symptoms compiled 2026-09-12 from Suno's v6 docs, vendor day-one testing and community reports; v6 rows added from the 2026-10-03 research sweep (no model change since launch).
- Studio 2.0 and the Song Editor validated 2026-08-13 (Replace Section at Pro re-confirmed official that day, no deprecation announced); download cap from 2026-09-03; v6 repair ladder and late-song reports from the 2026-10-03 sweep.
- Duration slider: shipped 2026-07-20 ([release note](https://suno.com/release-notes/duration-slider-on-web)); range 0:10–6:00 verified in the live UI on a Pro account 2026-08-14; the 5-second granularity is COMMUNITY-attested only. Suno published no range. Adherence reports are starkly split (a controlled batch 4 of 40, others near-perfect); an earlier account described silence padding where primary sources describe end-then-restart.
- Suno's EQ post (OFFICIAL, 2026-09-29, Studio) for the muddy-vocal mix fix.
- Replace Section seams: this module's production test, 2026-04-29.

## Evidence narrative

- **Style Influence plateau:** Style Influence 100 vs 85 on v6 — 6 of 12 vs 7 of 12 takes followed the instruction (ANECDOTAL-controlled, one outside channel, 2026-10-03).
- **Take variance and off-tempo takes:** an outside series of 24 takes of one song: the spread between takes beat the effect of rewording; the ranking flipped between 2 and 4 takes; every take's page said "99 bpm" including takes at 117; every off-tempo take had also dropped a requested instrument; the misses ran 13–24% fast, not double (ANECDOTAL-controlled, n=24).
- **Late-song degradation:** 15+ community threads; "like switching from stereo to mono" (4 users), steps "every 30 seconds" (several; the "chunked decoding" explanation is unverified), "20% from start to finish" level rise (1 user). Max Mode helped for 2 users. Extend from the last clean point: 3+ users.
- **Final chorus stripped:** 4 users in 4 threads (2026-10-03); production testing n=10 full-cued final choruses, none stripped.
- **Key change:** one report, "usually at 3rd verse".
- **librosa slow-prior reading:** on a 34-track reference catalog with ear-verified tempos, the default read 10 on the felt tempo and 14 double; the 80-BPM start read 17 on it and 1 double, but halved 4 fast songs.
- **Beat This! second opinion:** on an 83-track reference catalog it matched the human-verified felt BPM on 9 of 15 tracks, against librosa's 7, and fixed most slow-song halftime double-reads.
- **librosa misreads:** ~19% of a 31-track catalog had significant BPM misreads.
- **Gemini temperature A/B** (same brass-metal fusion track, blind prompts): at 0.5 — genre "progressive metal, ska-core, hard rock, swing/jazz, dark cabaret" (best from any LLM), brass correctly detected blind, verse dropouts captured, bass "punchy, metallic, pick-driven, walking lines", BPM ~145 (closer to librosa's 184.6 half-time). At 0.3 with the style prompt and a calibrated follow-up — genre "manic carnival-punk, ska-core, funk-metal", brass read as ska-punk, bass hallucinated as "slap/pop funk-metal" (likely primed by "NOLA funk groove" in the prompt), BPM ~165 (the same as a different track). Gaps at both: the a cappella moment, vocal yell, triple snare strike and final brass blast at the end were missed; 0.5 said full band at 0:00 when the first 10 seconds were brass only; a bass-specific follow-up at 0.5 produced "slap and pop, lead melodic role" when the bass was hidden behind guitar and tubas.
- **ChatGPT blind analysis:** on a southern rock / blues track it correctly heard "southern rock / blues rock with fingerstyle bass" where Gemini, shown the style prompt, heard "funk-metal party groove with slap/pop bass"; on a brass-metal fusion track it described "alternative rock, indie, hip-hop groove, synth pads" with no brass or metal and 94 BPM on a 184 BPM track. Possible causes: free-tier upload handling, track complexity, length or encoding. Its BPM estimates are rough (a 120–125 range against librosa's 123.0).
- **Gemini two-pass example:** first pass "NWOBHM speed metal, zero funk, bass follows guitar"; follow-up "funk-metal party groove, standout slap bass, Les Claypool comparison" — same audio. Prompt templates refined across 30+ song analyses.
- **Gemini atmospheric hallucination:** a "very prominent brass section" reported on a track with no brass — reverb tails on vocals and guitars from an atmospheric production stack.

## Sources

[Suno 4.5 Plus Extend — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-45-plus-extend-tool) | [Outro Prompts — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-outro-prompt-guide) | [End Prompts — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-end-prompt-guide) | [Fade Out Prompts — Jack Righteous](https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/suno-ai-fade-out-prompt-guide)

Goal-keyed slider recipes (clean/predictable, strong genre, stable hook with variation, adventurous bridge, uploaded-melody-leads, upload-as-loose-inspiration): ANECDOTAL, single source, updated 2026-08; held by the style prompt builder.
