#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Repair and upgrade an existing v7 sanctum from the shipped templates.

The sanctum is `{project-root}/_bmad/memory/suno-agent-band-manager/`. Template
and creed fixes never reach an existing sanctum on their own: First Breath
(init-sanctum.py) scaffolds only a fresh one. This script compares the live
sanctum with what the current skill would produce and proposes changes. It
never overwrites owner content on its own.

What it checks:
  - the identity files (PERSONA, CREED, BOND, HOW-I-REMEMBER, CAPABILITIES)
    and PULSE.md: missing ones are created from the templates (CREED with the
    Dominion rendered from the access-boundaries template, as First Breath
    does); existing ones are compared section by section
  - the folders: memory/<kind>/, raw/, capabilities/
  - the disciplines (memory/disciplines/) and incident stories
    (memory/incidents/) sliced from `references/creed.md`
  - CAPABILITIES.md's Built-in section, regenerated from assets/menu.csv

Change kinds:
  create-folder       a memory/<kind>/, raw/ or capabilities/ folder is missing (safe)
  create-file         an identity file, discipline or incident file is missing (safe)
  add-section         a template `## ` section the file lacks                   (safe)
  regenerate-section  CAPABILITIES.md Built-in differs from assets/menu.csv     (safe)
  replace-section     a section differs from the template                       (needs its id)
  replace-file        a discipline differs from the shipped creed               (needs its id)

Sections the owner grows are never proposed: CREED Mission, PERSONA Evolution
Log, BOND Owner Summary / Boundaries / Notes, PULSE Owner Preferences,
CAPABILITIES Learned, and any section the template does not have. Incident
stories are only ever created, never replaced. Standing memory files and raw/
are the owner's and Mac's own; they are never proposed.

Default is a dry run that prints every proposed change with a diff. Apply with
`--apply safe` (creates, additions, the generated roster) and/or `--apply ID,ID`
(named changes, including replacements the owner confirmed). Every file
touched is backed up first to a sibling `.suno-agent-band-manager-upgrade-backup-<stamp>/`.

A v1 or v2 store (the legacy `_bmad/_memory/band-manager-sidecar/`) is not
upgraded here: it converts with migrate-sanctum-to-v7.py.

Exit codes: 0 for a dry run, or when `--apply` applied every change it named;
1 when `--apply` applied nothing (a v1/v2 store or no sanctum included) or
named an id the plan does not have (the JSON says which, in `status` and
`unknown_ids`). `--apply safe` on a sanctum with no safe
change pending is `nothing-to-apply`, exit 0.

Usage:
    uv run {skill-root}/scripts/upgrade-sanctum.py --project-root PATH [--sanctum-dir DIR]
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

# Identity files (and PULSE.md) built from a template.
TEMPLATES = {
    "PERSONA.md": "PERSONA-template.md",
    "CREED.md": "CREED-template.md",
    "BOND.md": "BOND-template.md",
    "HOW-I-REMEMBER.md": "HOW-I-REMEMBER-template.md",
    "PULSE.md": "PULSE-template.md",
}
PROTECTED = {
    "CREED.md": {"## Mission"},
    "PERSONA.md": {"## Evolution Log"},
    "BOND.md": {"## Owner Summary", "## Boundaries Observed", "## Notes Toward the Bond"},
    "PULSE.md": {"## Owner Preferences"},
    "CAPABILITIES.md": {"## Learned"},
}
# Sections generated from the skill, never owner content: refreshing them is safe.
GENERATED = {"CAPABILITIES.md": {"## Built-in"}}
FOLDERS = ["raw", "capabilities", *(f"memory/{kind}" for kind in _seed.MEMORY_KINDS)]
DISCIPLINES_DIR = "memory/disciplines/"
INCIDENTS_DIR = "memory/incidents/"  # stories: only ever created
OLD_STORE_MARKERS = ("INDEX.md", "MEMORY.md", "access-boundaries.md")


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
    return "".join(body if body.endswith("\n") else body + "\n" for _, body in sections)


