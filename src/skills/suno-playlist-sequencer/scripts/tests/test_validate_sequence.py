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


def track(name, bpm, lufs, camelot="8A", key="A minor"):
    k = {"overall": key, "overall_camelot": camelot, "entry": key, "entry_camelot": camelot,
         "exit": key, "exit_camelot": camelot}
    return {"name": name, "bpm": bpm, "entry_bpm": bpm, "exit_bpm": bpm, "felt_bpm": None, "key": k,
            "loudness": {"entry_lufs": lufs, "exit_lufs": lufs, "thirds_lufs": [lufs] * 3}}


class TestWriteKeepsItemText(unittest.TestCase):
    def test_write_keeps_quotes_comments_and_fields(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            p = tmp / "band-a-playlist.yaml"
            p.write_text('album: "Band A"\ntracks:\n  # opener\n  - name: "One"\n    file: "One.mp3"\n\n'
                         '  - name: "Two"\n    file: \'Two.mp3\'  # single quotes\n    felt_bpm: 72\n\n'
                         '  - name: Three\n    file: Three.mp3\nnotes: keep me\n')
            o = tmp / "order.txt"
            o.write_text("Two\nThree\nOne\n")
            code, report = run(load(), p, "--order", o, "--write")
            self.assertEqual(code, 0)
            self.assertEqual(p.read_text(),
                             'album: "Band A"\ntracks:\n  - name: "Two"\n    file: \'Two.mp3\'  # single quotes\n    felt_bpm: 72\n\n'
                             '  - name: Three\n    file: Three.mp3\n\n  # opener\n  - name: "One"\n    file: "One.mp3"\nnotes: keep me\n')


class TestSeams(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)
        self.archive = self.tmp_path / "band-a.json"
        self.archive.write_text(json.dumps({"tracks": [
            track("One", 120, -9), track("Two", 144, -9), track("Three", 74, -10), track("Four", 121, -15)]}))

    def test_proposed_order_gets_measured_seam_labels(self):
        p, o = setup(self.tmp_path, "One\nFour\nTwo\nThree\n")
        code, report = run(load(), p, "--order", o, "--archive", self.archive)
        self.assertEqual(code, 0)
        labels = {(x["from"], x["to"]): x for x in report["seams"]}
        self.assertEqual(labels[("One", "Four")]["bpm_quality"], "smooth")
        self.assertEqual(labels[("One", "Four")]["loudness_quality"], "big jump (quieter)")
        self.assertTrue(labels[("Four", "Two")]["bpm_quality"].startswith("jump"))

    def test_felt_bpm_from_the_playlist_folds_the_seam(self):
        # Two's felt_bpm is 72 in the playlist: 144 measured folds to 72, close to Three's 74.
        p, _ = setup(self.tmp_path)
        code, report = run(load(), p, "--archive", self.archive)
        seam = [x for x in report["seams"] if (x["from"], x["to"]) == ("Two", "Three")][0]
        self.assertEqual(seam["bpm_quality"], "smooth")

    def test_track_missing_from_archive_is_named(self):
        self.archive.write_text(json.dumps({"tracks": [track("One", 120, -9)]}))
        p, _ = setup(self.tmp_path)
        code, report = run(load(), p, "--archive", self.archive)
        self.assertIn("missing", report["seams"][0])

    def test_slot_table_lists_every_slot_with_seams(self):
        p, _ = setup(self.tmp_path)
        code, report = run(load(), p, "--archive", self.archive, "--slot-table", "Four")
        rows = report["slot_table"]
        self.assertEqual([r["position"] for r in rows], [1, 2, 3, 4])
        self.assertEqual(rows[2]["splits_locked_arc"], ["Two > Three"])
        self.assertEqual(rows[0]["replaces"], None)
        summary = report["slot_summary"]
        self.assertEqual(summary["slots_splitting_a_locked_arc"], [3])
        self.assertTrue(all(r["net_jump_labels"] == r["jump_labels_made"] - r["jump_labels_removed"] for r in rows))
        self.assertIn(summary["fewest_net_jump_labels"], [r["net_jump_labels"] for r in rows])

    def test_rationale_flags_a_jump_called_smooth(self):
        p, o = setup(self.tmp_path, "One\nFour\nTwo\nThree\n")
        text = self.tmp_path / "why.txt"
        text.write_text("Four into Two is a smooth hand-off, and One > Four isn't smooth but works.")
        code, report = run(load(), p, "--order", o, "--archive", self.archive, "--rationale", text)
        self.assertEqual((code, report["status"]), (1, "fail"))
        self.assertEqual([f["seam"] for f in report["rationale_flags"]], ["Four > Two"])

    def test_rationale_reads_the_label_the_clause_is_about(self):
        rows = [{"from": "One", "to": "Five", "bpm_quality": "jump (33%)", "loudness_quality": "smooth"},
                {"from": "One", "to": "Four", "bpm_quality": "smooth", "loudness_quality": "big jump (6.0 LU)"}]
        flags = load().rationale_flags
        self.assertEqual(flags("One into Five is a smooth loudness step.", rows), [])
        self.assertEqual(len(flags("One into Five is a smooth tempo hand-off.", rows)), 1)
        self.assertEqual(flags("One into Four keeps a smooth tempo.", rows), [])
        self.assertEqual(len(flags("One into Four is a smooth seam.", rows)), 1)
        self.assertEqual(len(flags("One into Four is a smooth loudness step.", rows)), 1)

    def test_smooth_needs_a_smooth_label(self):
        rows = [{"from": "One", "to": "Two", "bpm_quality": "ok (4.8%)", "loudness_quality": "smooth"}]
        flags = load().rationale_flags
        self.assertEqual(len(flags("One into Two is smooth.", rows)), 1)
        self.assertEqual(flags("One into Two is the best of the options.", rows), [])

    def test_slot_reference_without_a_slot_table_is_not_read(self):
        rows = [{"from": "Four", "to": "Two", "bpm_quality": "jump (19%)", "loudness_quality": "smooth"}]
        self.assertEqual(load().rationale_flags("Slot 3 is the strongest alternative.", rows, ["One", "Four", "Two"]), [])

    def test_slot_reference_uses_the_slot_table_row(self):
        rows = [{"from": "Rust", "to": "Gravel", "bpm_quality": "jump (19%)", "loudness_quality": "smooth"}]
        slots = [{"position": 7, "seams": [{"from": "Rust", "to": "New", "bpm_quality": "smooth", "loudness_quality": "smooth"}]}]
        flags = load().rationale_flags("Slot 7 is smooth on the way in.", rows, ["A"], slots)
        self.assertEqual(flags, [])

    def test_worked_out_percentage_is_flagged(self):
        rows = [{"from": "One", "to": "Two", "bpm_quality": "ok (4.8%)", "loudness_quality": "smooth"}]
        flags = load().rationale_flags("One into Two is an ok tempo change (6.1%).", rows)
        self.assertEqual(len(flags), 1)
        self.assertEqual(load().rationale_flags("One into Two is an ok tempo change (4.8%).", rows), [])

    def test_brief_prints_only_the_cited_fields(self):
        p, o = setup(self.tmp_path, "One\nFour\nTwo\nThree\n")
        code, report = run(load(), p, "--order", o, "--archive", self.archive, "--brief")
        self.assertIn("seams", report)
        self.assertTrue(set(report) <= {"status", "errors", "locked_arcs", "seams", "moves", "slot_summary",
                                        "rationale_flags", "written"})

    def test_rationale_needs_archive(self):
        p, _ = setup(self.tmp_path)
        code, report = run(load(), p, "--rationale", self.tmp_path / "x.txt")
        self.assertEqual(code, 2)

    def test_unreadable_archive_is_an_error(self):
        p, _ = setup(self.tmp_path)
        code, report = run(load(), p, "--archive", self.tmp_path / "nope.json")
        self.assertEqual((code, report["status"]), (2, "error"))


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
