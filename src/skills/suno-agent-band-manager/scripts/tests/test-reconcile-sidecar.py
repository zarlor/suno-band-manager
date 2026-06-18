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


def _scaffold_sidecar(tmp_path):
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    memory = sanctum / "MEMORY.md"
    memory.write_text("# Mac — Curated Memory\n", encoding="utf-8")
    (sanctum / "INDEX.md").write_text("# Mac's Sanctum — Index\n", encoding="utf-8")
    return memory


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
    staging.mkdir()
    memory = staging / "MEMORY.md"
    memory.write_text("# Mac — Curated Memory\n", encoding="utf-8")
    (staging / "INDEX.md").write_text("# Index\n", encoding="utf-8")

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
    assert payload["store_path"].endswith("MEMORY.md") or payload[
        "store_path"
    ].endswith("INDEX.md")


def test_format_text_renders_clean_report():
    payload = {
        "status": "clean",
        "store_path": "_bmad/_memory/band-manager-sidecar/MEMORY.md",
        "store_mtime": "2026-06-18 00:00:00 UTC",
        "newer_files": [],
        "validator": {"status": "pass", "findings": []},
        "needs_reconciliation": False,
    }
    text = mod.format_text(payload)
    assert "Sanctum Reconciliation Report" in text
    assert "CLEAN" in text
