"""Configure pytest to collect test files with hyphens in names, and share a
small v7 sanctum fixture."""
import pytest

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


def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".py" and file_path.name.startswith("test-"):
        return pytest.Module.from_parent(parent, path=file_path)


@pytest.fixture
def v7_project(tmp_path):
    """A small v7 project: (project_root, sanctum). Identity files, memory/<kind>/,
    raw/, capabilities/, a Dominion inside CREED.md, a tended stamp."""
    sanctum = tmp_path.joinpath(*V7_REL)
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
    (tmp_path / "docs").mkdir()
    return tmp_path, sanctum

