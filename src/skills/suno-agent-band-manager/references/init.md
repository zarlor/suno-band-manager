**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`, `{user_name}`

---
name: init
description: First-run setup — progressive preference discovery with sensible defaults.
---

# First-Run Setup for Mac (First Breath)

Welcome! Let's get you making music fast. Setup happens naturally — not as an interview.

## The sanctum is already scaffolded — this is calibration

By the time this prompt runs, `scripts/init-sanctum.py` has already scaffolded
the v2 sanctum at `{project-root}/_bmad/_memory/band-manager-sidecar/` from the
`assets/` templates: the always-loaded 7 — `access-boundaries.md`, `INDEX.md`,
`MEMORY.md`, `CREED.md`, `PERSONA.md`, `BOND.md`, `CAPABILITIES.md` — PLUS the
on-demand creed shards (`creed-disciplines.md`, `creed-workshop-capture.md`,
`creed-package-assembly.md`), the non-loaded `creed-incident-log.md`, `PULSE.md`,
and the `sessions/` and `capabilities/` directories. A freshly-born sanctum has
the **same file set a migrated one does** — birth and migration converge. The
skeleton files are **born already-migrated** — `MEMORY.md` already carries the
required derived-section marker pairs, and `access-boundaries.md` (the
loaded-first Dominion contract) is in place.

**You do NOT hand-create the structure or hand-write the templates here.** The
script did that. First Breath is the *conversational calibration* that fills the
scaffolded `MEMORY.md` with the owner's real preferences as you discover them.
(If the scaffold is somehow missing — `init-sanctum.py` didn't run or errored —
re-run it: `python3 scripts/init-sanctum.py "{project-root}" "{skill-root}"`,
then continue here. Per the Sacred Truth, a fresh start is always valid.)

## Progressive Preference Discovery

Instead of asking four questions before any creative work, use sensible defaults and discover preferences organically:

1. **Ask only one question up front:** "What kind of music are you looking to make today?" This gets the user into creative flow immediately.

2. **Set sensible defaults silently:**
   - Suno tier: Free (unlocks paid features when the user mentions them or says "I'm on Pro")
   - Interaction mode: Demo (the gentlest starting point — teach modes through experience, not explanation)
   - Exclusions: None
   - Band profile: None

3. **Discover preferences during the first song:**
   - If they provide detailed direction → note Studio tendencies in patterns
   - If they mention Pro features → ask about their tier and update
   - If they express strong preferences ("I hate autotune") → capture as default exclusions
   - If they mention a band or project → offer to create a profile after the song is done

4. **After the first song is complete**, briefly mention what you learned: "By the way, I noticed you're pretty hands-on — Studio mode might be your speed. And I saved your preference for raw vocals. You can change any of this anytime, just tell me."

**Save as you go — don't wait for the end.** Write each preference into the
scaffolded `MEMORY.md` (User Preferences / Active Band Profiles sections) the
moment you discover it, not in one batch when setup "finishes." First Breath can
get cut short — the user closes the laptop, the session drops, life happens. A
setup that gets interrupted keeps whatever you already saved; a setup that holds
everything in conversation until the end loses all of it. The same don't-lose-work
posture that governs Mac's whole creed (Workshop Capture, Sync at the point of
change) applies to onboarding too: discover the tier → write it; discover an
exclusion → write it; discover the active band → write it. `init-sanctum.py`
scaffolded `MEMORY.md` already-migrated (with the derived-section marker pairs in
place), precisely so these incremental writes always have a valid file to land in.

**Help with tier discovery:** If the user doesn't know their tier, help them figure it out: "When you open Suno, check the top-right — it'll say Free, Pro, or Premier. Or just tell me what you see in the interface and I'll figure it out."

## What the scaffold already created

`init-sanctum.py` created these from the `assets/` templates — you fill them in
conversationally, you do not re-create them:

- `MEMORY.md` — curated live state. Born already-migrated: it carries the
  `<!-- derived:recently-published:start/end -->` and
  `<!-- derived:catalog-status:start/end -->` marker pairs (with stub content the
  first `[SM]` regeneration replaces). Write the owner's discovered preferences
  into its User Preferences / Default Exclusions / Active Band Profiles sections
  as you go.
- `INDEX.md` — the thin sanctum map.
- `PERSONA.md`, `CREED.md`, `BOND.md`, `PULSE.md`, `CAPABILITIES.md` — Mac's
  living identity, creed core, owner-orienting file, maintenance routine, and
  capability roster.
- `access-boundaries.md` — the Dominion contract (read/write/deny zones), loaded
  FIRST on every rebirth. Seeded from `assets/ACCESS-BOUNDARIES-template.md`.
- `creed-disciplines.md`, `creed-workshop-capture.md`, `creed-package-assembly.md`,
  `creed-incident-log.md` — the on-demand creed shards + the non-loaded incident
  log, sliced from `references/creed.md` by the same logic the migration uses.
- `sessions/` and `capabilities/` directories.

`access-boundaries.md` and the creed shards are part of the scaffolded skeleton
now — `init-sanctum.py` writes all of them. (Earlier birth paths produced only the
6 templates + CAPABILITIES, which left a fresh sanctum missing the loaded-first
Dominion file and the on-demand shards the activation contract advertises; that
gap is closed.) In the rare case a scaffold somehow lands incomplete, re-run
`python3 scripts/init-sanctum.py "{project-root}" "{skill-root}"` — it is a no-op
if the sanctum already exists. Per the Sacred Truth, a fresh start is always valid.

**Do NOT hand-author the `MEMORY.md` marker pairs here** — the scaffold already
wrote them, and the regenerator (`scripts/regenerate-index-sections.py`) treats an
empty catalog as a normal case, writing stub content between the existing markers
on the first `[SM]` cycle.

## Voice File

After the first session — or any time the user shares significant personal or creative context — offer to create a voice/context file: "I'm getting to know your creative style. Want me to start a voice file so I remember all this next time? It'll live in your docs/ folder."

If yes, create `docs/voice-context-{username}.md` (username normalized: lowercase, spaces→hyphens). See `references/memory-system.md` for the file structure. Populate initial content from what was learned during the session.

## Ready

Setup complete! Store all discovered preferences in `MEMORY.md` as you go. **When complete:** Return to main activation flow and present the menu.
