**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`

---
name: browse-songbook
description: Browse past songs, successful prompts, and creative history.
menu-code: SB
---

# Browse Songbook

Browse your creative portfolio — past songs, successful prompts, iteration history, and creative evolution.

## Step 1: Scan Available Content (parallel batch)

Check these locations in a single parallel batch:
- `docs/songbook/` — Saved lyrics from Lyric Transformer
- `docs/feedback-history/` — Iteration logs from Feedback Elicitor
- `{project-root}/_bmad/_memory/band-manager-sidecar/chronology.md` — Session timeline

If no saved work exists, let the user know: "Your songbook is empty — it'll grow as you create and save songs. Want to start your first one?"

## Step 2: Present Overview

Group by band profile (or "Unaffiliated" for one-offs):

```
## Your Songbook

### {Band Profile Name}
- {Song Title} — {date}, {transformations applied}, {model used}
  Style prompt: {first 80 chars}...

### Unaffiliated
- {Song Title} — {date}
```

**For comparisons:** When showing two songs side-by-side, highlight key differences: genre shift, vocal direction change, structural evolution. Keep it conversational — "Look how your sound evolved from that first folk demo to this polished studio cut."

## Step 3: Interact

The user can:
- **View details** — Show full lyrics, style prompt, parameters, and iteration history for a song
- **Search/filter** — Find songs by genre, mood, date range, model, band profile, or keyword. Accept natural language: "show me everything from March" or "find my jazz songs"
- **Reuse** — "Use this style prompt as a starting point for a new song" → route to create-song with pre-loaded context
- **Evolve** — Take a past song in a new direction: "What if this was acoustic?" or "Make a sequel" → route to create-song with the original as context, applying the requested transformation
- **Mashup** — Combine elements from two songs: "Merge the lyrics from Song A with the style of Song B" → route to create-song with both as context
- **Compare** — Show two songs side-by-side to see how their sound evolved
- **Export** — Present all data for a song in a copy-ready format (style prompt, lyrics, parameters, iteration history)
- **Archive/delete** — Move a song to an archive folder or remove it. Confirm before deleting: "Sure you want to shelve this one? I can archive it instead of deleting — just in case you change your mind."

## Step 4: Creative Insights (optional)

If the user asks "how has my sound evolved?" or similar, draw from `{project-root}/_bmad/_memory/band-manager-sidecar/patterns.md` and `{project-root}/_bmad/_memory/band-manager-sidecar/chronology.md` to surface patterns: genre trends, vocal direction shifts, production evolution, breakthrough moments.

## Output

Keep it conversational — this is Mac browsing the record collection, not a database query.

**When complete:** Return to the main menu or continue with the user's next request.
