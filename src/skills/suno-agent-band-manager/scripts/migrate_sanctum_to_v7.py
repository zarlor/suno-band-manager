#!/usr/bin/env -S uv run --script
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
waking map now does, each split file's own banner (its `# ` title and the
blockquote under it), and what `dropped` names. Text the layout has no home
for is kept under `raw/unplaced-*`: unknown files, non-markdown or nested files
in sessions/, owner text above a file's first `## ` heading, and the access
boundaries when the old CREED.md has no Dominion section to take them.

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
    uv run {skill-root}/scripts/migrate_sanctum_to_v7.py <project-root>
        [--from DIR] [--to DIR] [--skill-path DIR] [--dry-run] [--force]
        [--today YYYY-MM-DD] [--backup-dir DIR | --no-backup]

Default output is the plan as JSON. `--dry-run` writes nothing; without it the
new sanctum is written (refused when the target exists, unless --force).
The source must be a complete v2 store and the skill must hold the
HOW-I-REMEMBER and PULSE templates; anything else is refused before a plan is
made, as is a source file that is not readable UTF-8 text.

The new sanctum is built in a hidden sibling folder
(`.suno-agent-band-manager.converting`), checked there, and only then moved
into place in one step. A run that is killed part-way therefore leaves the
target as it was (absent, or the sanctum --force was about to overlay); the
next run clears the leftover folder and starts again.

