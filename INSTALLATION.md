# Installation Guide

Mac follows the [Agent Skills](https://agentskills.io) open standard. The same SKILL.md files work across multiple LLM CLI tools. Choose the installation path that matches your setup.

> **Requirement: `uv`.** The module's Python scripts run via `uv run`, which reads each script's [PEP 723](https://peps.python.org/pep-0723/) inline metadata and auto-provisions dependencies (`pyyaml`, and optionally `librosa`/`numpy`) — no virtualenv or manual `pip install` to manage. Install it once: `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux/WSL) or `pip install uv`. Dependency-free scripts can fall back to plain `python3` (3.11+) if `uv` is unavailable. (BMad v7 runs its own skill scripts with `uv run` too.)

## Installation from a Clone (Recommended)

Works with any LLM CLI that supports Agent Skills: Claude Code, Gemini CLI, Codex CLI, GitHub Copilot, Windsurf, OpenCode.

### 1. Clone the repository

```bash
git clone https://github.com/zarlor/bmad-suno-band-manager.git
cd bmad-suno-band-manager
```

### 2. Link skills

**macOS / Linux / WSL:**
```bash
./link-skills.sh
```

**Windows (PowerShell):**
```powershell
./link-skills.ps1
```

This links the six Suno skills and `bmod-suno`, the module record BMad's setup reads, into `.claude/skills/`, `.agents/skills/` and `.gemini/skills/`. The `.agents/skills/` path is the portable standard scanned by most LLM CLI tools. The script also removes links to skills that no longer exist (such as the retired `suno-setup`).

> **Windows note:** Symlinks require either Developer Mode (Settings → Update & Security → For developers → Developer Mode) or running PowerShell as Administrator. The script will print a clear error if neither is enabled.

### 3. Configure with BMad

Install BMad's `bmad` skill if the project doesn't have it (BMad v7; the skill's version string is 6.13.0-next or later):

```bash
npx skills add bmad-code-org/BMAD-METHOD --skill bmad
```

Then ask it, in your LLM CLI:

```
bmad setup suno
```

It asks the five questions described under [Configuration](#configuration) and writes the answers to `_bmad/config.toml`. You can skip this step: every skill runs on the default answers until you set them.

### 4. First run

Activate Mac using your tool's skill invocation. Mac doesn't open with a form; he learns your name, how you like to work and your bands as you go.

**Claude Code:**
```
/suno-agent-band-manager
```

**Gemini CLI:**
Activate the `suno-agent-band-manager` skill via Gemini's skill activation flow.

**Other tools:**
Skills in `.agents/skills/` are auto-discovered at session start. Invoke by name or description match.

### 5. Start creating

Tell Mac what kind of song you want. See the [Usage Guide](src/skills/suno-agent-band-manager/references/USAGE.md) for all features.

---

## Installation without a clone (`npx skills`)

BMad v7 installs modules with the `skills` CLI instead of the old `npx bmad-method install` installer. To install the module straight from GitHub:

```bash
npx skills add bmad-code-org/BMAD-METHOD --skill bmad   # if the project doesn't have BMad's bmad skill yet
npx skills add zarlor/suno-band-manager
```

Select the six `suno-*` skills and `bmod-suno` (the module record; `bmad setup` can't find the module without it), then ask `bmad setup suno`. This route installs the skills only. The top-level `scripts/` folder (multi-machine sync) and the `CLAUDE.md` / `GEMINI.md` / `AGENTS.md` standing orders don't come with it; see [Multi-Machine Sync](#multi-machine-sync-optional) and [Pipeline Guard](#pipeline-guard-recommended).

BMad v6 installs (6.12 and earlier, `npx bmad-method install`) are not supported from module 4.0.0.

---

## Configuration

`bmad setup suno` asks these questions in order:

| Key | Values | Default | What it decides |
|---|---|---|---|
| `suno_tier` | `free`, `pro`, `premier` | `free` | Which Suno models and features Mac recommends |
| `default_mode` | `demo`, `studio`, `jam` | `demo` | Mac's starting interaction mode |
| `pytorch_audio_tools` | `on`, `off` | `off` | Whether the audio scripts take tempo from Beat This! and the Demucs tools are available (see [Optional: Audio Analysis](#optional-audio-analysis)) |
| `band_profiles_folder` | folder, relative to the project root | `docs/band-profiles` | Where band profiles are stored |
| `songbook_folder` | folder, relative to the project root | `docs/songbook` | Where saved songs and lyrics are stored |

The answers live in `_bmad/config.toml` under `[modules.suno]`:

```toml
[modules.suno]
suno_tier = "pro"
default_mode = "studio"
pytorch_audio_tools = "off"
band_profiles_folder = "docs/band-profiles"
songbook_folder = "docs/songbook"
```

To override them without touching that file, put a `[modules.suno]` table in `_bmad/custom/config.toml` (shared with the team) or `_bmad/custom/config.user.toml` (personal, not committed). Later layers win. Skills read the merged result through `_bmad/scripts/resolve_config.py`; the module's scripts read the same layers through their vendored `scripts/_shared/bmad_config.py`.

**Changing an answer:** run `bmad setup suno` again and say which answer to change, or edit the file yourself. Rerunning setup asks only questions you haven't answered and never overwrites an answer you didn't change.

**Your name and language** are not config keys. Mac takes them from his memory (the Owner Summary in `_bmad/_memory/band-manager-sidecar/BOND.md`), or, before that exists, from your `docs/voice-context-<name>.md` file; if neither exists he asks. The other skills reply in the language you write in.

**Without BMad:** with no `_bmad/` directory, every skill uses the defaults in the table above. Mac mentions once that `bmad setup suno` sets the tier, mode and folders, and carries on. Tier and mode preferences you give Mac in conversation ("I'm on Pro", "switch to Studio mode") are saved to his memory either way.

**Help:** ask `bmad` what to do next, or about the module ("what can the suno module do?"); it answers from the module's help files in `src/skills/bmod-suno/help/`.

---

## Pipeline Guard (Recommended)

The module ships a Stop hook script (`.claude/skills/suno-agent-band-manager/scripts/pipeline-guard.py`) that enforces Mac's mandatory production pipeline. It blocks any response containing a Suno package if `suno-style-prompt-builder` and `suno-lyric-transformer` weren't invoked during the session.

**Why:** Without this guard, the agent may hand-build packages from conversation memory instead of running them through the skills. The skills contain critical guardrails (artist name detection, production descriptor checks, character budget validation, section tag validation) that cannot be replicated from memory.

**Auto-configuration:** Ask Mac to "set up the pipeline guard". He runs `configure-guard.py` (in `suno-agent-band-manager/scripts/`), which appends the standing order to `AGENTS.md` and, when the project has a `.claude/` folder, merges the Stop hook into `.claude/settings.local.json`. Both steps are safe to repeat. The manual steps below are for reference or if you prefer to set it up yourself.

### Claude Code Setup

Add to your `.claude/settings.local.json` (create if it doesn't exist):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/skills/suno-agent-band-manager/scripts/pipeline-guard.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Adjust the path to match where you cloned the module. If using a standalone install, the path would be relative to your project root.

### Standing Orders (All Platforms)

The module ships three standing-order files at the repo root with identical content:

- **`CLAUDE.md`** — auto-loaded by Claude Code
- **`GEMINI.md`** — auto-loaded by Gemini CLI
- **`AGENTS.md`** — auto-loaded by Codex CLI and OpenCode

These files contain mandatory skill activation discipline (run pre-activate scripts, read persona/creed/capabilities, present the dynamic menu, load voice context) and the Suno Pipeline Rule (never hand-build packages — always invoke `suno-style-prompt-builder` and `suno-lyric-transformer`). They exist because some LLM CLIs (notably Gemini) interpret the declarative `SKILL.md` activation style more literally than Claude Code does, so cross-platform robustness requires explicit standing orders outside the skill files themselves.

If you have your own `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` in the project root that you don't want overwritten, merge the Suno rules into it manually rather than letting the module's copies replace yours. The module's rules are scoped to the Suno skills, so they should compose cleanly with project-level instructions for unrelated work.

---

## Tool-Specific Notes

### Claude Code

Primary development and testing platform. Full feature support including:
- Skill invocation via `/suno-agent-band-manager`
- Sub-agent spawning for parallel skill execution
- Bash tool for `uv run` script execution (validation, analysis)
- Full read/write file access for memory, profiles, songbook
- Pipeline guard Stop hook (see above)

Skills discovered from: `.claude/skills/`, `.agents/skills/`

### Gemini CLI

Skills discovered from: `.agents/skills/`, `.gemini/skills/`

Gemini CLI uses the same SKILL.md format. The skill activates when Gemini identifies a matching task from the skill description. User approval is requested before activation.

`link-skills.sh` / `link-skills.ps1` also link the skills into `.gemini/skills/`, Gemini's native path, because Gemini doesn't always follow the symlinks in `.agents/skills/`.

### Codex CLI (OpenAI)

Skills discovered from: `.agents/skills/`

Codex uses the same SKILL.md format. Skills can be invoked explicitly via `$skill-name` or through the `/skills` menu.

Custom instructions live in `AGENTS.md` (Codex's equivalent of `CLAUDE.md`). The module does not require an `AGENTS.md` file but you can create one for project-level instructions.

### GitHub Copilot

Skills discovered from: `.agents/skills/`, `.github/skills/`, `.claude/skills/`

Works across Copilot coding agent, Copilot CLI, and VS Code agent mode.

### Windsurf

Skills discovered from: `.agents/skills/`, `.windsurf/skills/`

Activate skills via `@skill-name` in Cascade input.

### OpenCode

Skills discovered from: `.agents/skills/`, `.opencode/skills/`, `.claude/skills/`

OpenCode also supports custom agent definitions in `.opencode/agents/` with granular per-agent tool permissions.

### Cursor

Skills discovered from: `.cursor/skills/` only (does not scan `.agents/skills/`).

Cursor requires skills in its own directory. Copy (don't symlink) if symlinks cause issues:
```bash
mkdir -p .cursor/skills
cp -r src/skills/suno-* src/skills/bmod-suno .cursor/skills/
```

Note: Copying means `git pull` won't auto-update Cursor's copies. Re-copy after updates.

### Aider

Aider does not support the Agent Skills format. You can load reference documents manually:
```bash
aider \
  --read src/skills/suno-agent-band-manager/references/SUNO-REFERENCE.md \
  --read src/skills/suno-agent-band-manager/references/USAGE.md
```

This provides Suno context but not the interactive Mac workflow.

---

## Updating

From a clone:

```bash
git pull
```

Symlinks point into `src/skills/`, so changes are picked up immediately. When a release adds or retires a skill, rerun `./link-skills.sh` (or `./link-skills.ps1`); it links new skills and removes links to retired ones. If you installed with `npx skills`, run `npx skills update` instead, or ask `bmad` to update.

Then run `bmad setup suno`. It asks any new questions, keeps your existing answers, and offers to delete skills the module has retired.

Keep `uv` current as well (`uv self update`). The first audio-script run after an update fetches any new dependency versions automatically. Check the release's **Upgrade at a glance** block in `CHANGELOG.md` for anything else to do.

### Upgrading from module 3.x (BMad v6)

Module 4.0.0 drops BMad v6 support and the `suno-setup` skill.

1. Install BMad's `bmad` skill: `npx skills add bmad-code-org/BMAD-METHOD --skill bmad`.
2. `git pull`, then rerun `./link-skills.sh` (or `./link-skills.ps1`). It removes the dangling `suno-setup` links and links `bmod-suno`.
3. Ask `bmad setup suno`. It doesn't read the old `_bmad/config.yaml`, so answer the five questions again (see [Configuration](#configuration)). It offers to delete the retired `suno-setup` skill and to remove other v6 leftovers (it backs up `_bmad/` first).
4. If you used the pipeline guard, nothing changes: the hook still runs `suno-agent-band-manager/scripts/pipeline-guard.py`.

Mac's memory (`_bmad/_memory/band-manager-sidecar/`), band profiles, songbook and voice files are not touched.

---

## Multi-Machine Sync (Optional)

Mac stores user-generated content (voice files, band profiles, songbook, WIP files) under `docs/`, which is gitignored so personal content stays out of the repo. To move that content between machines without git, use the bundled pack/unpack scripts.

**Important — these scripts ship at the repository's top-level `scripts/` folder.** They are user-facing entry points (commands you run directly), distinct from the agent's internal scripts that live inside the skill at `.claude/skills/suno-agent-band-manager/scripts/`. If you installed the module with `npx skills` and only the skills landed (no top-level `scripts/` folder), you can either: (a) clone this repo separately and run the scripts from there pointed at your project root, or (b) copy `pack-portable.sh` / `unpack-portable.sh` (and the `.ps1` variants) from the [GitHub repo](https://github.com/zarlor/suno-band-manager/tree/main/scripts) into your project's `scripts/` folder.

**Pack on the source machine:**

```bash
# macOS / Linux / WSL
bash scripts/pack-portable.sh

# Windows (PowerShell)
./scripts/pack-portable.ps1
```

This creates `docs/portable-sync.tar.gz` containing the documented module data:
- `docs/voice-context-*.md` — your voice/identity files
- `docs/songbook/**/*.md` — your songs
- `docs/band-profiles/**/*.yaml` — your band identities
- `docs/wip-*.md` — work in progress

Move the tar.gz to your other machine (any way you like — USB, scp, cloud sync, etc.) and unpack:

```bash
# macOS / Linux / WSL
bash scripts/unpack-portable.sh

# Windows (PowerShell)
./scripts/unpack-portable.ps1
```

**Customizing what gets packed:** Copy `portable-manifest.example.yaml` to `portable-manifest.yaml` at your project root and edit it. The manifest takes precedence over the defaults — useful if you've added companion files (e.g. detailed background docs referenced from your voice file's Companion Files table) that you also want synced. The example file shows commented patterns for common cases.

---

## Optional: Audio Analysis

For objective audio measurements (BPM, key, energy, chord progressions, playlist sequencing), the audio scripts depend on `librosa`, `numpy`, and `pyloudnorm`. Running them via `uv run` provisions them automatically from each script's PEP 723 metadata — no manual install needed. They require Python 3.12+ (librosa 1.0's floor); `uv run` downloads a compatible Python on its own when the system one is older. Only if you're running without `uv` do you install them by hand:

```bash
pip install librosa numpy pyloudnorm
```

Three opt-in scripts in the Feedback Elicitor need PyTorch: `beat-grid.py` (Beat This! beat tracking), `vocal-placement.py` (Demucs vocal placement), and `section-map.py` (Demucs plus faster-whisper: maps a render's sections against its lyrics). Through `uv run`, the first run provisions PyTorch (1–3 GB) and downloads the model weights; nothing else in the module pulls them in. **GPU:** on Linux and WSL, PyPI's current PyTorch build targets CUDA 13, which needs NVIDIA driver 580 or newer; with an older driver (or no NVIDIA GPU) the tools fall back to CPU automatically. Native Windows gets PyPI's CPU-only PyTorch build (use WSL for the GPU), and Apple Silicon Macs run on CPU. **Intel Macs are not supported** for these tools: PyTorch's last Intel-Mac build predates numpy 2, which librosa 1.0 requires. On CPU, Beat This! takes a few seconds per track; Demucs takes minutes. Demucs's first run may print an "unauthenticated requests to the HF Hub" warning — harmless. `section-map.py` also downloads a Whisper model on first run (medium, about 1.5 GB). Whisper runs on CPU, because its GPU build needs CUDA 12 libraries that PyTorch's CUDA 13 build doesn't ship; expect about a minute per song.

**Using Beat This! for tempo everywhere:** turn on **PyTorch audio tools** with `bmad setup suno` (config key `pytorch_audio_tools`). The audio scripts then take tempo and beats from Beat This! instead of librosa. With it off, they keep using librosa and never download PyTorch. Any of them also accepts `--tempo-source librosa|beat-this` for a single run.

Without `uv` and without these deps, the audio scripts return JSON with install instructions (exit code 2). The full song creation and refinement workflow works without audio analysis.

---

## Troubleshooting

**Skills not discovered:** Verify symlinks exist in the expected directory for your tool. Run `ls -la .agents/skills/` to check.

**Permission denied on link-skills.sh:** Run `chmod +x link-skills.sh` first.

**Python scripts fail:** The module's scripts run via `uv run`, which reads each script's PEP 723 inline metadata and auto-provisions dependencies (`pyyaml`, and optionally `librosa`/`numpy`). If `uv` is missing, install it (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`). Most scripts are dependency-free and also run under plain Python 3.10+ (`python3 scripts/<name>.py`); scripts that need `pyyaml` require either `uv` or a manual `pip install pyyaml`. The one exception is the `pipeline-guard.py` Stop-hook command, which is invoked directly with `python3` (a hot path — kept off `uv` to avoid per-call startup latency).

**Mac says the module has no answers yet:** `bmad setup suno` hasn't been run in this project. Run it, or ignore the note: every skill uses the defaults.

**`bmad setup suno` reports an unknown module:** BMad can't see the `bmod-suno` record. Rerun `./link-skills.sh`, or, for an `npx skills` install, add `bmod-suno` with `npx skills add zarlor/suno-band-manager --skill bmod-suno`.

**A `suno-setup` skill still shows up:** it was retired in 4.0.0. Rerun `./link-skills.sh` to drop the dangling link, and let `bmad setup suno` delete any installed copy.

**Symlinks not working (Windows):** Run `link-skills.ps1` from an elevated PowerShell, or enable Developer Mode (Settings → Update & Security → For developers → Developer Mode) and re-run from a normal PowerShell. As a last resort, copy the `src/skills/suno-*` and `src/skills/bmod-suno` directories into `.agents/skills/` manually — but you'll need to re-copy after every `git pull`.
