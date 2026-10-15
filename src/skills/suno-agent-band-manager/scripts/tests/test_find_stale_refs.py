#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for find-stale-refs.py (fixtures are invented, de-identified)."""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).parent.parent
spec = spec_from_file_location("find_stale_refs", SCRIPTS_DIR / "find-stale-refs.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402


def run_main(argv):
    """Run mod.main() under `argv`, capturing stdout: (exit code, stdout)."""
    out = io.StringIO()
    with patch.object(sys, "argv", argv), redirect_stdout(out):
        code = mod.main()
    return code, out.getvalue()


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


class FindStaleRefsTests(TempDirMixin, unittest.TestCase):
    def test_hits_cover_the_defined_set_only(self):
        report = mod.scan(_project(self.tmp_path), "Harbor Lights")
        files = {h["file"] for h in report["hits"]}
        self.assertIn("docs/songbook/paper-lanterns/harbor-lights.md", files)
        self.assertIn("docs/paper-lanterns-playlist.yaml", files)  # casefold hit
        self.assertIn("docs/notes/extra.md", files)  # via the Companion Files table
        self.assertIn(f"{SANCTUM}/memory/work/current.md", files)
        self.assertIn(f"{SANCTUM}/memory/catalog/recently-published.md", files)
        self.assertIn(f"{SANCTUM}/memory/chronology/2026-01-01-first-light.md", files)
        self.assertIn(f"{SANCTUM}/memory/sessions/2026-01-02-note.md", files)
        self.assertNotIn("docs/unrelated.md", files)
        self.assertFalse(any("/raw/" in f for f in files))
        self.assertFalse(any("_bmad/_memory" in f for f in files))

    def test_match_kinds(self):
        report = mod.scan(_project(self.tmp_path), "Harbor Lights")
        kinds = {(h["file"], h["match_kind"]) for h in report["hits"]}
        self.assertIn(("docs/paper-lanterns-playlist.yaml", "casefold"), kinds)
        self.assertIn(("docs/songbook/paper-lanterns/harbor-lights.md", "exact"), kinds)

    def test_subtitle_match_when_old_has_one(self):
        report = mod.scan(_project(self.tmp_path), "Harbor Lights (Night Mix)")
        kinds = {h["match_kind"] for h in report["hits"]}
        self.assertIn("exact", kinds)
        self.assertIn("subtitle", kinds)

    def test_partial_only_on_request(self):
        root = _project(self.tmp_path)
        _w(root, "docs/wip-dock.md", "# Dock\nharbor at dusk\n")
        self.assertFalse(any(h["match_kind"] == "partial" for h in mod.scan(root, "Harbor Lights")["hits"]))
        partial = [h for h in mod.scan(root, "Harbor Lights", partial=True)["hits"]
                   if h["match_kind"] == "partial"]
        self.assertEqual([h["file"] for h in partial], ["docs/wip-dock.md"])

    def test_raw_included_on_request(self):
        report = mod.scan(_project(self.tmp_path), "Harbor Lights", include_raw=True)
        files = {h["file"] for h in report["hits"]}
        self.assertIn(f"{SANCTUM}/raw/2026-01-01-session-log.md", files)
        self.assertIn(f"{SANCTUM}/raw/2026-01-01-collection-of-writings-extracted.txt", files)
        self.assertIs(report["raw_included"], True)

    def test_cli_include_sessions_is_an_alias_for_include_raw(self):
        root = _project(self.tmp_path)
        for flag in ("--include-raw", "--include-sessions"):
            code, stdout = run_main(["find-stale-refs.py", str(root), "--old", "Harbor Lights", flag])
            self.assertEqual(code, 0)
            out = json.loads(stdout)
            self.assertTrue(any("/raw/" in h["file"] for h in out["hits"]))

    def test_cli_sanctum_dir_override(self):
        root = _project(self.tmp_path)
        _w(root, "staging/memory/work/current.md", "Harbor Lights staged\n")
        code, stdout = run_main([
            "find-stale-refs.py", str(root), "--old", "Harbor Lights", "--sanctum-dir", str(root / "staging")])
        self.assertEqual(code, 0)
        files = {h["file"] for h in json.loads(stdout)["hits"]}
        self.assertIn("staging/memory/work/current.md", files)
        self.assertFalse(any(f.startswith(SANCTUM) for f in files))

    def test_new_value_adds_preview(self):
        report = mod.scan(_project(self.tmp_path), "Harbor Lights", new="Lantern Light")
        exact = next(h for h in report["hits"] if h["match_kind"] == "exact")
        self.assertIn("Lantern Light", exact["preview"])

    def test_missing_targets_listed(self):
        report = mod.scan(_project(self.tmp_path), None)
        self.assertEqual(report["hits"], [])
        self.assertEqual(report["missing_targets"], [
            {"file": "docs/songbook/paper-lanterns/harbor-lights.md", "line": 5, "target": "docs/wip-dock.md"}])

    def test_same_input_same_output(self):
        root = _project(self.tmp_path)
        self.assertEqual(mod.scan(root, "Harbor Lights"), mod.scan(root, "Harbor Lights"))

    def test_cli_requires_old_or_paths_only(self):
        code, stdout = run_main(["find-stale-refs.py", str(self.tmp_path)])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stdout)["status"], "error")

    def test_cli_json(self):
        root = _project(self.tmp_path)
        code, stdout = run_main(["find-stale-refs.py", str(root), "--old", "Harbor Lights"])
        self.assertEqual(code, 0)
        out = json.loads(stdout)
        self.assertEqual(out["status"], "ok")
        self.assertGreaterEqual(out["hit_count"], 4)


if __name__ == "__main__":
    unittest.main()
