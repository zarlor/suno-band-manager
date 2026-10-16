# Band Profile Schema

A profile is `{band_profiles_folder}/{slug}.yaml`, the slug being the kebab-case form of `name`. Each field's facts live in its comment below; `scripts/validate-profile.py` enforces the structure (required fields, enums, caps, tier and Voice consistency, filename = slug, the band's playlist YAML) and every finding carries its fix, so judge what it cannot: whether each field is specific enough for its reader.

```yaml
# Band Profile — {band_name}
# Created: {date}
# Last modified: {date}

name: "Band Name Here"         # required; the display name, and the source of the filename slug
version: 1                     # increment on a major sound evolution
instrumental: false            # true makes the vocal block optional

# Sound Identity
genre: "indie folk-rock with electronic textures"   # required
mood: "melancholic but hopeful, atmospheric"         # required
language: "English"            # lyrics and style cues; default English
reference_tracks:              # "sounds like" lines
  - "Bon Iver meets Radiohead"

# Model & Tier (see Tier gates)
model_preference: "v6"         # v6 | v6-wild | v6-mini; a retired pre-v6 name draws a validator warning, so suggest v6
tier: "pro"                    # free | pro | premier

# Style baseline: max 1,000 chars on the v6 family. The limits are community-attested,
# not Suno docs: enforce them, don't cite them as platform documentation. The first
# ~200 chars influence generation most, so genre, mood and vocal direction go there.
style_baseline: >
  Indie folk-rock with electronic textures, atmospheric and layered.
  Warm analog synths underneath acoustic guitar, subtle ambient pads.
exclusion_defaults:            # concise, specific; 5 at most
  - "no autotune"

# Vocal direction (required unless instrumental: true)
vocal:
  gender: "male"               # male | female | nonbinary | any. Leave empty when voice_id is set
  tone: "warm, breathy"        # required; evocative, not "male vocals"
  delivery: "intimate, conversational"   # required
  energy: "restrained, building"         # required
  diction: ""                  # optional refinement
  persona_reference: ""        # Suno Persona name. Personas still work; they live inside the Voices menu
  persona_source_song: ""      # the song the Persona came from, so it can be recreated
  # NOTE: a Persona pulls the sound toward the era of its source song; an era-specific
  # piece wants no Persona or one made from an era-appropriate song.
  voice_id: ""                 # Suno Voice id (a clone). Distinct from a Persona (style capture); set the one the band uses

# Several cloned Voices for different track types: the source of truth for per-track
# Voice choice; vocal.voice_id stays the primary and should be one of these. Each Voice
# is one stable character; variety lives across Voices, not within one recording.
voices:
  # - voice_id: "<Suno Voice id>"   # required
  #   label: "Ballad Intimate"
  #   use_case: "tender, stripped-back tracks"   # without it, the entry is just a vocal.voice_id

creativity_default: "balanced"     # conservative | balanced | experimental

sliders:                           # Pro/Premier
  weirdness: 50                    # 0-100
  style_influence: 50              # 0-100
  audio_influence: null            # 0-100, only with uploaded audio; proven per-Voice values go in generation_learnings

studio_preferences:                # Premier
  bpm: null                        # a number
  key: ""                          # e.g. "C minor"
  time_signature: ""               # e.g. "3/4"

custom_model_id: ""                # Pro/Premier; up to 3 per account, trained on 6+ original tracks, now on v6
custom_model_notes: ""             # what it was trained on and the production style it brings

writer_voice:                      # optional; filled by Analyze Writer Voice, each key backed by a quoted line
  vocabulary: ""
  rhythm: ""
  imagery: ""
  emotional_tone: ""
  metaphor_style: ""
  repetition_patterns: ""
  sample_quotes: []

# The band's institutional memory (lists of strings)
known_working_patterns: []         # exact prompt wording that reliably nails the identity
known_limitations: []              # what Suno can't do for this sound, e.g. "'funk metal' triggers slap bass, not fingerstyle"
generation_learnings: []           # durable, cross-song: "'sludge' triggers harsh vocals; say 'thick, heavy'"

generation_history: []             # per-generation snapshots, max 10 (appends trim the oldest)
#   - date: "2026-03-19"
#     style_prompt: "..."
#     model: "v6"
#     sliders: { weirdness: 65, style_influence: 55 }
#     note: "nailed the vocal tone"
```

## Tier gates

The plan decides which fields a profile may carry. Feature facts (credits, downloads, stems, Studio) come from `scripts/tier-features.py <tier>`; this table is only their field consequences.

| Tier | `model_preference` | Fields that apply |
|---|---|---|
| free | `v6-mini` only | No `sliders`, `voice_id`/`voices`, `persona_reference`, `custom_model_id` or `studio_preferences`. Exclusions are carried as positive phrasing by the Style Prompt Builder |
| pro | `v6` (default) or `v6-wild` for exploration; `v6-mini` allowed | `sliders`, Personas, Voices, Custom Models |
| premier | as Pro | Everything Pro has, plus `studio_preferences` |

## A band with a Voice

A Voice carries vocal character (gender, timbre, lilt, mic artifacts), not genre. With `voice_id` set, keep gender and timbre words out of `style_baseline` and `vocal.tone` (which then says how the voice is used — "hushed, close" — not how it sounds — "smoky, husky") and leave `vocal.gender` empty, since a stored gender invites them back and they fight the captured character; delivery words stay. Spend the baseline on arrangement: instrumentation, genre, production, dynamics. A clean Voice can't scream, so a harsh-vocal exclusion wastes Exclude Styles space; suggest production and genre guards instead. A stored `style_influence` around 65 suits a Voice used across genres, so the prompt leads the band.

## Who reads what

- **Style Prompt Builder:** `style_baseline`, `reference_tracks`, `vocal`, `voices`, `exclusion_defaults`, `sliders`, `creativity_default`, `model_preference`, `language`, `instrumental`, `custom_model_*`.
- **Lyric Transformer:** `writer_voice`, `language`.
- **Feedback Elicitor:** `style_baseline`, `sliders`, `model_preference`. It writes through this skill's `--headless:append`: each round's snapshot to `generation_history`, and any pattern that snapshot taught to `generation_learnings`. The learnings (with `known_working_patterns` and `known_limitations`) are the band's distilled memory; the history is the changelog they were distilled from.