def norm(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


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
    for name in ("CREED.md", "PERSONA.md", "PULSE.md"):
        path = sanctum / name
        if path.is_file():
            match = BORN_RE.search(path.read_text(encoding="utf-8"))
            if match:
                return match.group(1)
    return None


def expected_identity(project_root: Path, sanctum: Path, skill_path: Path) -> tuple[dict, list[str]]:
    """{filename: expected text} for the identity files, as First Breath writes them."""
    config = _seed.resolve_config(project_root, sanctum)
    variables = _seed.template_variables(project_root, config, birth_date=live_birth_date(sanctum))
    assets = skill_path / "assets"
    variables["dominion"] = _seed.render_dominion(assets, variables)
    expected: dict[str, str] = {}
    notes: list[str] = []
    for out_name, template in TEMPLATES.items():
        path = assets / template
        if path.is_file():
            expected[out_name] = _seed.substitute_vars(path.read_text(encoding="utf-8"), variables)
        else:
            notes.append(f"assets/{template} not found; {out_name} not checked.")
    csv_path = _seed.find_menu_csv(skill_path)
    if csv_path:
        expected["CAPABILITIES.md"] = _seed.generate_capabilities_md(_seed.menu_rows(csv_path, [_seed.MODULE_CODE]))
    else:
        notes.append("assets/menu.csv not found; CAPABILITIES.md left as is.")
    return expected, notes


def expected_disciplines(skill_path: Path) -> tuple[dict, list[str]]:
    """{sanctum-relative path: text} for memory/disciplines/ and memory/incidents/."""
    creed = skill_path / "references" / "creed.md"
    if not creed.is_file():
        return {}, ["references/creed.md not found; disciplines not checked."]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        files = _seed.discipline_files(creed.read_text(encoding="utf-8"))
    return files, sorted({str(w.message) for w in caught})


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


def plan_file(name: str, live_text: str, new_text: str) -> tuple[list[dict], list[str]]:
    """Proposed changes for one existing identity file, plus the owner sections kept."""
    changes: list[dict] = []
    kept: list[str] = []
    tmpl = split(new_text)
    template_headings = {h for h, _ in tmpl}
    live = split(live_text)
    live_by = {h: body for h, body in live}
    protected = PROTECTED.get(name, set())
    generated = GENERATED.get(name, set())

    for idx, (heading, body) in enumerate(tmpl):
        if heading not in live_by:
            if heading == PREAMBLE:
                continue
            # Insert after the nearest earlier template heading the live file has.
            after = next((h for h, _ in reversed(tmpl[:idx]) if h in live_by), None)
            changes.append({
                "file": name, "kind": "add-section", "heading": heading, "safe": True,
                "after": after, "new": body, "diff": diff_text("", body, name),
            })
            continue
        live_body = live_by[heading]
        if norm(live_body) == norm(body):
            continue
        if heading in protected:
            kept.append(f"{name} {heading}")
            continue
        if heading in generated:
            changes.append({
                "file": name, "kind": "regenerate-section", "heading": heading, "safe": True,
                "new": body, "diff": diff_text(live_body, body, f"{name} {heading}"),
            })
            continue
        removed = [l for l in norm(live_body).splitlines() if l.strip() and l not in norm(body).splitlines()]
        changes.append({
            "file": name, "kind": "replace-section", "heading": heading, "safe": False,
            "removes_lines": len(removed), "new": body,
            "diff": diff_text(live_body, body, f"{name} {heading}"),
        })
    for heading, _ in live:
        if heading not in template_headings and heading != PREAMBLE:
            kept.append(f"{name} {heading}")
    return changes, kept


def refusal(sanctum: Path, fmt: str) -> dict | None:
    """A not-applicable report for anything that is not a v7 sanctum to repair."""
    messages = {
        "absent": "No sanctum to upgrade — First Breath (`uv run {skill-root}/scripts/init-sanctum.py`) scaffolds one.",
        "v1": (
            "This is a v1 store. Convert it first: "
            "`uv run {skill-root}/scripts/migrate-sidecar-to-v2.py --in-place`, "
            "then `uv run {skill-root}/scripts/migrate-sanctum-to-v7.py`."
        ),
        "v2": (
            "This is a v2 store. Convert it with `uv run {skill-root}/scripts/migrate-sanctum-to-v7.py`; "
            "upgrade-sanctum.py repairs v7 sanctums only."
        ),
    }
    if fmt == "damaged" and sanctum.is_dir() and not (sanctum / "HOW-I-REMEMBER.md").exists() and any(
        (sanctum / m).exists() for m in OLD_STORE_MARKERS
    ):
        fmt, message = "v2", (
            "This looks like a partial v2 store (INDEX.md / MEMORY.md / access-boundaries.md). "
            "Convert it with `uv run {skill-root}/scripts/migrate-sanctum-to-v7.py`; "
            "upgrade-sanctum.py repairs v7 sanctums only."
        )
    elif fmt in messages:
        message = messages[fmt]
    else:
        return None
    return {"status": "not-applicable", "sanctum_path": str(sanctum), "sidecar_format": fmt,
            "message": message, "changes": []}


def plan(project_root: Path, sanctum: Path, skill_path: Path) -> dict:
    state = _seed.classify_sanctum(sanctum)
    refused = refusal(sanctum, state["sidecar_format"])
    if refused:
        return refused

    changes: list[dict] = []
    kept: list[str] = []

    for folder in FOLDERS:
        if not (sanctum / folder).is_dir():
            changes.append({"file": folder + "/", "kind": "create-folder", "heading": None, "safe": True,
                            "diff": f"+{folder}/\n"})

    expected, notes = expected_identity(project_root, sanctum, skill_path)
    for name, new_text in expected.items():
        path = sanctum / name
        if not path.is_file():
            changes.append({"file": name, "kind": "create-file", "heading": None, "safe": True,
                            "new": new_text, "diff": diff_text("", new_text, name)})
            continue
        file_changes, file_kept = plan_file(name, path.read_text(encoding="utf-8"), new_text)
        changes.extend(file_changes)
        kept.extend(file_kept)

    disciplines, discipline_notes = expected_disciplines(skill_path)
    notes.extend(discipline_notes)
    for rel, new_text in disciplines.items():
        path = sanctum / rel
        if not path.is_file():
            changes.append({"file": rel, "kind": "create-file", "heading": None, "safe": True,
                            "new": new_text, "diff": diff_text("", new_text, rel)})
            continue
        if rel.startswith(INCIDENTS_DIR):
            continue  # the stories are only ever created
        live = path.read_text(encoding="utf-8")
        if norm(live) == norm(new_text):
            continue
        removed = [l for l in norm(live).splitlines() if l.strip() and l not in norm(new_text).splitlines()]
        changes.append({"file": rel, "kind": "replace-file", "heading": None, "safe": False,
                        "removes_lines": len(removed), "new": new_text, "diff": diff_text(live, new_text, rel)})

    counters: dict[str, int] = {}
    for change in changes:
        counters[change["file"]] = counters.get(change["file"], 0) + 1
        change["id"] = f"{change['file']}#{counters[change['file']]}"
    return {
        "status": "dry-run",
        "sanctum_path": str(sanctum),
        "skill_path": str(skill_path),
        "sidecar_format": state["sidecar_format"],
        "missing_identity": state["missing_spine"],
        "changes": changes,
        "owner_sections_kept": kept,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def _apply_sections(path: Path, file_changes: list[dict]) -> None:
    sections = split(path.read_text(encoding="utf-8"))
    for change in file_changes:
        headings = [h for h, _ in sections]
        if change["kind"] in ("replace-section", "regenerate-section"):
            i = headings.index(change["heading"])
            sections[i] = (change["heading"], change["new"])
        elif change["kind"] == "add-section":
            after = change["after"]
            i = headings.index(after) + 1 if after in headings else len(sections)
            new_body = change["new"].rstrip("\n") + ("\n\n" if i < len(sections) else "\n")
            if i > 0 and not sections[i - 1][1].endswith("\n\n"):
                prev_h, prev_b = sections[i - 1]
                sections[i - 1] = (prev_h, prev_b.rstrip("\n") + "\n\n")
            sections.insert(i, (change["heading"], new_body))
    path.write_text(join(sections), encoding="utf-8")


def apply_changes(sanctum: Path, report: dict, selection: set[str]) -> dict:
    """Apply the selected changes ('safe' and/or ids). Back up each file first."""
    chosen = [c for c in report["changes"] if c["id"] in selection or ("safe" in selection and c["safe"])]
    unknown = sorted(s for s in selection if s != "safe" and s not in {c["id"] for c in report["changes"]})
    if not chosen:
        if selection == {"safe"} and not any(c["safe"] for c in report["changes"]):
            return {**report, "status": "nothing-to-apply", "applied": [], "unknown_ids": []}
        return {**report, "status": "nothing-applied", "applied": [], "unknown_ids": unknown}

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = sanctum.parent / f".{sanctum.name}-upgrade-backup-{stamp}"

    # Folders first, so new files have somewhere to go.
    for change in chosen:
        if change["kind"] == "create-folder":
            (sanctum / change["file"]).mkdir(parents=True, exist_ok=True)

    # Missing disciplines/incidents: when every planned one was chosen, re-seed
    # them the way the recovery CLI does (only missing files are written).
    seed_creates = [
        c for c in report["changes"]
        if c["kind"] == "create-file" and c["file"].startswith((DISCIPLINES_DIR, INCIDENTS_DIR))
    ]
    chosen_seed = [c for c in chosen if c in seed_creates]
    if chosen_seed and len(chosen_seed) == len(seed_creates):
        references = Path(report["skill_path"]) / "references"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _seed.write_disciplines(sanctum, references, only_missing=True)
    else:
        for change in chosen_seed:
            target = sanctum / change["file"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(change["new"], encoding="utf-8")

    by_file: dict[str, list[dict]] = {}
    for change in chosen:
        if change["kind"] == "create-folder" or change in chosen_seed:
            continue
        by_file.setdefault(change["file"], []).append(change)

    for name, file_changes in by_file.items():
        path = sanctum / name
        if path.exists():
            (backup / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup / name)
        whole = [c for c in file_changes if c["kind"] in ("create-file", "replace-file")]
        if whole:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(whole[0]["new"], encoding="utf-8")
            continue
        _apply_sections(path, file_changes)

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
    if report.get("missing_identity"):
        out.append(f"Missing identity files: {', '.join(report['missing_identity'])}")
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
    if report["status"] == "nothing-applied":
        out.append("Nothing was applied: --apply named no change this plan proposes.")
    if report["status"] == "nothing-to-apply":
        out.append("Nothing to apply: no safe change is pending.")
    if report.get("unknown_ids"):
        out.append(f"Unknown ids (not applied): {', '.join(report['unknown_ids'])}")
    if report["status"] == "dry-run":
        for c in changes:
            out += ["", f"----- {c['id']} {c['kind']} -----", c["diff"].rstrip()]
        out += [
            "",
            "Nothing was written. Apply with --apply safe (folders, missing files, additions, the "
            "generated roster) and/or --apply <id>,<id> after the owner confirms each replacement.",
        ]
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run diff and confirmed repair/upgrade of an existing v7 sanctum from the shipped templates."
    )
    parser.add_argument("--project-root", default=".", help="Project root (where _bmad/ lives).")
    parser.add_argument(
        "--sanctum-dir",
        default=None,
        help="Override the sanctum directory (default: <project-root>/_bmad/memory/suno-agent-band-manager).",
    )
    parser.add_argument("--skill-path", default=None, help="Skill dir (assets/, references/). Default: inferred.")
    parser.add_argument(
        "--apply",
        default=None,
        help="'safe' and/or comma-separated change ids. Omit for a dry run.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    sanctum, _ = _seed.locate_sanctum(project_root, args.sanctum_dir)
    sanctum = sanctum.resolve()
    skill_path = Path(args.skill_path).resolve() if args.skill_path else Path(__file__).resolve().parent.parent

    report = plan(project_root, sanctum, skill_path)
    if args.apply and report["status"] == "dry-run" and not args.apply.strip(" ,"):
        report = {**report, "status": "nothing-applied", "applied": [], "unknown_ids": []}
    elif args.apply and report["status"] == "dry-run":
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
    return exit_code(report, bool(args.apply))


def exit_code(report: dict, applying: bool) -> int:
    """0 for a dry run or a clean apply; 1 when an apply did not do what it was asked."""
    if not applying:
        return 0
    if report.get("unknown_ids"):
        return 1
    return 0 if report["status"] in ("applied", "nothing-to-apply") else 1


if __name__ == "__main__":
    sys.exit(main())
