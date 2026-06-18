# Decision Log — suno-style-prompt-builder

## 2026-06-17 — v2-standard fix-pass (quality-analysis findings)

Brought the skill to BMad Module Builder v2 standard by resolving all quality-report findings.

- **Paths + Conventions:** Stripped the `./` prefix from all 5 internal references in SKILL.md (4× `references/model-prompt-strategies.md`, 1× `scripts/validate-prompt.py`). Added the canonical 4-line `## Conventions` block near the top. Re-scan: SKILL.md `cross-dir-dot-slash` findings 5 → 0.
- **Agent-shape:** Dropped the `## Identity` / `## Communication Style` / `## Principles` persona scaffolding (a simple-workflow skill should not carry agent constructs). Folded the load-bearing DOMAIN principles — decompose-don't-name-drop, web-search-before-fabricating, frame-positively, less-exclusion-is-more, capture-don't-interrupt, full-package rationale — into the Overview's "Design rationale (load-bearing constraints)". The soft-gate / show-decomposition choreography was dropped as LLM-native / already in the workflow body.
- **Compaction survival (HARD RULE):** Added an On-Activation-adjacent `## Compaction Survival` section requiring a reload of `references/model-prompt-strategies.md` before EVERY build and EVERY refine, since all scream/dangerous-word/genre safety tables live only there (~19k tokens) and a long refine loop can compact them away. Reinforced at Step 2, Step 5 refinement, and the headless generate path.
- **Determinism → script (shared constants):** Extended `_shared/suno_constants.py` (ADD-only; existing names unchanged) with `HEAVY_VOCAL_TRIGGERS`, `VOCAL_SAFE_PAIRINGS`, `KEYBOARD_PULL_WORDS`, `SHOUT_TRIGGER_CHAR`, and a fuller `GENRE_SIGNALS` set (now covers swamp metal, heartland/southern rock, prog rock, slowcore, doom, etc. — fixes false "no genre keyword" trips). `validate-prompt.py` now imports `GENRE_SIGNALS` (replacing the inline literal at the old line 101) and adds a `detect_triggers()` pass emitting a `trigger` category: unpaired heavy-vocal scream triggers (high, word-boundary matched, cleared by a positive vocal pairing), keyboard-pull words (medium), and `!` (low). Detection is deterministic; the SUBSTITUTION decision stays with the LLM. Version 1.1.0 → 1.2.0.
- **Headless contract:** Defined the success JSON (`status: complete|blocked`, `style_prompt`, `exclusion_prompt`, `sliders`, optional `wild_card`, `validation`) and a `decisions[]` audit array logging each non-obvious call (dangerous-word substitution, genre demotion, slider choice, skipped decomposition confirmation). Re-shaped the `:refine` input to accept the sibling Feedback Elicitor's `adjustment_recommendations` shape (style_prompt/exclusions/sliders/model deltas; `reorder_notes` free-text rather than `reorder: string[]`), with the legacy adjustments shape kept for back-compat.
- **UX + fail-fast:** Step 1 now opens with an open-floor invitation, signposts build-vs-refine (hands refine intents toward the Feedback Elicitor), and short-circuits for experts who supply model+direction+creativity up front. Step 5 inverted to run `validate-prompt.py` FIRST and feed its JSON back, with the LLM self-review rescoped to only what the script can't do (genre-term appropriateness, dangerous-word semantics, decomposition fidelity, intent alignment).
- **Customization:** Added a minimal `customize.toml` `[workflow]` block (`activation_steps_prepend = []`, `activation_steps_append = []`, `persistent_facts = ["file:{project-root}/**/project-context.md"]`) and a resolver step as On-Activation step 1.
- **Tests:** Added trigger-detection + expanded-genre tests to `scripts/tests/test-validate-prompt.py` (35 pass) and shared-constant table tests to `_shared/tests/test-suno-constants.py` (23 pass). All six sibling scripts importing `suno_constants` still load cleanly. `scan-scripts.py` passes; `scan-path-standards.py` SKILL.md findings resolved (remaining hits are `.analysis/` workspace files + the canonical `.decision-log.md`, both out of scope).

**Note on `_shared/suno_constants.py`:** This fix-pass added the trigger tables and `GENRE_SIGNALS` to the shared module. ADD-only — no existing constant was renamed or changed, so sibling imports (feedback-elicitor, lyric-transformer, band-profile-manager) are unaffected.

## 2026-06-17 — Quality analysis

Grade: Good. Interactive HTML: `.analysis/20260617-184244/quality-report.html`. Full markdown: `.analysis/20260617-184244/quality-report.md`.
Run via `bmad-workflow-builder` analyze (5-skill suno-workflow sweep; agent excluded). 4 LLM scanners + 5 lint/prepass scripts per skill.

## 2026-06-18 — Quality analysis (post-v2-remediation re-run)

Grade: Good. HTML: `.analysis/20260618-091127/quality-report.html`, markdown: `.analysis/20260618-091127/quality-report.md`.

## 2026-06-18 — Remaining quality-opportunity fix-pass (high→medium→low)

