#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for reconcile-sidecar.py"""

import sys
import time
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

sys.path.insert(0, str(Path(__file__).parent.parent))

spec = spec_from_file_location(
    "reconcile_sidecar",
    Path(__file__).parent.parent / "reconcile-sidecar.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


V7_REL = ("_bmad", "memory", "suno-agent-band-manager")


def _scaffold_sidecar(tmp_path, sanctum=None):
    """A v7 sanctum with one standing file; returns that file (the store reference)."""
    sanctum = sanctum or tmp_path.joinpath(*V7_REL)
    work = sanctum / "memory" / "work"
    work.mkdir(parents=True)
    current = work / "current.md"
    current.write_text("# Current Work\n", encoding="utf-8")
    return current


def test_format_mtime_is_utc_string():
    s = mod._format_mtime(0.0)
    assert s.endswith("UTC")
    assert s.startswith("1970-01-01")


def test_build_report_no_sidecar(tmp_path):
    payload = mod.build_report(tmp_path)
    assert payload["status"] == "no_sidecar"
    assert payload["newer_files"] == []
    assert payload["needs_reconciliation"] is False


def test_find_newer_docs_detects_fresh_file(tmp_path):
    index = _scaffold_sidecar(tmp_path)
    index_mtime = index.stat().st_mtime

    docs = tmp_path / "docs"
    docs.mkdir()
    fresh = docs / "wip-new-song.md"
    fresh.write_text("fragments\n", encoding="utf-8")
    # Force the fresh file's mtime clearly after the index.
    future = index_mtime + 100
    import os
    os.utime(fresh, (future, future))

    newer = mod.find_newer_docs(tmp_path, index_mtime)
    paths = {item["path"] for item in newer}
    assert any("wip-new-song.md" in p for p in paths)


def test_find_newer_docs_ignores_older_file(tmp_path):
    index = _scaffold_sidecar(tmp_path)
    index_mtime = index.stat().st_mtime + 1000  # pretend index is very recent

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "old.md").write_text("old\n", encoding="utf-8")

    assert mod.find_newer_docs(tmp_path, index_mtime) == []


def test_run_validator_skips_when_missing(tmp_path, monkeypatch):
    # Point the validator lookup at a directory with no validate-sidecar.py.
    fake_dir = tmp_path / "nope"
    fake_dir.mkdir()
    monkeypatch.setattr(mod, "__file__", str(fake_dir / "reconcile-sidecar.py"))
    result = mod.run_validator(tmp_path)
    assert result["status"] == "skipped"


def test_build_report_flags_reconciliation_when_newer_file(tmp_path, monkeypatch):
    index = _scaffold_sidecar(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    fresh = docs / "session.md"
    fresh.write_text("update\n", encoding="utf-8")
    import os
    future = index.stat().st_mtime + 50
    os.utime(fresh, (future, future))

    # Stub the validator so the test doesn't depend on validate-sidecar.py.
    monkeypatch.setattr(
        mod, "run_validator", lambda root, sanctum=None: {"status": "skipped"}
    )

    payload = mod.build_report(tmp_path)
    assert payload["needs_reconciliation"] is True
    assert payload["status"] == "needs_reconciliation"


def test_build_report_honors_sanctum_dir_override(tmp_path, monkeypatch):
    """--sanctum-dir reads the store-freshness reference from a staging copy."""
    staging = tmp_path / "staging-copy"
    memory = _scaffold_sidecar(tmp_path, staging)

    docs = tmp_path / "docs"
    docs.mkdir()
    fresh = docs / "session.md"
    fresh.write_text("update\n", encoding="utf-8")
    import os
    future = memory.stat().st_mtime + 50
    os.utime(fresh, (future, future))

    monkeypatch.setattr(
        mod, "run_validator", lambda root, sanctum=None: {"status": "skipped"}
    )

    payload = mod.build_report(tmp_path, sanctum_dir=str(staging))
    assert payload["status"] == "needs_reconciliation"
    assert payload["store_path"].endswith("memory/work/current.md")


def test_store_reference_is_newest_memory_file_but_not_the_catalog(tmp_path, monkeypatch):
    import os
    current = _scaffold_sidecar(tmp_path)
    sanctum = tmp_path.joinpath(*V7_REL)
    base = current.stat().st_mtime
    note = sanctum / "memory" / "sessions" / "2026-10-02-note.md"
    note.parent.mkdir(parents=True)
    note.write_text("note\n", encoding="utf-8")
    os.utime(note, (base + 100, base + 100))
    catalog = sanctum / "memory" / "catalog" / "status.md"
    catalog.parent.mkdir(parents=True)
    catalog.write_text("derived\n", encoding="utf-8")
    os.utime(catalog, (base + 1000, base + 1000))  # regenerated later: ignored
    doc = tmp_path / "docs" / "wip-x.md"
    doc.parent.mkdir()
    doc.write_text("x\n", encoding="utf-8")
    os.utime(doc, (base + 500, base + 500))
    monkeypatch.setattr(mod, "run_validator", lambda root, sanctum=None: {"status": "skipped"})
    payload = mod.build_report(tmp_path)
    assert payload["store_path"] == "_bmad/memory/suno-agent-band-manager/memory/sessions/2026-10-02-note.md"
    assert [f["path"] for f in payload["newer_files"]] == ["docs/wip-x.md"]


def test_legacy_store_is_not_read(tmp_path):
    """A v2 MEMORY.md at the legacy path is not the v7 store."""
    legacy = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    legacy.mkdir(parents=True)
    (legacy / "MEMORY.md").write_text("# old\n", encoding="utf-8")
    assert mod.build_report(tmp_path)["status"] == "no_sidecar"


def test_format_text_renders_clean_report():
    payload = {
        "status": "clean",
        "store_path": "_bmad/memory/suno-agent-band-manager/memory/work/current.md",
        "store_mtime": "2026-06-18 00:00:00 UTC",
        "newer_files": [],
        "validator": {"status": "pass", "findings": []},
        "needs_reconciliation": False,
    }
    text = mod.format_text(payload)
    assert "Sanctum Reconciliation Report" in text
    assert "CLEAN" in text


def test_run_validator_launches_through_uv_when_available(tmp_path, monkeypatch):
    """validate-sidecar.py needs PyYAML; `uv run` provisions it, else this interpreter."""
    import json as _json
    import subprocess

    seen = []

    def fake_run(cmd, **kwargs):
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=_json.dumps({"status": "pass"}), stderr="")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/uv")
    assert mod.run_validator(tmp_path, "/staging")["status"] == "pass"
    assert seen[-1][:4] == ["/usr/bin/uv", "run", "-q", "--script"]
    assert seen[-1][-2:] == ["--sanctum-dir", "/staging"]
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    mod.run_validator(tmp_path)
    assert seen[-1][0] == sys.executable
