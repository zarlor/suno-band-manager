# Pipeline Guard

The owner asked to set up the pipeline guard. It enforces Mac's production pipeline: Mac can't present a Suno package without running the Style Prompt Builder and Lyric Transformer skills first. Those skills carry checks (reference names, production descriptors, character budgets, section tags) that a hand-built package skips.

There are three layers. Each writes its own file or settings entry, and every command is idempotent. Pass real paths: the script rejects a literal `{project-root}` token.

**Standing order (all platforms).** Always run this. It appends the rule to `AGENTS.md`, creating the file if needed. Codex CLI, Cursor, GitHub Copilot, Windsurf, Amp, and Gemini CLI (when set to read AGENTS.md) read it.

```bash
uv run {skill-root}/scripts/configure_guard.py --agents-md-path "{project-root}/AGENTS.md"
```

**Claude Code hooks.** Offer these when `{project-root}/.claude/` exists, and ask whether the owner wants the second one:

- *Pipeline guard (Stop hook)* — blocks a package when the transcript shows the builder or transformer didn't run that turn, when the sections are out of Create-screen order, or when a tagged Lyrics block changed without the transformer running.
- *Dominion guard (PreToolUse hook, optional)* — while Mac is awake, a Write or Edit outside the sanctum that the CREED.md Dominion doesn't allow stops and asks the owner to approve it. It does nothing in sessions where Mac isn't active.

```bash
uv run {skill-root}/scripts/configure_guard.py --settings-path "{project-root}/.claude/settings.local.json" --guard-script-path "{skill-root}/scripts/pipeline_guard.py" --dominion-hook
```

- Leave off `--dominion-hook` when the owner wants only the pipeline guard; running the command again later with it adds the Dominion guard and leaves the rest alone.
- `--guard-script-path` is this skill's own copy of the guard, wherever the skill is installed (the project, a plugin, a user-wide folder). The script writes the hook as `python3 "$CLAUDE_PROJECT_DIR"/<relative path>` when the guard is inside the project and by its absolute path otherwise. The hook runs on bare `python3` on purpose: it fires on every turn and write, and the guard is stdlib-only, so it skips `uv`'s startup.
- When a hook can't read what it needs (no transcript, no sanctum yet), it lets the turn or write through rather than block it.

**Reading the result.** Each entry in `results` has a `target` and a `status`:

- `configured` or `already_configured` → tell the owner in a line, in character, what is now guarded. A `replaced_command` beside `configured` means a hook left from an older install location was pointed at the current one; mention it.
- `error`, exit 2 → nothing was written (the guard script wasn't found at the path given, the settings file isn't valid JSON, or its `hooks` value has the wrong shape). Give the owner the `message` and stop; a hook pointing at a missing file would block every turn.
- Exit 1 → the command was incomplete (only one of `--settings-path` and `--guard-script-path`, `--dominion-hook` without both, or an unresolved path token). Fix the arguments and run it again.
