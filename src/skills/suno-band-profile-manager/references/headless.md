# Headless Mode

`--headless` or `-H`: scripted profile management with no conversation. Skip the greeting and routing, but still load config and apply customization (activation steps, persistent facts, `on_complete`).

All scripts run as `uv run {skill-root}/scripts/<name>.py … --project-root {project-root}`. They read `band_profiles_folder` and `songbook_folder` from module config themselves. `{skill-root}/scripts/apply_profile.py` owns every profile write: it keeps YAML comments, key order and quoting, and never replaces a list without being told to.

**Names.** A `<name>` argument may be a slug or a band name. Resolve it with `uv run {skill-root}/scripts/list_profiles.py --check "<name>" --project-root {project-root}` and use the returned `slug`; `ambiguous` (with its `matches`) or not found (with any `suggestions` and `message`) → `blocked`, and the reason carries those lists.

**Inputs.** `create` reads the full profile YAML on stdin. `edit` reads a YAML mapping of field overrides on stdin, with nested keys merged by path. `append` reads one list entry (JSON or YAML) on stdin. Every other subcommand takes positional arguments only.

**Decision log.** Every assumption made without the user goes into `{band_profiles_folder}/{slug}.decision-log.md`: an inferred name or slug, inferred tier or model, an auto-trimmed style baseline, conflict resolutions, lint fixes. Create it on `create` and `duplicate`; on `edit` and `append`, add a new session heading.

**Work silently and finish everything:** send no message before the reply: every tool call goes out with no words beside it (no "Now emitting…", no progress note), and run no background commands: every tool call finishes before you return, so nothing reports after the reply. Scratch files go in a fresh `mktemp -d` folder, never a fixed `/tmp` name another run could share.

**Returns.** Every return is JSON with `status` (`complete` | `blocked`). **The reply is the JSON object alone:** no text before or after it and no code fence, so a script can parse it. Anything worth saying goes in a field (`reason`, `decision_log`). On `blocked`, add a one-line `reason`, and include `decision_log` only if one was written. Return the smallest set of paths the caller needs.

