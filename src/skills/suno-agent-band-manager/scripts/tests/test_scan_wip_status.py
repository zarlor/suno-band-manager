#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for scan_wip_status.py — WIP COMPLETED-marker scan + songbook correlation."""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402
from fake_resolver import install_resolver  # noqa: E402

SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

spec = spec_from_file_location("scan_wip_status", SCRIPTS_DIR / "scan_wip_status.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


PUBLISHED_SONG = (
    "---\n"
    'title: "Harbor Lights"\n'
    "band_profile: paper-lanterns\n"
    "status: published\n"
    "date: 2026-06-10\n"
    "---\n"
    "**Status: PUBLISHED — Published 2026-06-10.**\n"
)

COMPLETED_WIP = (
    "# Harbor Lights\n"
    "## WIP — 2026-05-01\n\n"
    "---\n\n"
    '## STATUS: COMPLETED as "Harbor Lights" — published 2026-06-10\n\n'
    "Preserved as historical record. See the songbook entry at\n"
    "`docs/songbook/paper-lanterns/harbor-lights.md` for the finished form.\n\n"
    "**This WIP file is NOT active work — do not list it in pending/parked work.**\n\n"
    "---\n\n"
    "old fragments...\n"
)


def _project(tmp_path):
    (tmp_path / "docs").mkdir()
    return tmp_path


class ScanWipStatusTests(TempDirMixin, unittest.TestCase):
    def test_no_docs_dir_returns_empty(self):
        tmp_path = self.tmp_path
        report = mod.build_report(tmp_path)
        self.assertEqual(report["wip_count"], 0)
        self.assertEqual(report["files"], [])

    def test_completed_marker_parsed(self):
        tmp_path = self.tmp_path
        proj = _project(tmp_path)
        (proj / "docs" / "wip-harbor-lights-fragments.md").write_text(COMPLETED_WIP, encoding="utf-8")
        report = mod.build_report(proj)
        self.assertEqual(report["wip_count"], 1)
        f = report["files"][0]
        self.assertEqual(f["status"], "completed")
        self.assertEqual(f["completed_as"], "Harbor Lights")
        self.assertEqual(f["published_date"], "2026-06-10")
        self.assertEqual(f["songbook_ref"], "docs/songbook/paper-lanterns/harbor-lights.md")
        self.assertIsNone(f["correlation_warning"])

    def test_active_wip_no_collision_no_warning(self):
        tmp_path = self.tmp_path
        proj = _project(tmp_path)
        (proj / "docs" / "wip-brand-new-idea.md").write_text(
            "# Brand New Idea\n## WIP — 2026-06-16\n\na fresh concept\n"
        , encoding="utf-8")
        report = mod.build_report(proj)
        f = report["files"][0]
        self.assertEqual(f["status"], "active")
        self.assertIsNone(f["correlation_warning"])

    def test_active_wip_collides_with_published_warns(self):
        tmp_path = self.tmp_path
        proj = _project(tmp_path)
        sb = proj / "docs" / "songbook" / "paper-lanterns"
        sb.mkdir(parents=True)
        (sb / "harbor-lights.md").write_text(PUBLISHED_SONG, encoding="utf-8")
        # Active WIP whose working title matches the published song (v2 suffix stripped).
        (proj / "docs" / "wip-harbor-lights-v2-fragments.md").write_text(
            "# Harbor Lights v2\n## WIP — 2026-06-15\n\nsequel lines\n"
        , encoding="utf-8")
        report = mod.build_report(proj)
        f = report["files"][0]
        self.assertEqual(f["status"], "active")
        self.assertIsNotNone(f["correlation_warning"])
        self.assertIn("Harbor Lights v2", f["correlation_warning"])
        self.assertEqual(f["songbook_ref"], "docs/songbook/paper-lanterns/harbor-lights.md")
        self.assertEqual(report["correlation_warnings"], 1)

    def test_mixed_set_counts(self):
        tmp_path = self.tmp_path
        proj = _project(tmp_path)
        sb = proj / "docs" / "songbook" / "paper-lanterns"
        sb.mkdir(parents=True)
        (sb / "harbor-lights.md").write_text(PUBLISHED_SONG, encoding="utf-8")
        (proj / "docs" / "wip-harbor-lights-fragments.md").write_text(COMPLETED_WIP, encoding="utf-8")
        (proj / "docs" / "wip-harbor-lights-v2-fragments.md").write_text(
            "# Harbor Lights v2\n\nsequel\n"
        , encoding="utf-8")
        (proj / "docs" / "wip-unrelated.md").write_text("# Unrelated\n\nstuff\n", encoding="utf-8")
        report = mod.build_report(proj)
        self.assertEqual(report["wip_count"], 3)
        self.assertEqual(report["completed"], 1)
        self.assertEqual(report["active"], 2)
        self.assertEqual(report["correlation_warnings"], 1)

    def test_unpublished_song_does_not_trigger_warning(self):
        """A WIP matching a NON-published songbook entry must not warn (nothing to mark)."""
        tmp_path = self.tmp_path
        proj = _project(tmp_path)
        sb = proj / "docs" / "songbook" / "paper-lanterns"
        sb.mkdir(parents=True)
        (sb / "harbor-lights.md").write_text(
            "---\n"
            'title: "Harbor Lights"\n'
            "band_profile: paper-lanterns\n"
            "status: wip\n"
            "---\n"
            "**Status: WIP.**\n"
        , encoding="utf-8")
        (proj / "docs" / "wip-harbor-lights-fragments.md").write_text(
            "# Harbor Lights\n\nfragments\n"
        , encoding="utf-8")
        report = mod.build_report(proj)
        f = report["files"][0]
        self.assertEqual(f["status"], "active")
        self.assertIsNone(f["correlation_warning"])

    def test_main_json_output(self):
        tmp_path = self.tmp_path
        proj = _project(tmp_path)
        (proj / "docs" / "wip-x.md").write_text("# X\n\nstuff\n", encoding="utf-8")
        buf = io.StringIO()
        with mock.patch.object(sys, "argv", ["scan_wip_status.py", str(proj), "--format", "json"]), \
                redirect_stdout(buf):
            rc = mod.main()
        self.assertEqual(rc, 0)
        out = json.loads(buf.getvalue())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["wip_count"], 1)

    def test_marker_without_quotes_or_date_still_completed(self):
        """A slightly-off marker (no quoted title / no date) still flips status."""
        tmp_path = self.tmp_path
        proj = _project(tmp_path)
        (proj / "docs" / "wip-loose.md").write_text(
            "# Loose\n\n## STATUS: COMPLETED — folded into the album\n\nfragments\n"
        , encoding="utf-8")
        report = mod.build_report(proj)
        f = report["files"][0]
        self.assertEqual(f["status"], "completed")
        self.assertIsNone(f["completed_as"])
        self.assertIsNone(f["published_date"])

    def test_source_wip_correlates_a_renamed_song(self):
        """A WIP whose working title differs from the published title still
        correlates when the songbook entry records it as source_wip."""
        tmp_path = self.tmp_path
        proj = _project(tmp_path)
        sb = proj / "docs" / "songbook" / "paper-lanterns"
        sb.mkdir(parents=True)
        (sb / "harbor-lights.md").write_text(
            PUBLISHED_SONG.replace(
                "status: published\n",
                "status: published\nsource_wip: docs/wip-dock-song-fragments.md\n",
            )
        , encoding="utf-8")
        (proj / "docs" / "wip-dock-song-fragments.md").write_text("# Dock Song\n\nlines\n", encoding="utf-8")
        f = mod.build_report(proj)["files"][0]
        self.assertEqual(f["status"], "active")
        self.assertEqual(f["correlated_by"], "source_wip")
        self.assertEqual(f["songbook_ref"], "docs/songbook/paper-lanterns/harbor-lights.md")
        self.assertIn("source_wip", f["correlation_warning"])

    def test_title_match_is_reported_as_fallback(self):
        tmp_path = self.tmp_path
        proj = _project(tmp_path)
        sb = proj / "docs" / "songbook" / "paper-lanterns"
        sb.mkdir(parents=True)
        (sb / "harbor-lights.md").write_text(PUBLISHED_SONG, encoding="utf-8")
        (proj / "docs" / "wip-harbor-lights-fragments.md").write_text("# Harbor Lights\n\nx\n", encoding="utf-8")
        f = mod.build_report(proj)["files"][0]
        self.assertEqual(f["correlated_by"], "title")

    def test_uncorrelated_active_wip_has_null_correlated_by(self):
        tmp_path = self.tmp_path
        proj = _project(tmp_path)
        (proj / "docs" / "wip-new.md").write_text("# New\n\nx\n", encoding="utf-8")
        self.assertIsNone(mod.build_report(proj)["files"][0]["correlated_by"])

    # --- the songbook is the module's songbook_folder ---

    def test_configured_songbook_folder_is_correlated_and_pointed_at(self):
        proj = _project(self.tmp_path)
        install_resolver(proj)
        (proj / "_bmad" / "config.toml").write_text(
            '[modules.suno]\nsongbook_folder = "{project-root}/music/songs"\n', encoding="utf-8")
        song = proj / "music" / "songs" / "paper-lanterns" / "harbor-lights.md"
        song.parent.mkdir(parents=True)
        song.write_text(PUBLISHED_SONG, encoding="utf-8")
        (proj / "docs" / "wip-harbor-lights-fragments.md").write_text("# Harbor Lights\n\nfragments\n", encoding="utf-8")
        (proj / "docs" / "wip-done.md").write_text(
            COMPLETED_WIP.replace("docs/songbook/", "music/songs/"), encoding="utf-8")
        files = {Path(f["path"]).name: f for f in mod.build_report(proj)["files"]}
        active = files["wip-harbor-lights-fragments.md"]
        self.assertEqual(active["correlated_by"], "title")
        self.assertEqual(active["songbook_ref"], "music/songs/paper-lanterns/harbor-lights.md")
        self.assertEqual(files["wip-done.md"]["songbook_ref"], "music/songs/paper-lanterns/harbor-lights.md")

    def test_unparseable_songbook_entry_does_not_stop_the_scan(self):
        proj = _project(self.tmp_path)
        songbook = proj / "docs" / "songbook" / "paper-lanterns"
        songbook.mkdir(parents=True)
        (songbook / "broken.md").write_text("---\njust prose\n---\n\nbody\n", encoding="utf-8")
        (songbook / "harbor-lights.md").write_text(PUBLISHED_SONG, encoding="utf-8")
        (proj / "docs" / "wip-harbor-lights-fragments.md").write_text("# Harbor Lights\n", encoding="utf-8")
        report = mod.build_report(proj)
        self.assertEqual(report["correlation_warnings"], 1)


if __name__ == "__main__":
    unittest.main()
