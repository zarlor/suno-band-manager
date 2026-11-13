#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for migrate_sanctum_to_v7.py — Mac's v2 sanctum to the BMad v7 layout.

The old store and the skill it converts with are both synthetic (the fixture
below and helpers.make_skill). One smoke test converts with the shipped skill
and checks shape only.
"""

import json
import subprocess
import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import SKILL_ASSETS, TempDirMixin, make_skill, snapshot  # noqa: E402

SCRIPTS_DIR = Path(__file__).parent.parent
SCRIPT = SCRIPTS_DIR / "migrate_sanctum_to_v7.py"

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
    """A temp project holding a v2 sanctum at the legacy path, and the synthetic
    skill beside it (`skill_of`); returns the project root."""
    make_skill(tmp_path)
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


def skill_of(project):
    return project / "skill"


def legacy_of(project):
    return project / "_bmad" / "_memory" / "band-manager-sidecar"


def run(project, *extra, backup=False, shipped=False):
    """Run the converter as a subprocess (the synthetic skill unless `shipped`)."""
    flags = [] if backup else ["--no-backup"]
    if not shipped:
        flags += ["--skill-path", str(skill_of(project))]
    proc = subprocess.run([sys.executable, str(SCRIPT), str(project), *flags, *extra], capture_output=True, text=True)
    if proc.stderr.strip():
        raise AssertionError(f"the converter wrote to stderr:\n{proc.stderr}")
    return proc.returncode, (json.loads(proc.stdout) if proc.stdout.strip() else None)


def target_of(project):
    return project / "_bmad" / "memory" / "suno-agent-band-manager"


class MigrateSanctumToV7Tests(TempDirMixin, unittest.TestCase):
    def test_dry_run_plans_and_writes_nothing(self):
        project = make_project(self.tmp_path)
        code, out = run(project, "--dry-run", "--today", "2026-10-15")
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "planned")
        self.assertFalse(target_of(project).exists())
        destinations = {e["to"] for e in out["entries"]}
        self.assertIn("memory/work/current.md", destinations)
        self.assertIn("raw/2026-09-22-session-log.md", destinations)
        self.assertGreaterEqual({d["from"] for d in out["dropped"]}, {"INDEX.md"})

    def test_conversion_writes_the_v7_layout(self):
        project = make_project(self.tmp_path)
        code, out = run(project, "--today", "2026-10-15")
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "written")
        t = target_of(project)
        self.assertEqual(seed.classify_sanctum(t)["sidecar_format"], "v7")
        for rel in ("memory/work/current.md", "memory/owner/preferences.md", "memory/work/downloads.md",
                    "memory/catalog/recently-published.md", "memory/misc/a-brand-new-section.md",
                    "memory/disciplines/research-discipline.md", "memory/disciplines/thematic-discipline.md",
                    "memory/disciplines/package-assembly.md", "memory/disciplines/workshop-capture.md",
                    "memory/incidents/thematic-discipline.md",
                    "memory/chronology/2026-05-17-imposter-syndrome-workshop-session-parked.md",
                    "memory/chronology/2026-03-21-session-1.md",
                    "raw/2026-05-17-patterns-superseded.md", "raw/2026-09-14-session-log.md",
                    "raw/unplaced-stray-notes.md", "validate-ignore.txt", "capabilities/liner-notes.md"):
            self.assertTrue((t / rel).is_file(), rel)
        self.assertEqual((t / "memory/.tended").read_text().strip(), "2026-10-15")
        for old in ("INDEX.md", "MEMORY.md", "access-boundaries.md", "sessions"):
            self.assertFalse((t / old).exists(), old)
        # Empty sections are not carried as files.
        self.assertFalse((t / "memory/pending.md").exists())
        self.assertFalse((t / "memory/work/session-history.md").exists())

    def test_source_is_never_modified(self):
        project = make_project(self.tmp_path)
        legacy = project / "_bmad" / "_memory" / "band-manager-sidecar"
        before = {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()}
        run(project)
        after = {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_references_follow_the_files(self):
        project = make_project(self.tmp_path)
        run(project)
        t = target_of(project)
        current = (t / "memory/work/current.md").read_text()
        self.assertIn("raw/2026-09-22-session-log.md", current)
        self.assertIn("memory/disciplines/package-assembly.md", current)
        raw = (t / "raw/2026-09-22-session-log.md").read_text()
        self.assertTrue(raw.startswith("---\nstatus: distilled"))
        self.assertIn("raw/2026-09-14-session-log.md", raw)
        creed = (t / "CREED.md").read_text()
        self.assertIn("### Read Access", creed)
        self.assertIn("### Deny Zones", creed)
        self.assertIn("_bmad/memory/suno-agent-band-manager/", creed)
        self.assertNotIn("_memory/band-manager-sidecar", creed)
        self.assertIn("memory/disciplines/", creed)
        self.assertNotIn("creed-disciplines.md", creed)

    def test_identity_files_and_templates(self):
        project = make_project(self.tmp_path)
        run(project)
        t = target_of(project)
        self.assertEqual((t / "PERSONA.md").read_text(), "# Persona\n\nNOLA soul.\n")
        # HOW-I-REMEMBER.md is the template, filled in as First Breath fills it.
        how = (t / "HOW-I-REMEMBER.md").read_text()
        self.assertEqual(how, SKILL_ASSETS["HOW-I-REMEMBER-template.md"].replace("{project-root}", str(project)))
        base = json.loads((t / "memory" / ".template-base.json").read_text())["units"]
        self.assertEqual(set(base), {"HOW-I-REMEMBER.md (preamble)", "HOW-I-REMEMBER.md ## Layout",
                                     "HOW-I-REMEMBER.md ## Tending", "PULSE.md (preamble)",
                                     "PULSE.md ## Default Wake Behavior"})  # never the owner's or carried text
        # PULSE.md: the new template's routine, the owner's name and birth date, the owner's preferences kept.
        shipped_pulse = (SKILL_ASSETS["PULSE-template.md"].replace("{user_name}", "Robin")
                         .replace("{birth_date}", "2026-06-18"))
        head = shipped_pulse.partition("## Owner Preferences")[0]
        self.assertEqual((t / "PULSE.md").read_text(), head + "## Owner Preferences\n\n- **Enabled:** no, never at night\n")

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
        self.assertFalse(missing)

    def test_refuses_an_existing_target_without_force(self):
        project = make_project(self.tmp_path)
        target_of(project).mkdir(parents=True)
        (target_of(project) / "PERSONA.md").write_text("already here")
        code, out = run(project)
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "refused")
        self.assertEqual((target_of(project) / "PERSONA.md").read_text(), "already here")

    def test_refuses_without_a_source(self):
        tmp_path = self.tmp_path
        code, out = run(tmp_path)
        self.assertEqual(code, 1)
        self.assertIn("no v2 sanctum", out["reason"])

    def test_conversion_writes_born_from_the_old_creed(self):
        project = make_project(self.tmp_path)
        run(project, "--today", "2026-10-15")
        self.assertEqual((target_of(project) / "memory/.born").read_text().strip(), "2026-06-18")

    def test_born_falls_back_to_persona_then_today(self):
        project = make_project(self.tmp_path)
        legacy = project / "_bmad" / "_memory" / "band-manager-sidecar"
        (legacy / "CREED.md").write_text(CREED.replace("> **Born:** 2026-06-18\n", ""), encoding="utf-8")
        (legacy / "PERSONA.md").write_text("# Persona\n\n**Born:** 2026-05-01\n", encoding="utf-8")
        run(project, "--today", "2026-10-15")
        self.assertEqual((target_of(project) / "memory/.born").read_text().strip(), "2026-05-01")
        (legacy / "PERSONA.md").write_text("# Persona\n", encoding="utf-8")
        run(project, "--today", "2026-10-15", "--force")
        self.assertEqual((target_of(project) / "memory/.born").read_text().strip(), "2026-10-15")

    def test_backup_is_written_by_default_and_lists_the_source(self):
        project = make_project(self.tmp_path)
        import tarfile
        code, out = run(project, "--today", "2026-10-15", backup=True)
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "written")
        archive = Path(out["backup_path"])
        self.assertEqual(archive.parent, project / "_bmad" / "backups")
        self.assertTrue(archive.name.startswith("mac-sanctum-v2-"))
        legacy = project / "_bmad" / "_memory" / "band-manager-sidecar"
        expected = {"band-manager-sidecar/" + p.relative_to(legacy).as_posix() for p in legacy.rglob("*") if p.is_file()}
        with tarfile.open(archive) as tar:
            self.assertLessEqual(expected, {m.name for m in tar.getmembers() if m.isfile()})

    def test_backup_includes_an_existing_target_on_force(self):
        project = make_project(self.tmp_path)
        import tarfile
        target_of(project).mkdir(parents=True)
        (target_of(project) / "PERSONA.md").write_text("already here")
        code, out = run(project, "--force", backup=True)
        self.assertEqual(code, 0)
        with tarfile.open(out["backup_path"]) as tar:
            self.assertIn("suno-agent-band-manager/PERSONA.md", tar.getnames())

    def test_no_backup_and_dry_run_report_null_backup_path(self):
        project = make_project(self.tmp_path)
        self.assertIsNone(run(project, "--dry-run", backup=True)[1]["backup_path"])
        self.assertFalse((project / "_bmad" / "backups").exists())
        self.assertIsNone(run(project)[1]["backup_path"])
        self.assertFalse((project / "_bmad" / "backups").exists())

    def test_failed_backup_refuses_and_writes_nothing(self):
        project = make_project(self.tmp_path)
        blocker = project / "not-a-dir"
        blocker.write_text("a file where the backup folder should be")
        code, out = run(project, "--backup-dir", str(blocker / "sub"), backup=True)
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "refused")
        self.assertIn("backup failed", out["reason"])
        self.assertFalse(target_of(project).exists())

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
        self.assertIsNone(archive)
        self.assertIn("does not list the source", reason)
        self.assertFalse((tmp_path / "bk" / "mac-sanctum-v2-stamp.tar.gz").exists())

    def test_verify_flags_missing_and_changed_files(self):
        project = make_project(self.tmp_path)
        tmp_path = self.tmp_path
        legacy = project / "_bmad" / "_memory" / "band-manager-sidecar"
        plan = mod.build_plan(legacy, skill_of(project), "2026-10-15", project)
        target = tmp_path / "out"
        mod.write(plan, target)
        self.assertEqual(mod.verify(plan, target), [])
        (target / "PERSONA.md").unlink()
        (target / "memory/.tended").write_text("")
        (target / "capabilities/liner-notes.md").write_text("changed size\n")
        self.assertEqual(mod.verify(plan, target), ["PERSONA.md", "capabilities/liner-notes.md", "memory/.tended"])

    def test_bad_today_is_exit_2(self):
        project = make_project(self.tmp_path)
        code, out = run(project, "--today", "15-10-2026")
        self.assertEqual(code, 2)
        self.assertEqual(out["status"], "error")

    def test_shipped_skill_converts_to_a_v7_sanctum(self):
        """Smoke check with the shipped templates: shape only."""
        project = make_project(self.tmp_path)
        code, out = run(project, "--today", "2026-10-15", shipped=True)
        self.assertEqual((code, out["status"]), (0, "written"))
        self.assertEqual(seed.classify_sanctum(target_of(project))["sidecar_format"], "v7")
        self.assertTrue((target_of(project) / "PULSE.md").read_text().strip())

    # --- nothing of the old store is dropped unreported -----------------------

    def test_default_fixture_places_no_preamble_or_boundaries_in_raw(self):
        """Title-and-blockquote banners are not owner text; a CREED with a Dominion takes the boundaries."""
        project = make_project(self.tmp_path)
        code, out = run(project, "--dry-run")
        unplaced = sorted(e["to"] for e in out["entries"] if e["to"].startswith("raw/unplaced-"))
        self.assertEqual(unplaced, ["raw/unplaced-stray-notes.md"])

    def test_other_files_in_sessions_are_kept_in_raw(self):
        project = make_project(self.tmp_path)
        sessions = legacy_of(project) / "sessions"
        (sessions / "notes.txt").write_text("a text note\n")
        (sessions / "audio").mkdir()
        (sessions / "audio" / "take.wav").write_bytes(b"RIFF\x00\xff\x00")
        (sessions / "older").mkdir()
        (sessions / "older" / "2026-01-01.md").write_text("# nested log\n")
        expected = {
            "sessions/notes.txt": "raw/unplaced-sessions-notes.txt",
            "sessions/audio/take.wav": "raw/unplaced-sessions-audio-take.wav",
            "sessions/older/2026-01-01.md": "raw/unplaced-sessions-older-2026-01-01.md",
        }
        code, planned = run(project, "--dry-run")
        self.assertEqual({e["from"]: e["to"] for e in planned["entries"] if e["from"] in expected}, expected)
        code, out = run(project)
        self.assertEqual((code, out["status"]), (0, "written"))
        for src, dest in expected.items():
            self.assertEqual((target_of(project) / dest).read_bytes(), (legacy_of(project) / src).read_bytes(), src)
        # The dated logs are still converted, not copied twice.
        self.assertTrue((target_of(project) / "raw/2026-09-22-session-log.md").is_file())
        self.assertFalse((target_of(project) / "raw/unplaced-sessions-2026-09-22.md").exists())

    def test_boundaries_are_kept_when_the_creed_has_no_dominion(self):
        project = make_project(self.tmp_path)
        legacy = legacy_of(project)
        creed = (legacy / "CREED.md").read_text()
        cut = creed.index("## Dominion (Access Boundaries)")
        (legacy / "CREED.md").write_text(creed[:cut] + creed[creed.index("## Discipline Shards"):])
        code, out = run(project)
        self.assertEqual((code, out["status"]), (0, "written"))
        entry = next(e for e in out["entries"] if e["from"] == "access-boundaries.md")
        self.assertEqual(entry["to"], "raw/unplaced-access-boundaries.md")
        kept = (target_of(project) / "raw/unplaced-access-boundaries.md").read_text()
        self.assertTrue(kept.startswith("---\nstatus: raw\n"))
        self.assertTrue(kept.endswith(BOUNDARIES))
        self.assertNotIn("### Read Access", (target_of(project) / "CREED.md").read_text())
        # The wake lists it as undistilled, so it is not forgotten there either.
        self.assertEqual(seed.undistilled_raw(target_of(project)), ["unplaced-access-boundaries.md"])

    def test_owner_text_above_the_first_heading_is_kept_in_raw(self):
        project = make_project(self.tmp_path)
        legacy = legacy_of(project)
        edits = {
            "MEMORY.md": ("# Mac — Curated Memory\n", "# Mac — Curated Memory\n\nOwner: mornings only.\n"),
            "chronology.md": ("# Session Chronology\n", "# Session Chronology\n\nKept since the first tour.\n"),
            "creed-disciplines.md": ("> Loaded on demand.\n", "> Loaded on demand.\n\nMy own rule of thumb.\n"),
            "creed-package-assembly.md": ("# Mac — Creed Shard: Package Assembly\n",
                                          "# Mac — Creed Shard: Package Assembly\n\nNever skip the builder.\n"),
        }
        for name, (old, new) in edits.items():
            text = (legacy / name).read_text()
            self.assertIn(old, text)
            (legacy / name).write_text(text.replace(old, new, 1))
        code, out = run(project)
        self.assertEqual((code, out["status"]), (0, "written"))
        placed = {e["from"]: e["to"] for e in out["entries"] if e["section"] == "(preamble)"}
        self.assertEqual(placed, {
            "MEMORY.md": "raw/unplaced-MEMORY-preamble.md",
            "chronology.md": "raw/unplaced-chronology-preamble.md",
            "creed-disciplines.md": "raw/unplaced-creed-disciplines-preamble.md",
            "creed-package-assembly.md": "raw/unplaced-creed-package-assembly-preamble.md",
        })
        for name, (_, new) in edits.items():
            kept = (target_of(project) / placed[name]).read_text()
            self.assertTrue(kept.startswith("---\nstatus: raw\n"), name)
            self.assertIn(new.splitlines()[-1], kept)
        self.assertFalse((target_of(project) / "raw/unplaced-creed-workshop-capture-preamble.md").exists())

    def test_unexpected_folder_is_reported_in_dropped(self):
        """The one signal that a whole folder will not reach the new sanctum."""
        project = make_project(self.tmp_path)
        (legacy_of(project) / "daily").mkdir()
        (legacy_of(project) / "daily" / "x.md").write_text("note")
        entry = {"from": "daily", "section": None, "why": "unexpected folder; not copied"}
        code, planned = run(project, "--dry-run")
        self.assertIn(entry, planned["dropped"])
        code, out = run(project)
        self.assertEqual((code, out["status"]), (0, "written"))
        self.assertIn(entry, out["dropped"])
        self.assertFalse(any("daily" in rel for rel in snapshot(target_of(project))))

    # --- refusals before anything is planned ---------------------------------

    def test_source_that_is_not_a_complete_v2_store_is_refused(self):
        project = make_project(self.tmp_path)
        (legacy_of(project) / "BOND.md").unlink()
        for extra in ((), ("--dry-run",)):
            with self.subTest(extra=extra):
                code, out = run(project, *extra)
                self.assertEqual((code, out["status"], out["sidecar_format"]), (1, "refused", "damaged"))
                self.assertIn("not a complete v2 store", out["reason"])
                self.assertIn("BOND.md", out["reason"])
                self.assertFalse(target_of(project).exists())

    def test_v1_source_is_sent_to_the_first_hop(self):
        project = self.tmp_path
        make_skill(project)
        legacy = legacy_of(project)
        legacy.mkdir(parents=True)
        (legacy / "index.md").write_text("# v1 store\n\n## User Preferences\n\n- x\n")
        code, out = run(project)
        self.assertEqual((code, out["status"], out["sidecar_format"]), (1, "refused", "v1"))
        self.assertIn("migrate_sidecar_to_v2.py --in-place", out["reason"])
        self.assertFalse(target_of(project).exists())

    def test_skill_without_the_templates_is_refused(self):
        project = make_project(self.tmp_path)
        (skill_of(project) / "assets" / "HOW-I-REMEMBER-template.md").unlink()
        code, out = run(project)
        self.assertEqual((code, out["status"]), (1, "refused"))
        self.assertIn("assets/HOW-I-REMEMBER-template.md", out["reason"])
        self.assertFalse(target_of(project).exists())

    def test_source_file_that_is_not_utf8_is_refused_with_its_name(self):
        for name in ("MEMORY.md", "sessions/2026-09-14.md", "chronology.md"):
            with self.subTest(name=name):
                project = make_project(self.tmp_path / name.replace("/", "-"))
                (legacy_of(project) / name).write_bytes(b"# Title\n\n## Section\n\ncaf\xe9 notes\n")
                before = snapshot(legacy_of(project))
                code, out = run(project)  # run() fails the test on any traceback
                self.assertEqual((code, out["status"]), (1, "refused"))
                self.assertIn("cannot read the old store", out["reason"])
                self.assertIn(name, out["reason"])
                self.assertFalse(target_of(project).exists())
                self.assertEqual(snapshot(legacy_of(project)), before)

    def test_target_that_is_a_file_is_refused(self):
        project = make_project(self.tmp_path)
        target_of(project).parent.mkdir(parents=True)
        target_of(project).write_text("not a folder")
        code, out = run(project, "--force")
        self.assertEqual((code, out["status"]), (1, "refused"))
        self.assertIn("not a directory", out["reason"])


class ConversionFailureTests(TempDirMixin, unittest.TestCase):
    """main() driven in-process, with one step made to fail: what the JSON says and
    what is left on disk. The target is written beside itself and moved into place,
    so a failed or killed run leaves it as it was."""

    def setUp(self):
        super().setUp()
        self.project = make_project(self.tmp_path)
        self.target = target_of(self.project)
        self.staging = mod.staging_dir(self.target)
        self.source_before = snapshot(legacy_of(self.project))

    def main(self, *argv):
        args = ["migrate_sanctum_to_v7.py", str(self.project), "--no-backup",
                "--skill-path", str(skill_of(self.project)), "--today", "2026-10-15", *argv]
        with mock.patch.object(sys, "argv", args), self.capsys():
            code = mod.main()
        return code, json.loads(self.capsys.readouterr().out)

    def assert_nothing_left(self):
        self.assertFalse(self.target.exists())
        self.assertFalse(self.staging.exists())
        self.assertEqual(snapshot(legacy_of(self.project)), self.source_before)
        # The next wake still finds the old store and routes to the conversion.
        self.assertEqual(seed.locate_sanctum(self.project)[1]["sidecar_format"], "v2")

    def test_failed_post_write_check_is_refused_with_the_files_named(self):
        with mock.patch.object(mod, "verify", lambda plan, target: ["PERSONA.md"]):
            code, out = self.main()
        self.assertEqual((code, out["status"]), (1, "refused"))
        self.assertIn("post-write check failed", out["reason"])
        self.assertEqual(out["target_written"], "none")
        self.assertEqual(out["unverified"], ["PERSONA.md"])
        self.assert_nothing_left()

    def test_post_write_check_runs_on_what_was_written(self):
        """A write that leaves a planned file short is caught by the real check."""
        real_write = mod.write

        def short_write(plan, target):
            real_write(plan, target)
            (target / "PERSONA.md").unlink()

        with mock.patch.object(mod, "write", short_write):
            code, out = self.main()
        self.assertEqual((code, out["status"], out["unverified"]), (1, "refused", ["PERSONA.md"]))
        self.assert_nothing_left()

    def test_write_failure_is_refused_and_leaves_no_target(self):
        def failing_write(plan, target):
            (target / "PERSONA.md").parent.mkdir(parents=True, exist_ok=True)
            (target / "PERSONA.md").write_text("half")
            raise OSError("No space left on device")

        with mock.patch.object(mod, "write", failing_write):
            code, out = self.main()
        self.assertEqual((code, out["status"], out["target_written"]), (1, "refused", "none"))
        self.assertIn("No space left on device", out["reason"])
        self.assertNotIn("unverified", out)
        self.assert_nothing_left()

    def test_killed_conversion_leaves_no_partial_sanctum_and_reruns_clean(self):
        """The process dies mid-write: nothing is at the v7 path, and the next run converts."""
        def killed_write(plan, target):
            (target / "PERSONA.md").parent.mkdir(parents=True, exist_ok=True)
            (target / "PERSONA.md").write_text("half")
            raise KeyboardInterrupt  # no cleanup runs, as when the session is closed

        with mock.patch.object(mod, "write", killed_write), self.capsys():
            with mock.patch.object(sys, "argv", ["migrate_sanctum_to_v7.py", str(self.project), "--no-backup",
                                                 "--skill-path", str(skill_of(self.project))]):
                with self.assertRaises(KeyboardInterrupt):
                    mod.main()
        self.assertFalse(self.target.exists())
        self.assertTrue(self.staging.is_dir())  # the leftover the next run clears
        self.assertEqual(seed.locate_sanctum(self.project)[1]["sidecar_format"], "v2")
        code, out = self.main()
        self.assertEqual((code, out["status"]), (0, "written"))
        self.assertEqual(seed.classify_sanctum(self.target)["sidecar_format"], "v7")
        self.assertEqual((self.target / "PERSONA.md").read_text(), "# Persona\n\nNOLA soul.\n")
        self.assertFalse(self.staging.exists())

    def test_failed_move_into_place_is_refused_and_force_keeps_the_old_target(self):
        self.target.mkdir(parents=True)
        (self.target / "PERSONA.md").write_text("already here")
        (self.target / "memory").mkdir()
        (self.target / "memory" / "owner-note.md").write_text("written since\n")
        before = snapshot(self.target)
        real_replace = mod.os.replace
        calls = []

        def replace_failing_second(src, dst):
            calls.append((Path(src).name, Path(dst).name))
            if len(calls) == 2:
                raise OSError("Device or resource busy")
            return real_replace(src, dst)

        with mock.patch.object(mod.os, "replace", replace_failing_second):
            code, out = self.main("--force")
        self.assertEqual((code, out["status"], out["target_written"]), (1, "refused", "none"))
        self.assertIn("Device or resource busy", out["reason"])
        self.assertEqual(len(calls), 3)  # aside, the failed move, the restore
        self.assertEqual(snapshot(self.target), before)
        self.assertEqual(sorted(p.name for p in self.target.parent.iterdir()), [self.target.name])

    def test_failed_move_and_failed_restore_say_where_the_old_target_is(self):
        self.target.mkdir(parents=True)
        (self.target / "PERSONA.md").write_text("already here")
        real_replace = mod.os.replace
        calls = []

        def replace_only_once(src, dst):
            calls.append(src)
            if len(calls) > 1:
                raise OSError("Device or resource busy")
            return real_replace(src, dst)

        with mock.patch.object(mod.os, "replace", replace_only_once):
            code, out = self.main("--force")
        self.assertEqual((code, out["status"], out["target_written"]), (1, "refused", "moved-aside"))
        self.assertEqual((Path(out["moved_to"]) / "PERSONA.md").read_text(), "already here")
        self.assertIn(out["moved_to"], out["reason"])

    def test_force_overlays_the_plan_on_what_the_target_holds(self):
        self.target.mkdir(parents=True)
        (self.target / "PERSONA.md").write_text("already here")
        (self.target / "memory").mkdir()
        (self.target / "memory" / "owner-note.md").write_text("written since\n")
        code, out = self.main("--force")
        self.assertEqual((code, out["status"]), (0, "written"))
        self.assertEqual((self.target / "PERSONA.md").read_text(), "# Persona\n\nNOLA soul.\n")
        self.assertEqual((self.target / "memory" / "owner-note.md").read_text(), "written since\n")
        self.assertEqual(sorted(p.name for p in self.target.parent.iterdir()), [self.target.name])


if __name__ == "__main__":
    unittest.main()
