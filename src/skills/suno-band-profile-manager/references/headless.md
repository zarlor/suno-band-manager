# Headless Mode

`--headless` or `-H`: scripted profile management with no conversation. Skip the greeting and routing, but still load config and apply customization (activation steps, persistent facts, `on_complete`).

All scripts run as `uv run scripts/<name>.py … --project-root {project-root}`. They read `band_profiles_folder` and `songbook_folder` from module config themselves. `apply-profile.py` owns every profile write: it keeps YAML comments, key order and quoting, and never replaces a list without being told to. Never hand-write profile YAML.

**Inputs.** `create` reads the full profile YAML on stdin. `edit` reads a YAML mapping of field overrides on stdin, with nested keys merged by path. `append` reads one list entry (JSON or YAML) on stdin. Every other subcommand takes positional arguments only.

**Decision log.** Every assumption made without the user goes into `{band_profiles_folder}/{slug}.decision-log.md`: an inferred name or slug, inferred tier or model, an auto-trimmed style baseline, conflict resolutions, lint fixes. Create it on `create` and `duplicate`; on `edit` and `append`, add a new session heading.

**Returns.** Every return is JSON with `status` (`complete` | `blocked`). On `blocked`, add a one-line `reason`, and include `decision_log` only if one was written. Return the smallest set of paths the caller needs.

| Subcommand | Action | Returns |
|---|---|---|
| `--headless:create` | Stage the YAML to `{band_profiles_folder}/drafts/{slug}.yaml` and validate it. Fix auto-resolvable issues and log them: a style baseline over the model's limit is trimmed, free-tier sliders and studio preferences are dropped. Then `apply-profile.py --save --in <draft>`, `scaffold-playlist.py {slug}`, write the decision log and delete the draft. Unresolvable issues (missing `genre`/`mood`/`style_baseline`, invalid `tier`/`model`, profile already exists) → `blocked`, nothing saved, no log. | `{"status":"complete","profile_path","playlist_path","decision_log","validation":{"warnings":[...]}}` |
| `--headless:edit <name> [--append\|--replace]` | `apply-profile.py <name> --set` with the overrides on stdin, then validate. A list value that meets an existing non-empty list is refused unless the caller passes `--append` (add to it) or `--replace` (overwrite it); these map to `--lists append\|replace`. The refusal → `blocked` with the script's error as `reason`. | `{"status","profile_path","fields_changed":[...],"decision_log","validation":{...}}` |
| `--headless:append <name> <field>` | `apply-profile.py <name> --append <field> --append-json '<entry>'`. Adds one entry and trims the oldest to the schema cap (`generation_history`: 10; `--max N` overrides). A wrong entry shape → `blocked`. | the script's JSON (`field`, `appended`, `trimmed`, `length`) plus `decision_log` |
| `--headless:duplicate <source> <new_name>` | `apply-profile.py <source> --duplicate "<new_name>"` (sets the copy's `name`, keeps comments), validate, write a fresh decision log for the new slug. | `{"status","profile_path","source","decision_log"}` |
| `--headless:validate <name>` | `validate-profile.py {band_profiles_folder}/<name>.yaml --project-root {project-root}` | the validator's JSON |
| `--headless:load <name>` | `apply-profile.py <name> --load` | the script's JSON, verbatim |
| `--headless:delete <name> [--purge]` | `apply-profile.py <name> --delete --confirm`. Calling this subcommand is the confirmation. It archives the profile, decision log, draft and playlist YAML to `{band_profiles_folder}/archive/{slug}-{stamp}/`, so the data can be recovered and a new band that reuses the slug does not inherit the old log. Pass `--purge` to delete them instead; only use it when the caller explicitly asks for it. Songbook entries are never touched. | `{"status","removed":[...],"archive_dir","left_in_place":[...]}` |
| `--headless` (bare) | `list-profiles.py --project-root {project-root}` | the script's JSON |
