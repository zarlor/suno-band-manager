# Decision Log — suno-feedback-elicitor

## 2026-08-14 — Agent-shape removal (BMB simple-workflow standard) + Suno reference refresh

**Agent-shape:** Dropped the `## Identity` / `## Communication Style` / `## Principles` persona scaffolding, applying the same ruling the sibling `suno-style-prompt-builder` recorded on 2026-06-17 — a simple-workflow skill should not carry agent constructs. The `prepass-workflow-integrity.py` scanner classifies this skill as `simple-workflow`, so the triad was the last agent-shaped surface left in it.

Everything load-bearing was folded into the Overview as **Design rationale (load-bearing constraints)**, not cut:
- The six Principles moved across intact (feedback-always-valid, triage-before-elicitation, minimum-viable-context, prompt-changes-before-regeneration, preserve-what-works, round-awareness).
- From Communication Style, two items were kept because they are domain mechanics rather than tone: **mirror the user's vocabulary** (renaming the user's term breaks the vocabulary bridge this skill exists to build) and **conversational not clinical** (the no-1-10-rating-scales guard — BMB's own quality principles reject scoring formulas for subjective judgment). The plain-language-with-technical-term-parenthetically contract moved into the Overview's role sentence.
- The Identity paragraph became the Overview's `Act as ...` role clause, per the BMB standard-fields "Role Guidance Format".
- Dropped as LLM-native: "warm, collaborative, never judgmental" (implied by feedback-always-valid) and "celebrate what works before addressing what doesn't" (already operationalized in Step 4b, "Lead with the win, not a manufactured problem").

**Section order:** Moved `## Overview` above `## Conventions` to match the BMB SKILL template, which puts Overview first as the primary help output for the skill.

Net effect: 264 → 253 lines, no functional content removed. `prepass-workflow-integrity.py` still reports `status: pass`; section inventory 23 → 20 (the three dropped scaffolding headers), with `Overview` now the first section.

**Suno reference refresh (same pass).** Factual corrections from the 2026-08-13/14 research sweep: Studio is Premier-only (was "Studio features require Pro/Premier"); Studio 1.x tool names routed to outcomes, with Take Lanes and comping kept as current since they survived the 2.0 overhaul; stems described as Auto Split with its credit cost; Song Editor naming plus the local audible-seams caveat on Replace Section; within-track degradation past ~2 minutes; softened Weirdness ceiling and ending-tag promise; character-limit provenance; and a stale cross-reference to a renamed section in `references/suno-parameter-map.md`.

## 2026-06-17 — Quality analysis

Grade: Good. Interactive HTML: `.analysis/20260617-184244/quality-report.html`. Full markdown: `.analysis/20260617-184244/quality-report.md`.
Run via `bmad-workflow-builder` analyze (5-skill suno-workflow sweep; agent excluded). 4 LLM scanners + 5 lint/prepass scripts per skill.

## 2026-06-17 — Quality-analysis fix-pass (v2 standard)

Resolved the quality-report findings, bringing the skill to the current Module Builder (v2) bar. Both scanners now clean on live files: path-standards 0 live findings (was 14: 13 `./` in SKILL.md + 1 `../` in suno-parameter-map.md), scan-scripts `pass` / 0 findings (was `fail`, 14 findings). All script tests pass (57 across 10 test files).

**Path hygiene (Theme 1).** Stripped every leading `./` from SKILL.md internal references; replaced the fragile `../../suno-agent-band-manager/...` markdown link in `suno-parameter-map.md:455` with a stable plain-text pointer (cross-skill, can't use a bare skill-root path); fixed `./gemini-audio-analysis.md` → bare path in the (unrouted) playlist-sequencing-methodology doc; stamped the canonical four-bullet `## Conventions` block.

**Customization opt-in (minimal).** Added `customize.toml` with a `[workflow]` block only (`activation_steps_prepend = []`, `activation_steps_append = []`, `persistent_facts = ["file:{project-root}/**/project-context.md"]`) — no scalars, no toggles. Added the resolver step as the first On-Activation step with the base→team→user read-three-files fallback. The Identity/Communication/Principles triad was deliberately NOT lifted into `[workflow]` (module house style; would make the workflow want to be an agent).

**Headless seam (Themes 2/3).** `headless-contract.md` now carries a flag→JSON mapping table (`--feedback`→`feedback_text`, `--style-prompt`→`original_style_prompt`, `--model`→`model`, `--sliders`→`slider_settings`, …) and states the LLM is the translation layer; output schema gained top-level `status` (complete|blocked), `reason`, and `decision_log[]`. `map-adjustments.py` now accepts `--style-prompt`/`--model` (and reads `original_style_prompt`/`model` from input JSON), emitting a `style_prompt_overflow` warning keyed to `STYLE_PROMPT_LIMITS[model]` from `_shared` (v4 Pro = 200, else 1000) — closes the "model-specific full-prompt length validation asserted but not scripted" determinism leak. `_shared` untouched (constant imported, not edited). README example model fixed `v5-pro` → `"v5 Pro"`.

**Iteration log as Decision-Log Workspace (Theme 4).** The log is now the living spine: Step 2 surfaces/resumes any prior log for this song/band before re-asking; Step 1 writes from round 1 (what was tried + the reaction); the 4c compaction checkpoint is generalized to the 4d (long contradictory rebuild) and 4e (multi-attempt technical) branches; Step 5 effectiveness check reads the log to avoid re-recommending failed moves; Step 7 turned into the handoff log audit.

**UX express lanes / dead-ends (Theme 5).** Step 4b leads a satisfied user with celebration + profile-bank offer (no manufactured "change one thing"); the Priority-1 ask surfaces the reconstruct-from-description fallback to the USER (not just the agent); Step 2 has a one-line express path when the opening already supplied prompt+model; an instrumental skip cue (Step 2 + triage-guide dimension checklist) keeps the agent from burning a turn confirming no vocals.

**Script hygiene (Theme 6).** `audio-files-manifest.py` + `verify-audio-files.py` already had PEP 723 blocks but used the plain `python3` shebang and `pip install pyyaml` error text → switched to the `uv run --script` shebang and PEP-723/uv guidance; added `sys.exit(0)` to the manifest script's success path. Added `sys.exit(0/1/2)` + missing-input guards to `analyze-audio.py`, `audio-deep-analysis.py`, `chord-progression.py`, `tempo-detail.py`. Added per-script unit tests for all eight previously-untested scripts (full functional tests for the manifest pair; exit-code contract tests via `uv run` for the librosa single-song scripts; minimal smoke tests for the album/playlist scripts pending extraction).

**SCOPE-CREEP RECOMMENDATION (carried forward — NOT actioned here per project decision).** The album/catalog/playlist apparatus — `playlist-sequencing-methodology.md` (orphan), the album-level scripts `batch-full-analysis.py` + `playlist-sequencing-data.py`, and their librosa stack — is off-mission for a single-song feedback skill (~13k tokens). It was left physically in place but UNROUTED (no playlist front-door added; no move to the Band Manager agent). Recommendation: EXTRACT this apparatus into a future dedicated `suno-playlist-sequencer` workflow so agents stay lean and each workflow owns one job. `gemini-audio-analysis.md` was KEPT and stays routed — it is used for single-song deep technical analysis (Step 4e), not just album work. Do not entrench the album apparatus further pending extraction; the smoke tests added for the two album scripts give that future move a known-good baseline.

## 2026-06-18 — Quality analysis (post-v2-remediation re-run)

Grade: Good. HTML: `.analysis/20260618-091127/quality-report.html`, markdown: `.analysis/20260618-091127/quality-report.md`.

## 2026-06-18 — Remaining-opportunities fix-pass

Resolved the outstanding quality-analysis opportunities (high → medium → low). Both scanners clean on live skill content (path-standards: 0 live findings — all 250 raw hits are inside `.analysis/` scanner output + `.decision-log.md` prose, none in SKILL.md / references / scripts / customize.toml; scan-scripts: `pass`, 0 findings, 8/8 scripts tested). All 8 manual-runner test files pass (55 tests, every file exit 0).

**OPP-high — Finish album/playlist extraction (RESOLVED).** `gemini-audio-analysis.md`: deleted the live `## Playlist Sequencing` → Methodology / Sequencing Principles body (album-craft methodology, Camelot harmonic-mixing table, BPM-priority rules, the LV Mirror-Image placement case study, W-Shape setlist model — ~50 lines) that sat ABOVE its own "moved to suno-playlist-sequencer" stub. Kept the single-track `chord-progression.py` subsection (promoted to its own `## Single-Track Harmonic Scripts` heading) and collapsed the trailing stub to one routing line. No duplicated album methodology can now reach a Step-4e single-song load. Also: trimmed the "Integration with Feedback Elicitor" playlist-ordering bullet (`gemini` line ~242) to per-song framing with a routing aside; reframed the file-top "Post-publish pipeline" pointer (`gemini` line 3) to single-song scope. (The SKILL.md:242 / line-~3 callouts in the brief were `gemini-audio-analysis.md` line refs — SKILL.md had no live playlist methodology, only the already-correct `## Album/playlist scope` routing note.)

**OPP-medium — DLW names folder but not file (RESOLVED).** SKILL.md Step 1 now states the file convention: `docs/feedback-history/{band-or-session}/{song-slug}.md`, slug = title kebab-cased (or `YYYYMMDD-HHMM` session timestamp when band/song unnamed), one dated `## Round {n}` heading per round. Step 2 resume check made concrete (derive slug, check whether that file exists, surface + resume; fuzzy-title → scan the band folder). Step 7 audit + `output-template.md` "Iteration Log" block aligned to the same path; clarified the template JSON line is the per-round snapshot embedded under the round heading (= headless `iteration_log` payload). **`iteration-log.py --find/--append` helper: SKIPPED as future** — slug derivation, find-by-path, round-numbering, and markdown append are all things the LLM does correctly unprompted (skill-quality "would the model do this without being told?" bar); a script would add test/maintenance surface for pure plumbing. Noted here, not built.

**OPP-medium — Latent contract ambiguities (RESOLVED).** SKILL.md:49 `--headless:adjustments` line now states it runs triage internally if `feedback_type`/`dimensions` are absent and trusts+skips re-triage when present. SKILL.md Step 5 effectiveness-tracking reconciled to the pinned band-profile data contract: writes BOTH — `generation_history` (per-round settings+reaction snapshot, every round) and `generation_learnings` (durable cross-song pattern, only when one round generalizes). Step 7 band-profile-update line attributes the systematic-preference write to `generation_learnings` and notes the per-round `generation_history` write happens regardless. profile-schema.md left untouched (band-profile owns it).

**OPP-low — Vague/express conversational edges (RESOLVED).** SKILL.md:130 maximally-vague shortcut widened to "a song, an artist, a movie scene, or even just a feeling" (surfacing the feedback-triage-guide.md "don't require musical knowledge" forgiveness). Express path (SKILL.md:84) loosened to the style prompt alone — model deferred to a single inline ask at Step 5 only when overflow validation needs the char limit AND the adjusted prompt is near it; lyrics likewise on-demand. Intent check (SKILL.md:61) now asks one disambiguating question when refine-vs-build is ambiguous (not clearly out of scope) before redirecting.

**audio-files-manifest.py / verify-audio-files.py:** KEPT in this skill this pass per pinned decision (they support single-song multi-version audio intake). No future-relocation flag raised — they read as in-scope for a single-song workflow that ingests multiple takes.

Files touched: `SKILL.md`, `references/gemini-audio-analysis.md`, `references/output-template.md`.

