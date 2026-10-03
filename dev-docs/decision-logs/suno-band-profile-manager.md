# Decision Log — suno-band-profile-manager

## 2026-06-18 — Long-lived-artifact gaps + headless/legibility pass (enhancement F1–F6)

Resolved the remaining quality-analysis opportunities from `.analysis/20260618-091127/enhancement-analysis.md` (F1–F6). Scope limited to this skill's own files. The "remediation pass landed; what's left are long-lived-artifact gaps" framing held — these are the gaps that only surface once the profile lives for months.

**Data contract pinned (applied, not relitigated).** Stated plainly in `profile-schema.md`: `generation_learnings` = durable learned patterns across songs (distilled "what works / what doesn't", not tied to one generation); `generation_history` = per-generation snapshots (this round's settings + reaction). The Feedback Elicitor writes BOTH — appends the snapshot to history, promotes durable patterns into learnings. Updated the two YAML-section header comments, the Feedback-Elicitor read/write note, and added an explicit contract paragraph in "Notes for Downstream Skills."

**OPP-high F1 — multi-Voice strategy had no structural home → RESOLVED (added the structure).** Chose the cleaner of the two options (add the field, not just disclaim). Added an optional `voices:` list (`{voice_id, label, use_case}` per entry) to the schema YAML structure, field-definitions table, validation rules (new rules 20–21), and the Style Prompt Builder read-list. Reconciled the contradicting "Multi-profile Voice strategy" note (schema, formerly promised a mapping with nowhere to live) to point at the new list; `vocal.voice_id` stays the single-Voice primary/default. Wired Create discovery to capture the list when a band uses >1 Voice. Implemented the rules in `validate-profile.py` (voices must be a list; each entry needs a non-empty `voice_id`; `use_case` recommended; warn if `vocal.voice_id` names a Voice absent from the list) with 7 new unit tests.

**OPP-high F2 — accumulator fields written but never surfaced/captured → RESOLVED.** `known_working_patterns` / `known_limitations` / `generation_learnings` now have in-skill read+capture moments: **Edit** reads all three when a change touches genre/mood/vocal and surfaces collisions ("known_limitations says 'funk metal' triggers slap bass — rephrase?"); **Health Check** adds a review bullet that reads them back and offers to capture newly-learned patterns into the right field per the data contract; **Create** gets an optional learnings-capture bullet (don't push first-timers). No new machinery — same loop the decision-log pattern already closes, applied to the band's craft fields.

**OPP-high F3 — Analyze Writer Voice "create new" dead-end → RESOLVED.** The Store step now spells out the no-band-yet branch: don't manufacture a stub that fails validation; hold the analysis, route into Create, drop it into `writer_voice` once required fields are gathered.

**OPP-medium F5 — headless:create failure-mode → RESOLVED.** The `--headless:create` row now states both outcomes: auto-resolvable issues (over-limit style_baseline → trim; free-tier sliders/studio prefs → drop) are fixed, logged, surfaced in a `validation.warnings` block → `complete`; unresolvable (missing required genre/mood/style_baseline, invalid tier/model) → `blocked` with `reason`, nothing saved. Both return shapes shown.

**OPP-medium F4 — open-floor opening didn't net tier/model → RESOLVED.** Added the Suno plan to the open-floor invite so `tier-features.py` can run early and prune discovery to the user's reality, with a one-line rationale on why tier is load-bearing.

**OPP-low (customize.toml legibility) → RESOLVED.** Added a comment pointing to `band_profiles_folder` / `songbook_folder` in `_bmad/config.yaml` as the output-path override channel (paths are config-driven, deliberately not scalars here), plus an inline note on `persistent_facts` intent.

**OPP-low F6 — Health Check parallel review lenses → SKIPPED (better left as-is).** The analysis itself rates it low and notes the pattern only pays off "if the skill ever grows"; fanning a single friendly six-dimension pass into subagent lenses adds machinery for marginal benefit and cuts against the don't-over-engineer bar. Noted, not implemented.

**Accepted lint exceptions (unchanged, per task).** The `.decision-log.md`-at-skill-root path-standards flags (7) are the DLW sibling artifact; the 2 cross-skill `../` links in `tier-features.md:114,120` (→ `_shared/references/STUDIO-EDITOR-REFERENCE.md`) are intrinsic real relative links to a sibling. Both left in place.

**Note (out of scope, observed).** `profile-schema.md` YAML-structure comment (line ~23) lists `v5.5` as a model value but `_shared/suno_constants.py` `VALID_MODELS` uses `v5.5 Pro`; bare `v5.5` fails validation. Pre-existing, not one of the assigned opportunities, and `_shared/` is off-limits — flagged for a future pass, not touched here.

**Validation.** scan-scripts: 0 findings. scan-path-standards: 9 live findings, all accepted exceptions above (0 in any file edited this pass). Tests: `uv run --with pytest --with pyyaml python -m pytest src/skills/_shared/tests src/skills/suno-band-profile-manager -q -p no:cacheprovider` → **132 passed** (was 125; +7 voices tests). Smoke-tested the validator against a valid multi-Voice profile (passes clean) and the primary-not-in-list warning path.

## 2026-06-18 — Config-driven output paths threaded into scripts (backward-compatible)

Closed the SKILL.md-vs-script split-brain noted as a caveat in the 2026-06-17 entry below. The module config vars (`band_profiles_folder`, `songbook_folder`) are now load-bearing in the Python scripts, not just referenced in SKILL.md text.

**Scripts + args added:**
- `validate-profile.py` — added optional `--docs-dir`. The per-band playlist/songbook check previously derived the docs root from `profile_path.parent.parent.parent` ("`docs`"); it now uses `--docs-dir` when given, else the profile's grandparent dir (`{profile}/../..`, = `{project-root}/docs` for the standard `docs/band-profiles/{slug}.yaml` layout). Default behavior is byte-identical.
- `scaffold-playlist.py` — added optional `--docs-dir`. Both the playlist write target (`{docs-dir}/{slug}-playlist.yaml`) and the `--from-songbook` discovery (`{docs-dir}/songbook/{slug}/`) now honor it; default is `{project-root}/docs` (unchanged). Added a `_report_path` fallback so the JSON `path`/`songbook_path` report relative-to-project-root when possible and absolute when `--docs-dir` points outside the project (avoids a `relative_to` crash).
- `list-profiles.py` — added optional `--profiles-dir` named flag that overrides the existing positional `profiles_dir` (which still defaults to `docs/band-profiles`). Lets callers pass the configured `{band_profiles_folder}` by flag; omitting it reproduces prior behavior exactly.
- `apply-profile.py` — already had `--profiles-dir` (default `{project-root}/docs/band-profiles` via `_resolve_profiles_dir`); left as-is, now covered by a unit test.
- `diff-profiles.py` — no change; it takes two explicit file paths with no directory derivation.

**SKILL.md:** List/Load/Delete now invoke `list-profiles.py --profiles-dir {band_profiles_folder}`. Both `scaffold-playlist.py` calls (Create, Manage Playlist) pass `--docs-dir {project-root}/docs`. The Scripts table documents the new config-var args on each script, and the Headless note spells out that omitting the args falls back to the `{project-root}/docs/...` defaults. `--project-root` kept as-is everywhere.

**Tests:** Added `--docs-dir`/`--profiles-dir` default-and-override coverage to `test-validate-profile.py`, `test-scaffold-playlist.py` (incl. subprocess main() path-placement), `test-list-profiles.py` (subprocess CLI: positional vs flag vs default), and `_resolve_profiles_dir` coverage to `test-apply-profile.py`. Added a `scripts/tests/conftest.py` (mirroring `_shared/tests/` and `suno-lyric-transformer/scripts/tests/`) so this skill's hyphenated `test-*.py` files are collected — they had no conftest of their own and were silently uncollected by the bare pytest invocation. Full run `uv run --with pytest --with pyyaml python -m pytest src/skills/_shared/tests src/skills/suno-band-profile-manager -q`: **125 passed** (23 shared + 102 here).

## 2026-06-17 — Quality analysis

Grade: Good. Interactive HTML: `.analysis/20260617-184244/quality-report.html`. Full markdown: `.analysis/20260617-184244/quality-report.md`.
Run via `bmad-workflow-builder` analyze (5-skill suno-workflow sweep; agent excluded). 4 LLM scanners + 5 lint/prepass scripts per skill.

## 2026-06-17 — v2-standard remediation pass

Brought the skill up to the BMad Module Builder v2 bar by resolving every quality-analysis finding. Scope was limited to this skill's own files (plus a verified link into the sibling agent skill).

**Paths + Conventions (Opportunity 4).** Stripped all `./references/` and `./scripts/` prefixes to bare skill-root paths across SKILL.md, `references/README.md`, and `references/tier-features.md`. Stamped the canonical 4-bullet `## Conventions` block after Overview. Fixed the dangling `tier-features.md:114` link — it pointed at a non-existent `../../STUDIO-EDITOR-REFERENCE.md`; now matches the verified-working `../../suno-agent-band-manager/references/STUDIO-EDITOR-REFERENCE.md` form used on line 120. Path lint dropped 19→2 source findings; the 2 residual are the cross-skill markdown hyperlinks whose `../` is intrinsic to a real relative link reaching a sibling skill (the accepted house-style finding, not the dangling link).

**Agent-shape trim (Opportunity 2).** Collapsed the Identity line into the Overview's first sentence ("Acts as a music producer's assistant…"). Deleted the 5-row Communication Style table (LLM-native register adaptation — re-teaches what the model does for free). Reduced Principles from 5 bullets to the 2 genuinely non-obvious BMad-specific ones (profile-serves-downstream; capture-over-interrogate). Routed persona/tone variance to `persistent_facts` / `project-context.md` via an explicit note in Step 1 — never a workflow scalar.

**Customization (project decision).** Added a minimal `customize.toml` with `[workflow]`: empty `activation_steps_prepend`/`append` and the default `persistent_facts = ["file:{project-root}/**/project-context.md"]` glob. Added the resolver step as Step 1 of On Activation (verbatim build-process.md shape, with the read-three-files base→team→user fallback). Deliberately did NOT add output-path scalars, booleans, or identity/tone scalars.

**Output paths via config vars.** SKILL.md now references `{band_profiles_folder}` and `{songbook_folder}` (the existing module config vars) instead of hardcoding `docs/band-profiles`/`docs/...`. (FOLLOW-UP: the script-threading caveat originally noted here — that `validate-profile.py`/`scaffold-playlist.py` still derived `docs/...` from `--project-root` only — was **resolved on 2026-06-18**; see the entry at the top of this log. `--docs-dir`/`--profiles-dir` are now threaded through, backward-compatibly.)

**Playlist + headless write path (Opportunity 1).** Added `scaffold-playlist.py` to both the SKILL.md Scripts table and `references/README.md`. Wired it into `--headless:create` (same write batch, returns `playlist_path`) so headless create can't manufacture profiles that fail the validator's playlist rule. Created `apply-profile.py` as the deterministic save/field-merge/duplicate owner (`--save` from stdin, `--set` dot-notation merge preserving key order + untouched fields, `--duplicate` with optional `--bump-version`); headless create/edit/duplicate now call it instead of hand-serializing YAML. Added a **Manage Playlist** router row + operation (scaffold/add/reorder/rename against the canonical YAML, hand off to Feedback Elicitor for album-craft) so playlist requests no longer dead-end in Unclear. Added `scripts/tests/test-scaffold-playlist.py` (10 tests) and `scripts/tests/test-apply-profile.py` (11 tests).

**Headless contract (Opportunity 5).** Documented the input channel per subcommand (create/edit read stdin; rest positional). Every create/edit/duplicate return now carries a `decision_log` path; `status` is `complete`|`blocked` with a one-line `reason` on blocked. The decision log absorbs inferred slug/tier/model and auto-trims.

**Decision-Log Workspace (Opportunity 5).** Adopted the lightweight (~5-sentence) treatment — no `## Workspace` header, no tree diagram, no prescribed frontmatter. Create writes a sibling `{band_profiles_folder}/{profile-name}.decision-log.md` at intent-confirmation (append a session heading if present). Edit reads it and surfaces conflicts before changing fields; Health Check reads it before critiquing against the user's own standards; Post-Operation Flow audits it at handoff. Duplicate writes a fresh log for the new slug.

**UX (Opportunity 5/6).** Added an open-floor "tell me everything you've got" opening to Create. Added a non-blocking validate-on-Load advisory (Load previously never validated, so stale/deprecated state persisted silently). Reordered Create so deterministic `validate-profile.py` runs BEFORE the inline judgment pass (fail-fast). Added the "same as X but…" trigger to Duplicate and chained Duplicate→Edit.

**Script hygiene (Opportunity 5/7).** Added graceful-degradation try/except around the `import yaml` and `_shared`/`suno_constants` imports in `validate-profile.py`, `tier-features.py`, `list-profiles.py`, `diff-profiles.py`, and `apply-profile.py` — each now emits a clear JSON error (or falls back to a literal default for `tier-features.py`'s tier set) instead of an uncaught ImportError, so the LLM can do the work by hand on a web sandbox. Corrected `scaffold-playlist.py`'s PEP 723 block: it declared a `pyyaml` dependency it never imports (stdlib-only string rendering) — removed the spurious dep so the plain `python3` shebang is honest.

**Validation.** scan-path-standards: 19→2 source findings (2 residual = accepted cross-skill `../` markdown links). scan-scripts: clean (0 findings; the missing-test finding resolved). Tests: 88/88 pass (67 pre-existing + 21 new). End-to-end smoke test of apply-profile (save/set/duplicate) → validate → scaffold confirmed clean JSON and correct YAML round-trip.

**Deferred / partial:** ~~script-level `--profiles-dir`/`--docs-dir` threading for a true output-path override (caveat above).~~ DONE 2026-06-18 (see top entry). `references/README.md` orphan-in-`references/` (analysis low/awareness) left in place but kept in sync with the new scripts — moving it is outside this surgical pass.

## 2026-06-18 — Quality analysis (post-v2-remediation re-run)

Grade: Good. HTML: `.analysis/20260618-091127/quality-report.html`, markdown: `.analysis/20260618-091127/quality-report.md`.
Re-run surfaced a self-introduced broken[high]: interactive Create (SKILL.md:113) hand-serialized the save, contradicting the line-76 apply-profile.py invariant. Fixed same day — Create now routes its save through `apply-profile.py --save`, matching Edit/Duplicate.

