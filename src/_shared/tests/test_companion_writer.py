#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for companion_writer: what a refresh keeps, what it replaces, and where the file goes.

The companion files hold the owner's hand-written sections outside the AUTOGEN
markers, so every branch is pinned on what survives it.
"""
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

SHARED = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHARED))
from companion_writer import MARKER_END, MARKER_START_FMT, resolve_companion_path, update_companion  # noqa: E402

SCRIPT = "analyze-audio"
START = MARKER_START_FMT.format(script=SCRIPT)
OTHER_START = MARKER_START_FMT.format(script="batch-full-analysis")

# A child Python whose default text encoding is ASCII, standing in for a platform
# whose default is not UTF-8 (Windows cp1252): a text read or write without
# encoding="utf-8" fails there on the first non-ASCII character.
ASCII_LOCALE = {**os.environ, "LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}
ASCII_DRIVER = r"""
import sys
sys.path.insert(0, sys.argv[1])
from companion_writer import update_companion
from json_archiver import write_archive
folder = sys.argv[2]
arrow, cafe = "\u2192", "Caf\u00e9"
made = folder + "/made.md"
update_companion(made, "x", "In " + arrow + " out", header="# " + cafe)   # created
update_companion(made, "x", "Fresh " + arrow + " " + cafe)                 # refreshed (reads, then writes)
kept = folder + "/kept.md"
with open(kept, "w", encoding="utf-8") as f:
    f.write("Hand note " + arrow + " " + cafe + "\n")
