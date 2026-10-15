#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for validate-sidecar.py"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402

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


V7_REL = ("_bmad", "memory", "suno-agent-band-manager")
GHOST_RECENT = (
    "# Recently Published\n\n"
    "<!-- derived:recently-published:start -->\n\n"
    "- **Ghost Song** (2026-01-15, PUBLISHED) — not in songbook.\n\n"
    "<!-- derived:recently-published:end -->\n"
)


def _v7_file(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _docs(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Parity checks the prompts used to re-derive by hand
# ---------------------------------------------------------------------------


def _songs(tmp_path):
    songs, _ = mod.load_all_songs(tmp_path)
    return songs


VOICE_FILE = (
    "# Voice\n\n## Companion Files — Load On Demand\n\n"
    "| File | What | When |\n|---|---|---|\n"
    "| `docs/paper-lanterns-playlist.yaml` | playlist | always |\n"
    "| `docs/gone.md` | deleted doc | never |\n"
    "| `docs/songbook/paper-lanterns/` | packages — {count} published as of today | refining |\n\n"
    "## Paper Lanterns — The Band\n\n**Catalog status:** **{count} published tracks** so far.\n\n"
    "## Other\n\nnothing\n"
)


PARKED_FILE = (
    "# Pending / Parked Work\n\n"
    "- Dock song — `docs/wip-dock.md`\n"
    "- Old idea — `docs/wip-done.md`\n\n"
    "### Resolved WIP fragments (historical record only)\n\n"
    "- `docs/wip-finished.md` -> published\n"
)


# ---------------------------------------------------------------------------
# voice_catalog_order — voice-file track numbers vs the playlist YAML
# ---------------------------------------------------------------------------

ORDER_PLAYLIST = (
    'album: "PL"\ntracks:\n'
    '  - name: "Harbor Lights"\n    file: a.mp3\n'
    '  - name: "Mirror Song"\n    file: b.mp3\n'
    '  - name: "Askin\'?"\n    file: c.mp3\n'
    '  - name: "Encore (Version 1)"\n    file: d.mp3\n'
)


def _order_project(tmp_path, voice_body):
    _docs(tmp_path, "docs/band-profiles/paper-lanterns.yaml", "name: Paper Lanterns\n")
    _docs(tmp_path, "docs/band-profiles/paper-lanterns-redux.yaml", "name: Paper Lanterns - Redux\n")
    _docs(tmp_path, "docs/paper-lanterns-playlist.yaml", ORDER_PLAYLIST)
    _docs(tmp_path, "docs/voice-context-owner.md", voice_body)
    _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
    _write_song(tmp_path, "mirror.md", PUBLISHED_SONG.replace(
        'title: "Harbor Lights"', 'title: "gnoS rorriM|Mirror Song"'))
    return mod.check_voice_catalog_order(_songs(tmp_path), tmp_path)


class ValidateSidecarTests(TempDirMixin, unittest.TestCase):
    def test_parse_song_published(self):
        tmp_path = self.tmp_path
        p = _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        song, err = mod.parse_song(p, tmp_path)
        self.assertIsNone(err)
        self.assertIs(song.is_published, True)
        self.assertEqual(song.title, "Harbor Lights")
        self.assertEqual(song.body_date, "2026-01-15")

    def test_parse_song_no_frontmatter_returns_none(self):
        tmp_path = self.tmp_path
        p = _write_song(tmp_path, "notes.md", "just prose, no frontmatter\n")
        song, err = mod.parse_song(p, tmp_path)
        self.assertIsNone(song)
        self.assertIsNone(err)

    def test_parse_song_bad_yaml_returns_error(self):
        tmp_path = self.tmp_path
        bad = "---\ntitle: \"x\nstatus: [unterminated\n---\n\nbody\n"
        p = _write_song(tmp_path, "broken.md", bad)
        song, err = mod.parse_song(p, tmp_path)
        self.assertIsNone(song)
        self.assertIsNotNone(err)

    def test_check_songbook_consistency_flags_status_disagreement(self):
        tmp_path = self.tmp_path
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
        self.assertTrue(any(f.severity == "error" for f in findings))

    def test_check_songbook_consistency_warns_on_missing_marker(self):
        tmp_path = self.tmp_path
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
        self.assertTrue(any(f.severity == "warning" for f in findings))

    def test_check_markdown_cross_references_flags_broken_link(self):
        tmp_path = self.tmp_path
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            "See `docs/does-not-exist.md` for details.\n", encoding="utf-8"
        )
        findings = mod.check_markdown_cross_references(tmp_path)
        self.assertTrue(any(f.category == "cross_reference_missing" for f in findings))

    def test_check_markdown_cross_references_accepts_existing(self):
        tmp_path = self.tmp_path
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "target.md").write_text("hi\n", encoding="utf-8")
        (docs / "a.md").write_text("See `docs/target.md`.\n", encoding="utf-8")
        findings = mod.check_markdown_cross_references(tmp_path)
        self.assertFalse(any(f.category == "cross_reference_missing" for f in findings))

    def test_run_checks_clean_published_song(self):
        tmp_path = self.tmp_path
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        findings, stats = mod.run_checks(tmp_path)
        self.assertEqual(stats["songs_scanned"], 1)
        self.assertEqual(stats["songs_published"], 1)
        self.assertEqual(stats["findings_error"], 0)

    def test_run_checks_detects_index_drift(self):
        tmp_path = self.tmp_path
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        sanctum = tmp_path.joinpath(*V7_REL)
        _v7_file(sanctum, "memory/catalog/recently-published.md", GHOST_RECENT)
        findings, stats = mod.run_checks(tmp_path)
        drift = [f for f in findings if f.category == "index_drift"]
        self.assertTrue(drift)
        # The finding points at the v7 catalog file.
        self.assertTrue(all(f.path == "_bmad/memory/suno-agent-band-manager/memory/catalog/recently-published.md" for f in drift))

    def test_run_checks_reads_catalog_status_file(self):
        tmp_path = self.tmp_path
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        _v7_file(tmp_path, "docs/band-profiles/paper-lanterns.yaml", "name: Paper Lanterns\n")
        sanctum = tmp_path.joinpath(*V7_REL)
        _v7_file(
            sanctum,
            "memory/catalog/status.md",
            "# Catalog Status\n\n<!-- derived:catalog-status:start -->\n\n"
            "- **Paper Lanterns:** **5 published tracks** — Harbor Lights.\n\n"
            "<!-- derived:catalog-status:end -->\n",
        )
        findings, _ = mod.run_checks(tmp_path)
        drift = [f for f in findings if f.category == "index_drift"]
        self.assertTrue(drift)
        self.assertTrue(drift[0].path.endswith("memory/catalog/status.md"))

    def test_run_checks_reads_parked_file(self):
        tmp_path = self.tmp_path
        _v7_file(tmp_path, "docs/wip-dock.md", "# Dock\n")
        sanctum = tmp_path.joinpath(*V7_REL)
        _v7_file(sanctum, "memory/work/parked.md", "# Pending / Parked Work\n\n- nothing about the dock\n")
        findings, _ = mod.run_checks(tmp_path)
        pending = [f for f in findings if f.category == "pending_drift"]
        self.assertEqual([f.message for f in pending], ["active WIP docs/wip-dock.md is not listed in Pending / Parked Work"])
        self.assertTrue(pending[0].path.endswith("memory/work/parked.md"))

    def test_run_checks_ignores_legacy_memory_md(self):
        """A MEMORY.md (v2) is not a live file: its claims are not checked."""
        tmp_path = self.tmp_path
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        sanctum = tmp_path.joinpath(*V7_REL)
        _v7_file(sanctum, "MEMORY.md", "## Recently Published\n\n- **Ghost Song** (2026-01-15, PUBLISHED)\n\n## X\n")
        findings, _ = mod.run_checks(tmp_path)
        self.assertFalse(any(f.category == "index_drift" for f in findings))

    def test_run_checks_honors_sanctum_dir_override(self):
        """--sanctum-dir reads the catalog files from a staging copy."""
        tmp_path = self.tmp_path
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        staging = tmp_path / "staging-copy"
        _v7_file(staging, "memory/catalog/recently-published.md", GHOST_RECENT)
        # Nothing at the default location — drift only surfaces via the override.
        self.assertFalse(any(f.category == "index_drift" for f in mod.run_checks(tmp_path)[0]))
        findings, stats = mod.run_checks(tmp_path, sanctum_dir=str(staging))
        self.assertTrue(any(f.category == "index_drift" for f in findings))

    def test_cli_json_with_sanctum_dir(self):
        tmp_path = self.tmp_path
        import json
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        staging = tmp_path / "staging-copy"
        _v7_file(staging, "memory/catalog/recently-published.md", GHOST_RECENT)
        buf = io.StringIO()
        with patch.object(sys, "argv", [
                "validate-sidecar.py", str(tmp_path), "--format", "json", "--sanctum-dir", str(staging)]), \
                redirect_stdout(buf):
            rc = mod.main()
        self.assertEqual(rc, 1)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["status"], "fail")
        with patch.object(sys, "argv", [
                "validate-sidecar.py", str(tmp_path), "--warn-only", "--sanctum-dir", str(staging)]), \
                redirect_stdout(io.StringIO()):
            rc = mod.main()
        self.assertEqual(rc, 0)

    def test_format_text_pass(self):
        text = mod.format_text([], {
            "songs_scanned": 0, "songs_published": 0,
            "findings_total": 0, "findings_error": 0, "findings_warning": 0,
        })
        self.assertIn("PASS", text)

    def test_published_field_is_the_date_the_body_marker_must_match(self):
        """`date:` can hold the start date when a separate `published:` holds the publish day."""
        tmp_path = self.tmp_path
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
        self.assertIsNone(err)
        self.assertEqual(song.frontmatter_published, "2026-01-15")
        self.assertFalse([f for f in mod.check_songbook_consistency(song) if "disagrees" in f.message])

    def test_published_field_mismatch_is_still_an_error(self):
        tmp_path = self.tmp_path
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
        self.assertTrue(errs)
        self.assertIn("frontmatter published=2026-01-20", errs[0].message)

    def test_cross_ref_resolves_bare_module_filename_by_suffix(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "src/skills/x/references/creed.md", "creed\n")
        _docs(tmp_path, "docs/notes.md", "see `creed.md` and `references/creed.md`\n")
        self.assertEqual(mod.check_markdown_cross_references(tmp_path), [])

    def test_cross_ref_skips_template_placeholders(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/notes.md", "each band has `docs/{band-slug}-genre-coverage.md`\n")
        self.assertEqual(mod.check_markdown_cross_references(tmp_path), [])

    def test_cross_ref_still_flags_a_missing_file(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/notes.md", "see `docs/does-not-exist.md`\n")
        found = mod.check_markdown_cross_references(tmp_path)
        self.assertEqual(len(found), 1)
        self.assertIn("does-not-exist.md", found[0].message)

    def test_cross_ref_honors_sanctum_ignore_list(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/other-agent/notes.md", "see `their-memory/secret.md`\n")
        sanctum = tmp_path.joinpath(*V7_REL)
        _docs(tmp_path, "_bmad/memory/suno-agent-band-manager/validate-ignore.txt", "# other agent's docs\ndocs/other-agent/*\n")
        self.assertEqual(mod.check_markdown_cross_references(tmp_path, sanctum), [])
        self.assertEqual(len(mod.check_markdown_cross_references(tmp_path)), 1)
        # run_checks reads the ignore list from the v7 sanctum root.
        findings, _ = mod.run_checks(tmp_path)
        self.assertFalse(any(f.category == "cross_reference_missing" for f in findings))

    def test_parity_skips_thematic_playlists_and_counts_versions_once(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/band-profiles/paper-lanterns.yaml", "name: Paper Lanterns\n")
        _docs(tmp_path, "docs/paper-lanterns-playlist.yaml",
              'album: "PL"\ntracks:\n  - name: "Harbor Lights (Version 1)"\n    file: a.mp3\n'
              '  - name: "Harbor Lights (Version 2)"\n    file: b.mp3\n')
        _docs(tmp_path, "docs/late-night-playlist.yaml", 'album: "LN"\ntracks:\n  - name: "X"\n    file: x.mp3\n')
        p = _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        song, _ = mod.parse_song(p, tmp_path)
        self.assertEqual(mod.check_playlist_songbook_parity([song], tmp_path), [])

    def test_parity_catches_a_rename_with_the_same_count(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/band-profiles/paper-lanterns.yaml", "name: Paper Lanterns\n")
        _docs(tmp_path, "docs/paper-lanterns-playlist.yaml",
              'album: "PL"\ntracks:\n  - name: "Harbour Light"\n    file: a.mp3\n')
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        findings = mod.check_playlist_songbook_parity(_songs(tmp_path), tmp_path)
        messages = " ".join(f.message for f in findings)
        self.assertIn("no songbook entry", messages)
        self.assertIn("'Harbour Light'", messages)
        self.assertIn("missing from the playlist", messages)
        self.assertIn("'Harbor Lights'", messages)

    def test_parity_accepts_short_title_and_stylized_forms(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/band-profiles/paper-lanterns.yaml", "name: Paper Lanterns\n")
        _docs(tmp_path, "docs/paper-lanterns-playlist.yaml",
              'album: "PL"\ntracks:\n  - name: "Mirror Song"\n    file: a.mp3\n'
              '  - name: "Harbor Lights"\n    file: b.mp3\n')
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        _write_song(tmp_path, "mirror.md", PUBLISHED_SONG.replace(
            'title: "Harbor Lights"', 'title: "gnoS rorriM|Mirror Song"'))
        self.assertEqual(mod.check_playlist_songbook_parity(_songs(tmp_path), tmp_path), [])

    def test_parity_ignores_unpublished_songs_missing_from_playlist(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/band-profiles/paper-lanterns.yaml", "name: Paper Lanterns\n")
        _docs(tmp_path, "docs/paper-lanterns-playlist.yaml",
              'album: "PL"\ntracks:\n  - name: "Harbor Lights"\n    file: b.mp3\n')
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        _write_song(tmp_path, "draft.md", "---\ntitle: Draft\nband_profile: paper-lanterns\nstatus: wip\n---\n")
        self.assertEqual(mod.check_playlist_songbook_parity(_songs(tmp_path), tmp_path), [])

    def test_voice_catalog_counts_match_songbook(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/band-profiles/paper-lanterns.yaml", "name: Paper Lanterns\n")
        _docs(tmp_path, "docs/voice-context-owner.md", VOICE_FILE.format(count=1))
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        self.assertEqual(mod.check_voice_catalog_counts(_songs(tmp_path), tmp_path), [])

    def test_voice_catalog_count_drift_is_flagged_in_section_and_row(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/band-profiles/paper-lanterns.yaml", "name: Paper Lanterns\n")
        _docs(tmp_path, "docs/voice-context-owner.md", VOICE_FILE.format(count=3))
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        findings = mod.check_voice_catalog_counts(_songs(tmp_path), tmp_path)
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(f.category == "voice_catalog_drift" for f in findings))
        self.assertTrue(all("claims 3" in f.message and "has 1" in f.message for f in findings))

    def test_companion_table_missing_entry_flagged(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/voice-context-owner.md", VOICE_FILE.format(count=1))
        _docs(tmp_path, "docs/paper-lanterns-playlist.yaml", "tracks: []\n")
        (tmp_path / "docs" / "songbook" / "paper-lanterns").mkdir(parents=True)
        findings = mod.check_companion_files(tmp_path)
        self.assertEqual([f.message for f in findings], [
            "Companion Files table lists 'docs/gone.md', which is not on disk"])

    def test_companion_untracked_since_date(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/voice-context-owner.md", VOICE_FILE.format(count=1))
        _docs(tmp_path, "docs/paper-lanterns-playlist.yaml", "tracks: []\n")
        _docs(tmp_path, "docs/gone.md", "now here\n")
        _docs(tmp_path, "docs/new-research.md", "fresh\n")
        _docs(tmp_path, "docs/wip-idea.md", "# Idea\n")
        (tmp_path / "docs" / "songbook" / "paper-lanterns").mkdir(parents=True)
        findings = mod.check_companion_files(tmp_path, since="2000-01-01")
        untracked = [f.path for f in findings if f.category == "companion_untracked"]
        self.assertEqual(untracked, ["docs/new-research.md"])
        self.assertEqual(mod.check_companion_files(tmp_path), [])  # no --since, no forward check

    def test_pending_vs_wip_markers(self):
        tmp_path = self.tmp_path
        marker = '# X\n\n## STATUS: COMPLETED as "X" — published 2026-01-01\n'
        _docs(tmp_path, "docs/wip-dock.md", "# Dock\n")
        _docs(tmp_path, "docs/wip-done.md", marker)
        _docs(tmp_path, "docs/wip-finished.md", marker)
        _docs(tmp_path, "docs/wip-unlisted.md", "# Unlisted\n")
        findings = mod.check_pending_vs_wip(PARKED_FILE, tmp_path, "memory/work/parked.md")
        messages = sorted(f.message for f in findings)
        self.assertEqual(messages, [
            "Pending / Parked Work lists docs/wip-done.md as active, but it carries a COMPLETED marker",
            "active WIP docs/wip-unlisted.md is not listed in Pending / Parked Work",
        ])

    def test_source_wip_and_short_title_parsed(self):
        tmp_path = self.tmp_path
        p = _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG.replace(
            "status: published\n",
            'status: published\nsource_wip: docs/wip-dock.md\nshort_title: "Harbor"\n'))
        song, _ = mod.parse_song(p, tmp_path)
        self.assertEqual(song.source_wip, "docs/wip-dock.md")
        self.assertEqual(song.short_title, "Harbor")

    def test_voice_catalog_order_clean_when_numbers_match(self):
        tmp_path = self.tmp_path
        body = ("# Voice\n\n## The Paper Lanterns Catalog\n\n"
                "1. **Harbor Lights** — opener\n2. \"Mirror Song\" (the mirror one)\n"
                "| 3 | Askin'? | pocket |\n**Track 4:** Encore (Version 2)\n")
        self.assertEqual(_order_project(tmp_path, body), [])

    def test_voice_catalog_order_flags_each_stale_number(self):
        tmp_path = self.tmp_path
        body = ("# Voice\n\n## The Paper Lanterns Catalog\n\n"
                "1. **Mirror Song** — moved\n2. **Harbor Lights** — moved\n"
                "| 7 | Askin'? | pocket |\nTrack 9: gnoS rorriM\n")
        findings = _order_project(tmp_path, body)
        self.assertTrue(all(f.category == "voice_catalog_order" and f.severity == "warning" for f in findings))
        messages = [f.message for f in findings]
        self.assertEqual(len(messages), 4)
        self.assertTrue(any("'mirror song' as 1" in m and "at 2" in m for m in messages))
        self.assertTrue(any("'harbor lights' as 2" in m and "at 1" in m for m in messages))
        self.assertTrue(any("as 7" in m and "at 3" in m for m in messages))
        self.assertTrue(any("as 9" in m and "at 2" in m for m in messages))  # stylized songbook form

    def test_voice_catalog_order_ignores_procedure_lists_and_other_sections(self):
        tmp_path = self.tmp_path
        body = ("# Voice\n\n## How He Writes\n\n4. **Harbor Lights** in a section naming no band\n\n"
                "## The Paper Lanterns Catalog\n\n1. Find direction\n2. Find the words\n"
                "3. Harbor Lights came first — a prose note, not a title\n")
        self.assertEqual(_order_project(tmp_path, body), [])

    def test_voice_catalog_order_uses_the_longest_band_name(self):
        tmp_path = self.tmp_path
        body = "# Voice\n\n## Paper Lanterns - Redux\n\n5. **Harbor Lights**\n"
        # The Redux band has no playlist YAML, so nothing is compared.
        self.assertEqual(_order_project(tmp_path, body), [])

    def test_voice_catalog_order_skips_without_playlist(self):
        tmp_path = self.tmp_path
        _docs(tmp_path, "docs/band-profiles/paper-lanterns.yaml", "name: Paper Lanterns\n")
        _docs(tmp_path, "docs/voice-context-owner.md", "## Paper Lanterns\n\n9. **Harbor Lights**\n")
        _write_song(tmp_path, "harbor-lights.md", PUBLISHED_SONG)
        self.assertEqual(mod.check_voice_catalog_order(_songs(tmp_path), tmp_path), [])

    def test_voice_catalog_order_is_a_warning_in_run_checks(self):
        tmp_path = self.tmp_path
        _order_project(tmp_path, "## Paper Lanterns\n\n4. **Harbor Lights**\n")
        findings, stats = mod.run_checks(tmp_path)
        order = [f for f in findings if f.category == "voice_catalog_order"]
        self.assertEqual(len(order), 1)
        self.assertEqual(order[0].severity, "warning")


if __name__ == "__main__":
    unittest.main()
