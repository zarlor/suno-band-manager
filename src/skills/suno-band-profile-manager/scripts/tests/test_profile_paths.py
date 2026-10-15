#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for profile_paths.py — folder resolution from module config (flags > config > defaults)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from profile_paths import derive_slug, read_module_config, resolve_dirs  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_resolver import install_resolver  # noqa: E402

CONFIG = """[core]
output_folder = "{project-root}/_bmad-output"
band_profiles_folder = "/wrong"

[modules.suno]
band_profiles_folder = "profiles" # inline comment
songbook_folder = "{project-root}/book"
suno_tier = "pro"

[modules.other]
band_profiles_folder = "/wrong"
"""


def write_config(root: Path, text: str = CONFIG) -> None:
    (root / "_bmad").mkdir()
    (root / "_bmad" / "config.toml").write_text(text, encoding="utf-8")
    install_resolver(root)


class TmpPathTestCase(unittest.TestCase):
    """Gives each test a fresh temporary directory as self.tmp_path."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name).resolve()


class TestDeriveSlug(unittest.TestCase):
    def test_the_one_name_to_slug_rule(self):
        cases = {
            "Test Band": "test-band",
            "Rosa's Voice": "rosas-voice",
            "Ember Hollow - Redux": "ember-hollow-redux",
            "  My   Cool  Band  ": "my-cool-band",
            "already-kebab": "already-kebab",
            "Rider's Hymn!": "riders-hymn",
            "!!!": "",
        }
        for name, slug in cases.items():
            self.assertEqual(derive_slug(name), slug, name)


class TestProfilePaths(TmpPathTestCase):
    def test_reads_only_the_named_section_and_substitutes_project_root(self):
        tmp_path = self.tmp_path
        write_config(tmp_path)
        cfg = read_module_config(tmp_path)
        self.assertEqual(cfg["band_profiles_folder"], "profiles")
        self.assertEqual(cfg["songbook_folder"], f"{tmp_path}/book")
        self.assertEqual(cfg["suno_tier"], "pro")

    def test_missing_config_returns_empty(self):
        tmp_path = self.tmp_path
        self.assertEqual(read_module_config(tmp_path), {})

    def test_custom_layer_overrides_and_legacy_yaml_is_ignored(self):
        tmp_path = self.tmp_path
        write_config(tmp_path)
        (tmp_path / "_bmad" / "custom").mkdir()
        (tmp_path / "_bmad" / "custom" / "config.user.toml").write_text(
            '[modules.suno]\nsongbook_folder = "elsewhere/book"\n', encoding="utf-8")
        (tmp_path / "_bmad" / "config.yaml").write_text("suno:\n  suno_tier: free\n", encoding="utf-8")
        cfg = read_module_config(tmp_path)
        self.assertEqual(cfg["songbook_folder"], "elsewhere/book")
        self.assertEqual(cfg["suno_tier"], "pro")
        self.assertEqual(resolve_dirs(tmp_path)["songbook_dir"], tmp_path / "elsewhere" / "book")

    def test_config_wins_over_defaults(self):
        tmp_path = self.tmp_path
        write_config(tmp_path)
        dirs = resolve_dirs(tmp_path)
        self.assertEqual(dirs["profiles_dir"], tmp_path / "profiles")
        self.assertEqual(dirs["docs_dir"], tmp_path)
        self.assertEqual(dirs["songbook_dir"], tmp_path / "book")

    def test_flags_win_over_config(self):
        tmp_path = self.tmp_path
        write_config(tmp_path)
        dirs = resolve_dirs(tmp_path, profiles_dir=tmp_path / "p", docs_dir=tmp_path / "d", songbook_dir=tmp_path / "s")
        self.assertEqual(dirs, {"profiles_dir": tmp_path / "p", "docs_dir": tmp_path / "d", "songbook_dir": tmp_path / "s"})

    def test_defaults_without_config(self):
        tmp_path = self.tmp_path
        dirs = resolve_dirs(tmp_path)
        self.assertEqual(dirs["profiles_dir"], tmp_path / "docs" / "band-profiles")
        self.assertEqual(dirs["docs_dir"], tmp_path / "docs")
        self.assertEqual(dirs["songbook_dir"], tmp_path / "docs" / "songbook")


if __name__ == "__main__":
    unittest.main()
