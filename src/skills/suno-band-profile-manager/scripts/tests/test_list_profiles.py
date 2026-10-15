#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for list-profiles.py"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_resolver import install_resolver  # noqa: E402

SCRIPT_PATH = Path(__file__).parent.parent / "list-profiles.py"

spec = spec_from_file_location(
    "list_profiles",
    SCRIPT_PATH,
)
list_profiles_mod = module_from_spec(spec)
spec.loader.exec_module(list_profiles_mod)
list_profiles = list_profiles_mod.list_profiles
check_profile = list_profiles_mod.check_profile


SAMPLE_PROFILE = {
    "name": "Test Band",
    "genre": "indie rock",
    "mood": "melancholic",
    "model_preference": "v4.5-all",
    "tier": "free",
}


class TmpPathTestCase(unittest.TestCase):
    """Gives each test a fresh temporary directory as self.tmp_path."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name).resolve()


class TestListProfiles(TmpPathTestCase):
    def test_nonexistent_directory(self):
        tmp_path = self.tmp_path
        result = list_profiles(tmp_path / "nope")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["count"], 0)
        self.assertIn("No profiles directory", result.get("message", ""))

    def test_empty_directory(self):
        tmp_path = self.tmp_path
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        result = list_profiles(profiles_dir)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["count"], 0)

    def test_single_profile(self):
        tmp_path = self.tmp_path
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        with open(profiles_dir / "test-band.yaml", "w") as f:
            yaml.dump(SAMPLE_PROFILE, f)
        result = list_profiles(profiles_dir)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["profiles"][0]["name"], "Test Band")
        self.assertEqual(result["profiles"][0]["genre"], "indie rock")

    def test_multiple_profiles(self):
        tmp_path = self.tmp_path
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        for i in range(3):
            data = {**SAMPLE_PROFILE, "name": f"Band {i}"}
            with open(profiles_dir / f"band-{i}.yaml", "w") as f:
                yaml.dump(data, f)
        result = list_profiles(profiles_dir)
        self.assertEqual(result["count"], 3)

    def test_writer_voice_detection(self):
        tmp_path = self.tmp_path
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        data_with_voice = {
            **SAMPLE_PROFILE,
            "writer_voice": {"vocabulary": "formal, archaic", "rhythm": "long flowing"}
        }
        with open(profiles_dir / "voiced.yaml", "w") as f:
            yaml.dump(data_with_voice, f)
        data_without = {**SAMPLE_PROFILE}
        with open(profiles_dir / "plain.yaml", "w") as f:
            yaml.dump(data_without, f)

        result = list_profiles(profiles_dir)
        voiced = next(p for p in result["profiles"] if p["file"] == "voiced.yaml")
        plain = next(p for p in result["profiles"] if p["file"] == "plain.yaml")
        self.assertIs(voiced["has_writer_voice"], True)
        self.assertIs(plain["has_writer_voice"], False)

    def test_invalid_yaml_skipped(self):
        tmp_path = self.tmp_path
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        (profiles_dir / "bad.yaml").write_text(": {{invalid")
        with open(profiles_dir / "good.yaml", "w") as f:
            yaml.dump(SAMPLE_PROFILE, f)
        result = list_profiles(profiles_dir)
        self.assertEqual(result["count"], 1)

    def test_new_fields_in_listing(self):
        tmp_path = self.tmp_path
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        data = {
            **SAMPLE_PROFILE,
            "instrumental": True,
            "language": "Spanish",
            "creativity_default": "experimental",
            "generation_history": [{"date": "2026-03-19"}],
        }
        with open(profiles_dir / "test.yaml", "w") as f:
            yaml.dump(data, f)
        result = list_profiles(profiles_dir)
        p = result["profiles"][0]
        self.assertIs(p["instrumental"], True)
        self.assertEqual(p["language"], "Spanish")
        self.assertEqual(p["creativity_default"], "experimental")
        self.assertIs(p["has_generation_history"], True)

    # --- check_profile tests ---
    def test_check_profile_exists(self):
        tmp_path = self.tmp_path
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        with open(profiles_dir / "test-band.yaml", "w") as f:
            yaml.dump(SAMPLE_PROFILE, f)
        result = check_profile(profiles_dir, "test-band")
        self.assertIs(result["exists"], True)
        self.assertEqual(result["name"], "Test Band")
        self.assertIn("size_bytes", result)
        self.assertIn("last_modified", result)

    def test_check_profile_exists_with_extension(self):
        tmp_path = self.tmp_path
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        with open(profiles_dir / "test-band.yaml", "w") as f:
            yaml.dump(SAMPLE_PROFILE, f)
        result = check_profile(profiles_dir, "test-band.yaml")
        self.assertIs(result["exists"], True)

    def test_check_profile_not_exists(self):
        tmp_path = self.tmp_path
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        result = check_profile(profiles_dir, "nonexistent")
        self.assertIs(result["exists"], False)
        self.assertEqual(result["query"], "nonexistent")


# --- CLI: positional vs --profiles-dir flag ---

def _run(*args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True, text=True,
    )
    return proc


class TestCli(TmpPathTestCase):
    def test_cli_positional_profiles_dir(self):
        tmp_path = self.tmp_path
        profiles_dir = tmp_path / "store"
        profiles_dir.mkdir()
        with open(profiles_dir / "test-band.yaml", "w") as f:
            yaml.dump(SAMPLE_PROFILE, f)
        proc = _run(str(profiles_dir))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["profiles_dir"], str(profiles_dir))

    def test_cli_profiles_dir_flag_overrides_positional(self):
        tmp_path = self.tmp_path
        # Positional points at an EMPTY dir; --profiles-dir points at the populated
        # one and must win.
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        with open(real_dir / "test-band.yaml", "w") as f:
            yaml.dump(SAMPLE_PROFILE, f)
        proc = _run(str(empty_dir), "--profiles-dir", str(real_dir))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["profiles_dir"], str(real_dir))

    def test_cli_profiles_dir_flag_with_check(self):
        tmp_path = self.tmp_path
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        with open(real_dir / "test-band.yaml", "w") as f:
            yaml.dump(SAMPLE_PROFILE, f)
        proc = _run("--profiles-dir", str(real_dir), "--check", "test-band")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertIs(payload["exists"], True)
        self.assertEqual(payload["name"], "Test Band")

    def test_cli_default_positional_unchanged(self):
        tmp_path = self.tmp_path
        # No args at all: default positional is docs/band-profiles (relative).
        # Run from an empty tmp cwd so the default dir doesn't exist -> count 0,
        # confirming the default derivation is untouched.
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["profiles_dir"], "docs/band-profiles")

    def test_cli_profiles_dir_from_module_config(self):
        tmp_path = self.tmp_path
        store = tmp_path / "music" / "profiles"
        store.mkdir(parents=True)
        with open(store / "test-band.yaml", "w") as f:
            yaml.dump(SAMPLE_PROFILE, f)
        (tmp_path / "_bmad").mkdir()
        (tmp_path / "_bmad" / "config.toml").write_text(
            "[core]\noutput_folder = 'out'\n[modules.suno]\nband_profiles_folder = '{project-root}/music/profiles'\n")
        install_resolver(tmp_path)
        proc = _run("--project-root", str(tmp_path))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["count"], 1)


if __name__ == "__main__":
    unittest.main()
