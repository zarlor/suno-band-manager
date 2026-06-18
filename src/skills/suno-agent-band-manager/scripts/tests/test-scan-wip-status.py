#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Tests for scan-wip-status.py — WIP COMPLETED-marker scan + songbook correlation."""

import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

spec = spec_from_file_location("scan_wip_status", SCRIPTS_DIR / "scan-wip-status.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


PUBLISHED_SONG = (
    "---\n"
    'title: "The Slide"\n'
    "band_profile: lennys-voice\n"
    "status: published\n"
    "date: 2026-06-10\n"
    "---\n"
    "**Status: PUBLISHED — Published 2026-06-10.**\n"
)

COMPLETED_WIP = (
    "# The Slide\n"
    "## WIP — 2026-05-01\n\n"
    "---\n\n"
    '## STATUS: COMPLETED as "The Slide" — published 2026-06-10\n\n'
    "Preserved as historical record. See the songbook entry at\n"
    "`docs/songbook/lennys-voice/the-slide.md` for the finished form.\n\n"
    "**This WIP file is NOT active work — do not list it in pending/parked work.**\n\n"
    "---\n\n"
    "old fragments...\n"
)


def _project(tmp_path):
    (tmp_path / "docs").mkdir()
    return tmp_path


def test_no_docs_dir_returns_empty(tmp_path):
    report = mod.build_report(tmp_path)
    assert report["wip_count"] == 0
    assert report["files"] == []


def test_completed_marker_parsed(tmp_path):
    proj = _project(tmp_path)
    (proj / "docs" / "wip-the-slide-fragments.md").write_text(COMPLETED_WIP)
    report = mod.build_report(proj)
    assert report["wip_count"] == 1
    f = report["files"][0]
    assert f["status"] == "completed"
    assert f["completed_as"] == "The Slide"
    assert f["published_date"] == "2026-06-10"
    assert f["songbook_ref"] == "docs/songbook/lennys-voice/the-slide.md"
    assert f["correlation_warning"] is None


def test_active_wip_no_collision_no_warning(tmp_path):
    proj = _project(tmp_path)
    (proj / "docs" / "wip-brand-new-idea.md").write_text(
        "# Brand New Idea\n## WIP — 2026-06-16\n\na fresh concept\n"
    )
    report = mod.build_report(proj)
    f = report["files"][0]
    assert f["status"] == "active"
    assert f["correlation_warning"] is None


def test_active_wip_collides_with_published_warns(tmp_path):
    proj = _project(tmp_path)
    sb = proj / "docs" / "songbook" / "lennys-voice"
    sb.mkdir(parents=True)
    (sb / "the-slide.md").write_text(PUBLISHED_SONG)
    # Active WIP whose working title matches the published song (v2 suffix stripped).
    (proj / "docs" / "wip-the-slide-v2-fragments.md").write_text(
        "# The Slide v2\n## WIP — 2026-06-15\n\nsequel lines\n"
    )
    report = mod.build_report(proj)
    f = report["files"][0]
    assert f["status"] == "active"
    assert f["correlation_warning"] is not None
    assert "The Slide v2" in f["correlation_warning"]
    assert f["songbook_ref"] == "docs/songbook/lennys-voice/the-slide.md"
    assert report["correlation_warnings"] == 1


def test_mixed_set_counts(tmp_path):
    proj = _project(tmp_path)
    sb = proj / "docs" / "songbook" / "lennys-voice"
    sb.mkdir(parents=True)
    (sb / "the-slide.md").write_text(PUBLISHED_SONG)
    (proj / "docs" / "wip-the-slide-fragments.md").write_text(COMPLETED_WIP)
    (proj / "docs" / "wip-the-slide-v2-fragments.md").write_text(
        "# The Slide v2\n\nsequel\n"
    )
    (proj / "docs" / "wip-unrelated.md").write_text("# Unrelated\n\nstuff\n")
    report = mod.build_report(proj)
    assert report["wip_count"] == 3
    assert report["completed"] == 1
    assert report["active"] == 2
    assert report["correlation_warnings"] == 1


def test_unpublished_song_does_not_trigger_warning(tmp_path):
    """A WIP matching a NON-published songbook entry must not warn (nothing to mark)."""
    proj = _project(tmp_path)
    sb = proj / "docs" / "songbook" / "lennys-voice"
    sb.mkdir(parents=True)
    (sb / "the-slide.md").write_text(
        "---\n"
        'title: "The Slide"\n'
        "band_profile: lennys-voice\n"
        "status: wip\n"
        "---\n"
        "**Status: WIP.**\n"
    )
    (proj / "docs" / "wip-the-slide-fragments.md").write_text(
        "# The Slide\n\nfragments\n"
    )
    report = mod.build_report(proj)
    f = report["files"][0]
    assert f["status"] == "active"
    assert f["correlation_warning"] is None


def test_main_json_output(tmp_path, monkeypatch, capsys):
    proj = _project(tmp_path)
    (proj / "docs" / "wip-x.md").write_text("# X\n\nstuff\n")
    monkeypatch.setattr(sys, "argv", ["scan-wip-status.py", str(proj), "--format", "json"])
    rc = mod.main()
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    assert out["wip_count"] == 1


def test_marker_without_quotes_or_date_still_completed(tmp_path):
    """A slightly-off marker (no quoted title / no date) still flips status."""
    proj = _project(tmp_path)
    (proj / "docs" / "wip-loose.md").write_text(
        "# Loose\n\n## STATUS: COMPLETED — folded into the album\n\nfragments\n"
    )
    report = mod.build_report(proj)
    f = report["files"][0]
    assert f["status"] == "completed"
    assert f["completed_as"] is None
    assert f["published_date"] is None
