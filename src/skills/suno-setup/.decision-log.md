# Decision Log — suno-setup

## 2026-06-17 — Quality analysis

Grade: Good. Interactive HTML: `.analysis/20260617-184244/quality-report.html`. Full markdown: `.analysis/20260617-184244/quality-report.md`.
Run via `bmad-workflow-builder` analyze (5-skill suno-workflow sweep; agent excluded). 4 LLM scanners + 5 lint/prepass scripts per skill.

## 2026-06-17 — Module Builder v2 fix-pass (all quality findings)

Brought suno-setup to the v2 standard, judging it as a config-writing installer utility (not a creative HITL workflow). All edits scoped to `src/skills/suno-setup/`.

- **Paths + Conventions (Opp 2).** Stamped the canonical `## Conventions` block, adapting the `{skill-root}` line to "(where `SKILL.md` lives)" since this installer correctly keeps no `customize.toml` (a second override layer for the values it already writes would be redundant). Converted all 9 leading-dot-slash assets/scripts references to bare skill-root paths and prefixed the file-path `_bmad` references with `{project-root}` (including prose mentions the lexical scanner flags). Kept the `{project-root}`-is-literal-token note — extended it to clarify the token is resolved only for filesystem ops, never when persisting values.
- **Headless return contract (Opp 1).** Added a `## Headless mode` section: final-line JSON `{status, config_path, user_config_path, module_code, version, mode, guard_configured, decisions[]}`, a headless guard DEFAULT (auto-configure for whatever platform files exist; create AGENTS.md if neither), and a lightweight inline `decisions` list instead of full Decision-Log ceremony.
- **Update-mode non-destructiveness (Opp 4).** Write Files now reads the pre-write version and reports "upgrading suno X → Y", and shows a per-key "current → new" diff for any value about to change, letting the user keep hand-edits (carried back into the answers JSON).
- **Hostile-env + dead command (Opp 3).** Removed the dead `bash scripts/pack-portable.sh` greeting from module.yaml (pointed to INSTALLATION.md Multi-Machine Sync instead). Wrapped `load_yaml_file` in try/except emitting a clean actionable JSON error (exit 1) on malformed YAML. Added a missing-dep recovery line (`uv run` / `pip install pyyaml`). Stated the guard no-platform fallback (configure-guard.py creates AGENTS.md).
- **Directory plumbing (Opp 5).** Honored the `directories:` declaration via a new `merge-config.py --create-dirs` flag that consumes the declared list + `output_folder`, resolves `{project-root}` on disk only, and returns JSON `{created, existed}`. SKILL.md "Create Output Directories" now calls the script instead of having the LLM resolve tokens by hand.
- **Script hygiene + tests (Opp 6).** Added `scripts/tests/` with unit tests for all four scripts (24 tests, all passing). Added `sys.exit()` codes to configure-guard.py (0/1/2). All scripts retain PEP 723 metadata.

**Lint:** scan-scripts 6→0 findings (status pass). scan-path-standards in-scope (SKILL.md + assets) 13→0 path findings. One residual scanner finding remains: `.decision-log.md` flagged as a root prompt file — accepted as a known scanner false positive; the Decision-Log Workspace pattern mandates `.decision-log.md` at skill root as a peer of SKILL.md. The `.analysis/` directory findings are pre-existing scanner-output artifacts (out of scope, not deleted).

**Tests:** 24/24 passing — merge-config (9), merge-help-csv (5), configure-guard (6), cleanup-legacy (4). Verified end-to-end merge + `--create-dirs` integration manually.

## 2026-06-18 — Quality analysis (post-v2-remediation re-run)

Grade: Good. HTML: `.analysis/20260618-091127/quality-report.html`, markdown: `.analysis/20260618-091127/quality-report.md`.

## 2026-06-18 — Remaining-opportunities fix-pass (medium→low)

Resolved the five clustered opportunities from the 0618 report. All edits scoped to `src/skills/suno-setup/`. Kept it a tight installer — no new ceremony.

- **OPP-1 Install-to-first-use handoff (medium) — RESOLVED.** Confirm now closes with a concrete first-use pointer derived from the `module-help.csv` `after:`/`before:` graph ("create a band profile, then create a song"), before the generic `module_greeting`. Standalone installs drop the greeting's multi-machine-sync paragraph (it requires the top-level `scripts/` a standalone/marketplace install lacks). `module.yaml` greeting reworded to state the `scripts/` prerequisite honestly instead of pitching it unconditionally.
- **OPP-2 Update-diff timing + headless keep-vs-overwrite (medium) — RESOLVED + optional script half done.** Write Files now pins the diff + keep decision as **pre-write** ("a preview reported after the write would be a replay"). Headless mode states the keep-vs-overwrite default (keep hand-edits on conflict, record in `decisions[]`). Implemented the optional `merge-config.py --detect-mode` returning `{mode, has_module_section, has_legacy, version_transition}` plus `changes:[{key,old,new}]` when `--answers` is passed (result-template-aware, excludes user-only/unchanged keys) — a real dry-run→confirm→commit shape. The update-diff and mode-classification now come from the *same* deterministic pass that the merge uses.
- **OPP-3 Headless caller-facing surface (low) — RESOLVED.** Added a concrete NL invocation example and a note that the "flags" are model-interpreted language, not argv. Return JSON now carries `output_dirs` (resolved `band_profiles_folder`/`songbook_folder`) so a chaining caller wires the next skill without re-reading config; optional `--create-dirs {created,existed}` mentioned.
- **OPP-4 Mode classification + legacy messaging (low) — RESOLVED.** Moved classification into the `--detect-mode` pre-pass (consistency: narrated/returned mode can't drift from the written mode). Distinguished installer-written init bridge files from genuine pre-consolidation legacy — `update` fires when a consolidated section exists even with init configs present, so the "legacy migration" message no longer false-fires on a clean upgrade. Write Files echoes the resolved `{project-root}` ("Installing into …") before the first destructive action.
- **OPP-5 Architecture doc precision (low) — RESOLVED.** Overview now names `assets/module-help.csv` as the second asset input. The anti-zombie sentence names both scripts (`merge-config.py`, `merge-help-csv.py`). Confirm collapsed from key-by-key JSON re-enumeration to an outcome statement ("surface them as an outcome, don't re-list mechanically").

**Lint:** scan-scripts 0 findings (pass). scan-path-standards on a `.analysis`-excluded copy: only the adjudicated `.decision-log.md` root-file false positive remains (mandated DLW peer) — same as baseline; two transient `bare-bmad` findings from new prose were fixed by prefixing `{project-root}/_bmad/`.

**Tests:** 28/28 passing (was 24) — added 4 `--detect-mode` tests (fresh/standalone, update-not-migration-with-init-files, migration-without-section, changes-diff). Verified detect-mode behavior manually across all four modes.

SKILL.md grew 152→169 lines; above the ~130 soft ceiling but justified for a multi-section installer with per-mode branch narration (report classifies it as correctly inline). No items skipped — every listed opportunity was resolved or better.

