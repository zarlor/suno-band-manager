# Style Prompt Builder

The Style Prompt Builder generates model-aware Suno style prompts optimized for the user's chosen model tier, blending band profile baselines with per-song creative direction. It writes for the current v6 family (ordered production direction) and can migrate prompts written for the retired models, and it produces a complete package: style prompt, Exclude Styles, Controls settings, a title suggestion, and a wild-card variant. The skill enforces the 1,000-character limit (200 for the retired v4 Pro) and prioritizes the critical first 200 characters where Suno's attention is strongest.

## When to Use Directly vs. Through Mac

Use this skill directly when you already have a band profile or clear musical direction and just need a style prompt built. Use Mac (the orchestrating agent) when style prompt creation is part of a larger workflow that includes profile setup, lyric transformation, or post-generation feedback refinement.

## Operations

### Interactive Mode (default)

1. **Gather Inputs** — Collects song direction, band profile, model selection, creativity mode (conservative/balanced/experimental), and specific requests
2. **Build Style Prompt** — Constructs model-specific prompt with critical zone awareness; decomposes reference tracks into concrete descriptors (never puts artist names in prompts)
3. **Build Exclusion Prompt** — Generates "Exclude Styles" content from profile defaults, user requests, and genre inference
4. **Controls** — Weirdness and Style Influence chosen per song, Audio Influence by slot (Persona or Voice), Variety, Max Mode, Duration, Personalize, Vocal Gender
5. **Wild Card Variant** — A genre or subgenre shift inside the band's core sound, on the primary's model and sliders
6. **Validate & Present** — Validation of both prompts, copy-ready output blocks, refinement loop

### Headless Mode (`--headless` or `-H`)

- `--headless` — Build a package from the inputs given: a band profile's baseline plus any overrides, or `genre_mood` alone without a profile (`--headless:from-profile` and `--headless:custom` are accepted aliases)
- `--headless:refine` — Apply structured adjustments from the Feedback Elicitor to an existing prompt
- `--headless:migrate` — Reformat an existing prompt from one model's style to another

The input and output contract is in `references/headless-contract.md`.

## Scripts

| Script | Description |
|--------|-------------|
| `validate-prompt.py` | Validates the primary and wild-card style prompts (model-specific limits, critical zone, structure, scream/keyboard/crowd-noise triggers, inline negatives), the Exclude Styles text, and the Audio Influence range. Takes the package as JSON on stdin |

## Example Invocation

```
# Interactive
"Build a style prompt for my midnight-echoes profile"
"Create a Suno prompt for a dreamy indie folk song on v6"

# Headless
--headless --profile midnight-echoes
--headless --model v6 --genre_mood "dreamy, introspective indie folk"
--headless:migrate --prompt "warm indie rock..." --from "v5.5 Pro" --to v6
```

## Creativity Modes

| Mode | Behavior | Weirdness Range |
|------|----------|-----------------|
| **Conservative** | Genre-pure descriptors, proven combinations | 20-35 |
| **Balanced** (default) | Standard approach, some distinctive touches | 40-60 |
| **Experimental** | Unexpected fusions, unusual descriptors | 65-85 |

## Supported Models

| Model | Prompt Style | Character Limit |
|-------|-------------|-----------------|
| **v6 / v6-wild / v6-mini** (current) | Ordered production direction — each instrument's job per section, positive text only (PREVIEW) | 1,000 |
| v4.5-all / v4.5 Pro / v4.5+ Pro (retired) | Conversational, flowing sentences | 1,000 |
| v5 Pro / v5.5 Pro (retired) | Crisp, 5-8 film-brief descriptors | 1,000 |
| v4 Pro (retired) | Simple, straightforward descriptors | 200 |

**Character-limit provenance (2026-08-13):** these limits are community-attested and validated by our own use — **no official Suno documentation states them.** Keep enforcing them; don't present them as documented platform facts. Suno has also announced that current models will be retired when the next model ships, with no versions or dates published.

## Part of the Suno Band Manager Module

This skill is part of the Suno Band Manager module and works with any LLM CLI supporting the [Agent Skills](https://agentskills.io) standard. For the full guided experience, invoke Mac — the orchestrating agent — instead of using this skill directly.
