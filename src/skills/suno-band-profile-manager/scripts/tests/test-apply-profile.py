#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Tests for apply-profile.py"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location(
    "apply_profile",
    Path(__file__).parent.parent / "apply-profile.py"
)
apply_mod = module_from_spec(spec)
spec.loader.exec_module(apply_mod)

_derive_slug = apply_mod._derive_slug
_set_nested = apply_mod._set_nested
_flatten = apply_mod._flatten
_write_yaml = apply_mod._write_yaml
_read_yaml = apply_mod._read_yaml
_resolve_profiles_dir = apply_mod._resolve_profiles_dir
cmd_set = apply_mod.cmd_set
cmd_duplicate = apply_mod.cmd_duplicate


SAMPLE = {
    "name": "Test Band",
    "genre": "indie rock",
    "tier": "free",
    "version": 1,
    "vocal": {"gender": "male", "tone": "warm"},
}


class Args:
    """Lightweight argparse.Namespace stand-in."""
    def __init__(self, **kw):
        self.slug = None
        self.profiles_dir = None
        self.project_root = "."
        self.input = None
        self.set_json = None
        self.duplicate = None
        self.bump_version = False
        self.force = False
        for k, v in kw.items():
            setattr(self, k, v)


# --- pure helpers ---

def test_derive_slug():
    assert _derive_slug("Test Band") == "test-band"
    assert _derive_slug("Rider's Hymn!") == "riders-hymn"
    assert _derive_slug("  Multiple   Spaces ") == "multiple-spaces"


def test_set_nested_changes():
    d = {"vocal": {"tone": "warm"}}
    assert _set_nested(d, "vocal.tone", "bright") is True
    assert d["vocal"]["tone"] == "bright"
    # no-op set returns False
    assert _set_nested(d, "vocal.tone", "bright") is False


def test_set_nested_creates_path():
    d = {}
    assert _set_nested(d, "sliders.weirdness", 65) is True
    assert d["sliders"]["weirdness"] == 65


def test_flatten():
    flat = _flatten({"a": 1, "b": {"c": 2, "d": {"e": 3}}})
    assert flat == {"a": 1, "b.c": 2, "b.d.e": 3}


# --- profiles-dir resolution ---

def test_resolve_profiles_dir_default():
    # No --profiles-dir: default to {project-root}/docs/band-profiles — unchanged.
    args = Args(project_root="/proj")
    assert _resolve_profiles_dir(args) == Path("/proj") / "docs" / "band-profiles"


def test_resolve_profiles_dir_override():
    # --profiles-dir wins when provided.
    args = Args(project_root="/proj", profiles_dir="/custom/store")
    assert _resolve_profiles_dir(args) == Path("/custom/store")


# --- cmd_set ---

def test_cmd_set_merges_fields(tmp_path):
    _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
    args = Args(slug="test-band", profiles_dir=str(tmp_path),
                set_json='{"tier": "pro", "vocal": {"tone": "bright"}}')
    result = cmd_set(args)
    assert result["status"] == "complete"
    assert set(result["fields_changed"]) == {"tier", "vocal.tone"}
    saved = _read_yaml(tmp_path / "test-band.yaml")
    assert saved["tier"] == "pro"
    assert saved["vocal"]["tone"] == "bright"
    # untouched fields survive
    assert saved["vocal"]["gender"] == "male"
    assert saved["genre"] == "indie rock"


def test_cmd_set_missing_profile(tmp_path):
    args = Args(slug="nope", profiles_dir=str(tmp_path), set_json='{"tier": "pro"}')
    result = cmd_set(args)
    assert result["status"] == "fail"
    assert "not found" in result["error"].lower()


def test_cmd_set_no_change(tmp_path):
    _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
    args = Args(slug="test-band", profiles_dir=str(tmp_path), set_json='{"tier": "free"}')
    result = cmd_set(args)
    assert result["status"] == "complete"
    assert result["fields_changed"] == []


# --- cmd_duplicate ---

def test_cmd_duplicate(tmp_path):
    _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
    args = Args(slug="test-band", profiles_dir=str(tmp_path), duplicate="Test Band V2")
    result = cmd_duplicate(args)
    assert result["status"] == "complete"
    assert result["slug"] == "test-band-v2"
    assert (tmp_path / "test-band-v2.yaml").exists()
    saved = _read_yaml(tmp_path / "test-band-v2.yaml")
    assert saved["name"] == "Test Band"
    assert saved["version"] == 1  # not bumped by default


def test_cmd_duplicate_bump_version(tmp_path):
    _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
    args = Args(slug="test-band", profiles_dir=str(tmp_path),
                duplicate="Test Band V2", bump_version=True)
    result = cmd_duplicate(args)
    saved = _read_yaml(tmp_path / "test-band-v2.yaml")
    assert saved["version"] == 2


def test_cmd_duplicate_existing_no_force(tmp_path):
    _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
    _write_yaml(tmp_path / "test-band-v2.yaml", dict(SAMPLE))
    args = Args(slug="test-band", profiles_dir=str(tmp_path), duplicate="Test Band V2")
    result = cmd_duplicate(args)
    assert result["status"] == "fail"
    assert "already exists" in result["error"].lower()


def test_cmd_duplicate_missing_source(tmp_path):
    args = Args(slug="nope", profiles_dir=str(tmp_path), duplicate="New Name")
    result = cmd_duplicate(args)
    assert result["status"] == "fail"
    assert "not found" in result["error"].lower()