Resolved the remaining quality-analysis opportunities for `suno-style-prompt-builder`. Edits confined to `suno-style-prompt-builder/` and `_shared/suno_constants.py` (+ `_shared/tests`). Not committed.

**OPP-high — Slider anti-anchoring discipline (resolved):**
- SKILL.md Compaction-Survival enumeration now lists the Slider Guidelines table + per-song anti-anchoring rule (choose fresh each song; never anchor to a profile's stored `sliders:` or to similar catalog songs; bare-Demo fallback is the one exception) as load-bearing knowledge that must survive a reload.
- Step 3's hardcoded bare slider ranges (Weirdness 20-35/40-60/65-85, SI 65-80/40-60/20-40) replaced with a pointer to the reference table + the anti-anchoring rule + the documented failure mode + the single Demo exception. (Audio Influence ~25%-for-Personas note retained.)
- Headless generate path: added a clause requiring the same discipline and `decisions[]` logging of chosen values + behavioral reasoning; marked user-supplied sliders authoritative.
- Expert quick-win short-circuit: user-supplied slider values are authoritative (don't re-derive).
- Demo-mode slider exception now visible in the SKILL body (Step 3 + Compaction Survival).

**OPP-high — Instrumental songs (resolved):** Added an instrumental detection clause in Step 1 and a short instrumental branch in Step 2 — drops all vocal direction, skips the Vocal-Gender recommendation (Step 3) and Lyrics Mode → Instrumental, suppresses scream-trigger *pairing* prompts (no vocals to protect; validator's unpaired-heavy `trigger` is a non-issue, note-as-handled), notes `[Instrumental]`, and redirects the critical-zone budget to arrangement/texture/dynamics. (Field `instrumental: true` already flows from the band profile; the builder previously ignored it.)

**OPP-medium — Reference decay + shared-constant reconcile (resolved):**
- `model-prompt-strategies.md` Universal Rules renumbered contiguously 1-19 (was 1-16 then a duplicate 13/14/15). Fixed rule 14's "see Dangerous Words above" → "table below" stale cross-ref.
- Consolidated the duplicated Voices/Custom-Model interaction subsections (`## Persona Style Prompt Integration`) into a cross-reference to the v5.5 Pro section, **preserving** the genuinely-unique Custom-Model prompt-strategy-shift / optimal-formula / what-becomes-redundant content. Persona-specific guidelines kept (distinct from Voices).
- **`_shared/suno_constants.py` (ADD/reconcile only; no existing name renamed):** Removed `"orchestral"` and `"cinematic"` from `GENRE_SIGNALS` — they overlapped with `KEYBOARD_PULL_WORDS`, creating a self-contradicting validator signal (a word that both satisfied front-loading AND flagged as a dangerous keyboard pull). **Decision: cinematic/orchestral/baroque/rock-opera are texture/production modifiers, not genres.** The two sets are now disjoint (guarded by a new `_shared` test). Applied consistently: `GENRE_SIGNALS` (constant), `validate-prompt.py` fix-text (now names `rock opera`), and the reference (rule 14 reworded "texture modifier, not a genre"; SKILL.md Step 2 keyboard-pull block added). "rock opera" now surfaced consistently across script constant, validator fix-text, reference table, and SKILL.md (previously only in the script constant).

**OPP-medium — Validation coverage + standalone seams (resolved):**
- Wired the existing validator into the headless migrate/refine emit path (reuse `validate-prompt.py --model {target}`; no new script) — migrate/refine produce a new prompt against a possibly-new model budget, so the Step-5 fail-fast check now applies there too, folded into the `validation` field.
- Added a Step 1 clause exposing the in-skill `:refine`/`:migrate` machinery to the standalone (no-agent/Mac) user, so they aren't forced toward the Feedback Elicitor when it isn't present.
- Added a minimal `.style-prompt-ledger.md` scratch ledger (vN | prompt/key-change | changed variable, append-per-version) so the end-of-session version summary survives compaction. Explicitly NOT a Decision-Log Workspace (one line per version).

**Skipped (genuinely optional):** None — all listed opportunities resolved.

**Incidental fix (in-scope, required for validation):** `suno-style-prompt-builder/scripts/tests/` was missing the hyphen-collection `conftest.py` that every sibling test dir has, so its 35 validate-prompt tests were silently not collected. Added it. (The sibling `suno-feedback-elicitor/scripts/tests/` has the same gap but is out of scope per guardrails — noted for a future pass.)

**Tests:** `_shared/tests` + `suno-style-prompt-builder` = 61 pass (added: disjoint-set guard in `_shared`; `rock opera` + texture-modifier-doesn't-satisfy-front-loading in SPB). Full task sweep (`_shared` + SPB + feedback-elicitor/scripts/tests + playlist-sequencer) = 63 pass. All 6 sibling scripts importing `suno_constants` load cleanly. `scan-path-standards.py` + `scan-scripts.py`: 0 live findings on edited files (remaining path-scan hits are `.analysis/` workspace + the canonical `.decision-log.md`, both out of scope).

