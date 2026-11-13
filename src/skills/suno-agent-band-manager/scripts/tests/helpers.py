"""Shared test helpers: a small v7 sanctum project builder (formerly the
pytest `v7_project` fixture in conftest.py)."""

import contextlib
import io
import tempfile
from collections import namedtuple
from pathlib import Path

V7_REL = ("_bmad", "memory", "suno-agent-band-manager")
IDENTITY = ("PERSONA.md", "CREED.md", "BOND.md", "HOW-I-REMEMBER.md", "CAPABILITIES.md")

V7_CREED = """# Mac — Creed

## Mission

Make music.

## Dominion (Access Boundaries)

The one home of my write rule.

### Read Access
- `{project-root}/_bmad/memory/suno-agent-band-manager/` — own memory
- `docs/band-profiles/` — profiles

### Write Access
- `{project-root}/_bmad/memory/suno-agent-band-manager/` — own memory
- `docs/wip-*.md` — fragments

### The Write Rule

- **Routine sync** — `docs/not-a-rule.md` stays prose.

### Deny Zones

- `src/` — module source

### Notes
- Prose.

## Discipline Shards — Load On Demand

- `docs/also-not-a-rule.md`
"""


def make_v7_project(root):
    """Build a small v7 project under `root`: returns (project_root, sanctum).
    Identity files, memory/<kind>/, raw/, capabilities/, a Dominion inside
    CREED.md, a tended stamp."""
    root = Path(root)
    sanctum = root.joinpath(*V7_REL)
    for name in IDENTITY:
        (sanctum / name).parent.mkdir(parents=True, exist_ok=True)
        (sanctum / name).write_text(f"# {name}\n", encoding="utf-8")
    (sanctum / "CREED.md").write_text(V7_CREED, encoding="utf-8")
    (sanctum / "BOND.md").write_text("# Bond\n\n## Owner Summary\n\n- **Name:** Sam\n", encoding="utf-8")
    for kind in ("work", "owner", "bands", "catalog", "module", "disciplines", "incidents", "chronology", "sessions"):
        (sanctum / "memory" / kind).mkdir(parents=True, exist_ok=True)
    (sanctum / "raw").mkdir()
    (sanctum / "capabilities").mkdir()
    (sanctum / "memory" / "work" / "current.md").write_text("# Current Work\n\n- on a song\n", encoding="utf-8")
    (sanctum / "memory" / ".tended").write_text("2026-10-01\n", encoding="utf-8")
    (root / "docs").mkdir()
    return root, sanctum


CapturedOutput = namedtuple("CapturedOutput", "out err")


class OutputCapture:
    """A small stand-in for pytest's capsys: `with cap(): ...` sends stdout and
    stderr to buffers; `cap.readouterr()` returns (out, err) and resets them."""

    def __init__(self):
        self._out = io.StringIO()
        self._err = io.StringIO()

    @contextlib.contextmanager
    def __call__(self):
        with contextlib.redirect_stdout(self._out), contextlib.redirect_stderr(self._err):
            yield self

    def readouterr(self):
        captured = CapturedOutput(self._out.getvalue(), self._err.getvalue())
        self._out = io.StringIO()
        self._err = io.StringIO()
        return captured


class TempDirMixin:
    """setUp gives `self.tmp_path` (a fresh pathlib.Path, removed on cleanup)
    and `self.capsys` (an OutputCapture)."""

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)
        self.capsys = OutputCapture()

    def make_v7_project(self):
        return make_v7_project(self.tmp_path)


# ---------------------------------------------------------------------------
# A synthetic skill folder: small templates, a menu and a creed source, so the
# sanctum scripts are tested on inputs the tests own, never on the wording of
# the shipped prompt files.
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent.parent


def load_script(module_name, filename):
    """Import one of the (hyphen-named) scripts by path."""
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location(module_name, SCRIPTS_DIR / filename)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SKILL_MENU_CSV = (
    "code,name,description,action,skill,prompt\n"
    'CS,Create Song,"Create a song package.",create-song,,references/create-song.md\n'
    'RS,Refine Song,"Refine a song.",refine-song,,references/refine-song.md\n'
    'MB,Manage Bands,"Manage band profiles.",manage-profiles,suno-band-profile-manager,\n'
    'AA,Analyze Audio,"Measure a render.",analyze-audio,suno-feedback-elicitor,\n'
)

