---
name: capability-authoring
description: How Mac authors, registers, and evolves a capability the owner teaches him
---

# Capability Authoring

When the owner wants Mac to learn a new ability, you build the capability together. The mechanics are below; first, the one thing that decides whether the capability is any good.

## Write the destination, not the route

Know your own default. Asked to author a capability, you will script it — numbered steps, question lists, a template with mandatory sections — because elaborate scaffolding feels like diligence and reads like quality. That instinct is the central defect to resist. A script is your imagined transcript of one good session; real sessions diverge from it, and a capability that scripts the path spends your future self's intelligence on compliance instead of the problem.

Write the destination instead. A capability prompt holds four things: the **outcome** (the artifact or change that must exist when it has done its job), the **consumer** (who must act on that outcome, and what they can or cannot be assumed to know), the **bar** (what the consumer needs to be true of it), and the **non-inferables** — what your future self cannot infer on its own: owner specifics worth pulling from MEMORY.md, BOND.md and the voice file, wiring like paths and formats, and any rule with real consequences behind it. Then stop. The outcome and its consumer imply the process. Do not restate your stance: your persona is already in the room when a capability runs, and it supplies the voice and the relationship — the capability only adds what this ability needs on top.

A complete capability body, not an excerpt:

```text
The outcome is liner notes the owner would print on the sleeve: what the
song is about in their own framing, how it was made, who it is for. Read the
songbook entry and the WIP history first; quote the owner, don't interpret
them (Hedge Preservation). Two short paragraphs beat a page. Check MEMORY.md
for the tone their earlier notes landed in.
```

Everything a scripted version would add — an intake questionnaire, a section template, a word count per section — subtracts adaptivity.

This section is the working standard, synced from the prompt-quality canon. For the full canon — the cut tests, the two-version comparison, the retirement test — load `references/prompt-quality-canon.md` (the CREED's "Author to the standard" order says when).

## What stays true inside a learned capability

- If it produces a style prompt, lyrics or settings for Suno, the Package Assembly Rule still applies: the pipeline skills build the package, not the capability.
- It writes under the access-boundaries write rule like everything else Mac does.
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

The code must not clash with a code already on Mac's menu (the module's `module-help.csv` codes) — a clashing learned row is left off the menu.

## Creating a capability

Explore what the owner needs before writing anything, draft it, show it, refine it with them, then:

1. Save it to `{project-root}/_bmad/_memory/band-manager-sidecar/capabilities/`.
2. Add a row to CAPABILITIES.md's `## Learned` table, in this exact shape (the wake reads it into the menu):
   `| [XX] | Name | One-line description | `capabilities/{name}.md` | YYYY-MM-DD |`
   For an external skill, the Source cell is `External: skill-name`.
3. Add its row to INDEX.md under Loaded on Demand.
4. Tell the owner the code that triggers it next session.

## Refining and retiring

When you refine a capability, update the file in place and note the change in today's session log. When it stops earning its place — the canon's retirement test: it no longer beats what you would do bare — remove its CAPABILITIES.md row, keep the file so the owner can bring it back, and note the retirement in the session log.
