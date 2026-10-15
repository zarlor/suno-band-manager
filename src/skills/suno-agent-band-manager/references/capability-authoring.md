---
name: capability-authoring
description: How Mac authors, registers, and evolves a capability the owner teaches him
---

# Capability Authoring

When the owner wants Mac to learn a new ability, you build the capability together.

## The standard

Write it to the prompt-quality canon, `references/prompt-quality-canon.md`, which your CREED's "Author to the standard" order has you load now. One difference for a capability: its stance is already in the room — your persona supplies the voice and the relationship — so the prompt holds the outcome, its consumer, the bar and the non-inferables (owner specifics from your `memory/` files, BOND.md and the voice file; paths and formats; rules with real consequences). A complete capability body, not an excerpt:

```text
The outcome is liner notes the owner would print on the sleeve: what the
song is about in their own framing, how it was made, who it is for. Read the
songbook entry and the WIP history first; quote the owner, don't interpret
them (Hedge Preservation). Two short paragraphs beat a page. Grep memory/
for the tone their earlier notes landed in.
```

## What stays true inside a learned capability

- If it produces a style prompt, lyrics or settings for Suno, the Package Assembly Rule still applies: the pipeline skills build the package, not the capability.
- It writes under the write rule in CREED.md's Dominion like everything else Mac does.
- Suno facts come from `references/SUNO-REFERENCE.md` at run time, not from the capability text, so a platform change does not leave it stale.

## Capability types

- **Prompt (default)** — `capabilities/{name}.md`. Best for judgment work.
- **Script** — `capabilities/{name}.py` plus a short `{name}.md` saying when to run it and what to do with the result. One job per script; take paths as arguments; read and write inside the sanctum or the allowed `docs/` zones.
- **Multi-file** — `capabilities/{name}/` with a main `{name}.md` and its reference material.
- **External skill** — point at an installed skill instead of rebuilding it. Ask before installing anything.

## Prompt file frontmatter

```markdown
---
name: {kebab-case-name}
description: {one line, what this does}
code: {2-letter menu code}
added: {YYYY-MM-DD}
type: prompt | script | multi-file | external
---
```

The code must not clash with a code already on Mac's menu (the codes in the skill's `assets/menu.csv`) — a clashing learned row is left off the menu.

## Creating a capability

Explore what the owner needs before writing anything, draft it, show it, refine it with them, then:

1. Save it to `{project-root}/_bmad/memory/suno-agent-band-manager/capabilities/`.
2. Add a row to CAPABILITIES.md's `## Learned` table, in this exact shape (the wake reads it into the menu):
   `| [XX] | Name | One-line description | `capabilities/{name}.md` | YYYY-MM-DD |`
   For an external skill, the Source cell is `External: skill-name`.
3. Tell the owner the code that triggers it next session.

## Refining and retiring

When you refine a capability, update the file in place and note the change in today's session note. When it stops earning its place — the canon's retirement test: it no longer beats what you would do bare — remove its CAPABILITIES.md row, keep the file so the owner can bring it back, and note the retirement in the session note.
