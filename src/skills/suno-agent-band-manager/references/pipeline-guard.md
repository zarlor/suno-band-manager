# Pipeline Guard

Load this when the owner asks to set up the pipeline guard (BMad's post-install message points them to you).

The guard enforces Mac's production pipeline: Mac can't present a Suno package without running the Style Prompt Builder and Lyric Transformer skills first. Those skills carry checks (artist names, production descriptors, character budgets, section tags) that a hand-built package skips.

There are three layers. Each writes its own file or settings entry, and every command is idempotent.

**Standing order (all platforms).** Always run this. It appends the rule to `AGENTS.md`, creating the file if needed. Codex CLI, Cursor, GitHub Copilot, Windsurf, Amp, and Gemini CLI (when set to read AGENTS.md) read it.

```bash
uv run {skill-root}/scripts/configure-guard.py --agents-md-path "{project-root}/AGENTS.md"
```

**Claude Code hooks.** Offer these when `{project-root}/.claude/` exists, and ask whether the owner wants the second one:

- *Pipeline guard (Stop hook)* — blocks a package when the transcript shows the builder or transformer didn't run that turn, or when the sections are out of Create-screen order.
- *Dominion guard (PreToolUse hook, optional)* — while Mac is awake, a Write or Edit outside the sanctum that the CREED.md Dominion doesn't allow stops and asks the owner to approve it. It does nothing in sessions where Mac isn't active.

```bash
uv run {skill-root}/scripts/configure-guard.py --settings-path "{project-root}/.claude/settings.local.json" --guard-script-path ".claude/skills/suno-agent-band-manager/scripts/pipeline-guard.py" --dominion-hook
```

Leave off `--dominion-hook` when the owner wants only the pipeline guard; running the command again later with it adds the Dominion guard and leaves the rest alone. When a hook can't read what it needs (no transcript, no sanctum yet), it lets the turn or write through rather than block it.

Each result has a `target` and a `status` (`configured`, `already_configured`, or `error`). Tell the owner in a line, in character, what is now guarded.
