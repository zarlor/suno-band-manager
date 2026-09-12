#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for json_archiver.archive_path — flat and per-band song archives."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from json_archiver import archive_path, ARCHIVE_ROOT


def test_song_archive_flat():
    assert archive_path("songs", "For Now", "/r") == os.path.join("/r", ARCHIVE_ROOT, "songs", "for-now.json")


def test_song_archive_band_subfolder():
    assert archive_path("songs", "solitary-fire/For Now-Lenny", "/r") == os.path.join(
        "/r", ARCHIVE_ROOT, "songs", "solitary-fire", "for-now-lenny.json"
    )


def test_catalog_identifier_unchanged():
    assert archive_path("catalog", "2026-09-12-summary", "/r") == os.path.join(
        "/r", ARCHIVE_ROOT, "catalog", "2026-09-12-summary.json"
    )


def test_input_archive_identifier(tmp_path):
    from json_archiver import input_archive_identifier
    band = tmp_path / "audio" / "my-band"
    band.mkdir(parents=True)
    song = band / "The Song.mp3"
    song.write_bytes(b"")
    loose = tmp_path / "Loose.mp3"
    loose.write_bytes(b"")
    assert input_archive_identifier(str(song), "beat-grid") == ("songs", "my-band/The Song-beat-grid")
    assert input_archive_identifier(str(loose), "beat-grid") == ("songs", "Loose-beat-grid")
    category, ident = input_archive_identifier(str(band), "vocal-placement")
    assert category == "catalog" and ident.endswith("-vocal-placement") and len(ident) == len("2026-09-12-vocal-placement")
