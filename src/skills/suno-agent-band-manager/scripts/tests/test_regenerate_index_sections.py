#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for regenerate-index-sections.py"""

import sys
import unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent))

spec = spec_from_file_location(
    "regenerate_index_sections",
    Path(__file__).parent.parent / "regenerate-index-sections.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


SONG_TEXT = (
    "---\n"
    'title: "Harbor Lights"\n'
    "band_profile: paper-lanterns\n"
    "status: published\n"
    "date: 2026-01-15\n"
    "---\n\n"
    "**Status: LOCKED — Published 2026-01-15. A firearm-as-cog confession.**\n"
)


SANCTUM_REL = ("_bmad", "memory", "suno-agent-band-manager")
RECENT = "memory/catalog/recently-published.md"
STATUS = "memory/catalog/status.md"
MARKED_RECENT = (
    "# Recently Published\n\n"
    "<!-- derived:recently-published:start -->\n\nstub\n\n"
    "<!-- derived:recently-published:end -->\n"
)
MARKED_STATUS = (
    "# Catalog Status\n\n"
    "<!-- derived:catalog-status:start -->\n\nstub\n\n"
    "<!-- derived:catalog-status:end -->\n"
)


def _songbook(tmp_path):
    (tmp_path / "docs" / "band-profiles").mkdir(parents=True)
    (tmp_path / "docs" / "band-profiles" / "paper-lanterns.yaml").write_text(
        'name: "Paper Lanterns"\n', encoding="utf-8"
    )
    songbook = tmp_path / "docs" / "songbook" / "paper-lanterns"
    songbook.mkdir(parents=True)
    (songbook / "harbor-lights.md").write_text(SONG_TEXT, encoding="utf-8")


def _v7(tmp_path, recent=MARKED_RECENT, status=MARKED_STATUS):
    """A v7 project; catalog files written when given (None = absent)."""
    _songbook(tmp_path)
    sanctum = tmp_path.joinpath(*SANCTUM_REL)
    (sanctum / "memory" / "catalog").mkdir(parents=True)
    if recent is not None:
        (sanctum / RECENT).write_text(recent, encoding="utf-8")
    if status is not None:
        (sanctum / STATUS).write_text(status, encoding="utf-8")
    return sanctum


def _main(capsys, *argv):
    with patch.object(sys, "argv", ["regenerate-index-sections.py", *argv]), capsys():
        return mod.main()


def _add_bad_songs(tmp_path):
    songbook = tmp_path / "docs" / "songbook" / "paper-lanterns"
    (songbook / "broken.md").write_text("---\ntitle: [unclosed\n---\n\nbody\n", encoding="utf-8")
    (songbook / "typo-band.md").write_text(SONG_TEXT.replace("paper-lanterns", "paper-lantern")
                                           .replace("Harbor Lights", "Typo Song"), encoding="utf-8")
    (songbook / "no-frontmatter.md").write_text("# Just a heading\n", encoding="utf-8")


class TestRegenerateIndexSections(TempDirMixin, unittest.TestCase):
    def test_parse_song_reads_frontmatter_and_body(self):
        p = self.tmp_path / "song.md"
        p.write_text(SONG_TEXT, encoding="utf-8")
        song = mod.parse_song(p)
        assert song["title"] == "Harbor Lights"
        assert song["band"] == "paper-lanterns"
        assert song["frontmatter_status"] == "published"
        assert song["body_status"] == "LOCKED"
        assert song["body_date"] == "2026-01-15"

    def test_is_published_requires_both_markers(self):
        assert mod.is_published({"frontmatter_status": "published", "body_status": "LOCKED"})
        assert not mod.is_published({"frontmatter_status": "published", "body_status": "WIP"})
        assert not mod.is_published({"frontmatter_status": "wip", "body_status": "LOCKED"})

    def test_band_display_map_uses_profile_name(self):
        (self.tmp_path / "docs" / "band-profiles").mkdir(parents=True)
        (self.tmp_path / "docs" / "band-profiles" / "paper-lanterns.yaml").write_text(
            'name: "Paper Lanterns"\n', encoding="utf-8"
        )
        out = mod.band_display_map(self.tmp_path)
        assert out["paper-lanterns"] == "Paper Lanterns"

    def test_band_display_map_falls_back_to_titlecased_slug(self):
        (self.tmp_path / "docs" / "band-profiles").mkdir(parents=True)
        (self.tmp_path / "docs" / "band-profiles" / "iron-meridian.yaml").write_text(
            "tier: pro\n", encoding="utf-8"
        )
        out = mod.band_display_map(self.tmp_path)
        assert out["iron-meridian"] == "Iron Meridian"

    def test_replace_section_swaps_marked_content(self):
        text = (
            "intro\n"
            "<!-- derived:catalog-status:start -->\nOLD\n<!-- derived:catalog-status:end -->\n"
            "outro\n"
        )
        new, ok = mod.replace_section(text, "catalog-status", "NEW CONTENT")
        assert ok is True
        assert "NEW CONTENT" in new
        assert "OLD" not in new

    def test_replace_section_reports_missing_markers(self):
        new, ok = mod.replace_section("no markers here", "catalog-status", "X")
        assert ok is False

    def test_migrate_section_wraps_existing_heading(self):
        text = "# Top\n\n## Catalog Status\n\n- one band\n\n## Other\n"
        new, migrated = mod.migrate_section(text, "## Catalog Status", "catalog-status")
        assert migrated is True
        assert "<!-- derived:catalog-status:start -->" in new
        assert "<!-- derived:catalog-status:end -->" in new

    def test_main_regenerates_catalog_files(self):
        import json
        sanctum = _v7(self.tmp_path)
        assert _main(self.capsys, str(self.tmp_path), "--format", "json") == 0
        result = json.loads(self.capsys.readouterr().out)
        assert result["status"] == "regenerated"
        recent = (sanctum / RECENT).read_text(encoding="utf-8")
        status = (sanctum / STATUS).read_text(encoding="utf-8")
        assert recent.startswith("# Recently Published\n")
        assert "**Harbor Lights** (2026-01-15, PUBLISHED)" in recent and "stub" not in recent
        assert "**Paper Lanterns:** **1 published tracks** — Harbor Lights." in status
        # A second run changes nothing.
        assert _main(self.capsys, str(self.tmp_path), "--format", "json") == 0
        assert json.loads(self.capsys.readouterr().out)["status"] == "unchanged"

    def test_main_never_touches_memory_or_index(self):
        sanctum = _v7(self.tmp_path)
        assert _main(self.capsys, str(self.tmp_path)) == 0
        assert not (sanctum / "MEMORY.md").exists()
        assert not (sanctum / "INDEX.md").exists()

    def test_main_creates_missing_catalog_files(self):
        sanctum = _v7(self.tmp_path, recent=None, status=None)
        (sanctum / "memory" / "catalog").rmdir()
        assert _main(self.capsys, str(self.tmp_path)) == 0
        recent = (sanctum / RECENT).read_text(encoding="utf-8")
        assert recent.startswith("# Recently Published\n\n<!-- derived:recently-published:start -->")
        assert recent.rstrip().endswith("<!-- derived:recently-published:end -->")
        assert "Harbor Lights" in recent
        assert "<!-- derived:catalog-status:start -->" in (sanctum / STATUS).read_text(encoding="utf-8")

    def test_main_errors_when_markers_missing_and_writes_nothing(self):
        sanctum = _v7(self.tmp_path, status="# Catalog Status\n\n- hand-written\n")
        before = (sanctum / RECENT).read_text(encoding="utf-8")
        assert _main(self.capsys, str(self.tmp_path)) == 1
        assert (sanctum / STATUS).read_text(encoding="utf-8") == "# Catalog Status\n\n- hand-written\n"
        assert (sanctum / RECENT).read_text(encoding="utf-8") == before

    def test_main_migrate_wraps_unmarked_file(self):
        sanctum = _v7(self.tmp_path, status="# Catalog Status\n\n- hand-written\n")
        assert _main(self.capsys, str(self.tmp_path), "--migrate") == 0
        text = (sanctum / STATUS).read_text(encoding="utf-8")
        assert text.startswith("# Catalog Status\n")
        assert "<!-- derived:catalog-status:start -->" in text and "hand-written" not in text
        assert "Harbor Lights" in text

    def test_main_dry_run_writes_nothing(self):
        sanctum = _v7(self.tmp_path)
        assert _main(self.capsys, str(self.tmp_path), "--dry-run") == 0
        assert "Harbor Lights" in self.capsys.readouterr().out
        assert (sanctum / RECENT).read_text(encoding="utf-8") == MARKED_RECENT

    def test_main_errors_without_sanctum(self):
        _songbook(self.tmp_path)
        assert _main(self.capsys, str(self.tmp_path)) == 2
        assert "migrate-sanctum-to-v7.py" in self.capsys.readouterr().err

    def test_main_honors_sanctum_dir_override(self):
        """--sanctum-dir points the rewrite at a staging copy outside the default."""
        import json
        _songbook(self.tmp_path)
        staging = self.tmp_path / "staging-copy"
        (staging / "memory" / "catalog").mkdir(parents=True)
        (staging / RECENT).write_text(MARKED_RECENT, encoding="utf-8")
        (staging / STATUS).write_text(MARKED_STATUS, encoding="utf-8")
        assert _main(self.capsys, str(self.tmp_path), "--sanctum-dir", str(staging), "--format", "json") == 0
        assert json.loads(self.capsys.readouterr().out)["status"] == "regenerated"
        assert "Harbor Lights" in (staging / RECENT).read_text(encoding="utf-8")
        # The default location was never created.
        assert not self.tmp_path.joinpath(*SANCTUM_REL).exists()

    def test_load_all_songs_reports_every_skip(self):
        _songbook(self.tmp_path)
        _add_bad_songs(self.tmp_path)
        songs, skipped = mod.load_all_songs(self.tmp_path)
        assert [s["title"] for s in songs] == ["Harbor Lights"]
        reasons = {Path(s["path"]).name: s["reason"] for s in skipped}
        assert set(reasons) == {"broken.md", "typo-band.md", "no-frontmatter.md"}
        assert "YAML error" in reasons["broken.md"]
        assert "paper-lantern'" in reasons["typo-band.md"]
        assert "frontmatter" in reasons["no-frontmatter.md"]

    def test_main_with_skips_reports_status_and_exits_1(self):
        import json
        sanctum = _v7(self.tmp_path)
        _add_bad_songs(self.tmp_path)
        assert _main(self.capsys, str(self.tmp_path), "--format", "json") == 1
        result = json.loads(self.capsys.readouterr().out)
        assert result["status"] == "regenerated_with_skips"
        assert len(result["skipped"]) == 3
        # The good song still lands in the catalog.
        assert "Harbor Lights" in (sanctum / RECENT).read_text(encoding="utf-8")
        assert _main(self.capsys, str(self.tmp_path), "--format", "json") == 1
        assert json.loads(self.capsys.readouterr().out)["status"] == "unchanged_with_skips"

    def test_main_text_mode_prints_skips_to_stderr(self):
        _v7(self.tmp_path)
        _add_bad_songs(self.tmp_path)
        assert _main(self.capsys, str(self.tmp_path)) == 1
        err = self.capsys.readouterr().err
        assert "3 songbook entries left out" in err and "broken.md" in err

    def test_dry_run_with_skips_exits_1(self):
        import json
        _v7(self.tmp_path)
        _add_bad_songs(self.tmp_path)
        assert _main(self.capsys, str(self.tmp_path), "--dry-run", "--format", "json") == 1
        assert len(json.loads(self.capsys.readouterr().out)["skipped"]) == 3

    def test_clean_run_has_empty_skipped(self):
        import json
        _v7(self.tmp_path)
        assert _main(self.capsys, str(self.tmp_path), "--format", "json") == 0
        assert json.loads(self.capsys.readouterr().out)["skipped"] == []


if __name__ == "__main__":
    unittest.main()
