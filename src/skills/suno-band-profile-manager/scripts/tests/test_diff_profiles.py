#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for diff-profiles.py"""

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location(
    "diff_profiles",
    Path(__file__).parent.parent / "diff-profiles.py"
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


if __name__ == "__main__":
    unittest.main()
