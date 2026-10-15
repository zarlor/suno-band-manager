#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for scaffold-playlist.py"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_resolver import install_resolver  # noqa: E402

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


class TmpPathTestCase(unittest.TestCase):
    """Gives each test a fresh temporary directory as self.tmp_path."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name).resolve()


class TestScaffoldHelpers(TmpPathTestCase):
    # --- slug -> name ---

    def test_band_name_from_slug(self):
        self.assertEqual(_band_name_from_slug("iron-meridian"), "Iron Meridian")
        self.assertEqual(_band_name_from_slug("riders-hymn"), "Riders Hymn")
        self.assertEqual(_band_name_from_slug("band_under_score"), "Band Under Score")

    # --- render: empty template ---
    def test_render_empty_template(self):
        out = render_playlist_yaml("Iron Meridian", [], from_songbook=False)
        self.assertIn('album: "Iron Meridian"', out)
        self.assertIn("tracks:", out)
        # Empty template carries instructional comments, no real track entries.
        self.assertIn("Add tracks below as they are published", out)
        real_track_lines = [ln for ln in out.splitlines()
                            if ln.lstrip().startswith("- name:")]
        self.assertEqual(real_track_lines, [])
        self.assertTrue(out.endswith("\n"))

    # --- render: with tracks ---
    def test_render_with_tracks_manual(self):
        tracks = [{"name": "First Song"}, {"name": "Second Song"}]
        out = render_playlist_yaml("My Band", tracks, from_songbook=False)
        self.assertIn('- name: "First Song"', out)
        self.assertIn('- name: "Second Song"', out)
        self.assertIn('file: ""', out)
        # Manual mode does not emit the songbook TODO comment.
        self.assertNotIn("TODO: set to the actual filename", out)

    def test_render_with_tracks_from_songbook(self):
        tracks = [{"name": "Discovered Song", "songbook_path": "docs/songbook/my-band/discovered-song.md"}]
        out = render_playlist_yaml("My Band", tracks, from_songbook=True)
        self.assertIn('- name: "Discovered Song"', out)
        self.assertIn("TODO: set to the actual filename", out)
        self.assertIn("# songbook: docs/songbook/my-band/discovered-song.md", out)

    # --- songbook frontmatter parsing ---
    def test_extract_title_from_songbook(self):
        tmp_path = self.tmp_path
        md = tmp_path / "song.md"
        md.write_text('---\ntitle: "My Great Song"\nstatus: published\n---\nbody\n')
        self.assertEqual(_extract_title_from_songbook(md), "My Great Song")

    def test_extract_title_unquoted(self):
        tmp_path = self.tmp_path
        md = tmp_path / "song.md"
        md.write_text("---\ntitle: Plain Title\n---\nbody\n")
        self.assertEqual(_extract_title_from_songbook(md), "Plain Title")

    def test_extract_title_no_frontmatter(self):
        tmp_path = self.tmp_path
        md = tmp_path / "song.md"
        md.write_text("just body, no frontmatter\n")
        self.assertIsNone(_extract_title_from_songbook(md))

    def test_is_published(self):
        tmp_path = self.tmp_path
        pub = tmp_path / "pub.md"
        pub.write_text("---\ntitle: X\nstatus: published\n---\n")
        draft = tmp_path / "draft.md"
        draft.write_text("---\ntitle: Y\nstatus: draft\n---\n")
        self.assertIs(_is_published(pub), True)
        self.assertIs(_is_published(draft), False)

    # --- discovery: only published, only with titles ---
    def test_discover_songbook_tracks(self):
        tmp_path = self.tmp_path
        band_dir = tmp_path / "docs" / "songbook" / "my-band"
        band_dir.mkdir(parents=True)
        (band_dir / "a.md").write_text('---\ntitle: "Alpha"\nstatus: published\n---\n')
        (band_dir / "b.md").write_text('---\ntitle: "Beta"\nstatus: draft\n---\n')
        (band_dir / "c.md").write_text('---\ntitle: "Gamma"\nstatus: published\n---\n')

        tracks = discover_songbook_tracks(tmp_path, "my-band")
        names = {t["name"] for t in tracks}
        # Only published entries with titles are returned.
        self.assertEqual(names, {"Alpha", "Gamma"})
        for t in tracks:
            self.assertTrue(t["songbook_path"].startswith("docs/songbook/my-band/"))

    def test_discover_songbook_no_dir(self):
        tmp_path = self.tmp_path
        self.assertEqual(discover_songbook_tracks(tmp_path, "no-such-band"), [])

    # --- docs-dir override on discovery ---
    def test_discover_default_docs_dir(self):
        tmp_path = self.tmp_path
        # Default (docs_dir=None) reads from {project_root}/docs/songbook — unchanged.
        band_dir = tmp_path / "docs" / "songbook" / "my-band"
        band_dir.mkdir(parents=True)
        (band_dir / "a.md").write_text('---\ntitle: "Alpha"\nstatus: published\n---\n')
        tracks = discover_songbook_tracks(tmp_path, "my-band")
        self.assertEqual({t["name"] for t in tracks}, {"Alpha"})

    def test_discover_docs_dir_override(self):
        tmp_path = self.tmp_path
        # With docs_dir pointing at a relocated docs root, discovery reads from there.
        alt_docs = tmp_path / "alt-docs"
        band_dir = alt_docs / "songbook" / "my-band"
        band_dir.mkdir(parents=True)
        (band_dir / "a.md").write_text('---\ntitle: "Relocated"\nstatus: published\n---\n')
        # The default {tmp_path}/docs has nothing.
        self.assertEqual(discover_songbook_tracks(tmp_path, "my-band"), [])
        tracks = discover_songbook_tracks(tmp_path, "my-band", docs_dir=alt_docs)
        self.assertEqual({t["name"] for t in tracks}, {"Relocated"})


# --- main() end-to-end via subprocess (path placement) ---

def _run(*args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True, text=True,
    )
    return proc


class TestMain(TmpPathTestCase):
    def test_main_default_writes_under_project_docs(self):
        tmp_path = self.tmp_path
        proc = _run("my-band", "--project-root", str(tmp_path))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "created")
        # Default destination is {project-root}/docs/{slug}-playlist.yaml.
        expected = tmp_path / "docs" / "my-band-playlist.yaml"
        self.assertTrue(expected.exists())
        self.assertEqual(payload["path"], "docs/my-band-playlist.yaml")

    def test_main_docs_dir_override_writes_there(self):
        tmp_path = self.tmp_path
        alt_docs = tmp_path / "alt-docs"
        proc = _run("my-band", "--project-root", str(tmp_path), "--docs-dir", str(alt_docs))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "created")
        # Playlist must land under the overridden docs dir, NOT {project-root}/docs.
        self.assertTrue((alt_docs / "my-band-playlist.yaml").exists())
        self.assertFalse((tmp_path / "docs" / "my-band-playlist.yaml").exists())

    def test_render_emits_band_audio_dir(self):
        out = render_playlist_yaml("My Band", [], from_songbook=False, band_slug="my-band")
        self.assertIn('audio_dir: "docs/audio/my-band"', out)
        # Without a band slug the key is omitted (resolver falls back to derivation).
        self.assertNotIn("audio_dir:", render_playlist_yaml("My Band", [], from_songbook=False))

    def test_main_follows_module_config(self):
        tmp_path = self.tmp_path
        # band_profiles_folder and songbook_folder relocated in config: the playlist
        # lands beside the profiles folder and --from-songbook reads the songbook there.
        (tmp_path / "_bmad").mkdir()
        (tmp_path / "_bmad" / "config.toml").write_text(
            "[modules.suno]\n"
            "band_profiles_folder = 'music/band-profiles'\n"
            "songbook_folder = '{project-root}/music/songbook'  # moved\n")
        install_resolver(tmp_path)
        entry = tmp_path / "music" / "songbook" / "my-band" / "song.md"
        entry.parent.mkdir(parents=True)
        entry.write_text('---\ntitle: "Moved Song"\nstatus: published\n---\n')
        proc = _run("my-band", "--project-root", str(tmp_path), "--from-songbook")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        target = tmp_path / "music" / "my-band-playlist.yaml"
        self.assertTrue(target.exists())
        self.assertIn("Moved Song", target.read_text())

    def test_titles_with_yaml_specials_round_trip(self):
        import yaml
        titles = ['She Said "Run"', "Back\\slash: a #1 song", "It's 3 A.M."]
        out = render_playlist_yaml('The "Quoted" Band', [{"name": t} for t in titles],
                                   from_songbook=True, band_slug="quoted-band")
        data = yaml.safe_load(out)
        self.assertEqual(data["album"], 'The "Quoted" Band')
        self.assertEqual([t["name"] for t in data["tracks"]], titles)
        self.assertEqual(data["audio_dir"], "docs/audio/quoted-band")

    def test_album_name_comes_from_the_band_profile(self):
        tmp_path = self.tmp_path
        profiles = tmp_path / "docs" / "band-profiles"
        profiles.mkdir(parents=True)
        (profiles / "rosas-voice.yaml").write_text("# craft note\nname: Rosa's Voice\ngenre: x\n")
        proc = _run("rosas-voice", "--project-root", str(tmp_path))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["album"], "Rosa's Voice")
        self.assertIn('album: "Rosa\'s Voice"', (tmp_path / "docs" / "rosas-voice-playlist.yaml").read_text())

    def test_album_name_flag_and_slug_fallback(self):
        tmp_path = self.tmp_path
        self.assertEqual(json.loads(_run("no-profile", "--project-root", str(tmp_path)).stdout)["album"],
                         "No Profile")
        proc = _run("other", "--project-root", str(tmp_path), "--album-name", "Given")
        self.assertEqual(json.loads(proc.stdout)["album"], "Given")

    def test_songbook_title_with_quotes_is_seeded_intact(self):
        import yaml
        tmp_path = self.tmp_path
        entry = tmp_path / "docs" / "songbook" / "my-band" / "a.md"
        entry.parent.mkdir(parents=True)
        entry.write_text("---\ntitle: 'She Said \"Run\"'\nstatus: published\n---\nbody\n")
        (entry.parent / "b.md").write_text("---\ntitle: Draft Song\nstatus: draft\n---\n")
        proc = _run("my-band", "--project-root", str(tmp_path), "--from-songbook")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = yaml.safe_load((tmp_path / "docs" / "my-band-playlist.yaml").read_text())
        self.assertEqual([t["name"] for t in data["tracks"]], ['She Said "Run"'])

    def test_status_reports_created_vs_overwritten(self):
        tmp_path = self.tmp_path
        self.assertEqual(json.loads(_run("b", "--project-root", str(tmp_path), "--force").stdout)["status"],
                         "created")
        self.assertEqual(json.loads(_run("b", "--project-root", str(tmp_path)).stdout)["status"], "exists")
        self.assertEqual(json.loads(_run("b", "--project-root", str(tmp_path), "--force").stdout)["status"],
                         "overwritten")

    def test_template_documents_optional_sequencer_fields(self):
        out = render_playlist_yaml("My Band", [], from_songbook=False)
        self.assertIn("felt_bpm", out)
        self.assertIn("locked_arcs", out)


if __name__ == "__main__":
    unittest.main()
