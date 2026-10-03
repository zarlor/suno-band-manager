# Headless Mode

Load this when the skill is invoked with `--headless` / `-H` or "accept all defaults". The flags are natural language the calling model passes, for example: *"install suno module -H, user name is BMad, language English, accept the guard default."*

## Run

Run end-to-end with no prompts:

- **Values.** Put only the values the caller gave into the answers JSON. `merge-config.py` fills every other key from the existing config, then the per-module config files, then the `assets/module.yaml` defaults. On an update this keeps hand-edited values without extra steps.
- **Update preview.** Still run the `--detect-mode --answers` preview before the merge. Record each entry in `changes` in `decisions[]` (for example `"headless update changed suno_tier free → pro (caller value)"`).
- **Cleanup.** Only when `cleanup_needed` is true. Run the dry run and record the paths it lists in `decisions[]`, then run it for real. Skip it otherwise.
- **Pipeline guard.** Configure it unless the caller opted out: run the AGENTS.md command, plus the Stop-hook command if `{project-root}/.claude/` exists (see `references/pipeline-guard.md`).

## Return

Emit, as the final line of your response, a single JSON object the calling process can parse:

```json
{"status": "complete", "config_path": "...", "user_config_path": "...", "module_code": "suno", "version": "2.4.1", "mode": "fresh", "guard_configured": true, "output_dirs": {"band_profiles_folder": "{project-root}/docs/band-profiles", "songbook_folder": "{project-root}/docs/songbook"}, "decisions": []}
```

- On `blocked`, add a one-line `reason` and still return the paths you know.
- On an update, `version` is `"<old> → <new>"`.
- `output_dirs` keeps the literal `{project-root}` token, so a chaining caller can wire the next skill without re-reading config.
- `decisions` lists every default chosen without the user (for example `"language defaulted to English"`, `"guard configured: AGENTS.md only (no .claude/)"`).
