---
name: suno-setup
description: Sets up Suno Band Manager module in a project. Use when the user requests to 'install suno module', 'configure Suno Band Manager', or 'setup Suno Band Manager'.
---

# Module Setup

## Conventions

- Bare paths (e.g. `scripts/merge-config.py`) resolve from the skill root.
- `{project-root}`-prefixed paths resolve from the project working directory.

`{project-root}` is a **literal token** in config *values*: never substitute it when writing config. It tells the consuming LLM the value is relative to the project root, not the skill root. Script **path arguments** (`--*-path`, `--*-dir`, `--target`, `--source`, `--project-root`) are real filesystem paths, so resolve the token to the actual project root before running. The scripts reject an unresolved token.

## Overview

Installs and configures the Suno Band Manager module. Module identity, variables and the agent roster come from `assets/module.yaml`; capability rows come from `assets/module-help.csv`. Setup writes:

- **`{project-root}/_bmad/config.yaml`**: core settings at root (`output_folder`, `document_output_language`) plus a `suno:` section with metadata and module values. `user_name` and `communication_language` are never written here.
- **`{project-root}/_bmad/config.user.yaml`**: personal settings, meant to be gitignored: `user_name`, `communication_language`, and any module variable marked `user_setting: true`.
- **`{project-root}/_bmad/module-help.csv`**: the capability list Mac's menu reads.
- **`{project-root}/_bmad/suno/module-help.csv`**: the same rows, where the BMad v6.12 installer looks for them. Its next run (`npx bmad-method install`) adds them to the bmad-help catalog.
- **`{project-root}/_bmad/suno/config.yaml`**: a flat copy of the config that the module's audio scripts read first. Written only when no BMad installer manages `{project-root}/_bmad/`; otherwise the installer owns that file.

Both merges are anti-zombie: they rebuild this module's section and rows from scratch, so stale entries never persist. Setup never writes, moves or deletes anything the BMad installer or another module owns: `{project-root}/_bmad/_config/`, `{project-root}/_bmad/core/` (including `core/config.yaml`), other modules' folders.

## On Activation

**Preflight.** Run `uv --version`. If uv is missing, offer to install it (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`). Without uv, the scripts run with `python3`, but `merge-config.py` then needs `pip install pyyaml`.

1. Read `assets/module.yaml` (the `code` field is the module identifier).
2. Run the detection pre-pass. It writes nothing:

   ```bash
   uv run scripts/merge-config.py --detect-mode --config-path "{project-root}/_bmad/config.yaml" --module-yaml assets/module.yaml --legacy-dir "{project-root}/_bmad"
   ```

   It returns `mode`, `installer_managed`, `cleanup_needed`, `has_core`, `version_transition`, and `defaults`. Narrate the mode:
   - **`update`**: the `suno:` section exists. Lead Confirm with the version transition.
   - **`fresh`**: `{project-root}/_bmad/` exists with no `suno:` section. This includes a v6.12 installer-managed project, whose per-module configs belong to the installer and only seed defaults.
   - **`standalone`**: no `{project-root}/_bmad/`. Say: "Setting up standalone — no BMad Method detected, using direct configuration."
   - **`migration`**: an earlier installer left per-module config and no installer manages `{project-root}/_bmad/` now. Its values become the defaults, and leftover module copies are cleaned up after setup.

If the invocation includes `--headless` / `-H` or "accept all defaults", load `references/headless.md` and follow it. If the user gave inline values (e.g. `user name is BMad, I speak Swahili`), map them to config keys, use defaults for the rest, skip prompting, and still show the full summary at the end.

## Collect Configuration

Show every value at once, with its default in brackets, so the user can reply once with only what they want to change (e.g. "change language to Swahili, rest are fine"). Never tell the user to "press enter" or "leave blank": in a chat interface they must type something to respond.

Take each default from `defaults` in the pre-pass output. It already applies the priority: existing config, then per-module config files, then `assets/module.yaml` defaults, with folder values shown without the `{project-root}/` prefix.

- **Core** (ask only when `has_core` is false): `user_name`, one language question that sets both `communication_language` and `document_output_language`, and `output_folder`.
- **Module**: each variable in `assets/module.yaml` with a `prompt` field, asked with its prompt.

## Write Files

Before the first write, echo the resolved project root once ("Installing into `<resolved path>`"), so a user who launched from the wrong directory can catch it.

Write a temp JSON file with the answers as `{"core": {...}, "module": {...}}`. Values keep the literal `{project-root}` token. Keys you leave out keep their current value; nothing is reset to a default behind the user's back.

**On an update, preview before the merge**, because the anti-zombie rewrite is what could revert a hand edit. Run the pre-pass again with `--answers {temp-file}`. Its `changes` list (`{file, key, old, new}`) is exactly what the merge will write. Show each as "current → new" (`new: null` is a key the module no longer uses) and let the user keep the current value; put kept values back in the answers file. A preview shown after the write would be a replay, not a preview.

Then run the three writes. They touch different files, so batch them in one message:

```bash
uv run scripts/merge-config.py --config-path "{project-root}/_bmad/config.yaml" --user-config-path "{project-root}/_bmad/config.user.yaml" --module-yaml assets/module.yaml --answers {temp-file} --legacy-dir "{project-root}/_bmad"
uv run scripts/merge-help-csv.py --target "{project-root}/_bmad/module-help.csv" --source assets/module-help.csv
uv run scripts/merge-help-csv.py --target "{project-root}/_bmad/suno/module-help.csv" --source assets/module-help.csv
```

Each prints JSON. If one exits non-zero, surface its error verbatim and stop. A corrupt existing config is reported, never overwritten. Run any script with `--help` for full usage.

## Create Output Directories

```bash
uv run scripts/merge-config.py --create-dirs --config-path "{project-root}/_bmad/config.yaml" --module-yaml assets/module.yaml --project-root "{project-root}"
```

It creates `output_folder` and the module's `directories:` on disk and returns `{created, existed}`. The stored values keep the token.

## Clean Up Legacy Copies

Run this only when the pre-pass said `cleanup_needed: true` (`migration` mode). It removes only copies of this module's own skills (`{project-root}/_bmad/suno/suno-*/`) that are installed in a platform skills folder and that no BMad installer tracks. Pass every skills folder the project has (`.claude/skills`, `.agents/skills`, `.gemini/skills`, `.cursor/skills`, and so on), each as a `--skills-dir`. Preview first:

```bash
uv run scripts/cleanup-legacy.py --bmad-dir "{project-root}/_bmad" --module-code suno --skills-dir "{project-root}/.claude/skills" --dry-run
```

If `would_remove` is empty, skip the rest. Otherwise show the paths and file counts, and run the same command without `--dry-run` once the user agrees. Copies listed in `unverified` (not found in any skills folder) are kept; mention them.

## Pipeline Guard (Optional)

Ask: "Want me to set up the pipeline guard? It makes sure Mac always runs the production skills before presenting a Suno package." If the user accepts, load `references/pipeline-guard.md` and follow it.

## Confirm

Summarize from the scripts' JSON: the mode, what went into each config file, help rows registered, folders created, cleanup (if any), and the guard. On an update, lead with the version transition and any kept-versus-changed values.

Close with the first step: "Next: say 'create a band profile', then 'create a song'." Then show the `module_greeting` from `assets/module.yaml`. On a **standalone** install, drop the greeting's multi-machine-sync paragraph: it needs the repo's top-level `scripts/` folder, which a standalone or marketplace install lacks.

## Outcome

Once `user_name` and `communication_language` are known, address the user by that name and communicate in that language for the rest of the session.
