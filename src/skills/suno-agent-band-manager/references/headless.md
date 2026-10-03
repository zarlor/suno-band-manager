# Mac — Headless Capability Runs

**Language:** Use `{communication_language}` for any text in the result.

A headless run lets a script, a scheduled job or a sibling skill drive one of Mac's capabilities with no human in the loop. It is invoked as `--headless:{capability}` (e.g. `--headless:create-song`), `-H {capability}`, or with a structured JSON payload naming a capability. This is a capability contract — distinct from a Pulse wake (`--pulse`, maintenance only).

## What headless skips

No greeting, no menu, no sync-package prompt, no reconcile walk-through, and no "anything I'm missing?" soft gates inside the capability — the input is taken as confirmed.

## What headless still does

1. **Wake as usual.** The wake already printed the sanctum, so access-boundaries, the CREED core (the Package Assembly Rule binds headless package runs too) and MEMORY.md are loaded — tier, default exclusions and the active band resolve from MEMORY.md, with `config.suno_tier` as the fallback. If the tier is still unknown, build for Free and say so in `warnings`. If the mode is UPGRADE_V1, run the headless branch of `references/upgrade-v1.md` first.
2. **Resolve the capability** against `routing_table` (action name or menu code; FL routes to RS). For a `prompt` route, load the prompt and check its `Headless-eligible:` marker first:
   - `true` (create-song, refine-song) → run that capability's own Headless Mode contract.
   - `false` (browse-songbook, save-memory, reconcile) → interactive-only by design. Don't improvise a contract; return `blocked` with `summary: "capability {capability} is interactive-only"` and leave durable files untouched.

   A `skill` route invokes that skill in its own headless mode.
3. **Pipeline tool choice.** The Package Assembly Rule calls for Agent subagents to keep the pipeline skills' JSON out of a user-facing turn. A headless run has no such turn, and may already be running inside another skill's subagent, so invoke the style and lyric skills directly with the Skill tool rather than nesting Agent inside Agent. The requirement to run the pipeline at all is unchanged.
4. **Persist like the interactive flow does.** Run the capability's own save and regenerate steps (`regenerate-index-sections.py`, `genre-coverage.py` where it already calls them). Before each durable write, check the path: `uv run scripts/validate-path.py <path> write --boundaries "{project-root}/_bmad/_memory/band-manager-sidecar/access-boundaries.md" --project-root "{project-root}" --skill-root "{skill-root}"`; a denied path is a `blocked` result, not a workaround. Any write the interactive flow gates behind a "never overwrite without asking" checkpoint is staged and reported in `warnings`, never auto-applied. Headless skips prompts, not persistence and not boundaries.

## Result

Return structured output, no conversational prose:

```json
{
  "status": "complete | blocked",
  "capability": "create-song",
  "artifact_path": "the file the capability wrote, or null",
  "package": "the capability's own payload (create-song: its package object; refine-song: its delta JSON), or null",
  "summary": "one-line plain-language result",
  "warnings": ["non-fatal issues, staged-but-not-applied writes, skipped optional steps, an assumed tier"]
}
```

- **Blocked** — a required input is missing, a boundary forbids the write, or a precondition fails (malformed sanctum, missing band profile): return `blocked` with a one-line `summary` and the specifics in `warnings`. Never half-apply, never invent an artifact path.
- **Unknown capability** — return `blocked` with `summary: "unknown capability: {capability}"` and the available capability names in `warnings`.
