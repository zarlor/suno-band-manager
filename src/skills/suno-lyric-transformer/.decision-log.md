# Decision Log — suno-lyric-transformer

## 2026-06-17 — Quality analysis

Grade: Good. Interactive HTML: `.analysis/20260617-184244/quality-report.html`. Full markdown: `.analysis/20260617-184244/quality-report.md`.
Run via `bmad-workflow-builder` analyze (5-skill suno-workflow sweep; agent excluded). 4 LLM scanners + 5 lint/prepass scripts per skill.

## 2026-06-17 — v2-standard fix pass

Brought the skill up to BMad Module Builder (v2) standard against the quality report. Resolved all themes:

- **DEFECT (sha256):** `analyze-input.py` now emits `metrics.source_hash` (stdlib `hashlib`) — the authoritative change-tracking hash. SKILL.md headless contract (`source_hash`) and the LT-STATE marker now READ it from JSON instead of demanding an uncomputable hand-hash; `draft_hash` comes from re-running the script on the current draft. Bumped to v1.1.0; added two hash unit tests.
- **On Activation:** added a proper `## On Activation` (resolver step 1, bmad-init config load, greet→Step 1), folding in the former `## Config` and routing from a slimmed `## Activation Mode Detection`. Mirrors suno-style-prompt-builder / suno-feedback-elicitor.
- **Customization:** added minimal `customize.toml` (`[workflow]` with the default `persistent_facts` glob) + the resolver activation step. Output paths now read `{songbook_folder}` / `{band_profiles_folder}` instead of hardcoded `docs/` literals.
- **Paths/Conventions:** stripped all 6 `./` prefixes to bare paths; stamped the canonical `## Conventions` block.
- **SKILL.md/references seam:** declared `metatag-reference.md` canonical; thinned the duplicated inline Step-3 tag/rhythm lore to outcome statements + pointers; deferred the 959-line reference load to Step 3 (only on ST/RA) while keeping `section-jobs.md` in the Step-1 load. Wired short-input detection to the short-poem strategies and added em-dash narrative-tag flagging/translation.
- **Headless:** added `status` (complete|blocked) + one-line `reason`, a `decision_log` of unsupervised assumptions, and a documented non-Latin headless default. Moved the lyric-vs-metatag char split into `validate-lyrics.py` (`lyric_character_count` / `metatag_character_count`, v1.2.0) so the LLM reads it rather than counting brackets.
- **DLW:** songbook save now writes `.decision-log.md` (key decisions + intentional keeps, incl. the writer's voice/hedge choices); Refinement Mode reads it first and surfaces conflicts before overriding. LT-STATE marker now seeded at Step 2 (after analysis + option selection), not Step 3.
- **UX:** open-floor invitation + soft-gate in Step 1; Step 2 leads with the recommended set + rationale, full 8-code table framed as optional; interactive quick-win path for explicit option statements; upfront split/focus for far-over-budget input; starter-prompt now labeled "run through Style Prompt Builder first."
- **Cleanup:** removed on-disk `scripts/__pycache__/` (already gitignored, untracked); bumped both touched scripts' versions and help epilogs.

**Validation:** scan-path-standards — SKILL.md/customize.toml clean (0 findings; before: 6 high `./` on SKILL.md). scan-scripts — pass, 0 lint issues. Tests: 102 passed (was 99; +3). Remaining path-scan findings are all inside `.analysis/` (immutable run record) and `.decision-log.md` at root (module-wide DLW convention shared by all siblings).

## 2026-06-18 — CODE_DESCRIPTIONS drift fix

**Bug:** The `CODE_DESCRIPTIONS` dicts in `scripts/validate-options.py` (~line 35) and `scripts/assemble-summary.py` (~line 33) had drifted from the canonical 8-code menu in `SKILL.md` (Step 2 "Full menu" table). Both scripts carried the same wrong expansions, so a user-facing Transformation Summary and the options validator both mislabeled what each code does — e.g. `CE` rendered as "Cliche Elimination" when it means **Chorus Extraction**, and `CC` as "Consistency Check" when it means **Chorus Creation**. The contradictions were silent (no test asserted the mapping), and the `RE` code was missing entirely from both dicts — and from `validate-options.py`'s `VALID_CODES`, so a perfectly legal `RE` selection was being rejected as an invalid code.

**Canonical mapping (SKILL.md is source of truth):** ST = Structure Tagging · CE = Chorus Extraction · CC = Chorus Creation · RA = Rhythmic Adjustment · RE = Rhyme Enhancement · FR = Full Rewrite · CD = Cliche Detection · WF = Word Fidelity Mode.

**Fixes (both files reconciled to SKILL.md and to each other):**
- `validate-options.py`: corrected ST/CE/CC/RA/WF descriptions, added the missing `RE` entry, and derived `VALID_CODES = set(CODE_DESCRIPTIONS)` (was a hand-maintained set missing `RE`). Added a source-of-truth comment. Also corrected the inline finding messages that spelled out `WF (Word Flow)` → `WF (Word Fidelity Mode)` and `CE (Cliche Elimination)` → `CE (Chorus Extraction)`, plus the CC/CE dependency note, and added `RE` to the `--help` "Valid codes" line.
- `assemble-summary.py`: same five corrected descriptions + added `RE` + source-of-truth comment. Line ~91 usage (`CODE_DESCRIPTIONS.get(code, code)`) was already correct and unchanged.
- Other scripts scanned (analyze-input, validate-lyrics, cliche-detector, syllable-counter, lyrics-diff, section-length-checker): none hardcode the option-code list/descriptions, so no further drift of this class exists.

**Drift guards added:** `test-validate-options.py` and `test-assemble-summary.py` now import each script and assert `CODE_DESCRIPTIONS` equals the canonical mapping (and, for the validator, `VALID_CODES == set(canonical)`); added a regression test that `RE` validates cleanly and that the assembled markdown renders every code with its canonical meaning.

**Validation:** `uv run --with pytest --with pyyaml python -m pytest src/skills/_shared/tests src/skills/suno-lyric-transformer -q -p no:cacheprovider` → 130 passed (was 124; +6).

## 2026-06-18 — Quality analysis (post-v2-remediation re-run)

Grade: Excellent. HTML: `.analysis/20260618-091127/quality-report.html`, markdown: `.analysis/20260618-091127/quality-report.md`.

## 2026-06-18 — Excellent-grade polish pass (remaining opportunities)

Resolved the leftover quality-analysis opportunities on an already-Excellent skill — polish, not remediation; no regression to the grade. Edits confined to `src/skills/suno-lyric-transformer/` (SKILL.md, customize.toml, references/README.md). Craft voice and the writer's-voice / hedge-preservation disciplines preserved throughout.

- **OPP-high — verify voice preservation, don't just promise it (resolved):**
  - SKILL.md Step 4: added a single-lens **voice-preservation second read** (original vs transformed) run before presenting/returning — names the one biggest risk that a transform weakened the strongest image, flattened the emotional core, or drifted from voice (or states the transform held). Surfaced as one line in "Changes Made" (interactive, added to the output-format block) and a `caveats` entry (headless). Deliberately one lens, not a review panel.
  - SKILL.md Step 1 band-profile input: split into three distinct states — **not found / found-but-malformed / found-but-no-voice-fields** — carried into Step 4 so "verify voice alignment" reports "no constraints to check against" instead of rubber-stamping absent constraints. Step 4 alignment check updated to honor the field-less case.
- **OPP-medium — headless + edge-input corners (resolved):**
  - Oversized input: documented a **headless default** (focus the strongest section that fits, log it, return `complete_with_caveats`; block only if even that won't fit). Named oversize as a `blocked` trigger.
  - Added a **mixed-script clause** at Step 1 (Latin lines → syllable/rhyme/cliche; non-Latin lines → structure-only; report the split in analysis + `caveats`/`decision_log`).
  - Added a **Step-1 unbroken-prose sentence**: segment running prose into candidate lines on clause/breath boundaries before arc-mapping or line-based script analysis; flag the breaks as inferred.
  - Added `caveats` array + **`complete_with_caveats`** status to the headless contract so degraded-but-delivered runs (second-read flag, script fallback, oversize-focus, non-Latin/mixed) are machine-visible and distinct from `blocked`. (This subsumes the requested `warnings` array.)
- **OPP-medium — codes leak into novice path (resolved):**
  - Step 2: recommendations now **lead with the plain-English outcome, code in parentheses** ("even out line lengths so Suno doesn't rush them (RA)"); codes framed as return-user shorthand.
  - Step 4 diff: added a line telling the user they can **reverse a single transformation by naming its code/effect**, with the correct mechanic — re-apply the remaining codes to the **original**, not the current draft.
- **OPP-low — trim drift-prone duplicate copy (resolved):**
  - `references/README.md`: chose the **strip-to-pointers** option (kept in `references/`, still non-loaded by design). Removed the duplicated transformation-options and scripts tables — now one-line pointers to the canonical homes (SKILL.md / metatag-reference.md / section-jobs.md). Fixed **seven → eight** transformation options and added a note that the file is non-loaded and points rather than restates.
  - `customize.toml`: dropped the dangling `See standard-fields.md ...` clause (that file doesn't ship with the skill) and described the `[workflow]` shape inline as siblings do ("Scalars override; plain arrays append").

Nothing skipped — all listed opportunities resolved.

**Validation:** scan-path-standards — 0 live findings (all 75 are inside `.analysis/` and `.decision-log.md`, the pre-existing baseline). scan-scripts — 0 findings. Tests: `uv run --with pytest --with pyyaml python -m pytest src/skills/_shared/tests src/skills/suno-lyric-transformer -q -p no:cacheprovider` → 131 passed (no scripts/tests touched this pass; confirms no regression). Not committed.

