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
    """A curated store is GREEN: MEMORY.md under its token budget with no packed
    lines; patterns/chronology large but under their ceilings."""
    (tmp_path / "MEMORY.md").write_text("- a short curated line\n" * 120)
    (tmp_path / "patterns.md").write_text("x" * 43000)
    (tmp_path / "chronology.md").write_text("x" * 94000)

    result = mod.check_health(tmp_path)
    assert result["maintenance_recommended"] is False
    assert result["needs_pruning"] == []


def test_memory_over_token_budget_with_few_lines(tmp_path):
    """Few lines, many tokens: a line count would pass this; the token budget flags it."""
    (tmp_path / "MEMORY.md").write_text(("y" * 590 + "\n") * 30)  # ~4.4k tokens, 30 lines
    result = mod.check_health(tmp_path)
    assert "MEMORY.md" in result["needs_pruning"]
    facts = result["files"]["MEMORY.md"]
    assert facts["metric"] == "tokens"
    assert facts["over_threshold"] is True
    assert facts["size_lines"] == 30


def test_packed_line_is_flagged(tmp_path):
    """One line hiding a whole session narrative is flagged even under budget."""
    (tmp_path / "MEMORY.md").write_text("- ok\n- " + "z" * 2000 + "\n- ok\n")
    result = mod.check_health(tmp_path)
    assert result["files"]["MEMORY.md"]["packed_lines"] == [{"line": 2, "chars": 2002}]
    assert "MEMORY.md" in result["needs_pruning"]


def test_companion_files_measured(tmp_path):
    """The voice file and mac-preferences are measured; over budget → offer compaction."""
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    (sanctum / "MEMORY.md").write_text("- ok\n")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "voice-context-sam.md").write_text("v" * 1000)
    (docs / "mac-preferences.md").write_text("p" * 100000)  # ~25k tokens
    result = mod.check_health(sanctum)  # project root inferred from the path
    assert result["companions"]["docs/voice-context-sam.md"]["over_threshold"] is False
    assert result["companions_over_budget"] == ["docs/mac-preferences.md"]
    assert "compaction" in result["recommendation"]
    assert result["maintenance_recommended"] is True


def test_index_coverage(tmp_path):
    """Organic files INDEX.md does not mention are reported."""
    (tmp_path / "MEMORY.md").write_text("- ok\n")
    (tmp_path / "INDEX.md").write_text("| `patterns.md` | x |\n| `_collection_*.txt` | y |\n")
    (tmp_path / "patterns.md").write_text("p")
    (tmp_path / "_collection_layout.txt").write_text("c")
    (tmp_path / "liner-notes.md").write_text("new organic file")
    (tmp_path / "sessions").mkdir()
    result = mod.check_health(tmp_path)
    assert result["index_unlisted"] == ["liner-notes.md"]
    assert result["maintenance_recommended"] is True


def test_spine_total_reported(tmp_path):
    for name in mod.SPINE:
        (tmp_path / name).write_text("x" * 400)
    result = mod.check_health(tmp_path)
    assert result["spine_total_tokens_est"] == 700
    assert result["spine_over_budget"] is False


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
    (staging / "MEMORY.md").write_text("a fairly long curated line here\n" * 500)  # over budget

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
