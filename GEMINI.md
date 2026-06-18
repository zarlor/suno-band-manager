# Suno Band Manager — Project Standing Orders

This file contains standing orders that apply to any LLM agent working in this repository. It is loaded automatically by Gemini CLI, Claude Code (`CLAUDE.md`), and Codex CLI / OpenCode (`AGENTS.md`) — three separate files with identical content for cross-tool compatibility.

## Skill Activation Discipline (MANDATORY)

When activating any skill in this module — `suno-agent-band-manager`, `suno-band-profile-manager`, `suno-style-prompt-builder`, `suno-lyric-transformer`, `suno-feedback-elicitor`, or `suno-setup` — you MUST follow the "On Activation" instructions in the skill's `SKILL.md` exactly:

1. **Execute any scripts** referenced in the activation block (e.g., `pre-activate.py`, `check-memory-health.py`, `validate-path.py`) using your shell tool. Do not skip these — they emit dynamic menu data and pre-load required state. The menu you present to the user MUST come from the script output, not from a hardcoded approximation derived from `SKILL.md` text.

2. **Follow the agent's own activation protocol exactly** — for the `suno-agent-band-manager` ("Mac") agent this is `references/activation.md`, which loads the lean **sanctum** files in the right order on every rebirth (the sanctum's `CREED.md` slim core, `PERSONA.md`, `INDEX.md`, `MEMORY.md`, plus `access-boundaries.md` FIRST). Do NOT blanket-read every file under the skill's `references/` directory. In particular, `references/creed.md` (~382 lines) and `references/persona.md` are **authored SOURCE / template lineage** — they seed the sanctum at First Breath and are **consulted only when (re)seeding the sanctum, NOT loaded on every activation**. Force-loading them re-imposes the per-rebirth token cost the v2 sanctum sharding was designed to eliminate. The agent's living identity (how it communicates) comes from the *sanctum's* `CREED.md` core and `PERSONA.md`, which `activation.md` already loads.

3. **Present the dynamic menu** from the script output (e.g., from `pre-activate.py`), not a hardcoded approximation derived from your interpretation of `SKILL.md`. Missing menu items confuse users who expect a complete capability list.

4. **Load voice context** (`docs/voice-context-{username}.md` if it exists) before greeting. This is the user's durable creative identity file — without it, you have no context about who you're working with, their creative history, their preferences, or their active projects.

5. **Internalize persona vocabulary, do not enumerate it.** When the loaded `PERSONA.md` (from the sanctum) lists vocabulary or phrasing examples (e.g., NOLA voice terms), treat them as voice grounding to be sampled naturally, NOT as a checklist to use exhaustively in a single response.

## Suno Pipeline Rule (MANDATORY)

When the `suno-agent-band-manager` skill is active, NEVER hand-build a Suno package from conversation memory. ALWAYS invoke `suno-style-prompt-builder` and `suno-lyric-transformer` via your skill/tool invocation mechanism before presenting any style prompt + lyrics + settings package to the user.

The skills contain critical guardrails (artist name detection, production descriptor checks, character budget validation, section tag validation, current-prompt-only exclusion reasoning) that cannot be reliably replicated from memory. Skipping them produces packages that look correct but fail in Suno or violate documented constraints.

**The Package Assembly Rule core (marked INVARIANT) lives in the sanctum's loaded `CREED.md`** (`_bmad/_memory/band-manager-sidecar/CREED.md` → "Package Assembly Rule — CORE"), which `references/activation.md` loads on **every** agent activation — so the guarantee holds: whenever a package is assembled, the rule is loaded. **The full rule** — Pre-Output Self-Check, Violation Tells, Agent-vs-Skill tool choice, highest-risk contexts, and refinement presentation scope — lives in the on-demand `creed-package-assembly.md` shard (loaded before any package-assembly work). This root file is a brief cross-tool reinforcement — the authoritative rule is in the sanctum creed core and its package-assembly shard, NOT in the authored-source `references/creed.md` (which is no longer loaded on activation).

## Why This File Exists

The activation rules used to live only inside individual `SKILL.md` files in a declarative style ("Load config...", "Route by state..."). That style works in Claude Code because the harness adds scaffolding around skill activation, but in Gemini CLI, Codex CLI, OpenCode, and other LLM CLIs, the model sees the `SKILL.md` text more literally and may treat the activation steps as optional reading rather than mandatory tool calls.

This file makes the activation discipline explicit and tool-agnostic. It is loaded into every session automatically by the LLM CLI, so the standing orders are always present regardless of which skill activates or how the model interprets `SKILL.md`.

## Cross-References

- `INSTALLATION.md` — Setup instructions for all supported LLM CLIs (Claude Code, Gemini CLI, Codex CLI, GitHub Copilot, Windsurf, OpenCode, Cursor, Aider)
- `src/skills/suno-agent-band-manager/references/USAGE.md` — End-user guide
- `README.md` — Module overview and architecture
- `src/skills/*/SKILL.md` — Per-skill activation and capability definitions
