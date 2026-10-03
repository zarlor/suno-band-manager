#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Bring an existing v2 sanctum up to date with the shipped templates.

Template and creed fixes never reach an existing sanctum on their own: init
scaffolds only a fresh sanctum, and migration only handles v1 stores. This
script compares the live sanctum with what the current templates (and the
sharded `references/creed.md`) would produce, section by section, and proposes
changes. It never overwrites owner content on its own.

Change kinds:
  create-file     a spine file or shard is missing            (safe)
  add-section     a template `## ` section the file lacks     (safe)
  add-rows        INDEX.md table rows the live table lacks    (safe)
  replace-section a section differs from the template         (needs its id)

Sections the owner grows are never proposed: CREED Mission, PERSONA Evolution
Log, BOND Boundaries / Notes, PULSE Owner Preferences / State, CAPABILITIES
Learned, and every existing MEMORY.md section (MEMORY only gains new sections;
its header banner can be replaced on request).
The creed incident log is only ever created, never replaced.

Default is a dry run that prints every proposed change with a diff. Apply with
`--apply safe` (creates and additions only) and/or `--apply ID,ID` (named
changes, including replacements). Every file touched is backed up first to a
sibling `.sanctum-upgrade-backup-<stamp>/` directory.

Usage:
    uv run scripts/upgrade-sanctum.py --project-root PATH [--sanctum-dir DIR]
                                      [--apply safe|ID[,ID...]] [--format text|json]
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import sys
import warnings
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_sanctum_seed():
    seed_path = Path(__file__).resolve().parent / "_sanctum_seed.py"
    spec = spec_from_file_location("_sanctum_seed", seed_path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_seed = _load_sanctum_seed()

SECTION_SPLIT_RE = re.compile(r"(?m)^(?=##\s)")
BORN_RE = re.compile(r"\*\*Born:\*\*\s*(\d{4}-\d{2}-\d{2})")
PREAMBLE = "(preamble)"

TEMPLATES = {
    "CREED.md": "CREED-template.md",
    "PERSONA.md": "PERSONA-template.md",
    "BOND.md": "BOND-template.md",
    "PULSE.md": "PULSE-template.md",
    "INDEX.md": "INDEX-template.md",
    "MEMORY.md": "MEMORY-template.md",
    "access-boundaries.md": "ACCESS-BOUNDARIES-template.md",
}
PROTECTED = {
    "CREED.md": {"## Mission"},
    "PERSONA.md": {"## Evolution Log"},
    "BOND.md": {"## Boundaries Observed", "## Notes Toward the Bond"},
    "PULSE.md": {"## Owner Preferences", "## State"},
    "CAPABILITIES.md": {"## Learned"},
}
# Headings the templates renamed: live old heading -> template heading. The
# section is matched under its new name and the heading line is renamed (safe).
RENAMES = {
    "INDEX.md": {
        "## Loaded on Rebirth (always)": "## Loaded on Waking (always)",
        "## Not Loaded on Rebirth (raw layers / references)": "## Not Loaded on Waking (raw layers / references)",
    },
}
ADDITIVE = {"MEMORY.md"}      # only gains new sections (its banner may be replaced)
TABLE_MERGE = {"INDEX.md"}    # gains sections and table rows, never loses rows
CREATE_ONLY = {"creed-incident-log.md"}


# ---------------------------------------------------------------------------
# Section model
# ---------------------------------------------------------------------------


def split(text: str) -> list[tuple[str, str]]:
    """[(heading, text)] with the text before the first `## ` as the preamble."""
    parts = SECTION_SPLIT_RE.split(text)
    out: list[tuple[str, str]] = []
    for i, part in enumerate(parts):
        if not part:
            continue
        if i == 0 and not part.startswith("## "):
            out.append((PREAMBLE, part))
        else:
            out.append((part.splitlines()[0].strip(), part))
    return out


def join(sections: list[tuple[str, str]]) -> str:
    chunks = []
    for _, body in sections:
        chunks.append(body if body.endswith("\n") else body + "\n")
    return "".join(chunks)


def norm(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def table_rows(text: str) -> list[str]:
    return [
        line for line in text.splitlines()
        if line.startswith("|") and not re.match(r"^\|[\s\-|:]+\|\s*$", line)
    ]


def row_key(row: str) -> str:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return cells[0] if cells else row


def diff_text(old: str, new: str, label: str) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"live/{label}",
            tofile=f"template/{label}",
        )
    )


