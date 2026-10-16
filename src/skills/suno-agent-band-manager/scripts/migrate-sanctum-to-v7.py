#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Convert Mac's v2 sanctum to the BMad v7 memory layout (Continuity of Self).

The v2 sanctum (`_bmad/_memory/band-manager-sidecar/`) kept a hand-maintained
INDEX.md, one growing MEMORY.md, a long chronology and creed shards beside the
identity files. The v7 sanctum (`_bmad/memory/suno-agent-band-manager/`) keeps
five identity files that load at waking and many small files under `memory/`
and `raw/`, found with ls and grep and mapped by the waking script.

The conversion reads the old sanctum and writes a new one; it never modifies or
deletes the source. Every byte of the source lands somewhere (the plan lists
each file and section with its destination), except INDEX.md, whose job the
waking map now does.

  identity   PERSONA, BOND, CAPABILITIES copied; CREED gets
             access-boundaries.md as its Dominion section and the new shard
             paths; HOW-I-REMEMBER.md and PULSE.md are written from the
             skill's templates (PULSE keeps the owner's Pulse preferences)
  memory/    MEMORY.md sections -> standing files by kind; creed shards ->
             memory/disciplines/; incident log -> memory/incidents/;
             chronology entries -> memory/chronology/YYYY-MM-DD-<slug>.md
  raw/       session logs, the superseded patterns.md and the Collection
             exports, marked distilled (their content was curated up already)

Usage:
    uv run {skill-root}/scripts/migrate-sanctum-to-v7.py <project-root>
        [--from DIR] [--to DIR] [--skill-path DIR] [--dry-run] [--force]
        [--today YYYY-MM-DD] [--backup-dir DIR | --no-backup]

Default output is the plan as JSON. `--dry-run` writes nothing; without it the
new sanctum is written (refused when the target exists, unless --force).

