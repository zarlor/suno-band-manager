# Access Boundaries for Mac

> Dominion contract. Loaded FIRST on every rebirth, before any file op. This is
> the seed shape; it grows as the project's companion-file constellation grows.
> The proportionate write discipline below is load-bearing — keep it.

## Read Access
- `docs/voice-context-{username}.md` — voice file (loaded on activation per SKILL.md)
- `docs/band-profiles/` — all band profile YAMLs
- `docs/songbook/` — all song packages
- `docs/wip-*.md` — works in progress
- `docs/*-playlist*.md`, `docs/audio-analysis-reference.md`, `docs/*-genre-coverage.md`, and the companion files listed in the voice file's Companion Files table
- `{project_root}/_bmad/_memory/band-manager-sidecar/` — own memory

## Write Access
- `{project_root}/_bmad/_memory/band-manager-sidecar/` — own memory only
- WIP files (`docs/wip-*.md`) when capturing creative fragments
- `docs/voice-context-{username}.md` — **Mac maintains this file.** Discipline is PROPORTIONATE, not blanket:
  - **Routine sync edits** (Companion Files table entries, catalog counts, file-path/status cross-references) — just make them, in the same write batch as the triggering change, per creed.md "Sync at the point of change." No need to ask.
  - **Substantive identity/voice additions** (new "who the owner is as a writer/creator" material) — write them in the owner's words (quote, don't paraphrase-promote — see Hedge Preservation), AND surface exactly what was added in the same turn so the owner can correct or cut it. Do the work; elevate the questionable for review. Do NOT withhold the edit and "just flag it" — that is the overreaction this rule corrects.
  - The owner approves content by seeing it and reacting, not by pre-authorizing each edit (per activation.md "Updating: propose specific additions; the owner approves what goes in" — proportionate, not a gate that blocks the work).
- `docs/mac-preferences.md` — append durable behavioral corrections in the same turn they land (per the file's own append protocol + activation.md 6b)
- Other companion docs Mac maintains — edit when the triggering change requires it, per sync-at-point-of-change
- Band profile writes happen via the `suno-band-profile-manager` skill, not directly
- Songbook writes happen via the create-song / refine-song workflows, not directly

## Deny Zones
- `src/` — module source code
- `scripts/` — module utility scripts
- `{project_root}/_bmad/config*.yaml` — module config files
- `.claude/`, `.gemini/`, `.agents/`, `.claude-plugin/` — LLM CLI integration directories
- `tests/` — test files
- All other directories outside the lists above

## Notes
- The voice context file (`docs/voice-context-{username}.md`) is loaded on every activation per the SKILL.md activation protocol — it must be in read access AND write access. An earlier version of this file omitted it from write access, which Mac over-read as a prohibition and self-restricted to "flag, don't edit" — contradicting activation.md, creed.md, and the create-song/refine-song sync rules, all of which expect Mac to maintain the voice file. The fix is the proportionate discipline above: elevate questionable additions for review, don't blanket-disallow the work. This is the recurring failure pattern to watch for — over-reading a narrow/omitted constraint into an over-broad self-restriction.
- The canonical reference docs (SUNO-REFERENCE.md, USAGE.md, etc.) live at `{skill-root}/references/` — these are skill source code; read them via the skill protocol, not directly.
