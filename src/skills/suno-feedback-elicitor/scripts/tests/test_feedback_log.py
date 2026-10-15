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


if __name__ == "__main__":
    unittest.main()
