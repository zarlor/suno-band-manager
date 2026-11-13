#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for script_io.py and for how the scripts fail when input or output is bad.

Exit 1 means a gate ran and failed, so anything that stops a script from
running at all (unreadable input, unwritable output, a missing vendored
folder) has to exit 2 with the reason on stderr and no traceback.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent

# The scripts that read lyrics as `<file> | --text | --stdin`.
TEXT_SCRIPTS = ["validate_lyrics.py", "analyze_input.py", "syllable_counter.py",
                "cliche_detector.py", "section_length_checker.py"]
# The scripts that import the vendored _shared helpers.
SHARED_IMPORTERS = ["validate_lyrics.py", "analyze_input.py", "syllable_counter.py",
                    "cliche_detector.py", "assemble_summary.py"]

LYRICS = "[Verse 1]\nWalking through the morning light\nCounting shadows on the wall\n"


def run(script, *args, scripts_dir=SCRIPTS, **kwargs):
    return subprocess.run([sys.executable, str(Path(scripts_dir) / script), *args],
                          capture_output=True, **kwargs)


class TestBadInputExitsTwo(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def assert_bad_input(self, result, needle):
        self.assertEqual(result.returncode, 2, result.stderr)
        stderr = result.stderr.decode("utf-8", "replace")
        self.assertIn(needle, stderr)
        self.assertNotIn("Traceback", stderr)
        self.assertEqual(result.stdout, b"")

    def test_stdin_that_is_not_utf8(self):
        for script in TEXT_SCRIPTS:
            with self.subTest(script=script):
                result = run(script, "--stdin", input=b"[Verse 1]\ncaf\xe9 lights\n")
                self.assert_bad_input(result, "stdin")

    def test_file_that_is_not_utf8(self):
        bad = self.tmp / "latin1.txt"
        bad.write_bytes(b"[Verse 1]\ncaf\xe9 lights\n")
        for script in TEXT_SCRIPTS:
            with self.subTest(script=script):
                self.assert_bad_input(run(script, str(bad)), "latin1.txt")

    def test_unwritable_output_path(self):
        target = str(self.tmp / "no-such-folder" / "out.json")
        for script in TEXT_SCRIPTS:
            with self.subTest(script=script):
                self.assert_bad_input(run(script, "--text", LYRICS, "-o", target), "no-such-folder")
        self.assert_bad_input(run("validate_options.py", "ST,CD", "-o", target), "no-such-folder")
        self.assert_bad_input(run("lyrics_diff.py", "--original-text", "a", "--transformed-text", "b",
                                  "-o", target), "no-such-folder")
        self.assert_bad_input(run("spacing_check.py", "--original-text", "a", "--transformed-text", "a",
                                  "-o", target), "no-such-folder")

    def test_missing_shared_folder(self):
        copy = self.tmp / "scripts"
        shutil.copytree(SCRIPTS, copy, ignore=shutil.ignore_patterns("_shared", "tests", "__pycache__", ".*"))
        for script in SHARED_IMPORTERS:
            with self.subTest(script=script):
                result = run(script, "--help", scripts_dir=copy)
                self.assert_bad_input(result, "_shared")


class TestTextInput(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def test_empty_text_argument_is_text_not_a_missing_argument(self):
        for script in TEXT_SCRIPTS:
            with self.subTest(script=script):
                result = run(script, "--text", "")
                self.assertIn(result.returncode, (0, 1))  # ran; validate-lyrics fails empty lyrics
                # The report's `script` label keeps its hyphenated form; only the file name is snake_case.
                self.assertEqual(json.loads(result.stdout)["script"], script[:-3].replace("_", "-"))

    def test_no_input_prints_help_and_exits_2(self):
        for script in TEXT_SCRIPTS:
            with self.subTest(script=script):
                result = run(script)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b"usage:", result.stdout)

    def test_byte_order_mark_is_dropped_from_file_and_stdin(self):
        path = self.tmp / "bom.txt"
        path.write_bytes(b"\xef\xbb\xbf" + LYRICS.encode("utf-8"))
        plain = json.loads(run("validate_lyrics.py", "--text", LYRICS).stdout)["metrics"]
        from_file = json.loads(run("validate_lyrics.py", str(path)).stdout)["metrics"]
        from_stdin = json.loads(run("validate_lyrics.py", "--stdin", input=path.read_bytes()).stdout)["metrics"]
        self.assertEqual(plain["sections"], ["Verse 1"])
        self.assertEqual(from_file, plain)
        self.assertEqual(from_stdin, plain)

    def test_output_file_is_utf8_json(self):
        out = self.tmp / "report.json"
        result = run("validate_lyrics.py", "--text", LYRICS, "-o", str(out))
        self.assertEqual(result.stdout, b"")
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["script"], "validate-lyrics")

    def test_non_ascii_text_prints_under_an_ascii_locale(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("LC_", "LANG", "PYTHON"))}
        env.update(LC_ALL="C", PYTHONUTF8="0", PYTHONCOERCECLOCALE="0")
        original = self.tmp / "orig.txt"
        original.write_text("café   lights\n夜の雨", encoding="utf-8")
        draft = self.tmp / "draft.txt"
        draft.write_text("[Verse]\ncafé lights\n夜の雨", encoding="utf-8")
        result = run("spacing_check.py", "--original", str(original), "--transformed", str(draft),
                     "--flatten", env=env)
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout.decode("utf-8"))
        self.assertIn("café lights", report["flat_copy"])
        self.assertIn("夜の雨", report["flat_copy"])


if __name__ == "__main__":
    unittest.main()
