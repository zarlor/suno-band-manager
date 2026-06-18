#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Migration of Mac's legacy (v1) sidecar into a v2 sanctum.

Two modes:

1. STAGING mode (default, `--out DIR`) — NON-DESTRUCTIVE BY CONTRACT. NEVER
   writes to or modifies the source sidecar. Reads the live sidecar and writes a
   complete v2 sanctum layout into an output directory (default:
   {project-root}/_bmad/_memory/.sidecar-v2-staging). Nothing is cut over — a
   human reviews the staging dir and promotes it.

2. IN-PLACE mode (`--in-place`) — the scripted, safe automatic upgrade an
   existing user hits the first time they activate the v2 version. It backs the
   live sidecar up FIRST (dir + tarball), migrates to a temp staging dir, runs
   verify(), and ONLY swaps the live location into place if verify passes with
   all source content present. If verify fails it ABORTS and leaves the original
   untouched (Law 3 — never lose content). A v1 store is migrated; an already-v2
   store is a no-op; an absent sidecar is a no-op. Idempotent, safe to re-run.

What it does
------------
1. Parse the source `index.md` into ## sections and classify each as either
   NON-SESSION (preferences, derived catalog sections, module state, pending,
   session-history) or SESSION ("## Current Work — Session ..." /
   "## Prior Work — Session ..." narrative blocks).
2. NON-SESSION content -> staging `MEMORY.md`, preserving the derived-section
   marker pairs (<!-- derived:recently-published:start/end -->,
   <!-- derived:catalog-status:start/end -->) verbatim so
   regenerate-index-sections.py keeps working against the new file.
3. Each SESSION block -> staging `sessions/YYYY-MM-DD.md`, keyed by the first
   date token in the heading. Same-date blocks append to one file.
4. Seed PERSONA.md / CREED.md (+ shards + incident log) / BOND.md /
   CAPABILITIES.md / PULSE.md from the skill's assets/ templates, with config
   values substituted.
5. Build a thin INDEX.md map of the produced sanctum.
6. Copy (preserve) the bespoke organic files: patterns.md, chronology.md,
   access-boundaries.md, _collection_*.txt.

Usage
-----
    migrate-sidecar-to-v2.py --project-root PATH [--out DIR]
    migrate-sidecar-to-v2.py --project-root PATH --out DIR --verify
    migrate-sidecar-to-v2.py --project-root PATH --in-place --format json
    migrate-sidecar-to-v2.py --help

