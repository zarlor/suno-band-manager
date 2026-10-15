#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for json_archiver.archive_path — flat and per-band song archives."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from json_archiver import archive_path, ARCHIVE_ROOT


class TmpPathTestCase(unittest.TestCase):
    """Gives each test a fresh temporary directory as self.tmp_path."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name).resolve()


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
        from json_archiver import input_archive_identifier
        band = tmp_path / "audio" / "my-band"
        band.mkdir(parents=True)
        song = band / "The Song.mp3"
        song.write_bytes(b"")
        loose = tmp_path / "Loose.mp3"
        loose.write_bytes(b"")
        self.assertEqual(input_archive_identifier(str(song), "beat-grid"), ("songs", "my-band/The Song-beat-grid"))
        self.assertEqual(input_archive_identifier(str(loose), "beat-grid"), ("songs", "Loose-beat-grid"))
        category, ident = input_archive_identifier(str(band), "vocal-placement")
        self.assertEqual(category, "catalog")
        self.assertTrue(ident.endswith("-vocal-placement"))
        self.assertEqual(len(ident), len("2026-09-12-vocal-placement"))


if __name__ == "__main__":
    unittest.main()
