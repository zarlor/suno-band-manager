#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for migrate-sanctum-to-v7.py — Mac's v2 sanctum to the BMad v7 layout."""

import json
import subprocess
import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402

SCRIPTS_DIR = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS_DIR.parent
SCRIPT = SCRIPTS_DIR / "migrate-sanctum-to-v7.py"

spec = spec_from_file_location("migrate_sanctum_to_v7", SCRIPT)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

seed_spec = spec_from_file_location("_sanctum_seed", SCRIPTS_DIR / "_sanctum_seed.py")
seed = module_from_spec(seed_spec)
seed_spec.loader.exec_module(seed)

MEMORY = """# Mac — Curated Memory

> Curated long-term memory. Raw narrative in `sessions/YYYY-MM-DD.md`.

## Current Work

**PICK UP HERE** — raw narrative in `sessions/2026-09-22.md`. Rules in `creed-package-assembly.md`.

## User Preferences

- **Name:** Robin

## Downloads

- **Cap:** 20

## Recently Published

<!-- derived:recently-published:start -->
- Song A
<!-- derived:recently-published:end -->

## A Brand New Section

- something only this owner keeps

## Pulse Report

_(empty — a Pulse wake writes its staged report here; the next live session opens with it, then clears it)_

## Session History (recent)
"""

CREED = """# Mac — Creed (Core)

> **Born:** 2026-06-18

## Mission

Make songs.

## Dominion (Access Boundaries)

They live in `access-boundaries.md`.

## Discipline Shards — Load On Demand

| `creed-disciplines.md` | all |
| `creed-incident-log.md` | why |
"""

BOUNDARIES = """# Access Boundaries for Mac

## Read Access
- `{project-root}/_bmad/_memory/band-manager-sidecar/` — own memory

## Write Access
- `_bmad/_memory/band-manager-sidecar/` — own memory

## Deny Zones
- `src/`
"""

DISCIPLINES = """# Mac — Creed Shard: Disciplines

> Loaded on demand.

## Research Discipline

Look it up.

## Thematic Discipline — Read the Songbook Before Making Thematic Claims

Read first.
"""

INCIDENTS = """# Mac — Creed Incident Log

## Thematic Discipline — Read the Songbook Before Making Thematic Claims

The time it went wrong.
"""

CHRONOLOGY = """# Session Chronology

## 2026-05-17 — Imposter Syndrome workshop (session parked)

Workshop notes.

## 2026-03-21 — Session 1

### Songs

First song.
"""

PULSE = """# Mac — Pulse

## Default Wake Behavior

Old routine that writes MEMORY.md.

## Owner Preferences

- **Enabled:** no, never at night
"""


def make_project(tmp_path):
    """A temp project holding a v2 sanctum at the legacy path; returns the project root."""
    legacy = tmp_path / "_bmad" / "_memory" / "band-manager-sidecar"
    (legacy / "sessions").mkdir(parents=True)
    (legacy / "capabilities").mkdir()
    files = {
        "INDEX.md": "# Index\n\nmap\n",
        "MEMORY.md": MEMORY,
        "CREED.md": CREED,
        "access-boundaries.md": BOUNDARIES,
        "PERSONA.md": "# Persona\n\nNOLA soul.\n",
        "BOND.md": "# Bond — Robin\n\n- **Name:** Robin\n- **Language:** English\n",
        "CAPABILITIES.md": "# Capabilities\n\n## Learned\n",
        "PULSE.md": PULSE,
        "creed-disciplines.md": DISCIPLINES,
        "creed-incident-log.md": INCIDENTS,
        "creed-package-assembly.md": "# Mac — Creed Shard: Package Assembly\n\n## Package Assembly Rule\n\nUse the skills.\n",
        "creed-workshop-capture.md": "# Mac — Creed Shard: Workshop Capture\n\n## Workshop Capture Discipline\n\nVerbatim first.\n",
        "chronology.md": CHRONOLOGY,
        "patterns.md": "# Patterns\n\n> SUPERSEDED\n\n## Old\n\nold pattern\n",
        "_collection_layout.txt": "A Collection of Writings\n",
        "validate-ignore.txt": "docs/RA/*\n",
        "stray-notes.md": "something unexpected\n",
        "sessions/2026-09-22.md": "# Session 2026-09-22\n\nRaw narrative; see sessions/2026-09-14.md.\n",
        "sessions/2026-09-14.md": "# Session 2026-09-14\n\nEarlier.\n",
        "capabilities/liner-notes.md": "# Liner notes\n",
    }
    for rel, text in files.items():
        (legacy / rel).write_text(text, encoding="utf-8")
    return tmp_path


