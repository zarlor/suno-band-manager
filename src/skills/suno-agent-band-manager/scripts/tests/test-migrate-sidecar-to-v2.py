#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for migrate-sidecar-to-v2.py.

Uses a small SYNTHETIC fixture sidecar built in tmp_path — never the real data.
"""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

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


@pytest.fixture
def synthetic_project(tmp_path):
    """Build a synthetic project with a fixture sidecar + config."""
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "config.yaml").write_text(
        "user_name: Fixtureville\ncommunication_language: English\n"
    )
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


def test_split_sections_counts():
    preamble, sections = mod.split_sections(SYNTH_INDEX)
    assert preamble.strip().startswith("# Mac")
    # 4 session + 5 non-session (Prefs, Exclusions, Recently, Catalog, Module,
    # Pending, Session History) — count headings.
    headings = [mod.heading_of(s) for s in sections]
    assert any(h.startswith("## Current Work") for h in headings)


def test_session_classification():
    _, sections = mod.split_sections(SYNTH_INDEX)
    session = [s for s in sections if mod.is_session_section(s)]
    assert len(session) == 4


def test_session_date_extraction_paren_form():
    section = "## Prior Work — Synthetic publish + session 7 (2026-06-01 evening)\nbody\n"
    assert mod.session_date(section) == "2026-06-01"


# --- migration output ---


def test_migrate_writes_only_to_out_dir(synthetic_project):
    tmp_path, sanctum = synthetic_project
    src_before = {p: p.read_bytes() for p in sanctum.iterdir() if p.is_file()}
    out_dir, result = run_migrate(tmp_path, sanctum)
    assert result["status"] == "migrated"
    # Source untouched.
    src_after = {p: p.read_bytes() for p in sanctum.iterdir() if p.is_file()}
    assert src_before == src_after


def test_same_date_sessions_grouped(synthetic_project):
    tmp_path, sanctum = synthetic_project
    out_dir, result = run_migrate(tmp_path, sanctum)
    # 4 blocks, but two share 2026-06-09 → 3 files.
    assert result["session_blocks_found"] == 4
    assert result["session_files_written"] == 3
    sessions = sorted(p.name for p in (out_dir / "sessions").glob("*.md"))
    assert sessions == ["2026-06-01.md", "2026-06-09.md", "2026-06-10.md"]
    # The same-date file holds both blocks.
    body = (out_dir / "sessions" / "2026-06-09.md").read_text()
    assert "synthetic earlier session" in body
    assert "same-date second block" in body


def test_derived_markers_preserved_in_memory(synthetic_project):
    tmp_path, sanctum = synthetic_project
    out_dir, _ = run_migrate(tmp_path, sanctum)
    memory = (out_dir / "MEMORY.md").read_text()
    for marker in ("recently-published", "catalog-status"):
        assert f"<!-- derived:{marker}:start -->" in memory
        assert f"<!-- derived:{marker}:end -->" in memory
    # The derived content rode along verbatim.
    assert "Synthetic Song" in memory
    assert "Fixture Band" in memory


def test_non_session_content_in_memory(synthetic_project):
    tmp_path, sanctum = synthetic_project
    out_dir, _ = run_migrate(tmp_path, sanctum)
    memory = (out_dir / "MEMORY.md").read_text()
    assert "Synthetic parked idea" in memory
    assert "v9.9.9 (synthetic)" in memory
    # Session narrative is NOT in MEMORY (only the pointer block).
    assert "Round 1 swing on the table" not in memory


def test_preserved_files_byte_identical(synthetic_project):
    tmp_path, sanctum = synthetic_project
    out_dir, result = run_migrate(tmp_path, sanctum)
    for name in mod.PRESERVED_FILES:
        assert (sanctum / name).read_bytes() == (out_dir / name).read_bytes()
    assert set(result["preserved_files"]) == set(mod.PRESERVED_FILES)


def test_template_seeded_files_present(synthetic_project):
    tmp_path, sanctum = synthetic_project
    out_dir, _ = run_migrate(tmp_path, sanctum)
    for name in ("INDEX.md", "PERSONA.md", "CREED.md", "BOND.md", "PULSE.md", "CAPABILITIES.md"):
        assert (out_dir / name).exists(), f"missing {name}"
    # Variables substituted in seeded files.
    assert "{user_name}" not in (out_dir / "PERSONA.md").read_text()
    assert "Fixtureville" in (out_dir / "PERSONA.md").read_text()


def test_creed_shards_produced(synthetic_project):
    tmp_path, sanctum = synthetic_project
    out_dir, _ = run_migrate(tmp_path, sanctum)
    # Shards seeded from the real skill creed.md.
    assert (out_dir / "creed-package-assembly.md").exists()
    assert (out_dir / "creed-incident-log.md").exists()
    # Package Assembly content landed in its shard.
    assert "Package Assembly Rule" in (out_dir / "creed-package-assembly.md").read_text()


def test_rerun_is_clean(synthetic_project):
    tmp_path, sanctum = synthetic_project
    out_dir, _ = run_migrate(tmp_path, sanctum)
    # Drop a stray file, rerun, confirm it's gone (wipe-and-rebuild).
    (out_dir / "stray.txt").write_text("x")
    out_dir2, _ = run_migrate(tmp_path, sanctum)
    assert not (out_dir2 / "stray.txt").exists()


# --- verify ---


def test_verify_passes_on_clean_migration(synthetic_project):
    tmp_path, sanctum = synthetic_project
    out_dir, _ = run_migrate(tmp_path, sanctum)
    report = mod.verify(sanctum, out_dir)
    assert report["status"] == "pass", report["findings"]
    assert report["session_blocks_found"] == 4
    assert report["session_files_written"] == 3
    assert report["session_dates_match"] is True
    assert report["derived_markers"]["recently-published"] is True
    assert report["derived_markers"]["catalog-status"] is True
    assert report["char_accounting"]["all_sections_present"] is True
    assert all(report["preserved_files_byte_identical"].values())


def test_verify_detects_dropped_content(synthetic_project):
    tmp_path, sanctum = synthetic_project
    out_dir, _ = run_migrate(tmp_path, sanctum)
    # Corrupt MEMORY.md by deleting the parked-work content.
    memory = out_dir / "MEMORY.md"
    text = memory.read_text().replace("Synthetic parked idea", "")
    memory.write_text(text)
    report = mod.verify(sanctum, out_dir)
    assert report["status"] == "fail"
    assert report["char_accounting"]["all_sections_present"] is False


# --- in-place upgrade (backup → migrate → verify → swap, abort-on-loss) ---


def test_sidecar_state_classification(synthetic_project, tmp_path):
    tmp_path2, sanctum = synthetic_project
    # v1: index.md present, no v2 markers.
    assert mod.sidecar_state(sanctum) == "v1"
    # v2: MEMORY.md present.
    (sanctum / "MEMORY.md").write_text("# memory\n")
    assert mod.sidecar_state(sanctum) == "v2"
    # absent: dir doesn't exist.
    assert mod.sidecar_state(tmp_path / "nope" / "band-manager-sidecar") == "absent"
    # damaged: dir exists, neither marker.
    damaged = tmp_path / "damaged"
    damaged.mkdir()
    assert mod.sidecar_state(damaged) == "damaged"


def test_in_place_migrates_v1_with_backup_and_swap(synthetic_project):
    tmp_path, sanctum = synthetic_project
    # Capture the source content before the upgrade so we can prove backup fidelity.
    src_index = (sanctum / "index.md").read_bytes()

    result = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
    assert result["status"] == "migrated", result

    # Live location is now v2.
    assert (sanctum / "MEMORY.md").is_file()
    assert mod.sidecar_state(sanctum) == "v2"
    # The old index.md content store is gone from the live location (migrated).
    assert not (sanctum / "index.md").exists()

    # Backup dir + tarball both exist.
    backup_dir = Path(result["backup_path"])
    backup_tarball = Path(result["backup_tarball"])
    assert backup_dir.is_dir()
    assert backup_tarball.is_file()
    assert "sidecar-backup-pre-v2-" in backup_dir.name
    # Backup is a faithful copy of the ORIGINAL v1 content.
    assert (backup_dir / "index.md").read_bytes() == src_index

    # Verify rode along and passed; content is present in the new MEMORY.md.
    assert result["verify"]["status"] == "pass"
    assert result["verify"]["char_accounting"]["all_sections_present"] is True
    memory = (sanctum / "MEMORY.md").read_text()
    assert "Synthetic parked idea" in memory
    assert "Fixture Band" in memory
    # Session narrative migrated into sessions/ (not lost).
    assert result["session_files"]
    assert (sanctum / "sessions" / "2026-06-10.md").is_file()


def test_in_place_already_v2_is_noop(synthetic_project):
    tmp_path, sanctum = synthetic_project
    # First upgrade brings it to v2.
    first = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
    assert first["status"] == "migrated"
    memory_before = (sanctum / "MEMORY.md").read_bytes()

    # Second run is a clean no-op — no new backup, sanctum untouched.
    backups_before = list((tmp_path / "_bmad" / "_memory").glob(".sidecar-backup-pre-v2-*"))
    second = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
    assert second["status"] == "already-v2"
    backups_after = list((tmp_path / "_bmad" / "_memory").glob(".sidecar-backup-pre-v2-*"))
    assert len(backups_after) == len(backups_before)
    assert (sanctum / "MEMORY.md").read_bytes() == memory_before


def test_in_place_no_sidecar_is_noop(tmp_path):
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "config.yaml").write_text("user_name: Nobody\n")
    sanctum = bmad / "_memory" / "band-manager-sidecar"  # never created
    result = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
    assert result["status"] == "no-sidecar"
    assert not sanctum.exists()


def test_in_place_aborts_on_content_loss(synthetic_project, monkeypatch):
    """If verify can't account for all content, ABORT: no swap, original intact."""
    tmp_path, sanctum = synthetic_project
    src_before = {p.name: p.read_bytes() for p in sanctum.iterdir() if p.is_file()}

    # Force a content-loss verify by monkeypatching verify() to report a drop.
    def fake_verify(sanctum_path, out_dir):
        return {
            "status": "fail",
            "findings": ["forced content loss for test"],
            "char_accounting": {"all_sections_present": False, "dropped_sections": ["X"]},
        }

    monkeypatch.setattr(mod, "verify", fake_verify)
    result = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)

    assert result["status"] == "blocked"
    assert "verify did not pass" in result["reason"]
    # Original sidecar is STILL v1 and byte-identical — nothing swapped.
    assert mod.sidecar_state(sanctum) == "v1"
    src_after = {p.name: p.read_bytes() for p in sanctum.iterdir() if p.is_file()}
    assert src_before == src_after
    # The backup was still made (backup-first) and is reported.
    assert Path(result["backup_path"]).is_dir()
    # No staging dir left lying around.
    staging = list((tmp_path / "_bmad" / "_memory").glob(".sidecar-v2-staging-*"))
    assert staging == []


def test_in_place_blocks_damaged_sidecar(tmp_path):
    """A damaged sidecar (no index.md, no MEMORY.md) is blocked, not migrated."""
    bmad = tmp_path / "_bmad"
    bmad.mkdir()
    (bmad / "config.yaml").write_text("user_name: Nobody\n")
    sanctum = bmad / "_memory" / "band-manager-sidecar"
    sanctum.mkdir(parents=True)
    (sanctum / "stray.txt").write_text("junk\n")
    result = mod.migrate_in_place(tmp_path, sanctum, SKILL_DIR)
    assert result["status"] == "blocked"
    assert "re-scaffold" in result["reason"]


def test_in_place_staging_mode_still_works(synthetic_project):
    """The original staging-mode migrate() is unchanged by the in-place addition."""
    tmp_path, sanctum = synthetic_project
    out_dir, result = run_migrate(tmp_path, sanctum)
    assert result["status"] == "migrated"
    # Source untouched by staging mode.
    assert (sanctum / "index.md").is_file()
    assert mod.sidecar_state(sanctum) == "v1"
    assert (out_dir / "MEMORY.md").is_file()
