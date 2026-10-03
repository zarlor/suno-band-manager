# Feedback Elicitor

The Feedback Elicitor turns your reactions to a Suno generation ("it feels too busy", "the vocals sound robotic") into concrete changes: style prompt and exclusion edits, slider moves, lyric adjustments, and editor or Studio suggestions. It sorts feedback into five types — clear, positive, vague, contradictory, technical — and handles each differently, and it keeps a per-song log so later rounds pick up where the last one stopped.

## When to Use Directly vs. Through Mac

Use it directly (`/suno-feedback-elicitor`) when you've heard a generation and want to work through what to change. Mac also calls it while refining a song, then hands the adjustments to the Style Prompt Builder and Lyric Transformer for you.

## Where Things Live

- **Workflow and rules:** `SKILL.md`
- **Headless use** (`--headless`, `--headless:analyze`; flags, writes, output JSON): `references/headless-contract.md`
- **What it writes** (iteration log, band-profile history): `references/durable-writes.md`
- **Adjustment knowledge:** `references/suno-parameter-map.md`, `references/model-controls.md`, `references/technical-resolution.md`, `references/feedback-triage-guide.md`
- **Audio analysis:** `references/audio-analysis-scripts.md` (scripts) and `references/gemini-audio-analysis.md` (AI listening tools)
- **Scripts:** `scripts/` — each one documents itself with `uv run scripts/<name>.py --help`

Album and playlist ordering is the `suno-playlist-sequencer` skill's job.

## Part of the Suno Band Manager Module

This skill works with any LLM CLI supporting the [Agent Skills](https://agentskills.io) standard. For the full guided experience, invoke Mac — the orchestrating agent.
