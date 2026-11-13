# Mac — Headless Capability Runs

**Language:** Use `{communication_language}` for any text in the result.

A headless run lets a script, a scheduled job or a sibling skill drive one of Mac's capabilities with no human in the loop. It is invoked as `--headless:{capability}` (e.g. `--headless:create-song`), `-H {capability}`, or with a structured JSON payload naming a capability. This is a capability contract — distinct from a Pulse wake (`--pulse`, maintenance only).

The keys named below are in the wake's state block. `{skill-root}` is this skill's folder and `{project-root}` the project root.

## What headless skips

No greeting, no menu, no sync-package prompt, no reconcile walk-through, and no "anything I'm missing?" soft gates inside the capability — the input is taken as confirmed.

## What headless still does

1. **Wake as usual, then check the mode.** The wake already printed the identity files, so the CREED core (the Package Assembly Rule binds headless package runs too, and its Dominion governs every write) and HOW-I-REMEMBER.md are loaded. What the mode means here:
   - WAKING → go on.
   - UPGRADE_V2 or UPGRADE_V1 → run the headless branch of `references/upgrade-v2.md` or `references/upgrade-v1.md` first.
   - FIRST_BREATH (with or without `resume`) or SCAFFOLD_FAILED → return `blocked` with `summary: "no sanctum yet; needs an interactive First Breath"`, and don't run the scaffold: a birth needs an owner to answer.
   - DAMAGED or ERROR → return `blocked` with the wake's reason (`references/damaged-sanctum.md` names the case for DAMAGED) and change nothing.

   Tier, default exclusions and the active band resolve from `memory/owner/preferences.md`, `memory/work/default-exclusions.md` and `memory/bands/active.md`, with `config.suno_tier` as the fallback. If the tier is still unknown, build for Free and say so in `warnings`. If `template_upgrade` lists changes, follow `references/upgrade-sanctum.md` "Headless and Pulse".
2. **Resolve the capability** against `routing_table` (a menu code, or an entry's `name`; an entry whose value is another code is an alias for it):
   - create-song → load `references/create-song-headless.md`; refine-song → load `references/refine-song-headless.md`. Each holds its own input contract and payload.
   - A `skill` route invokes that skill in its own headless mode, passing the row's `name`.
   - Any other `prompt` route (browse-songbook, save-memory and whatever the menu gains later), every `learned` route, and the routes with no menu line (reconcile, post-publish, pipeline-guard setup) are interactive-only: return `blocked` with `summary: "capability {capability} is interactive-only"` and leave durable files untouched. An owner-taught prompt has no headless contract, and improvising one runs it without the owner it was written for.

3. **Run the pipeline in this run.** The Package Assembly Rule keeps the pipeline skills' JSON out of an owner-facing turn. A headless run has no such turn, and may already be running inside another skill's subagent, so invoke the style and lyric skills directly here rather than nesting a subagent inside it. The order is the discipline's: the Style Prompt Builder first, then the Lyric Transformer with `section_cues` lifted from the builder's style prompt; only refine rebuilds that don't depend on each other go out together. The requirement to run the pipeline at all is unchanged.
4. **Persist like the interactive flow does.** Run the capability's own save and regenerate steps (`regenerate_index_sections.py`, `genre_coverage.py` where it already calls them). Before each durable write, check the path with the command in the Notes of CREED.md's Dominion; a denied write is never worked around — skip it and report it in `warnings`, or return `blocked` when it was the run's main artifact. Any write the interactive flow gates behind a "never overwrite without asking" checkpoint is staged and reported in `warnings`, never auto-applied. Headless skips prompts, not persistence and not boundaries.

## Result

**The reply is the JSON object alone**, so a script can parse it: no text before or after it, no code fence, and no message before it. Every tool call goes out with no words beside it (no "Now emitting…", no progress note), and anything worth saying goes in a field (`warnings`, `decision_log`, `summary`).

How the run handles its own files and commands:

- A heredoc's delimiter is quoted (`<<'EOF'`), so backticks and `$` in the text stay literal and never run.
- Scratch files (a lyric draft for a script, a package to pipe) go in a fresh `mktemp -d` folder, never a fixed `/tmp` name another run could share.
- No command runs in the background: every tool call finishes before you return, so nothing reports after the reply.

```json
{
  "status": "complete | blocked",
  "capability": "create-song",
  "artifact_path": "the file the capability wrote, or null",
  "package": "the capability's own payload (create-song: its package object; refine-song: its delta JSON), or null",
  "summary": "one-line plain-language result",
  "lyrics_changes": "create-song with transformed lyrics: the Lyric Transformer's `changes`, as returned; otherwise omitted",
  "warnings": ["non-fatal issues, staged-but-not-applied writes, skipped optional steps, an assumed tier"]
}
```

- **Blocked** — a required input is missing, a boundary forbids the write, or a precondition fails (malformed sanctum, missing band profile): return `blocked` with a one-line `summary` and the specifics in `warnings`. Never half-apply, never invent an artifact path.
- **Unknown capability** — return `blocked` with `summary: "unknown capability: {capability}"` and the available capability names in `warnings`.
