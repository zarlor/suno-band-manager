#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for diff_profiles.py"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location(
    "diff_profiles",
    Path(__file__).parent.parent / "diff_profiles.py"
)
diff_profiles_mod = module_from_spec(spec)
spec.loader.exec_module(diff_profiles_mod)
diff_profiles = diff_profiles_mod.diff_profiles


PROFILE_A = {
    "name": "Test Band",
    "genre": "indie rock",
    "mood": "melancholic",
    "model_preference": "v4.5-all",
    "tier": "free",
    "style_baseline": "Indie rock with warm guitars",
    "vocal": {
        "gender": "male",
        "tone": "warm",
        "delivery": "intimate",
        "energy": "restrained",
    },
}


def write_yaml(tmp_path, filename, data):
    path = tmp_path / filename
    with open(path, "w") as f:
        yaml.dump(data, f)
    return path


class TmpPathTestCase(unittest.TestCase):
    """Gives each test a fresh temporary directory as self.tmp_path."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name).resolve()


class TestDiffProfiles(TmpPathTestCase):
    def test_identical_profiles(self):
        tmp_path = self.tmp_path
        a = write_yaml(tmp_path, "a.yaml", PROFILE_A)
        b = write_yaml(tmp_path, "b.yaml", PROFILE_A)
        result = diff_profiles(a, b)
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["has_changes"], False)
        self.assertEqual(result["summary"]["total_changes"], 0)

    def test_changed_fields(self):
        tmp_path = self.tmp_path
        modified = {**PROFILE_A, "genre": "electronic", "mood": "energetic"}
        a = write_yaml(tmp_path, "a.yaml", PROFILE_A)
        b = write_yaml(tmp_path, "b.yaml", modified)
        result = diff_profiles(a, b)
        self.assertIs(result["has_changes"], True)
        self.assertEqual(result["summary"]["fields_changed"], 2)
        changed_fields = [c["field"] for c in result["changed"]]
        self.assertIn("genre", changed_fields)
        self.assertIn("mood", changed_fields)

    def test_added_fields(self):
        tmp_path = self.tmp_path
        modified = {**PROFILE_A, "language": "Spanish", "instrumental": True}
        a = write_yaml(tmp_path, "a.yaml", PROFILE_A)
        b = write_yaml(tmp_path, "b.yaml", modified)
        result = diff_profiles(a, b)
        self.assertIs(result["has_changes"], True)
        self.assertGreaterEqual(result["summary"]["fields_added"], 2)
        added_fields = [c["field"] for c in result["added"]]
        self.assertIn("language", added_fields)
        self.assertIn("instrumental", added_fields)

    def test_removed_fields(self):
        tmp_path = self.tmp_path
        modified = {k: v for k, v in PROFILE_A.items() if k != "mood"}
        a = write_yaml(tmp_path, "a.yaml", PROFILE_A)
        b = write_yaml(tmp_path, "b.yaml", modified)
        result = diff_profiles(a, b)
        self.assertIs(result["has_changes"], True)
        self.assertGreaterEqual(result["summary"]["fields_removed"], 1)
        removed_fields = [c["field"] for c in result["removed"]]
        self.assertIn("mood", removed_fields)

    def test_nested_changes(self):
        tmp_path = self.tmp_path
        modified = {**PROFILE_A, "vocal": {**PROFILE_A["vocal"], "tone": "bright, clear"}}
        a = write_yaml(tmp_path, "a.yaml", PROFILE_A)
        b = write_yaml(tmp_path, "b.yaml", modified)
        result = diff_profiles(a, b)
        self.assertIs(result["has_changes"], True)
        changed_fields = [c["field"] for c in result["changed"]]
        self.assertIn("vocal.tone", changed_fields)

    def test_missing_original(self):
        tmp_path = self.tmp_path
        b = write_yaml(tmp_path, "b.yaml", PROFILE_A)
        result = diff_profiles(tmp_path / "nope.yaml", b)
        self.assertEqual(result["status"], "fail")
        self.assertIn("errors", result)

    def test_missing_modified(self):
        tmp_path = self.tmp_path
        a = write_yaml(tmp_path, "a.yaml", PROFILE_A)
        result = diff_profiles(a, tmp_path / "nope.yaml")
        self.assertEqual(result["status"], "fail")

    def test_invalid_yaml(self):
        tmp_path = self.tmp_path
        a = write_yaml(tmp_path, "a.yaml", PROFILE_A)
        bad = tmp_path / "bad.yaml"
        bad.write_text(": {{invalid yaml")
        result = diff_profiles(a, bad)
        self.assertEqual(result["status"], "fail")

    def test_mixed_changes(self):
        tmp_path = self.tmp_path
        modified = {**PROFILE_A, "genre": "electronic", "language": "French"}
        del modified["mood"]
        a = write_yaml(tmp_path, "a.yaml", PROFILE_A)
        b = write_yaml(tmp_path, "b.yaml", modified)
        result = diff_profiles(a, b)
        self.assertIs(result["has_changes"], True)
        self.assertGreaterEqual(result["summary"]["fields_changed"], 1)
        self.assertGreaterEqual(result["summary"]["fields_added"], 1)
        self.assertGreaterEqual(result["summary"]["fields_removed"], 1)

    def test_non_utf8_file_fails_with_a_reason(self):
        a = write_yaml(self.tmp_path, "a.yaml", PROFILE_A)
        bad = self.tmp_path / "latin.yaml"
        bad.write_bytes("name: Sigur R\xf3s\n".encode("latin-1"))
        result = diff_profiles(a, bad)
        self.assertEqual(result["status"], "fail")
        self.assertIn("cannot be read", result["errors"][0])

    def test_directory_fails_with_a_reason(self):
        a = write_yaml(self.tmp_path, "a.yaml", PROFILE_A)
        folder = self.tmp_path / "folder.yaml"
        folder.mkdir()
        self.assertEqual(diff_profiles(a, folder)["status"], "fail")


SCRIPT = Path(__file__).parent.parent / "diff_profiles.py"


def _run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


class TestCli(TmpPathTestCase):
    """main(): the --text diff a user approves an edit from, and the exit codes."""

    def _pair(self):
        a, b = self.tmp_path / "a.yaml", self.tmp_path / "b.yaml"
        a.write_text("name: Test Band\ntier: pro  # note\n", encoding="utf-8")
        b.write_text("name: Test Band\ntier: premier  # note\n", encoding="utf-8")
        return a, b

    def test_text_shows_before_as_minus_and_after_as_plus(self):
        a, b = self._pair()
        proc = _run("--text", a, b)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("-tier: pro  # note", proc.stdout)
        self.assertIn("+tier: premier  # note", proc.stdout)
        self.assertNotIn("(no differences)", proc.stdout)

    def test_text_shows_a_comment_only_change(self):
        a, b = self._pair()
        b.write_text("name: Test Band\ntier: pro  # changed note\n", encoding="utf-8")
        out = _run("--text", a, b).stdout
        self.assertIn("-tier: pro  # note", out)
        self.assertIn("+tier: pro  # changed note", out)

    def test_text_identical_files(self):
        a, _ = self._pair()
        proc = _run("--text", a, a)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, "(no differences)"))

    def test_text_missing_file_exits_2(self):
        a, _ = self._pair()
        proc = _run("--text", a, self.tmp_path / "nope.yaml")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("nope.yaml", proc.stderr)

    def test_json_mode_exit_codes(self):
        a, b = self._pair()
        ok = _run(a, b)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual([c["field"] for c in json.loads(ok.stdout)["changed"]], ["tier"])
        missing = _run(a, self.tmp_path / "nope.yaml")
        self.assertEqual(missing.returncode, 1)
        self.assertEqual(json.loads(missing.stdout)["status"], "fail")

    def test_json_mode_survives_an_unquoted_yaml_date(self):
        a, b = self.tmp_path / "a.yaml", self.tmp_path / "b.yaml"
        a.write_text("name: X\ngeneration_history:\n- date: 2026-03-19\n", encoding="utf-8")
        b.write_text("name: X\ngeneration_history:\n- date: 2026-03-20\n", encoding="utf-8")
        proc = _run(a, b)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        changed = json.loads(proc.stdout)["changed"]
        self.assertEqual(changed[0]["field"], "generation_history")
        self.assertIn("2026-03-20", json.dumps(changed[0]["new"]))


if __name__ == "__main__":
    unittest.main()
