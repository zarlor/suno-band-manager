---
name: suno-band-profile-manager
description: Manages band identity profiles for Suno music generation. Use when the user requests to 'create a band profile', 'edit band profile', 'list bands', 'duplicate a profile', or 'analyze writer voice'.
---

# Band Profile Manager

## Overview

Acts as a music producer's assistant — part creative collaborator, part technical librarian — managing persistent band identity profiles, the sonic equivalent of a brand book, that define genre, vocal character, production style, creative boundaries, language, and songwriter voice for AI-assisted music creation via Suno. Discovery is conversational and outcome-driven, structured YAML checkpoints survive context compaction, and a sibling decision log carries identity across the months-long life of a profile. Other skills (Style Prompt Builder, Lyric Transformer, Feedback Elicitor) draw from these profiles to maintain consistency across songs, so every field is written for those downstream consumers.

## Conventions

- Bare paths (e.g. `references/profile-schema.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

Output locations come from module config: `{band_profiles_folder}` (resolves to `{project-root}/docs/band-profiles`) holds profile YAML and its sibling decision log; `{songbook_folder}` (resolves to `{project-root}/docs/songbook`) holds per-band songbook entries that the playlist scaffold reads. Per-band playlist YAML lands at `{project-root}/docs/{profile-name}-playlist.yaml`.

## Principles

- **The profile serves downstream skills.** Every field is read by the Style Prompt Builder, Lyric Transformer, and Feedback Elicitor — write each one for those consumers, not just for the user reading it back. Vague profiles produce vague songs.
- **Capture over interrogate.** Absorb volunteered information out of order; never force the user back into sequence.

## On Activation

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

If the script fails, resolve the `workflow` block yourself by reading these three files in base → team → user order and applying structural merge rules: `{skill-root}/customize.toml`, `{project-root}/_bmad/custom/{skill-name}.toml`, `{project-root}/_bmad/custom/{skill-name}.user.toml`. Scalars override, tables deep-merge, arrays of tables keyed by `code`/`id` replace matching entries and append new ones, all other arrays append.

Treat `{workflow.persistent_facts}` as foundational context loaded on activation (`file:` prefix = path/glob; bare entries = literal facts). Run any `{workflow.activation_steps_prepend}` before greeting and `{workflow.activation_steps_append}` after greeting, before routing. Persona/tone variance the user wants lives in `persistent_facts` / `project-context.md`, never in the workflow surface.

### Step 2: Greet and Route

Config needs (defaults if config unavailable — never block on missing config): `user_name` (default: generic greeting), `communication_language` (default: English), `document_output_language` (default: English).

Greet the user as `{user_name}` in `{communication_language}`, then detect operation:

| Operation | Trigger | Route |
|-----------|---------|-------|
| **Create** | "create/new band/profile" | Create Profile |
| **List** | "list/show bands/profiles" | List Profiles |
| **Load** | "load/show/view [name]" | Load Profile |
| **Edit** | "edit/update/modify [name]" | Edit Profile |
| **Delete** | "delete/remove [name]" | Delete Profile |
| **Duplicate** | "clone/duplicate/fork [name]", "new version of [name]", "same as [name] but…" | Duplicate Profile |
| **Analyze Voice** | "analyze voice/writing", provides samples | Analyze Writer Voice |
| **Health Check** | "check/review my profile", "is my profile good?" | Health Check |
| **Manage Playlist** | "add a track", "reorder the playlist", "playlist for [name]" | Manage Playlist |
| **Unclear** | — | Present operations and ask |
| **Wrong skill** | "make a song", "create music" | Redirect to Style Prompt Builder or Lyric Transformer |

## Headless Mode

**Headless mode** (`--headless` or `-H`): automated/scripted profile management without conversation. Skip greeting and routing.

**Input channel:** `--headless:create` reads profile YAML from stdin. `--headless:edit <name>` reads YAML field overrides from stdin and applies them as a merge over the existing profile. All other subcommands take their inputs as positional arguments (no stdin).

**Decision log absorbs every assumption made without the user** — inferred band name/slug, inferred tier/model, auto-trimmed style_baseline, conflict resolutions, any lint-fix. Write it to the sibling `{band_profiles_folder}/{profile-name}.decision-log.md` (create on `create`/`duplicate`; append a new session heading on `edit`).

Every return is JSON with `status` (`complete` | `blocked`). On `blocked`, add a one-line `reason` and still return the decision_log path so the caller can read the detail. Return the smallest path set the caller needs.

| Flag | Action | Returns |
|------|--------|---------|
| `--headless:create` | Validate provided YAML, save profile, scaffold playlist YAML, write decision log — all in one write batch | `{"status": "complete", "profile_path": "...", "playlist_path": "...", "decision_log": "...", "validation": {...}}` |
| `--headless:edit <name>` | Merge YAML field overrides via `apply-profile.py --set`, validate, save | `{"status": "complete", "profile_path": "...", "fields_changed": [...], "decision_log": "...", "validation": {...}}` |
| `--headless:duplicate <source> <new_name>` | Copy via `apply-profile.py --duplicate`, validate, write decision log | `{"status": "complete", "profile_path": "...", "source": "...", "decision_log": "..."}` |
| `--headless:validate` | Validate existing profile | validate-profile.py JSON output |
| `--headless:load <name>` | Read and return profile | Structured JSON |
| `--headless:delete <name>` | Delete without confirmation | `{"status": "complete", "profile_path": "..."}` |
| `--headless` (bare) | List all profiles | JSON array |

The deterministic save/field-merge for create, edit, and duplicate is owned by `apply-profile.py` — never hand-serialize profile YAML. Pass `--profiles-dir {band_profiles_folder}` so the write store follows module config; pass `--docs-dir {project-root}/docs` to `scaffold-playlist.py` and `validate-profile.py` so the playlist/songbook root follows config too. Omitting these falls back to the `{project-root}/docs/...` defaults (identical to prior behavior).

## Workflow Operations

### Create Profile

Once the band is named (propose a kebab-case slug if the user doesn't give one — a rename later is a logged decision, not a redo), write the sibling decision log at `{band_profiles_folder}/{profile-name}.decision-log.md`. The decision log is canonical memory — load-bearing decisions, rejected references/descriptors, and overrides live on disk, not in the conversation. If a log already exists for this slug, append a new session heading instead.

**Open-floor opening:** Start by inviting the user to dump everything they've got — "Tell me everything you've got: the vibe, bands it should sound like, lyrics or poems lying around, links, whatever's in your head." Extract what they give, then ask only about what's genuinely missing.

Load `references/profile-schema.md` and run `scripts/tier-features.py` (if tier known) in parallel when entering this operation.

**Discovery — conversational, not a form:**

Gather the information needed for a complete profile through natural dialogue (full schema in `references/profile-schema.md`):

- **Identity**: Band name, instrumental vs. vocal, genre/mood, language
- **References**: 2-3 "sounds like" artists/songs. Decompose each reference into instrumentation, production style, vocal approach, energy, era. Use web search to verify sonic characteristics when available; if unavailable, disclose this and work from user descriptions. Confirm: "Does that breakdown match what you hear?"
- **Model & tier**: Which Suno model/plan. Run `scripts/tier-features.py` to show available features.
- **Vocal direction** (skip if instrumental): Gender, tone, delivery, energy, diction — push for evocative specifics ("warm, breathy female vocal with indie folk phrasing" not "female vocals"). Capture Voice (v5.5, `voice_id`) or Persona (v4.5/v5, name + source song). When a Voice is set, flag that gender descriptors should be omitted from style baseline.
- **Voices & Custom Models** (Pro/Premier only): Capture `voice_id` (v5.5 voice cloning) and/or `custom_model_id` with `custom_model_notes`.
- **Style baseline**: Build default style prompt from collected answers. Front-load essentials in the first ~200 characters (critical zone — strongest influence on generation). 1,000 char hard limit for v4.5+/v5/v5.5 (200 for v4 Pro). Show draft: "Read this like a recipe for your sound — does every ingredient belong?"
- **Exclusions**: What should never appear (max 5, concise). Note internally: Suno doesn't reliably process negatives — Style Prompt Builder translates these into positive language.
- **Creative settings**: Creativity mode (conservative/balanced/experimental). Paid tiers: Weirdness and Style Influence slider preferences (0-100).
- **Writer voice** (optional): Offer to analyze now or skip for later.

**Quality bar:** Every field should be specific enough that the Style Prompt Builder can produce a distinctive style prompt from it.

**Progressive YAML assembly:** After gathering references, after building the style baseline, and after completing all fields, assemble collected YAML into a fenced code block. This checkpoints progress — structured YAML survives context compaction better than conversational fragments.

**Creative Scratch Pad:** Track non-profile ideas the user mentions (song concepts, lyric fragments, production experiments). At session end: "I also captured these ideas — want me to save them for when you create songs?"

**After discovery:**
- Assemble profile YAML.
- Run `scripts/validate-profile.py` (use `--derive-filename "Band Name"` for the kebab-case filename) for the deterministic checks (length, enum, exclusions cap, tier/model/slider consistency) — run this BEFORE the inline judgment pass so structural problems fail fast.
- **Inline quality check** (judgment only, after validation): Is style_baseline specific or vague? Is vocal direction generic or evocative? Do exclusions contradict the genre? Fix issues; flag what needs user input.
- Generate a **Band Identity Card** — 3-4 sentence summary of who this band is. Present this first, then the YAML.
- On approval, save via `scripts/apply-profile.py --save --profiles-dir {band_profiles_folder} --project-root {project-root}` — feed the assembled profile YAML on stdin (the slug is derived from the profile's `name`). This is the same deterministic write owner Edit and Duplicate use; never hand-serialize the YAML (per the invariant above). In the same write batch:
  - **Scaffold the per-band playlist YAML.** Run `scripts/scaffold-playlist.py {profile-name} --project-root {project-root} --docs-dir {project-root}/docs` to create `{project-root}/docs/{profile-name}-playlist.yaml` (pass the `--docs-dir` matching `{songbook_folder}`'s parent if the project relocates its docs root). This empty template is the canonical source for the band's track sequence — without it, `validate-profile.py` will flag the band the moment a song is added, and downstream playlist work has nowhere to write to. See `references/profile-schema.md` "Per-Band Playlist YAML" section for the schema and conventions.
  - Record the meaningful decisions (chosen slug, references kept/rejected, tier, any auto-trims) in the decision log.

### List Profiles

Run `scripts/list-profiles.py --profiles-dir {band_profiles_folder}` to display all saved profiles. If none exist, suggest creating one.

### Load Profile

Use `scripts/list-profiles.py --profiles-dir {band_profiles_folder} --check "{profile-name}"` to verify existence, then read from `{band_profiles_folder}/{profile-name}.yaml`. Display organized by section.

**Validate-on-load (non-blocking advisory):** Run `scripts/validate-profile.py` after loading. Don't gate the display on it — surface any deprecated/stale findings as a gentle advisory ("Heads up: this profile still carries a deprecated `playlist:` block / its tier no longer matches your plan"). Stale state shouldn't persist silently just because Load never checks.

**Tier drift detection:** Compare stored tier against known user tier. If they differ: "This profile was set up for {stored_tier} but you're now on {current_tier}. Want me to unlock the new tier's features?"

If ambiguous, list profiles and ask to clarify.

### Edit Profile

Read the target profile YAML, its sibling `{profile-name}.decision-log.md`, and `references/profile-schema.md` in parallel when entering this operation. The change request enters as a change signal against the standing record: if it contradicts a prior decision in the log, surface the conflict before applying.

Accept natural language changes and apply to relevant fields. If tier changes, run `scripts/tier-features.py` to check feature availability. If genre/mood/vocal fields change, suggest reviewing style_baseline.

**Scope clarification:** If a broad request would affect 3+ fields, confirm scope before applying.

After edits, run `scripts/validate-profile.py` and `scripts/diff-profiles.py` in parallel. Show diff, confirm with user, save. Append the change (clean or override) to the decision log; overrides also note the rejected prior reasoning.

### Delete Profile

Confirm existence via `scripts/list-profiles.py --profiles-dir {band_profiles_folder} --check`, show summary, get explicit confirmation, then delete.

### Duplicate Profile

Copy an existing profile to a new name. Ask for the new name (or generate: "{original}-v{N+1}" or "{original}-{variant}"). Optionally increment version. Ask if they want to modify now or save as-is — if they want changes, chain into Edit. Validate, write a fresh sibling decision log for the new slug, and save.

### Analyze Writer Voice

Extracts writer voice patterns from writing samples and stores them in a band profile.

**Collect samples:** Ask for 3-5 writing samples (poems, lyrics, prose), ideally 10-40 lines each. Guide: "Pick pieces that feel most like YOU." Accept pasted text or file paths (read all files in parallel).

**Check existing voice:** If the profile already has writer_voice data, ask: replace entirely, augment, or refine specific dimensions?

**Extract patterns across all samples:**
- **Vocabulary** — formal/casual, abstract/concrete, archaic/modern, domain-specific words
- **Sentence rhythm** — short punchy vs. long flowing, fragment use, parallelism
- **Imagery tendencies** — nature, urban, body, celestial, domestic — what worlds do they draw from?
- **Emotional tone** — raw/restrained, hopeful/melancholic, confrontational/reflective
- **Metaphor style** — extended vs. quick, conventional vs. surprising, frequency
- **Repetition patterns** — anaphora, refrains, echo structures, callbacks

**Present analysis** with example quotes from their samples illustrating each pattern. User confirms or corrects.

**Store** as `writer_voice` section of the specified band profile. If none specified, ask which one (or create new).

### Health Check

Read the profile YAML, its sibling `{profile-name}.decision-log.md`, and run `scripts/validate-profile.py` in parallel when entering this operation. Critique against the standards the user themselves set (recorded in the log), not just generic rubrics.

Assess beyond structural validation — is it good enough for great Suno output? Review:
- **style_baseline specificity** — vague ("rock music") or detailed? Suggest improvements.
- **writer_voice** — empty? Suggest analyzing samples.
- **reference_tracks** — empty? Suggest adding for better Style Prompt Builder results.
- **exclusion_defaults** — none? Suggest common exclusions for the genre.
- **vocal direction depth** — generic? Suggest specific descriptors.
- **generation_history** — any snapshots? Remind to save winners.

Present as friendly recommendations, not failures.

### Manage Playlist

Each band owns one canonical `{project-root}/docs/{profile-name}-playlist.yaml` — the single source of truth for track sequence. If it doesn't exist yet, scaffold it with `scripts/scaffold-playlist.py {profile-name} --project-root {project-root} --docs-dir {project-root}/docs` (add `--from-songbook` to pre-populate from existing songbook entries). To add a track, reorder, or rename, edit that YAML directly (name + audio file per track), then confirm. For full album-craft sequencing methodology, hand off to the Feedback Elicitor — this operation just keeps the canonical YAML correct. See `references/profile-schema.md` "Per-Band Playlist YAML" for schema and workflow rules.

## Post-Operation Flow

After **Create** or **Edit**: bridge to downstream skills — "Your profile is saved. Ready to put it to work? You can 'build a style prompt' or 'write lyrics' for this band."

At handoff, audit the decision log: every meaningful entry should be captured in the profile, parked as a noted future idea, or explicitly set aside — so the user signs off on how their thinking was handled.

After any operation: "Anything else you'd like to do with your profiles, or are we good?"

## Scripts

All in `scripts/`. Run any script with `--help` for usage details (the help output documents what each checks, so the work can be done by hand when Python or `uv` is unavailable).

| Script | Purpose |
|--------|---------|
| `validate-profile.py` | Validate profile YAML; `--derive-filename` for kebab-case naming; `--docs-dir {project-root}/docs` to locate playlist/songbook when the docs root is relocated |
| `apply-profile.py` | Deterministic save / field-merge / duplicate of profile YAML (headless write owner; `--set`, `--duplicate`; `--profiles-dir {band_profiles_folder}`) |
| `scaffold-playlist.py` | Scaffold the canonical per-band playlist YAML; `--from-songbook` pre-populates from songbook entries; `--docs-dir {project-root}/docs` redirects the playlist/songbook docs root |
| `list-profiles.py` | List profiles; `--check` to verify specific profile; `--profiles-dir {band_profiles_folder}` selects the store |
| `tier-features.py` | Show Suno features available for a given tier |
| `diff-profiles.py` | Structured JSON diff between two profiles |
