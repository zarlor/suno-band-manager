#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for validate-path.py"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location(
    "validate_path",
    Path(__file__).parent.parent / "validate-path.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def test_parse_boundaries(tmp_path):
    """Parse access-boundaries.md correctly."""
    boundaries_file = tmp_path / "access-boundaries.md"
    boundaries_file.write_text(
        "# Access Boundaries\n\n"
        "## Read Access\n"
        "- docs/band-profiles/\n"
        "- {project-root}/_bmad/_memory/band-manager-sidecar/\n\n"
        "## Write Access\n"
        "- {project-root}/_bmad/_memory/band-manager-sidecar/\n\n"
        "## Deny Zones\n"
        "- All other directories\n"
    )

    boundaries = mod.parse_boundaries(boundaries_file)
    assert "docs/band-profiles/" in boundaries["read"]
    assert "_bmad/_memory/band-manager-sidecar/" in boundaries["read"]
    assert "_bmad/_memory/band-manager-sidecar/" in boundaries["write"]


def test_validate_read_allowed(tmp_path):
    boundaries = {"read": ["docs/band-profiles/"], "write": []}
    result = mod.validate_path("docs/band-profiles/midnight-orchid.yaml", "read", boundaries)
    assert result["allowed"] is True


def test_validate_read_denied(tmp_path):
    boundaries = {"read": ["docs/band-profiles/"], "write": []}
    result = mod.validate_path("src/secret.py", "read", boundaries)
    assert result["allowed"] is False


def test_validate_write_allowed(tmp_path):
    boundaries = {"read": [], "write": ["_bmad/_memory/band-manager-sidecar/"]}
    result = mod.validate_path("_bmad/_memory/band-manager-sidecar/index.md", "write", boundaries)
    assert result["allowed"] is True


def test_validate_write_denied(tmp_path):
    boundaries = {"read": [], "write": ["_bmad/_memory/band-manager-sidecar/"]}
    result = mod.validate_path("docs/band-profiles/test.yaml", "write", boundaries)
    assert result["allowed"] is False


TEMPLATE = Path(__file__).parent.parent.parent / "assets" / "ACCESS-BOUNDARIES-template.md"


def _template_boundaries(tmp_path):
    text = TEMPLATE.read_text(encoding="utf-8").replace("{project-root}", "/proj")
    path = tmp_path / "access-boundaries.md"
    path.write_text(text)
    return mod.parse_boundaries(path)


def test_template_parses_backticked_entries(tmp_path):
    b = _template_boundaries(tmp_path)
    assert "docs/wip-*.md" in b["write"]
    assert "{skill-root}/" in b["read"]
    assert "src/" in b["deny"]
    # Prose bullets are not treated as paths.
    assert not any(" " in p for p in b["read"] + b["write"] + b["deny"])


def test_template_write_rules(tmp_path):
    b = _template_boundaries(tmp_path)
    ok = lambda p, op: mod.validate_path(p, op, b, project_root="/proj", skill_root="/proj/src/skills/mac")["allowed"]
    assert ok("/proj/_bmad/_memory/band-manager-sidecar/MEMORY.md", "write")
    assert ok("docs/wip-new-song-fragments.md", "write")
    assert ok("docs/voice-context-sam.md", "write")
    assert not ok("docs/band-profiles/x.yaml", "write")      # via the profile skill only
    assert not ok("src/skills/mac/references/creed.md", "write")  # deny zone
    assert not ok("/proj/_bmad/config.yaml", "write")
    assert not ok("README.md", "write")


def test_template_bundle_carve_out_allows_reads(tmp_path):
    b = _template_boundaries(tmp_path)
    ok = lambda p, op: mod.validate_path(p, op, b, project_root="/proj", skill_root="/proj/src/skills/mac")["allowed"]
    # src/ is a deny zone for writes, but the skill's own bundle is readable.
    assert ok("src/skills/mac/references/create-song.md", "read")
    assert not ok("src/other/thing.py", "read")
    assert ok("docs/band-profiles/x.yaml", "read")
