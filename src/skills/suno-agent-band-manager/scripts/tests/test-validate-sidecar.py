#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Tests for validate-sidecar.py"""

import sys
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

sys.path.insert(0, str(Path(__file__).parent.parent))

spec = spec_from_file_location(
    "validate_sidecar",
    Path(__file__).parent.parent / "validate-sidecar.py",
)
mod = module_from_spec(spec)
# Register before exec so @dataclass can resolve cls.__module__ during class build.
sys.modules["validate_sidecar"] = mod
spec.loader.exec_module(mod)


PUBLISHED_SONG = (
    "---\n"
    'title: "Harbor Lights"\n'
    "band_profile: paper-lanterns\n"
    "status: published\n"
    "date: 2026-01-15\n"
    "---\n\n"
    "**Status: LOCKED — Published 2026-01-15. A confession.**\n"
)


def _write_song(tmp_path, name, text):
    songbook = tmp_path / "docs" / "songbook" / "paper-lanterns"
    songbook.mkdir(parents=True, exist_ok=True)
    p = songbook / name
    p.write_text(text, encoding="utf-8")
    return p


def test_parse_song_published(tmp_path):
    p = _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
    song, err = mod.parse_song(p, tmp_path)
    assert err is None
    assert song.is_published is True
    assert song.title == "Harbor Lights"
    assert song.body_date == "2026-01-15"


def test_parse_song_no_frontmatter_returns_none(tmp_path):
    p = _write_song(tmp_path, "notes.md", "just prose, no frontmatter\n")
    song, err = mod.parse_song(p, tmp_path)
    assert song is None and err is None


def test_parse_song_bad_yaml_returns_error(tmp_path):
    bad = "---\ntitle: \"x\nstatus: [unterminated\n---\n\nbody\n"
    p = _write_song(tmp_path, "broken.md", bad)
    song, err = mod.parse_song(p, tmp_path)
    assert song is None
    assert err is not None


def test_check_songbook_consistency_flags_status_disagreement(tmp_path):
    text = (
        "---\n"
        'title: "Mismatch"\n'
        "band_profile: paper-lanterns\n"
        "status: published\n"
        "---\n\n"
        "**Status: WIP — still drafting.**\n"
    )
    p = _write_song(tmp_path, "mismatch.md", text)
    song, _ = mod.parse_song(p, tmp_path)
    findings = mod.check_songbook_consistency(song)
    assert any(f.severity == "error" for f in findings)


def test_check_songbook_consistency_warns_on_missing_marker(tmp_path):
    text = (
        "---\n"
        'title: "NoMarker"\n'
        "band_profile: paper-lanterns\n"
        "status: published\n"
        "---\n\n"
        "Body with no status marker.\n"
    )
    p = _write_song(tmp_path, "nomarker.md", text)
    song, _ = mod.parse_song(p, tmp_path)
    findings = mod.check_songbook_consistency(song)
    assert any(f.severity == "warning" for f in findings)


def test_check_markdown_cross_references_flags_broken_link(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text(
        "See `docs/does-not-exist.md` for details.\n", encoding="utf-8"
    )
    findings = mod.check_markdown_cross_references(tmp_path)
    assert any(f.category == "cross_reference_missing" for f in findings)


def test_check_markdown_cross_references_accepts_existing(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "target.md").write_text("hi\n", encoding="utf-8")
    (docs / "a.md").write_text("See `docs/target.md`.\n", encoding="utf-8")
    findings = mod.check_markdown_cross_references(tmp_path)
    assert not any(f.category == "cross_reference_missing" for f in findings)


def test_run_checks_clean_published_song(tmp_path):
    _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
    findings, stats = mod.run_checks(tmp_path)
    assert stats["songs_scanned"] == 1
    assert stats["songs_published"] == 1
    assert stats["findings_error"] == 0


def test_run_checks_detects_index_drift(tmp_path):
    # One published song, but MEMORY.md claims a different title in Recently Published.
    _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    (sanctum / "MEMORY.md").write_text(
        "# Mac — Curated Memory\n\n"
        "## Recently Published\n\n"
        "- **Ghost Song** (2026-01-15, PUBLISHED) — not in songbook.\n\n"
        "## Catalog Status\n\nstub\n\n"
        "## Module State\n\nend\n",
        encoding="utf-8",
    )
    findings, stats = mod.run_checks(tmp_path)
    assert any(f.category == "index_drift" for f in findings)
    # The finding's path points at MEMORY.md, not the legacy index.md.
    assert any(
        f.category == "index_drift" and f.path.endswith("MEMORY.md")
        for f in findings
    )


def test_run_checks_honors_sanctum_dir_override(tmp_path):
    """--sanctum-dir reads the derived sections from a staging copy."""
    _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
    staging = tmp_path / "staging-copy"
    staging.mkdir()
    (staging / "MEMORY.md").write_text(
        "# Mac — Curated Memory\n\n"
        "## Recently Published\n\n"
        "- **Ghost Song** (2026-01-15, PUBLISHED) — not in songbook.\n\n"
        "## Catalog Status\n\nstub\n\n"
        "## Module State\n\nend\n",
        encoding="utf-8",
    )
    # No MEMORY.md at the default location — drift only surfaces via the override.
    findings, stats = mod.run_checks(tmp_path, sanctum_dir=str(staging))
    assert any(f.category == "index_drift" for f in findings)


def test_format_text_pass():
    text = mod.format_text([], {
        "songs_scanned": 0, "songs_published": 0,
        "findings_total": 0, "findings_error": 0, "findings_warning": 0,
    })
    assert "PASS" in text
