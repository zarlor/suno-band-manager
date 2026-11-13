#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for genre_coverage.py"""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402
from fake_resolver import install_resolver  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent))

spec = spec_from_file_location(
    "genre_coverage",
    Path(__file__).parent.parent / "genre_coverage.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def _band(tmp_path):
    songbook = tmp_path / "docs" / "songbook" / "paper-lanterns"
    songbook.mkdir(parents=True)
    song = songbook / "harbor-lights.md"
    song.write_text('title: "Harbor Lights"\nstatus: published\n\n'
                    "## Style Prompt\n\n```\nchamber folk, close vocal\n```\n", encoding="utf-8")
    (tmp_path / "docs" / "band-profiles").mkdir()
    (tmp_path / "docs" / "band-profiles" / "paper-lanterns.yaml").write_text(
        'name: "Paper Lanterns"\nreference_tracks:\n  - "Artist One — warm"\n', encoding="utf-8")
    return song


def _run(capsys, *argv):
    with patch.object(sys, "argv", ["genre_coverage.py", *argv]), capsys():
        return mod.main()


def _break_profile(tmp_path):
    (tmp_path / "docs" / "band-profiles" / "paper-lanterns.yaml").write_text(
        'name: "Paper Lanterns\nreference_tracks: [unclosed\n', encoding="utf-8")


class TestGenreCoverage(TempDirMixin, unittest.TestCase):
    def test_title_of_prefers_frontmatter(self):
        text = 'title: "Harbor Lights"\n\n# Wrong Heading\n'
        self.assertEqual(mod.title_of(text, "fallback"), "Harbor Lights")

    def test_title_of_falls_back_to_heading(self):
        text = "no frontmatter here\n\n# Sunday Driver\n"
        self.assertEqual(mod.title_of(text, "fallback"), "Sunday Driver")

    def test_title_of_uses_fallback_when_nothing_matches(self):
        self.assertEqual(mod.title_of("plain prose, nothing useful", "the-slug"), "the-slug")

    def test_status_of_reads_status_line(self):
        self.assertEqual(mod.status_of("title: X\nstatus: published\n"), "published")
        self.assertEqual(mod.status_of("no status field"), "unknown")

    def test_first_style_prompt_extracts_code_block(self):
        text = (
            "## Style Prompt\n\n"
            "```\nprogressive groove metal, down-tuned, halftime groove\n```\n"
        )
        self.assertIn("progressive groove metal", mod.first_style_prompt(text))

    def test_first_style_prompt_returns_none_without_heading(self):
        self.assertIsNone(mod.first_style_prompt("no style prompt heading here"))

    def test_labeled_territory_extracts_verbatim(self):
        text = "**Reference territory:** Blink-182 / Matchbox 20, '90s alt\n"
        self.assertEqual(mod.labeled_territory(text), ["Blink-182 / Matchbox 20, '90s alt"])

    def test_profile_fields_extracts_curated_fields_verbatim(self):
        profile = {
            "genre": "Harbor folk / chamber pop",
            "reference_tracks": ["Artist One — warm close vocal", "Band 182 — fast punk edge"],
            "style_alternatives": {"ballad": "Warm folk, brushed drums"},
            "voice_profiles": [{"name": "Voice A", "use_case": "Sparse intimate verses"}],
            "catalog": [{"title": "Harbor Lights", "genre_applied": "chamber folk (Artist One territory)"}],
        }
        f = mod.profile_fields(profile)
        self.assertEqual(f["genre"], "Harbor folk / chamber pop")
        self.assertIn("Band 182 — fast punk edge", f["reference_tracks"])  # digits survive
        self.assertEqual(f["style_alternatives"], [("ballad", "Warm folk, brushed drums")])
        self.assertEqual(f["voice_use_cases"], [("Voice A", "Sparse intimate verses")])
        self.assertEqual(f["genre_applied"], [("Harbor Lights", "chamber folk (Artist One territory)")])

    def test_profile_fields_tolerates_missing_or_odd_shapes(self):
        self.assertEqual(mod.profile_fields(None), {})
        self.assertEqual(mod.profile_fields({"reference_tracks": None, "catalog": "x"}), {})

    def test_collect_band_and_json_run(self):
        """End-to-end: a band dir with one published song produces a JSON summary."""
        songbook = self.tmp_path / "docs" / "songbook" / "paper-lanterns"
        songbook.mkdir(parents=True)
        (songbook / "harbor-lights.md").write_text(
            'title: "Harbor Lights"\nstatus: published\n\n'
            "## Style Prompt\n\n```\nprogressive groove metal, down-tuned\n```\n"
            "Reference territory: Pantera-heavy lineage\n",
            encoding="utf-8",
        )

        with patch.object(
            sys, "argv",
            ["genre_coverage.py", str(self.tmp_path), "--format", "json"],
        ), self.capsys():
            mod.main()
        out = json.loads(self.capsys.readouterr().out)
        self.assertEqual(out["band_count"], 1)
        band = out["bands"][0]
        self.assertEqual(band["band"], "paper-lanterns")
        self.assertEqual(band["entries"], 1)
        # The generated doc was written, with the style prompt verbatim.
        doc = (self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md").read_text(encoding="utf-8")
        self.assertIn("progressive groove metal, down-tuned", doc)
        self.assertIn("Pantera-heavy lineage", doc)
        self.assertIn("Absence here does not prove", doc)

    def test_empty_catalog_is_clean_noop_json(self):
        """No docs/songbook/ yet → exit 0 with a zeroed JSON result, not exit 2."""
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        out = json.loads(self.capsys.readouterr().out)
        self.assertEqual(out, {"bands": [], "band_count": 0})
        # --check on an empty catalog is clean too: there is nothing to be stale.
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--check", "--format", "json"), 0)

    def test_empty_catalog_is_clean_noop_text(self):
        """Empty catalog in text mode prints a friendly no-op line and exits 0."""
        self.assertEqual(_run(self.capsys, str(self.tmp_path)), 0)
        captured = self.capsys.readouterr().out
        self.assertTrue("empty catalog" in captured.lower() or "nothing to index" in captured.lower())

    def test_missing_project_root_is_an_error_not_an_empty_catalog(self):
        gone = str(self.tmp_path / "no-such-project")
        self.assertEqual(_run(self.capsys, gone, "--format", "json"), 2)
        out = json.loads(self.capsys.readouterr().out)
        self.assertEqual(out["status"], "error")
        self.assertIn("project root not found", out["error"])
        self.assertEqual(_run(self.capsys, gone, "--check"), 2)
        captured = self.capsys.readouterr()
        self.assertIn("project root not found", captured.err)
        self.assertNotIn("empty catalog", captured.out)

    def test_without_pyyaml_the_error_is_json_not_a_traceback(self):
        script = Path(__file__).parent.parent / "genre_coverage.py"
        code = ("import runpy, sys; sys.modules['yaml'] = None; sys.argv = ['genre_coverage.py', sys.argv[1]]; "
                f"runpy.run_path({str(script)!r}, run_name='__main__')")
        proc = subprocess.run([sys.executable, "-c", code, str(self.tmp_path)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "error")
        self.assertIn("PyYAML", out["message"])

    # --- the coverage doc's own text is never lost ---

    def test_doc_without_markers_is_kept_whole_below_the_new_index(self):
        _band(self.tmp_path)
        out = self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md"
        hand_written = "# My own coverage notes\n\nNever done: sea shanties.\n"
        for label, existing in (("no markers", hand_written),
                                ("start marker only", hand_written + mod.AUTOGEN_START + "\nhalf an index\n"),
                                ("end marker only", mod.AUTOGEN_END + "\n" + hand_written)):
            with self.subTest(doc=label):
                out.write_text(existing, encoding="utf-8")
                self.assertEqual(_run(self.capsys, str(self.tmp_path), "--format", "json"), 0)
                row = json.loads(self.capsys.readouterr().out)["bands"][0]
                self.assertIs(row["kept_unmarked_text"], True)
                doc = out.read_text(encoding="utf-8")
                self.assertTrue(doc.startswith(mod.AUTOGEN_START))
                self.assertTrue(doc.endswith(existing))  # every byte that was there, after the index
                self.assertIn("chamber folk, close vocal", doc)
        # The next run finds the markers and replaces only the index.
        out.write_text(hand_written, encoding="utf-8")
        _run(self.capsys, str(self.tmp_path))
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        self.capsys.readouterr()
        _run(self.capsys, str(self.tmp_path), "--format", "json")
        self.assertIs(json.loads(self.capsys.readouterr().out)["bands"][0]["kept_unmarked_text"], False)
        doc = out.read_text(encoding="utf-8")
        self.assertEqual((doc.count(mod.AUTOGEN_START), doc.count("Never done: sea shanties.")), (1, 1))

    def test_fresh_and_marked_docs_report_nothing_kept(self):
        _band(self.tmp_path)
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        self.assertIs(json.loads(self.capsys.readouterr().out)["bands"][0]["kept_unmarked_text"], False)

    # --- a songbook entry that is not UTF-8 ---

    def test_non_utf8_entry_is_listed_reported_and_exits_1(self):
        song = _band(self.tmp_path)
        bad = song.with_name("latin.md")
        bad.write_bytes('title: "Caf\u00e9"\nstatus: published\n'.encode("latin-1"))
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--format", "json"), 1)
        row = json.loads(self.capsys.readouterr().out)["bands"][0]
        self.assertEqual(row["entries"], 2)
        self.assertEqual(len(row["unreadable_entries"]), 1)
        self.assertIn("latin.md", row["unreadable_entries"][0])
        doc = (self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md").read_text(encoding="utf-8")
        self.assertIn("**latin** (unreadable)", doc)
        self.assertIn("chamber folk, close vocal", doc)  # the readable entry is still indexed
        # --check still works on the band (the fingerprint reads bytes).
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--check", "--format", "json"), 0)

    def test_entry_with_a_bom_reads_like_any_other(self):
        song = _band(self.tmp_path)
        song.write_text("\ufeff" + song.read_text(encoding="utf-8"), encoding="utf-8")
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        self.capsys.readouterr()
        doc = (self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md").read_text(encoding="utf-8")
        self.assertIn("**Harbor Lights** (published): chamber folk, close vocal", doc)

    # --- songbook_folder / band_profiles_folder from the module config ---

    def _moved(self):
        root = self.tmp_path
        song = root / "music" / "songs" / "paper-lanterns" / "harbor-lights.md"
        song.parent.mkdir(parents=True)
        song.write_text('title: "Harbor Lights"\nstatus: published\n\n'
                        "## Style Prompt\n\n```\nchamber folk, close vocal\n```\n", encoding="utf-8")
        (root / "music" / "bands").mkdir()
        (root / "music" / "bands" / "paper-lanterns.yaml").write_text(
            'name: "Paper Lanterns"\nreference_tracks:\n  - "Artist One — warm"\n', encoding="utf-8")
        install_resolver(root)
        (root / "_bmad" / "config.toml").write_text(
            '[modules.suno]\nsongbook_folder = "{project-root}/music/songs"\n'
            'band_profiles_folder = "{project-root}/music/bands"\n', encoding="utf-8")
        return song

    def test_configured_folders_are_indexed(self):
        song = self._moved()
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        row = json.loads(self.capsys.readouterr().out)["bands"][0]
        self.assertEqual((row["band"], row["entries"], row["profile_scanned"], row["influences"]),
                         ("paper-lanterns", 1, True, 1))
        doc = (self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md").read_text(encoding="utf-8")
        self.assertIn("chamber folk, close vocal", doc)
        self.assertIn("Artist One — warm", doc)
        # --check follows the same folders: current, then stale after an edit there.
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--check"), 0)
        song.write_text(song.read_text(encoding="utf-8") + "\nnew note\n", encoding="utf-8")
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--check"), 1)
        self.capsys.readouterr()
        # An unknown band names the configured folder.
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--band", "ghost"), 2)
        self.assertIn("music/songs/ghost/", self.capsys.readouterr().err)

    def test_default_folders_without_config(self):
        _band(self.tmp_path)
        songbook, profiles = mod.content_dirs(str(self.tmp_path))
        self.assertEqual((Path(songbook), Path(profiles)),
                         (self.tmp_path / "docs" / "songbook", self.tmp_path / "docs" / "band-profiles"))
        sources = mod.band_sources(str(self.tmp_path), "paper-lanterns", str(Path(songbook) / "paper-lanterns"))
        # The names a fingerprint is built from: unchanged, so existing indexes stay current.
        self.assertEqual([rel.replace("\\", "/") for rel, _ in sources],
                         ["docs/songbook/paper-lanterns/harbor-lights.md", "docs/band-profiles/paper-lanterns.yaml"])

    def test_unreadable_config_exits_2(self):
        _band(self.tmp_path)
        install_resolver(self.tmp_path)
        (self.tmp_path / "_bmad" / "config.toml").write_text("[modules.suno\nbroken", encoding="utf-8")
        with self.assertRaises(SystemExit) as exc:
            _run(self.capsys, str(self.tmp_path), "--format", "json")
        self.assertEqual(exc.exception.code, 2)
        self.assertIn("module config unreadable", self.capsys.readouterr().err)
        self.assertFalse((self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md").exists())

    def test_check_reports_missing_then_current_then_stale(self):
        song = _band(self.tmp_path)
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--check"), 1)
        self.assertIn("missing", self.capsys.readouterr().out)
        self.assertEqual(_run(self.capsys, str(self.tmp_path)), 0)
        self.capsys.readouterr()
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--check", "--format", "json"), 0)
        self.assertEqual(json.loads(self.capsys.readouterr().out)["bands"][0]["index"], "current")
        song.write_text(song.read_text(encoding="utf-8") + "\nnew note\n", encoding="utf-8")
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--check"), 1)
        self.assertIn("stale", self.capsys.readouterr().out)

    def test_check_writes_nothing(self):
        _band(self.tmp_path)
        _run(self.capsys, str(self.tmp_path), "--check")
        self.assertFalse((self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md").exists())

    def test_regeneration_keeps_text_outside_markers_and_stamps_time(self):
        _band(self.tmp_path)
        out = self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md"
        out.write_text("Owner note above.\n" + mod.AUTOGEN_START + "\nold\n" + mod.AUTOGEN_END + "\nBelow.\n",
                       encoding="utf-8")
        _run(self.capsys, str(self.tmp_path))
        doc = out.read_text(encoding="utf-8")
        self.assertTrue(doc.startswith("Owner note above.") and doc.rstrip().endswith("Below."))
        self.assertNotIn("\nold\n", doc)
        self.assertTrue(re.search(r"on \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", doc))
        self.assertIn("Artist One — warm", doc)

    def test_profile_yaml_error_is_recorded_rendered_and_exits_1(self):
        _band(self.tmp_path)
        _break_profile(self.tmp_path)
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--format", "json"), 1)
        band = json.loads(self.capsys.readouterr().out)["bands"][0]
        self.assertIn("paper-lanterns.yaml", band["profile_error"])
        doc = (self.tmp_path / "docs" / "paper-lanterns-genre-coverage.md").read_text(encoding="utf-8")
        self.assertTrue("PROFILE ERROR" in doc and "paper-lanterns.yaml" in doc)

    def test_check_fails_on_profile_error_even_when_fingerprint_matches(self):
        _band(self.tmp_path)
        _break_profile(self.tmp_path)
        _run(self.capsys, str(self.tmp_path))  # writes an index whose fingerprint matches
        self.capsys.readouterr()
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--check", "--format", "json"), 1)
        row = json.loads(self.capsys.readouterr().out)["bands"][0]
        self.assertTrue(row["index"] == "profile_error" and "paper-lanterns.yaml" in row["profile_error"])

    def test_good_profile_reports_no_error(self):
        _band(self.tmp_path)
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--format", "json"), 0)
        self.assertIsNone(json.loads(self.capsys.readouterr().out)["bands"][0]["profile_error"])

    def test_unknown_band_exits_2_with_reason(self):
        _band(self.tmp_path)
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--band", "paper-lantern", "--check"), 2)
        err = self.capsys.readouterr().err
        self.assertTrue("paper-lantern" in err and "paper-lanterns" in err)
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--band", "nope", "--format", "json"), 2)
        self.assertEqual(json.loads(self.capsys.readouterr().out)["status"], "error")

    def test_unknown_band_without_songbook_exits_2(self):
        self.assertEqual(_run(self.capsys, str(self.tmp_path), "--band", "ghost"), 2)


if __name__ == "__main__":
    unittest.main()
