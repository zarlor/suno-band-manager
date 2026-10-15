#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for check-memory-health.py (v7 sanctum)."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402

spec = spec_from_file_location(
    "check_memory_health",
    Path(__file__).parent.parent / "check-memory-health.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def _w(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _run(*argv):
    buf = io.StringIO()
    with patch.object(sys, "argv", ["check-memory-health.py", *argv]), redirect_stdout(buf):
        rc = mod.main()
    return rc, buf.getvalue()


class CheckMemoryHealthTests(TempDirMixin, unittest.TestCase):
    def test_healthy_sanctum(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        result = mod.check_health(sanctum, root)
        self.assertIs(result["maintenance_recommended"], False)
        self.assertIs(result["identity"]["over_threshold"], False)
        self.assertEqual(result["standing_too_long"], [])
        self.assertEqual(result["undistilled_raw"], [])
        self.assertIs(result["tending"]["tending_due"], False)

    def test_no_memory_md_or_index_checks(self):
        """v7 has no MEMORY.md token budget and no INDEX.md coverage check."""
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        _w(sanctum / "liner-notes.md", "an unlisted organic file is fine now")
        result = mod.check_health(sanctum, root)
        self.assertNotIn("index_unlisted", result)
        self.assertNotIn("files", result)
        self.assertIs(result["maintenance_recommended"], False)

    def test_identity_set_over_budget(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        _w(sanctum / "PERSONA.md", "p" * 30000)
        _w(sanctum / "CREED.md", "c" * 30000)  # ~15k tokens together
        result = mod.check_health(sanctum, root)
        self.assertGreater(result["identity"]["total_tokens_est"], 12000)
        self.assertIs(result["identity"]["over_threshold"], True)
        self.assertIn("identity set", result["recommendation"])

    def test_missing_identity_file_reported(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        (sanctum / "HOW-I-REMEMBER.md").unlink()
        result = mod.check_health(sanctum, root)
        self.assertEqual(result["identity"]["missing"], ["HOW-I-REMEMBER.md"])
        self.assertIs(result["maintenance_recommended"], True)

    def test_companion_files_owner_voice_and_preferences(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        _w(root / "docs" / "voice-context-sam.md", "v" * 1000)
        _w(root / "docs" / "voice-context-other.md", "o" * 100000)  # not the owner's: not measured
        _w(root / "docs" / "mac-preferences.md", "p" * 100000)  # ~25k tokens
        result = mod.check_health(sanctum, root)
        self.assertEqual(set(result["companions"]), {"docs/voice-context-sam.md", "docs/mac-preferences.md"})
        self.assertEqual(result["companions_over_budget"], ["docs/mac-preferences.md"])
        self.assertIn("compaction", result["recommendation"])

    def test_standing_file_longer_than_a_screen(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        _w(sanctum / "memory" / "work" / "parked.md", "- a parked thread\n" * 70)  # 70 lines
        _w(sanctum / "memory" / "owner" / "preferences.md", "x" * 4500 + "\n")  # few lines, many chars
        _w(sanctum / "memory" / "module" / "state.md", "- short\n" * 10)
        result = mod.check_health(sanctum, root)
        flagged = [f["file"] for f in result["standing_too_long"]]
        self.assertEqual(flagged, ["memory/owner/preferences.md", "memory/work/parked.md"])
        self.assertIn("appended to", result["recommendation"])

    def test_non_standing_folders_are_not_measured(self):
        """chronology/, sessions/, incidents/, the generated catalog/ and the disciplines
        are never flagged for length; a new kind of folder is."""
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        for rel in (
            "memory/chronology/2026-04-01-long-milestone.md",
            "memory/sessions/2026-10-02-long-session.md",
            "memory/incidents/workshop-capture.md",
            "memory/catalog/status.md",
            "memory/disciplines/thematic-discipline.md",
        ):
            _w(sanctum / rel, "line\n" * 200)
        _w(sanctum / "raw" / "2026-05-27-session-log.md", "---\nstatus: distilled\n---\n" + "x" * 50000)
        result = mod.check_health(sanctum, root)
        self.assertEqual(result["standing_too_long"], [])
        _w(sanctum / "memory" / "gear" / "studio.md", "line\n" * 61)
        _w(sanctum / "memory" / "pending.md", "p" * 4001)
        flagged = [f["file"] for f in mod.check_health(sanctum, root)["standing_too_long"]]
        self.assertEqual(flagged, ["memory/gear/studio.md", "memory/pending.md"])

    def test_undistilled_raw(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        _w(sanctum / "raw" / "2026-10-02-owner-poems.md", "---\nstatus: raw\ndistilled_to: []\n---\nwords\n")
        _w(sanctum / "raw" / "2026-09-01-session-log.md", "---\nstatus: distilled\n---\nold\n")
        result = mod.check_health(sanctum, root)
        self.assertEqual(result["undistilled_raw"], ["2026-10-02-owner-poems.md"])
        self.assertIs(result["maintenance_recommended"], True)

    def test_tending_due_after_three_notes(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        sessions = sanctum / "memory" / "sessions"
        _w(sessions / "2026-09-20-before.md", "old")  # before the stamp: not counted
        for day in ("2026-10-02", "2026-10-05"):
            _w(sessions / f"{day}-note.md", "n")
        self.assertIs(mod.check_health(sanctum, root)["tending"]["tending_due"], False)
        _w(sessions / "2026-10-09-note.md", "n")
        result = mod.check_health(sanctum, root)
        self.assertEqual(result["tending"]["session_notes_since"], 3)
        self.assertIs(result["tending"]["tending_due"], True)
        self.assertIn("tend memory", result["recommendation"])

    def test_never_tended_is_due(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        (sanctum / "memory" / ".tended").unlink()
        result = mod.check_health(sanctum, root)
        self.assertIsNone(result["tending"]["tended"])
        self.assertIs(result["tending"]["tending_due"], True)

    def test_cli_project_root_json(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        rc, out = _run(str(root), "--format", "json")
        self.assertEqual(rc, 0)
        result = json.loads(out)
        self.assertEqual(result["sidecar_format"], "v7")
        self.assertEqual(Path(result["sanctum_path"]), sanctum)

    def test_cli_text_format(self):
        v7_project = self.make_v7_project()
        root, _ = v7_project
        rc, out = _run(str(root), "--format", "text")
        self.assertEqual(rc, 0)
        self.assertIn("Identity set:", out)
        self.assertIn("Tended: 2026-10-01", out)

    def test_cli_accepts_sanctum_path_positionally(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        _w(root / "docs" / "mac-preferences.md", "prefs")
        rc, out = _run(str(sanctum))
        self.assertEqual(rc, 0)
        self.assertIn("docs/mac-preferences.md", json.loads(out)["companions"])

    def test_cli_sanctum_dir_override(self):
        v7_project = self.make_v7_project()
        root, sanctum = v7_project
        staging_dir = tempfile.TemporaryDirectory()
        self.addCleanup(staging_dir.cleanup)
        staging = Path(staging_dir.name) / "staging"
        staging.mkdir()
        for name in mod._seed.IDENTITY_FILES:
            _w(staging / name, "x")
        _w(staging / "raw" / "2026-10-10-x.md", "---\nstatus: raw\n---\n")
        rc, out = _run(str(root), "--sanctum-dir", str(staging))
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["undistilled_raw"], ["2026-10-10-x.md"])

    def test_cli_refuses_legacy_v2_store(self):
        tmp_path = self.tmp_path
        legacy = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
        for name in mod._seed.V2_SPINE:
            _w(legacy / name, "x")
        rc, out = _run(str(tmp_path))
        self.assertEqual(rc, 1)
        result = json.loads(out)
        self.assertEqual(result["sidecar_format"], "v2")
        self.assertIn("migrate-sanctum-to-v7.py", result["message"])

    def test_cli_absent_sanctum(self):
        tmp_path = self.tmp_path
        rc, out = _run(str(tmp_path))
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["sidecar_format"], "absent")


if __name__ == "__main__":
    unittest.main()
