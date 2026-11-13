#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for update_current.py — one song's bullet in current.md, changed in place."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "update_current.py"
SANCTUM = Path("_bmad/memory/suno-agent-band-manager")
REL = SANCTUM / "memory/work/current.md"

CURRENT = """# Current Work

- **Low Tide Ledger** (Tidewater Rail) — workshopping verse 2.
  Chorus locked; verse 2 needs the turn.
- **Salt Road** (Tidewater Rail) — brief: a slow road song, owner's pick of key.
"""


def run(root, *args, stdin=None):
    proc = subprocess.run([sys.executable, str(SCRIPT), str(root), *args], input=stdin,
                          capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout) if proc.stdout.strip() else None


class UpdateCurrent(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.path = self.root / REL
        self.path.parent.mkdir(parents=True)
        self.path.write_text(CURRENT, encoding="utf-8")
        # A checkpoint needs a v7 sanctum: its CREED.md is the marker.
        (self.root / SANCTUM / "CREED.md").write_text("# Creed\n", encoding="utf-8")

    def test_replaces_only_that_songs_bullet_and_continuation(self):
        code, out = run(self.root, "--song", "low tide ledger", "--text", "(Tidewater Rail) — swing 3 captured.")
        self.assertEqual((code, out["action"]), (0, "replaced"))
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("- **low tide ledger** (Tidewater Rail) — swing 3 captured.\n", text)
        self.assertNotIn("Chorus locked", text)
        self.assertIn("- **Salt Road** (Tidewater Rail) — brief: a slow road song, owner's pick of key.\n", text)

    def test_adds_a_new_song_at_the_end(self):
        code, out = run(self.root, "--song", "Ferry Lights", stdin="(Tidewater Rail) — new brief.\n")
        self.assertEqual((code, out["action"]), (0, "added"))
        self.assertTrue(self.path.read_text(encoding="utf-8").startswith(CURRENT))

    def test_dated_event_line_is_refused(self):
        code, out = run(self.root, "--song", "Low Tide Ledger", "--text", "2026-10-15: captured swing 3")
        self.assertEqual((code, out["status"]), (1, "refused"))
        self.assertEqual(self.path.read_text(encoding="utf-8"), CURRENT)

    def test_remove_drops_the_bullet(self):
        code, out = run(self.root, "--song", "Salt Road", "--remove")
        self.assertEqual((code, out["action"]), (0, "removed"))
        self.assertNotIn("Salt Road", self.path.read_text(encoding="utf-8"))

    def test_creates_the_file_with_a_heading(self):
        self.path.unlink()
        code, _ = run(self.root, "--song", "Salt Road", "--text", "brief.")
        self.assertEqual(code, 0)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "# Current Work\n\n- **Salt Road** brief.\n")

    def test_no_bmad_folder_is_bad_input(self):
        with tempfile.TemporaryDirectory() as bare:
            code, _ = run(bare, "--song", "x", "--text", "y")
        self.assertEqual(code, 2)

    def test_empty_entry_is_bad_input(self):
        code, out = run(self.root, "--song", "Salt Road", "--text", "   ")
        self.assertEqual((code, out["status"]), (2, "error"))
        self.assertEqual(self.path.read_text(encoding="utf-8"), CURRENT)

    def test_no_v7_sanctum_is_refused_and_nothing_is_created(self):
        """A checkpoint before the sanctum exists (an old store still to convert, or no
        birth yet) must not leave a stub sanctum behind."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "_bmad" / "_memory" / "band-manager-sidecar"
            legacy.mkdir(parents=True)
            (legacy / "MEMORY.md").write_text("# old\n", encoding="utf-8")
            for args in (("--text", "brief."), ("--remove",)):
                with self.subTest(args=args):
                    code, out = run(root, "--song", "Salt Road", *args)
                    self.assertEqual((code, out["status"]), (1, "refused"))
                    self.assertIn("no v7 sanctum", out["reason"])
                    self.assertFalse((root / "_bmad" / "memory").exists())
            self.assertEqual(sorted(p.name for p in (root / "_bmad").iterdir()), ["_memory"])

    def test_sanctum_without_its_creed_is_refused(self):
        (self.root / SANCTUM / "CREED.md").unlink()
        code, out = run(self.root, "--song", "Salt Road", "--text", "brief.")
        self.assertEqual((code, out["status"]), (1, "refused"))
        self.assertEqual(self.path.read_text(encoding="utf-8"), CURRENT)

    def test_unreadable_current_file_is_refused_and_left_alone(self):
        raw = b"# Current Work\n\n- **Salt Road** caf\xe9 brief.\n"
        self.path.write_bytes(raw)
        code, out = run(self.root, "--song", "Salt Road", "--text", "new brief.")
        self.assertEqual((code, out["status"]), (1, "refused"))
        self.assertIn("could not be read or written", out["reason"])
        self.assertEqual(self.path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