# ---------------------------------------------------------------------------
# Expected content
# ---------------------------------------------------------------------------


def live_birth_date(sanctum: Path) -> str | None:
    for name in ("CREED.md", "INDEX.md", "PERSONA.md", "MEMORY.md"):
        path = sanctum / name
        if path.is_file():
            match = BORN_RE.search(path.read_text(encoding="utf-8"))
            if match:
                return match.group(1)
    return None


def expected_files(project_root: Path, sanctum: Path, skill_path: Path) -> tuple[dict, list[str]]:
    """{filename: expected text} from the templates, the CSV roster and the creed."""
    variables = _seed.template_variables(project_root, birth_date=live_birth_date(sanctum))
    assets = skill_path / "assets"
    expected: dict[str, str] = {}
    notes: list[str] = []
    for out_name, template in TEMPLATES.items():
        path = assets / template
        if path.is_file():
            expected[out_name] = _seed.substitute_vars(path.read_text(encoding="utf-8"), variables)
    csv_path = _seed.find_module_csv(project_root, skill_path)
    if csv_path:
        expected["CAPABILITIES.md"] = _seed.generate_capabilities_md(
            _seed.menu_rows(csv_path, [_seed.MODULE_CODE])
        )
    else:
        notes.append("module-help.csv not found; CAPABILITIES.md left as is.")
    creed = skill_path / "references" / "creed.md"
    if creed.is_file():
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            expected.update(_seed.shard_creed(creed.read_text(encoding="utf-8")))
        notes.extend(sorted({str(w.message) for w in caught}))
    return expected, notes


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


def plan_file(name: str, live_text: str, new_text: str) -> tuple[list[dict], list[str]]:
    """Proposed changes for one existing file, plus the owner sections kept."""
    changes: list[dict] = []
    kept: list[str] = []
    renames = RENAMES.get(name, {})
    tmpl = split(new_text)
    template_headings = {h for h, _ in tmpl}
    live = []
    for heading, body in split(live_text):
        new_heading = renames.get(heading)
        if new_heading and new_heading in template_headings:
            changes.append(
                {
                    "file": name,
                    "kind": "rename-heading",
                    "heading": heading,
                    "to": new_heading,
                    "safe": True,
                    "diff": f"-{heading}\n+{new_heading}\n",
                }
            )
            body = body.replace(heading, new_heading, 1)
            heading = new_heading
        live.append((heading, body))
    live_by = {h: body for h, body in live}
    protected = PROTECTED.get(name, set())

    for idx, (heading, body) in enumerate(tmpl):
        if heading not in live_by:
            if heading == PREAMBLE:
                continue
            # Insert after the nearest earlier template heading the live file has.
            after = None
            for prev_heading, _ in reversed(tmpl[:idx]):
                if prev_heading in live_by:
                    after = prev_heading
                    break
            changes.append(
                {
                    "file": name,
                    "kind": "add-section",
                    "heading": heading,
                    "safe": True,
                    "after": after,
                    "new": body,
                    "diff": diff_text("", body, name),
                }
            )
            continue
        live_body = live_by[heading]
        if norm(live_body) == norm(body):
            continue
        if heading in protected or (name in ADDITIVE and heading != PREAMBLE):
            kept.append(f"{name} {heading}")
            continue
        if name in TABLE_MERGE:
            have = {row_key(r) for r in table_rows(live_body)}
            missing = [r for r in table_rows(body) if row_key(r) not in have]
            if missing:
                changes.append(
                    {
                        "file": name,
                        "kind": "add-rows",
                        "heading": heading,
                        "safe": True,
                        "rows": missing,
                        "diff": "".join(f"+{r}\n" for r in missing),
                    }
                )
            continue
        removed = [l for l in norm(live_body).splitlines() if l.strip() and l not in norm(body).splitlines()]
        changes.append(
            {
                "file": name,
                "kind": "replace-section",
                "heading": heading,
                "safe": False,
                "removes_lines": len(removed),
                "new": body,
                "diff": diff_text(live_body, body, f"{name} {heading}"),
            }
        )
    for heading, _ in live:
        if heading not in template_headings and heading != PREAMBLE:
            kept.append(f"{name} {heading}")
    return changes, kept