SKILL_ASSETS = {
    "PERSONA-template.md": """# Mac — Persona

> **Owner:** {user_name} · **Born:** {birth_date}

## Identity

A band manager for {user_name}.

## Model Awareness

Read the tier at the moment it matters.
The second line never changes.
The third line never changes.
The fourth line never changes.
The fifth line never changes.

## Evolution Log

- **{birth_date}** — First Breath. Met {user_name}.
""",
    "CREED-template.md": """# Mac — Creed (Core)

> **Owner:** {user_name} · **Born:** {birth_date}

## Mission

_Placeholder until the owner says what a great outcome is._

## Principles

- Always output everything.

## Standing Orders

- Capture before you discuss.

## Package Assembly Rule — CORE

Use the skills; hand over no package built from memory.

## Dominion (Access Boundaries)

{dominion}

## Discipline Shards — Load On Demand

Rules live in `memory/disciplines/`.
""",
    "BOND-template.md": """# Bond — {user_name}

## Owner Summary

- **Name:** {user_name}
- **Language:** {communication_language}

## Load These

| File | What |
|------|------|
| `docs/voice-context-{user_slug}.md` | the owner's voice |

## Boundaries Observed

_None yet._

## Notes Toward the Bond

_None yet._
""",
    "HOW-I-REMEMBER-template.md": """# How I Remember

## Layout

My sanctum is `{project-root}/_bmad/memory/suno-agent-band-manager/`.

## Tending

Tend when session notes pile up.
""",
    "PULSE-template.md": """# Mac — Pulse

> **Owner:** {user_name} · **Born:** {birth_date}

## Default Wake Behavior

Stage a report for the next live session.

## Owner Preferences

- **Enabled:** not yet asked
""",
    "MEMORY-template.md": """# Memory seed

> Each section seeds one standing file.

## Current Work

_Nothing in progress._

## User Preferences

- **Tier:** unknown

## Downloads

- **Cap:** unknown

## Default Exclusions

_None._

## Active Band Profiles

_None._

## Recently Published

<!-- derived:recently-published:start -->
<!-- derived:recently-published:end -->

## Catalog Status

<!-- derived:catalog-status:start -->
<!-- derived:catalog-status:end -->

## Module State

- Version: synthetic

## Pending / Parked Work

_None._

## Pulse Report

_(empty — a Pulse wake stages its report here)_

## Session History (recent)
""",
    "ACCESS-BOUNDARIES-template.md": """# Synthetic Boundaries

## Read Access

- `{project-root}/_bmad/memory/suno-agent-band-manager/` — own memory
- `{skill-root}/` — the skill's own bundle
- `docs/` — creative records
- `{band_profiles_folder}/` — band profiles
- `{songbook_folder}/` — the songbook

## Write Access

- `{project-root}/_bmad/memory/suno-agent-band-manager/` — own memory
- `docs/wip-*.md` — fragments
- `docs/voice-context-{username}.md` — the owner's voice file
- `{songbook_folder}/` — written by the song flows
- Band profiles are written through another skill, not directly

## The Write Rule

- Ask before writing outside the list.

## Deny Zones

- `src/` — module source
- `{project-root}/_bmad/config*` — config files
- Anything not listed above

## Notes

- Check a path with `{skill-root}/scripts/validate_path.py`.
""",
    "menu.csv": SKILL_MENU_CSV,
}

SKILL_CREED = """# Creed source (synthetic)

> Not loaded on waking.

## Mission

The species mission.

## Principles

- A principle the core carries.

## Research Discipline

Look it up before you claim it.

## Thematic Discipline — Read the Songbook Before Making Thematic Claims

Read the dossier first.

### Steps

1. Open the songbook.

### Why — the incident

Once, a theme was claimed unread.

## Workshop Capture Discipline

Capture verbatim first.

### Why — the incident

A swing was lost before it was written down.

## Package Assembly Rule

Invoke the builder and the transformer.
"""


def creed_source(skill):
    """Where the scripts read the creed source inside a skill folder (their one definition)."""
    return load_script("_sanctum_seed", "_sanctum_seed.py").creed_source(skill)


def make_skill(root, name="skill"):
    """Build the synthetic skill under `root/<name>`; returns its path."""
    skill = Path(root) / name
    (skill / "assets").mkdir(parents=True)
    for filename, text in SKILL_ASSETS.items():
        (skill / "assets" / filename).write_text(text, encoding="utf-8")
    creed = creed_source(skill)
    creed.parent.mkdir(parents=True, exist_ok=True)
    creed.write_text(SKILL_CREED, encoding="utf-8")
    return skill


def snapshot(folder):
    """{relative path: bytes} of every file under `folder`."""
    folder = Path(folder)
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*") if p.is_file()}