update_companion(kept, "x", "Block " + arrow)                               # wrapped (reads, then writes)
write_archive(folder + "/a.json", {"title": cafe + " " + arrow})
"""


class TmpPathTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name).resolve()
        self.path = self.tmp_path / "docs" / "audio-analysis-reference.md"

    def seed(self, text):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(text, encoding="utf-8")

    def text(self):
        return self.path.read_text(encoding="utf-8")


class TestCreate(TmpPathTestCase):
    def test_missing_file_is_created_with_the_header_above_the_markers(self):
        res = update_companion(str(self.path), SCRIPT, "body line\n\n", header="# Title\n")
        self.assertEqual(res["status"], "created")
        self.assertEqual(res["path"], str(self.path))
        self.assertEqual(self.text(), f"# Title\n\n{START}\nbody line\n{MARKER_END}\n")
        self.assertEqual(res["bytes_written"], len(self.text()))

    def test_missing_file_without_a_header_starts_at_the_marker(self):
        res = update_companion(str(self.path), SCRIPT, "body line")
        self.assertEqual(res["status"], "created")
        self.assertEqual(self.text(), f"{START}\nbody line\n{MARKER_END}\n")


class TestRefresh(TmpPathTestCase):
    def test_text_outside_the_markers_survives_and_the_block_is_replaced(self):
        self.seed(f"Owner note\n{START}\nold\n{MARKER_END}\nBelow\n")
        res = update_companion(str(self.path), SCRIPT, "new")
        self.assertEqual(res["status"], "refreshed")
        self.assertEqual(self.text(), f"Owner note\n{START}\nnew\n{MARKER_END}\nBelow\n")

    def test_hand_written_sections_above_and_below_survive_a_second_run(self):
        update_companion(str(self.path), SCRIPT, "first results", header="# Audio Analysis Reference")
        created = self.text()
        self.seed(created.replace(START, "Hand note above\n" + START)
                  + "\n## Felt BPM Corrections\nkeep me\n")
        res = update_companion(str(self.path), SCRIPT, "second results")
        after = self.text()
        self.assertEqual(res["status"], "refreshed")
        self.assertIn("Hand note above\n", after)
        self.assertTrue(after.endswith("\n## Felt BPM Corrections\nkeep me\n"))
        self.assertTrue(after.startswith("# Audio Analysis Reference\n"))
        self.assertIn(f"{START}\nsecond results\n{MARKER_END}", after)
        self.assertNotIn("first results", after)

    def test_the_header_is_not_added_on_a_refresh(self):
        self.seed(f"{START}\nold\n{MARKER_END}\n")
        update_companion(str(self.path), SCRIPT, "new", header="# Title")
        self.assertEqual(self.text(), f"{START}\nnew\n{MARKER_END}\n")

    def test_refreshing_twice_with_the_same_content_changes_nothing(self):
        self.seed(f"Above\n{START}\nold\n{MARKER_END}\nBelow\n")
        update_companion(str(self.path), SCRIPT, "new")
        once = self.text()
        update_companion(str(self.path), SCRIPT, "new")
        self.assertEqual(self.text(), once)

    def test_another_scripts_block_above_is_left_alone(self):
        other = f"{OTHER_START}\nother script's table\n{MARKER_END}\n"
        self.seed(f"Intro\n{other}Between\n{START}\nold\n{MARKER_END}\nBelow\n")
        for content in ("new", "newer"):
            res = update_companion(str(self.path), SCRIPT, content)
            self.assertEqual(res["status"], "refreshed")
        self.assertEqual(self.text(), f"Intro\n{other}Between\n{START}\nnewer\n{MARKER_END}\nBelow\n")

    def test_another_scripts_block_below_is_left_alone(self):
        other = f"{OTHER_START}\nother script's table\n{MARKER_END}\n"
        self.seed(f"{START}\nold\n{MARKER_END}\nBetween\n{other}")
        update_companion(str(self.path), SCRIPT, "new")
        self.assertEqual(self.text(), f"{START}\nnew\n{MARKER_END}\nBetween\n{other}")


class TestWrap(TmpPathTestCase):
    def test_unmarked_file_is_wrapped_and_its_content_kept(self):
        self.seed("hand notes\nsecond line\n")
        res = update_companion(str(self.path), SCRIPT, "new", header="# Title")
        after = self.text()
        self.assertEqual(res["status"], "wrapped")
        self.assertIn("note", res)
        self.assertTrue(after.startswith(f"# Title\n\n{START}\nnew\n{MARKER_END}\n"))
        self.assertTrue(after.endswith("hand notes\nsecond line\n"))

    def test_a_wrapped_file_refreshes_in_place_on_the_next_run(self):
        self.seed("hand notes\n")
        update_companion(str(self.path), SCRIPT, "first")
        res = update_companion(str(self.path), SCRIPT, "second")
        after = self.text()
        self.assertEqual(res["status"], "refreshed")
        self.assertEqual(after.count(START), 1)
        self.assertIn("second", after)
        self.assertNotIn("first", after)
        self.assertTrue(after.endswith("hand notes\n"))

    def test_a_file_holding_only_another_scripts_block_is_wrapped_with_that_block_kept(self):
        other = f"Intro\n{OTHER_START}\nother script's table\n{MARKER_END}\nOutro\n"
        self.seed(other)
        res = update_companion(str(self.path), SCRIPT, "new")
        after = self.text()
        self.assertEqual(res["status"], "wrapped")
        self.assertTrue(after.startswith(f"{START}\nnew\n{MARKER_END}\n"))
        self.assertTrue(after.endswith(other))

    def test_a_start_marker_with_no_end_after_it_loses_nothing(self):
        broken = f"{OTHER_START}\nother\n{MARKER_END}\nMiddle\n{START}\nunterminated block\n"
        self.seed(broken)
        res = update_companion(str(self.path), SCRIPT, "new")
        self.assertEqual(res["status"], "wrapped")
        self.assertTrue(self.text().endswith(broken))


class TestEncoding(TmpPathTestCase):
    def test_reads_and_writes_are_utf8_whatever_the_platform_default(self):
        proc = subprocess.run([sys.executable, "-c", ASCII_DRIVER, str(SHARED), str(self.tmp_path)],
                              capture_output=True, text=True, env=ASCII_LOCALE)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        made = (self.tmp_path / "made.md").read_bytes().decode("utf-8")
        self.assertEqual(made, f"# Café\n\n{MARKER_START_FMT.format(script='x')}\nFresh → Café\n{MARKER_END}\n")
        kept = (self.tmp_path / "kept.md").read_bytes().decode("utf-8")
        self.assertIn("Block →", kept)
        self.assertTrue(kept.endswith("Hand note → Café\n"))
        self.assertTrue((self.tmp_path / "a.json").is_file())


class TestResolveCompanionPath(unittest.TestCase):
    def test_none_means_no_companion(self):
        self.assertIsNone(resolve_companion_path(SCRIPT, None))
        self.assertIsNone(resolve_companion_path(SCRIPT, None, project_root="/r"))

    def test_empty_value_is_the_canonical_path_relative_to_the_working_directory(self):
        self.assertEqual(resolve_companion_path(SCRIPT, ""), "docs/audio-analysis-reference.md")
        self.assertEqual(resolve_companion_path("batch-full-analysis", ""), "docs/catalog-analysis-report.md")
        self.assertEqual(resolve_companion_path(SCRIPT, "", project_root="."), "docs/audio-analysis-reference.md")

    def test_per_album_script_names_the_file_after_the_album(self):
        self.assertEqual(resolve_companion_path("playlist-sequencing-data", "", album="Rider's Hymn"),
                         "docs/riders-hymn-playlist-sequencing.md")

    def test_project_root_prefixes_the_canonical_path(self):
        self.assertEqual(resolve_companion_path(SCRIPT, "", project_root="/r"),
                         os.path.join("/r", "docs/audio-analysis-reference.md"))
        self.assertEqual(resolve_companion_path("playlist-sequencing-data", "", "Band A", "/r"),
                         os.path.join("/r", "docs/band-a-playlist-sequencing.md"))

    def test_explicit_path_is_used_verbatim(self):
        self.assertEqual(resolve_companion_path(SCRIPT, "notes/mine.md"), "notes/mine.md")
        self.assertEqual(resolve_companion_path(SCRIPT, "notes/mine.md", project_root="/r"), "notes/mine.md")

    def test_unregistered_script_exits_1_with_a_reason(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit) as cm, redirect_stderr(err):
            resolve_companion_path("no-such-script", "")
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("no-such-script", err.getvalue())

    def test_per_album_script_without_an_album_exits_1_with_a_reason(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit) as cm, redirect_stderr(err):
            resolve_companion_path("playlist-sequencing-data", "")
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("per-album", err.getvalue())


if __name__ == "__main__":
    unittest.main()
