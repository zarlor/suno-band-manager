**Language:** Use `{communication_language}` for all output.
**Variables:** `{project-root}`, `{communication_language}`

---
name: save-memory
description: Explicitly save current session context to memory
menu-code: SM
---

# Save Memory

Immediately persist the current session context to memory.

## Process

1. **Read current index.md** — Load existing context from `{project-root}/_bmad/_memory/band-manager-sidecar/index.md`

2. **Update with current session:**
   - Active song work (style prompt, lyrics, parameters, model, band profile in use)
   - User preferences discovered or changed this session
   - Current interaction mode preference
   - Any band profile updates pending
   - Next steps to continue

3. **Write updated index.md** — Replace content with condensed, current version

4. **Checkpoint other files if needed (parallel batch)** — These writes are independent; run in parallel:
   - `patterns.md` — Add new musical preferences discovered (genre tendencies, vocal preferences, exclusion patterns, creativity level preferences)
   - `chronology.md` — Add session summary if significant work was done

## Output

Confirm save with a brief session recap in Mac's voice:

"Memory saved. Here's what we covered:
- {2-4 bullet points summarizing the session: songs created/refined, preferences discovered, profiles updated}
- Ready to pick up right here next time."

**When complete:** Return to the main menu or continue with the user's next request.
