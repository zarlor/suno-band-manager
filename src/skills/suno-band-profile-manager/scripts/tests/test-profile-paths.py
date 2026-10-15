#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for profile_paths.py — folder resolution from module config (flags > config > defaults)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from profile_paths import read_module_config, resolve_dirs  # noqa: E402

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


def test_reads_only_the_named_section_and_substitutes_project_root(tmp_path):
    write_config(tmp_path)
    cfg = read_module_config(tmp_path)
    assert cfg["band_profiles_folder"] == "profiles"
    assert cfg["songbook_folder"] == f"{tmp_path}/book"
    assert cfg["suno_tier"] == "pro"


def test_missing_config_returns_empty(tmp_path):
    assert read_module_config(tmp_path) == {}


def test_custom_layer_overrides_and_legacy_yaml_is_ignored(tmp_path):
    write_config(tmp_path)
    (tmp_path / "_bmad" / "custom").mkdir()
    (tmp_path / "_bmad" / "custom" / "config.user.toml").write_text(
        '[modules.suno]\nsongbook_folder = "elsewhere/book"\n', encoding="utf-8")
    (tmp_path / "_bmad" / "config.yaml").write_text("suno:\n  suno_tier: free\n", encoding="utf-8")
    cfg = read_module_config(tmp_path)
    assert cfg["songbook_folder"] == "elsewhere/book"
    assert cfg["suno_tier"] == "pro"
    assert resolve_dirs(tmp_path)["songbook_dir"] == tmp_path / "elsewhere" / "book"


def test_config_wins_over_defaults(tmp_path):
    write_config(tmp_path)
    dirs = resolve_dirs(tmp_path)
    assert dirs["profiles_dir"] == tmp_path / "profiles"
    assert dirs["docs_dir"] == tmp_path
    assert dirs["songbook_dir"] == tmp_path / "book"


def test_flags_win_over_config(tmp_path):
    write_config(tmp_path)
    dirs = resolve_dirs(tmp_path, profiles_dir=tmp_path / "p", docs_dir=tmp_path / "d", songbook_dir=tmp_path / "s")
    assert dirs == {"profiles_dir": tmp_path / "p", "docs_dir": tmp_path / "d", "songbook_dir": tmp_path / "s"}


def test_defaults_without_config(tmp_path):
    dirs = resolve_dirs(tmp_path)
    assert dirs["profiles_dir"] == tmp_path / "docs" / "band-profiles"
    assert dirs["docs_dir"] == tmp_path / "docs"
    assert dirs["songbook_dir"] == tmp_path / "docs" / "songbook"
