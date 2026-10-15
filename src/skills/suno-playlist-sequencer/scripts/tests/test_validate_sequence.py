#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for validate-sequence.py: the pre-write gate on the playlist YAML."""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT = str(Path(__file__).parent.parent / "validate-sequence.py")

PLAYLIST = """album: "Band A"
audio_dir: "docs/audio/band-a"
# Order in this list = playlist order.
tracks:
  - name: "One"
    file: "One.mp3"
  - name: "Two"
    file: "Two.mp3"
    felt_bpm: 72
  - name: "Three"
    file: "Three.mp3"
  - name: "Four"
    file: "Four.mp3"

locked_arcs:
  - "Two > Three"
"""


def load():
    spec = importlib.util.spec_from_file_location("validate_sequence", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def setup(tmp_path, order=None):
    p = tmp_path / "band-a-playlist.yaml"
    p.write_text(PLAYLIST)
    o = None
    if order is not None:
        o = tmp_path / "order.txt"
        o.write_text(order)
    return p, o


def run(m, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = m.main([*map(str, args)])
    return code, json.loads(out.getvalue())


class TestValidateSequence(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def test_read_order_strips_numbering_and_comments(self):
        m = load()
        self.assertEqual(m.read_order("# proposal\n1. One\n2) Two\n\n- Three\nFour\n"), ["One", "Two", "Three", "Four"])

    def test_current_order_surfaces_locked_arcs(self):
        m = load()
        p, _ = setup(self.tmp_path)
        code, out = run(m, p, "--locked", "One > Two")
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["moves"], [])
        self.assertEqual(out["locked_arcs"], [{"tracks": ["Two", "Three"], "status": "intact"},
                                      {"tracks": ["One", "Two"], "status": "intact"}])

    def test_permutation_errors_name_the_track(self):
        m = load()
        p, o = setup(self.tmp_path, "Four\nTwo\nThree\nTwo\nFive\n")
        code, out = run(m, p, "--order", o, "--write")
        self.assertEqual(code, 1)
        self.assertIs(out["written"], False)
        errs = " | ".join(out["errors"])
        self.assertIn("duplicated: Two (positions 2, 4)", errs)
        self.assertIn("dropped: One", errs)
        self.assertIn("unknown: Five", errs)
        self.assertEqual(p.read_text(), PLAYLIST)  # nothing written

    def test_split_and_reordered_arcs_fail(self):
        m = load()
        p, o = setup(self.tmp_path, "Two\nOne\nThree\nFour\n")
        code, out = run(m, p, "--order", o)
        self.assertEqual(code, 1)
        self.assertIn("locked arc split: Two > Three", out["errors"])
        p, o = setup(self.tmp_path, "Three\nTwo\nOne\nFour\n")
        code, out = run(m, p, "--order", o)
        self.assertIn("locked arc out-of-order: Two > Three", out["errors"])
        code, out = run(m, p, "--locked", "One > Ghost")
        self.assertTrue(any("not in the playlist: Ghost" in e for e in out["errors"]))

    def test_preview_then_write_keeps_everything_but_order(self):
        m = load()
        p, o = setup(self.tmp_path, "Four\nTwo\nThree\nOne\n")
        code, out = run(m, p, "--order", o)
        self.assertEqual(code, 0)
        self.assertIs(out["written"], False)
        self.assertEqual(p.read_text(), PLAYLIST)  # preview only
        self.assertEqual(out["moves"], [{"name": "Four", "from": 4, "to": 1}, {"name": "One", "from": 1, "to": 4}])
        self.assertEqual(out["unchanged"], 2)
        code, out = run(m, p, "--order", o, "--write")
        self.assertEqual(code, 0)
        self.assertIs(out["written"], True)
        text = p.read_text()
        self.assertTrue(text.startswith('album: "Band A"\naudio_dir: "docs/audio/band-a"\n# Order in this list = playlist order.\n'))
        data = yaml.safe_load(text)
        self.assertEqual([t["name"] for t in data["tracks"]], ["Four", "Two", "Three", "One"])
        self.assertEqual(data["tracks"][1], {"name": "Two", "file": "Two.mp3", "felt_bpm": 72})
        self.assertEqual(data["locked_arcs"], ["Two > Three"])

    def test_write_needs_order(self):
        m = load()
        p, _ = setup(self.tmp_path)
        code, out = run(m, p, "--write")
        self.assertEqual(code, 2)
        self.assertEqual(out["status"], "error")

    def test_unusable_playlists_are_errors_not_passes(self):
        m = load()
        p = self.tmp_path / "x-playlist.yaml"
        for text, needle in (("- a list\n", "must be a mapping"),
                             ("album: X\n", "no `tracks:` list"),
                             ("album: X\ntracks: []\n", "no `tracks:` list")):
            p.write_text(text)
            code, out = run(m, p)
            self.assertEqual(code, 2)
            self.assertIn(needle, out["error"])

    def test_unnamed_track_blocks_a_write_that_would_lose_it(self):
        m = load()
        p, o = setup(self.tmp_path, "Two\nOne\n")
        text = 'album: X\ntracks:\n  - name: One\n    file: One.mp3\n  - file: Orphan.mp3\n  - name: Two\n    file: Two.mp3\n'
        p.write_text(text)
        code, out = run(m, p, "--order", o, "--write")
        self.assertEqual(code, 2)
        self.assertIn("track 2", out["error"])
        self.assertEqual(p.read_text(), text)

    def test_short_arcs_are_reported(self):
        m = load()
        p, _ = setup(self.tmp_path)
        code, out = run(m, p, "--locked", "One")
        self.assertEqual(code, 2)
        self.assertIn("at least two tracks", out["error"])
        p.write_text(PLAYLIST.replace('  - "Two > Three"', '  - "Two > Three"\n  - "Four"'))
        code, out = run(m, p)
        self.assertEqual(code, 1)
        self.assertIn("locked_arcs item 2 names fewer than two tracks: 'Four'", out["errors"])

    def test_scalar_locked_arcs_is_one_arc(self):
        m = load()
        p, _ = setup(self.tmp_path)
        p.write_text(PLAYLIST.replace('locked_arcs:\n  - "Two > Three"', 'locked_arcs: "Three > Four"'))
        code, out = run(m, p)
        self.assertEqual(code, 0)
        self.assertEqual(out["locked_arcs"], [{"tracks": ["Three", "Four"], "status": "intact"}])

    def test_empty_order_file_is_an_error(self):
        m = load()
        p, o = setup(self.tmp_path, "# nothing yet\n")
        code, out = run(m, p, "--order", o)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
