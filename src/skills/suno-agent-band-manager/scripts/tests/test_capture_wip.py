#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for capture_wip.py — verbatim, attributed, dated capture into a WIP file."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "capture_wip.py"

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


SONG = """---
title: "Harbor Lights"
band_profile: paper-lanterns
status: wip
---

# Harbor Lights

## Lyrics

```
[Verse 1]
The porch light flickers on
```
"""

# Pasted external text that carries its own markdown headings.
HEADED = "## Verse idea\nLow tide, low tide\n### alt ending\nshow me what the water hides\n"


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
        text = path.read_text(encoding="utf-8")
        self.assertIn("### Swing 1 — verse 2 turn — ChatGPT, 2026-10-15", text)
        self.assertIn(SWING, text)  # byte for byte, leading spaces and trailing spaces kept
        self.assertIn("````\n", text)  # fence longer than the triple backticks inside
        self.assertNotIn("_(none yet)_", text)
        for line in ("## Verse 2 — what it needs", "The turn.", "> **Status:** workshopping the second verse."):
            self.assertIn(line, text)

    def test_capture_reports_each_sung_lines_syllables(self):
        self.wip()
        code, out = run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 2",
                        stdin="[Verse 2]\nFound her ledger in a coffee can\n\nPaid in full\n")
        self.assertEqual(code, 0)
        self.assertEqual(out["line_syllables"], [
            {"line": "Found her ledger in a coffee can", "syllables": 9},
            {"line": "Paid in full", "syllables": 3}])

    def test_dry_run_counts_and_writes_nothing(self):
        path = self.wip()
        code, out = run(self.root, "--title", "Low Tide Ledger", "--label", "draft", "--dry-run",
                        stdin="Paid in full\n")
        self.assertEqual((code, out["status"]), (0, "counted"))
        self.assertEqual(out["line_syllables"], [{"line": "Paid in full", "syllables": 3}])
        self.assertEqual(path.read_text(encoding="utf-8"), WIP)

    def test_second_capture_appends_after_the_first(self):
        path = self.wip()
        run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 1", stdin="one\n")
        run(self.root, "--title", "Low Tide Ledger", "--source", "owner", "--label", "Swing 2", stdin="two\n")
        text = path.read_text(encoding="utf-8")
        self.assertLess(text.index("### Swing 1"), text.index("### Swing 2"))

    def test_capture_lands_inside_the_section_before_the_next_heading(self):
        path = self.wip(WIP.replace("_(none yet)_\n", "### Swing 0 — Mac, 2026-10-01\n\n```\nzero\n```\n\n## Later\n\nkeep me\n"))
        run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 1", stdin="one\n")
        text = path.read_text(encoding="utf-8")
        self.assertLess(text.index("### Swing 1"), text.index("## Later"))
        self.assertIn("keep me", text)

    def test_missing_wip_is_created_with_the_section(self):
        code, out = run(self.root, "--title", "New Song", "--source", "Mac", "--label", "Swing 1", stdin="hello\n")
        self.assertEqual(code, 0)
        self.assertTrue(out["created"])
        text = (self.root / "docs" / "wip-new-song-fragments.md").read_text(encoding="utf-8")
        self.assertIn("## Swings tried", text)
        self.assertIn("hello\n", text)

    def test_critique_attaches_to_its_entry(self):
        path = self.wip()
        run(self.root, "--title", "Low Tide Ledger", "--source", "ChatGPT", "--label", "Swing 1", stdin="one\n")
        run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 2", stdin="two\n")
        code, _ = run(self.root, "--title", "Low Tide Ledger", "--label", "Swing 1", "--critique", "Too on the nose.",
                      "--date", "2026-10-15")
        self.assertEqual(code, 0)
        text = path.read_text(encoding="utf-8")
        self.assertLess(text.index("**Critique (2026-10-15):** Too on the nose."), text.index("### Swing 2"))

    def test_refusals(self):
        self.wip()
        code, out = run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "x", stdin="  \n")
        self.assertEqual((code, out["status"]), (2, "refused"))
        code, out = run(self.root, "--file", "../outside.md", "--source", "Mac", "--label", "x", stdin="a")
        self.assertEqual((code, out["status"]), (1, "refused"))
        code, out = run(self.root, "--title", "Low Tide Ledger", "--label", "nope", "--critique", "c")
        self.assertEqual((code, out["status"]), (1, "refused"))


    # --- headings inside captured material are material ---

    def test_capture_after_material_with_headings_lands_after_it_not_inside(self):
        path = self.wip()
        run(self.root, "--title", "Low Tide Ledger", "--source", "ChatGPT", "--label", "Swing 1", stdin=HEADED)
        code, _ = run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 2", stdin="two\n")
        self.assertEqual(code, 0)
        text = path.read_text(encoding="utf-8")
        self.assertIn(HEADED, text)  # the first capture is still whole
        first_close = text.index(HEADED) + len(HEADED)
        self.assertGreater(text.index("### Swing 2 — Mac"), first_close)
        self.assertEqual(text.count("## Swings tried"), 1)

    def test_critique_on_material_with_headings_lands_after_its_fence(self):
        path = self.wip()
        run(self.root, "--title", "Low Tide Ledger", "--source", "ChatGPT", "--label", "Swing 1", stdin=HEADED)
        run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 2", stdin="two\n")
        code, _ = run(self.root, "--title", "Low Tide Ledger", "--label", "Swing 1", "--critique", "Too tidy.",
                      "--date", "2026-10-15")
        self.assertEqual(code, 0)
        text = path.read_text(encoding="utf-8")
        self.assertIn(HEADED, text)
        critique = text.index("**Critique (2026-10-15):** Too tidy.")
        self.assertGreater(critique, text.index(HEADED) + len(HEADED))
        self.assertLess(critique, text.index("### Swing 2 — Mac"))

    def test_a_heading_line_inside_material_is_not_an_entry(self):
        path = self.wip()
        run(self.root, "--title", "Low Tide Ledger", "--source", "ChatGPT", "--label", "Swing 1",
            stdin="### Swing 9 — someone, 2026-01-01\nquoted, not an entry\n")
        before = path.read_text(encoding="utf-8")
        code, out = run(self.root, "--title", "Low Tide Ledger", "--label", "Swing 9", "--critique", "c")
        self.assertEqual((code, out["status"]), (1, "refused"))
        self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_an_unclosed_fence_earlier_in_the_file_does_not_hide_the_section(self):
        path = self.wip(WIP.replace("The turn.\n", "The turn.\n\n```\nnotes that never close\n"))
        run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 1", stdin="one\n")
        code, _ = run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 2", stdin="two\n")
        self.assertEqual(code, 0)
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count("## Swings tried"), 1)
        self.assertLess(text.index("### Swing 1"), text.index("### Swing 2"))

    # --- a critique goes to the entry with that whole label ---

    def test_critique_label_is_matched_whole_not_as_a_prefix(self):
        path = self.wip()
        run(self.root, "--title", "Low Tide Ledger", "--source", "ChatGPT", "--label", "Swing 3 — verse 2 turn",
            "--date", "2026-10-14", stdin="turn\n")
        run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 3",
            "--date", "2026-10-15", stdin="plain\n")
        code, out = run(self.root, "--title", "Low Tide Ledger", "--label", "Swing 3", "--critique", "Flat.",
                        "--date", "2026-10-16")
        self.assertEqual(code, 0, out)
        text = path.read_text(encoding="utf-8")
        self.assertGreater(text.index("**Critique (2026-10-16):** Flat."), text.index("### Swing 3 — Mac, 2026-10-15"))
        # And the longer label still reaches its own entry.
        run(self.root, "--title", "Low Tide Ledger", "--label", "Swing 3 — verse 2 turn", "--critique", "Sharp.",
            "--date", "2026-10-16")
        text = path.read_text(encoding="utf-8")
        self.assertLess(text.index("**Critique (2026-10-16):** Sharp."), text.index("### Swing 3 — Mac, 2026-10-15"))

    def test_critique_with_only_a_prefix_of_a_label_is_refused_and_lists_the_entries(self):
        path = self.wip()
        run(self.root, "--title", "Low Tide Ledger", "--source", "ChatGPT", "--label", "Swing 3 — verse 2 turn",
            "--date", "2026-10-14", stdin="turn\n")
        before = path.read_text(encoding="utf-8")
        code, out = run(self.root, "--title", "Low Tide Ledger", "--label", "Swing 3", "--critique", "Flat.")
        self.assertEqual((code, out["status"]), (1, "refused"))
        self.assertEqual(out["entries"], ["Swing 3 — verse 2 turn — ChatGPT, 2026-10-14"])
        self.assertEqual(path.read_text(encoding="utf-8"), before)

    # --- --critique writes: never with --dry-run, never without a label ---

    def test_critique_with_dry_run_or_without_label_is_bad_input_and_writes_nothing(self):
        path = self.wip()
        run(self.root, "--title", "Low Tide Ledger", "--source", "Mac", "--label", "Swing 1", stdin="one\n")
        before = path.read_text(encoding="utf-8")
        for extra in (["--label", "Swing 1", "--dry-run"], ["--dry-run"], []):
            with self.subTest(extra=extra):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT), str(self.root), "--title", "Low Tide Ledger",
                     "--critique", "Too on the nose.", *extra],
                    capture_output=True, text=True)
                self.assertEqual(proc.returncode, 2)
                self.assertNotIn("Traceback", proc.stderr)
                self.assertIn("--critique", proc.stderr)
                self.assertEqual(path.read_text(encoding="utf-8"), before)

    # --- --file: capture into an existing file (a songbook entry) ---

    def song(self):
        path = self.root / "docs" / "songbook" / "band" / "song.md"
        path.parent.mkdir(parents=True)
        path.write_text(SONG, encoding="utf-8")
        return path

    def test_file_capture_appends_the_section_and_keeps_the_entry(self):
        path = self.song()
        code, out = run(self.root, "--file", "docs/songbook/band/song.md", "--source", "owner",
                        "--label", "Bridge draft", "--date", "2026-10-15", "--text", "x")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["status"], "written")
        self.assertIs(out["created"], False)
        self.assertEqual(out["path"], "docs/songbook/band/song.md")
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(SONG))  # every original byte, in place
        self.assertEqual(text[len(SONG):], "\n## Swings tried\n\n### Bridge draft — owner, 2026-10-15\n\n```\nx\n```\n")

    def test_file_naming_a_missing_path_is_refused_and_creates_nothing(self):
        self.song()
        missing = self.root / "docs" / "songbook" / "band" / "sonng.md"
        code, out = run(self.root, "--file", "docs/songbook/band/sonng.md", "--source", "owner",
                        "--label", "Bridge draft", "--text", "x")
        self.assertEqual((code, out["status"]), (1, "refused"))
        self.assertIn("does not exist", out["reason"])
        self.assertFalse(missing.exists())
        self.assertEqual(sorted(p.name for p in missing.parent.iterdir()), ["song.md"])

    def test_file_reached_through_a_symlink_or_dot_dot_is_written_once_and_reported(self):
        path = self.song()
        link = self.root.parent / (self.root.name + "-link")
        link.symlink_to(self.root, target_is_directory=True)
        self.addCleanup(link.unlink)
        code, out = run(self.root, "--file", str(link / "docs" / "songbook" / "band" / "song.md"),
                        "--source", "owner", "--label", "Via link", "--text", "one")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["path"], "docs/songbook/band/song.md")
        code, out = run(self.root, "--file", "docs/wip/../songbook/band/song.md",
                        "--source", "owner", "--label", "Via dots", "--text", "two")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["path"], "docs/songbook/band/song.md")
        text = path.read_text(encoding="utf-8")
        self.assertEqual((text.count("### Via link"), text.count("### Via dots")), (1, 1))

    def test_symlink_inside_the_project_to_a_file_outside_is_refused(self):
        outside = self.root.parent / (self.root.name + "-outside.md")
        outside.write_text("mine\n", encoding="utf-8")
        self.addCleanup(outside.unlink)
        (self.root / "docs" / "wip-linked.md").symlink_to(outside)
        code, out = run(self.root, "--file", "docs/wip-linked.md", "--source", "Mac", "--label", "x", "--text", "a")
        self.assertEqual((code, out["status"]), (1, "refused"))
        self.assertEqual(outside.read_text(encoding="utf-8"), "mine\n")


if __name__ == "__main__":
    unittest.main()
