# Pipeline Guard

The guard enforces Mac's production pipeline: Mac can't present a Suno package without running the Style Prompt Builder and Lyric Transformer skills first. Those skills carry checks (artist names, production descriptors, character budgets, section tags) that a hand-built package skips.

Configure two layers. They write to different files, so batch both commands in one message.

**Standing order (all platforms).** Always run this. It appends the rule to `AGENTS.md`, creating the file if needed. Codex CLI, Cursor, GitHub Copilot, Windsurf, Amp, and Gemini CLI (when set to read AGENTS.md) read it.

```bash
uv run scripts/configure-guard.py --agents-md-path "{project-root}/AGENTS.md"
```

**Claude Code Stop hook.** Run this as well when `{project-root}/.claude/` exists. It merges a deterministic Stop hook into the settings without touching other configuration.

```bash
uv run scripts/configure-guard.py --settings-path "{project-root}/.claude/settings.local.json" --guard-script-path ".claude/skills/suno-agent-band-manager/scripts/pipeline-guard.py"
```

Both are idempotent. Each result has a `status`: `configured`, `already_configured`, or `error`. Report what was configured in Confirm.
