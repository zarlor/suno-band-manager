#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Tests for songbook-catalog.py (fixtures are invented, de-identified)."""

import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))
spec = spec_from_file_location("songbook_catalog", SCRIPTS_DIR / "songbook-catalog.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

TABLE_SONG = (
    '---\ntitle: "Harbor Lights"\nband_profile: paper-lanterns\nstatus: published\n'
    "date: 2026-01-15\nsource_wip: docs/wip-dock.md\n---\n\n# Harbor Lights\n\n"
    "## Style Prompt (v6)\n\n```\nwarm indie folk, fingerpicked nylon guitar, brushed drums, close vocal\n```\n\n"
    "## Settings\n\n| Setting | Value |\n|---|---|\n| Model | v6 |\n| Weirdness | 45% |\n"
    "| Style Influence | 70 |\n\n## Generation Log\n\n**Status: PUBLISHED — Published 2026-01-15.**\n"
)
BULLET_SONG = (
    '---\ntitle: "Tin Roof"\nband_profile: paper-lanterns\nstatus: wip\ndate: 2025-12-01\n---\n\n'
    "## Style Prompt\n\n```\nswamp blues\n```\n\n## Settings\n\n"
    "- Model: v6-mini · Vocal Gender: Female\n- Weirdness **45** · Style Influence **60**\n"
)
OTHER_BAND = (
    '---\ntitle: "Iron Gate"\nband_profile: iron-band\nstatus: published\ndate: 2026-02-01\n---\n\n'
    "## Settings\n- Model: v6\n\n**Status: PUBLISHED — Published 2026-02-01.**\n"
)


def _project(tmp_path):
    for rel, text in (
        ("docs/songbook/paper-lanterns/harbor-lights.md", TABLE_SONG),
        ("docs/songbook/paper-lanterns/tin-roof.md", BULLET_SONG),
        ("docs/songbook/iron-band/iron-gate.md", OTHER_BAND),
    ):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


def test_extract_settings_table_and_bullets():
    assert mod.extract_settings(TABLE_SONG) == {"Model": "v6", "Weirdness": "45%", "Style Influence": "70"}
    assert mod.extract_settings(BULLET_SONG) == {
        "Model": "v6-mini", "Vocal Gender": "Female", "Weirdness": "45", "Style Influence": "60"}


def test_catalog_fields_and_tallies(tmp_path):
    report = mod.build_catalog(_project(tmp_path), band="paper-lanterns")
    assert report["song_count"] == 2
    harbor = next(s for s in report["songs"] if s["title"] == "Harbor Lights")
    assert harbor["status"] == "published" and harbor["published"] == "2026-01-15"
    assert harbor["model"] == "v6" and harbor["source_wip"] == "docs/wip-dock.md"
    assert harbor["style_prompt"].startswith("warm indie folk")
    band = report["bands"]["paper-lanterns"]
    assert band == {"songs": 2, "published": 1, "models": {"v6": 1, "v6-mini": 1},
                    "sliders": {"Weirdness": {"45": 2}, "Style Influence": {"70": 1, "60": 1}}}


def test_preview_vs_full_prompt(tmp_path):
    root = _project(tmp_path)
    long_prompt = "x" * 300
    p = root / "docs/songbook/paper-lanterns/tin-roof.md"
    p.write_text(BULLET_SONG.replace("swamp blues", long_prompt), encoding="utf-8")
    short = mod.build_catalog(root, title="tin")["songs"][0]
    assert len(short["style_prompt"]) == mod.PREVIEW_CHARS and short["style_prompt_chars"] == 300
    full = mod.build_catalog(root, title="tin", full_prompts=True)["songs"][0]
    assert full["style_prompt"] == long_prompt


def test_filters(tmp_path):
    root = _project(tmp_path)
    assert [s["title"] for s in mod.build_catalog(root, status="published")["songs"]] == [
        "Iron Gate", "Harbor Lights"]
    assert [s["title"] for s in mod.build_catalog(root, model="mini")["songs"]] == ["Tin Roof"]
    assert [s["title"] for s in mod.build_catalog(root, since="2026-01-20")["songs"]] == ["Iron Gate"]
    assert [s["title"] for s in mod.build_catalog(root, title="HARBOR")["songs"]] == ["Harbor Lights"]
    assert [s["title"] for s in mod.build_catalog(root, status="wip")["songs"]] == ["Tin Roof"]


def test_empty_project(tmp_path):
    report = mod.build_catalog(tmp_path)
    assert report["song_count"] == 0 and report["songs"] == []


def test_cli_json_and_text(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path)
    monkeypatch.setattr(sys, "argv", ["songbook-catalog.py", str(root), "--band", "iron-band"])
    assert mod.main() == 0
    assert json.loads(capsys.readouterr().out)["song_count"] == 1
    monkeypatch.setattr(sys, "argv", ["songbook-catalog.py", str(root), "--format", "text"])
    assert mod.main() == 0
    assert "Harbor Lights" in capsys.readouterr().out
