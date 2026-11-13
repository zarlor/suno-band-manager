# Create Song — Headless

**Preference shard first.** If `{project-root}/docs/mac-preferences-packages.md` exists (the wake lists it under `voice_context.preference_shards`), read it in full before anything else here: it holds the owner's package, prompt, slider and pipeline rules. The pipeline guard blocks a package presented without it.

No greeting, no soft gates, no handoff checkpoint: the input is taken as confirmed. The Package Assembly Rule binds here too — the package comes from the pipeline skills, never from your own drafting. `references/headless.md` sets the result envelope and the write checks, and has already resolved the tier, the default exclusions and the active band where the input leaves them out.

## Input

```json
{
  "genre_mood": "required — genre, mood, vibe description",
  "source_text": "optional — poem or text to transform",
  "lyrics": "optional — finished lyrics to use as-is (with lyrics_ready: true)",
  "lyrics_ready": "optional — true skips the Lyric Transformer and uses `lyrics` unchanged",
  "band_profile": "optional — profile name to load",
  "tier": "optional — free|pro|premier",
  "model": "optional — a current model; default is the tier's",
  "exclusions": "optional — the caller's \"no X\" asks; the builder applies the profile's exclusion_defaults itself",
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

- No `genre_mood` and no band profile → `status: blocked` with the reason.
- `lyrics_ready: true` with `lyrics` → the lyrics go into the package unchanged and the transformer doesn't run.
- `lyrics_ready: true` with no `lyrics` → `status: blocked`: there is nothing to use as-is, and inventing lyrics is not this run's job.
- `lyrics` without `lyrics_ready` → treat them as `source_text` and transform them, and say so in `warnings`.
- Neither `source_text` nor `lyrics` → the package's lyrics are `auto` (Suno's auto-lyrics); an instrumental carries `instrumental`.

## Process

Scratch files go in the run's fresh `mktemp -d` folder. Each skill's whole JSON return is written there before you go on, and every value the package or the envelope carries is read from those files, never from a draft or from memory.

1. **suno-style-prompt-builder, headless — always.** Pass the builder's own field names:
   - `band_profile`, `tier` (always; the builder returns `blocked` with `missing: ["tier"]` without one), `model`, `genre_mood` (the input's), `reference_tracks`, `vocal_direction`, `instrumental`, `working_title`;
   - `requests`: the direction and specific asks ("acoustic only");
   - `creativity_mode`: the input's value, `balanced` when it gives none;
   - `exclusions`: only the caller's own "no X" asks and `memory/work/default-exclusions.md`. Leave the field out when there are none; an empty list is not the same thing. The builder reads the profile's `exclusion_defaults` itself and keeps those this prompt pulls toward;
   - `voice` / `persona` / `custom_model`.

   Write its return (the JSON its `--emit` step printed, whole) to `style.json`. A `blocked` return makes this run `blocked` with the builder's reason. Its `handoff_notes` go in the envelope's `warnings`, each prefixed "builder note: ", so no mid-build idea is lost. `reference_names` is not a package field.

2. **suno-lyric-transformer, headless — when there is source text, the song isn't instrumental and `lyrics_ready` isn't set.** Pass `text` (the `source_text`), `band_profile`, `direction`, `language`, the same `creativity_mode`, and `section_cues`: each section's instruction lifted from the style prompt in `style.json`, in the builder's words, left out when the prompt gives no per-section direction. This is why the builder runs first.

   Write its transform return (the contract's whole JSON object, `changes` and `decision_log` included) to `lyrics.json`. Keep its `decision_log` and `intentional_keeps` for the songbook entry.

## Output

The result envelope from `references/headless.md`, with a `package` object in Suno's Create-screen order:

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

The package is assembled, not retyped. Build it with a script (`jq`, or a few lines of Python run with `uv run`) that reads the two scratch files:

- `lyrics` ← `transformed_lyrics` from `lyrics.json` (the writer's spacing intact), the input's `lyrics` when `lyrics_ready`, or `auto` / `instrumental`.
- `style_prompt`, `char_count`, `exclude_styles` ← `style_prompt`, `style_prompt_chars`, `exclusion_prompt` in `style.json`.
- `settings` ← `model`, `vocal_gender`, `v6_options` and `sliders` in `style.json`. The sliders are `null` on Free.
- `title` ← `title_suggestion`.
- `wild_card` ← the builder's `wild_card`: `style_prompt`, `twist` as the `pitch`, `exclusion_prompt` as `exclude_styles`. It is `null` when `include_wild_card` is false.
- `voice` ← the input's `voice`, or `null`.
- `save_to` is the band's Suno workspace, which carries the band's name: copy the profile's `name` exactly, with no "workspace" suffix, or `null` with no band profile.
- The `package` carries exactly the keys above, in that order. Anything else the builder returned (rationales, slider reasoning) stays out of it; pass a note on in `warnings` if the owner needs it.
- Figures in the envelope's `summary` (character counts, slider values) are read from `style.json` too.
- When the transformer's `changes` include an added or split line, put its `changes`, as returned, in the envelope's `lyrics_changes`, so the caller sees every line that isn't the writer's.
- `artifact_path` stays `null` unless `save_to_songbook` is true. Then write the songbook entry as `references/songbook-entry.md` describes, after the path check in `references/headless.md`; a denied path, or a song with no band profile to file it under, is skipped and reported in `warnings`.
