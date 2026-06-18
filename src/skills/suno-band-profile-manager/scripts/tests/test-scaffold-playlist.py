#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for scaffold-playlist.py"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

SCRIPT_PATH = Path(__file__).parent.parent / "scaffold-playlist.py"

spec = spec_from_file_location(
    "scaffold_playlist",
    SCRIPT_PATH,
)
scaffold_mod = module_from_spec(spec)
spec.loader.exec_module(scaffold_mod)

render_playlist_yaml = scaffold_mod.render_playlist_yaml
discover_songbook_tracks = scaffold_mod.discover_songbook_tracks
_band_name_from_slug = scaffold_mod._band_name_from_slug
_extract_title_from_songbook = scaffold_mod._extract_title_from_songbook
_is_published = scaffold_mod._is_published


# --- slug -> name ---

def test_band_name_from_slug():
    assert _band_name_from_slug("solitary-fire") == "Solitary Fire"
    assert _band_name_from_slug("lennys-voice") == "Lennys Voice"
    assert _band_name_from_slug("band_under_score") == "Band Under Score"


# --- render: empty template ---

def test_render_empty_template():
    out = render_playlist_yaml("Solitary Fire", [], from_songbook=False)
    assert 'album: "Solitary Fire"' in out
    assert "tracks:" in out
    # Empty template carries instructional comments, no real track entries.
    assert "Add tracks below as they are published" in out
    real_track_lines = [ln for ln in out.splitlines()
                        if ln.lstrip().startswith("- name:")]
    assert real_track_lines == []
    assert out.endswith("\n")


# --- render: with tracks ---

def test_render_with_tracks_manual():
    tracks = [{"name": "First Song"}, {"name": "Second Song"}]
    out = render_playlist_yaml("My Band", tracks, from_songbook=False)
    assert '- name: "First Song"' in out
    assert '- name: "Second Song"' in out
    assert 'file: ""' in out
    # Manual mode does not emit the songbook TODO comment.
    assert "TODO: set to the actual filename" not in out


def test_render_with_tracks_from_songbook():
    tracks = [{"name": "Discovered Song", "songbook_path": "docs/songbook/my-band/discovered-song.md"}]
    out = render_playlist_yaml("My Band", tracks, from_songbook=True)
    assert '- name: "Discovered Song"' in out
    assert "TODO: set to the actual filename" in out
    assert "# songbook: docs/songbook/my-band/discovered-song.md" in out


# --- songbook frontmatter parsing ---

def test_extract_title_from_songbook(tmp_path):
    md = tmp_path / "song.md"
    md.write_text('---\ntitle: "My Great Song"\nstatus: published\n---\nbody\n')
    assert _extract_title_from_songbook(md) == "My Great Song"


def test_extract_title_unquoted(tmp_path):
    md = tmp_path / "song.md"
    md.write_text("---\ntitle: Plain Title\n---\nbody\n")
    assert _extract_title_from_songbook(md) == "Plain Title"


def test_extract_title_no_frontmatter(tmp_path):
    md = tmp_path / "song.md"
    md.write_text("just body, no frontmatter\n")
    assert _extract_title_from_songbook(md) is None


def test_is_published(tmp_path):
    pub = tmp_path / "pub.md"
    pub.write_text("---\ntitle: X\nstatus: published\n---\n")
    draft = tmp_path / "draft.md"
    draft.write_text("---\ntitle: Y\nstatus: draft\n---\n")
    assert _is_published(pub) is True
    assert _is_published(draft) is False


# --- discovery: only published, only with titles ---

def test_discover_songbook_tracks(tmp_path):
    band_dir = tmp_path / "docs" / "songbook" / "my-band"
    band_dir.mkdir(parents=True)
    (band_dir / "a.md").write_text('---\ntitle: "Alpha"\nstatus: published\n---\n')
    (band_dir / "b.md").write_text('---\ntitle: "Beta"\nstatus: draft\n---\n')
    (band_dir / "c.md").write_text('---\ntitle: "Gamma"\nstatus: published\n---\n')

    tracks = discover_songbook_tracks(tmp_path, "my-band")
    names = {t["name"] for t in tracks}
    # Only published entries with titles are returned.
    assert names == {"Alpha", "Gamma"}
    for t in tracks:
        assert t["songbook_path"].startswith("docs/songbook/my-band/")


def test_discover_songbook_no_dir(tmp_path):
    assert discover_songbook_tracks(tmp_path, "no-such-band") == []


# --- docs-dir override on discovery ---

def test_discover_default_docs_dir(tmp_path):
    # Default (docs_dir=None) reads from {project_root}/docs/songbook — unchanged.
    band_dir = tmp_path / "docs" / "songbook" / "my-band"
    band_dir.mkdir(parents=True)
    (band_dir / "a.md").write_text('---\ntitle: "Alpha"\nstatus: published\n---\n')
    tracks = discover_songbook_tracks(tmp_path, "my-band")
    assert {t["name"] for t in tracks} == {"Alpha"}


def test_discover_docs_dir_override(tmp_path):
    # With docs_dir pointing at a relocated docs root, discovery reads from there.
    alt_docs = tmp_path / "alt-docs"
    band_dir = alt_docs / "songbook" / "my-band"
    band_dir.mkdir(parents=True)
    (band_dir / "a.md").write_text('---\ntitle: "Relocated"\nstatus: published\n---\n')
    # The default {tmp_path}/docs has nothing.
    assert discover_songbook_tracks(tmp_path, "my-band") == []
    tracks = discover_songbook_tracks(tmp_path, "my-band", docs_dir=alt_docs)
    assert {t["name"] for t in tracks} == {"Relocated"}


# --- main() end-to-end via subprocess (path placement) ---

def _run(*args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True, text=True,
    )
    return proc


def test_main_default_writes_under_project_docs(tmp_path):
    proc = _run("my-band", "--project-root", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "created"
    # Default destination is {project-root}/docs/{slug}-playlist.yaml.
    expected = tmp_path / "docs" / "my-band-playlist.yaml"
    assert expected.exists()
    assert payload["path"] == "docs/my-band-playlist.yaml"


def test_main_docs_dir_override_writes_there(tmp_path):
    alt_docs = tmp_path / "alt-docs"
    proc = _run("my-band", "--project-root", str(tmp_path), "--docs-dir", str(alt_docs))
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "created"
    # Playlist must land under the overridden docs dir, NOT {project-root}/docs.
    assert (alt_docs / "my-band-playlist.yaml").exists()
    assert not (tmp_path / "docs" / "my-band-playlist.yaml").exists()
