---
name: create-song-headless
description: Create Song with no one at the keyboard — input contract, pipeline run and package result.
---

# Create Song — Headless

**Preference shard first.** If `{project-root}/docs/mac-preferences-packages.md` exists (the wake lists it under `voice_context.preference_shards`), read it in full before anything else here: it holds the owner's package, prompt, slider and pipeline rules. The pipeline guard blocks a package presented without it.

No greeting, no soft gates, no handoff checkpoint: the input is taken as confirmed. The Package Assembly Rule binds here too — the package comes from the pipeline skills, never from your own drafting — and `references/headless.md` sets the result envelope and the write checks.

**Input contract:**
```json
{
  "genre_mood": "required — genre, mood, vibe description",
  "source_text": "optional — poem or text to transform",
  "lyrics": "optional — finished lyrics to use as-is (with lyrics_ready: true)",
  "lyrics_ready": "optional — true skips the Lyric Transformer and uses `lyrics` unchanged",
  "band_profile": "optional — profile name to load",
  "tier": "optional — free|pro|premier (else memory/owner/preferences.md)",
  "model": "optional — default v6 on Pro/Premier, v6-mini on Free (also: v6-wild)",
  "exclusions": "optional — the caller's \"no X\" asks (else memory/work/default-exclusions.md); the builder applies the profile's exclusion_defaults itself",
  "voice": "optional — Voice name attached in Suno",
  "persona": "optional — Persona name",
  "custom_model": "optional — Custom Model name",
  "creativity_mode": "optional — conservative|balanced|experimental, default balanced",
  "instrumental": "optional — true for instrumental-only",
  "language": "optional — default English",
  "include_wild_card": "optional — default true",
  "save_to_songbook": "optional — default false"
}
```

**Process.** Fill what the input leaves out from `memory/owner/preferences.md`, `memory/work/default-exclusions.md` and `memory/bands/active.md`; an unresolved tier builds for Free and says so in `warnings`. Then run the pipeline:

- **suno-lyric-transformer, headless** — when there is source text, the song isn't instrumental and `lyrics_ready` isn't set. Pass `text` (the `source_text`), `band_profile`, `direction`, `language` and `creativity_mode`. Its transform return (the contract's whole JSON object, `changes` and `decision_log` included) is written to the scratch folder as `lyrics.json` before you go on; read `transformed_lyrics` (the writer's spacing intact) and `changes` from that file, never from a draft. Keep its `decision_log` and `intentional_keeps` for the songbook entry.
- **suno-style-prompt-builder, headless** — always. Pass the builder's own field names: `band_profile`, `tier`, `model`, `genre_mood`, `reference_tracks`, `vocal_direction`, `requests` (the direction and specific asks, "acoustic only"), `creativity_mode` (same mapping as Step 3), `exclusions` (only the owner's own "no X" asks and `memory/work/default-exclusions.md`; the builder reads the profile's `exclusion_defaults` itself and keeps those this prompt pulls toward), `voice` / `persona` / `custom_model`, `instrumental` and `working_title` (`genre_mood` is the input's; leave `exclusions` out rather than pass `[]`). Its success JSON carries the style prompt and character count, exclusions, settings, title and wild card; its `handoff_notes` go in the envelope's `warnings`, each prefixed "builder note: ", so no mid-build idea is lost.

Without source text the lyrics are `auto` (Suno's auto-lyrics); instrumental songs carry `instrumental`.

**Output:** the result envelope from `references/headless.md` with a `package` object in Suno's Create-screen order:

```json
{
  "package": {
    "voice": "name or null",
    "lyrics": "transformed lyrics, 'auto' for Suno auto-lyrics, or 'instrumental'",
    "style_prompt": "string",
    "char_count": 612,
    "exclude_styles": "comma-separated, or null on Free",
    "settings": {
      "model": "v6", "vocal_gender": "", "duration": "Auto", "max_mode": true,
      "weirdness": 55, "style_influence": 75, "audio_influence": null,
      "variety": "Exact style", "personalize": false
    },
    "title": "string",
    "save_to": "the band profile's `name`, exactly, or null without a profile",
    "wild_card": {"style_prompt": "string", "pitch": "one line", "exclude_styles": null}
  }
}
```

**The package is assembled, not retyped:** read `style_prompt`, `char_count` (`style_prompt_chars`), `exclude_styles` (`exclusion_prompt`), the settings (`model`, `vocal_gender`, `v6_options`, `sliders`) and `wild_card` (`style_prompt`, `twist` as the pitch, `exclusion_prompt`) straight from the builder's `--emit` JSON programmatically from that file, never typing a value. The `package` carries exactly the keys above, in that order; anything else the builder returned (rationales, slider reasoning) stays out of it — pass a note on in `warnings` if the owner needs it. Figures in the envelope's `summary` (character counts, slider values) are read from the builder's emitted JSON too, never typed. `save_to` is the band's Suno workspace, which carries the band's name: copy the profile's `name` exactly (no "workspace" suffix), or `null` with no band profile. When the transformer's `changes` include an added or split line, list them in the envelope's `lyrics_changes` (its `changes`, as returned) so the caller sees every line that isn't the writer's. Sliders are `null` on Free. `wild_card` is `null` when `include_wild_card` is false. `artifact_path` stays `null` unless `save_to_songbook` is true; that write passes the path check in `references/headless.md` first, and a denied path is skipped and reported in `warnings`. Missing `genre_mood` with no band profile → `status: blocked` with the reason.
