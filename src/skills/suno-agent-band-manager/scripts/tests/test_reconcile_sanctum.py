#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for reconcile_sanctum.py"""

import io
import json
import os
import subprocess
import sys
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent))

spec = spec_from_file_location(
    "reconcile_sanctum",
    Path(__file__).parent.parent / "reconcile_sanctum.py",
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


class ReconcileSidecarTests(TempDirMixin, unittest.TestCase):
    def test_format_mtime_is_utc_string(self):
        s = mod._format_mtime(0.0)
        self.assertTrue(s.endswith("UTC"))
        self.assertTrue(s.startswith("1970-01-01"))

    def test_build_report_no_sidecar(self):
        tmp_path = self.tmp_path
        payload = mod.build_report(tmp_path)
        self.assertEqual(payload["status"], "no_sidecar")
        self.assertEqual(payload["newer_files"], [])
        self.assertIs(payload["needs_reconciliation"], False)

    def test_find_newer_docs_detects_fresh_file(self):
        tmp_path = self.tmp_path
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
        self.assertTrue(any("wip-new-song.md" in p for p in paths))

    def test_find_newer_docs_ignores_older_file(self):
        tmp_path = self.tmp_path
        index = _scaffold_sidecar(tmp_path)
        index_mtime = index.stat().st_mtime + 1000  # pretend index is very recent

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "old.md").write_text("old\n", encoding="utf-8")

        self.assertEqual(mod.find_newer_docs(tmp_path, index_mtime), [])

    def test_run_validator_skips_when_missing(self):
        tmp_path = self.tmp_path
        fake_dir = tmp_path / "nope"
        fake_dir.mkdir()
        self.enterContext(mock.patch.object(mod, "__file__", str(fake_dir / "reconcile_sanctum.py")))
        result = mod.run_validator(tmp_path)
        self.assertEqual(result["status"], "skipped")

    def test_build_report_flags_reconciliation_when_newer_file(self):
        tmp_path = self.tmp_path
        index = _scaffold_sidecar(tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        fresh = docs / "session.md"
        fresh.write_text("update\n", encoding="utf-8")
        import os
        future = index.stat().st_mtime + 50
        os.utime(fresh, (future, future))

        # Stub the validator so the test doesn't depend on validate_sanctum.py.
        self.enterContext(mock.patch.object(
            mod, "run_validator", lambda root, sanctum=None: {"status": "skipped"}
        ))

        payload = mod.build_report(tmp_path)
        self.assertIs(payload["needs_reconciliation"], True)
        self.assertEqual(payload["status"], "needs_reconciliation")

    def test_build_report_honors_sanctum_dir_override(self):
        """--sanctum-dir reads the store-freshness reference from a staging copy."""
        tmp_path = self.tmp_path
        staging = tmp_path / "staging-copy"
        memory = _scaffold_sidecar(tmp_path, staging)

        docs = tmp_path / "docs"
        docs.mkdir()
        fresh = docs / "session.md"
        fresh.write_text("update\n", encoding="utf-8")
        import os
        future = memory.stat().st_mtime + 50
        os.utime(fresh, (future, future))

        self.enterContext(mock.patch.object(
            mod, "run_validator", lambda root, sanctum=None: {"status": "skipped"}
        ))

        payload = mod.build_report(tmp_path, sanctum_dir=str(staging))
        self.assertEqual(payload["status"], "needs_reconciliation")
        self.assertTrue(payload["store_path"].endswith("memory/work/current.md"))

    def test_store_reference_is_newest_memory_file_but_not_the_catalog(self):
        tmp_path = self.tmp_path
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
        self.enterContext(mock.patch.object(mod, "run_validator", lambda root, sanctum=None: {"status": "skipped"}))
        payload = mod.build_report(tmp_path)
        self.assertEqual(payload["store_path"], "_bmad/memory/suno-agent-band-manager/memory/sessions/2026-10-02-note.md")
        self.assertEqual([f["path"] for f in payload["newer_files"]], ["docs/wip-x.md"])

    def test_legacy_store_is_not_read(self):
        """A v2 MEMORY.md at the legacy path is not the v7 store."""
        tmp_path = self.tmp_path
        legacy = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
        legacy.mkdir(parents=True)
        (legacy / "MEMORY.md").write_text("# old\n", encoding="utf-8")
        self.assertEqual(mod.build_report(tmp_path)["status"], "no_sidecar")

    def test_format_text_renders_clean_report(self):
        payload = {
            "status": "clean",
            "store_path": "_bmad/memory/suno-agent-band-manager/memory/work/current.md",
            "store_mtime": "2026-06-18 00:00:00 UTC",
            "newer_files": [],
            "validator": {"status": "pass", "findings": []},
            "needs_reconciliation": False,
        }
        text = mod.format_text(payload)
        self.assertIn("Sanctum Reconciliation Report", text)
        self.assertIn("CLEAN", text)

    def test_run_validator_launches_through_uv_when_available(self):
        """validate_sanctum.py needs PyYAML; `uv run` provisions it, else this interpreter."""
        tmp_path = self.tmp_path
        import json as _json
        import subprocess

        seen = []

        def fake_run(cmd, **kwargs):
            seen.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout=_json.dumps({"status": "pass"}), stderr="")

        self.enterContext(mock.patch.object(mod.subprocess, "run", fake_run))
        self.enterContext(mock.patch.object(mod.shutil, "which", lambda name: "/usr/bin/uv"))
        self.assertEqual(mod.run_validator(tmp_path, "/staging")["status"], "pass")
        self.assertEqual(seen[-1][:4], ["/usr/bin/uv", "run", "-q", "--script"])
        self.assertEqual(seen[-1][-2:], ["--sanctum-dir", "/staging"])
        self.enterContext(mock.patch.object(mod.shutil, "which", lambda name: None))
        mod.run_validator(tmp_path)
        self.assertEqual(seen[-1][0], sys.executable)

    # --- validator findings and failures decide the report (not only newer docs) ---

    def _stub_validator(self, result):
        self.enterContext(mock.patch.object(mod, "run_validator", lambda root, sanctum=None: result))

    def _main(self, *argv):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["reconcile_sanctum.py", *argv]), redirect_stdout(out):
            code = mod.main()
        return code, out.getvalue()

    def test_validator_error_finding_alone_needs_reconciliation(self):
        _scaffold_sidecar(self.tmp_path)
        self._stub_validator({"status": "fail", "findings": [
            {"severity": "error", "category": "index_drift", "path": "x", "message": "m"}]})
        payload = mod.build_report(self.tmp_path)
        self.assertEqual(payload["newer_files"], [])
        self.assertIs(payload["needs_reconciliation"], True)
        self.assertEqual(payload["status"], "needs_reconciliation")
        code, out = self._main(str(self.tmp_path), "--format", "json")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["validator"]["findings"][0]["category"], "index_drift")

    def test_validator_warnings_alone_stay_clean(self):
        _scaffold_sidecar(self.tmp_path)
        self._stub_validator({"status": "pass", "findings": [
            {"severity": "warning", "category": "audio_missing", "path": "x", "message": "m"}]})
        payload = mod.build_report(self.tmp_path)
        self.assertIs(payload["needs_reconciliation"], False)
        self.assertEqual(self._main(str(self.tmp_path))[0], 0)

    def test_validator_that_reports_an_error_is_not_a_clean_report(self):
        _scaffold_sidecar(self.tmp_path)
        self._stub_validator({"status": "error", "message": "PyYAML required."})
        payload = mod.build_report(self.tmp_path)
        self.assertIs(payload["needs_reconciliation"], True)
        self.assertEqual(payload["status"], "needs_reconciliation")
        code, out = self._main(str(self.tmp_path))
        self.assertEqual(code, 1)
        self.assertIn("nothing was validated", out)
        self.assertIn("PyYAML required.", out)
        self.assertNotIn("CLEAN", out)

    def test_validator_that_crashes_is_not_a_clean_report(self):
        _scaffold_sidecar(self.tmp_path)

        def crashed(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 2, stdout="", stderr="Traceback (most recent call last): boom")

        self.enterContext(mock.patch.object(mod.subprocess, "run", crashed))
        payload = mod.build_report(self.tmp_path)
        self.assertEqual(payload["validator"]["status"], "error")
        self.assertIn("exited 2", payload["validator"]["reason"])
        self.assertIs(payload["needs_reconciliation"], True)
        self.assertEqual(self._main(str(self.tmp_path), "--format", "json")[0], 1)

    def test_validator_output_that_is_not_json_is_not_a_clean_report(self):
        _scaffold_sidecar(self.tmp_path)
        for stdout in ("not json at all", "[1, 2]"):
            with self.subTest(stdout=stdout):
                self.enterContext(mock.patch.object(
                    mod.subprocess, "run",
                    lambda cmd, _out=stdout, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=_out, stderr="")))
                payload = mod.build_report(self.tmp_path)
                self.assertEqual(payload["validator"]["status"], "error")
                self.assertIs(payload["needs_reconciliation"], True)

    def test_real_validator_hand_off_surfaces_catalog_drift(self):
        """No stub: reconcile launches validate_sanctum.py and reads its JSON. A ghost
        entry in the catalog is an index_drift error, so the report is not clean."""
        current = _scaffold_sidecar(self.tmp_path)
        sanctum = self.tmp_path.joinpath(*V7_REL)
        catalog = sanctum / "memory" / "catalog" / "recently-published.md"
        catalog.parent.mkdir(parents=True)
        catalog.write_text(
            "# Recently Published\n\n<!-- derived:recently-published:start -->\n\n"
            "- **Ghost Song** (2026-01-15, PUBLISHED) — not in songbook.\n\n"
            "<!-- derived:recently-published:end -->\n", encoding="utf-8")
        song = self.tmp_path / "docs" / "songbook" / "paper-lanterns" / "harbor-lights.md"
        song.parent.mkdir(parents=True)
        song.write_text('---\ntitle: "Harbor Lights"\nband_profile: paper-lanterns\nstatus: wip\n---\n\nbody\n',
                        encoding="utf-8")
        # The store is newer than the doc, so only the validator can raise the flag.
        later = time.time() + 100
        os.utime(current, (later, later))
        # This interpreter has PyYAML (the suite runs with it); no network needed.
        self.enterContext(mock.patch.object(mod.shutil, "which", lambda name: None))
        payload = mod.build_report(self.tmp_path)
        self.assertEqual(payload["newer_files"], [])
        self.assertEqual(payload["validator"]["status"], "fail", payload["validator"])
        drift = [f for f in payload["validator"]["findings"] if f["category"] == "index_drift"]
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0]["severity"], "error")
        self.assertIn("Ghost Song", drift[0]["message"])
        self.assertIs(payload["needs_reconciliation"], True)
        self.assertEqual(self._main(str(self.tmp_path), "--format", "json")[0], 1)

    def test_real_validator_hand_off_passes_the_sanctum_override(self):
        staging = self.tmp_path / "staging-copy"
        current = _scaffold_sidecar(self.tmp_path, staging)
        (staging / "memory" / "catalog").mkdir(parents=True)
        (staging / "memory" / "catalog" / "recently-published.md").write_text(
            "# Recently Published\n\n- **Ghost Song** (2026-01-15, PUBLISHED) — x.\n", encoding="utf-8")
        (self.tmp_path / "docs").mkdir()
        later = time.time() + 100
        os.utime(current, (later, later))
        self.enterContext(mock.patch.object(mod.shutil, "which", lambda name: None))
        payload = mod.build_report(self.tmp_path, sanctum_dir=str(staging))
        self.assertEqual([f["category"] for f in payload["validator"]["findings"]], ["index_drift"])

    # --- docs that arrived with an edit time older than the store ---

    def test_unpacked_doc_with_an_old_edit_time_is_listed_as_arrived(self):
        """`tar xzf` keeps the other machine's edit time. A doc edited there before
        this machine's last memory write is not newer by mtime, yet it landed after."""
        current = _scaffold_sidecar(self.tmp_path)
        now = time.time()
        os.utime(current, (now - 3600, now - 3600))  # the store: written an hour ago
        docs = self.tmp_path / "docs"
        docs.mkdir()
        for name, age in (("wip-older.md", 9000), ("wip-recent.md", 7200)):
            doc = docs / name
            doc.write_text("arrived\n", encoding="utf-8")
            os.utime(doc, (now - age, now - age))  # edited before the store; written to disk just now
        self._stub_validator({"status": "pass", "findings": []})
        payload = mod.build_report(self.tmp_path)
        self.assertEqual(payload["newer_files"], [])
        self.assertEqual(payload["arrived_count"], 2)
        # Most recently edited first.
        self.assertEqual([Path(f["path"]).name for f in payload["arrived_files"]], ["wip-recent.md", "wip-older.md"])
        # It informs; it does not by itself make the report "needs reconciliation".
        self.assertIs(payload["needs_reconciliation"], False)
        text = mod.format_text(payload)
        self.assertIn("arrived after the store was last written", text)
        self.assertIn("wip-recent.md", text)

    def test_arrived_list_is_capped_and_counted(self):
        current = _scaffold_sidecar(self.tmp_path)
        now = time.time()
        os.utime(current, (now - 3600, now - 3600))
        docs = self.tmp_path / "docs"
        docs.mkdir()
        for i in range(mod.ARRIVED_LIMIT + 5):
            doc = docs / f"wip-{i:02d}.md"
            doc.write_text("x\n", encoding="utf-8")
            os.utime(doc, (now - 7200 - i, now - 7200 - i))
        self._stub_validator({"status": "pass", "findings": []})
        payload = mod.build_report(self.tmp_path)
        self.assertEqual(payload["arrived_count"], mod.ARRIVED_LIMIT + 5)
        self.assertEqual(len(payload["arrived_files"]), mod.ARRIVED_LIMIT)
        self.assertEqual(Path(payload["arrived_files"][0]["path"]).name, "wip-00.md")

    def test_doc_newer_by_edit_time_is_in_newer_files_not_arrived(self):
        current = _scaffold_sidecar(self.tmp_path)
        docs = self.tmp_path / "docs"
        docs.mkdir()
        fresh = docs / "wip-new.md"
        fresh.write_text("x\n", encoding="utf-8")
        future = current.stat().st_mtime + 50
        os.utime(fresh, (future, future))
        self._stub_validator({"status": "pass", "findings": []})
        payload = mod.build_report(self.tmp_path)
        self.assertEqual([Path(f["path"]).name for f in payload["newer_files"]], ["wip-new.md"])
        self.assertEqual((payload["arrived_count"], payload["arrived_files"]), (0, []))

    def test_no_sidecar_report_has_the_same_keys(self):
        payload = mod.build_report(self.tmp_path)
        self.assertEqual((payload["arrived_count"], payload["arrived_files"]), (0, []))


if __name__ == "__main__":
    unittest.main()
