#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for genre-coverage.py"""

import json
import sys
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

sys.path.insert(0, str(Path(__file__).parent.parent))

spec = spec_from_file_location(
    "genre_coverage",
    Path(__file__).parent.parent / "genre-coverage.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def test_title_of_prefers_frontmatter():
    text = 'title: "Harbor Lights"\n\n# Wrong Heading\n'
    assert mod.title_of(text, "fallback") == "Harbor Lights"


def test_title_of_falls_back_to_heading():
    text = "no frontmatter here\n\n# Sunday Driver\n"
    assert mod.title_of(text, "fallback") == "Sunday Driver"


def test_title_of_uses_fallback_when_nothing_matches():
    assert mod.title_of("plain prose, nothing useful", "the-slug") == "the-slug"


def test_status_of_reads_status_line():
    assert mod.status_of("title: X\nstatus: published\n") == "published"
    assert mod.status_of("no status field") == "unknown"


def test_first_style_prompt_extracts_code_block():
    text = (
        "## Style Prompt\n\n"
        "```\nprogressive groove metal, down-tuned, halftime groove\n```\n"
    )
    assert "progressive groove metal" in mod.first_style_prompt(text)


def test_first_style_prompt_returns_none_without_heading():
    assert mod.first_style_prompt("no style prompt heading here") is None


def test_anchors_splits_on_commas():
    a1, a2 = mod.anchors("progressive groove metal, down-tuned crush, dark")
    assert a1 == "progressive groove metal"
    assert a2 == "down-tuned crush"


def test_free_text_clauses_captures_slash_lists():
    clauses = mod.free_text_clauses(
        "leans into Counting Crows / Wallflowers / Wilco for the verse feel"
    )
    assert any("Counting Crows" in c for c in clauses)


def test_free_text_clauses_rejects_section_word_slashes():
    # Intro / Verse / Chorus are structure tokens, not artist references.
    clauses = mod.free_text_clauses("Intro / Verse / Chorus structure")
    assert not any("Verse" in c for c in clauses)


def test_noise_filter_drops_stats_and_stopwords():
    assert mod._noise("New Orleans")        # stopword
    assert mod._noise("128 BPM")            # stats noise
    assert not mod._noise("Songs:Ohia territory")


def test_collect_band_and_json_run(tmp_path, capsys, monkeypatch):
    """End-to-end: a band dir with one published song produces a JSON summary."""
    songbook = tmp_path / "docs" / "songbook" / "paper-lanterns"
    songbook.mkdir(parents=True)
    (songbook / "harbor-lights.md").write_text(
        'title: "Harbor Lights"\nstatus: published\n\n'
        "## Style Prompt\n\n```\nprogressive groove metal, down-tuned\n```\n"
        "Reference territory: Pantera-heavy lineage\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys, "argv",
        ["genre-coverage.py", str(tmp_path), "--format", "json"],
    )
    mod.main()
    out = json.loads(capsys.readouterr().out)
    assert out["band_count"] == 1
    band = out["bands"][0]
    assert band["band"] == "paper-lanterns"
    assert band["entries"] == 1
    # The generated doc was written.
    assert (tmp_path / "docs" / "paper-lanterns-genre-coverage.md").exists()


def test_empty_catalog_is_clean_noop_json(tmp_path, capsys, monkeypatch):
    """No docs/songbook/ yet → clean exit with a zeroed JSON result, not exit 2."""
    monkeypatch.setattr(
        sys, "argv",
        ["genre-coverage.py", str(tmp_path), "--format", "json"],
    )
    # Must NOT raise SystemExit — an empty catalog is a normal no-op.
    mod.main()
    out = json.loads(capsys.readouterr().out)
    assert out == {"bands": [], "band_count": 0}


def test_empty_catalog_is_clean_noop_text(tmp_path, capsys, monkeypatch):
    """Empty catalog in text mode prints a friendly no-op line, exits cleanly."""
    monkeypatch.setattr(
        sys, "argv",
        ["genre-coverage.py", str(tmp_path)],
    )
    mod.main()
    captured = capsys.readouterr().out
    assert "empty catalog" in captured.lower() or "nothing to index" in captured.lower()
