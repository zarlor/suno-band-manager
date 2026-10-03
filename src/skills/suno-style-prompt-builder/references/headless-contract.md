# Headless Contract

The Band Manager agent calls this skill headless for every package, so the return carries everything its package needs. No greeting, no questions: make each call a user would have weighed in on, and log it in `decisions[]`.

## Modes

- **`--headless`** (or `-H`) — build a package. The inputs decide the shape: a named `band_profile` supplies the baseline and any other inputs override it; without a profile, `genre_mood` is required. `--headless:from-profile`, `--headless:custom`, and "`--headless` with a profile name" are accepted aliases of this one mode, kept for older callers and batch scripts.
- **`--headless:refine`** — apply structured adjustments to an existing prompt. It accepts the Feedback Elicitor's `adjustment_recommendations` shape, so that skill's output pipes straight in:
  ```json
  {
    "prompt": "string", "model": "string",
    "style_prompt": {"add": [], "remove": [], "reorder_notes": ""},
    "exclusions": {"add": [], "remove": []},
    "sliders": {"weirdness": "", "style_influence": ""},
    "model_suggestion": ""
  }
  ```
  `reorder_notes` is free-text guidance; apply it as a re-front-loading instruction. The legacy `adjustments.reorder: string[]` / `adjustments.replace[]` shape is still accepted.
- **`--headless:migrate`** — reformat `prompt` from `from_model` to `target_model` using the target's strategy. Read `references/retired-model-strategies.md` when either model is retired; a retired target can't generate, so migrate to v6 and log why.

Headless skips the reference-decomposition confirmation; record the skip in `decisions[]`.

## Build inputs

| Field | Notes |
|---|---|
| `band_profile` | Profile name, read from `{band_profiles_folder}/{name}.yaml` |
| `genre_mood` | Required when there's no profile |
| `model` | Default: the profile's `model_preference` if it names a current model, else v6 (v6-mini on Free). A retired model gets built for v6, logged |
| `tier` | `free` / `pro` / `premier`. Default: the profile's `tier`, else `{suno_tier}` |
| `creativity_mode` | `conservative` / `balanced` (default) / `experimental` |
| `reference_tracks`, `vocal_direction`, `requests` | Song direction; decompose references into descriptors |
| `exclusions` | The user's "no X" asks: each goes to Exclude Styles, with a positive in the prompt |
| `instrumental` | `true` drops vocal direction; `vocal_gender` is `""` and `lyrics_mode` is `Instrumental` |
| `voice` / `persona` / `custom_model` | Name (or `true`) of what is attached. A Voice drops gender and timbre descriptors and leaves `vocal_gender` `""` |
| `sliders` | User-supplied values are authoritative: pass them through |
| `lyrics_mode` | `Manual` / `Auto` / `Instrumental`, passed through. Default: `Instrumental` for an instrumental, else `Manual` |
| `working_title` | Seeds `title_suggestion` |
| `include_wild_card` | Default `true` for a build, `false` for refine and migrate |

## Rules that hold headless

- **Sliders are chosen per song,** from what each slider does and the song-type table in `references/safety-tables.md` — never from a band profile's stored values. Log each value with its reasoning.
- **Audio Influence follows its slot:** a Persona runs 15–25%, a Voice 35–95%. A value from the wrong range is an error.
- **Every exclude defends against drift from the current prompt's own descriptors.** Give each one a rationale naming the descriptor it defends against; drop any that defend against nothing.
- **Wild card:** see SKILL.md Step 4. It's on by default for a build.
- **Validate before emitting,** in every mode: pipe the package JSON to `uv run scripts/validate-prompt.py --stdin` (it checks the wild card too), fix what it flags, re-run, and put the report in `validation`. If the script can't run, do its checks by hand (see SKILL.md Step 5) and say so in `validation`.
- **Capture, don't drop:** lyric ideas, structure preferences or mix notes in the input go in `handoff_notes`.

## Success output

Fields run in the order the caller presents them: Voice → Lyrics → Style → Exclude → Settings (Model, then the Controls panel) → Title → Wild Card.

```json
{
  "status": "complete",
  "mode": "build",
  "voice_note": "Voice active: gender and timbre descriptors omitted",
  "lyrics_mode": "Manual",
  "style_prompt": "string",
  "style_prompt_chars": 612,
  "style_prompt_limit": 1000,
  "exclusion_prompt": "screaming vocals, steel guitar",
  "exclusion_rationale": [
    {"term": "screaming vocals", "defends_against": "'metal' in the genre head"},
    {"term": "steel guitar", "defends_against": "'southern rock' can pull slide/steel"}
  ],
  "model": "v6",
  "vocal_gender": "",
  "v6_options": {"variety": "Exact style", "max_mode": true, "duration": "Auto", "personalize": false},
  "sliders": {
    "weirdness": 55, "style_influence": 75,
    "audio_influence": 55, "audio_source": "voice",
    "reasoning": {"weirdness": "string", "style_influence": "string", "audio_influence": "string"}
  },
  "title_suggestion": "string",
  "wild_card": {
    "style_prompt": "string",
    "style_prompt_chars": 588,
    "twist": "subgenre shift: string",
    "reasoning": "one-line pitch",
    "model": "v6",
    "sliders": "same as primary",
    "exclusion_prompt": null,
    "exclusion_rationale": [],
    "alt_route": "Or run the primary prompt unchanged on v6-wild."
  },
  "validation": {"...": "validate-prompt.py report covering both prompts"},
  "handoff_notes": [{"for": "suno-lyric-transformer", "note": "string"}],
  "decisions": [
    {"call": "substituted 'progressive heavy groove' for 'metal'", "reason": "profile avoids screaming; 'metal' triggers harsh vocals"},
    {"call": "skipped decomposition confirmation", "reason": "headless — no interactive turn"}
  ]
}
```

- The Controls panel order, top to bottom, is Vocal Gender, Duration, Max Mode, Weirdness, Style Influence, Audio Influence (only with a Voice, Persona or audio attached), Variety, Personalize. Exclude Styles is the panel's first row.
- `voice_note` is `""` when nothing is attached. It also carries Persona and Custom Model handling.
- `vocal_gender` is `""` with a Voice or an instrumental. `audio_influence` and `audio_source` are `null` without audio attached. `sliders` is `null` on Free.
- `wild_card.exclusion_prompt` is `null` when it matches the primary's; give it (with a rationale) only when the wild card needs different excludes. `wild_card` is `null` when it's off.
- Refine and migrate return the same shape with `mode` set; fields the input didn't carry and the change didn't touch are `null`.

## Blocked output

When required inputs are missing, return `status: "blocked"` with the missing fields, a one-line reason, and any `decisions[]` so far:

```json
{"status": "blocked", "missing": ["genre_mood"], "reason": "No band profile and no genre_mood given.", "decisions": []}
```
