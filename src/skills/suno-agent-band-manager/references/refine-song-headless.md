---
name: refine-song-headless
description: Refine Song with no one at the keyboard — diagnose feedback and return the package delta.
---

# Refine Song — Headless

**Preference shard first.** If `{project-root}/docs/mac-preferences-packages.md` exists (the wake lists it under `voice_context.preference_shards`), read it in full before anything else here: it holds the owner's package, prompt, slider and pipeline rules. The pipeline guard blocks a package presented without it.

No handoff checkpoints, no "want me to rebuild…?" offers, no conversational loop: the input is taken as confirmed. The Package Assembly Rule binds here too — load the sanctum's `memory/disciplines/package-assembly.md` — and `references/headless.md` sets the result envelope and the write checks.

**Input contract:**
```json
{
  "song_ref": "optional — songbook path or title of the song being refined; if omitted, the caller must supply original_style_prompt/original_lyrics",
  "original_style_prompt": "optional — the prompt being refined (looked up from song_ref if absent)",
  "original_lyrics": "optional — the lyrics being refined",
  "feedback": "required — the listener reaction / adjustment request to act on",
  "model": "optional — model the song used (inferred from tier/profile if absent)",
  "tier": "optional — free|pro|premier (else memory/owner/preferences.md)",
  "band_profile": "optional — profile name for voice constraints",
  "creativity_mode": "optional — conservative|balanced|experimental, default balanced"
}
```

**Process.** Resolve `song_ref` with `uv run {skill-root}/scripts/songbook-catalog.py "{project-root}" --title "<song_ref>" --full-prompts --format json`. Read `memory/owner/preferences.md` for a missing tier (warn and assume Free if unresolved). Invoke the suno-feedback-elicitor skill headless with the feedback and context; it returns `adjustment_recommendations`. Route them on:

- style prompt or exclusion changes → the suno-style-prompt-builder skill, `--headless:refine`, passing the recommendations straight through;
- lyric changes → the suno-lyric-transformer skill, `--headless:refine`, with the current lyrics as `source_lyrics` and `song_path` when the song has a songbook entry;
- slider or setting changes → no skill re-run; they go into the delta as they are.

**Output:** the refined package delta as structured JSON (only what changed — style prompt, exclusions, lyrics, settings — under the create-song `package` field names: `style_prompt`, `char_count`, `exclude_styles`, `lyrics`, `settings`), inside the result envelope from `references/headless.md`. A refinement that would overwrite a *published* songbook entry is a Law-3-gated write: stage it and report it in `warnings` rather than applying it. Any other durable write passes the path check first; a denied path is skipped and reported. Missing `feedback`, or no original prompt or lyrics to resolve → `status: blocked` with the reason.
