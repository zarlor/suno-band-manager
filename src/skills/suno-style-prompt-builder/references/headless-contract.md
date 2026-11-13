# Headless Contract

The Band Manager agent calls this skill headless for every package, so the return carries everything its package needs. No greeting, no questions: make each call a user would have weighed in on, and log it in `decisions[]`.

## Modes

- **`--headless`** (or `-H`) — build a package. The inputs decide the shape: a named `band_profile` supplies the baseline and any other inputs override it; without a profile, `genre_mood` is required.
- **`--headless:refine`** — apply structured adjustments to an existing prompt. It accepts the Feedback Elicitor's `adjustment_recommendations` shape, so that skill's output pipes straight in:
  ```json
  {
    "prompt": "string", "model": "string",
    "exclusion_prompt": "optional — the current Exclude Styles, which exclusions.remove edits",
    "tier": "optional — free | pro | premier; default as for a build",
    "band_profile": "optional — keeps the profile's guardrails in play",
    "style_prompt": {"add": [], "remove": [], "keep": [], "reorder_notes": ""},
    "exclusions": {"add": [], "remove": []},
    "sliders": {"weirdness": "", "style_influence": ""},
    "model_suggestion": ""
  }
  ```
  `style_prompt.keep` names the descriptors behind what the user liked: never remove or reword them. `reorder_notes` is free-text guidance; apply it as a re-front-loading instruction. A refine never adds a descriptor that pulls toward the drift it is fixing (fixing a choir drift, don't add "shout-chorus" or "gang" anything). Without `exclusion_prompt`, `exclusions.remove` has nothing to edit: return the new excludes from `exclusions.add` and say in `warnings` that removals need the current list.
- **`--headless:migrate`** — reformat `prompt` from `from_model` to `target_model` using the target's strategy. A retired target can't generate, so migrate to v6 and log why.

Headless skips the reference-decomposition confirmation; record the skip in `decisions[]`.

## Build inputs

| Field | Notes |
|---|---|
| `band_profile` | Profile name, read from `{band_profiles_folder}/{name}.yaml`. A file that is missing or won't parse as YAML is a `warnings` entry: build from `genre_mood` and the other inputs, or return `blocked` when they leave nothing to build from |
| `genre_mood` | Required when there's no profile |
| `model` | Default: the profile's `model_preference` if it names a current model, else v6 (v6-mini on Free). A retired model gets built for v6, logged |
| `tier` | `free` / `pro` / `premier`. Default: the profile's `tier`, else `{suno_tier}`. With none of the three, return `blocked` with `missing: ["tier"]`: the tier rules can't run without it and `--emit` refuses |
| `creativity_mode` | `conservative` / `balanced` (default) / `experimental`. Any other value is built as `balanced`, logged in `decisions[]` |
| `reference_tracks`, `vocal_direction`, `requests` | Song direction; decompose references into descriptors, and list every artist, band, album or song name they give in the package's `reference_names`, which the validator checks against both prompts and the excludes |
| `exclusions` | The user's "no X" asks: each goes to Exclude Styles, with a positive in the prompt |
| `instrumental` | `true` drops vocal direction; `vocal_gender` is `""` and `lyrics_mode` is `Instrumental` |
| `voice` / `persona` / `custom_model` | Name (or `true`) of what is attached. A Voice drops gender and timbre descriptors and leaves `vocal_gender` `""` |
| `sliders` | User-supplied values are authoritative: pass them through. On refine an empty slider value means unchanged: keep the current setting, since the feedback didn't touch it |
| `lyrics_mode` | `Manual` / `Auto` / `Instrumental`, passed through. Default: `Instrumental` for an instrumental, else `Manual` |
| `working_title` | Seeds `title_suggestion` |
| `include_wild_card` | Default `true` for a build, `false` for refine and migrate |

## Rules that hold headless

- **Each slider value carries its reasoning from this song** in `sliders.reasoning`, never a profile's stored value.
- **Each exclude carries a rationale** in `exclusion_rationale`, one entry per item (the validator flags an item that has none):
  - The reason quotes, in single quotes, the words in this prompt that cause the drift it defends against: the genre, instrument, era or arrangement cue responsible, not whatever nearby phrase happens to be there. For `key change`, "'final chorus lift' or 'builds to a final chorus swell'" are causes, because they describe the lift; 'hard stop after the final chorus' only names a section.
  - Drop any exclude that defends against nothing: a profile default with no cause in this prompt is dropped, not justified with a stretch such as 'autotune' from 'close to the mic'.
  - In refine, list each dropped exclude in `exclusions_removed` with its reason in `decisions[]`, so the caller sees what left.
  - The validator flags a reason whose quoted words aren't in the prompt: it is citing the profile or general model behaviour, which Suno never sees.
- **Wild card** is on by default for a build and follows the Wild Card step (Step 4), with two additions: any alternative twist you mention beside it stays in the band's genre family too, and it keeps the primary's tempo unless a `decisions[]` entry says why it moves. The anchoring profile genre is logged in `decisions[]`.
- **Validate as the Validate and Present step (Step 5) says, in every mode,** with one addition: each finding carries an `id`, and a medium finding you keep needs a `decisions[]` entry `{"finding": "<id>", "call": ..., "reason": ...}`; an entry with no call or no reason judges nothing.
- **Leave headroom:** aim the primary at about 850–950 characters on a 1,000 limit, so a refine has room to add without cutting.
- **Read the references one file per call** (they don't fit one shell output together). When you expect the package to pass, validate straight with `--emit`: a refusal prints the same report, so a separate plain run first is optional.
- **The last step is `--emit`:** pipe the complete success package (everything below except `validation`) to `uv run {skill-root}/scripts/validate_prompt.py --stdin --emit <<'PKG'` … `PKG`.
  - Exit 0 prints the finished return: your package with the validator's report as `validation` and the script's character counts (`style_prompt_chars`, `style_prompt_limit`, `wild_card.style_prompt_chars`), so never count characters or write `validation` yourself.
  - Exit 1 (`emit_refused`) names the findings still standing (a critical or high one, or a medium one with no `decisions[]` entry): fix or judge them and emit again.
  - If the script can't run at all, do the safety tables' hand checks and say so in `validation`.
  - Run `{workflow.on_complete}`, when it's set, after the emit that exits 0 and before the reply.
  - **Your reply is the printed JSON, exactly as printed:** copy it whole with its line breaks and indentation (don't minify or reformat it), and don't reword, trim or annotate any field (a finding's text included); a judgment you want to add goes in `decisions[]` before you emit.
- **Capture, don't drop:** lyric ideas, structure preferences or mix notes in the input go in `handoff_notes`.

## Success output

**The reply, success or blocked, is the JSON object alone and the only text you send,** so a script can parse it:

- Every tool call before it goes out with no words beside it (no "Now emitting…", no progress note).
- The reply starts with `{` and ends with `}`, with no code fence.
- Anything worth saying goes in a field the schema below has (`warnings`, `decisions`, `handoff_notes`); add no other fields.
- Run no background commands: every tool call finishes before you return, so nothing reports after the reply.
- Scratch files go in a fresh `mktemp -d` folder, never a fixed `/tmp` name another run could share.

Fields run in the order the caller presents them: Voice → Lyrics → Style → Exclude → Settings (Model, then the Controls panel) → Title → Wild Card.

```json
{
  "status": "complete",
  "mode": "build",
  "tier": "pro",
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
  "reference_names": ["string"],
  "validation": {"...": "written by validate_prompt.py --emit: its report covering both prompts"},
  "exclusions_removed": [],
  "warnings": [],
  "handoff_notes": [{"for": "suno-lyric-transformer", "note": "string"}],
  "decisions": [
    {"call": "substituted 'progressive heavy groove' for 'metal'", "reason": "profile avoids screaming; 'metal' triggers harsh vocals"},
    {"call": "skipped decomposition confirmation", "reason": "headless — no interactive turn"},
    {"finding": "3f9a1c2e", "call": "kept 6 excludes", "reason": "each defends a word in this prompt"}
  ]
}
```

- The Controls panel order, top to bottom, is Vocal Gender, Duration, Max Mode, Weirdness, Style Influence, Audio Influence (only with a Voice, Persona or audio attached), Variety, Personalize. Exclude Styles is the panel's first row.
- `vocal_gender` is lower-case `"male"`, `"female"` or `""`. `exclusions_removed` lists excludes a refine dropped (`[]` in a build). `warnings` carries anything the caller should know that isn't a decision: a refine run without the current `exclusion_prompt`, BMad not set up here (one entry), a missing profile.
- `reference_names` holds each artist, band, album or song name the request gave, and is `[]` when it gave none. The validator matches only the names listed there, so a name left out is a name it can't catch.
- `voice_note` is `""` when nothing is attached. It never tells the user to change a Voice's Skill Level, which is fixed at recording (a Voice not set to Professional is re-recorded, not adjusted). It also carries Persona and Custom Model handling.
- `sliders.reasoning` values are always strings: `""` for a slider that is `null` (no audio, so no `audio_influence`).
- `vocal_gender` is `""` with a Voice or an instrumental. `audio_influence` and `audio_source` are `null` without audio attached. `sliders` is `null` on Free.
- `wild_card.exclusion_prompt` is `null` only when every one of the primary's excludes also defends words in the wild card's own prompt; otherwise give the wild card its own excludes with their own rationale (the validator flags an inherited exclude whose quoted words the wild card lacks, and a scream trigger the wild card adds), and include it in the package you validate: the validator checks it like the primary's (`wild_card_exclusion_prompt` findings). `wild_card` is `null` when it's off.
- Refine and migrate return the same shape with `mode` set; fields the input didn't carry and the change didn't touch are `null`, except `lyrics_mode`, which keeps its default (`Manual`, or `Instrumental` for an instrumental).

## Blocked output

When required inputs are missing (no profile and no `genre_mood`, or no resolvable `tier`), return `status: "blocked"` with the missing fields, a one-line reason, and any `decisions[]` so far:

```json
{"status": "blocked", "missing": ["genre_mood"], "reason": "No band profile and no genre_mood given.", "decisions": []}
```
