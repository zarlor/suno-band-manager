#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for analyze-input.py"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "analyze-input.py")


def run_script(*args):
    """Run the script and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True
    )
    return json.loads(result.stdout) if result.stdout else None, result.returncode


class TestAnalyzeInput:
    def test_basic_metrics(self):
        text = "Hello world\nThis is a test\nThree lines here"
        report, code = run_script("--text", text)
        assert report is not None
        m = report["metrics"]
        assert m["line_count"] == 3
        assert m["non_empty_line_count"] == 3
        assert m["word_count"] == 9
        assert m["character_count"] > 0

    def test_detects_existing_structure(self):
        text = "[Verse 1]\nSome lyrics here\nMore lyrics\n\n[Chorus]\nChorus line"
        report, code = run_script("--text", text)
        assert report is not None
        m = report["metrics"]
        assert m["has_existing_structure"] is True
        assert "Verse 1" in m["existing_tags"]
        assert "Chorus" in m["existing_tags"]

    def test_no_structure_detected(self):
        text = "Just raw text\nWith no brackets\nPlain poetry"
        report, code = run_script("--text", text)
        assert report is not None
        m = report["metrics"]
        assert m["has_existing_structure"] is False
        assert m["existing_tags"] == []

    def test_repeated_phrases(self):
        text = "come back to me tonight\nwhen the stars are bright\ncome back to me tonight\nunder the pale moonlight"
        report, code = run_script("--text", text)
        assert report is not None
        m = report["metrics"]
        phrases = [p["phrase"] for p in m["repeated_phrases"]]
        assert any("come back to me" in p for p in phrases)

    def test_suffix_matches(self):
        text = "Walking down the street\nFeeling the beat\nLooking for the light\nShining in the night"
        report, code = run_script("--text", text)
        assert report is not None
        m = report["metrics"]
        assert "potential_rhyme_pairs" not in m  # renamed: spelling is not rhyme
        rhymes = m["suffix_matches"]
        rhyme_words = [set(r["words"]) for r in rhymes]
        assert any({"street", "beat"} == w for w in rhyme_words) or any({"light", "night"} == w for w in rhyme_words)

    def test_short_structure_estimate(self):
        text = "\n".join(f"Line {i}" for i in range(1, 10))
        report, code = run_script("--text", text)
        assert report is not None
        m = report["metrics"]
        assert m["estimated_structure"] == "short"

    def test_medium_structure_estimate(self):
        text = "\n".join(f"Line number {i} of the song" for i in range(1, 25))
        report, code = run_script("--text", text)
        assert report is not None
        m = report["metrics"]
        assert m["estimated_structure"] == "medium"

    def test_long_structure_estimate(self):
        text = "\n".join(f"Line number {i} of a very long song" for i in range(1, 35))
        report, code = run_script("--text", text)
        assert report is not None
        m = report["metrics"]
        assert m["estimated_structure"] == "long"

    def test_source_hash_matches_sha256(self):
        # The hash is the authoritative LT-STATE / headless change-tracking
        # value the LLM reads instead of fabricating one.
        text = "come back to me tonight\nunder the pale moonlight"
        report, code = run_script("--text", text)
        assert report is not None
        m = report["metrics"]
        # Script normalizes literal "\n" to real newlines before hashing.
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert m["source_hash"] == expected
        assert len(m["source_hash"]) == 64

    def test_source_hash_changes_with_text(self):
        a, _ = run_script("--text", "first draft of the words")
        b, _ = run_script("--text", "second draft of the words")
        assert a["metrics"]["source_hash"] != b["metrics"]["source_hash"]

    def test_latin_only_script(self):
        report, _ = run_script("--text", "plain english line\nanother one")
        m = report["metrics"]
        assert m["script_type"] == "latin"
        assert m["mixed_script"] is False
        assert m["script_lines"]["latin"] == [1, 2]

    def test_non_latin_script(self):
        report, _ = run_script("--text", "夜の空に\n星が光る")
        m = report["metrics"]
        assert m["script_type"] == "non_latin"
        assert m["script_lines"]["non_latin"] == [1, 2]

    def test_mixed_script_flags_lines(self):
        text = "[Verse]\nwalking home tonight\n夜の空に\ncity 東京 lights"
        report, _ = run_script("--text", text)
        m = report["metrics"]
        assert m["mixed_script"] is True
        assert m["script_type"] == "mixed"
        assert m["script_lines"] == {"latin": [2], "non_latin": [3], "mixed": [4]}

    def test_accented_latin_is_latin(self):
        report, _ = run_script("--text", "canción del corazón\nça va très bien")
        assert report["metrics"]["script_type"] == "latin"

    def test_cyrillic_is_non_latin(self):
        report, _ = run_script("--text", "Тихая ночь")
        assert report["metrics"]["script_type"] == "non_latin"

    def test_unbroken_prose_flag(self):
        prose = ("I walked down to the river this morning and the water was higher than "
                 "I remembered it being when we were kids and nobody had told me why it rose")
        report, _ = run_script("--text", prose)
        assert report["metrics"]["unbroken_prose"] is True
        poem, _ = run_script("--text", "short line\nanother short line\nand one more")
        assert poem["metrics"]["unbroken_prose"] is False

    def test_spatial_layout_recorded(self):
        text = "Day   by   Day\n    the porch light hums\n\n\nand I wait\n\nstill"
        report, _ = run_script("--text", text)
        s = report["metrics"]["spatial_layout"]
        assert s["has_spatial_layout"] is True
        assert s["indented_lines"] == [2]
        assert s["internal_space_run_lines"] == [1]
        assert s["blank_line_gaps"] == [
            {"after_line": 2, "blank_lines": 2},
            {"after_line": 5, "blank_lines": 1},
        ]
        assert s["irregular_gaps"] is True

    def test_plain_stanzas_have_no_spatial_layout(self):
        text = "one line\ntwo line\n\nthree line\nfour line"
        report, _ = run_script("--text", text)
        s = report["metrics"]["spatial_layout"]
        assert s["has_spatial_layout"] is False
        assert s["irregular_gaps"] is False

    def test_report_structure(self):
        report, code = run_script("--text", "Some text")
        assert report is not None
        assert "script" in report
        assert "version" in report
        assert "timestamp" in report
        assert "status" in report
        assert "metrics" in report
        assert "findings" in report
        assert "summary" in report

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "analyze" in result.stdout.lower()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
