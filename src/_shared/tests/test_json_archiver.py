#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for json_archiver: archive paths, directory-run names, the project root, and the write."""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import json_archiver  # noqa: E402
from json_archiver import (  # noqa: E402
    ARCHIVE_ROOT,
    archive_path,
    catalog_identifier,
    find_project_root,
    folder_scope,
    input_archive_identifier,
    resolve_archive_arg,
    write_archive,
)


class TmpPathTestCase(unittest.TestCase):
    """Gives each test a fresh temporary directory as self.tmp_path."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name).resolve()

    def chdir(self, path):
        """Work from `path` for the rest of the test."""
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(path)

    def fix_today(self, day="2026-09-12"):
        """Pin the archive date for the rest of the test."""
        patcher = mock.patch.object(json_archiver, "datetime")
        fake = patcher.start()
        self.addCleanup(patcher.stop)
        fake.now.return_value = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)


class TestArchivePath(TmpPathTestCase):
    def test_song_archive_flat(self):
        self.assertEqual(archive_path("songs", "Night Shift", "/r"), os.path.join("/r", ARCHIVE_ROOT, "songs", "night-shift.json"))

    def test_song_archive_band_subfolder(self):
        self.assertEqual(archive_path("songs", "band-a/Night Shift-Duo", "/r"), os.path.join(
            "/r", ARCHIVE_ROOT, "songs", "band-a", "night-shift-duo.json"
        ))

    def test_catalog_identifier_unchanged(self):
        self.assertEqual(archive_path("catalog", "2026-09-12-summary", "/r"), os.path.join(
            "/r", ARCHIVE_ROOT, "catalog", "2026-09-12-summary.json"
        ))

    def test_input_archive_identifier(self):
        tmp_path = self.tmp_path
        self.fix_today()
        band = tmp_path / "audio" / "my-band"
        band.mkdir(parents=True)
        song = band / "The Song.mp3"
        song.write_bytes(b"")
        loose = tmp_path / "Loose.mp3"
        loose.write_bytes(b"")
        self.assertEqual(input_archive_identifier(str(song), "beat-grid"), ("songs", "my-band/The Song-beat-grid"))
        self.assertEqual(input_archive_identifier(str(loose), "beat-grid"), ("songs", "Loose-beat-grid"))
        self.assertEqual(input_archive_identifier(str(band), "vocal-placement"),
                         ("catalog", "2026-09-12-vocal-placement-my-band"))


class TestDirectoryRunNames(TmpPathTestCase):
    """A directory run over one band never takes another band's (or the catalog's) archive name."""

    def setUp(self):
        super().setUp()
        self.fix_today()
        self.audio = self.tmp_path / "docs" / "audio"
        for band in ("Band A", "band-b"):
            (self.audio / band).mkdir(parents=True)

    def test_catalog_root_keeps_the_bare_dated_name(self):
        self.assertEqual(input_archive_identifier(str(self.audio), "summary"), ("catalog", "2026-09-12-summary"))

    def test_two_bands_on_one_day_get_separate_archives(self):
        paths = {
            archive_path(*input_archive_identifier(str(self.audio / band), "summary"), "/r")
            for band in ("Band A", "band-b")
        }
        self.assertEqual(paths, {
            os.path.join("/r", ARCHIVE_ROOT, "catalog", "2026-09-12-summary-band-a.json"),
            os.path.join("/r", ARCHIVE_ROOT, "catalog", "2026-09-12-summary-band-b.json"),
        })

    def test_band_run_does_not_take_the_catalog_name(self):
        catalog = input_archive_identifier(str(self.audio), "beat-grid")
        band = input_archive_identifier(str(self.audio / "band-b"), "beat-grid")
        self.assertNotEqual(catalog, band)

    def test_relative_and_trailing_slash_folders_resolve_to_their_name(self):
        self.chdir(self.audio / "band-b")
        self.assertEqual(input_archive_identifier(".", "summary"), ("catalog", "2026-09-12-summary-band-b"))
        self.assertEqual(input_archive_identifier("../band-b/", "summary"), ("catalog", "2026-09-12-summary-band-b"))
        self.assertEqual(input_archive_identifier("..", "summary"), ("catalog", "2026-09-12-summary"))

    def test_folder_scope(self):
        self.assertIsNone(folder_scope(str(self.audio)))
        self.assertEqual(folder_scope(str(self.audio / "Band A")), "band-a")
        self.assertEqual(folder_scope(str(self.tmp_path / "docs")), "docs")

    def test_catalog_identifier(self):
        self.assertEqual(catalog_identifier("deep"), "2026-09-12-deep")
        self.assertEqual(catalog_identifier("deep", "band-a"), "2026-09-12-deep-band-a")
        self.assertEqual(catalog_identifier("deep", None), "2026-09-12-deep")


class TestFindProjectRoot(TmpPathTestCase):
    def setUp(self):
        super().setUp()
        self.project = self.tmp_path / "project"
        (self.project / "_bmad").mkdir(parents=True)
        self.band = self.project / "docs" / "audio" / "my-band"
        self.band.mkdir(parents=True)
        self.song = self.band / "Song.mp3"
        self.song.write_bytes(b"")
        self.elsewhere = self.tmp_path / "elsewhere"
        self.elsewhere.mkdir()

    def test_walks_up_from_a_file_to_the_folder_holding_bmad(self):
        self.chdir(self.elsewhere)
        self.assertEqual(find_project_root(str(self.song)), str(self.project))

    def test_walks_up_from_a_folder_and_from_the_root_itself(self):
        self.chdir(self.elsewhere)
        self.assertEqual(find_project_root(str(self.band)), str(self.project))
        self.assertEqual(find_project_root(str(self.project)), str(self.project))

    def test_a_path_that_does_not_exist_yet_still_resolves(self):
        self.chdir(self.elsewhere)
        self.assertEqual(find_project_root(str(self.band / "not-there" / "New.mp3")), str(self.project))

    def test_the_nearest_bmad_folder_wins(self):
        (self.band / "_bmad").mkdir()
        self.chdir(self.elsewhere)
        self.assertEqual(find_project_root(str(self.song)), str(self.band))

    def test_root_that_is_the_working_directory_comes_back_as_dot(self):
        self.chdir(self.project)
        self.assertEqual(find_project_root(str(self.song)), ".")
        self.assertEqual(find_project_root("docs/audio/my-band/Song.mp3"), ".")

    def test_relative_start_resolves_from_the_working_directory(self):
        self.chdir(self.band)
        self.assertEqual(find_project_root("Song.mp3"), str(self.project))

    def test_no_start_walks_up_from_the_working_directory(self):
        self.chdir(self.band)
        self.assertEqual(find_project_root(), str(self.project))

    def test_no_bmad_folder_gives_the_default(self):
        self.chdir(self.elsewhere)
        loose = self.elsewhere / "Loose.mp3"
        self.assertEqual(find_project_root(str(loose)), ".")
        self.assertEqual(find_project_root(str(loose), default="/fallback"), "/fallback")

    def test_a_file_named_bmad_is_not_a_project_marker(self):
        (self.elsewhere / "_bmad").write_text("not a folder", encoding="utf-8")
        self.chdir(self.elsewhere)
        self.assertEqual(find_project_root(str(self.elsewhere / "Loose.mp3")), ".")


class TestResolveArchiveArg(TmpPathTestCase):
    def test_none_means_no_archive(self):
        self.assertIsNone(resolve_archive_arg("songs", "x", None))
        self.assertIsNone(resolve_archive_arg("songs", "x", None, "/r"))

    def test_empty_value_is_the_canonical_path_under_the_working_directory_by_default(self):
        self.assertEqual(resolve_archive_arg("songs", "band-a/Song-deep", ""),
                         os.path.join(".", ARCHIVE_ROOT, "songs", "band-a", "song-deep.json"))

    def test_empty_value_is_the_canonical_path_under_the_given_project_root(self):
        self.assertEqual(resolve_archive_arg("songs", "band-a/Song-deep", "", "/r"),
                         os.path.join("/r", ARCHIVE_ROOT, "songs", "band-a", "song-deep.json"))
        self.assertEqual(resolve_archive_arg("songs", "band-a/Song-deep", "", project_root="/r"),
                         os.path.join("/r", ARCHIVE_ROOT, "songs", "band-a", "song-deep.json"))

    def test_explicit_path_is_used_verbatim(self):
        self.assertEqual(resolve_archive_arg("songs", "x", "out/mine.json", "/r"), "out/mine.json")

    def test_run_from_another_directory_archives_under_the_audio_project(self):
        project = self.tmp_path / "project"
        (project / "_bmad").mkdir(parents=True)
        song = project / "docs" / "audio" / "my-band" / "Song.mp3"
        song.parent.mkdir(parents=True)
        song.write_bytes(b"")
        elsewhere = self.tmp_path / "elsewhere"
        elsewhere.mkdir()
        self.chdir(elsewhere)
        category, identifier = input_archive_identifier(str(song), "summary")
        target = resolve_archive_arg(category, identifier, "", find_project_root(str(song)))
        self.assertEqual(target, str(project / ARCHIVE_ROOT / "songs" / "my-band" / "song-summary.json"))


class TestWriteArchive(TmpPathTestCase):
    def test_writes_the_data_and_creates_parent_folders(self):
        target = self.tmp_path / "docs" / "audio-analysis" / "songs" / "band" / "song.json"
        data = {"script": "x", "tracks": [{"file": "Café → Señor.mp3", "bpm": 120.0}]}
        res = write_archive(str(target), data)
        self.assertEqual(res["status"], "archived")
        self.assertEqual(res["path"], str(target))
        raw = target.read_bytes()
        self.assertEqual(res["bytes_written"], len(raw))
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(json.loads(raw.decode("utf-8")), data)

    def test_a_second_write_replaces_the_first(self):
        target = self.tmp_path / "a.json"
        write_archive(str(target), {"run": 1, "pad": "x" * 200})
        write_archive(str(target), {"run": 2})
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"run": 2})


if __name__ == "__main__":
    unittest.main()