def run(project, *extra, backup=False):
    flags = [] if backup else ["--no-backup"]
    proc = subprocess.run([sys.executable, str(SCRIPT), str(project), *flags, *extra], capture_output=True, text=True)
    return proc.returncode, (json.loads(proc.stdout) if proc.stdout.strip() else None)


def target_of(project):
    return project / "_bmad" / "memory" / "suno-agent-band-manager"


class MigrateSanctumToV7Tests(TempDirMixin, unittest.TestCase):
    def test_dry_run_plans_and_writes_nothing(self):
        project = make_project(self.tmp_path)
        code, out = run(project, "--dry-run", "--today", "2026-10-15")
        assert code == 0 and out["status"] == "planned"
        assert not target_of(project).exists()
        destinations = {e["to"] for e in out["entries"]}
        assert "memory/work/current.md" in destinations
        assert "raw/2026-09-22-session-log.md" in destinations
        assert {d["from"] for d in out["dropped"]} >= {"INDEX.md"}

    def test_conversion_writes_the_v7_layout(self):
        project = make_project(self.tmp_path)
        code, out = run(project, "--today", "2026-10-15")
        assert code == 0 and out["status"] == "written"
        t = target_of(project)
        assert seed.classify_sanctum(t)["sidecar_format"] == "v7"
        for rel in ("memory/work/current.md", "memory/owner/preferences.md", "memory/work/downloads.md",
                    "memory/catalog/recently-published.md", "memory/misc/a-brand-new-section.md",
                    "memory/disciplines/research-discipline.md", "memory/disciplines/thematic-discipline.md",
                    "memory/disciplines/package-assembly.md", "memory/disciplines/workshop-capture.md",
                    "memory/incidents/thematic-discipline.md",
                    "memory/chronology/2026-05-17-imposter-syndrome-workshop-session-parked.md",
                    "memory/chronology/2026-03-21-session-1.md",
                    "raw/2026-05-17-patterns-superseded.md", "raw/2026-09-14-session-log.md",
                    "raw/unplaced-stray-notes.md", "validate-ignore.txt", "capabilities/liner-notes.md"):
            assert (t / rel).is_file(), rel
        assert (t / "memory/.tended").read_text().strip() == "2026-10-15"
        for old in ("INDEX.md", "MEMORY.md", "access-boundaries.md", "sessions"):
            assert not (t / old).exists(), old
        # Empty sections are not carried as files.
        assert not (t / "memory/pending.md").exists()
        assert not (t / "memory/work/session-history.md").exists()

    def test_source_is_never_modified(self):
        project = make_project(self.tmp_path)
        legacy = project / "_bmad" / "_memory" / "band-manager-sidecar"
        before = {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()}
        run(project)
        after = {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()}
        assert before == after

    def test_references_follow_the_files(self):
        project = make_project(self.tmp_path)
        run(project)
        t = target_of(project)
        current = (t / "memory/work/current.md").read_text()
        assert "raw/2026-09-22-session-log.md" in current
        assert "memory/disciplines/package-assembly.md" in current
        raw = (t / "raw/2026-09-22-session-log.md").read_text()
        assert raw.startswith("---\nstatus: distilled")
        assert "raw/2026-09-14-session-log.md" in raw
        creed = (t / "CREED.md").read_text()
        assert "### Read Access" in creed and "### Deny Zones" in creed
        assert "_bmad/memory/suno-agent-band-manager/" in creed
        assert "_memory/band-manager-sidecar" not in creed
        assert "memory/disciplines/" in creed and "creed-disciplines.md" not in creed

    def test_identity_files_and_templates(self):
        project = make_project(self.tmp_path)
        run(project)
        t = target_of(project)
        assert (t / "PERSONA.md").read_text() == "# Persona\n\nNOLA soul.\n"
        how = (t / "HOW-I-REMEMBER.md").read_text()
        assert how == (SKILL_DIR / "assets" / "HOW-I-REMEMBER-template.md").read_text()
        pulse = (t / "PULSE.md").read_text()
        assert "memory/pending.md" in pulse and "Old routine" not in pulse
        assert "no, never at night" in pulse  # the owner's preferences survive
        assert "Robin" in pulse and "2026-06-18" in pulse

    def test_no_line_is_lost(self):
        """Every non-empty source line lands somewhere (after reference rewriting), except
        the file-title banners, the empty Pulse Report, the Dominion pointer and INDEX.md."""
        project = make_project(self.tmp_path)
        run(project)
        legacy = project / "_bmad" / "_memory" / "band-manager-sidecar"
        t = target_of(project)
        smap = {p.stem[:10]: f"raw/{p.stem[:10]}-session-log.md" for p in (legacy / "sessions").glob("*.md")}
        landed = set()
        for p in t.rglob("*"):
            if p.is_file():
                landed.update(line.strip().lstrip("#").strip() for line in p.read_text().splitlines())
        allowed = {"# Mac — Curated Memory", "# Session Chronology", "# Mac — Creed Shard: Disciplines",
                   "# Mac — Creed Incident Log", "# Access Boundaries for Mac", "> Loaded on demand.",
                   "They live in `access-boundaries.md`.", "## Pulse Report", "## Session History (recent)",
                   "# Mac — Creed Shard: Package Assembly", "# Mac — Creed Shard: Workshop Capture",
                   "Old routine that writes MEMORY.md.", "## Default Wake Behavior",
                   "> Curated long-term memory. Raw narrative in `sessions/YYYY-MM-DD.md`."}
        missing = []
        for p in legacy.rglob("*"):
            if not p.is_file() or p.name == "INDEX.md":
                continue
            for line in p.read_text().splitlines():
                s = line.strip()
                if not s or s in allowed or s.startswith("_(empty"):
                    continue
                if mod.rewrite_refs(s, smap).lstrip("#").strip() not in landed:
                    missing.append((p.name, s))
        assert not missing

    def test_refuses_an_existing_target_without_force(self):
        project = make_project(self.tmp_path)
        target_of(project).mkdir(parents=True)
        (target_of(project) / "PERSONA.md").write_text("already here")
        code, out = run(project)
        assert code == 1 and out["status"] == "refused"
        assert (target_of(project) / "PERSONA.md").read_text() == "already here"

    def test_refuses_without_a_source(self):
        tmp_path = self.tmp_path
        code, out = run(tmp_path)
        assert code == 1 and "no v2 sanctum" in out["reason"]

    def test_conversion_writes_born_from_the_old_creed(self):
        project = make_project(self.tmp_path)
        run(project, "--today", "2026-10-15")
        assert (target_of(project) / "memory/.born").read_text().strip() == "2026-06-18"

    def test_born_falls_back_to_persona_then_today(self):
        project = make_project(self.tmp_path)
        legacy = project / "_bmad" / "_memory" / "band-manager-sidecar"
        (legacy / "CREED.md").write_text(CREED.replace("> **Born:** 2026-06-18\n", ""), encoding="utf-8")
        (legacy / "PERSONA.md").write_text("# Persona\n\n**Born:** 2026-05-01\n", encoding="utf-8")
        run(project, "--today", "2026-10-15")
        assert (target_of(project) / "memory/.born").read_text().strip() == "2026-05-01"
        (legacy / "PERSONA.md").write_text("# Persona\n", encoding="utf-8")
        run(project, "--today", "2026-10-15", "--force")
        assert (target_of(project) / "memory/.born").read_text().strip() == "2026-10-15"

    def test_backup_is_written_by_default_and_lists_the_source(self):
        project = make_project(self.tmp_path)
        import tarfile
        code, out = run(project, "--today", "2026-10-15", backup=True)
        assert code == 0 and out["status"] == "written"
        archive = Path(out["backup_path"])
        assert archive.parent == project / "_bmad" / "backups" and archive.name.startswith("mac-sanctum-v2-")
        legacy = project / "_bmad" / "_memory" / "band-manager-sidecar"
        expected = {"band-manager-sidecar/" + p.relative_to(legacy).as_posix() for p in legacy.rglob("*") if p.is_file()}
        with tarfile.open(archive) as tar:
            assert expected <= {m.name for m in tar.getmembers() if m.isfile()}

    def test_backup_includes_an_existing_target_on_force(self):
        project = make_project(self.tmp_path)
        import tarfile
        target_of(project).mkdir(parents=True)
        (target_of(project) / "PERSONA.md").write_text("already here")
        code, out = run(project, "--force", backup=True)
        assert code == 0
        with tarfile.open(out["backup_path"]) as tar:
            assert "suno-agent-band-manager/PERSONA.md" in tar.getnames()

    def test_no_backup_and_dry_run_report_null_backup_path(self):
        project = make_project(self.tmp_path)
        assert run(project, "--dry-run", backup=True)[1]["backup_path"] is None
        assert not (project / "_bmad" / "backups").exists()
        assert run(project)[1]["backup_path"] is None
        assert not (project / "_bmad" / "backups").exists()

    def test_failed_backup_refuses_and_writes_nothing(self):
        project = make_project(self.tmp_path)
        blocker = project / "not-a-dir"
        blocker.write_text("a file where the backup folder should be")
        code, out = run(project, "--backup-dir", str(blocker / "sub"), backup=True)
        assert code == 1 and out["status"] == "refused" and "backup failed" in out["reason"]
        assert not target_of(project).exists()

    def test_backup_listing_mismatch_refuses(self):
        project = make_project(self.tmp_path)
        tmp_path = self.tmp_path
        import tarfile as tf
        real_open = tf.open

        class Lister:
            def __init__(self, archive):
                self.archive = archive
            def __enter__(self):
                return self
            def __exit__(self, *exc):
                return False
            def getmembers(self):
                return []

        def fake_open(path, mode="r", *a, **k):
            return Lister(path) if mode.startswith("r") else real_open(path, mode, *a, **k)

        self.enterContext(mock.patch.object(mod.tarfile, "open", fake_open))
        legacy = project / "_bmad" / "_memory" / "band-manager-sidecar"
        archive, reason = mod.backup(legacy, target_of(project), tmp_path / "bk", "stamp")
        assert archive is None and "does not list the source" in reason
        assert not (tmp_path / "bk" / "mac-sanctum-v2-stamp.tar.gz").exists()

    def test_verify_flags_missing_and_changed_files(self):
        project = make_project(self.tmp_path)
        tmp_path = self.tmp_path
        legacy = project / "_bmad" / "_memory" / "band-manager-sidecar"
        plan = mod.build_plan(legacy, SKILL_DIR, "2026-10-15", project)
        target = tmp_path / "out"
        mod.write(plan, target)
        assert mod.verify(plan, target) == []
        (target / "PERSONA.md").unlink()
        (target / "memory/.tended").write_text("")
        (target / "capabilities/liner-notes.md").write_text("changed size\n")
        assert mod.verify(plan, target) == ["PERSONA.md", "capabilities/liner-notes.md", "memory/.tended"]

    def test_bad_today_is_exit_2(self):
        project = make_project(self.tmp_path)
        code, out = run(project, "--today", "15-10-2026")
        assert code == 2 and out["status"] == "error"


if __name__ == "__main__":
    unittest.main()
