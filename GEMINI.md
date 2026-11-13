# Suno Band Manager — Project Standing Orders

This file contains standing orders that apply to any LLM agent working in this repository. It is loaded automatically by Gemini CLI, Claude Code (`CLAUDE.md`), and Codex CLI / OpenCode (`AGENTS.md`) — three separate files with identical content for cross-tool compatibility.

## Skill Activation Discipline (MANDATORY)

When activating any skill in this module — `suno-agent-band-manager`, `suno-band-profile-manager`, `suno-style-prompt-builder`, `suno-lyric-transformer`, `suno-feedback-elicitor`, or `suno-playlist-sequencer` — you MUST follow the "On Activation" instructions in the skill's `SKILL.md` exactly:

1. **Execute any scripts** referenced in the activation block (e.g., Mac's `pre_activate.py`, or the `resolve_customization.py` call in the workflow skills) using your shell tool. Do not skip these — they emit dynamic menu data and pre-load required state. The menu you present to the user MUST come from the script output, not from a hardcoded approximation derived from `SKILL.md` text.

2. **Follow the agent's own activation protocol exactly** — for the `suno-agent-band-manager` ("Mac") agent this is the skill's On Activation block plus `references/activation.md`. On every waking `uv run {skill-root}/scripts/pre_activate.py --wake` prints, in one pass, the identity files of his sanctum (`_bmad/memory/suno-agent-band-manager/`) in load order — `PERSONA.md`, `CREED.md` (slim core, including the Dominion: his access boundaries), `BOND.md`, `HOW-I-REMEMBER.md`, `CAPABILITIES.md` — followed by the generated memory map and `memory/pending.md`. That output IS the load set: read it in full, and open files under `memory/` only when the conversation calls for them, as `HOW-I-REMEMBER.md` says. Do NOT blanket-read every file under the skill's `references/` directory or the sanctum's `memory/` and `raw/` folders. In particular, `assets/creed.md` is **authored SOURCE** — it seeds the sanctum's creed disciplines at First Breath and is **consulted only when (re)seeding the sanctum, NOT loaded on every activation** (the sanctum's `PERSONA.md` is seeded from `assets/PERSONA-template.md`). Force-loading it re-imposes the per-waking cost the lean sanctum was designed to eliminate. The agent's living identity (how it communicates) comes from the *sanctum's* `CREED.md` core and `PERSONA.md`, which the wake already prints.

3. **Present the dynamic menu** from the script output (e.g., from `pre_activate.py`), not a hardcoded approximation derived from your interpretation of `SKILL.md`. Missing menu items confuse users who expect a complete capability list.

4. **Load voice context** (`docs/voice-context-{username}.md` if it exists) before greeting. This is the user's durable creative identity file — without it, you have no context about who you're working with, their creative history, their preferences, or their active projects.

5. **Internalize persona vocabulary, do not enumerate it.** When the loaded `PERSONA.md` (from the sanctum) lists vocabulary or phrasing examples (e.g., NOLA voice terms), treat them as voice grounding to be sampled naturally, NOT as a checklist to use exhaustively in a single response.

## Suno Pipeline Rule (MANDATORY)

When the `suno-agent-band-manager` skill is active, NEVER hand-build a Suno package from conversation memory. ALWAYS build it through the pipeline skills (`suno-style-prompt-builder`, and `suno-lyric-transformer` whenever there are lyrics to place), invoked via your skill/tool invocation mechanism, before presenting any style prompt + lyrics + settings package to the user.

The skills contain critical guardrails (turning named artists into sonic descriptors and flagging a name the request gave when it is left in a field, production descriptor checks, character budget validation, section tag validation, current-prompt-only exclusion reasoning) that cannot be reliably replicated from memory. Skipping them produces packages that look correct but fail in Suno or violate documented constraints.

**The authoritative rule is the Package Assembly Rule core (marked INVARIANT) in the sanctum's loaded `CREED.md`** (`_bmad/memory/suno-agent-band-manager/CREED.md` → "Package Assembly Rule — CORE"), which the wake prints on **every** agent activation, so whenever a package is assembled the rule is loaded. What applies while assembling or refining lives in the sanctum's on-demand `memory/disciplines/package-assembly.md` (loaded before any package-assembly work). This root file is a brief cross-tool reinforcement of the reason above; it does not restate the rule, and the skill's `assets/creed.md` is seed source that is not loaded on activation.

## Script Execution — `uv run` (MANDATORY)

Every Python script in this module runs via `uv run <path-to-script>.py` (inside a skill, `uv run {skill-root}/scripts/<name>.py`). `uv` reads each script's PEP 723 inline metadata (the `# /// script … # ///` header) and auto-provisions its dependencies — `pyyaml`, `librosa`, `numpy` — with no virtualenv to activate and no manual `pip install`. When an activation block, reference doc, or skill instruction says to run a script, invoke it with `uv run`.

**Fallback:** if `uv` is unavailable, install it (`curl -LsSf https://astral.sh/uv/install.sh | sh`, or `pip install uv`). Do not fall back to `python3` for a skill's scripts: `python3` skips the header that declares their dependencies, and the skills' own instructions say `uv run`. The one `python3` invocation is the hook below.

**Exception:** the `pipeline_guard.py` hook is invoked directly with `python3` — it fires on every tool call, so it is deliberately kept off `uv` to avoid per-invocation startup latency. Do not rewrite the hook's `python3` invocation.

This matches BMad v7, which runs every Python script in its skills with `uv run`.

## Cross-References

- `INSTALLATION.md` — Setup instructions for all supported LLM CLIs (Claude Code, Gemini CLI, Codex CLI, GitHub Copilot, Windsurf, OpenCode, Cursor, Aider)
- `USAGE.md` — End-user guide
