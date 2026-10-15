#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for feedback-log.py"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "feedback-log.py")


def run(args: list[str]) -> tuple[int, dict | str]:
    result = subprocess.run([sys.executable, SCRIPT, "locate", *args], capture_output=True, text=True)
    try:
        return result.returncode, json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.returncode, result.stderr


class FeedbackLogLocateTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp_path = Path(td.name)

    def test_existing_log_reports_last_round(self):
        tmp_path = self.tmp_path
        log = tmp_path / "test-band" / "my-song.md"
        log.parent.mkdir()
        log.write_text("# My Song\n\n## Round 1 — 2026-09-20\ntried x\n\n## Round 2 — 2026-09-28\ntried y\n",
                       encoding="utf-8")
        code, out = run(["--band", "Test Band", "--title", "My Song!", "--history-dir", str(tmp_path)])
        self.assertEqual(code, 0)
        self.assertIs(out["exists"], True)
        self.assertEqual(out["path"], str(log))
        self.assertEqual(out["last_round"], 2)
        self.assertEqual(out["last_date"], "2026-09-28")
        self.assertEqual(out["next_round"], 3)
        self.assertEqual(out["candidates"], [])

    def test_missing_log_lists_near_matches(self):
        tmp_path = self.tmp_path
        band = tmp_path / "test-band"
        band.mkdir()
        (band / "my-song-v2.md").write_text("## Round 1 — 2026-09-01\n", encoding="utf-8")
        (band / "something-else.md").write_text("", encoding="utf-8")
        code, out = run(["--band", "test-band", "--title", "My Song", "--history-dir", str(tmp_path)])
        self.assertEqual(code, 0)
        self.assertIs(out["exists"], False)
        self.assertEqual(out["next_round"], 1)
        self.assertIsNone(out["last_round"])
        self.assertEqual(out["candidates"], [str(band / "my-song-v2.md")])

    def test_no_band_or_title_uses_session_stamp(self):
        tmp_path = self.tmp_path
        code, out = run(["--history-dir", str(tmp_path), "--stamp", "20261003-1500"])
        self.assertEqual(code, 0)
        self.assertEqual(out["band_or_session"], "20261003-1500")
        self.assertEqual(out["song_slug"], "20261003-1500")
        self.assertEqual(out["path"], str(tmp_path / "20261003-1500" / "20261003-1500.md"))

    def test_round_heading_without_date(self):
        tmp_path = self.tmp_path
        log = tmp_path / "b" / "s.md"
        log.parent.mkdir()
        log.write_text("## Round 3\n", encoding="utf-8")
        code, out = run(["--band", "b", "--title", "s", "--history-dir", str(tmp_path)])
        self.assertEqual(out["last_round"], 3)
        self.assertIsNone(out["last_date"])
        self.assertEqual(out["next_round"], 4)

    def test_bad_stamp_is_rejected(self):
        code, err = run(["--history-dir", str(self.tmp_path), "--stamp", "today"])
        self.assertEqual(code, 2)
        self.assertIn("YYYYMMDD-HHMM", err)


def run_append(args: list[str], stdin: str | None = None) -> tuple[int, dict | str]:
    result = subprocess.run([sys.executable, SCRIPT, "append", *args], capture_output=True, text=True, input=stdin)
    try:
        return result.returncode, json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.returncode, result.stderr


class FeedbackLogAppendTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp_path = Path(td.name)
        self.base = ["--band", "Test Band", "--title", "My Song", "--history-dir", str(self.tmp_path)]
        self.log = self.tmp_path / "test-band" / "my-song.md"

    def test_first_round_creates_log_with_heading_and_snapshot(self):
        code, out = run_append([*self.base, "--date", "2026-10-15", "--text", "Tried rawer vocals. Liked it.",
                                "--snapshot", '{"feedback_type": "vague", "round": 9}'])
        self.assertEqual(code, 0)
        self.assertEqual((out["status"], out["round"], out["created"], out["new_round"]), ("ok", 1, True, True))
        text = self.log.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# My Song\n"))
        self.assertIn("## Round 1 — 2026-10-15\n", text)
        self.assertIn("Tried rawer vocals. Liked it.", text)
        self.assertIn('{"feedback_type": "vague", "round": 1}', text)  # round set from the log, not the input

    def test_next_round_follows_last_and_locate_agrees(self):
        run_append([*self.base, "--date", "2026-10-14", "--text", "round one"])
        code, out = run_append([*self.base, "--date", "2026-10-15", "--text", "round two"])
        self.assertEqual((out["round"], out["created"]), (2, False))
        code, loc = run(self.base)
        self.assertEqual((loc["last_round"], loc["last_date"], loc["next_round"]), (2, "2026-10-15", 3))

    def test_round_last_adds_to_current_round(self):
        run_append([*self.base, "--date", "2026-10-14", "--text", "round one"])
        code, out = run_append([*self.base, "--round", "last", "--text", "Anchor: keep the bass tone"])
        self.assertEqual((code, out["round"], out["new_round"]), (0, 1, False))
        text = self.log.read_text(encoding="utf-8")
        self.assertEqual(text.count("## Round"), 1)
        self.assertTrue(text.rstrip().endswith("Anchor: keep the bass tone"))

    def test_round_last_on_empty_log_opens_round_one(self):
        code, out = run_append([*self.base, "--round", "last", "--text", "first anchor"])
        self.assertEqual((out["round"], out["new_round"]), (1, True))

    def test_text_from_stdin(self):
        code, out = run_append([*self.base, "--stdin"], stdin="from stdin\n")
        self.assertEqual(code, 0)
        self.assertIn("from stdin", self.log.read_text(encoding="utf-8"))

    def test_bad_snapshot_rejected_and_nothing_written(self):
        code, out = run_append([*self.base, "--snapshot", "[1, 2]"])
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "error")
        code, out = run_append([*self.base, "--snapshot", "{not json"])
        self.assertEqual(code, 1)
        self.assertFalse(self.log.exists())

    def test_nothing_to_append_rejected(self):
        code, out = run_append(self.base)
        self.assertEqual(code, 1)
        self.assertIn("nothing to append", out["error"])

    def test_bad_date_rejected(self):
        code, err = run_append([*self.base, "--date", "15/10/2026", "--text", "x"])
        self.assertEqual(code, 2)
        self.assertIn("YYYY-MM-DD", err)


if __name__ == "__main__":
    unittest.main()
