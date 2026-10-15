#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for genre-coverage.py"""

import json
import re
import sys
import unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent))

spec = spec_from_file_location(
    "genre_coverage",
    Path(__file__).parent.parent / "genre-coverage.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def _band(tmp_path):
    songbook = tmp_path / "docs" / "songbook" / "paper-lanterns"
    songbook.mkdir(parents=True)
    song = songbook / "harbor-lights.md"
    song.write_text('title: "Harbor Lights"\nstatus: published\n\n'
                    "## Style Prompt\n\n```\nchamber folk, close vocal\n```\n", encoding="utf-8")
    (tmp_path / "docs" / "band-profiles").mkdir()
    (tmp_path / "docs" / "band-profiles" / "paper-lanterns.yaml").write_text(
        'name: "Paper Lanterns"\nreference_tracks:\n  - "Artist One — warm"\n', encoding="utf-8")
    return song


def _run(capsys, *argv):
    with patch.object(sys, "argv", ["genre-coverage.py", *argv]), capsys():
        return mod.main()


def _break_profile(tmp_path):
    (tmp_path / "docs" / "band-profiles" / "paper-lanterns.yaml").write_text(
        'name: "Paper Lanterns\nreference_tracks: [unclosed\n', encoding="utf-8")


class TestGenreCoverage(TempDirMixin, unittest.TestCase):
    def test_title_of_prefers_frontmatter(self):
        text = 'title: "Harbor Lights"\n\n# Wrong Heading\n'
        assert mod.title_of(text, "fallback") == "Harbor Lights"

    def test_title_of_falls_back_to_heading(self):
        text = "no frontmatter here\n\n# Sunday Driver\n"
        assert mod.title_of(text, "fallback") == "Sunday Driver"

    def test_title_of_uses_fallback_when_nothing_matches(self):
        assert mod.title_of("plain prose, nothing useful", "the-slug") == "the-slug"

    def test_status_of_reads_status_line(self):
        assert mod.status_of("title: X\nstatus: published\n") == "published"
        assert mod.status_of("no status field") == "unknown"

    def test_first_style_prompt_extracts_code_block(self):
        text = (
            "## Style Prompt\n\n"
            "```\nprogressive groove metal, down-tuned, halftime groove\n```\n"
        )
        assert "progressive groove metal" in mod.first_style_prompt(text)

    def test_first_style_prompt_returns_none_without_heading(self):
        assert mod.first_style_prompt("no style prompt heading here") is None

    def test_labeled_territory_extracts_verbatim(self):
        text = "**Reference territory:** Blink-182 / Matchbox 20, '90s alt\n"
        assert mod.labeled_territory(text) == ["Blink-182 / Matchbox 20, '90s alt"]

    def test_profile_fields_extracts_curated_fields_verbatim(self):
        profile = {
            "genre": "Harbor folk / chamber pop",
            "reference_tracks": ["Artist One — warm close vocal", "Band 182 — fast punk edge"],
            "style_alternatives": {"ballad": "Warm folk, brushed drums"},
            "voice_profiles": [{"name": "Voice A", "use_case": "Sparse intimate verses"}],
            "catalog": [{"title": "Harbor Lights", "genre_applied": "chamber folk (Artist One territory)"}],
        }
        f = mod.profile_fields(profile)
        assert f["genre"] == "Harbor folk / chamber pop"
        assert "Band 182 — fast punk edge" in f["reference_tracks"]  # digits survive
        assert f["style_alternatives"] == [("ballad", "Warm folk, brushed drums")]
        assert f["voice_use_cases"] == [("Voice A", "Sparse intimate verses")]
        assert f["genre_applied"] == [("Harbor Lights", "chamber folk (Artist One territory)")]

    def test_profile_fields_tolerates_missing_or_odd_shapes(self):
        assert mod.profile_fields(None) == {}
        assert mod.profile_fields({"reference_tracks": None, "catalog": "x"}) == {}

    def test_collect_band_and_json_run(self):
        """End-to-end: a band dir with one published song produces a JSON summary."""
        songbook = self.tmp_path / "docs" / "songbook" / "paper-lanterns"
        songbook.mkdir(parents=True)
        (songbook / "harbor-lights.md").write_text(
            'title: "Harbor Lights"\nstatus: published\n\n'
            "## Style Prompt\n\n```\nprogressive groove metal, down-tuned\n```\n"
            "Reference territory: Pantera-heavy lineage\n",
            encoding="utf-8",
        )

        with patch.object(
            sys, "argv",
            ["genre-coverage.py", str(self.tmp_path), "--format", "json"],
        ), self.capsys():
            mod.main()
        out = json.loads(self.capsys.readouterr().out)
        assert out["band_count"] == 1
        band = out["bands"][0]
        assert band["band"] == "paper-lanterns"
        assert band["entries"] == 1
        # The generated doc was written, with the style prompt verbatim.
        doc = (self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md").read_text(encoding="utf-8")
        assert "progressive groove metal, down-tuned" in doc
        assert "Pantera-heavy lineage" in doc
        assert "Absence here does not prove" in doc

    def test_empty_catalog_is_clean_noop_json(self):
        """No docs/songbook/ yet → clean exit with a zeroed JSON result, not exit 2."""
        with patch.object(
            sys, "argv",
            ["genre-coverage.py", str(self.tmp_path), "--format", "json"],
        ), self.capsys():
            # Must NOT raise SystemExit — an empty catalog is a normal no-op.
            mod.main()
        out = json.loads(self.capsys.readouterr().out)
        assert out == {"bands": [], "band_count": 0}

    def test_empty_catalog_is_clean_noop_text(self):
        """Empty catalog in text mode prints a friendly no-op line, exits cleanly."""
        with patch.object(
            sys, "argv",
            ["genre-coverage.py", str(self.tmp_path)],
        ), self.capsys():
            mod.main()
        captured = self.capsys.readouterr().out
        assert "empty catalog" in captured.lower() or "nothing to index" in captured.lower()

    def test_check_reports_missing_then_current_then_stale(self):
        song = _band(self.tmp_path)
        assert _run(self.capsys, str(self.tmp_path), "--check") == 1
        assert "missing" in self.capsys.readouterr().out
        assert _run(self.capsys, str(self.tmp_path)) == 0
        self.capsys.readouterr()
        assert _run(self.capsys, str(self.tmp_path), "--check", "--format", "json") == 0
        assert json.loads(self.capsys.readouterr().out)["bands"][0]["index"] == "current"
        song.write_text(song.read_text(encoding="utf-8") + "\nnew note\n", encoding="utf-8")
        assert _run(self.capsys, str(self.tmp_path), "--check") == 1
        assert "stale" in self.capsys.readouterr().out

    def test_check_writes_nothing(self):
        _band(self.tmp_path)
        _run(self.capsys, str(self.tmp_path), "--check")
        assert not (self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md").exists()

    def test_regeneration_keeps_text_outside_markers_and_stamps_time(self):
        _band(self.tmp_path)
        out = self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md"
        out.write_text("Owner note above.\n" + mod.AUTOGEN_START + "\nold\n" + mod.AUTOGEN_END + "\nBelow.\n",
                       encoding="utf-8")
        _run(self.capsys, str(self.tmp_path))
        doc = out.read_text(encoding="utf-8")
        assert doc.startswith("Owner note above.") and doc.rstrip().endswith("Below.")
        assert "\nold\n" not in doc
        assert re.search(r"on \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", doc)
        assert "Artist One — warm" in doc

    def test_profile_yaml_error_is_recorded_rendered_and_exits_1(self):
        _band(self.tmp_path)
        _break_profile(self.tmp_path)
        assert _run(self.capsys, str(self.tmp_path), "--format", "json") == 1
        band = json.loads(self.capsys.readouterr().out)["bands"][0]
        assert "paper-lanterns.yaml" in band["profile_error"]
        doc = (self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md").read_text(encoding="utf-8")
        assert "PROFILE ERROR" in doc and "paper-lanterns.yaml" in doc

    def test_check_fails_on_profile_error_even_when_fingerprint_matches(self):
        _band(self.tmp_path)
        _break_profile(self.tmp_path)
        _run(self.capsys, str(self.tmp_path))  # writes an index whose fingerprint matches
        self.capsys.readouterr()
        assert _run(self.capsys, str(self.tmp_path), "--check", "--format", "json") == 1
        row = json.loads(self.capsys.readouterr().out)["bands"][0]
        assert row["index"] == "profile_error" and "paper-lanterns.yaml" in row["profile_error"]

    def test_good_profile_reports_no_error(self):
        _band(self.tmp_path)
        assert _run(self.capsys, str(self.tmp_path), "--format", "json") == 0
        assert json.loads(self.capsys.readouterr().out)["bands"][0]["profile_error"] is None

    def test_unknown_band_exits_2_with_reason(self):
        _band(self.tmp_path)
        assert _run(self.capsys, str(self.tmp_path), "--band", "paper-lantern", "--check") == 2
        err = self.capsys.readouterr().err
        assert "paper-lantern" in err and "paper-lanterns" in err
        assert _run(self.capsys, str(self.tmp_path), "--band", "nope", "--format", "json") == 2
        assert json.loads(self.capsys.readouterr().out)["status"] == "error"

    def test_unknown_band_without_songbook_exits_2(self):
        assert _run(self.capsys, str(self.tmp_path), "--band", "ghost") == 2


if __name__ == "__main__":
    unittest.main()
