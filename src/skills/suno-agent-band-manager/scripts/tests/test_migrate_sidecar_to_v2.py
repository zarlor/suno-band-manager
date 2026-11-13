#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for migrate_sidecar_to_v2.py.

Uses a small SYNTHETIC fixture sidecar built in tmp_path — never the real data —
and the synthetic skill from helpers.make_skill for the templates and the creed
source. One smoke test migrates with the shipped skill and checks shape only.
"""

import io
import json
import shutil
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
from helpers import TempDirMixin, make_skill, snapshot  # noqa: E402

spec = spec_from_file_location("migrate_sidecar", SCRIPTS_DIR / "migrate_sidecar_to_v2.py")
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


def skill_of(tmp_path):
    return tmp_path / "skill"


def make_synthetic_project(tmp_path):
    """Build a synthetic project with a fixture sidecar + config, and the synthetic skill beside it."""
    make_skill(tmp_path)
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
    result = mod.migrate(tmp_path, sanctum, out_dir, skill_of(tmp_path))
    return out_dir, result


def add_v1_extras(sanctum):
    """Files a v1 store may hold beyond index.md and the six preserved names."""
    (sanctum / "owner-notes.md").write_text("# Owner notes\n\nKeep the bridge short.\n")
    (sanctum / "validate-ignore.txt").write_text("docs/RA/*\n")
    (sanctum / "daily").mkdir()
    (sanctum / "daily" / "2026-03-01.md").write_text("A day's note.\n")
    (sanctum / "daily" / "audio").mkdir()
    (sanctum / "daily" / "audio" / "take.bin").write_bytes(b"\x00\xff\x10")
    return ["daily/2026-03-01.md", "daily/audio/take.bin", "owner-notes.md", "validate-ignore.txt"]


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
        # Shards sliced from the skill's creed source, one file per routed group plus the incident log.
        shards = mod.shard_creed(mod._seed.creed_source(skill_of(tmp_path)).read_text())
        self.assertEqual(sorted(p.name for p in out_dir.glob("creed-*.md")), sorted(shards))
        for name, text in shards.items():
            self.assertEqual((out_dir / name).read_text(), text, name)

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

        result = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))
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
        first = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))
        self.assertEqual(first["status"], "migrated")
        memory_before = (sanctum / "MEMORY.md").read_bytes()

        # Second run is a clean no-op — no new backup, sanctum untouched.
        backups_before = list((tmp_path / "_bmad" / "_memory").glob(".sidecar-backup-pre-v2-*"))
        second = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))
        self.assertEqual(second["status"], "already-v2")
        backups_after = list((tmp_path / "_bmad" / "_memory").glob(".sidecar-backup-pre-v2-*"))
        self.assertEqual(len(backups_after), len(backups_before))
        self.assertEqual((sanctum / "MEMORY.md").read_bytes(), memory_before)

    def test_in_place_no_sidecar_is_noop(self):
        tmp_path = self.tmp_path
        bmad = tmp_path / "_bmad"
        bmad.mkdir()
        sanctum = bmad / "_memory" / "band-manager-sidecar"  # never created
        result = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))
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
            result = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))

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
        sanctum = bmad / "_memory" / "band-manager-sidecar"
        sanctum.mkdir(parents=True)
        (sanctum / "stray.txt").write_text("junk\n")
        result = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))
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
        self.assertEqual(text, mod._seed.render_access_boundaries(skill_of(tmp_path) / "assets",
                                                                   mod.build_variables(tmp_path)))
        self.assertNotIn("{project-root}", text)
        # The full spine exists, so the migrated sanctum classifies as v2.
        self.assertEqual(mod.sidecar_state(out_dir), "v2")

    def test_migration_capabilities_has_builtin_roster(self):
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        out_dir, _ = run_migrate(tmp_path, sanctum)
        caps = (out_dir / "CAPABILITIES.md").read_text(encoding="utf-8")
        rows = mod._seed.menu_rows(skill_of(tmp_path) / "assets" / "menu.csv")
        self.assertEqual(caps, mod._seed.generate_capabilities_md(rows))
        self.assertNotIn("was not found", caps)

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
        result = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))
        self.assertEqual(result["status"], "already-v7")

    def test_default_paths_are_the_legacy_store(self):
        """The CLI reads the v1 store at the legacy path and stages beside it."""
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        self.assertEqual(sanctum, mod._seed.legacy_sanctum_dir(tmp_path))
        buf = io.StringIO()
        with patch.object(sys, "argv", ["migrate_sidecar_to_v2.py", "--project-root", str(tmp_path),
                                        "--skill-path", str(skill_of(tmp_path)), "--format", "json"]), \
                redirect_stdout(buf):
            rc = mod.main()
        self.assertEqual(rc, 0)
        out = json.loads(buf.getvalue())
        self.assertEqual(out["status"], "migrated")
        self.assertEqual(Path(out["out_dir"]), tmp_path / "_bmad" / "_memory" / ".sidecar-v2-staging")

    def test_v1_reaches_v7_through_both_hops(self):
        """v1 -> v2 here, then migrate_sanctum_to_v7.py converts the result to a v7 sanctum."""
        synthetic_project = make_synthetic_project(self.tmp_path)
        tmp_path, sanctum = synthetic_project
        (sanctum / "access-boundaries.md").write_text(
            "# Access Boundaries\n\n## Read Access\n\n- `docs/synthetic/` — fixture\n\n"
            "## Write Access\n\n- `docs/wip-*.md` — fragments\n\n## Deny Zones\n\n- `src/`\n"
        )
        extras = add_v1_extras(sanctum)
        (sanctum / "index.md").write_text(SYNTH_INDEX.replace(
            "# Mac — Session Index\n", "# Mac — Session Index\n\nA note above every heading.\n", 1))
        self.assertEqual(mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))["status"], "migrated")

        v7_spec = spec_from_file_location("migrate_to_v7", SCRIPTS_DIR / "migrate_sanctum_to_v7.py")
        v7 = module_from_spec(v7_spec)
        v7_spec.loader.exec_module(v7)
        plan = v7.build_plan(sanctum, skill_of(tmp_path), "2026-10-15")
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
        # What the v1 store held beyond its index reaches the v7 sanctum or is named as dropped.
        self.assertEqual((target / "validate-ignore.txt").read_text(), "docs/RA/*\n")
        self.assertEqual((target / "raw" / "unplaced-owner-notes.md").read_text(),
                         "# Owner notes\n\nKeep the bridge short.\n")
        self.assertIn({"from": "daily", "section": None, "why": "unexpected folder; not copied"}, plan.dropped)
        self.assertTrue(all((sanctum / rel).is_file() for rel in extras))  # still in the v2 store, the rollback
        notes = target / "memory" / "misc" / "notes-above-the-first-heading-v1-index-md.md"
        self.assertIn("A note above every heading.", notes.read_text())

    def test_shipped_skill_migrates_in_place_to_a_v2_store(self):
        """Smoke check with the shipped templates and creed: shape only."""
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        result = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
        self.assertEqual(result["status"], "migrated", result)
        self.assertEqual(mod.sidecar_state(sanctum), "v2")

    # --- --out is only ever wiped when it is a staging folder ------------------

    def test_out_that_would_wipe_real_data_is_refused(self):
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        other = tmp_path / "owner-folder"
        other.mkdir()
        (other / "keep.md").write_text("irreplaceable\n")
        inside = sanctum / "staging"
        cases = {
            "the source store": sanctum,
            "its parent": sanctum.parent,
            "the project root": tmp_path,
            "a folder inside the source": inside,
            "another non-empty folder": other,
        }
        before = snapshot(tmp_path)
        for label, out_dir in cases.items():
            with self.subTest(out=label):
                result = mod.migrate(tmp_path, sanctum, out_dir, skill_of(tmp_path))
                self.assertEqual(result["status"], "error")
                self.assertIn("refusing to", result["message"])
                self.assertEqual(snapshot(tmp_path), before)
        # The CLI says so and exits 1.
        buf = io.StringIO()
        with patch.object(sys, "argv", ["migrate_sidecar_to_v2.py", "--project-root", str(tmp_path),
                                        "--skill-path", str(skill_of(tmp_path)), "--out", str(sanctum),
                                        "--format", "json"]), redirect_stdout(buf):
            self.assertEqual(mod.main(), 1)
        self.assertEqual(json.loads(buf.getvalue())["status"], "error")
        self.assertEqual(snapshot(tmp_path), before)

    def test_out_may_be_new_empty_or_a_previous_staging_folder(self):
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        new = tmp_path / "review" / "v2"
        empty = tmp_path / "empty"
        empty.mkdir()
        previous = tmp_path / ".sidecar-v2-staging-old"
        previous.mkdir()
        (previous / "stray.txt").write_text("x")
        for out_dir in (new, empty, previous):
            with self.subTest(out=out_dir.name):
                result = mod.migrate(tmp_path, sanctum, out_dir, skill_of(tmp_path))
                self.assertEqual(result["status"], "migrated")
                self.assertEqual(mod.sidecar_state(out_dir), "v2")
                self.assertFalse((out_dir / "stray.txt").exists())

    # --- nothing of the v1 store is left behind ------------------------------

    def test_extra_v1_files_are_carried_into_the_migrated_store(self):
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        extras = add_v1_extras(sanctum)
        originals = {rel: (sanctum / rel).read_bytes() for rel in extras}
        result = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))
        self.assertEqual(result["status"], "migrated", result)
        self.assertEqual(mod.sidecar_state(sanctum), "v2")
        for rel, data in originals.items():
            self.assertEqual((sanctum / rel).read_bytes(), data, rel)
            self.assertIn(rel, result["files"])
        self.assertEqual(result["verify"]["carried_files_byte_identical"], {rel: True for rel in extras})

    def test_carried_file_that_clashes_with_a_written_name_lands_beside_it(self):
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        (sanctum / "PULSE.md").write_text("# the owner's own pulse notes\n")
        (sanctum / "sessions").mkdir()
        (sanctum / "sessions" / "2026-06-10.md").write_text("an older hand-kept log\n")
        (sanctum / "sessions" / "2025-12-31.md").write_text("a log with no block in the index\n")
        out_dir, result = run_migrate(tmp_path, sanctum)
        self.assertEqual(sorted(result["carried_files"]),
                         ["PULSE.v1.md", "sessions/2025-12-31.md", "sessions/2026-06-10.v1.md"])
        self.assertEqual((out_dir / "PULSE.v1.md").read_text(), "# the owner's own pulse notes\n")
        self.assertEqual((out_dir / "sessions" / "2026-06-10.v1.md").read_text(), "an older hand-kept log\n")
        self.assertIn("synthetic active dig", (out_dir / "sessions" / "2026-06-10.md").read_text())
        # Carried session files are not counted as migrated session blocks.
        report = mod.verify(sanctum, out_dir)
        self.assertEqual(report["status"], "pass", report["findings"])
        self.assertEqual(report["session_files_written"], 3)

    def test_verify_blocks_the_swap_when_a_carried_file_is_missing_or_changed(self):
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        add_v1_extras(sanctum)
        out_dir, _ = run_migrate(tmp_path, sanctum)
        (out_dir / "owner-notes.md").unlink()
        (out_dir / "daily" / "2026-03-01.md").write_text("changed\n")
        report = mod.verify(sanctum, out_dir)
        self.assertEqual(report["status"], "fail")
        self.assertEqual({k for k, ok in report["carried_files_byte_identical"].items() if not ok},
                         {"owner-notes.md", "daily/2026-03-01.md"})
        self.assertIn("v1 file not carried byte-identical: owner-notes.md", report["findings"])

        # In place, a migration that leaves a file out never reaches the swap.
        real_migrate = mod.migrate

        def lossy_migrate(project_root, sanctum_path, out, skill_path):
            result = real_migrate(project_root, sanctum_path, out, skill_path)
            (out / "owner-notes.md").unlink()
            return result

        before = snapshot(sanctum)
        with patch.object(mod, "migrate", lossy_migrate):
            result = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))
        self.assertEqual(result["status"], "blocked")
        self.assertIn("owner-notes.md", result["reason"])
        self.assertEqual(snapshot(sanctum), before)

    def test_index_preamble_reaches_memory_and_verify_checks_it(self):
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        preamble = "# Mac — Session Index\n\nOwner: always ask before publishing.\n> and keep the hedges.\n\n"
        (sanctum / "index.md").write_text(SYNTH_INDEX.replace("# Mac — Session Index\n\n", preamble, 1))
        out_dir, result = run_migrate(tmp_path, sanctum)
        self.assertIs(result["preamble_carried"], True)
        memory = (out_dir / "MEMORY.md").read_text()
        self.assertIn(f"{mod.PREAMBLE_HEADING}\n\nOwner: always ask before publishing.\n> and keep the hedges.\n", memory)
        report = mod.verify(sanctum, out_dir)
        self.assertEqual(report["status"], "pass", report["findings"])
        self.assertIs(report["char_accounting"]["preamble_present"], True)
        # Lose it from MEMORY.md and verify fails, naming the preamble.
        (out_dir / "MEMORY.md").write_text(memory.replace("Owner: always ask before publishing.\n", ""))
        report = mod.verify(sanctum, out_dir)
        self.assertEqual(report["status"], "fail")
        self.assertIs(report["char_accounting"]["preamble_present"], False)
        self.assertEqual(report["char_accounting"]["dropped_sections"], ["(preamble)"])
        self.assertIs(report["char_accounting"]["all_sections_present"], False)

    def test_title_only_preamble_adds_no_section(self):
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        out_dir, result = run_migrate(tmp_path, sanctum)
        self.assertIs(result["preamble_carried"], False)
        self.assertNotIn(mod.PREAMBLE_HEADING, (out_dir / "MEMORY.md").read_text())
        self.assertEqual(mod.preamble_body("# Title only\n\n"), "")
        self.assertEqual(mod.preamble_body("# Title\n\ntext\n"), "text")
        self.assertEqual(mod.preamble_body("text with no title\n"), "text with no title")

    def test_source_blockquote_lines_are_accounted_for_not_a_false_loss(self):
        """A `>` line in a v1 section is source content: it must be found, and not block the swap."""
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        (sanctum / "index.md").write_text(SYNTH_INDEX.replace(
            "- Synthetic parked idea.\n", "- Synthetic parked idea.\n\n> The owner said: wait for spring.\n", 1))
        result = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))
        self.assertEqual(result["status"], "migrated", result)
        self.assertIn("> The owner said: wait for spring.", (sanctum / "MEMORY.md").read_text())

    # --- the swap ------------------------------------------------------------

    def test_failed_swap_restores_the_original_store(self):
        """The second move (staging into place) fails: the original goes back, nothing is left behind."""
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        add_v1_extras(sanctum)
        before = snapshot(sanctum)
        real_move = shutil.move
        calls = []

        def move_failing_second(src, dst, *args, **kwargs):
            calls.append((Path(src).name, Path(dst).name))
            if len(calls) == 2:
                raise OSError("Device or resource busy")
            return real_move(src, dst, *args, **kwargs)

        with patch.object(mod.shutil, "move", move_failing_second):
            result = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))

        self.assertEqual(result["status"], "blocked")
        self.assertIn("swap failed", result["reason"])
        self.assertEqual(len(calls), 3)  # aside, the failed move into place, the restore
        self.assertEqual(calls[2][1], sanctum.name)
        self.assertEqual(mod.sidecar_state(sanctum), "v1")
        self.assertEqual(snapshot(sanctum), before)
        memory_root = sanctum.parent
        self.assertEqual(list(memory_root.glob(".sidecar-old-*")), [])
        self.assertEqual(list(memory_root.glob(".sidecar-v2-staging-*")), [])
        # The backup made first is still there, and still the original.
        self.assertEqual(snapshot(Path(result["backup_path"])), before)

    def test_in_place_reports_an_unreadable_index_as_blocked(self):
        tmp_path, sanctum = make_synthetic_project(self.tmp_path)
        (sanctum / "index.md").write_bytes(b"# Mac\n\n## User Preferences\n\ncaf\xe9\n")
        before = snapshot(sanctum)
        result = mod.migrate_in_place(tmp_path, sanctum, skill_of(tmp_path))
        self.assertEqual(result["status"], "blocked")
        self.assertIn("migration failed", result["reason"])
        self.assertEqual(snapshot(sanctum), before)
        self.assertEqual(list(sanctum.parent.glob(".sidecar-v2-staging-*")), [])


if __name__ == "__main__":
    unittest.main()
