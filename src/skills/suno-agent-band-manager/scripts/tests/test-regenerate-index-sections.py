#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Tests for regenerate-index-sections.py"""

import sys
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

sys.path.insert(0, str(Path(__file__).parent.parent))

spec = spec_from_file_location(
    "regenerate_index_sections",
    Path(__file__).parent.parent / "regenerate-index-sections.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


SONG_TEXT = (
    "---\n"
    'title: "The Slide"\n'
    "band_profile: lennys-voice\n"
    "status: published\n"
    "date: 2026-01-15\n"
    "---\n\n"
    "**Status: LOCKED — Published 2026-01-15. A firearm-as-cog confession.**\n"
)


def _scaffold(tmp_path, memory_body):
    (tmp_path / "docs" / "band-profiles").mkdir(parents=True)
    (tmp_path / "docs" / "band-profiles" / "lennys-voice.yaml").write_text(
        'name: "Lenny\'s Voice"\n', encoding="utf-8"
    )
    songbook = tmp_path / "docs" / "songbook" / "lennys-voice"
    songbook.mkdir(parents=True)
    (songbook / "the-slide.md").write_text(SONG_TEXT, encoding="utf-8")
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    memory = sanctum / "MEMORY.md"
    memory.write_text(memory_body, encoding="utf-8")
    return memory


def test_parse_song_reads_frontmatter_and_body(tmp_path):
    p = tmp_path / "song.md"
    p.write_text(SONG_TEXT, encoding="utf-8")
    song = mod.parse_song(p)
    assert song["title"] == "The Slide"
    assert song["band"] == "lennys-voice"
    assert song["frontmatter_status"] == "published"
    assert song["body_status"] == "LOCKED"
    assert song["body_date"] == "2026-01-15"


def test_is_published_requires_both_markers():
    assert mod.is_published({"frontmatter_status": "published", "body_status": "LOCKED"})
    assert not mod.is_published({"frontmatter_status": "published", "body_status": "WIP"})
    assert not mod.is_published({"frontmatter_status": "wip", "body_status": "LOCKED"})


def test_band_display_map_uses_profile_name(tmp_path):
    (tmp_path / "docs" / "band-profiles").mkdir(parents=True)
    (tmp_path / "docs" / "band-profiles" / "lennys-voice.yaml").write_text(
        'name: "Lenny\'s Voice"\n', encoding="utf-8"
    )
    out = mod.band_display_map(tmp_path)
    assert out["lennys-voice"] == "Lenny's Voice"


def test_band_display_map_falls_back_to_titlecased_slug(tmp_path):
    (tmp_path / "docs" / "band-profiles").mkdir(parents=True)
    (tmp_path / "docs" / "band-profiles" / "solitary-fire.yaml").write_text(
        "tier: pro\n", encoding="utf-8"
    )
    out = mod.band_display_map(tmp_path)
    assert out["solitary-fire"] == "Solitary Fire"


def test_replace_section_swaps_marked_content():
    text = (
        "intro\n"
        "<!-- derived:catalog-status:start -->\nOLD\n<!-- derived:catalog-status:end -->\n"
        "outro\n"
    )
    new, ok = mod.replace_section(text, "catalog-status", "NEW CONTENT")
    assert ok is True
    assert "NEW CONTENT" in new
    assert "OLD" not in new


def test_replace_section_reports_missing_markers():
    new, ok = mod.replace_section("no markers here", "catalog-status", "X")
    assert ok is False


def test_migrate_section_wraps_existing_heading():
    text = "# Top\n\n## Catalog Status\n\n- one band\n\n## Other\n"
    new, migrated = mod.migrate_section(text, "## Catalog Status", "catalog-status")
    assert migrated is True
    assert "<!-- derived:catalog-status:start -->" in new
    assert "<!-- derived:catalog-status:end -->" in new


MARKED_MEMORY_BODY = (
    "# Mac — Curated Memory\n\n"
    "## Recently Published\n\n"
    "<!-- derived:recently-published:start -->\n\nstub\n\n"
    "<!-- derived:recently-published:end -->\n\n"
    "## Catalog Status\n\n"
    "<!-- derived:catalog-status:start -->\n\nstub\n\n"
    "<!-- derived:catalog-status:end -->\n"
)


def test_main_regenerates_into_marked_memory(tmp_path, monkeypatch, capsys):
    import json
    memory = _scaffold(tmp_path, MARKED_MEMORY_BODY)
    monkeypatch.setattr(
        sys, "argv",
        ["regenerate-index-sections.py", str(tmp_path), "--format", "json"],
    )
    rc = mod.main()
    assert rc == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] in ("regenerated", "unchanged")
    assert "The Slide" in memory.read_text(encoding="utf-8")


def test_main_errors_when_markers_missing(tmp_path, monkeypatch):
    _scaffold(tmp_path, "# Mac — Curated Memory\n\nno markers at all\n")
    monkeypatch.setattr(
        sys, "argv", ["regenerate-index-sections.py", str(tmp_path)]
    )
    rc = mod.main()
    assert rc == 1


def test_main_honors_sanctum_dir_override(tmp_path, monkeypatch, capsys):
    """--sanctum-dir points the rewrite at a staging copy outside the default."""
    import json
    # Songbook/profiles live under tmp_path; the sanctum lives in a sibling dir.
    (tmp_path / "docs" / "band-profiles").mkdir(parents=True)
    (tmp_path / "docs" / "band-profiles" / "lennys-voice.yaml").write_text(
        'name: "Lenny\'s Voice"\n', encoding="utf-8"
    )
    songbook = tmp_path / "docs" / "songbook" / "lennys-voice"
    songbook.mkdir(parents=True)
    (songbook / "the-slide.md").write_text(SONG_TEXT, encoding="utf-8")

    staging = tmp_path / "staging-copy"
    staging.mkdir()
    (staging / "MEMORY.md").write_text(MARKED_MEMORY_BODY, encoding="utf-8")
    # A default-location MEMORY.md must NOT be created — proving the override is used.

    monkeypatch.setattr(
        sys, "argv",
        [
            "regenerate-index-sections.py", str(tmp_path),
            "--sanctum-dir", str(staging), "--format", "json",
        ],
    )
    rc = mod.main()
    assert rc == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] in ("regenerated", "unchanged")
    assert "The Slide" in (staging / "MEMORY.md").read_text(encoding="utf-8")
