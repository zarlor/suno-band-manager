#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for spacing-check.py: the writer's spacing must come through verbatim."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "spacing-check.py")

WRITER = "Day   by   Day\n    the porch light hums\n\n\nand I wait"


def run(original, transformed, *flags):
    result = subprocess.run(
        [sys.executable, SCRIPT, "--original-text", original, "--transformed-text", transformed, *flags],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout), result.returncode


def kinds(report, severity=None):
    return [f["category"] for f in report["findings"] if severity is None or f["severity"] == severity]


def test_tags_added_spacing_kept_passes():
    transformed = "[Verse 1]\nDay   by   Day\n    the porch light hums\n\n\n[Chorus]\nand I wait\n\n[End]"
    report, code = run(WRITER, transformed)
    assert report["status"] == "pass"
    assert code == 0
    assert report["metrics"]["whitespace_changes"] == 0
    assert report["metrics"]["blank_lines_removed"] == 0


def test_internal_spacing_flattened_is_high():
    transformed = "[Verse 1]\nDay by Day\n    the porch light hums\n\n\nand I wait"
    report, code = run(WRITER, transformed)
    assert report["status"] == "fail"
    assert code == 1
    issues = [f["issue"] for f in report["findings"] if f["severity"] == "high"]
    assert any("internal spacing" in i for i in issues)


def test_indentation_removed_is_high():
    transformed = "Day   by   Day\nthe porch light hums\n\n\nand I wait"
    report, _ = run(WRITER, transformed)
    issues = [f["issue"] for f in report["findings"] if f["severity"] == "high"]
    assert any("indentation" in i for i in issues)


def test_tab_vs_spaces_counts_as_indentation_change():
    report, _ = run("\tline one\nline two", "    line one\nline two")
    assert report["status"] == "fail"


def test_writer_blank_gap_shrunk_is_high():
    transformed = "Day   by   Day\n    the porch light hums\n\nand I wait"
    report, _ = run(WRITER, transformed)
    assert report["metrics"]["blank_lines_removed"] == 1
    assert report["status"] == "fail"


def test_blank_lines_added_at_section_break_are_fine():
    original = "line one\nline two"
    transformed = "[Verse 1]\nline one\n\n[Chorus]\nline two"
    report, _ = run(original, transformed)
    assert report["status"] == "pass"
    assert report["metrics"]["blank_lines_added"] == 1


def test_trailing_inline_tag_is_set_aside():
    report, _ = run("Day   by   Day", "Day   by   Day [Silence]")
    assert report["status"] == "pass"


def test_leading_inline_tag_keeps_indentation_check():
    report, _ = run("    soft line", "    [Whispered] soft line")
    assert report["status"] == "pass"
    report, _ = run("    soft line", "[Whispered] soft line")
    assert report["status"] == "fail"


def test_trailing_whitespace_only_is_low():
    report, code = run("line one  \nline two", "line one\nline two")
    assert report["status"] == "warning"
    assert kinds(report, "low") == ["spacing"]
    assert code == 1


def test_crlf_input_is_not_a_spacing_change():
    report, _ = run("line one\r\nline two", "line one\nline two")
    assert report["status"] == "pass"


def test_word_edit_is_info_listed_for_reporting():
    report, _ = run("the cold rain falls", "the cold rain pours")
    assert report["status"] == "pass"
    edits = [f for f in report["findings"] if f["category"] == "edit"]
    assert len(edits) == 1
    assert report["metrics"]["line_edits"] == 1


def test_word_fidelity_flags_word_change():
    report, _ = run("the cold rain falls", "the cold rain pours", "--word-fidelity")
    assert report["status"] == "fail"
    assert "word_fidelity" in kinds(report, "high")


def test_word_fidelity_allows_tags_only():
    report, _ = run("the cold rain falls", "[Verse]\nthe cold rain falls\n\n[End]", "--word-fidelity")
    assert report["status"] == "pass"
    assert report["metrics"]["word_fidelity_broken"] is False


def test_flatten_returns_flat_copy_and_savings():
    transformed = "[Verse 1]\nDay   by   Day\n    the porch light hums\n\n\nand I wait"
    report, _ = run(WRITER, transformed, "--flatten")
    assert report["flat_copy"] == "[Verse 1]\nDay by Day\nthe porch light hums\n\nand I wait"
    assert report["metrics"]["flat_saved_chars"] == len(transformed) - len(report["flat_copy"])


def test_flat_copy_omitted_by_default():
    report, _ = run("a", "a")
    assert "flat_copy" not in report


def test_missing_input_exits_2():
    result = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    assert result.returncode == 2
