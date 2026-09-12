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


def test_published_field_is_the_date_the_body_marker_must_match(tmp_path):
    """`date:` can hold the start date when a separate `published:` holds the publish day."""
    text = (
        "---\n"
        'title: "Harbor Lights"\n'
        "band_profile: paper-lanterns\n"
        "status: published\n"
        "date: 2026-01-02\n"
        "published: 2026-01-15\n"
        "---\n\n"
        "**Status: LOCKED — Published 2026-01-15. A confession.**\n"
    )
    p = _write_song(tmp_path, "harbor-lights.md", text)
    song, err = mod.parse_song(p, tmp_path)
    assert err is None and song.frontmatter_published == "2026-01-15"
    assert not [f for f in mod.check_songbook_consistency(song) if "disagrees" in f.message]


def test_published_field_mismatch_is_still_an_error(tmp_path):
    text = (
        "---\n"
        'title: "Harbor Lights"\n'
        "band_profile: paper-lanterns\n"
        "status: published\n"
        "date: 2026-01-02\n"
        "published: 2026-01-20\n"
        "---\n\n"
        "**Status: LOCKED — Published 2026-01-15. A confession.**\n"
    )
    p = _write_song(tmp_path, "harbor-lights.md", text)
    song, _ = mod.parse_song(p, tmp_path)
    errs = [f for f in mod.check_songbook_consistency(song) if f.severity == "error"]
    assert errs and "frontmatter published=2026-01-20" in errs[0].message


def _docs(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def test_cross_ref_resolves_bare_module_filename_by_suffix(tmp_path):
    _docs(tmp_path, "src/skills/x/references/creed.md", "creed\n")
    _docs(tmp_path, "docs/notes.md", "see `creed.md` and `references/creed.md`\n")
    assert mod.check_markdown_cross_references(tmp_path) == []


def test_cross_ref_skips_template_placeholders(tmp_path):
    _docs(tmp_path, "docs/notes.md", "each band has `docs/{band-slug}-genre-coverage.md`\n")
    assert mod.check_markdown_cross_references(tmp_path) == []


def test_cross_ref_still_flags_a_missing_file(tmp_path):
    _docs(tmp_path, "docs/notes.md", "see `docs/does-not-exist.md`\n")
    found = mod.check_markdown_cross_references(tmp_path)
    assert len(found) == 1 and "does-not-exist.md" in found[0].message


def test_cross_ref_honors_sanctum_ignore_list(tmp_path):
    _docs(tmp_path, "docs/other-agent/notes.md", "see `their-memory/secret.md`\n")
    sanctum = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    _docs(tmp_path, "_bmad/_memory/band-manager-sidecar/validate-ignore.txt", "# other agent's docs\ndocs/other-agent/*\n")
    assert mod.check_markdown_cross_references(tmp_path, sanctum) == []
    assert len(mod.check_markdown_cross_references(tmp_path)) == 1


def test_parity_skips_thematic_playlists_and_counts_versions_once(tmp_path):
    _docs(tmp_path, "docs/band-profiles/paper-lanterns.yaml", "name: Paper Lanterns\n")
    _docs(tmp_path, "docs/paper-lanterns-playlist.yaml",
          'album: "PL"\ntracks:\n  - name: "Harbor Lights (Version 1)"\n    file: a.mp3\n'
          '  - name: "Harbor Lights (Version 2)"\n    file: b.mp3\n')
    _docs(tmp_path, "docs/late-night-playlist.yaml", 'album: "LN"\ntracks:\n  - name: "X"\n    file: x.mp3\n')
    p = _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
    song, _ = mod.parse_song(p, tmp_path)
    assert mod.check_playlist_songbook_parity([song], tmp_path) == []

