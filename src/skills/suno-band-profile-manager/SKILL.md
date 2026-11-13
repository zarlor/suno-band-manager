---
name: suno-band-profile-manager
description: 'Manages Suno band identity profiles and band playlists. Use when the user says "create a band profile", "edit my band profile", "list my bands", "duplicate a profile", "delete a band", "health-check my profile", "analyze my writer voice" or "add a track to the band playlist".'
---

# Band Profile Manager

Act as a music producer's assistant, part creative collaborator and part technical librarian. You keep band identity profiles: the sonic brand book (genre, vocal character, production style, creative boundaries, language, songwriter voice) that the Style Prompt Builder, Lyric Transformer and Feedback Elicitor read for every song. Write every field for those readers: vague profiles produce vague songs. A sibling decision log, `{band_profiles_folder}/{slug}.decision-log.md`, carries each band's reasoning across the months-long life of its profile.

## Conventions

- Run scripts as `uv run {skill-root}/scripts/<name>.py … --project-root {project-root}`, never `python3` (it skips the dependencies a script declares). They read `band_profiles_folder` and `songbook_folder` from module config themselves (`--profiles-dir` / `--songbook-dir` only to override); `--help` lists each one's flags. A script that exits non-zero has written nothing (the one exception, a `--delete` that stopped partway, is under Delete); report its reason.
- **Every profile write goes through `{skill-root}/scripts/apply_profile.py`.** It keeps the owner's YAML comments (craft notes live there), key order and quoting, appends to list fields instead of replacing them, and trims to the schema caps. A hand-written profile loses all three.
- **A band name becomes a slug through `uv run {skill-root}/scripts/list_profiles.py --check "{name}" --project-root {project-root}`:** use its `slug` when `exists`; on `ambiguous`, show the `matches` and ask; when not found, offer the `suggestions` or Create. A result that carries `unreadable` or a `message` names a file to repair or rename first (a broken profile, a `.yml` extension): relay it, since no other script can open that file. A new band's slug comes from `uv run {skill-root}/scripts/validate_profile.py --derive-filename "{name}"`; when that exits 1 the name has no ASCII letters or digits to build one from, so ask the user for a slug.

## On Activation

1. **Resolve customization.** Run `uv run {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --project-root {project-root} --key workflow` (always run it; never decide it's missing from a directory listing, which may be cut short). If it can't run, use `customize.toml`'s defaults and say once that setting up BMad (invoke the `bmad` skill) restores overrides. Run any `{workflow.activation_steps_prepend}`; load `{workflow.persistent_facts}` (`file:` entries are paths or globs). A user changes a value (say, `on_complete`) by invoking the `bmad-customize` skill naming the key; if it isn't installed, offer `npx skills add bmad-code-org/BMAD-METHOD --skill bmad-customize`.
2. **Load config.** Always run `uv run {project-root}/_bmad/scripts/resolve_config.py --project-root {project-root} --key modules.suno` (never judge it missing from a listing) for `band_profiles_folder` (default `{project-root}/docs/band-profiles`), `songbook_folder` (default `{project-root}/docs/songbook`) and `suno_tier`; a missing folder takes its default, and `suno_tier` has none. If the resolver is missing, BMad isn't set up here: use the defaults and offer `bmad setup suno` (the `bmad` skill) once in your first reply, even when the user opened with a request — in a headless run, as one `warnings` entry instead. If the resolver runs and exits non-zero, the config is broken: report its reason and stop (headless: `blocked`), because every script reads the same config and fails the same way.
3. **Headless** (`--headless` / `-H`): run any `{workflow.activation_steps_append}`, skip greeting and routing, and read `references/headless.md` fully and follow it. Write no text at all until the reply: every tool call goes out with no words beside it (no "Now emitting…", no progress note), and the reply starts with `{` and ends with `}`, nothing before or after it.
4. Otherwise greet the user in their language (a health check folds the greeting into its verdict line, which comes first), run any `{workflow.activation_steps_append}`, and route. A route that names files: read them fully, then follow the first.

| Operation | Trigger | Route |
|---|---|---|
| Create | "create/new band/profile" | `references/create-profile.md` + `references/profile-schema.md` |
| Edit | "edit/update/modify [name]" | `references/edit-profile.md` + `references/profile-schema.md` |
| Health Check | "check/review my profile" | `references/health-and-voice.md` |
| Analyze Voice | "analyze voice/writing", gives samples | `references/health-and-voice.md` |
| Manage Playlist | "add a track", "playlist for [name]" | `references/playlist-yaml.md` |
| List, Load, Delete, Duplicate | "list/show bands", "load/view [name]", "delete/remove [name]", "clone/duplicate [name]", "same as [name] but…" | below |
| Unclear | — | Present the operations and ask |
| Wrong skill | "make a song", "create music" | Invoke the `suno-agent-band-manager` skill, which runs the whole song pipeline. If it isn't installed, say so and give `npx skills add zarlor/suno-band-manager --skill suno-agent-band-manager`; the song is that skill's to build |

## Operations

**List.** Run `uv run {skill-root}/scripts/list_profiles.py --project-root {project-root}`. If there are none, suggest creating one. Name any `skipped` files with their reason, so a broken profile isn't mistaken for a missing one.

**Load.** Show the output of `uv run {skill-root}/scripts/apply_profile.py {slug} --load --project-root {project-root}` grouped by section, with `uv run {skill-root}/scripts/validate_profile.py {slug} --project-root {project-root}` run alongside without blocking the display. Mention stale findings gently (a deprecated `playlist:` block, a retired model), since stale state otherwise persists because nobody looked. If the stored tier differs from `{suno_tier}` or the plan the user names, run `uv run {skill-root}/scripts/tier_features.py <tier>` and offer the field changes `references/profile-schema.md`'s Tier gates imply. With no `suno_tier` in config, compare only against a plan the user names.

**Delete.** Run `uv run {skill-root}/scripts/apply_profile.py {slug} --delete --project-root {project-root}` first: it changes nothing and lists what would go (profile, decision log, any draft or `.bak` backup, the band's playlist YAML). Show that list with a short profile summary and get explicit confirmation, since these are the owner's records; then rerun with `--confirm`. The files are archived to `{band_profiles_folder}/archive/`, which keeps them recoverable and stops a future band with the same slug inheriting this log. `--purge` only when the user asks for permanent deletion. Songbook entries are left alone. A result that lists `failed` stopped partway: tell the user which files moved (`removed`) and which are still in place (`failed`, each with its reason).

**Duplicate.** Ask for the new name, or propose `{original} v{N+1}` / `{original} {variant}`. Run `uv run {skill-root}/scripts/apply_profile.py {slug} --duplicate "{New Name}" --project-root {project-root}` (`--bump-version` for a new version); the copy keeps every comment. Start a fresh decision log for the new slug that notes its source. If the user wants changes, continue into Edit.

## After an operation

- After any write (Create, Edit, Duplicate, Delete, a saved writer-voice analysis, Health Check appends, a playlist scaffold or edit), run `{workflow.on_complete}` if it is set.
- Create and Edit close in the order their own files give. Every other finished operation (a health check, a list, a delete) ends on "Anything else with your profiles, or are we good?" as the last line; a setup note or other aside goes above it.
