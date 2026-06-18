#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for _sanctum_seed.py — the shared seeding logic.

This is the single source of the creed-sharding + access-boundaries seeding that
BOTH init-sanctum.py and migrate-sidecar-to-v2.py depend on, so it is tested
directly here.
"""

import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

spec = spec_from_file_location("_sanctum_seed", SCRIPTS_DIR / "_sanctum_seed.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

ASSETS = SKILL_DIR / "assets"
REFERENCES = SKILL_DIR / "references"


def test_shard_routing_covers_three_shards_plus_incident_log():
    creed_text = (REFERENCES / "creed.md").read_text(encoding="utf-8")
    shards = mod.shard_creed(creed_text)
    # Every routed shard + the incident log.
    assert "creed-disciplines.md" in shards
    assert "creed-workshop-capture.md" in shards
    assert "creed-package-assembly.md" in shards
    assert "creed-incident-log.md" in shards
    for name, text in shards.items():
        assert text.strip(), f"empty shard: {name}"


def test_shard_creed_lifts_package_assembly_rule():
    creed_text = (REFERENCES / "creed.md").read_text(encoding="utf-8")
    shards = mod.shard_creed(creed_text)
    assert "Package Assembly Rule" in shards["creed-package-assembly.md"]


def test_render_access_boundaries_substitutes_project_root():
    body = mod.render_access_boundaries(ASSETS, {"project_root": "/tmp/proj"})
    assert body is not None
    assert "Access Boundaries for Mac" in body
    assert "{project_root}" not in body
    assert "/tmp/proj" in body


def test_render_access_boundaries_missing_template_returns_none(tmp_path):
    assert mod.render_access_boundaries(tmp_path, {"project_root": "x"}) is None


def test_write_access_boundaries_writes_file(tmp_path):
    name = mod.write_access_boundaries(tmp_path, ASSETS, {"project_root": str(tmp_path)})
    assert name == "access-boundaries.md"
    written = (tmp_path / "access-boundaries.md").read_text(encoding="utf-8")
    assert "Deny Zones" in written


def test_write_creed_shards_writes_all(tmp_path):
    written = mod.write_creed_shards(tmp_path, REFERENCES)
    assert "creed-disciplines.md" in written
    assert "creed-package-assembly.md" in written
    assert "creed-incident-log.md" in written
    for name in written:
        assert (tmp_path / name).read_text(encoding="utf-8").strip()


def test_write_creed_shards_missing_creed_returns_empty(tmp_path):
    assert mod.write_creed_shards(tmp_path, tmp_path) == []


def test_cli_seeds_into_out_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv",
        [
            "_sanctum_seed.py",
            "--out", str(tmp_path),
            "--skill-path", str(SKILL_DIR),
            "--project-root", str(tmp_path),
            "--format", "json",
        ],
    )
    rc = mod.main()
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "seeded"
    assert "access-boundaries.md" in out["written"]
    assert "creed-package-assembly.md" in out["written"]
    assert (tmp_path / "access-boundaries.md").exists()
