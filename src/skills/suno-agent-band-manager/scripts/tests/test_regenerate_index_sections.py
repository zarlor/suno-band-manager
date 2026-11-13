#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for regenerate_index_sections.py"""

import json
import sys
import unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402
from fake_resolver import install_resolver  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent))

spec = spec_from_file_location(
    "regenerate_index_sections",
    Path(__file__).parent.parent / "regenerate_index_sections.py",
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
    with patch.object(sys, "argv", ["regenerate_index_sections.py", *argv]), capsys():
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
        self.assertEqual(song["title"], "Harbor Lights")
        self.assertEqual(song["band"], "paper-lanterns")
        self.assertEqual(song["frontmatter_status"], "published")
        self.assertEqual(song["body_status"], "LOCKED")
        self.assertEqual(song["body_date"], "2026-01-15")

    def test_is_published_requires_both_markers(self):
        self.assertTrue(mod.is_published({"frontmatter_status": "published", "body_status": "LOCKED"}))
        self.assertFalse(mod.is_published({"frontmatter_status": "published", "body_status": "WIP"}))
        self.assertFalse(mod.is_published({"frontmatter_status": "wip", "body_status": "LOCKED"}))

    def test_band_display_map_uses_profile_name(self):
        (self.tmp_path / "docs" / "band-profiles").mkdir(parents=True)
        (self.tmp_path / "docs" / "band-profiles" / "paper-lanterns.yaml").write_text(
            'name: "Paper Lanterns"\n', encoding="utf-8"
        )
        out = mod.band_display_map(self.tmp_path)
        self.assertEqual(out["paper-lanterns"], "Paper Lanterns")

    def test_band_display_map_falls_back_to_titlecased_slug(self):
        (self.tmp_path / "docs" / "band-profiles").mkdir(parents=True)
        (self.tmp_path / "docs" / "band-profiles" / "iron-meridian.yaml").write_text(
            "tier: pro\n", encoding="utf-8"
        )
        out = mod.band_display_map(self.tmp_path)
        self.assertEqual(out["iron-meridian"], "Iron Meridian")

    def test_replace_section_swaps_marked_content(self):
        text = (
            "intro\n"
            "<!-- derived:catalog-status:start -->\nOLD\n<!-- derived:catalog-status:end -->\n"
            "outro\n"
        )
        new, ok = mod.replace_section(text, "catalog-status", "NEW CONTENT")
        self.assertIs(ok, True)
        self.assertIn("NEW CONTENT", new)
        self.assertNotIn("OLD", new)

    def test_replace_section_reports_missing_markers(self):
        new, ok = mod.replace_section("no markers here", "catalog-status", "X")
        self.assertIs(ok, False)

    def test_migrate_section_wraps_existing_heading(self):
        text = "# Top\n\n## Catalog Status\n\n- one band\n\n## Other\n"
        new, migrated = mod.migrate_section(text, "## Catalog Status", "catalog-status")
        self.assertIs(migrated, True)
        self.assertIn("<!-- derived:catalog-status:start -->", new)
        self.assertIn("<!-- derived:catalog-status:end -->", new)

    def test_main_regenerates_catalog_files(self):
        import json
        sanctum = _v7(self.tmp_path)
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        result = json.loads(self.capsys.readouterr().out)
        self.assertEqual(result["status"], "regenerated")
        recent = (sanctum / RECENT).read_text(encoding="utf-8")
        status = (sanctum / STATUS).read_text(encoding="utf-8")
        self.assertTrue(recent.startswith("# Recently Published\n"))
        self.assertTrue("**Harbor Lights** (2026-01-15, PUBLISHED)" in recent and "stub" not in recent)
        self.assertIn("**Paper Lanterns:** **1 published tracks** — Harbor Lights.", status)
        # A second run changes nothing.
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        self.assertEqual(json.loads(self.capsys.readouterr().out)["status"], "unchanged")

    def test_main_never_touches_memory_or_index(self):
        sanctum = _v7(self.tmp_path)
        self.assertEqual(_main(self.capsys, str(self.tmp_path)), 0)
        self.assertFalse((sanctum / "MEMORY.md").exists())
        self.assertFalse((sanctum / "INDEX.md").exists())

    def test_main_creates_missing_catalog_files(self):
        sanctum = _v7(self.tmp_path, recent=None, status=None)
        (sanctum / "memory" / "catalog").rmdir()
        self.assertEqual(_main(self.capsys, str(self.tmp_path)), 0)
        recent = (sanctum / RECENT).read_text(encoding="utf-8")
        self.assertTrue(recent.startswith("# Recently Published\n\n<!-- derived:recently-published:start -->"))
        self.assertTrue(recent.rstrip().endswith("<!-- derived:recently-published:end -->"))
        self.assertIn("Harbor Lights", recent)
        self.assertIn("<!-- derived:catalog-status:start -->", (sanctum / STATUS).read_text(encoding="utf-8"))

    def test_main_errors_when_markers_missing_and_writes_nothing(self):
        sanctum = _v7(self.tmp_path, status="# Catalog Status\n\n- hand-written\n")
        before = (sanctum / RECENT).read_text(encoding="utf-8")
        self.assertEqual(_main(self.capsys, str(self.tmp_path)), 1)
        self.assertEqual((sanctum / STATUS).read_text(encoding="utf-8"), "# Catalog Status\n\n- hand-written\n")
        self.assertEqual((sanctum / RECENT).read_text(encoding="utf-8"), before)

    def test_main_migrate_wraps_unmarked_file(self):
        sanctum = _v7(self.tmp_path, status="# Catalog Status\n\n- hand-written\n")
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--migrate"), 0)
        text = (sanctum / STATUS).read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Catalog Status\n"))
        self.assertTrue("<!-- derived:catalog-status:start -->" in text and "hand-written" not in text)
        self.assertIn("Harbor Lights", text)

    def test_main_dry_run_writes_nothing(self):
        sanctum = _v7(self.tmp_path)
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--dry-run"), 0)
        self.assertIn("Harbor Lights", self.capsys.readouterr().out)
        self.assertEqual((sanctum / RECENT).read_text(encoding="utf-8"), MARKED_RECENT)

    def test_main_errors_without_sanctum(self):
        _songbook(self.tmp_path)
        self.assertEqual(_main(self.capsys, str(self.tmp_path)), 2)
        self.assertIn("migrate_sanctum_to_v7.py", self.capsys.readouterr().err)

    def test_main_honors_sanctum_dir_override(self):
        """--sanctum-dir points the rewrite at a staging copy outside the default."""
        import json
        _songbook(self.tmp_path)
        staging = self.tmp_path / "staging-copy"
        (staging / "memory" / "catalog").mkdir(parents=True)
        (staging / RECENT).write_text(MARKED_RECENT, encoding="utf-8")
        (staging / STATUS).write_text(MARKED_STATUS, encoding="utf-8")
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--sanctum-dir", str(staging), "--format", "json"), 0)
        self.assertEqual(json.loads(self.capsys.readouterr().out)["status"], "regenerated")
        self.assertIn("Harbor Lights", (staging / RECENT).read_text(encoding="utf-8"))
        # The default location was never created.
        self.assertFalse(self.tmp_path.joinpath(*SANCTUM_REL).exists())

    def test_load_all_songs_reports_every_skip(self):
        _songbook(self.tmp_path)
        _add_bad_songs(self.tmp_path)
        songs, skipped = mod.load_all_songs(self.tmp_path)
        self.assertEqual([s["title"] for s in songs], ["Harbor Lights"])
        reasons = {Path(s["path"]).name: s["reason"] for s in skipped}
        self.assertEqual(set(reasons), {"broken.md", "typo-band.md", "no-frontmatter.md"})
        self.assertIn("YAML error", reasons["broken.md"])
        self.assertIn("paper-lantern'", reasons["typo-band.md"])
        self.assertIn("frontmatter", reasons["no-frontmatter.md"])

    def test_main_with_skips_reports_status_and_exits_1(self):
        import json
        sanctum = _v7(self.tmp_path)
        _add_bad_songs(self.tmp_path)
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--format", "json"), 1)
        result = json.loads(self.capsys.readouterr().out)
        self.assertEqual(result["status"], "regenerated_with_skips")
        self.assertEqual(len(result["skipped"]), 3)
        # The good song still lands in the catalog.
        self.assertIn("Harbor Lights", (sanctum / RECENT).read_text(encoding="utf-8"))
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--format", "json"), 1)
        self.assertEqual(json.loads(self.capsys.readouterr().out)["status"], "unchanged_with_skips")

    def test_main_text_mode_prints_skips_to_stderr(self):
        _v7(self.tmp_path)
        _add_bad_songs(self.tmp_path)
        self.assertEqual(_main(self.capsys, str(self.tmp_path)), 1)
        err = self.capsys.readouterr().err
        self.assertTrue("3 songbook entries left out" in err and "broken.md" in err)

    def test_dry_run_with_skips_exits_1(self):
        import json
        _v7(self.tmp_path)
        _add_bad_songs(self.tmp_path)
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--dry-run", "--format", "json"), 1)
        self.assertEqual(len(json.loads(self.capsys.readouterr().out)["skipped"]), 3)

    def test_clean_run_has_empty_skipped(self):
        import json
        _v7(self.tmp_path)
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        self.assertEqual(json.loads(self.capsys.readouterr().out)["skipped"], [])

    # --- entry shapes that used to stop the regeneration ---

    def test_non_string_titles_regenerate_as_the_text_written(self):
        sanctum = _v7(self.tmp_path)
        songbook = self.tmp_path / "docs" / "songbook" / "paper-lanterns"
        (songbook / "y2k.md").write_text(SONG_TEXT.replace('title: "Harbor Lights"', "title: 1999"), encoding="utf-8")
        (songbook / "no.md").write_text(SONG_TEXT.replace('title: "Harbor Lights"', "title: No"), encoding="utf-8")
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        self.assertEqual(json.loads(self.capsys.readouterr().out)["status"], "regenerated")
        recent = (sanctum / RECENT).read_text(encoding="utf-8")
        status = (sanctum / STATUS).read_text(encoding="utf-8")
        self.assertIn("**1999** (2026-01-15, PUBLISHED)", recent)
        self.assertIn("**No** (2026-01-15, PUBLISHED)", recent)
        self.assertIn("**3 published tracks**", status)
        self.assertIn("1999", status)

    def test_entry_with_a_bom_and_an_empty_title_is_still_cataloged(self):
        sanctum = _v7(self.tmp_path)
        songbook = self.tmp_path / "docs" / "songbook" / "paper-lanterns"
        (songbook / "tin-roof.md").write_text(
            "\ufeff" + SONG_TEXT.replace('title: "Harbor Lights"', "title:"), encoding="utf-8")
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        self.assertEqual(json.loads(self.capsys.readouterr().out)["skipped"], [])
        self.assertIn("**tin-roof** (2026-01-15, PUBLISHED)", (sanctum / RECENT).read_text(encoding="utf-8"))

    def test_empty_band_profile_is_reported_not_a_crash(self):
        _v7(self.tmp_path)
        songbook = self.tmp_path / "docs" / "songbook" / "paper-lanterns"
        (songbook / "orphan.md").write_text(SONG_TEXT.replace("band_profile: paper-lanterns", "band_profile:"),
                                            encoding="utf-8")
        songs, skipped = mod.load_all_songs(self.tmp_path)
        self.assertEqual([s["title"] for s in songs], ["Harbor Lights"])
        self.assertEqual([Path(item["path"]).name for item in skipped], ["orphan.md"])

    def test_oddly_shaped_playlist_does_not_stop_the_regeneration(self):
        sanctum = _v7(self.tmp_path)
        for text in ("", "- a\n- b\n", "tracks: 5\n"):
            with self.subTest(playlist=text):
                (self.tmp_path / "docs" / "paper-lanterns-playlist.yaml").write_text(text, encoding="utf-8")
                self.assertEqual(_main(self.capsys, str(self.tmp_path), "--format", "json"), 0)
                self.capsys.readouterr()
                self.assertIn("**1 published tracks**", (sanctum / STATUS).read_text(encoding="utf-8"))

    # --- songbook_folder / band_profiles_folder from the module config ---

    def _moved(self):
        root = self.tmp_path
        sanctum = root.joinpath(*SANCTUM_REL)
        (sanctum / "memory" / "catalog").mkdir(parents=True)
        for rel, text in (
            ("music/songs/paper-lanterns/harbor-lights.md", SONG_TEXT),
            ("music/bands/paper-lanterns.yaml", 'name: "Paper Lanterns"\n'),
            ("music/paper-lanterns-playlist.yaml", "tracks:\n  - name: a\n  - name: b\n  - name: c\n"),
        ):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        install_resolver(root)
        (root / "_bmad" / "config.toml").write_text(
            '[modules.suno]\nsongbook_folder = "{project-root}/music/songs"\n'
            'band_profiles_folder = "{project-root}/music/bands"\n', encoding="utf-8")
        return sanctum

    def test_configured_folders_feed_the_catalog(self):
        sanctum = self._moved()
        self.assertEqual(_main(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        self.assertEqual(json.loads(self.capsys.readouterr().out)["skipped"], [])
        recent = (sanctum / RECENT).read_text(encoding="utf-8")
        self.assertIn("**Harbor Lights** (2026-01-15, PUBLISHED)", recent)
        self.assertIn("Songbook: `music/songs/paper-lanterns/harbor-lights.md`.", recent)
        status = (sanctum / STATUS).read_text(encoding="utf-8")
        self.assertIn("**Paper Lanterns:** 3-track playlist", status)
        self.assertIn("`music/paper-lanterns-playlist.yaml`", status)

    def test_default_folders_without_config_keep_the_docs_paths(self):
        sanctum = _v7(self.tmp_path)
        self.assertEqual(mod.content_dirs(self.tmp_path),
                         (self.tmp_path / "docs" / "songbook", self.tmp_path / "docs" / "band-profiles"))
        self.assertEqual(_main(self.capsys, str(self.tmp_path)), 0)
        self.assertIn("Songbook: `docs/songbook/paper-lanterns/harbor-lights.md`.",
                      (sanctum / RECENT).read_text(encoding="utf-8"))

    def test_unreadable_config_exits_2_and_writes_nothing(self):
        sanctum = _v7(self.tmp_path)
        install_resolver(self.tmp_path)
        (self.tmp_path / "_bmad" / "config.toml").write_text("[modules.suno\nbroken", encoding="utf-8")
        with self.assertRaises(SystemExit) as exc:
            _main(self.capsys, str(self.tmp_path))
        self.assertEqual(exc.exception.code, 2)
        self.assertIn("module config unreadable", self.capsys.readouterr().err)
        self.assertEqual((sanctum / RECENT).read_text(encoding="utf-8"), MARKED_RECENT)


if __name__ == "__main__":
    unittest.main()
