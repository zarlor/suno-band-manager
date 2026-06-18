#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for check-memory-health.py"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location(
    "check_memory_health",
    Path(__file__).parent.parent / "check-memory-health.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def test_healthy_files(tmp_path):
    """A realistically-curated store is GREEN.

    MEMORY.md can be char-heavy (long derived catalog lines) yet still healthy
    because it's line-bounded; patterns/chronology are large organic files but
    well under their generous ceilings.
    """
    (tmp_path / "MEMORY.md").write_text(("a line\n" * 102) + "x" * 23000)
    (tmp_path / "patterns.md").write_text("x" * 43000)
    (tmp_path / "chronology.md").write_text("x" * 94000)

    result = mod.check_health(tmp_path)
    assert result["maintenance_recommended"] is False
    assert result["needs_pruning"] == []


def test_memory_over_line_threshold(tmp_path):
    """MEMORY.md is flagged when it blows its ~200-line curated bound."""
    (tmp_path / "MEMORY.md").write_text("a line\n" * 250)
    (tmp_path / "patterns.md").write_text("x" * 100)
    (tmp_path / "chronology.md").write_text("x" * 100)

    result = mod.check_health(tmp_path)
    assert result["maintenance_recommended"] is True
    assert "MEMORY.md" in result["needs_pruning"]
    assert result["files"]["MEMORY.md"]["metric"] == "lines"


def test_chronology_over_char_threshold(tmp_path):
    """Organic reference files are flagged only on genuine runaway growth."""
    (tmp_path / "MEMORY.md").write_text("a line\n" * 10)
    (tmp_path / "patterns.md").write_text("x" * 100)
    (tmp_path / "chronology.md").write_text("x" * 130000)  # past 120000 ceiling

    result = mod.check_health(tmp_path)
    assert result["maintenance_recommended"] is True
    assert "chronology.md" in result["needs_pruning"]


def test_missing_files(tmp_path):
    """Missing files reported correctly."""
    result = mod.check_health(tmp_path)
    assert result["files"]["MEMORY.md"]["exists"] is False


def test_sessions_not_flagged(tmp_path):
    """Large raw session files are reported in a count but never flagged."""
    (tmp_path / "MEMORY.md").write_text("x" * 100)
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    (sessions / "2026-05-27.md").write_text("x" * 50000)  # huge raw log

    result = mod.check_health(tmp_path)
    assert result["maintenance_recommended"] is False
    assert result["needs_pruning"] == []
    assert result["session_files"] == 1


def test_sanctum_dir_override(tmp_path, monkeypatch, capsys):
    """--sanctum-dir takes precedence over the positional path."""
    import json
    real = tmp_path / "real"
    real.mkdir()
    (real / "MEMORY.md").write_text("a line\n" * 10)
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "MEMORY.md").write_text("a line\n" * 250)  # over the line bound

    monkeypatch.setattr(
        sys, "argv",
        [
            "check-memory-health.py", str(real),
            "--sanctum-dir", str(staging),
        ],
    )
    mod.main()
    result = json.loads(capsys.readouterr().out)
    assert result["maintenance_recommended"] is True
    assert "MEMORY.md" in result["needs_pruning"]
