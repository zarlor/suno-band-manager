---
name: suno-setup
description: Sets up Suno Band Manager module in a project. Use when the user requests to 'install suno module', 'configure Suno Band Manager', or 'setup Suno Band Manager'.
---

# Module Setup

## Conventions

- Bare paths (e.g. `scripts/merge-config.py`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `SKILL.md` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

`{project-root}` is also a **literal token** in config *values* — never substitute it with an actual path when writing config. It signals to the consuming LLM that the value is relative to the project root, not the skill root. (Resolve it only for filesystem operations like directory creation, never when persisting the value.)

## Overview

Installs and configures a BMad module into a project. Module identity (name, code, version) and variable definitions come from `assets/module.yaml`; the capability rows registered for the help system come from `assets/module-help.csv`. Collects user preferences and writes them to three files:

- **`{project-root}/_bmad/config.yaml`** — shared project config: core settings at root (e.g. `output_folder`, `document_output_language`) plus a section per module with metadata and module-specific values. User-only keys (`user_name`, `communication_language`) are **never** written here.
- **`{project-root}/_bmad/config.user.yaml`** — personal settings intended to be gitignored: `user_name`, `communication_language`, and any module variable marked `user_setting: true` in `assets/module.yaml`. These values live exclusively here.
- **`{project-root}/_bmad/module-help.csv`** — registers module capabilities for the help system.
- **`{project-root}/_bmad/core/config.yaml`** and **`{project-root}/_bmad/suno/config.yaml`** — per-module config files written automatically by `merge-config.py` so that `bmad-init` can load config at runtime. These bridge the shared config format with `bmad-init`'s expected per-module layout.

`merge-config.py` (config.yaml) and `merge-help-csv.py` (module-help.csv) each use an anti-zombie pattern — both rewrite this module's section fresh, removing any existing entries before writing, so stale values never persist.

## On Activation

1. Read `assets/module.yaml` for module metadata and variable definitions (the `code` field is the module identifier)
2. **Detect installation mode deterministically** with the pre-pass — it classifies the install the same way the merge will, so the narrated mode never drifts from what gets written or returned:

   ```bash
   uv run scripts/merge-config.py --detect-mode --config-path "{project-root}/_bmad/config.yaml" --module-yaml assets/module.yaml --legacy-dir "{project-root}/_bmad"
   ```

   It returns `{mode, has_module_section, has_legacy, version_transition}`. Narrate the `mode`:
   - **`update`** — config.yaml already has this module's section. Lead Confirm with the `version_transition`. Any per-module init configs present are this installer's own runtime bridge files (`has_legacy: true` here is expected), **not** pre-consolidation legacy — do not show the legacy-migration message.
   - **`fresh`** — `{project-root}/_bmad/` exists, no module section. If `has_legacy`, a prior installer left per-module config; tell the user it was detected and values will be consolidated into the new format (used as fallback defaults).
   - **`standalone`** — no `{project-root}/_bmad/`. Create it and proceed with defaults. Inform the user: "Setting up standalone — no BMad Method detected, using direct configuration."
   - **`migration`** — genuine pre-consolidation legacy: per-module config exists but config.yaml has no module section. Inform the user legacy values will be used as fallback defaults.

   In the `fresh`-with-legacy and `migration` cases, the per-module config files and directories are cleaned up after setup.

If the user provides arguments (e.g. `accept all defaults`, `--headless` / `-H`, or inline values like `user name is BMad, I speak Swahili`), map any provided values to config keys, use defaults for the rest, and skip interactive prompting. Still display the full confirmation summary at the end. See **Headless mode** for the autonomous-run contract.

## Collect Configuration

Ask the user for values. Show defaults in brackets. Present all values together so the user can respond once with only the values they want to change (e.g. "change language to Swahili, rest are fine"). Never tell the user to "press enter" or "leave blank" — in a chat interface they must type something to respond.

**Default priority** (highest wins): existing new config values > legacy config values > `assets/module.yaml` defaults. When legacy configs exist, read them and use matching values as defaults instead of `module.yaml` defaults. Only keys that match the current schema are carried forward — changed or removed keys are ignored.

**Core config** (only if no core keys exist yet): `user_name` (default: BMad), `communication_language` and `document_output_language` (default: English — ask as a single language question, both keys get the same answer), `output_folder` (default: `{project-root}/_bmad-output`). Of these, `user_name` and `communication_language` are written exclusively to `config.user.yaml`. The rest go to `config.yaml` at root and are shared across all modules.

**Module config**: Read each variable in `assets/module.yaml` that has a `prompt` field. Ask using that prompt with its default value (or legacy value if available).

## Write Files

Before the first write, echo the resolved project root once ("Installing into `<resolved path>`") so a user who launched from the wrong directory can catch it before anything is created or deleted.

**Resolve the update-diff and keep/overwrite decisions BEFORE the merge runs** — the anti-zombie rewrite is destructive, so the preview has to happen against the still-untouched config. On an update, run the dry-run pass first (it writes nothing), settle any keeps with the user, fold kept values back into the answers JSON, and only then run the merge below. See **Update mode** for the diff mechanics.

Write a temp JSON file with the collected answers structured as `{"core": {...}, "module": {...}}` (omit `core` if it already exists). Then run both scripts — they can run in parallel since they write to different files (batch them in a single message to guarantee concurrency):

```bash
uv run scripts/merge-config.py --config-path "{project-root}/_bmad/config.yaml" --user-config-path "{project-root}/_bmad/config.user.yaml" --module-yaml assets/module.yaml --answers {temp-file} --legacy-dir "{project-root}/_bmad"
python3 scripts/merge-help-csv.py --target "{project-root}/_bmad/module-help.csv" --source assets/module-help.csv --legacy-dir "{project-root}/_bmad" --module-code suno
```

Both scripts output JSON to stdout with results. If either exits non-zero, surface the error and stop. The scripts automatically read legacy config values as fallback defaults, then delete the legacy files after a successful merge. `merge-config.py` also writes per-module config files (`{project-root}/_bmad/core/config.yaml` and `{project-root}/_bmad/suno/config.yaml`) that `bmad-init` reads at runtime. Check `legacy_configs_deleted`, `legacy_csvs_deleted`, and `init_configs_written` in the output to confirm.

`merge-config.py` requires `pyyaml`; `uv run` resolves it automatically from the script's PEP 723 metadata. If `uv` is unavailable and the run fails on a missing `pyyaml`, retry with `pip install pyyaml` (or `python3 -m pip install pyyaml`) then re-run. If `merge-config.py` reports a clean error about a corrupt existing config or user config, surface its message verbatim and stop — do not overwrite the file.

Run `scripts/merge-config.py --help` or `scripts/merge-help-csv.py --help` for full usage.

**Update mode — preview what changes before overwriting.** On an update, the anti-zombie rewrite replaces the whole module section, which can silently revert hand-edited values. Get the deterministic diff from the same pre-pass that classified the mode, passing the answers temp file so it dry-run-diffs them against the existing config (it writes nothing):

```bash
uv run scripts/merge-config.py --detect-mode --config-path "{project-root}/_bmad/config.yaml" --module-yaml assets/module.yaml --answers {temp-file}
```

- Report `version_transition` (e.g. "upgrading suno 1.8.2 → 1.8.3").
- For each entry in `changes:[{key, old, new}]`, show a "current → new" line and let the user keep the existing value. Carry kept values forward into the answers JSON so the merge writes them back. This whole exchange happens **before** the merge command above runs — a preview reported after the write would be a replay, not a preview.

## Create Output Directories

After writing config, create the module's declared output directories with one deterministic call. `merge-config.py --create-dirs` consumes the `directories:` list plus `output_folder` from the resolved config and creates any that don't exist (resolving `{project-root}` for the filesystem only — the stored config values keep the literal token):

```bash
uv run scripts/merge-config.py --create-dirs --config-path "{project-root}/_bmad/config.yaml" --module-yaml assets/module.yaml --project-root "{project-root}"
```

Pass the real project root for `--project-root` so the token resolves on disk. The script returns JSON `{created, existed}` — report `created` in the Confirm step.

## Cleanup Legacy Directories

After both merge scripts complete successfully, remove the installer's package directories. Skills and agents in these directories are already installed at `.claude/skills/` — the `{project-root}/_bmad/` directory should only contain config files.

```bash
python3 scripts/cleanup-legacy.py --bmad-dir "{project-root}/_bmad" --module-code suno --also-remove _config --skills-dir "{project-root}/.claude/skills"
```

The script verifies that every skill in the legacy directories exists at `.claude/skills/` before removing anything. Directories without skills (like `_config/`) are removed directly. The script preserves `config.yaml` files in directories being cleaned — `bmad-init` needs these per-module config files at runtime. If the script exits non-zero, surface the error and stop. Missing directories (already cleaned by a prior run) are not errors — the script is idempotent.

Check `directories_removed` and `files_removed_count` in the JSON output for the confirmation step. Run `scripts/cleanup-legacy.py --help` for full usage.

## Configure Pipeline Guard (Optional)

After config and cleanup are complete, offer to configure the pipeline guard. The guard enforces Mac's mandatory production pipeline — it prevents hand-building Suno packages without running the formal skill pipeline (Style Prompt Builder + Lyric Transformer).

Ask: "Want me to set up the pipeline guard? It ensures Mac always runs the production skills before presenting a Suno package. I can configure it for your coding tool."

If the user declines, skip to Confirm.

If the user accepts, configure both layers. The two commands write to different files, so batch them in a single message to run in parallel; report what was configured in Confirm.

### Claude Code Stop Hook

If the project has a `.claude/` directory (indicating Claude Code usage), configure the deterministic Stop hook:

```bash
python3 scripts/configure-guard.py --settings-path "{project-root}/.claude/settings.local.json" --guard-script-path ".claude/skills/suno-agent-band-manager/scripts/pipeline-guard.py"
```

The script merges the hook into existing settings without overwriting other configuration. It's idempotent — skips if already configured. Check the JSON output for `status` ("configured", "already_configured", or "error").

**Path note:** The hook command uses `$CLAUDE_PROJECT_DIR` (a Claude Code environment variable) so it works regardless of where the project lives on disk.

### Standing Order (All Platforms)

Configure the cross-platform standing order in `AGENTS.md` — readable by Codex CLI, Cursor, GitHub Copilot, Windsurf, Amp, and Gemini CLI (when configured to read AGENTS.md):

```bash
python3 scripts/configure-guard.py --agents-md-path "{project-root}/AGENTS.md"
```

The script appends the standing order section to AGENTS.md (creates the file if it doesn't exist). Idempotent — skips if the section already exists.

**No-platform fallback:** if the project has neither a `.claude/` directory nor an `AGENTS.md`, run only the `--agents-md-path` command — `configure-guard.py` creates `AGENTS.md` from scratch, so the standing order still lands.

## Confirm

Summarize the install from the scripts' JSON output — what config, user settings, init configs, help entries, and output directories were written, plus the install mode. On an update, lead with the version transition and any kept-vs-overwritten values from Write Files. If legacy files or directories were removed, mention the migration and the cleanup count (e.g. "Cleaned up 106 installer package files from bmb/, core/, \_config/ — skills are installed at .claude/skills/"). The result keys are bound at their source sections; surface them as an outcome, don't re-list them mechanically.

Then close with a concrete next step, not just the generic `module_greeting`. A fresh install's natural first move falls out of the `assets/module-help.csv` `after:`/`before:` graph: `create-song` lists `after: suno-band-profile-manager:manage-profiles`, which itself runs `before: build-style-prompt` — so the entry point is creating a band profile, then a song. Point the user there explicitly (e.g. "Next: say 'create a band profile', then 'create a song'"), then display the `module_greeting` from `assets/module.yaml`. On a **standalone** install, drop the greeting's multi-machine-sync paragraph — it needs the top-level `scripts/` folder that a standalone/marketplace install lacks, and it's the wrong pitch for a first-timer.

## Headless mode

These "flags" are natural language the orchestrating model interprets, not an argv parser — a caller invokes this skill the way it invokes any skill. Example: *"install suno module -H, user name is BMad, language English, accept the guard default."*

When invoked headlessly (`--headless` / `-H`, or "accept all defaults"), run end-to-end with no prompts: take provided inline values, fill the rest from the default-priority chain, and run all scripts. **Update keep-vs-overwrite default:** on a headless update, keep existing hand-edited values where they differ from the new defaults (run the `--detect-mode --answers` diff, fold the `changes` back as keeps) and record the override in `decisions[]`. **Pipeline-guard default:** auto-configure for whatever platform files exist — run the Stop-hook command if `{project-root}/.claude/` exists, run the AGENTS.md command if `{project-root}/AGENTS.md` exists, and if neither exists, create `AGENTS.md` (run the `--agents-md-path` command). Skip only if the caller passed an explicit guard opt-out.

**Headless return.** Emit, as the final line of your response, a single JSON object the calling process can parse:

```json
{"status": "complete", "config_path": "...", "user_config_path": "...", "module_code": "suno", "version": "1.8.3", "mode": "fresh", "guard_configured": true, "output_dirs": {"band_profiles_folder": "{project-root}/docs/band-profiles", "songbook_folder": "{project-root}/docs/songbook"}, "decisions": []}
```

- `status`: `complete` or `blocked`. On `blocked`, add a one-line `"reason"` and still return whatever paths are known.
- `mode`: `fresh` | `update` | `standalone` | `migration` (the detected installation mode, from `--detect-mode`).
- `version`: the `module_version` just written; on an update, use `"<old> → <new>"`.
- `guard_configured`: whether the pipeline guard was wired.
- `config_path` / `user_config_path`: resolved paths from `merge-config.py`'s JSON output.
- `output_dirs`: the resolved module output folders (the `band_profiles_folder` / `songbook_folder` values written to the module section, literal `{project-root}` token intact) so a chaining caller can wire the next skill without re-reading config. Optionally also include the `--create-dirs` `{created, existed}` result.
- `decisions`: lightweight inline list of any default chosen without the user (e.g. `"language defaulted to English"`, `"headless update kept hand-edited suno_tier=pro"`, `"guard auto-configured: AGENTS.md (no .claude/)"`). Full Decision-Log ceremony is overkill for an installer; this list is the audit trail.

## Outcome

Once the user's `user_name` and `communication_language` are known (from collected input, arguments, or existing config), use them consistently for the remainder of the session: address the user by their configured name and communicate in their configured `communication_language`.
