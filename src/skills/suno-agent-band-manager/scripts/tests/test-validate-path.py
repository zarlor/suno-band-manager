#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
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


def test_parse_legacy_access_boundaries(tmp_path):
    """A legacy standalone access-boundaries.md (top-level ## sections) still parses."""
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
    assert ok("/proj/_bmad/memory/suno-agent-band-manager/memory/work/current.md", "write")
    assert not ok("/proj/_bmad/_memory/band-manager-sidecar/MEMORY.md", "write")  # the legacy store
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


# --- v7: the Dominion inside the sanctum's CREED.md ---


def test_parse_creed_dominion_subsections(v7_project):
    root, sanctum = v7_project
    b = mod.parse_boundaries(sanctum / "CREED.md")
    assert b["read"] == ["_bmad/memory/suno-agent-band-manager/", "docs/band-profiles/"]
    assert b["write"] == ["_bmad/memory/suno-agent-band-manager/", "docs/wip-*.md"]
    assert b["deny"] == ["src/"]
    # Write Rule prose and the sections outside the Dominion are not rules.
    everything = b["read"] + b["write"] + b["deny"]
    assert "docs/not-a-rule.md" not in everything
    assert "docs/also-not-a-rule.md" not in everything


def test_creed_dominion_decisions(v7_project):
    root, sanctum = v7_project
    b = mod.parse_boundaries(sanctum / "CREED.md")
    ok = lambda p, op: mod.validate_path(p, op, b, project_root=str(root))["allowed"]
    assert ok(str(sanctum / "memory" / "work" / "current.md"), "write")
    assert ok("docs/wip-dock.md", "write")
    assert ok("docs/band-profiles/x.yaml", "read")
    assert not ok("docs/band-profiles/x.yaml", "write")
    assert not ok("src/skills/x.py", "write")
    assert not ok("docs/not-a-rule.md", "write")


def test_scaffolded_creed_carries_the_template_dominion(tmp_path):
    """init-sanctum renders the access-boundaries template into CREED.md; it parses
    the same as the template itself."""
    init_spec = spec_from_file_location("init_sanctum", Path(__file__).parent.parent / "init-sanctum.py")
    init = module_from_spec(init_spec)
    init_spec.loader.exec_module(init)
    init.scaffold(tmp_path, Path(__file__).parent.parent.parent)
    creed = tmp_path / "_bmad" / "memory" / "suno-agent-band-manager" / "CREED.md"
    from_creed = mod.parse_boundaries(creed)
    template_text = TEMPLATE.read_text(encoding="utf-8").replace("{project-root}", str(tmp_path))
    legacy = tmp_path / "access-boundaries.md"
    legacy.write_text(template_text, encoding="utf-8")
    from_template = mod.parse_boundaries(legacy)
    assert from_creed == from_template
    assert "docs/wip-*.md" in from_creed["write"]


def _cli(monkeypatch, capsys, *argv):
    import json
    monkeypatch.setattr(sys, "argv", ["validate-path.py", *argv])
    code = 0
    try:
        mod.main()
    except SystemExit as exc:
        code = exc.code or 0
    return code, json.loads(capsys.readouterr().out)


def test_cli_defaults_to_the_sanctum_creed(v7_project, monkeypatch, capsys):
    root, _ = v7_project
    code, out = _cli(monkeypatch, capsys, "docs/wip-dock.md", "write", "--project-root", str(root))
    assert code == 0 and out["allowed"] is True
    code, out = _cli(monkeypatch, capsys, "src/x.py", "write", "--project-root", str(root))
    assert code == 1 and out["reason"] == "deny zone"


def test_cli_explicit_boundaries_and_missing_file(v7_project, monkeypatch, capsys):
    root, sanctum = v7_project
    code, out = _cli(monkeypatch, capsys, "docs/band-profiles/a.yaml", "read",
                     "--boundaries", str(sanctum / "CREED.md"), "--project-root", str(root))
    assert code == 0 and out["allowed"] is True
    code, out = _cli(monkeypatch, capsys, "docs/a.md", "read", "--project-root", str(root / "nowhere"))
    assert code == 1 and out["error"] is True and "CREED.md" in out["message"]


def test_labeled_bullet_names_its_path_in_parentheses(tmp_path):
    creed = tmp_path / "CREED.md"
    creed.write_text(
        "# Creed\n\n## Dominion (Access Boundaries)\n\n### Write Access\n\n"
        "- WIP files (`docs/wip-*.md`) when capturing creative fragments\n"
        "- Band profile writes happen via the `suno-band-profile-manager` skill, not directly\n"
        "  - nested note (`docs/nested-not-a-rule.md`) stays prose\n"
        "- Plain prose (e.g. `docs/inline-not-a-rule.md`) mid-sentence\n",
        encoding="utf-8")
    b = mod.parse_boundaries(creed)
    assert b["write"] == ["docs/wip-*.md"]
