#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for migrate-sidecar-to-v2.py.

Uses a small SYNTHETIC fixture sidecar built in tmp_path — never the real data.
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402

spec = spec_from_file_location("migrate_sidecar", SCRIPTS_DIR / "migrate-sidecar-to-v2.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


SYNTH_INDEX = """# Mac — Session Index

## User Preferences

- Name: Fixtureville
- Suno tier: Pro

## Default Exclusions

- Rap

## Current Work — Session 2026-06-10 (synthetic active dig)

Working on the synthetic song. Round 1 swing on the table.

## Prior Work — Session 2026-06-09 (synthetic earlier session)

Earlier synthetic work. Published a synthetic track.

## Prior Work — Session 2026-06-09 morning (same-date second block)

A second block sharing the 2026-06-09 date — should append to one file.

## Prior Work — Synthetic publish + session 7 (2026-06-01 evening)

Date lives in parentheses, not right after "Session". Must still resolve.

## Recently Published

<!-- derived:recently-published:start -->

- **Synthetic Song** (2026-06-09, PUBLISHED) — a fixture track.

<!-- derived:recently-published:end -->

## Catalog Status

<!-- derived:catalog-status:start -->

- **Fixture Band:** **1 published track** — Synthetic Song.

<!-- derived:catalog-status:end -->

## Module State

- Latest release: v9.9.9 (synthetic).

## Pending / Parked Work

- Synthetic parked idea.

## Session History (recent)

- 2026-06-10: synthetic session note.
"""


def make_synthetic_project(tmp_path):
    """Build a synthetic project with a fixture sidecar + config."""
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "config.toml").write_text('[modules.suno]\nsuno_tier = "pro"\n')
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "voice-context-fixtureville.md").write_text("# voice\n")
    sanctum = bmad / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    (sanctum / "index.md").write_text(SYNTH_INDEX)
    # Bespoke preserved files.
    (sanctum / "patterns.md").write_text("# patterns\nsynthetic patterns body\n")
    (sanctum / "chronology.md").write_text("# chronology\nsynthetic timeline\n")
    (sanctum / "access-boundaries.md").write_text("# boundaries\nsynthetic\n")
    (sanctum / "_collection_extracted.txt").write_text("raw extract\n")
    (sanctum / "_collection_layout.txt").write_text("raw layout\n")
    (sanctum / "_collection_reflow.txt").write_text("raw reflow\n")
    return tmp_path, sanctum


def run_migrate(tmp_path, sanctum):
    out_dir = tmp_path / "_bmad" / "_memory" / ".sidecar-v2-staging"
    result = mod.migrate(tmp_path, sanctum, out_dir, SKILL_DIR)
    return out_dir, result


# --- section parsing ---


# --- migration output ---


# --- verify ---


# --- in-place upgrade (backup → migrate → verify → swap, abort-on-loss) ---