The --verify pass re-reads the produced staging dir and reports: # session
blocks found vs # session files written, derived-marker presence in MEMORY.md,
a char-accounting check (source index.md content vs migrated content), and the
full list of files produced.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tarfile
from datetime import date, datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_sanctum_seed():
    """Import the shared seed module by path (hyphenated script dir, no package)."""
    seed_path = Path(__file__).resolve().parent / "_sanctum_seed.py"
    spec = spec_from_file_location("_sanctum_seed", seed_path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_seed = _load_sanctum_seed()
shard_creed = _seed.shard_creed  # single source of the creed-sharding logic

SKILL_NAME = "suno-agent-band-manager"
SANCTUM_REL = ("_bmad", "_memory", "band-manager-sidecar")
DEFAULT_OUT_REL = ("_bmad", "_memory", ".sidecar-v2-staging")

# Bespoke organic files preserved verbatim (copied, never rewritten).
PRESERVED_FILES = [
    "patterns.md",
    "chronology.md",
    "access-boundaries.md",
    "_collection_extracted.txt",
    "_collection_layout.txt",
    "_collection_reflow.txt",
]

# Templates → output filenames in the staging sanctum.
TEMPLATE_MAP = {
    "INDEX-template.md": "INDEX.md",
    "PERSONA-template.md": "PERSONA.md",
    "CREED-template.md": "CREED.md",
    "BOND-template.md": "BOND.md",
    "MEMORY-template.md": "MEMORY.md",  # MEMORY is woven, not copied — see below.
    "PULSE-template.md": "PULSE.md",
}

DERIVED_MARKERS = ["recently-published", "catalog-status"]

SESSION_HEADING_RE = re.compile(
    r"^##\s+(?:Current Work|Prior Work)\b", re.IGNORECASE
)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
SECTION_SPLIT_RE = re.compile(r"(?m)^(?=##\s)")


# ---------------------------------------------------------------------------
# Config + substitution
# ---------------------------------------------------------------------------


def parse_yaml_config(config_path: Path) -> dict:
    config: dict[str, str] = {}
    if not config_path.exists():
        return config
    for line in config_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.strip().strip("'\"")
            if value:
                config[key.strip()] = value
    return config


def build_variables(project_root: Path) -> dict:
    bmad_dir = project_root / "_bmad"
    config: dict[str, str] = {}
    for config_file in ("config.yaml", "config.user.yaml"):
        config.update(parse_yaml_config(bmad_dir / config_file))
    return {
        "user_name": config.get("user_name", "friend"),
        "communication_language": config.get("communication_language", "English"),
        "birth_date": date.today().isoformat(),
        "project_root": str(project_root),
    }


def substitute_vars(content: str, variables: dict) -> str:
    for key, value in variables.items():
        content = content.replace(f"{{{key}}}", value)
    return content


# ---------------------------------------------------------------------------
# index.md parsing / classification
# ---------------------------------------------------------------------------


def split_sections(index_text: str) -> tuple[str, list[str]]:
    """Split index.md into (preamble, [section_text, ...]) on top-level ## headings.

    The preamble is any content before the first ## heading (e.g. the
    "# Mac — Session Index" title line). Each section string starts with its
    "## " heading and runs to just before the next "## " heading.
    """
    parts = SECTION_SPLIT_RE.split(index_text)
    if not parts:
        return "", []
    # parts[0] is the preamble (may be empty); the rest each start with "## ".
    preamble = parts[0]
    sections = [p for p in parts[1:] if p.strip()]
    if preamble.strip() and not preamble.lstrip().startswith("##"):
        return preamble, sections
    # If the file starts directly with "## ", preamble is empty and parts[0]
    # would itself be a section.
    if preamble.strip().startswith("##"):
        return "", [p for p in parts if p.strip()]
    return preamble, sections


def heading_of(section: str) -> str:
    return section.splitlines()[0].strip() if section.strip() else ""


def is_session_section(section: str) -> bool:
    return bool(SESSION_HEADING_RE.match(section.lstrip()))


def session_date(section: str) -> str:
    """First date token in the heading; falls back to first date in the body."""
    heading = heading_of(section)
    m = DATE_RE.search(heading)
    if m:
        return m.group(1)
    m = DATE_RE.search(section)
    return m.group(1) if m else "undated"


# ---------------------------------------------------------------------------
# Output assembly
# ---------------------------------------------------------------------------


def build_memory(
    template_text: str,
    non_session_sections: list[str],
    current_work_pointer: str | None,
    variables: dict,
) -> str:
    """Weave MEMORY.md from the template header + the source non-session content.

    The template supplies the curated header (owner/born banner). We then append
    the source's non-session sections VERBATIM (preferences, derived catalog
    sections with their markers, module state, pending/parked, session history).
    This preserves the derived-section marker pairs exactly as the source had
    them, so regenerate-index-sections.py keeps working.
    """
    # Use only the template's top banner (everything before the first "## ").
    banner_parts = SECTION_SPLIT_RE.split(template_text)
    banner = banner_parts[0] if banner_parts else template_text
    banner = substitute_vars(banner, variables).rstrip() + "\n"

    chunks = [banner]
    if current_work_pointer:
        chunks.append(current_work_pointer.rstrip() + "\n")
    for section in non_session_sections:
        chunks.append(section.rstrip() + "\n")
    return "\n".join(chunks).rstrip() + "\n"


def current_work_pointer_block(current_section: str | None) -> str | None:
    """A short MEMORY.md pointer at the most-recent Current Work session file.

    The full narrative lives in sessions/YYYY-MM-DD.md (not loaded on rebirth).
    MEMORY.md gets a one-line pointer so the rebirth read knows where the active
    thread's detail lives without carrying the whole block.
    """
    if not current_section:
        return None
    d = session_date(current_section)
    heading = heading_of(current_section)
    # Strip the leading "## " for a cleaner pointer line.
    heading_text = heading[3:].strip() if heading.startswith("##") else heading
    return (
        "## Current Work\n\n"
        f"Active thread: **{heading_text}**. Full session detail lives in the raw "
        f"layer at `sessions/{d}.md` (not loaded on rebirth). Distill the live "
        "state up into this section as the work progresses.\n"
    )


# ---------------------------------------------------------------------------
# Creed sharding — the slicing logic now lives in the shared `_sanctum_seed`
# module so BOTH this migration tool and init-sanctum.py shard the source creed
# identically. `shard_creed` is imported at the top of this file.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Migration driver
# ---------------------------------------------------------------------------


def migrate(project_root: Path, sanctum_path: Path, out_dir: Path, skill_path: Path) -> dict:
    """Run the migration. READ-ONLY on sanctum_path; writes only under out_dir."""
    index_path = sanctum_path / "index.md"
    if not index_path.exists():
        return {"status": "error", "message": f"Source index.md not found at {index_path}"}

    assets_dir = skill_path / "assets"
    references_dir = skill_path / "references"
    variables = build_variables(project_root)

    index_text = index_path.read_text(encoding="utf-8")
    preamble, sections = split_sections(index_text)

    session_sections: list[str] = []
    non_session_sections: list[str] = []
    current_work_section: str | None = None
    for section in sections:
        if is_session_section(section):
            session_sections.append(section)
            if section.lstrip().lower().startswith("## current work"):
                current_work_section = section
        else:
            non_session_sections.append(section)

    # Fresh staging dir (idempotent: wipe + rebuild so reruns are clean).
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    (out_dir / "sessions").mkdir()
    (out_dir / "capabilities").mkdir()

    produced: list[str] = []

    # --- MEMORY.md (woven, with derived markers preserved) ---
    memory_template = (assets_dir / "MEMORY-template.md").read_text(encoding="utf-8")
    pointer = current_work_pointer_block(current_work_section)
    memory_text = build_memory(
        memory_template, non_session_sections, pointer, variables
    )
    (out_dir / "MEMORY.md").write_text(memory_text, encoding="utf-8")
    produced.append("MEMORY.md")

    # --- sessions/YYYY-MM-DD.md (one file per date; same-date appends) ---
    by_date: dict[str, list[str]] = {}
    for section in session_sections:
        by_date.setdefault(session_date(section), []).append(section)
    for d, secs in sorted(by_date.items()):
        body = "\n\n".join(s.rstrip() for s in secs)
        header = (
            f"# Session Log — {d}\n\n"
            "> Raw session narrative migrated from the legacy index.md. NOT "
            "loaded on rebirth — curated material lives in MEMORY.md.\n\n"
        )
        (out_dir / "sessions" / f"{d}.md").write_text(header + body + "\n", encoding="utf-8")
        produced.append(f"sessions/{d}.md")

    # --- Template-seeded sanctum files (skip MEMORY — already woven) ---
    for template_name, out_name in TEMPLATE_MAP.items():
        if out_name == "MEMORY.md":
            continue
        template_path = assets_dir / template_name
        if not template_path.exists():
            continue
        content = substitute_vars(template_path.read_text(encoding="utf-8"), variables)
        (out_dir / out_name).write_text(content, encoding="utf-8")
        produced.append(out_name)

    # --- Creed shards + incident log (seeded from the skill creed) ---
    creed_src = references_dir / "creed.md"
    if creed_src.exists():
        for shard_name, shard_text in shard_creed(creed_src.read_text(encoding="utf-8")).items():
            (out_dir / shard_name).write_text(shard_text, encoding="utf-8")
            produced.append(shard_name)

    # --- CAPABILITIES.md (pointer at the skill roster) ---
    caps = (
        "# Capabilities\n\n## Built-in\n\n"
        "_Mac's capability roster (external skills, audio analysis, playlist "
        "sequencing) lives in the skill's `references/capabilities.md`. Load it "
        "for the full list._\n\n"
        "## Learned\n\n"
        "_Owner-taught capability prompts live in `capabilities/`._\n\n"
        "| Code | Name | Description | Source | Added |\n"
        "|------|------|-------------|--------|-------|\n"
    )
    (out_dir / "CAPABILITIES.md").write_text(caps, encoding="utf-8")
    produced.append("CAPABILITIES.md")

    # --- Preserve bespoke organic files (copy verbatim) ---
    preserved: list[str] = []
    for name in PRESERVED_FILES:
        src = sanctum_path / name
        if src.exists():
            shutil.copy2(src, out_dir / name)
            produced.append(name)
            preserved.append(name)

    return {
        "status": "migrated",
        "out_dir": str(out_dir),
        "session_blocks_found": len(session_sections),
        "session_files_written": len(by_date),
        "non_session_sections": len(non_session_sections),
        "preserved_files": preserved,
        "files_produced": sorted(produced),
        "message": (
            f"Migrated to staging at {out_dir}: {len(session_sections)} session "
            f"blocks → {len(by_date)} session files; {len(non_session_sections)} "
            f"non-session sections → MEMORY.md; {len(preserved)} bespoke files "
            "preserved."
        ),
    }


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------


def _strip_template_scaffolding(text: str) -> str:
    """Remove blockquote-prefixed template guidance lines for char accounting.

    Template-injected guidance (lines beginning with '>') and the woven banner
    aren't source content, so they shouldn't count toward the accounting that
    asks "did we drop any SOURCE content?". We keep all non-'>' lines.
    """
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(">")
    )


