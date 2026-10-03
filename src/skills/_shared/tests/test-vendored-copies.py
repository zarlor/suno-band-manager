#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Every skill's scripts/_shared/ must be a byte-identical copy of src/skills/_shared/.

Installers copy skill folders one at a time, so each skill vendors the helpers it
imports. Edit only src/skills/_shared/, then run `uv run dev-tools/sync-shared.py`.
"""

from pathlib import Path

SHARED = Path(__file__).resolve().parent.parent
SKILLS = SHARED.parent
CANON = sorted(SHARED.glob("*.py"))


def test_canon_exists():
    assert CANON, "no helpers found in src/skills/_shared/"


def test_every_importing_skill_vendors_the_helpers():
    for script in SKILLS.glob("suno-*/scripts/*.py"):
        if '"_shared"' in script.read_text(encoding="utf-8"):
            assert (script.parent / "_shared").is_dir(), f"{script} imports _shared but its skill has no scripts/_shared/"


def test_vendored_copies_match_canon():
    drift = []
    for dest in SKILLS.glob("suno-*/scripts/_shared"):
        for src in CANON:
            target = dest / src.name
            if not target.is_file() or target.read_bytes() != src.read_bytes():
                drift.append(str(target.relative_to(SKILLS)))
    assert not drift, "vendored _shared copies drifted — run `uv run dev-tools/sync-shared.py`: " + ", ".join(drift)