class MigrateSidecarToV2Tests(TempDirMixin, unittest.TestCase):
    def test_split_sections_counts(self):
        preamble, sections = mod.split_sections(SYNTH_INDEX)
        self.assertTrue(preamble.strip().startswith("# Mac"))
        # 4 session + 5 non-session (Prefs, Exclusions, Recently, Catalog, Module,
        # Pending, Session History) — count headings.
        headings = [mod.heading_of(s) for s in sections]
        self.assertTrue(any(h.startswith("## Current Work") for h in headings))

    def test_session_classification(self):
        _, sections = mod.split_sections(SYNTH_INDEX)
        session = [s for s in sections if mod.is_session_section(s)]
        self.assertEqual(len(session), 4)

    def test_session_date_extraction_paren_form(self):
        section = "## Prior Work — Synthetic publish + session 7 (2026-06-01 evening)\nbody\n"
        self.assertEqual(mod.session_date(section), "2026-06-01")

    def test_migrate_writes_only_to_out_dir(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        src_before = {p: p.read_bytes() for p in sanctum.iterdir() if p.is_file()}
        out_dir, result = run_migrate(tmp_path, sanctum)
        self.assertEqual(result["status"], "migrated")
        # Source untouched.
        src_after = {p: p.read_bytes() for p in sanctum.iterdir() if p.is_file()}
        self.assertEqual(src_before, src_after)

    def test_same_date_sessions_grouped(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, result = run_migrate(tmp_path, sanctum)
        # 4 blocks, but two share 2026-06-09 → 3 files.
        self.assertEqual(result["session_blocks_found"], 4)
        self.assertEqual(result["session_files_written"], 3)
        sessions = sorted(p.name for p in (out_dir / "sessions").glob("*.md"))
        self.assertEqual(sessions, ["2026-06-01.md", "2026-06-09.md", "2026-06-10.md"])
        # The same-date file holds both blocks.
        body = (out_dir / "sessions" / "2026-06-09.md").read_text()
        self.assertIn("synthetic earlier session", body)
        self.assertIn("same-date second block", body)

    def test_derived_markers_preserved_in_memory(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, _ = run_migrate(tmp_path, sanctum)
        memory = (out_dir / "MEMORY.md").read_text()
        for marker in ("recently-published", "catalog-status"):
            self.assertIn(f"<!-- derived:{marker}:start -->", memory)
            self.assertIn(f"<!-- derived:{marker}:end -->", memory)
        # The derived content rode along verbatim.
        self.assertIn("Synthetic Song", memory)
        self.assertIn("Fixture Band", memory)

    def test_non_session_content_in_memory(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, _ = run_migrate(tmp_path, sanctum)
        memory = (out_dir / "MEMORY.md").read_text()
        self.assertIn("Synthetic parked idea", memory)
        self.assertIn("v9.9.9 (synthetic)", memory)
        # Session narrative is NOT in MEMORY (only the pointer block).
        self.assertNotIn("Round 1 swing on the table", memory)

    def test_preserved_files_byte_identical(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, result = run_migrate(tmp_path, sanctum)
        for name in mod.PRESERVED_FILES:
            self.assertEqual((sanctum / name).read_bytes(), (out_dir / name).read_bytes())
        self.assertEqual(set(result["preserved_files"]), set(mod.PRESERVED_FILES))

    def test_template_seeded_files_present(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, _ = run_migrate(tmp_path, sanctum)
        for name in ("INDEX.md", "PERSONA.md", "CREED.md", "BOND.md", "PULSE.md", "CAPABILITIES.md"):
            self.assertTrue((out_dir / name).exists(), f"missing {name}")
        # The whole v2 spine and no v7 marker: the output classifies as v2.
        self.assertTrue(all((out_dir / n).is_file() for n in mod._seed.V2_SPINE))
        self.assertFalse((out_dir / "HOW-I-REMEMBER.md").exists())
        self.assertEqual(mod.sidecar_state(out_dir), "v2")
        # The CREED template's Dominion placeholder is filled.
        creed = (out_dir / "CREED.md").read_text()
        self.assertNotIn("{dominion}", creed)
        self.assertIn("### Read Access", creed)
        # Variables substituted in seeded files.
        self.assertNotIn("{user_name}", (out_dir / "PERSONA.md").read_text())
        self.assertIn("Fixtureville", (out_dir / "PERSONA.md").read_text())

    def test_creed_shards_produced(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, _ = run_migrate(tmp_path, sanctum)
        # Shards seeded from the real skill creed.md.
        self.assertTrue((out_dir / "creed-package-assembly.md").exists())
        self.assertTrue((out_dir / "creed-incident-log.md").exists())
        # Package Assembly content landed in its shard.
        self.assertIn("Package Assembly Rule", (out_dir / "creed-package-assembly.md").read_text())

    def test_rerun_is_clean(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, _ = run_migrate(tmp_path, sanctum)
        # Drop a stray file, rerun, confirm it's gone (wipe-and-rebuild).
        (out_dir / "stray.txt").write_text("x")
        out_dir2, _ = run_migrate(tmp_path, sanctum)
        self.assertFalse((out_dir2 / "stray.txt").exists())

    def test_verify_passes_on_clean_migration(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, _ = run_migrate(tmp_path, sanctum)
        report = mod.verify(sanctum, out_dir)
        self.assertEqual(report["status"], "pass", report["findings"])
        self.assertEqual(report["session_blocks_found"], 4)
        self.assertEqual(report["session_files_written"], 3)
        self.assertIs(report["session_dates_match"], True)
        self.assertIs(report["derived_markers"]["recently-published"], True)
        self.assertIs(report["derived_markers"]["catalog-status"], True)
        self.assertIs(report["char_accounting"]["all_sections_present"], True)
        self.assertTrue(all(report["preserved_files_byte_identical"].values()))

    def test_verify_detects_dropped_content(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, _ = run_migrate(tmp_path, sanctum)
        # Corrupt MEMORY.md by deleting the parked-work content.
        memory = out_dir / "MEMORY.md"
        text = memory.read_text().replace("Synthetic parked idea", "")
        memory.write_text(text)
        report = mod.verify(sanctum, out_dir)
        self.assertEqual(report["status"], "fail")
        self.assertIs(report["char_accounting"]["all_sections_present"], False)

    def test_sidecar_state_classification(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path = self.tmp_path
        tmp_path2, sanctum = synthetic_project
        # v1: index.md present, no v2 markers.
        self.assertEqual(mod.sidecar_state(sanctum), "v1")
        # A partial v2 spine (MEMORY.md beside the old index.md) is damaged:
        # never migrated over, never loaded as if whole.
        (sanctum / "MEMORY.md").write_text("# memory\n")
        self.assertEqual(mod.sidecar_state(sanctum), "damaged")
        # absent: dir doesn't exist.
        self.assertEqual(mod.sidecar_state(tmp_path / "nope" / "band-manager-sidecar"), "absent")
        # An empty dir counts as absent (nothing to migrate, nothing lost).
        empty = tmp_path / "empty"
        empty.mkdir()
        self.assertEqual(mod.sidecar_state(empty), "absent")
        # damaged: dir has content, neither marker.
        damaged = tmp_path / "damaged"
        damaged.mkdir()
        (damaged / "stray.txt").write_text("junk\n")
        self.assertEqual(mod.sidecar_state(damaged), "damaged")

    def test_in_place_migrates_v1_with_backup_and_swap(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        # Capture the source content before the upgrade so we can prove backup fidelity.
        src_index = (sanctum / "index.md").read_bytes()

        result = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
        self.assertEqual(result["status"], "migrated", result)

        # Live location is now v2.
        self.assertTrue((sanctum / "MEMORY.md").is_file())
        self.assertEqual(mod.sidecar_state(sanctum), "v2")
        # The old index.md content store is gone from the live location (migrated).
        self.assertFalse((sanctum / "index.md").exists())

        # Backup dir + tarball both exist.
        backup_dir = Path(result["backup_path"])
        backup_tarball = Path(result["backup_tarball"])
        self.assertTrue(backup_dir.is_dir())
        self.assertTrue(backup_tarball.is_file())
        self.assertIn("sidecar-backup-pre-v2-", backup_dir.name)
        # Backup is a faithful copy of the ORIGINAL v1 content.
        self.assertEqual((backup_dir / "index.md").read_bytes(), src_index)

        # Verify rode along and passed; content is present in the new MEMORY.md.
        self.assertEqual(result["verify"]["status"], "pass")
        self.assertIs(result["verify"]["char_accounting"]["all_sections_present"], True)
        memory = (sanctum / "MEMORY.md").read_text()
        self.assertIn("Synthetic parked idea", memory)
        self.assertIn("Fixture Band", memory)
        # Session narrative migrated into sessions/ (not lost).
        self.assertTrue(result["session_files"])
        self.assertTrue((sanctum / "sessions" / "2026-06-10.md").is_file())

    def test_in_place_already_v2_is_noop(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        # First upgrade brings it to v2.
        first = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
        self.assertEqual(first["status"], "migrated")
        memory_before = (sanctum / "MEMORY.md").read_bytes()

        # Second run is a clean no-op — no new backup, sanctum untouched.
        backups_before = list((tmp_path / "_bmad" / "_memory").glob(".sidecar-backup-pre-v2-*"))
        second = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
        self.assertEqual(second["status"], "already-v2")
        backups_after = list((tmp_path / "_bmad" / "_memory").glob(".sidecar-backup-pre-v2-*"))
        self.assertEqual(len(backups_after), len(backups_before))
        self.assertEqual((sanctum / "MEMORY.md").read_bytes(), memory_before)

    def test_in_place_no_sidecar_is_noop(self):
        tmp_path = self.tmp_path
        bmad = tmp_path / "_bmad"
        bmad.mkdir()
        (bmad / "config.yaml").write_text("user_name: Nobody\n")
        sanctum = bmad / "_memory" / "band-manager-sidecar"  # never created
        result = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
        self.assertEqual(result["status"], "no-sidecar")
        self.assertFalse(sanctum.exists())

    def test_in_place_aborts_on_content_loss(self):
        """If verify can't account for all content, ABORT: no swap, original intact."""
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        src_before = {p.name: p.read_bytes() for p in sanctum.iterdir() if p.is_file()}

        # Force a content-loss verify by patching verify() to report a drop.
        def fake_verify(sanctum_path, out_dir):
            return {
                "status": "fail",
                "findings": ["forced content loss for test"],
                "char_accounting": {"all_sections_present": False, "dropped_sections": ["X"]},
            }

        with patch.object(mod, "verify", fake_verify):
            result = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)

        self.assertEqual(result["status"], "blocked")
        self.assertIn("verify did not pass", result["reason"])
        # Original sidecar is STILL v1 and byte-identical — nothing swapped.
        self.assertEqual(mod.sidecar_state(sanctum), "v1")
        src_after = {p.name: p.read_bytes() for p in sanctum.iterdir() if p.is_file()}
        self.assertEqual(src_before, src_after)
        # The backup was still made (backup-first) and is reported.
        self.assertTrue(Path(result["backup_path"]).is_dir())
        # No staging dir left lying around.
        staging = list((tmp_path / "_bmad" / "_memory").glob(".sidecar-v2-staging-*"))
        self.assertEqual(staging, [])

    def test_in_place_blocks_damaged_sidecar(self):
        """A damaged sidecar (no index.md, no MEMORY.md) is blocked, not migrated."""
        tmp_path = self.tmp_path
        bmad = tmp_path / "_bmad"
        bmad.mkdir()
        (bmad / "config.yaml").write_text("user_name: Nobody\n")
        sanctum = bmad / "_memory" / "band-manager-sidecar"
        sanctum.mkdir(parents=True)
        (sanctum / "stray.txt").write_text("junk\n")
        result = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("re-scaffold", result["reason"])

    def test_in_place_staging_mode_still_works(self):
        """The original staging-mode migrate() is unchanged by the in-place addition."""
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, result = run_migrate(tmp_path, sanctum)
        self.assertEqual(result["status"], "migrated")
        # Source untouched by staging mode.
        self.assertTrue((sanctum / "index.md").is_file())
        self.assertEqual(mod.sidecar_state(sanctum), "v1")
        self.assertTrue((out_dir / "MEMORY.md").is_file())

    def test_migration_index_lists_preserved_files_and_persona_marks_migration(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, result = run_migrate(tmp_path, sanctum)
        index = (out_dir / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("`patterns.md`", index)
        self.assertIn("`chronology.md`", index)
        self.assertIn("`_collection_*.txt`", index)
        persona = (out_dir / "PERSONA.md").read_text(encoding="utf-8")
        self.assertIn("Woke into the v2 sanctum", persona)
        self.assertNotIn("First Breath.", persona)

    def test_migration_seeds_access_boundaries_when_old_store_had_none(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        (sanctum / "access-boundaries.md").unlink()
        out_dir, result = run_migrate(tmp_path, sanctum)
        text = (out_dir / "access-boundaries.md").read_text(encoding="utf-8")
        self.assertIn("Access Boundaries for Mac", text)
        # The full spine exists, so the migrated sanctum classifies as v2.
        self.assertEqual(mod.sidecar_state(out_dir), "v2")

    def test_migration_capabilities_has_builtin_roster(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, _ = run_migrate(tmp_path, sanctum)
        caps = (out_dir / "CAPABILITIES.md").read_text(encoding="utf-8")
        self.assertIn("The menu the wake prints", caps)
        self.assertIn("## Learned", caps)

    def test_v1_detected_on_case_insensitive_filesystem(self):
        """A lowercase index.md must not read as the v2 INDEX.md on APFS/NTFS."""
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        real_is_file = Path.is_file

        def insensitive_is_file(self):
            if self.parent == sanctum:
                return any(p.name.lower() == self.name.lower() for p in sanctum.iterdir())
            return real_is_file(self)

        with patch.object(Path, "is_file", insensitive_is_file):
            state = mod.sidecar_state(sanctum)
        self.assertEqual(state, "v1")

    def test_verify_flags_an_incomplete_v2_spine(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, _ = run_migrate(tmp_path, sanctum)
        (out_dir / "INDEX.md").unlink()
        report = mod.verify(sanctum, out_dir)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["missing_spine"], ["INDEX.md"])

    def test_in_place_already_v7_is_noop(self):
        tmp_path = self.tmp_path
        sanctum = tmp_path / "store"
        for name in mod._seed.IDENTITY_FILES:
            (sanctum / name).parent.mkdir(parents=True, exist_ok=True)
            (sanctum / name).write_text("x\n")
        result = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
        self.assertEqual(result["status"], "already-v7")

    def test_default_paths_are_the_legacy_store(self):
        """The CLI reads the v1 store at the legacy path and stages beside it."""
        synthetic_project = make_synthetic_project(self.tmp_path)
        import json
        tmp_path, sanctum = synthetic_project
        self.assertEqual(sanctum, mod._seed.legacy_sanctum_dir(tmp_path))
        buf = io.StringIO()
        with patch.object(sys, "argv", ["migrate-sidecar-to-v2.py", "--project-root", str(tmp_path), "--format", "json"]), \
                redirect_stdout(buf):
            rc = mod.main()
        self.assertEqual(rc, 0)
        out = json.loads(buf.getvalue())
        self.assertEqual(out["status"], "migrated")
        self.assertEqual(Path(out["out_dir"]), tmp_path / "_bmad" / "_memory" / ".sidecar-v2-staging")

    def test_v1_reaches_v7_through_both_hops(self):
        """v1 -> v2 here, then migrate-sanctum-to-v7.py converts the result to a v7 sanctum."""
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        (sanctum / "access-boundaries.md").write_text(
            "# Access Boundaries\n\n## Read Access\n\n- `docs/synthetic/` — fixture\n\n"
            "## Write Access\n\n- `docs/wip-*.md` — fragments\n\n## Deny Zones\n\n- `src/`\n"
        )
        self.assertEqual(mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)["status"], "migrated")

        v7_spec = spec_from_file_location("migrate_to_v7", SCRIPTS_DIR / "migrate-sanctum-to-v7.py")
        v7 = module_from_spec(v7_spec)
        v7_spec.loader.exec_module(v7)
        plan = v7.build_plan(sanctum, SKILL_DIR, "2026-10-15")
        target = mod._seed.sanctum_dir(tmp_path)
        v7.write(plan, target)

        self.assertEqual(mod._seed.classify_sanctum(target)["sidecar_format"], "v7")
        located, state = mod._seed.locate_sanctum(tmp_path)
        self.assertEqual(located, target)
        self.assertEqual(state["sidecar_format"], "v7")
        parked = (target / "memory" / "work" / "parked.md").read_text()
        self.assertIn("Synthetic parked idea", parked)
        self.assertIn("Fixture Band", (target / "memory" / "catalog" / "status.md").read_text())
        self.assertTrue((target / "raw" / "2026-06-10-session-log.md").is_file())
        creed = (target / "CREED.md").read_text()
        # The preserved access-boundaries.md became the CREED Dominion.
        self.assertIn("## Dominion", creed)
        self.assertIn("### Read Access", creed)
        self.assertIn("`docs/synthetic/`", creed)


if __name__ == "__main__":
    unittest.main()