| Subcommand | Action | Returns |
|---|---|---|
| `--headless:create` | Follow "Create" below. | `{"status":"complete","profile_path","playlist_path","decision_log","validation":{"warnings":[...]}}` |
| `--headless:edit <name> [--append\|--replace]` | Follow "Edit" below. | `{"status","profile_path","fields_changed":[...],"decision_log","validation":{...}}` |
| `--headless:append <name> <field>` | `uv run {skill-root}/scripts/apply_profile.py {slug} --append <field> --append-json '<entry>' --project-root {project-root}`. Adds one entry and trims the oldest to the schema cap (`generation_history`: 10; `--max N` overrides, N at least 1). A wrong entry shape or an unknown field → `blocked`. | the script's JSON (`field`, `appended`, `trimmed`, `length`) plus `decision_log` |
| `--headless:duplicate <source> <new_name>` | `uv run {skill-root}/scripts/apply_profile.py {slug} --duplicate "<new_name>" --project-root {project-root}` (sets the copy's `name`, keeps comments), validate, write a fresh decision log for the new slug. | `{"status","profile_path","source","decision_log"}` |
| `--headless:validate <name>` | `uv run {skill-root}/scripts/validate_profile.py {slug} --project-root {project-root}` | the validator's JSON |
| `--headless:load <name>` | `uv run {skill-root}/scripts/apply_profile.py {slug} --load --project-root {project-root}` | the script's JSON, verbatim |
| `--headless:delete <name> [--purge]` | `uv run {skill-root}/scripts/apply_profile.py {slug} --delete --confirm --project-root {project-root}`. Calling this subcommand is the confirmation. It archives the profile, decision log, draft, `.bak` backup and playlist YAML to `{band_profiles_folder}/archive/{slug}-{stamp}/`, so the data can be recovered and a new band that reuses the slug does not inherit the old log. Pass `--purge` to delete them instead; only use it when the caller explicitly asks for it. Songbook entries are never touched. A result that lists `failed` stopped partway → `blocked`, the script's `error` as `reason`, with its `removed` and `failed` lists. | `{"status","removed":[...],"archive_dir","left_in_place":[...]}` |
| `--headless:scaffold-playlist <name> [--from-songbook]` | `uv run {skill-root}/scripts/scaffold_playlist.py {slug} [--from-songbook] --project-root {project-root}`. An existing playlist YAML is left untouched (`exists`). | the script's JSON (`status`, `path`, `album`, `tracks_seeded`, and after `--from-songbook` its `skipped` and `warnings`) |
| `--headless` (bare) | `uv run {skill-root}/scripts/list_profiles.py --project-root {project-root}`. Files it could not read come back under `skipped` with a reason. | the script's JSON |
| any other `--headless:<subcommand>` | Run nothing. | `{"status":"blocked","reason"}`, the reason listing the subcommands above |

## Create

`<draft>` is `{band_profiles_folder}/drafts/{slug}.yaml`. Each step feeds the next:

1. **Slug.** Take the `slug` from `uv run {skill-root}/scripts/validate_profile.py --derive-filename "<name>"`, the name being the YAML's `name`.
2. **Stage the YAML exactly as given:** `uv run {skill-root}/scripts/apply_profile.py {slug} --save --stage <draft> --project-root {project-root}`, the YAML on stdin through a quoted heredoc (`<<'YAML'`, never retyped into a file by hand).
3. **Validate the draft** with `uv run {skill-root}/scripts/validate_profile.py {slug} --staged <draft> --project-root {project-root}`, so the validator sees every conflict before you fix anything.
4. **Fix the auto-resolvable issues it reports,** then re-validate the draft after any fix:
   - A style baseline over the model's limit is trimmed with `uv run {skill-root}/scripts/apply_profile.py {slug} --set --profiles-dir {band_profiles_folder}/drafts --project-root {project-root}` (the new `style_baseline` on stdin). `--profiles-dir` points the edit at the draft, because the profile is not saved yet.
   - Free-tier sliders and studio preferences are dropped with `uv run {skill-root}/scripts/apply_profile.py --drop sliders,studio_preferences --in <draft>`, never a hand edit.
5. **Save:** `uv run {skill-root}/scripts/apply_profile.py {slug} --save --in <draft> --archive-existing-log --project-root {project-root}`. An earlier band's log for the slug is moved aside rather than appended to; name it in `warnings`.
6. **Playlist:** `uv run {skill-root}/scripts/scaffold_playlist.py {slug} --project-root {project-root}`.
7. **Write a fresh decision log.** It names the moved-aside file by path only, never its contents.
8. **Only then delete the draft,** and the `drafts/` folder if that empties it.

Rules that hold across the steps:

- **Every auto-fix is logged and listed.** Each goes in the decision log and in the return's `warnings`. A dropped key is logged with the values it held, the only place they survive.
- **Add no comments of your own to the profile.** Reasons go in the decision log.
- **Unresolvable issues → `blocked`, nothing saved, no log:** a missing `name` or one with no derivable slug (step 1 exits 1), `profile_exists` true at step 2, a missing `genre`, `mood` or `style_baseline`, an invalid `tier` or `model`.

## Edit

`<draft>` is `{band_profiles_folder}/drafts/{slug}.yaml`. The change is staged and validated before it touches the profile, so a failing edit is never saved:

1. **Stage:** `uv run {skill-root}/scripts/apply_profile.py {slug} --set --stage <draft> --project-root {project-root}` with the overrides on stdin. A list value that meets an existing non-empty list is refused unless the caller passes `--append` (add to it) or `--replace` (overwrite it); these map to `--lists append|replace`. The refusal → `blocked` with the script's error as `reason`.
2. **Validate the draft:** `uv run {skill-root}/scripts/validate_profile.py {slug} --staged <draft> --project-root {project-root}`. On `fail`, delete the draft and return `blocked` with the failing findings as `reason`; the profile is untouched.
3. **Apply:** the same `--set` call without `--stage`, then delete the draft.
