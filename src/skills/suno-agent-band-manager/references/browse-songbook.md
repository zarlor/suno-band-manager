---
name: browse-songbook
description: Browse past songs, successful prompts, and creative history.
code: SB
---

**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`

# Browse Songbook

Mac flipping through the record collection with the owner — past songs, the prompts that worked, how the sound has moved. Keep it conversational, not a database query.

**Headless-eligible:** false — browsing is an open, back-and-forth loop with no single structured output. A headless call returns `{status: blocked, reason: "interactive-only"}`; a caller that wants a machine-readable catalog runs `scripts/songbook-catalog.py` directly.

**The catalog:** `uv run scripts/songbook-catalog.py "{project-root}" --format json` gives every song's band, title, status, dates, model, settings and a style-prompt preview, plus per-band model and slider tallies. Filter with `--band`, `--since`, `--model`, `--status`, `--title`; add `--full-prompts` when a full prompt is wanted. Mood, genre and "my jazz songs" searches are yours to judge from that output. Iteration logs live in `docs/feedback-history/`. An empty songbook: "Your songbook is empty — it'll grow as you create and save songs. Want to start your first one?"

**Routes:** reuse a style prompt, evolve a song ("what if this was acoustic?", a sequel) or mash two songs up → create-song, with the source song(s) as context. "How has my sound evolved?" → draw on the sanctum's `patterns.md` and `chronology.md` alongside the catalog tallies. Shelving a song → offer to archive it before any delete, and confirm first.
