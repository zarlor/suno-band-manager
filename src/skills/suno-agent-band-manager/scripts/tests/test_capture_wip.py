#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for capture-wip.py — verbatim, attributed, dated capture into a WIP file."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "capture-wip.py"

WIP = """# Low Tide Ledger — workshop fragments

> **Status:** workshopping the second verse.

## Verse 2 — what it needs

The turn.

## Swings tried

_(none yet)_
"""

SWING = "    Low tide, low tide\nshow me what the water hides  \n```not a fence```\n"


def run(root, *args, stdin=None):
    proc = subprocess.run([sys.executable, str(SCRIPT), str(root), *args], input=stdin,
                          capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout) if proc.stdout.strip() else None


class CaptureWip(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "docs").mkdir()

    def wip(self, text=WIP):
        path = self.root / "docs" / "wip-low-tide-ledger-fragments.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_capture_is_verbatim_attributed_dated_and_replaces_the_placeholder(self):
        path = self.wip()
        code, out = run(self.root, "--title", "Low Tide Ledger", "--source", "ChatGPT",
                        "--label", "Swing 1 — verse 2 turn", "--date", "2026-10-15", stdin=SWING)
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "written")
        text = path.read_text()
        self.assertIn("### Swing 1 — verse 2 turn — ChatGPT, 2026-10-15", text)
        self.assertIn(SWING, text)  # byte for byte, leading spaces and trailing spaces kept
        self.assertIn("````\n", text)  # fence longer than the triple backticks inside
        self.assertNotIn("_(none yet)_", text)
        for line in ("## Verse 2 — what it needs", "The turn.", "> **Status:** workshopping the second verse."):
            self.assertIn(line, text)

    def test_second_capture_appends_after_the_first(self):
        path = self.wip()
        run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 1", stdin="one\n")
        run(self.root, "--title", "Low Tide Ledger", "--source", "owner", "--label", "Swing 2", stdin="two\n")
        text = path.read_text()
        self.assertLess(text.index("### Swing 1"), text.index("### Swing 2"))

    def test_capture_lands_inside_the_section_before_the_next_heading(self):
        path = self.wip(WIP.replace("_(none yet)_\n", "### Swing 0 — Mac, 2026-10-01\n\n```\nzero\n```\n\n## Later\n\nkeep me\n"))
        run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 1", stdin="one\n")
        text = path.read_text()
        self.assertLess(text.index("### Swing 1"), text.index("## Later"))
        self.assertIn("keep me", text)

    def test_missing_wip_is_created_with_the_section(self):
        code, out = run(self.root, "--title", "New Song", "--source", "Mac", "--label", "Swing 1", stdin="hello\n")
        self.assertEqual(code, 0)
        self.assertTrue(out["created"])
        text = (self.root / "docs" / "wip-new-song-fragments.md").read_text()
        self.assertIn("## Swings tried", text)
        self.assertIn("hello\n", text)

    def test_critique_attaches_to_its_entry(self):
        path = self.wip()
        run(self.root, "--title", "Low Tide Ledger", "--source", "ChatGPT", "--label", "Swing 1", stdin="one\n")
        run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 2", stdin="two\n")
        code, _ = run(self.root, "--title", "Low Tide Ledger", "--label", "Swing 1", "--critique", "Too on the nose.",
                      "--date", "2026-10-15")
        self.assertEqual(code, 0)
        text = path.read_text()
        self.assertLess(text.index("**Critique (2026-10-15):** Too on the nose."), text.index("### Swing 2"))

    def test_refusals(self):
        self.wip()
        code, out = run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "x", stdin="  \n")
        self.assertEqual((code, out["status"]), (2, "refused"))
        code, out = run(self.root, "--file", "../outside.md", "--source", "Mac", "--label", "x", stdin="a")
        self.assertEqual((code, out["status"]), (1, "refused"))
        code, out = run(self.root, "--title", "Low Tide Ledger", "--label", "nope", "--critique", "c")
        self.assertEqual((code, out["status"]), (1, "refused"))


if __name__ == "__main__":
    unittest.main()
