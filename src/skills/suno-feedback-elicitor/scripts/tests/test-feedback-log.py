#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for feedback-log.py"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "feedback-log.py")


def run(args: list[str]) -> tuple[int, dict | str]:
    result = subprocess.run([sys.executable, SCRIPT, "locate", *args], capture_output=True, text=True)
    try:
        return result.returncode, json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.returncode, result.stderr


def test_existing_log_reports_last_round(tmp_path):
    log = tmp_path / "test-band" / "my-song.md"
    log.parent.mkdir()
    log.write_text("# My Song\n\n## Round 1 — 2026-09-20\ntried x\n\n## Round 2 — 2026-09-28\ntried y\n",
                   encoding="utf-8")
    code, out = run(["--band", "Test Band", "--title", "My Song!", "--history-dir", str(tmp_path)])
    assert code == 0
    assert out["exists"] is True and out["path"] == str(log)
    assert out["last_round"] == 2 and out["last_date"] == "2026-09-28" and out["next_round"] == 3
    assert out["candidates"] == []


def test_missing_log_lists_near_matches(tmp_path):
    band = tmp_path / "test-band"
    band.mkdir()
    (band / "my-song-v2.md").write_text("## Round 1 — 2026-09-01\n", encoding="utf-8")
    (band / "something-else.md").write_text("", encoding="utf-8")
    code, out = run(["--band", "test-band", "--title", "My Song", "--history-dir", str(tmp_path)])
    assert code == 0
    assert out["exists"] is False and out["next_round"] == 1 and out["last_round"] is None
    assert out["candidates"] == [str(band / "my-song-v2.md")]


def test_no_band_or_title_uses_session_stamp(tmp_path):
    code, out = run(["--history-dir", str(tmp_path), "--stamp", "20261003-1500"])
    assert code == 0
    assert out["band_or_session"] == "20261003-1500" and out["song_slug"] == "20261003-1500"
    assert out["path"] == str(tmp_path / "20261003-1500" / "20261003-1500.md")


def test_round_heading_without_date(tmp_path):
    log = tmp_path / "b" / "s.md"
    log.parent.mkdir()
    log.write_text("## Round 3\n", encoding="utf-8")
    code, out = run(["--band", "b", "--title", "s", "--history-dir", str(tmp_path)])
    assert out["last_round"] == 3 and out["last_date"] is None and out["next_round"] == 4


def test_bad_stamp_is_rejected(tmp_path):
    code, err = run(["--history-dir", str(tmp_path), "--stamp", "today"])
    assert code == 2 and "YYYYMMDD-HHMM" in err
