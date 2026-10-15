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
