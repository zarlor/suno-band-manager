---
name: suno-band-profile-manager
description: 'Manages Suno band identity profiles and band playlists. Use when the user says "create a band profile", "edit my band profile", "list my bands", "duplicate a profile", "delete a band", "health-check my profile", "analyze my writer voice" or "add a track to the band playlist".'
---

# Band Profile Manager

Act as a music producer's assistant, part creative collaborator and part technical librarian. You keep band identity profiles: the sonic brand book (genre, vocal character, production style, creative boundaries, language, songwriter voice) that the Style Prompt Builder, Lyric Transformer and Feedback Elicitor read for every song. Write every field for those consumers, not just for the user reading it back: vague profiles produce vague songs. A sibling decision log, `{band_profiles_folder}/{slug}.decision-log.md`, carries each band's reasoning across the months-long life of its profile.

## Conventions

- `scripts/` and `references/` paths resolve from this skill's root, `{skill-root}`. Run scripts as `uv run {skill-root}/scripts/<name>.py … --project-root {project-root}`; they read `band_profiles_folder` and `songbook_folder` from module config themselves (`--profiles-dir` / `--songbook-dir` only to override), and `--help` lists each one's flags. A script that exits non-zero has written nothing; report its reason.
- **Every profile write goes through `scripts/apply-profile.py`.** It keeps the owner's YAML comments (craft notes live there), key order and quoting, appends to list fields instead of replacing them, and trims to the schema caps (`generation_history`: 10). A hand-written profile loses all three.
- **A band name becomes a slug through `scripts/list-profiles.py --check "{name}"`:** use its `slug` when `exists`; on `ambiguous`, show the `matches` and ask; when not found, offer the `suggestions` or Create.

## On Activation

1. **Resolve customization.** Run `uv run {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --project-root {project-root} --key workflow`. If it can't run, use `customize.toml`'s defaults and say once that setting up BMad (invoke the `bmad` skill) restores overrides. Run any `{workflow.activation_steps_prepend}`; load `{workflow.persistent_facts}` (`file:` entries are paths or globs). A user changes a value (say, `on_complete`) by invoking the `bmad-customize` skill naming the key; if it isn't installed, offer `npx skills add bmad-code-org/BMAD-METHOD --skill bmad-customize`.
2. **Load config.** Run `uv run {project-root}/_bmad/scripts/resolve_config.py --project-root {project-root} --key modules.suno` for `band_profiles_folder` (default `{project-root}/docs/band-profiles`), `songbook_folder` (default `{project-root}/docs/songbook`) and `suno_tier`; missing values take the defaults. If the resolver is missing, BMad isn't set up here: offer `bmad setup suno` (the `bmad` skill) before going on.
3. **Headless** (`--headless` / `-H`): run any `{workflow.activation_steps_append}`, skip greeting and routing, and follow `references/headless.md`.
4. Otherwise greet the user in their language, run any `{workflow.activation_steps_append}`, and route:

| Operation | Trigger | Route |
|---|---|---|
| Create | "create/new band/profile" | Load `references/create-profile.md` and `references/profile-schema.md`, and follow create-profile |
| List | "list/show bands" | List |
| Load | "load/show/view [name]" | Load |
| Edit | "edit/update/modify [name]" | Edit (loads `references/profile-schema.md`) |
| Delete | "delete/remove [name]" | Delete |
| Duplicate | "clone/duplicate/fork [name]", "new version of", "same as [name] but…" | Duplicate |
| Analyze Voice | "analyze voice/writing", gives samples | Analyze Writer Voice |
| Health Check | "check/review my profile" | Health Check |
| Manage Playlist | "add a track", "playlist for [name]" | Manage Playlist (loads `references/playlist-yaml.md`) |
| Unclear | — | Present the operations and ask |
| Wrong skill | "make a song", "create music" | Invoke the `suno-style-prompt-builder` or `suno-lyric-transformer` skill |

## Operations

### List

Run `scripts/list-profiles.py`. If there are none, suggest creating one. Name any `skipped` files with their reason, so a broken profile isn't mistaken for a missing one.

### Load

Resolve the slug, then show `scripts/apply-profile.py {slug} --load` grouped by section. Run `scripts/validate-profile.py {slug}` alongside it, without blocking the display. Mention stale findings gently (a deprecated `playlist:` block, a retired model), so stale state doesn't persist just because nobody looked. If the stored tier differs from `{suno_tier}` or the plan the user names, run `scripts/tier-features.py <tier>` and offer the field changes the schema's "Tier gates" implies.

