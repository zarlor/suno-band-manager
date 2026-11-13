#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for validate_sequence.py: the pre-write gate on the playlist YAML."""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

SCRIPT = str(Path(__file__).parent.parent / "validate_sequence.py")
PRODUCER = str(Path(__file__).parent.parent / "playlist_sequencing_data.py")

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
        try:
            code = m.main([*map(str, args)])
        except SystemExit as exc:  # a usage error
            code = exc.code
    return code, json.loads(out.getvalue())


def track(name, bpm, lufs, camelot="8A", key="A minor", exit_lufs=None):
    k = {"overall": key, "overall_camelot": camelot, "entry": key, "entry_camelot": camelot,
         "exit": key, "exit_camelot": camelot}
    out = lufs if exit_lufs is None else exit_lufs
    return {"name": name, "bpm": bpm, "entry_bpm": bpm, "exit_bpm": bpm, "felt_bpm": None, "key": k,
            "loudness": {"entry_lufs": lufs, "exit_lufs": out, "thirds_lufs": [lufs, lufs, out]}}


def load_producer():
    spec = importlib.util.spec_from_file_location("playlist_sequencing_data_for_validate", PRODUCER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def analyzed(name, bpm, exit_bpm, entry_key, entry_camelot, exit_key, exit_camelot, entry_lufs, exit_lufs, felt=None):
    """One track in the shape analyze_track returns (plus the name and felt_bpm main() adds)."""
    return {"name": name, "duration": 200.0, "bpm": bpm, "entry_bpm": bpm, "exit_bpm": exit_bpm,
            "tempo_source": "librosa", "felt_bpm": felt,
            "overall_key": entry_key, "overall_conf": 0.8, "overall_camelot": entry_camelot,
            "entry_key": entry_key, "entry_conf": 0.8, "entry_camelot": entry_camelot,
            "exit_key": exit_key, "exit_conf": 0.8, "exit_camelot": exit_camelot,
            "energy_level": 6, "intro_energy_pct": 40, "outro_energy_pct": 70,
            "loudness": {"integrated_lufs": -13.0, "lra_lu": 5.0, "thirds_lufs": [entry_lufs, -13.0, exit_lufs],
                         "build_lu": 1.0, "entry_lufs": entry_lufs, "exit_lufs": exit_lufs}}


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


    def test_zero_indent_list_keeps_item_text_too(self):
        # `tracks:` items at zero indent are valid YAML and take the same verbatim path.
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            p = tmp / "band-a-playlist.yaml"
            p.write_text('album: "Band A"\ntracks:\n# opener\n- name: "One"\n  file: "One.mp3"\n'
                         '- name: "Two"\n  file: \'Two.mp3\'  # single quotes\n  felt_bpm: 72\n'
                         '- name: Three\n  file: Three.mp3\nlocked_arcs:\n- [Two, Three]\n', encoding="utf-8")
            o = tmp / "order.txt"
            o.write_text("Two\nThree\nOne\n", encoding="utf-8")
            code, report = run(load(), p, "--order", o, "--write")
            self.assertEqual((code, report["written"], report["rewrite"]), (0, True, "verbatim"))
            self.assertEqual(p.read_text(encoding="utf-8"),
                             'album: "Band A"\ntracks:\n- name: "Two"\n  file: \'Two.mp3\'  # single quotes\n  felt_bpm: 72\n'
                             '- name: Three\n  file: Three.mp3\n# opener\n- name: "One"\n  file: "One.mp3"\n'
                             'locked_arcs:\n- [Two, Three]\n')

    def test_a_list_that_is_not_a_block_list_is_re_rendered_whole_and_says_so(self):
        # The fallback path: a flow-style list has no `- ` items to move as text.
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            p = tmp / "band-a-playlist.yaml"
            p.write_text('album: "Band A"\naudio_dir: docs/audio/band-a\ntracks:\n'
                         '  [{name: One, file: One.mp3}, {name: Two, file: Two.mp3, felt_bpm: 72},\n'
                         '   {name: Three, file: Three.mp3, note: "kept: yes"}]\n'
                         'locked_arcs:\n- [Two, Three]\n', encoding="utf-8")
            before = yaml.safe_load(p.read_text(encoding="utf-8"))
            o = tmp / "order.txt"
            o.write_text("Two\nThree\nOne\n", encoding="utf-8")
            code, report = run(load(), p, "--order", o, "--write")
            self.assertEqual((code, report["written"], report["rewrite"]), (0, True, "re-rendered"))
            after = yaml.safe_load(p.read_text(encoding="utf-8"))
            by_name = {t["name"]: t for t in before["tracks"]}
            self.assertEqual(after["tracks"], [by_name["Two"], by_name["Three"], by_name["One"]])  # every field kept
            self.assertEqual(after["tracks"][0]["felt_bpm"], 72)
            self.assertEqual({k: v for k, v in after.items() if k != "tracks"},
                             {k: v for k, v in before.items() if k != "tracks"})
            self.assertTrue(p.read_text(encoding="utf-8").startswith('album: "Band A"\naudio_dir: docs/audio/band-a\ntracks:\n'))

    def test_a_rewrite_that_loses_a_field_is_refused(self):
        # The round-trip check compares whole track entries, not only their names.
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            p = tmp / "band-a-playlist.yaml"
            text = 'album: X\ntracks:\n  [{name: One, file: One.mp3}, {name: Two, file: Two.mp3, felt_bpm: 72}]\n'
            p.write_text(text, encoding="utf-8")
            o = tmp / "order.txt"
            o.write_text("Two\nOne\n", encoding="utf-8")
            m = load()
            real_dump = yaml.safe_dump

            def lossy(items, **kw):
                return real_dump([{k: v for k, v in t.items() if k != "felt_bpm"} for t in items], **kw)
            with mock.patch.object(yaml, "safe_dump", lossy):
                code, report = run(m, p, "--order", o, "--write")
            self.assertEqual((code, report["written"]), (1, False))
            self.assertIn("did not round-trip", report["errors"][0])
            self.assertEqual(p.read_text(encoding="utf-8"), text)


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
        # Slot 1 (before One): Four > One steps up 6 LU. Slot 2: One > Four steps down 6 LU and Four > Two
        # jumps in tempo (121 to felt 72) and level, replacing One > Two (a tempo jump). Slot 3 splits the
        # arc: Two > Four jumps on both, Four > Three on tempo. Slot 4 (after Three): Three > Four, a tempo jump.
        self.assertEqual([(r["jump_labels_made"], r["jump_labels_removed"], r["net_jump_labels"]) for r in rows],
                         [(1, 0, 1), (3, 1, 2), (3, 0, 3), (1, 0, 1)])
        self.assertEqual(summary["net_by_slot"], {"1": 1, "2": 2, "3": 3, "4": 1})
        self.assertEqual(summary["fewest_net_jump_labels"], 1)
        self.assertEqual(summary["slots_at_fewest"], [1, 4])
        self.assertEqual(summary["slots_adding_no_jump_label"], [])

    def test_slot_summary_never_counts_a_slot_that_splits_a_locked_arc(self):
        # One fits best between Two and Three, the locked arc: level with both, and it replaces their 8 LU step.
        self.archive.write_text(json.dumps({"tracks": [
            track("One", 73, -10, exit_lufs=-18), track("Two", 72, -10), track("Three", 74, -18),
            track("Four", 120, -18)]}), encoding="utf-8")
        p, _ = setup(self.tmp_path)
        code, report = run(load(), p, "--archive", self.archive, "--slot-table", "One")
        rows, summary = report["slot_table"], report["slot_summary"]
        self.assertEqual([r["splits_locked_arc"] for r in rows], [[], ["Two > Three"], [], []])
        nets = [r["net_jump_labels"] for r in rows]
        self.assertEqual(rows[1]["jump_labels_made"], 0)
        self.assertLess(nets[1], min(nets[0], nets[2], nets[3]))  # the splitter is the best slot on jumps alone
        self.assertEqual(summary["slots_splitting_a_locked_arc"], [2])
        self.assertNotIn(2, summary["slots_at_fewest"])
        self.assertNotIn(2, summary["slots_adding_no_jump_label"])
        self.assertEqual(summary["fewest_net_jump_labels"], min(nets[0], nets[2], nets[3]))
        self.assertEqual(summary["slots_at_fewest"],
                         [r["position"] for r in rows if not r["splits_locked_arc"]
                          and r["net_jump_labels"] == summary["fewest_net_jump_labels"]])
        self.assertEqual(summary["net_by_slot"]["2"], nets[1])  # still listed, with its scope in the note

    def test_rationale_flags_a_jump_called_smooth(self):
        p, o = setup(self.tmp_path, "One\nFour\nTwo\nThree\n")
        text = self.tmp_path / "why.txt"
        text.write_text("Four into Two is a smooth hand-off, and One > Four isn't smooth but works.")
        code, report = run(load(), p, "--order", o, "--archive", self.archive, "--rationale", text)
        self.assertEqual((code, report["status"]), (1, "fail"))
        self.assertEqual([f["seam"] for f in report["rationale_flags"]], ["Four > Two"])

    def test_rationale_reads_the_label_the_clause_is_about(self):
        rows = [{"from": "One", "to": "Five", "bpm_quality": "jump (33%)", "loudness_quality": "smooth"},
                {"from": "One", "to": "Four", "bpm_quality": "smooth", "loudness_quality": "big jump (quieter)"}]
        flags = load().rationale_flags
        self.assertEqual(flags("One into Five is a smooth loudness step.", rows), [])
        self.assertEqual(len(flags("One into Five is a smooth tempo hand-off.", rows)), 1)
        self.assertEqual(flags("One into Four keeps a smooth tempo.", rows), [])
        self.assertEqual(len(flags("One into Four is a smooth seam.", rows)), 1)
        self.assertEqual(len(flags("One into Four is a smooth loudness step.", rows)), 1)

    def test_smooth_needs_a_smooth_label(self):
        # The labels the producer emits: smooth, ok, jump (N%); smooth, noticeable (..), big jump (..).
        rows = [{"from": "One", "to": "Two", "bpm_quality": "ok", "loudness_quality": "smooth"}]
        flags = load().rationale_flags
        self.assertEqual(len(flags("One into Two is smooth.", rows)), 1)
        self.assertEqual(flags("One into Two is the best of the options.", rows), [])
        rows = [{"from": "One", "to": "Two", "bpm_quality": "smooth", "loudness_quality": "noticeable (louder)"}]
        self.assertEqual(len(flags("One into Two is a clean hand-off.", rows)), 1)
        self.assertEqual(flags("One into Two is the strongest option.", rows), [])

    def test_a_jump_called_best_or_strongest_is_flagged(self):
        rows = [{"from": "Four", "to": "Two", "bpm_quality": "jump (19%)", "loudness_quality": "smooth"}]
        flags = load().rationale_flags
        for claim in ("Four into Two is the strongest option.", "Four into Two is the best slot.",
                      "Four into Two is the ideal place for it."):
            self.assertEqual([f["seam"] for f in flags(claim, rows)], ["Four > Two"], claim)
        self.assertEqual(flags("Four into Two is not the strongest option.", rows), [])
        rows = [{"from": "Four", "to": "Two", "bpm_quality": "smooth", "loudness_quality": "big jump (louder)"}]
        self.assertEqual([f["label"] for f in flags("Four into Two is the best slot.", rows)], ["big jump (louder)"])

    def test_cli_fails_a_rationale_that_calls_a_jump_the_strongest(self):
        p, o = setup(self.tmp_path, "One\nFour\nTwo\nThree\n")
        text = self.tmp_path / "why.txt"
        text.write_text("Four into Two is the strongest option.", encoding="utf-8")
        code, report = run(load(), p, "--order", o, "--archive", self.archive, "--rationale", text)
        self.assertEqual((code, report["status"]), (1, "fail"))
        self.assertEqual([(f["seam"], f["label"]) for f in report["rationale_flags"]], [("Four > Two", "jump (40%)")])
        self.assertTrue(any("Four > Two is a jump (40%) seam" in e for e in report["errors"]))

    def test_names_holding_commas_or_joining_words_are_read_whole(self):
        rows = [{"from": "Salt, Smoke and Iron", "to": "Me and You", "bpm_quality": "jump (22%)",
                 "loudness_quality": "smooth"},
                {"from": "Me and You", "to": "Clean Slate", "bpm_quality": "smooth", "loudness_quality": "smooth"}]
        flags = load().rationale_flags
        found = flags("Salt, Smoke and Iron into Me and You is a smooth hand-off.", rows)
        self.assertEqual([f["seam"] for f in found], ["Salt, Smoke and Iron > Me and You"])
        self.assertEqual(found[0]["clause"], "Salt, Smoke and Iron into Me and You is a smooth hand-off.")
        # A word inside a title ("Clean") is not a claim about the seam.
        self.assertEqual(flags("Salt, Smoke and Iron into Me and You, then Clean Slate.", rows), [])
        self.assertEqual(flags("Me and You into Clean Slate is smooth.", rows), [])

    def test_praise_of_an_unmeasured_seam_is_flagged(self):
        rows = [{"from": "One", "to": "Ghost", "missing": "no analysis for Ghost"}]
        found = load().rationale_flags("One into Ghost is a smooth hand-off.", rows)
        self.assertEqual([(f["seam"], f["label"]) for f in found], [("One > Ghost", "unmeasured")])
        self.assertEqual(load().rationale_flags("One into Ghost is unmeasured: Ghost has no analysis.", rows), [])

    def test_slot_reference_without_a_slot_table_is_not_read(self):
        rows = [{"from": "Four", "to": "Two", "bpm_quality": "jump (19%)", "loudness_quality": "smooth"}]
        self.assertEqual(load().rationale_flags("Slot 3 is the strongest alternative.", rows, ["One", "Four", "Two"]), [])

    def test_slot_reference_uses_the_slot_table_row(self):
        rows = [{"from": "Rust", "to": "Gravel", "bpm_quality": "jump (19%)", "loudness_quality": "smooth"}]
        slots = [{"position": 7, "seams": [{"from": "Rust", "to": "New", "bpm_quality": "smooth", "loudness_quality": "smooth"}]}]
        flags = load().rationale_flags("Slot 7 is smooth on the way in.", rows, ["A"], slots)
        self.assertEqual(flags, [])

    def test_worked_out_percentage_is_flagged(self):
        flags = load().rationale_flags
        rows = [{"from": "Four", "to": "Two", "bpm_quality": "jump (19%)", "loudness_quality": "smooth"}]
        self.assertEqual(flags("Four into Two is a 19% tempo jump.", rows), [])
        found = flags("Four into Two is a 25% tempo jump.", rows)
        self.assertEqual([(f["kind"], f["seam"]) for f in found], [("percentage", "Four > Two")])
        self.assertIn("25.0% is not a figure its labels give", found[0]["detail"])
        # An `ok` label carries no percentage, so any figure beside it was worked out.
        rows = [{"from": "One", "to": "Two", "bpm_quality": "ok", "loudness_quality": "smooth"}]
        self.assertEqual([f["kind"] for f in flags("One into Two is an ok tempo change (4.8%).", rows)], ["percentage"])
        self.assertEqual(flags("One into Two is an ok tempo change.", rows), [])

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

    def test_archive_of_another_shape_is_an_error_not_a_crash(self):
        p, _ = setup(self.tmp_path)
        other = self.tmp_path / "other.json"
        for body in ([1, 2, 3], {"script": "batch-full-analysis", "tracks": [{"file": "One.mp3", "key": "A minor"}]},
                     {"tracks": "none"}, "just a string"):
            other.write_text(json.dumps(body), encoding="utf-8")
            code, report = run(load(), p, "--archive", other)
            self.assertEqual((code, report["status"]), (2, "error"), body)
            self.assertIn("not a playlist-sequencing-data report", report["error"])
        other.write_bytes(b'{"tracks": [{"name": "caf\xe9"}]}')  # not UTF-8
        code, report = run(load(), p, "--archive", other)
        self.assertEqual(code, 2)
        self.assertIn("archive unreadable", report["error"])

    def test_archive_fields_of_the_wrong_type_read_as_absent(self):
        p, _ = setup(self.tmp_path)
        odd = track("Three", 74, -10)
        odd.update(key="A minor", entry_bpm="74", loudness="loud")
        self.archive.write_text(json.dumps({"tracks": [
            track("One", 120, -9), track("Two", 144, -9), odd, {"name": "Four", "bpm": "121"}]}), encoding="utf-8")
        code, report = run(load(), p, "--archive", self.archive)
        self.assertEqual(code, 0)
        seam = {(x["from"], x["to"]): x for x in report["seams"]}
        self.assertEqual(seam[("Two", "Three")]["key_relation"], "unknown")
        self.assertIsNone(seam[("Two", "Three")]["loudness_step_lu"])
        self.assertEqual(seam[("Three", "Four")]["missing"], "no analysis for Four")

    def test_quoted_or_zero_felt_bpm_is_ignored_and_reported(self):
        p, _ = setup(self.tmp_path)
        p.write_text(PLAYLIST.replace("felt_bpm: 72", 'felt_bpm: "72"').replace(
            '    file: "Three.mp3"\n', '    file: "Three.mp3"\n    felt_bpm: 0\n'), encoding="utf-8")
        code, report = run(load(), p, "--archive", self.archive)
        self.assertEqual(code, 0)
        seam = [x for x in report["seams"] if (x["from"], x["to"]) == ("Two", "Three")][0]
        self.assertEqual((seam["bpm_from"], seam["bpm_basis"]), (144.0, "exit/entry"))  # not folded to 72
        self.assertTrue(seam["bpm_quality"].startswith("jump"))
        self.assertEqual(report["felt_bpm_ignored"], [
            {"name": "Two", "value": "72", "reason": "not a positive number"},
            {"name": "Three", "value": 0, "reason": "not a positive number"}])

    def test_seams_read_the_archive_the_producer_writes(self):
        # The archive is built by playlist_sequencing_data.py itself, not written by hand here.
        producer = load_producer()
        results = [analyzed("One", 120.0, 126.0, "A minor", "8A", "E minor", "9A", -12.0, -9.0),
                   analyzed("Two", 144.0, 146.0, "C major", "8B", "C major", "8B", -16.0, -11.0, felt=72.0),
                   analyzed("Three", 74.0, 74.0, "A major", "11B", "F# minor", "11A", -10.5, -20.0),
                   analyzed("Four", 121.0, 0.0, "E minor", "9A", "E minor", "9A", -13.0, -13.0)]
        producer.compute_transitions(results)
        report = producer.build_report("Band A", results)
        self.archive.write_text(json.dumps(report), encoding="utf-8")
        p, _ = setup(self.tmp_path)  # the same order; the YAML records Two's felt_bpm as 72 too
        code, out = run(load(), p, "--archive", self.archive)
        self.assertEqual(code, 0)
        self.assertEqual(len(out["seams"]), 3)
        for seam, written in zip(out["seams"], report["tracks"]):
            expected = written["transition_to_next"]
            self.assertEqual(seam["from"], written["name"])
            for field in ("to", "bpm_quality", "loudness_quality", "key_relation", "key_compat", "loudness_step_lu",
                          "bpm_from", "bpm_to", "bpm_basis", "camelot_distance", "pulse_pair"):
                self.assertEqual(seam[field], expected[field], (seam["from"], field))
        # The fixture exercises the labels, so a silent collapse to one value can't pass.
        self.assertEqual([s["bpm_quality"] for s in out["seams"]], ["jump (43%)", "smooth", "jump (64%)"])
        self.assertEqual([s["key_relation"] for s in out["seams"]], ["distant", "distant", "two-step"])
        self.assertEqual([s["loudness_quality"] for s in out["seams"]],
                         ["big jump (quieter)", "smooth", "big jump (louder)"])
        # A proposed order makes new seams from the same entries: Four exits at 0 BPM, so its tempo is unmeasured.
        o = self.tmp_path / "order.txt"
        o.write_text("Four\nOne\nTwo\nThree\n", encoding="utf-8")
        code, out = run(load(), p, "--order", o, "--archive", self.archive)
        self.assertEqual(out["seams"][0]["bpm_quality"], "unknown")
        self.assertEqual(out["seams"][0]["key_relation"], "adjacent")


class TestValidateSequence(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def test_read_order_strips_numbering_and_comments(self):
        m = load()
        self.assertEqual(m.read_order("# proposal\n1. One\n2) Two\n\n- Three\nFour\n"), ["One", "Two", "Three", "Four"])

    def test_a_line_that_is_a_track_name_is_taken_whole(self):
        m = load()
        known = ["#1 Crush", "- Dash", "99. Luftballons", "3) Doors Down", "Plain"]
        self.assertEqual(m.read_order("# a comment\n#1 Crush\n- Dash\n99. Luftballons\n3) Doors Down\n2. Plain\n", known),
                         ["#1 Crush", "- Dash", "99. Luftballons", "3) Doors Down", "Plain"])
        self.assertEqual(m.read_order("1. #1 Crush\n- - Dash\n", known), ["#1 Crush", "- Dash"])  # numbered, then exact
        p, o = setup(self.tmp_path, "Four\n#1 Crush\n99. Luftballons\n- Dash\n")
        p.write_text('album: X\ntracks:\n  - name: "#1 Crush"\n  - name: "- Dash"\n  - name: "99. Luftballons"\n'
                     '  - name: Four\n', encoding="utf-8")
        code, out = run(m, p, "--order", o, "--write")
        self.assertEqual((code, out["errors"], out["written"]), (0, [], True))
        self.assertEqual([t["name"] for t in yaml.safe_load(p.read_text(encoding="utf-8"))["tracks"]],
                         ["Four", "#1 Crush", "99. Luftballons", "- Dash"])

    def test_duplicate_playlist_name_blocks_an_order_however_it_lists_it(self):
        m = load()
        text = ('album: X\ntracks:\n  - name: One\n    file: One.mp3\n  - name: Two\n    file: Two.mp3\n'
                '  - name: One\n    file: One-reprise.mp3\n')
        for order in ("Two\nOne\n", "Two\nOne\nOne\n"):  # listed once would drop a track; twice can't tell them apart
            p, o = setup(self.tmp_path, order)
            p.write_text(text, encoding="utf-8")
            code, out = run(m, p, "--order", o, "--write")
            self.assertEqual((code, out["written"]), (1, False), order)
            self.assertTrue(any(e.startswith("duplicated in the playlist: One (tracks 1, 3)") for e in out["errors"]))
            self.assertEqual(p.read_text(encoding="utf-8"), text)  # all three entries still there
        code, out = run(m, p)  # the current-order check names it too
        self.assertEqual(code, 1)
        self.assertIn("duplicated: One (positions 1, 3)", out["errors"])

    def test_non_utf8_input_is_an_error_not_a_crash(self):
        m = load()
        p, o = setup(self.tmp_path, "One\nTwo\nThree\nFour\n")
        o.write_bytes("One\nTwo\nThree\nFour\nCaf\xe9\n".encode("latin-1"))
        code, out = run(m, p, "--order", o)
        self.assertEqual((code, out["status"]), (2, "error"))
        self.assertIn("UTF-8", out["error"])
        p.write_bytes(PLAYLIST.replace("Band A", "Band \xc9").encode("latin-1"))
        code, out = run(m, p)
        self.assertEqual((code, out["status"]), (2, "error"))
        self.assertIn("UTF-8", out["error"])

    def test_missing_pyyaml_is_the_structured_error_exit(self):
        m = load()
        p, _ = setup(self.tmp_path)
        real = importlib.util.find_spec
        with mock.patch.object(importlib.util, "find_spec", lambda name, *a: None if name == "yaml" else real(name, *a)):
            code, out = run(m, p)
        self.assertEqual((code, out["status"]), (2, "error"))
        self.assertIn("pyyaml", out["error"])
        self.assertIn("uv run", out["error"])

    def test_usage_error_prints_the_error_object(self):
        m = load()
        p, _ = setup(self.tmp_path)
        code, out = run(m, p, "--no-such-flag")
        self.assertEqual((code, out["status"]), (2, "error"))
        self.assertIn("--no-such-flag", out["error"])

    def test_output_folder_is_created_and_a_bad_one_is_an_error(self):
        m = load()
        p, _ = setup(self.tmp_path)
        target = self.tmp_path / "new" / "deep" / "report.json"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = m.main([str(p), "-o", str(target)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["status"], "ok")
        blocker = self.tmp_path / "file.txt"
        blocker.write_text("x", encoding="utf-8")
        code, out = run(m, p, "-o", blocker / "sub" / "report.json")  # a file where a folder is needed
        self.assertEqual((code, out["status"]), (2, "error"))
        self.assertIn("-o", out["error"])

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
