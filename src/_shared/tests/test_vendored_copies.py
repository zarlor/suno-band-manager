#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Every skill's scripts/_shared/ holds byte-identical copies of the src/_shared/ helpers it imports.

Installers copy skill folders one at a time, so each skill vendors the helpers it
imports. Edit only src/_shared/, then run `uv run dev-tools/sync-shared.py`.
"""

import unittest
from pathlib import Path

SHARED = Path(__file__).resolve().parent.parent
SKILLS = SHARED.parent / "skills"
CANON = sorted(SHARED.glob("*.py"))


class TestVendoredCopies(unittest.TestCase):
    def test_canon_exists(self):
        self.assertTrue(CANON, "no helpers found in src/_shared/")

    def test_every_importing_skill_vendors_the_helpers(self):
        for script in SKILLS.glob("suno-*/scripts/*.py"):
            if '"_shared"' in script.read_text(encoding="utf-8"):
                self.assertTrue((script.parent / "_shared").is_dir(), f"{script} imports _shared but its skill has no scripts/_shared/")

    def test_vendored_copies_match_canon(self):
        """Each skill vendors exactly the helpers its scripts import, byte-identical to the canon."""
        import subprocess
        import sys

        tool = SHARED.parent.parent / "dev-tools" / "sync-shared.py"
        proc = subprocess.run([sys.executable, str(tool), "--check"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, "vendored _shared copies drifted — run `uv run dev-tools/sync-shared.py`:\n" + proc.stdout)


if __name__ == "__main__":
    unittest.main()