Before writing, the script tars the source store (and an existing target, when
--force overwrites one) into `{project-root}/_bmad/backups/` (or --backup-dir)
and checks the archive lists every file; no verified backup, no conversion.
`--no-backup` skips it (tests). After writing, every planned file is checked to
exist with the planned content (copies: the source's size). The JSON carries
`backup_path`; any failure is `status: "refused"` with a `reason`. A refusal
after the backup also carries `target_written`: `"none"` when the target is as
it was before the run (the usual case), `"moved-aside"` with `moved_to` when
the final move failed and the sanctum --force was overlaying could not be put
back. A failed post-write check lists the files in `unverified`.

The converted sanctum gets `memory/.tended` (the conversion is a tending),
`memory/.born` (the birth date from the old CREED.md or PERSONA.md
`**Born:**` line, else --today), so the wake reads it as a finished birth, and
`memory/.template-base.json`, which records the template text it was given
(HOW-I-REMEMBER.md, PULSE.md apart from the owner's preferences). The carried
over identity files and disciplines get no base: they are the owner's text,
which upgrade_sanctum.py integrates into the new format, never overwrites.

Exit codes: 0 ok, 1 refused (target exists / source missing, not v2 or
unreadable / templates missing / backup failed / write or post-write check
failed), 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import os
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

# Templates the converted sanctum is written from; without them it would lack
# an identity file, so the conversion is refused.
REQUIRED_TEMPLATES = ("HOW-I-REMEMBER-template.md", "PULSE-template.md")


class Unreadable(Exception):
    """A source file that can't be read as UTF-8 text."""


def read_source(path: Path, source: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Unreadable(f"{path.relative_to(source).as_posix()}: {exc}") from exc


def has_owner_text(preamble: str) -> bool:
    """True when text above a file's first `## ` is more than its banner
    (the `# ` title and blockquote lines the old layout put there)."""
    return any(
        line.strip() and not line.startswith("# ") and not line.lstrip().startswith(">")
        for line in preamble.splitlines()
    )


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
        return read_source(path, source) if path.is_file() else None

    def keep_preamble(name: str, preamble: str) -> None:
        """Owner text above a file's first `## ` has no section to travel with: keep it in raw/."""
        if has_owner_text(preamble):
            head = frontmatter({"status": "raw",
                                "note": f"Text above the first heading of the old {name}; it had no section to travel with."})
            plan.add(name, "(preamble)", f"raw/unplaced-{Path(name).stem}-preamble.md", head + preamble)

    # raw/: session logs first, so references to them can be rewritten everywhere.
    session_map: dict[str, str] = {}
    sessions_dir = source / "sessions"
    sessions = sorted(p for p in sessions_dir.glob("*.md") if p.is_file()) if sessions_dir.is_dir() else []
    for log in sessions:
        day = log.stem[:10]
        session_map[day] = f"raw/{day}-session-log.md"
    for log in sessions:
        body = read_source(log, source)
        head = frontmatter({"status": "distilled", "distilled_to": ["memory/"],
                            "note": "Mac's raw session narrative from the v2 sanctum; curated into MEMORY.md, now memory/."})
        plan.add(f"sessions/{log.name}", None, session_map[log.stem[:10]], head + rewrite_refs(body, session_map))
    # Anything else in sessions/ (other file types, subfolders) is kept as it is.
    if sessions_dir.is_dir():
        for path in sorted(p for p in sessions_dir.rglob("*") if p.is_file() and p not in sessions):
            plan.copy(path, "raw/unplaced-sessions-" + path.relative_to(sessions_dir).as_posix().replace("/", "-"))

    # Identity: copied files.
    for name in COPIED_IDENTITY:
        text = read(name)
        if text is not None:
            plan.add(name, None, name, rewrite_refs(text, session_map))

    # CREED: Dominion from access-boundaries.md, shard map to the new homes.
    creed = read("CREED.md")
    boundaries = read("access-boundaries.md")
    placed = False
    if creed is not None:
        preamble, sections = split_sections(creed)
        out = [preamble]
        for heading, body in sections:
            if heading.lower().startswith("dominion") and boundaries is not None and not placed:
                lead, parts = split_sections(boundaries)
                lead = "\n".join(l for l in lead.splitlines() if not l.startswith("# ")).strip()
                body = "\n\n".join([lead] * bool(lead) + [f"### {h}\n\n{b}" for h, b in parts])
                plan.entries.append({"from": "access-boundaries.md", "section": None, "to": "CREED.md#dominion",
                                     "bytes": len(boundaries.encode())})
                placed = True
            out.append(f"## {heading}\n\n{body}")
        plan.add("CREED.md", None, "CREED.md", rewrite_refs("\n\n".join(out), session_map))
    if boundaries is not None and not placed:
        # No Dominion section to take them: the owner's boundaries are kept, never dropped.
        head = frontmatter({"status": "raw",
                            "note": "The old CREED.md had no Dominion section to take these access boundaries; "
                                    "fold them into CREED.md's Dominion."})
        plan.add("access-boundaries.md", None, "raw/unplaced-access-boundaries.md", head + boundaries)

    # Files written from the templates are filled in the way First Breath fills
    # them, and recorded as the base upgrade_sanctum.py compares against. The
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
        preamble, sections = split_sections(memory)
        keep_preamble("MEMORY.md", preamble)
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
            preamble, sections = split_sections(text)
            keep_preamble(name, preamble)
            body = "\n\n".join(f"## {h}\n\n{b}" for h, b in sections)
            title = sections[0][0] if len(sections) == 1 else name
            if len(sections) == 1:
                body = sections[0][1]
            plan.add(name, None, dest, f"# {title}\n\n{rewrite_refs(body, session_map)}")
    for name, folder in SPLIT_FILES.items():
        text = read(name)
        if text is None:
            continue
        preamble, sections = split_sections(text)
        keep_preamble(name, preamble)
        for heading, body in sections:
            plan.add(name, heading, f"{folder}/{_seed.discipline_file(heading)}",
                     f"# {heading}\n\n{rewrite_refs(body, session_map)}")

    # Chronology entries.
    chronology = read("chronology.md")
    if chronology is not None:
        preamble, sections = split_sections(chronology)
        keep_preamble("chronology.md", preamble)
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


def staging_dir(target: Path) -> Path:
    """The hidden sibling the new sanctum is built in before it is moved into place."""
    return target.with_name(f".{target.name}.converting")


def promote(staging: Path, target: Path) -> None:
    """Move the checked staging folder into place in one step.

    A non-empty target (--force) was copied into the staging folder before the
    plan was written over it, so it is moved aside, replaced, and the aside
    copy removed. When the replace fails the aside copy is moved back; if that
    fails too, OSError carries `moved_to`, the place the old target now is.
    """
    aside = None
    if target.is_dir():
        if any(target.iterdir()):
            aside = target.with_name(f".{target.name}.replaced")
            if aside.exists():
                shutil.rmtree(aside)
            os.replace(target, aside)
        else:
            target.rmdir()
    try:
        os.replace(staging, target)
    except OSError as exc:
        if aside is not None:
            try:
                os.replace(aside, target)
            except OSError:
                exc.moved_to = str(aside)
        raise
    if aside is not None:
        shutil.rmtree(aside, ignore_errors=True)


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
    skill_path = Path(args.skill_path)
    state = _seed.classify_sanctum(source)
    fmt = state["sidecar_format"]
    if fmt == "absent":
        return refused(f"no v2 sanctum at {source}")
    if fmt != "v2":
        names = set(os.listdir(source)) if source.is_dir() else set()
        why = {
            "v1": "it is a v1 store: run migrate_sidecar_to_v2.py --in-place first",
            "v7": "it is already a v7 sanctum",
        }.get(fmt) or ("it is missing " + ", ".join(n for n in _seed.V2_SPINE if n not in names)
                       + ": restore those files from a backup first")
        return refused(f"{source} is not a complete v2 store ({why}); nothing was converted", sidecar_format=fmt)
    lacking = [f"assets/{name}" for name in REQUIRED_TEMPLATES if not (skill_path / "assets" / name).is_file()]
    if lacking:
        return refused(f"the skill at {skill_path} lacks {', '.join(lacking)}; the converted sanctum would be "
                       "missing identity files. Reinstall the skill or pass --skill-path")
    if target.exists() and not target.is_dir():
        return refused(f"{target} exists and is not a directory")
    if target.is_dir() and any(target.iterdir()) and not args.force and not args.dry_run:
        return refused(f"{target} exists and is not empty; pass --force")

    try:
        plan = build_plan(source, skill_path, args.today, root)
    except (Unreadable, OSError, UnicodeDecodeError) as exc:
        return refused(f"cannot read the old store or the templates: {exc}; nothing was written")
    backup_path = None
    if not args.dry_run:
        if not args.no_backup:
            backup_dir = Path(args.backup_dir).resolve() if args.backup_dir else root / "_bmad" / "backups"
            archive, reason = backup(source, target, backup_dir, datetime.now().strftime("%Y%m%d-%H%M%S"))
            if reason:
                return refused(f"{reason}; nothing was written", backup_path=None)
            backup_path = str(archive)
        # Build beside the target and move into place only once it checks out,
        # so a run that dies part-way never leaves a half-written sanctum there.
        staging = staging_dir(target)
        try:
            if staging.exists():
                shutil.rmtree(staging)  # left by a run that was killed
            staging.parent.mkdir(parents=True, exist_ok=True)
            if target.is_dir() and any(target.iterdir()):
                shutil.copytree(target, staging)  # --force: the plan overlays what is there
            write(plan, staging)
        except OSError as exc:
            shutil.rmtree(staging, ignore_errors=True)
            return refused(f"writing the new sanctum failed: {exc}; the source and the target are untouched",
                           target_written="none", backup_path=backup_path)
        bad = verify(plan, staging)
        if bad:
            shutil.rmtree(staging, ignore_errors=True)
            return refused(
                f"post-write check failed: {len(bad)} planned file(s) missing, empty or different; "
                "the source and the target are untouched", target_written="none", unverified=bad,
                backup_path=backup_path)
        try:
            promote(staging, target)
        except OSError as exc:
            shutil.rmtree(staging, ignore_errors=True)
            moved_to = getattr(exc, "moved_to", None)
            if moved_to:
                return refused(f"moving the new sanctum into place failed: {exc}; the previous sanctum is at "
                               f"{moved_to}", target_written="moved-aside", moved_to=moved_to, backup_path=backup_path)
            return refused(f"moving the new sanctum into place failed: {exc}; the source and the target are "
                           "untouched", target_written="none", backup_path=backup_path)
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