def plan(project_root: Path, sanctum: Path, skill_path: Path) -> dict:
    state = _seed.classify_sanctum(sanctum)
    if state["sidecar_format"] in ("absent", "v1"):
        return {
            "status": "not-applicable",
            "sanctum_path": str(sanctum),
            "sidecar_format": state["sidecar_format"],
            "message": (
                "No sanctum to upgrade — First Breath scaffolds one."
                if state["sidecar_format"] == "absent"
                else "This is a v1 store — migrate it with migrate-sidecar-to-v2.py --in-place."
            ),
            "changes": [],
        }
    expected, notes = expected_files(project_root, sanctum, skill_path)
    changes: list[dict] = []
    kept: list[str] = []
    for name, new_text in expected.items():
        path = sanctum / name
        if not path.is_file():
            changes.append(
                {
                    "file": name,
                    "kind": "create-file",
                    "heading": None,
                    "safe": True,
                    "new": new_text,
                    "diff": diff_text("", new_text, name),
                }
            )
            continue
        if name in CREATE_ONLY:
            continue
        file_changes, file_kept = plan_file(name, path.read_text(encoding="utf-8"), new_text)
        changes.extend(file_changes)
        kept.extend(file_kept)
    counters: dict[str, int] = {}
    for change in changes:
        counters[change["file"]] = counters.get(change["file"], 0) + 1
        change["id"] = f"{change['file']}#{counters[change['file']]}"
    return {
        "status": "dry-run",
        "sanctum_path": str(sanctum),
        "sidecar_format": state["sidecar_format"],
        "missing_spine": state["missing_spine"],
        "changes": changes,
        "owner_sections_kept": kept,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_changes(sanctum: Path, report: dict, selection: set[str]) -> dict:
    """Apply the selected changes ('safe' and/or ids). Back up each file first."""
    chosen = [
        c for c in report["changes"]
        if c["id"] in selection or ("safe" in selection and c["safe"])
    ]
    unknown = sorted(s for s in selection if s != "safe" and s not in {c["id"] for c in report["changes"]})
    if not chosen:
        return {**report, "status": "nothing-applied", "applied": [], "unknown_ids": unknown}

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = sanctum.parent / f".sanctum-upgrade-backup-{stamp}"
    by_file: dict[str, list[dict]] = {}
    for change in chosen:
        by_file.setdefault(change["file"], []).append(change)

    for name, file_changes in by_file.items():
        path = sanctum / name
        if path.exists():
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup / name)
        create = [c for c in file_changes if c["kind"] == "create-file"]
        if create:
            path.write_text(create[0]["new"], encoding="utf-8")
            continue
        sections = split(path.read_text(encoding="utf-8"))
        renamed = {}
        for change in file_changes:
            if change["kind"] == "rename-heading":
                renamed[change["heading"]] = change["to"]
        rebuilt = []
        for heading, body in sections:
            target = renamed.get(heading)
            if target:
                body = body.replace(heading, target, 1)
                heading = target
            rebuilt.append((heading, body))
        sections = rebuilt
        # Changes are planned under the new heading names; when a rename was not
        # selected, address the section by its old name.
        aliases = {new: old for old, new in RENAMES.get(name, {}).items()}
        for change in file_changes:
            headings = [h for h, _ in sections]
            if change["kind"] == "rename-heading":
                continue
            if change.get("heading") not in headings and aliases.get(change.get("heading")) in headings:
                change = {**change, "heading": aliases[change["heading"]]}
            if change["kind"] == "replace-section":
                i = headings.index(change["heading"])
                sections[i] = (change["heading"], change["new"])
            elif change["kind"] == "add-rows":
                i = headings.index(change["heading"])
                body = sections[i][1]
                rows = table_rows(body)
                last = body.rfind(rows[-1]) + len(rows[-1]) if rows else len(body.rstrip("\n"))
                body = body[:last] + "\n" + "\n".join(change["rows"]) + body[last:]
                sections[i] = (change["heading"], body)
            elif change["kind"] == "add-section":
                after = change["after"]
                if after not in headings and aliases.get(after) in headings:
                    after = aliases[after]
                if after in headings:
                    i = headings.index(after) + 1
                else:
                    i = len(sections)
                new_body = change["new"].rstrip("\n") + ("\n\n" if i < len(sections) else "\n")
                if i > 0 and not sections[i - 1][1].endswith("\n\n"):
                    prev_h, prev_b = sections[i - 1]
                    sections[i - 1] = (prev_h, prev_b.rstrip("\n") + "\n\n")
                sections.insert(i, (change["heading"], new_body))
        path.write_text(join(sections), encoding="utf-8")

    return {
        **report,
        "status": "applied",
        "applied": [c["id"] for c in chosen],
        "backup_path": str(backup) if backup.exists() else None,
        "unknown_ids": unknown,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def render_text(report: dict) -> str:
    out = [f"Sanctum: {report['sanctum_path']}  ({report.get('sidecar_format')})"]
    if report["status"] == "not-applicable":
        out.append(report["message"])
        return "\n".join(out) + "\n"
    changes = report["changes"]
    out.append(f"Status: {report['status']} — {len(changes)} proposed change(s)")
    for c in changes:
        flag = "safe" if c["safe"] else f"review (removes {c.get('removes_lines', 0)} line(s))"
        where = f" {c['heading']}" if c.get("heading") else ""
        out.append(f"  [{c['id']}] {c['kind']}{where} — {flag}")
    if report.get("owner_sections_kept"):
        out.append("Owner sections kept as they are:")
        out += [f"  = {k}" for k in report["owner_sections_kept"]]
    for note in report.get("notes", []):
        out.append(f"  ! {note}")
    if report["status"] == "applied":
        out.append(f"Applied: {', '.join(report['applied'])}")
        out.append(f"Backup: {report.get('backup_path')}")
    if report.get("unknown_ids"):
        out.append(f"Unknown ids (ignored): {', '.join(report['unknown_ids'])}")
    if report["status"] == "dry-run":
        for c in changes:
            out += ["", f"----- {c['id']} {c['kind']} -----", c["diff"].rstrip()]
        out += [
            "",
            "Nothing was written. Apply with --apply safe (creates/additions) and/or "
            "--apply <id>,<id> after the owner confirms each replacement.",
        ]
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run diff and confirmed upgrade of an existing v2 sanctum.")
    parser.add_argument("--project-root", default=".", help="Project root (where _bmad/ lives).")
    parser.add_argument("--sanctum-dir", default=None, help="Override the sanctum directory.")
    parser.add_argument("--skill-path", default=None, help="Skill dir (assets/, references/). Default: inferred.")
    parser.add_argument(
        "--apply",
        default=None,
        help="'safe' and/or comma-separated change ids. Omit for a dry run.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    sanctum = _seed.sanctum_dir(project_root, args.sanctum_dir).resolve()
    skill_path = Path(args.skill_path).resolve() if args.skill_path else Path(__file__).resolve().parent.parent

    report = plan(project_root, sanctum, skill_path)
    if args.apply and report["status"] == "dry-run":
        selection = {s.strip() for s in args.apply.split(",") if s.strip()}
        report = apply_changes(sanctum, report, selection)

    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")
    if args.format == "json":
        slim = {**report, "changes": [{k: v for k, v in c.items() if k != "new"} for c in report["changes"]]}
        print(json.dumps(slim, indent=2, ensure_ascii=False))
    else:
        sys.stdout.write(render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