def _normalize(text: str) -> str:
    """Collapse whitespace for a robust content-presence comparison."""
    return re.sub(r"\s+", "", text)


def verify(sanctum_path: Path, out_dir: Path) -> dict:
    """Re-read source + staging and produce a verification report."""
    index_path = sanctum_path / "index.md"
    findings: list[str] = []

    index_text = index_path.read_text(encoding="utf-8")
    _, sections = split_sections(index_text)
    src_session_sections = [s for s in sections if is_session_section(s)]
    src_non_session = [s for s in sections if not is_session_section(s)]

    # Session file count.
    sessions_dir = out_dir / "sessions"
    session_files = sorted(sessions_dir.glob("*.md")) if sessions_dir.is_dir() else []
    expected_dates = {session_date(s) for s in src_session_sections}
    written_dates = {f.stem for f in session_files}

    if expected_dates != written_dates:
        findings.append(
            f"session date mismatch: expected {sorted(expected_dates)} "
            f"got {sorted(written_dates)}"
        )

    # Derived marker presence in MEMORY.md.
    memory_path = out_dir / "MEMORY.md"
    memory_text = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
    marker_status: dict[str, bool] = {}
    for marker in DERIVED_MARKERS:
        has_start = f"<!-- derived:{marker}:start -->" in memory_text
        has_end = f"<!-- derived:{marker}:end -->" in memory_text
        marker_status[marker] = has_start and has_end
        if not (has_start and has_end):
            findings.append(f"derived marker pair missing in MEMORY.md: {marker}")

    # Char accounting: every source SECTION's normalized content must appear
    # somewhere in the produced output (MEMORY.md + session files).
    output_blob = memory_text
    for f in session_files:
        output_blob += f.read_text(encoding="utf-8")
    output_norm = _normalize(_strip_template_scaffolding(output_blob))

    dropped_sections: list[str] = []
    src_section_chars = 0
    for section in src_session_sections + src_non_session:
        src_section_chars += len(section)
        section_norm = _normalize(section)
        if section_norm and section_norm not in output_norm:
            dropped_sections.append(heading_of(section))

    if dropped_sections:
        findings.append(
            f"{len(dropped_sections)} source section(s) not found verbatim in "
            f"output: {dropped_sections}"
        )

    # Preserved-file integrity (byte-identical copies).
    preserved_ok: dict[str, bool] = {}
    for name in PRESERVED_FILES:
        src = sanctum_path / name
        dst = out_dir / name
        if src.exists():
            ok = dst.exists() and src.read_bytes() == dst.read_bytes()
            preserved_ok[name] = ok
            if not ok:
                findings.append(f"preserved file not byte-identical: {name}")

    files_produced = sorted(
        str(p.relative_to(out_dir)) for p in out_dir.rglob("*") if p.is_file()
    )

    return {
        "status": "pass" if not findings else "fail",
        "session_blocks_found": len(src_session_sections),
        "session_files_written": len(session_files),
        "session_dates_match": expected_dates == written_dates,
        "derived_markers": marker_status,
        "char_accounting": {
            "source_section_chars": src_section_chars,
            "output_chars": len(output_blob),
            "dropped_sections": dropped_sections,
            "all_sections_present": not dropped_sections,
        },
        "preserved_files_byte_identical": preserved_ok,
        "files_produced": files_produced,
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# In-place upgrade (backup → migrate → verify → swap, abort-on-loss)
# ---------------------------------------------------------------------------


def sidecar_state(sanctum_path: Path) -> str:
    """Classify the live sidecar: 'absent' | 'v2' | 'v1' | 'damaged'.

    Mirrors pre-activate.py's detection so the router and this driver agree:
    MEMORY.md (or another v2 spine file) ⇒ v2; index.md with no v2 marker ⇒ v1;
    a dir with neither ⇒ damaged; no dir ⇒ absent.
    """
    if not sanctum_path.exists():
        return "absent"
    if (
        (sanctum_path / "MEMORY.md").is_file()
        or (sanctum_path / "CREED.md").is_file()
        or (sanctum_path / "INDEX.md").is_file()
    ):
        return "v2"
    if (sanctum_path / "index.md").is_file():
        return "v1"
    return "damaged"


def _timestamp() -> str:
    """Stable backup suffix: YYYYMMDD-HHMMSS (local time)."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _backup_sidecar(sanctum_path: Path, memory_root: Path, stamp: str) -> tuple[Path, Path]:
    """Copy the live sidecar to a timestamped backup dir AND a .tar.gz.

    Returns (backup_dir, backup_tarball). Both live alongside the sidecar in
    `memory_root` (the sidecar's parent) so a rollback is a single move/extract.
    """
    backup_dir = memory_root / f".sidecar-backup-pre-v2-{stamp}"
    # If a same-second backup dir somehow exists, clear it for a clean copy.
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    shutil.copytree(sanctum_path, backup_dir)

    backup_tarball = memory_root / f".sidecar-backup-pre-v2-{stamp}.tar.gz"
    with tarfile.open(backup_tarball, "w:gz") as tar:
        tar.add(sanctum_path, arcname=sanctum_path.name)

    return backup_dir, backup_tarball


def migrate_in_place(
    project_root: Path, sanctum_path: Path, skill_path: Path
) -> dict:
    """Safely upgrade a v1 sidecar to v2 IN PLACE: backup → migrate → verify → swap.

    Steps:
      a. Classify. already-v2 → no-op {status: "already-v2"}; absent → no-op
         {status: "no-sidecar"}; damaged → {status: "blocked"} (no content store
         to migrate — the router offers re-scaffold, not migration). Only a v1
         sidecar proceeds.
      b. Back up FIRST — copy the live sidecar to
         .sidecar-backup-pre-v2-{stamp}/ AND a matching .tar.gz.
      c. Migrate to a temp staging dir (reuses migrate()).
      d. verify(). If status != "pass" OR all_sections_present is false → ABORT:
         do NOT swap, leave the original untouched, clean up staging, return
         {status: "blocked", reason: ...}. (Law 3 — never lose content.)
      e. Verified pass → swap: move the live sidecar aside to a backup-old dir,
         move staging into the live location.
      f. Return {status: "migrated", backup_path, backup_tarball, sanctum_path,
         verify, session_files, files}.

    Idempotent and safe to re-run: a second run sees a v2 sidecar and no-ops.
    """
    state = sidecar_state(sanctum_path)
    if state == "v2":
        return {"status": "already-v2", "sanctum_path": str(sanctum_path)}
    if state == "absent":
        return {"status": "no-sidecar", "sanctum_path": str(sanctum_path)}
    if state == "damaged":
        return {
            "status": "blocked",
            "reason": (
                "sidecar has neither index.md (v1) nor MEMORY.md (v2) — no "
                "recognizable content store to migrate; re-scaffold instead"
            ),
            "sanctum_path": str(sanctum_path),
        }

    # --- v1: do the safe cutover ---
    memory_root = sanctum_path.parent
    stamp = _timestamp()

    # (b) Back up FIRST — before we touch anything.
    backup_dir, backup_tarball = _backup_sidecar(sanctum_path, memory_root, stamp)

    # (c) Migrate to a temp staging dir (sibling, hidden, stamped → never clobbers).
    staging_dir = memory_root / f".sidecar-v2-staging-{stamp}"
    migrate_result = migrate(project_root, sanctum_path, staging_dir, skill_path)
    if migrate_result["status"] != "migrated":
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        return {
            "status": "blocked",
            "reason": f"migration failed: {migrate_result.get('message', 'unknown error')}",
            "backup_path": str(backup_dir),
            "backup_tarball": str(backup_tarball),
            "sanctum_path": str(sanctum_path),
        }

    # (d) Verify the staging dir against the (still-untouched) source. Abort on loss.
    report = verify(sanctum_path, staging_dir)
    if report["status"] != "pass" or not report["char_accounting"]["all_sections_present"]:
        shutil.rmtree(staging_dir)
        return {
            "status": "blocked",
            "reason": (
                "verify did not pass — refusing to swap so no content is lost "
                f"(findings: {report.get('findings', [])})"
            ),
            "backup_path": str(backup_dir),
            "backup_tarball": str(backup_tarball),
            "sanctum_path": str(sanctum_path),
            "verify": report,
        }

    # (e) Verified pass → swap. Move the live sidecar aside, then staging into place.
    # The backup dir already holds a copy; this "old" move is the rollback anchor
    # that the swap itself can restore from if the final move ever fails.
    old_aside = memory_root / f".sidecar-old-{stamp}"
    if old_aside.exists():
        shutil.rmtree(old_aside)
    shutil.move(str(sanctum_path), str(old_aside))
    try:
        shutil.move(str(staging_dir), str(sanctum_path))
    except OSError:
        # Swap failed mid-flight: restore the original from the aside copy so the
        # live location is never left empty.
        shutil.move(str(old_aside), str(sanctum_path))
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        return {
            "status": "blocked",
            "reason": "swap failed; original restored — sidecar left untouched",
            "backup_path": str(backup_dir),
            "backup_tarball": str(backup_tarball),
            "sanctum_path": str(sanctum_path),
        }
    # Swap succeeded; the aside copy is redundant with the timestamped backup.
    shutil.rmtree(old_aside)

    session_files = sorted(
        p.name for p in (sanctum_path / "sessions").glob("*.md")
    ) if (sanctum_path / "sessions").is_dir() else []
    files = sorted(
        str(p.relative_to(sanctum_path)) for p in sanctum_path.rglob("*") if p.is_file()
    )

    return {
        "status": "migrated",
        "backup_path": str(backup_dir),
        "backup_tarball": str(backup_tarball),
        "sanctum_path": str(sanctum_path),
        "verify": report,
        "session_files": session_files,
        "files": files,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "READ-ONLY migration of Mac's legacy sidecar into a v2 sanctum "
            "staging dir. Never modifies the source sidecar."
        )
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root (where _bmad/ lives). Default: current dir.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Staging output dir. Default: "
            "{project-root}/_bmad/_memory/.sidecar-v2-staging"
        ),
    )
    parser.add_argument(
        "--skill-path",
        default=None,
        help=(
            "Path to the skill dir (assets/ + references/ live here). Default: "
            "inferred as the parent of this script's directory."
        ),
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help=(
            "Upgrade the live sidecar IN PLACE (backup → migrate → verify → swap, "
            "abort-on-loss). Only migrates a v1 sidecar; already-v2 and absent are "
            "no-ops. Ignores --out. This is the automatic activation-time upgrade."
        ),
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="After migrating (or against an existing staging dir), run the verify report.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Skip migration; only run --verify against an existing staging dir.",
    )
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format."
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(f"ERROR: project root not found: {project_root}", file=sys.stderr)
        return 2

    sanctum_path = project_root.joinpath(*SANCTUM_REL)
    out_dir = (
        Path(args.out).resolve()
        if args.out
        else project_root.joinpath(*DEFAULT_OUT_REL)
    )
    skill_path = (
        Path(args.skill_path).resolve()
        if args.skill_path
        else Path(__file__).resolve().parent.parent
    )

    def emit(payload: dict) -> None:
        if args.format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(payload.get("message", json.dumps(payload, indent=2)))

    # --- In-place upgrade mode (the automatic activation-time path) ---
    if args.in_place:
        result = migrate_in_place(project_root, sanctum_path, skill_path)
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            status = result["status"]
            if status == "migrated":
                print(
                    f"Upgraded sidecar to v2 in place.\n"
                    f"  backup dir:     {result['backup_path']}\n"
                    f"  backup tarball: {result['backup_tarball']}\n"
                    f"  sanctum:        {result['sanctum_path']}\n"
                    f"  session files:  {len(result['session_files'])}\n"
                    f"  files:          {len(result['files'])}"
                )
            elif status == "already-v2":
                print("Sidecar is already v2 — nothing to upgrade.")
            elif status == "no-sidecar":
                print("No sidecar present — nothing to upgrade.")
            else:  # blocked
                print(f"BLOCKED: {result.get('reason', 'unknown')}")
        # migrated / already-v2 / no-sidecar are success exits; blocked is non-zero.
        return 0 if result["status"] in ("migrated", "already-v2", "no-sidecar") else 1

    if not args.verify_only:
        result = migrate(project_root, sanctum_path, out_dir, skill_path)
        if result["status"] == "error":
            emit(result)
            return 1
        emit(result)

    if args.verify or args.verify_only:
        report = verify(sanctum_path, out_dir)
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print("\n=== VERIFY ===")
            print(f"status: {report['status']}")
            print(
                f"session blocks found: {report['session_blocks_found']} | "
                f"session files written: {report['session_files_written']} | "
                f"dates match: {report['session_dates_match']}"
            )
            print(f"derived markers: {report['derived_markers']}")
            ca = report["char_accounting"]
            print(
                f"char accounting: source_section_chars={ca['source_section_chars']} "
                f"output_chars={ca['output_chars']} "
                f"all_sections_present={ca['all_sections_present']}"
            )
            if ca["dropped_sections"]:
                print(f"  DROPPED: {ca['dropped_sections']}")
            print(f"preserved byte-identical: {report['preserved_files_byte_identical']}")
            print(f"files produced ({len(report['files_produced'])}):")
            for f in report["files_produced"]:
                print(f"  - {f}")
            if report["findings"]:
                print("FINDINGS:")
                for f in report["findings"]:
                    print(f"  ! {f}")
        return 0 if report["status"] == "pass" else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