Before writing, the script tars the source store (and an existing target, when
--force overwrites one) into `{project-root}/_bmad/backups/` (or --backup-dir)
and checks the archive lists every file; no verified backup, no conversion.
`--no-backup` skips it (tests). After writing, every planned file is checked to
exist with the planned content (copies: the source's size). The JSON carries
`backup_path`; any failure is `status: "refused"` with a `reason`.

The converted sanctum gets `memory/.tended` (the conversion is a tending),
`memory/.born` (the birth date from the old CREED.md or PERSONA.md
`**Born:**` line, else --today), so the wake reads it as a finished birth, and
`memory/.template-base.json`, which records the template text it was given
(HOW-I-REMEMBER.md, PULSE.md apart from the owner's preferences). The carried
over identity files and disciplines get no base: they are the owner's text,
which upgrade-sanctum.py integrates into the new format, never overwrites.

Exit codes: 0 ok, 1 refused (target exists / source missing / backup failed /
post-write check failed), 2 bad input.
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
    spec = spec_from_file_location("_sanctum_seed", Path(__file__).resolve().parent / "_sanctum_seed.py")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_seed = _load_sanctum_seed()

OLD_REL = _seed.LEGACY_SANCTUM_REL
NEW_REL = _seed.SANCTUM_REL
OLD_PREFIX = "/".join(OLD_REL)
NEW_PREFIX = "/".join(NEW_REL)

COPIED_IDENTITY = ("PERSONA.md", "BOND.md", "CAPABILITIES.md")

SHARD_FILES = {
    "creed-workshop-capture.md": "memory/disciplines/workshop-capture.md",
    "creed-package-assembly.md": "memory/disciplines/package-assembly.md",
}
SPLIT_FILES = {
    "creed-disciplines.md": "memory/disciplines",
    "creed-incident-log.md": "memory/incidents",
}

# References inside the moved text that point at old homes. Applied in order.
REF_REWRITES = [
    (OLD_PREFIX + "/", NEW_PREFIX + "/"),
    (OLD_PREFIX, NEW_PREFIX),
    ("creed-package-assembly.md", "memory/disciplines/package-assembly.md"),
    ("creed-workshop-capture.md", "memory/disciplines/workshop-capture.md"),
    ("creed-disciplines.md", "memory/disciplines/"),
    ("creed-incident-log.md", "memory/incidents/"),
    ("access-boundaries.md", "CREED.md (Dominion)"),
    ("_bmad/config*.yaml", "_bmad/config*.toml"),
    ("`patterns.md`", "`raw/2026-05-17-patterns-superseded.md`"),
    ("`chronology.md`", "`memory/chronology/`"),
]
SESSION_REF = re.compile(r"(?<![\w/])sessions/(\d{4}-\d{2}-\d{2})\.md")
DATED_HEADING = re.compile(r"^(\d{4}-\d{2}-\d{2})\b\s*[—–-]*\s*(.*)$")
EMPTY_PULSE = re.compile(r"^_\(empty\b.*\)_$", re.S)


slugify = _seed._slug
split_sections = _seed.split_sections


def rewrite_refs(text: str, session_map: dict[str, str]) -> str:
    for old, new in REF_REWRITES:
        text = text.replace(old, new)

    def session(match: re.Match) -> str:
        return session_map.get(match.group(1), match.group(0))

    return SESSION_REF.sub(session, text)


def unique(path: str, taken: set[str]) -> str:
    if path not in taken:
        taken.add(path)
        return path
    stem, dot, ext = path.rpartition(".")
    n = 2
    while f"{stem}-{n}.{ext}" in taken:
        n += 1
    taken.add(f"{stem}-{n}.{ext}")
    return f"{stem}-{n}.{ext}"


def _born(text: str) -> str | None:
    match = re.search(r"\*\*Born:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    return match.group(1) if match else None


def frontmatter(fields: dict) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {json.dumps(value) if isinstance(value, list) else value}")
    return "\n".join(lines + ["---", ""])


class Plan:
    def __init__(self, source: Path):
        self.source = source
        self.files: dict[str, str] = {}
        self.entries: list[dict] = []
        self.copies: list[tuple[Path, str]] = []
        self.taken: set[str] = set()
        self.dropped: list[dict] = []

    def add(self, src: str, section: str | None, dest: str, content: str) -> None:
        dest = unique(dest, self.taken)
        self.files[dest] = content.rstrip() + "\n"
        self.entries.append({"from": src, "section": section, "to": dest, "bytes": len(content.encode())})

    def copy(self, src: Path, dest: str) -> None:
        dest = unique(dest, self.taken)
        self.copies.append((src, dest))
        self.entries.append({"from": src.relative_to(self.source).as_posix(), "section": None, "to": dest,
                             "bytes": src.stat().st_size})


def build_plan(source: Path, skill_path: Path, today: str, project_root: Path | None = None) -> Plan:
    plan = Plan(source)
    project_root = project_root or source.parent.parent.parent

    def read(name: str) -> str | None:
        path = source / name
        return path.read_text(encoding="utf-8") if path.is_file() else None

    # raw/: session logs first, so references to them can be rewritten everywhere.
    session_map: dict[str, str] = {}
    sessions = sorted((source / "sessions").glob("*.md")) if (source / "sessions").is_dir() else []
    for log in sessions:
        day = log.stem[:10]
        session_map[day] = f"raw/{day}-session-log.md"
    for log in sessions:
        body = log.read_text(encoding="utf-8")
        head = frontmatter({"status": "distilled", "distilled_to": ["memory/"],
                            "note": "Mac's raw session narrative from the v2 sanctum; curated into MEMORY.md, now memory/."})
        plan.add(f"sessions/{log.name}", None, session_map[log.stem[:10]], head + rewrite_refs(body, session_map))

    # Identity: copied files.
    for name in COPIED_IDENTITY:
        text = read(name)
        if text is not None:
            plan.add(name, None, name, rewrite_refs(text, session_map))

    # CREED: Dominion from access-boundaries.md, shard map to the new homes.
    creed = read("CREED.md")
    if creed is not None:
        boundaries = read("access-boundaries.md")
        preamble, sections = split_sections(creed)
        out = [preamble]
        for heading, body in sections:
            if heading.lower().startswith("dominion") and boundaries is not None:
                lead, parts = split_sections(boundaries)
                lead = "\n".join(l for l in lead.splitlines() if not l.startswith("# ")).strip()
                body = "\n\n".join([lead] * bool(lead) + [f"### {h}\n\n{b}" for h, b in parts])
                plan.entries.append({"from": "access-boundaries.md", "section": None, "to": "CREED.md#dominion",
                                     "bytes": len(boundaries.encode())})
            out.append(f"## {heading}\n\n{body}")
        plan.add("CREED.md", None, "CREED.md", rewrite_refs("\n\n".join(out), session_map))

    # Files written from the templates are filled in the way First Breath fills
    # them, and recorded as the base upgrade-sanctum.py compares against. The
    # copied files get no base: their text is the owner's until an upgrade
    # integrates it.
    variables = _seed.template_variables(project_root, _seed.resolve_config(project_root, source))
    variables["birth_date"] = _born(read("CREED.md") or "") or variables["birth_date"]
    base: dict[str, dict] = {}

    # PULSE.md from the new template (the routine changed), keeping the owner's preferences.
    pulse_template = skill_path / "assets" / "PULSE-template.md"
    old_pulse = read("PULSE.md")
    if pulse_template.is_file():
        shipped_pulse = _seed.substitute_vars(pulse_template.read_text(encoding="utf-8"), variables)
        pulse = shipped_pulse
        if old_pulse is not None:
            kept = dict(split_sections(old_pulse)[1]).get("Owner Preferences")
            if kept:
                head, _, _ = pulse.partition("## Owner Preferences")
                pulse = head + "## Owner Preferences\n\n" + kept + "\n"
                plan.entries.append({"from": "PULSE.md", "section": "Owner Preferences", "to": "PULSE.md",
                                     "bytes": len(kept.encode())})
        plan.add("assets/PULSE-template.md", None, "PULSE.md", pulse)
        base.update(_seed.base_entries("PULSE.md", plan.files["PULSE.md"], today, shipped_pulse))

    # HOW-I-REMEMBER.md from the skill's template.
    template = skill_path / "assets" / "HOW-I-REMEMBER-template.md"
    if template.is_file():
        how = _seed.substitute_vars(template.read_text(encoding="utf-8"), variables)
        plan.add("assets/HOW-I-REMEMBER-template.md", None, "HOW-I-REMEMBER.md", how)
        base.update(_seed.base_entries("HOW-I-REMEMBER.md", plan.files["HOW-I-REMEMBER.md"], today))

    # MEMORY.md -> standing files.
    memory = read("MEMORY.md")
    if memory is not None:
        _, sections = split_sections(memory)
        for heading, body in sections:
            if not body or EMPTY_PULSE.match(body):
                plan.dropped.append({"from": "MEMORY.md", "section": heading, "why": "empty"})
                continue
            dest = _seed.memory_section_file(heading)
            plan.add("MEMORY.md", heading, dest, f"# {heading}\n\n{rewrite_refs(body, session_map)}")

    # Creed shards.
    for name, dest in SHARD_FILES.items():
        text = read(name)
        if text is not None:
            _, sections = split_sections(text)
            body = "\n\n".join(f"## {h}\n\n{b}" for h, b in sections)
            title = sections[0][0] if len(sections) == 1 else name
            if len(sections) == 1:
                body = sections[0][1]
            plan.add(name, None, dest, f"# {title}\n\n{rewrite_refs(body, session_map)}")
    for name, folder in SPLIT_FILES.items():
        text = read(name)
        if text is None:
            continue
        _, sections = split_sections(text)
        for heading, body in sections:
            plan.add(name, heading, f"{folder}/{_seed.discipline_file(heading)}",
                     f"# {heading}\n\n{rewrite_refs(body, session_map)}")

    # Chronology entries.
    chronology = read("chronology.md")
    if chronology is not None:
        preamble, sections = split_sections(chronology)
        for heading, body in sections:
            match = DATED_HEADING.match(heading)
            day, rest = (match.group(1), match.group(2)) if match else ("undated", heading)
            dest = f"memory/chronology/{day}-{slugify(rest or 'session')}.md"
            plan.add("chronology.md", heading, dest, f"# {heading}\n\n{rewrite_refs(body, session_map)}")

    # raw/: superseded patterns and the Collection exports.
    patterns = read("patterns.md")
    if patterns is not None:
        head = frontmatter({"status": "distilled",
                            "distilled_to": ["docs/"],
                            "note": "Superseded 2026-05-17; an audit trail only. The canonical homes are listed in its banner."})
        plan.add("patterns.md", None, "raw/2026-05-17-patterns-superseded.md", head + patterns)
    for export in sorted(source.glob("_collection_*.txt")):
        stamp = datetime.fromtimestamp(export.stat().st_mtime).date().isoformat()
        plan.copy(export, f"raw/{stamp}-collection-of-writings-{export.stem.removeprefix('_collection_')}.txt")

    # Tool config and learned capabilities carry over as they are.
    for name in ("validate-ignore.txt",):
        if (source / name).is_file():
            plan.copy(source / name, name)
    capabilities = source / "capabilities"
    if capabilities.is_dir():
        for path in sorted(p for p in capabilities.rglob("*") if p.is_file()):
            plan.copy(path, "capabilities/" + path.relative_to(capabilities).as_posix())

    # The conversion is itself a tending; the birth date carries over, so the
    # wake reads the converted sanctum as a finished First Breath.
    plan.files[_seed.TEMPLATE_BASE_REL] = json.dumps(
        {"version": 1, "units": dict(sorted(base.items()))}, indent=2, ensure_ascii=False) + "\n"
    plan.files["memory/.tended"] = today + "\n"
    plan.files["memory/.born"] = (_born(read("CREED.md") or "") or _born(read("PERSONA.md") or "") or today) + "\n"

    # Anything the plan did not place is reported, never silently lost.
    handled = {"INDEX.md", "MEMORY.md", "CREED.md", "access-boundaries.md", "chronology.md", "patterns.md",
               "PULSE.md", "validate-ignore.txt", *COPIED_IDENTITY, *SHARD_FILES, *SPLIT_FILES}
    for path in sorted(source.iterdir()):
        name = path.name
        if path.is_dir() and name in ("sessions", "capabilities"):
            continue
        if name in handled or name.startswith("_collection_"):
            continue
        if path.is_file():
            plan.copy(path, f"raw/unplaced-{name}")
        else:
            plan.dropped.append({"from": name, "section": None, "why": "unexpected folder; not copied"})
    if (source / "INDEX.md").is_file():
        plan.dropped.append({"from": "INDEX.md", "section": None,
                             "why": "v7 has no index; the waking map lists the memory"})
    return plan


def write(plan: Plan, target: Path) -> None:
    for rel, content in plan.files.items():
        out = target / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
    for src, rel in plan.copies:
        out = target / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
    for folder in ("raw", "capabilities", *(f"memory/{kind}" for kind in _seed.MEMORY_KINDS)):
        (target / folder).mkdir(parents=True, exist_ok=True)


def _discard(archive: Path) -> None:
    try:
        archive.unlink(missing_ok=True)
    except OSError:
        pass


def backup(source: Path, target: Path, backup_dir: Path, stamp: str) -> tuple[Path | None, str | None]:
    """Tar the source store (and a non-empty target) and verify the listing.

    Returns (archive, None) on success, (None, reason) on failure; a failed
    archive is removed so it never passes for a good one.
    """
    roots = [source] + ([target] if target.is_dir() and any(target.iterdir()) else [])
    expected = {f"{root.name}/{p.relative_to(root).as_posix()}"
                for root in roots for p in root.rglob("*") if p.is_file()}
    archive = backup_dir / f"mac-sanctum-v2-{stamp}.tar.gz"
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, "w:gz") as tar:
            for root in roots:
                tar.add(root, arcname=root.name)
        with tarfile.open(archive, "r:gz") as tar:
            listed = {m.name for m in tar.getmembers() if m.isfile()}
    except (OSError, tarfile.TarError) as exc:
        _discard(archive)
        return None, f"backup failed: {exc}"
    missing = sorted(expected - listed)
    if missing or not expected:
        _discard(archive)
        what = ", ".join(missing[:5]) + (" ..." if len(missing) > 5 else "") if missing else "no files"
        return None, f"backup archive does not list the source ({what})"
    return archive, None


def verify(plan: Plan, target: Path) -> list[str]:
    """Planned files that are missing, empty when they should not be, or differ."""
    bad = []
    for rel, content in plan.files.items():
        out = target / rel
        try:
            ok = out.is_file() and out.stat().st_size > 0 and out.read_text(encoding="utf-8") == content
        except (OSError, UnicodeDecodeError):
            ok = False
        if not ok:
            bad.append(rel)
    for src, rel in plan.copies:
        out = target / rel
        if not out.is_file() or out.stat().st_size != src.stat().st_size:
            bad.append(rel)
    return sorted(bad)


def refused(reason: str, **extra) -> int:
    print(json.dumps({"status": "refused", "reason": reason, **extra}, indent=2))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project_root")
    parser.add_argument("--from", dest="source", help="v2 sanctum (default: the project's)")
    parser.add_argument("--to", dest="target", help="v7 sanctum (default: the project's)")
    parser.add_argument("--skill-path", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--dry-run", action="store_true", help="print the plan; write nothing")
    parser.add_argument("--force", action="store_true", help="write into an existing target")
    parser.add_argument("--today", default=date.today().isoformat())
    parser.add_argument("--backup-dir", help="where the tarball goes (default: <project-root>/_bmad/backups)")
    parser.add_argument("--no-backup", action="store_true", help="skip the backup tarball (tests only)")
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.today):
        print(json.dumps({"status": "error", "reason": f"--today must be YYYY-MM-DD, got {args.today!r}"}))
        return 2

    root = Path(args.project_root).resolve()
    source = Path(args.source).resolve() if args.source else root.joinpath(*OLD_REL)
    target = Path(args.target).resolve() if args.target else root.joinpath(*NEW_REL)
    if not source.is_dir():
        return refused(f"no v2 sanctum at {source}")
    if target.exists() and any(target.iterdir()) and not args.force and not args.dry_run:
        return refused(f"{target} exists and is not empty; pass --force")

    plan = build_plan(source, Path(args.skill_path), args.today, root)
    backup_path = None
    if not args.dry_run:
        if not args.no_backup:
            backup_dir = Path(args.backup_dir).resolve() if args.backup_dir else root / "_bmad" / "backups"
            archive, reason = backup(source, target, backup_dir, datetime.now().strftime("%Y%m%d-%H%M%S"))
            if reason:
                return refused(f"{reason}; nothing was written", backup_path=None)
            backup_path = str(archive)
        try:
            write(plan, target)
        except OSError as exc:
            return refused(f"writing the new sanctum failed: {exc}; the source is untouched",
                           target_written="partial", backup_path=backup_path)
        bad = verify(plan, target)
        if bad:
            return refused(
                f"post-write check failed: {len(bad)} planned file(s) missing, empty or different; "
                "the source is untouched", target_written="partial", unverified=bad, backup_path=backup_path)
    source_bytes = sum(p.stat().st_size for p in source.rglob("*") if p.is_file())
    print(json.dumps({
        "status": "planned" if args.dry_run else "written",
        "source": str(source),
        "target": str(target),
        "backup_path": backup_path,
        "source_bytes": source_bytes,
        "files": len(plan.files) + len(plan.copies),
        "entries": plan.entries,
        "dropped": plan.dropped,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