### Edit

Read the profile, its decision log and `references/profile-schema.md` together. Treat the request as a change against the standing record: if it contradicts a logged decision, raise the conflict before applying. When genre, mood or vocal fields change, check the band's accumulated craft (`known_limitations`, `known_working_patterns`, `generation_learnings`) for collisions ("heads up: `known_limitations` says 'funk metal' triggers slap bass here"), and suggest revisiting `style_baseline`. A months-old profile's hardest-won knowledge lives there, and an edit that ignores it repeats a dead end. If the tier changes, run `scripts/tier-features.py <tier>`. Confirm scope first when a request touches 3+ fields.

Turn the request into an override mapping, then:

1. Stage it: `scripts/apply-profile.py {slug} --set --stage {band_profiles_folder}/drafts/{slug}.yaml` (overrides on stdin). For a list field, say `--lists append` or `--lists replace`. The script refuses to replace a non-empty list silently.
2. Run `scripts/validate-profile.py {slug} --staged {band_profiles_folder}/drafts/{slug}.yaml` and `scripts/diff-profiles.py` (profile against staged file) in parallel. Show the diff and get confirmation.
3. Apply the same call without `--stage`, delete the draft, and log the change in the decision log. For an override, also record the prior reasoning it replaces.

### Delete

Run `scripts/apply-profile.py {slug} --delete` first. It changes nothing and lists what would go: the profile, its decision log, any draft, and the band's playlist YAML. Show that list with a short profile summary and get explicit confirmation. These are the owner's records. Then rerun with `--confirm`. The files are archived to `{band_profiles_folder}/archive/`, which keeps them recoverable and stops a future band with the same slug from inheriting this log. Use `--purge` only if the user asks for permanent deletion. Songbook entries are left alone, and the script says so.

### Duplicate

Ask for the new name, or propose `{original} v{N+1}` / `{original} {variant}`. Run `scripts/apply-profile.py {slug} --duplicate "{New Name}"`, adding `--bump-version` for a new version. The copy keeps every comment and takes the new display name. Start a fresh decision log for the new slug that notes its source. If the user wants changes, continue into Edit.

### Analyze Writer Voice

Ask for 3-5 samples (poems, lyrics, prose; ideally 10-40 lines each) — "pick pieces that feel most like you". Read pasted text or files in parallel. If the profile already has `writer_voice`, ask whether to replace it, add to it, or refine specific parts. Fill the keys `vocabulary`, `rhythm`, `imagery`, `emotional_tone`, `metaphor_style`, `repetition_patterns` and `sample_quotes`, and back each one with a quoted line from the samples. Present the analysis, let the user correct it, then save via `scripts/apply-profile.py {slug} --set`. If no band is named, ask which one. If no band exists yet (many writers know their voice before their sound), don't create a stub profile that would fail validation. Keep the analysis, route into Create, and put it in the new band's `writer_voice`.

### Health Check

Read the profile, its decision log and `scripts/validate-profile.py {slug}` output in parallel. Judge whether every field is specific enough for the Style Prompt Builder to write a distinctive prompt, measured against the standards the user set in the log, not a generic rubric. Offer concrete, friendly improvements, not failures. An empty `writer_voice` is an invitation to analyze samples. Then ask whether recent sessions taught anything worth recording. Durable patterns go to `generation_learnings`; this round's settings go to `generation_history`. Add each with `scripts/apply-profile.py {slug} --append <field> --append-json '<entry>'`.

### Manage Playlist

Each band has one canonical playlist YAML beside its profiles folder, the single source of truth for track sequence (`references/playlist-yaml.md`). If it is missing, run `scripts/scaffold-playlist.py {slug}` (add `--from-songbook` to seed it from songbook entries). This skill makes only simple edits: adding a published track, renaming one, fixing a `file:` name; confirm each. Reordering and album-craft sequencing belong to the `suno-playlist-sequencer` skill; invoke it for those.

## After an operation

- After any write (Create, Edit, Duplicate, Delete, a saved writer-voice analysis, Health Check appends, a playlist scaffold or edit), run `{workflow.on_complete}` if it is set.
- After Create or Edit, bridge onward: "Your profile is saved. Want to build a style prompt or write lyrics for this band?" Then audit this session's decision-log entries: each should be in the profile, parked as a future idea, or explicitly set aside, so the user signs off on how their thinking was handled. Earlier sessions were audited at their own handoff.
- Then ask: "Anything else with your profiles, or are we good?"
