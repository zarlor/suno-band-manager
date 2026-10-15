#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for find-stale-refs.py (fixtures are invented, de-identified)."""

import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent
spec = spec_from_file_location("find_stale_refs", SCRIPTS_DIR / "find-stale-refs.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def _w(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


SANCTUM = "_bmad/memory/suno-agent-band-manager"


def _project(tmp_path):
    _w(tmp_path, "docs/songbook/paper-lanterns/harbor-lights.md",
       '---\ntitle: "Harbor Lights"\n---\n# Harbor Lights\nsee `docs/wip-dock.md`\n')
    _w(tmp_path, "docs/paper-lanterns-playlist.yaml",
       'tracks:\n  - name: "harbor lights"\n    file: a.mp3\n')
    _w(tmp_path, "docs/voice-context-owner.md",
       "# V\n\n## Companion Files\n\n| File | What |\n|---|---|\n"
       "| `docs/notes/extra.md` | extra |\n\n## Catalog\n\nHarbor Lights (Night Mix) is the opener.\n")
    _w(tmp_path, "docs/notes/extra.md", "Harbor Lights again\n")
    _w(tmp_path, "docs/unrelated.md", "Harbor Lights here is out of scope\n")
    _w(tmp_path, f"{SANCTUM}/memory/work/current.md", "- **Harbor Lights** in progress\n")
    _w(tmp_path, f"{SANCTUM}/memory/catalog/recently-published.md", "- **Harbor Lights** published\n")
    _w(tmp_path, f"{SANCTUM}/memory/chronology/2026-01-01-first-light.md", "Harbor Lights milestone\n")
    _w(tmp_path, f"{SANCTUM}/memory/sessions/2026-01-02-note.md", "Harbor Lights note\n")
    _w(tmp_path, f"{SANCTUM}/raw/2026-01-01-session-log.md", "Harbor Lights log\n")
    _w(tmp_path, f"{SANCTUM}/raw/2026-01-01-collection-of-writings-extracted.txt", "Harbor Lights poem\n")
    # A legacy store is not searched.
    _w(tmp_path, "_bmad/_memory/band-manager-sidecar/MEMORY.md", "- **Harbor Lights** old\n")
    return tmp_path


def test_hits_cover_the_defined_set_only(tmp_path):
    report = mod.scan(_project(tmp_path), "Harbor Lights")
    files = {h["file"] for h in report["hits"]}
    assert "docs/songbook/paper-lanterns/harbor-lights.md" in files
    assert "docs/paper-lanterns-playlist.yaml" in files  # casefold hit
    assert "docs/notes/extra.md" in files  # via the Companion Files table
    assert f"{SANCTUM}/memory/work/current.md" in files
    assert f"{SANCTUM}/memory/catalog/recently-published.md" in files
    assert f"{SANCTUM}/memory/chronology/2026-01-01-first-light.md" in files
    assert f"{SANCTUM}/memory/sessions/2026-01-02-note.md" in files
    assert "docs/unrelated.md" not in files
    assert not any("/raw/" in f for f in files)
    assert not any("_bmad/_memory" in f for f in files)


def test_match_kinds(tmp_path):
    report = mod.scan(_project(tmp_path), "Harbor Lights")
    kinds = {(h["file"], h["match_kind"]) for h in report["hits"]}
    assert ("docs/paper-lanterns-playlist.yaml", "casefold") in kinds
    assert ("docs/songbook/paper-lanterns/harbor-lights.md", "exact") in kinds


def test_subtitle_match_when_old_has_one(tmp_path):
    report = mod.scan(_project(tmp_path), "Harbor Lights (Night Mix)")
    kinds = {h["match_kind"] for h in report["hits"]}
    assert "exact" in kinds and "subtitle" in kinds


def test_partial_only_on_request(tmp_path):
    root = _project(tmp_path)
    _w(root, "docs/wip-dock.md", "# Dock\nharbor at dusk\n")
    assert not any(h["match_kind"] == "partial" for h in mod.scan(root, "Harbor Lights")["hits"])
    partial = [h for h in mod.scan(root, "Harbor Lights", partial=True)["hits"]
               if h["match_kind"] == "partial"]
    assert [h["file"] for h in partial] == ["docs/wip-dock.md"]


def test_raw_included_on_request(tmp_path):
    report = mod.scan(_project(tmp_path), "Harbor Lights", include_raw=True)
    files = {h["file"] for h in report["hits"]}
    assert f"{SANCTUM}/raw/2026-01-01-session-log.md" in files
    assert f"{SANCTUM}/raw/2026-01-01-collection-of-writings-extracted.txt" in files
    assert report["raw_included"] is True


def test_cli_include_sessions_is_an_alias_for_include_raw(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path)
    for flag in ("--include-raw", "--include-sessions"):
        monkeypatch.setattr(sys, "argv", ["find-stale-refs.py", str(root), "--old", "Harbor Lights", flag])
        assert mod.main() == 0
        out = json.loads(capsys.readouterr().out)
        assert any("/raw/" in h["file"] for h in out["hits"])


def test_cli_sanctum_dir_override(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path)
    _w(root, "staging/memory/work/current.md", "Harbor Lights staged\n")
    monkeypatch.setattr(sys, "argv", [
        "find-stale-refs.py", str(root), "--old", "Harbor Lights", "--sanctum-dir", str(root / "staging")])
    assert mod.main() == 0
    files = {h["file"] for h in json.loads(capsys.readouterr().out)["hits"]}
    assert "staging/memory/work/current.md" in files
    assert not any(f.startswith(SANCTUM) for f in files)


def test_new_value_adds_preview(tmp_path):
    report = mod.scan(_project(tmp_path), "Harbor Lights", new="Lantern Light")
    exact = next(h for h in report["hits"] if h["match_kind"] == "exact")
    assert "Lantern Light" in exact["preview"]


def test_missing_targets_listed(tmp_path):
    report = mod.scan(_project(tmp_path), None)
    assert report["hits"] == []
    assert report["missing_targets"] == [
        {"file": "docs/songbook/paper-lanterns/harbor-lights.md", "line": 5, "target": "docs/wip-dock.md"}]


def test_same_input_same_output(tmp_path):
    root = _project(tmp_path)
    assert mod.scan(root, "Harbor Lights") == mod.scan(root, "Harbor Lights")


def test_cli_requires_old_or_paths_only(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["find-stale-refs.py", str(tmp_path)])
    assert mod.main() == 2
    assert json.loads(capsys.readouterr().out)["status"] == "error"


def test_cli_json(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path)
    monkeypatch.setattr(sys, "argv", ["find-stale-refs.py", str(root), "--old", "Harbor Lights"])
    assert mod.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok" and out["hit_count"] >= 4
