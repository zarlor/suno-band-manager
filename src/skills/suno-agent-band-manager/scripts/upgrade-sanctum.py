#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Repair and upgrade an existing v7 sanctum from the shipped templates, carrying
the owner's own text into the new format.

The sanctum is `{project-root}/_bmad/memory/suno-agent-band-manager/`. Template
and creed fixes never reach an existing sanctum on their own: First Breath
(init-sanctum.py) scaffolds only a fresh one. This script compares the live
sanctum with what the current skill would produce and plans the upgrade. It
never drops a line of the owner's on its own.

Three texts, not two. For each templated unit (an identity-file section, or a
whole discipline file) it compares the live text, the text the skill ships now
and the base: the shipped text the sanctum last took, recorded in
`memory/.template-base.json` (First Breath, the v2 converter and every upgrade
write it). From those:

  live = shipped now          in sync; nothing to do
  base = shipped now          the template hasn't changed since the sanctum took
                              it, so a live difference is the owner's (or Mac's)
                              own text and stands; nothing to do
  live = base                 nobody changed it: update to the new template (safe)
  live, base, new merge       the owner's edits and the template's edits touch
    cleanly                   different lines: both kept, merged (safe)
  otherwise                   integrate: Mac writes the new-format text with
                              the owner's lines carried in, and this script
                              checks every one of them landed (see --integrate)

A unit whose live text has no lines beyond the new template (nothing of the
owner's to carry) is an update. A unit with no base on record (a sanctum from
before the record existed, or converted from v2) is an integrate whenever it
holds lines the new template doesn't.

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
  update-section      untouched older template text, or nothing of the owner's (safe)
  update-file           in it; the new template replaces it
  merge-section       the owner's edits and the new template merged line by     (safe)
  merge-file            line, with no overlap
  integrate-section   the owner's text and the new template overlap, or there   (Mac)
  integrate-file        is no base: Mac carries the owner's lines into the new
                        format and applies it with --integrate

Sections the owner grows are never proposed: CREED Mission, PERSONA Evolution
Log, BOND Owner Summary / Boundaries / Notes, PULSE Owner Preferences,
CAPABILITIES Learned, and any section the template does not have. Incident
stories are only ever created, never replaced; when a discipline is to be
integrated and its incident file is missing, the incident is written as part
of that integration (the owner's stories go there), not seeded on its own.
Standing memory files and raw/ are the owner's and Mac's own; never proposed.

Default is a dry run that prints every proposed change with a diff. Then:

  --apply safe|ID,...   apply the safe changes and/or named ones. An integrate
                        change can't be applied this way: it would drop the
                        owner's lines.
  --integrate ID --text FILE [--also PATH ...] [--dropped FILE]
                        write Mac's integrated text (FILE: the whole section,
                        heading included, or the whole discipline file) after
                        checking that each of the owner's lines (the change's
                        `owner_lines`) appears in FILE or in an --also file
                        (sanctum-relative, already written, e.g. the incident
                        story) or is listed in --dropped, a JSON list of
                        {"line": ..., "why": ...} for lines that were earlier
                        shipped wording, not the owner's. Any line unaccounted
                        for refuses the write and is listed. The previous text
                        goes to raw/ as a distilled record of the integration.
  --keep ID,...         the owner's text stays exactly as it is, on purpose.
                        Records the new template as its base, so the change
                        is not proposed again until the template changes.

Every file touched is backed up first to a sibling
`.suno-agent-band-manager-upgrade-backup-<stamp>/`, and every write records the
base, as does any unit found in sync.

A v1 or v2 store (the legacy `_bmad/_memory/band-manager-sidecar/`) is not
upgraded here: it converts with migrate-sanctum-to-v7.py.

Exit codes: 0 for a dry run, or when every named action was done; 1 when an
action did nothing (a v1/v2 store or no sanctum), named an unknown id, named an
integrate change for --apply, or an --integrate check failed (the JSON says
which, in `status`, `unknown_ids`, `needs_integration` and `unaccounted`).
`--apply safe` with no safe change pending is `nothing-to-apply`, exit 0.

Usage:
    uv run {skill-root}/scripts/upgrade-sanctum.py --project-root PATH [--sanctum-dir DIR]
        [--apply safe|ID[,ID...]] [--keep ID[,ID...]]
        [--integrate ID --text FILE [--also PATH ...] [--dropped FILE]]
        [--format text|json]
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import sys
import warnings
from datetime import date, datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_sanctum_seed():
    seed_path = Path(__file__).resolve().parent / "_sanctum_seed.py"
    spec = spec_from_file_location("_sanctum_seed", seed_path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_seed = _load_sanctum_seed()

BORN_RE = re.compile(r"\*\*Born:\*\*\s*(\d{4}-\d{2}-\d{2})")
PREAMBLE = _seed.PREAMBLE
split = _seed.template_units

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
UNIT_KINDS = ("update", "merge", "integrate")
MARKDOWN_LEAD_RE = re.compile(r"^(?:[#>*+\-|]+\s*|\d+[.)]\s+|_+(?=\S))+")


def join(sections: list[tuple[str, str]]) -> str:
    return "".join(body if body.endswith("\n") else body + "\n" for _, body in sections)


def norm(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def diff_text(old: str, new: str, label: str, a: str = "live", b: str = "template") -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"{a}/{label}",
            tofile=f"{b}/{label}",
        )
    )


# ---------------------------------------------------------------------------
# Line accounting and the three-way merge
# ---------------------------------------------------------------------------


def line_key(line: str) -> str:
    """A line compared for content: markdown lead (#, >, -, 1.) and spacing stripped."""
    text = MARKDOWN_LEAD_RE.sub("", line.strip())
    return " ".join(text.split())


def owner_lines(live: str, reference: str) -> list[str]:
    """Lines of `live` (as written) whose content `reference` doesn't hold."""
    ref = {line_key(l) for l in reference.splitlines()}
    out: list[str] = []
    for line in live.splitlines():
        key = line_key(line)
        if key and key not in ref and line.strip() not in out:
            out.append(line.strip())
    return out


def flat(text: str) -> str:
    """The text as one run of content, so a re-wrapped or re-bulleted line still matches."""
    return " ".join(k for k in (line_key(l) for l in text.splitlines()) if k)


def _hunks(base: list[str], other: list[str]) -> list[tuple[int, int, list[str]]]:
    matcher = difflib.SequenceMatcher(None, base, other, autojunk=False)
    return [(i1, i2, other[j1:j2]) for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"]


def merge3(base: str, live: str, new: str) -> str | None:
    """Line-level three-way merge, or None when the two sides' edits touch.

    Conservative: edits that overlap or merely touch on the base count as a
    conflict, so a merge is returned only when nothing of either side can be lost.
    """
    b = base.splitlines(keepends=True)
    if b and not b[-1].endswith("\n"):
        b[-1] += "\n"
    sides = {}
    for name, text in (("live", live), ("new", new)):
        lines = text.splitlines(keepends=True)
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        sides[name] = lines
    hunks = sorted(
        [(i1, i2, rep, "live") for i1, i2, rep in _hunks(b, sides["live"])]
        + [(i1, i2, rep, "new") for i1, i2, rep in _hunks(b, sides["new"])],
        key=lambda h: (h[0], h[1]),
    )
    groups: list[dict] = []
    for h in hunks:
        if groups and h[0] <= groups[-1]["end"]:
            groups[-1]["hunks"].append(h)
            groups[-1]["end"] = max(groups[-1]["end"], h[1])
        else:
            groups.append({"start": h[0], "end": h[1], "hunks": [h]})
    out: list[str] = []
    pos = 0
    for g in groups:
        out += b[pos:g["start"]]
        results = {}
        for side in ("live", "new"):
            mine = [h for h in g["hunks"] if h[3] == side]
            if not mine:
                continue
            seg, cur = [], g["start"]
            for i1, i2, rep, _ in mine:
                seg += b[cur:i1] + rep
                cur = i2
            results[side] = seg + b[cur:g["end"]]
        if len(results) == 2 and results["live"] != results["new"]:
            return None
        out += next(iter(results.values()))
        pos = g["end"]
    out += b[pos:]
    return "".join(out)


def classify(key: str, live: str, new: str, base: dict | None) -> dict | None:
    """The change for one templated unit, or None when nothing is to be done.

    Returns {"kind": update|merge|integrate, ...} or {"kind": "kept"} when the
    owner's text stands on purpose.
    """
    if norm(live) == norm(new):
        return None
    base_text = base["text"] if base else None
    if base_text is not None and norm(base_text) == norm(new):
        return {"kind": "kept"} if base.get("status") == "kept" else None
    if base_text is not None and norm(live) == norm(base_text):
        return {"kind": "update", "result": new}
    if base_text is not None:
        mine = owner_lines(live, base_text)
        if not mine:
            return {"kind": "update", "result": new}
        merged = merge3(base_text, live, new)
        if merged is not None:
            return {"kind": "merge", "result": merged}
        return {"kind": "integrate", "owner_lines": mine,
                "template_diff": diff_text(base_text, new, key, "base", "template")}
    mine = owner_lines(live, new)
    if not mine:
        return {"kind": "update", "result": new}
    return {"kind": "integrate", "owner_lines": mine}


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
        expected["CAPABILITIES.md"] = _seed.generate_capabilities_md(_seed.menu_rows(csv_path))
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


def _unit_change(file: str, heading: str | None, live: str, new: str, base: dict | None) -> dict | None:
    key = _seed.unit_key(file, heading)
    found = classify(key, live, new, base)
    if found is None or found["kind"] == "kept":
        return found
    scope = "file" if heading is None else "section"
    label = key
    change = {
        "file": file, "kind": f"{found['kind']}-{scope}", "heading": heading, "key": key,
        "safe": found["kind"] != "integrate", "new": new, "live": live,
    }
    if found["kind"] == "integrate":
        change["owner_lines"] = found["owner_lines"]
        change["diff"] = diff_text(live, new, label)
        if found.get("template_diff"):
            change["template_diff"] = found["template_diff"]
    else:
        change["result"] = found["result"]
        change["diff"] = diff_text(live, found["result"], label, "live", "result")
    return change


def plan_file(name: str, live_text: str, new_text: str, base: dict | None = None) -> tuple[list[dict], list[str], dict]:
    """(changes, owner sections kept, units in sync {key: text}) for one existing identity file."""
    base = base or {}
    changes: list[dict] = []
    kept: list[str] = []
    synced: dict[str, str] = {}
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
                "key": _seed.unit_key(name, heading), "after": after, "new": body,
                "diff": diff_text("", body, name),
            })
            continue
        live_body = live_by[heading]
        if heading in protected:
            if norm(live_body) != norm(body):
                kept.append(f"{name} {heading}")
            continue
        if norm(live_body) == norm(body):
            if heading not in generated:
                synced[_seed.unit_key(name, heading)] = body
            continue
        if heading in generated:
            changes.append({
                "file": name, "kind": "regenerate-section", "heading": heading, "safe": True,
                "new": body, "diff": diff_text(live_body, body, f"{name} {heading}"),
            })
            continue
        change = _unit_change(name, heading, live_body, body, base.get(_seed.unit_key(name, heading)))
        if change is None:
            continue
        if change["kind"] == "kept":
            kept.append(f"{name} {heading} (kept on purpose)")
            continue
        changes.append(change)
    for heading, _ in live:
        if heading not in template_headings and heading != PREAMBLE:
            kept.append(f"{name} {heading}")
    return changes, kept, synced


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

    base = _seed.load_template_base(sanctum)
    changes: list[dict] = []
    kept: list[str] = []
    synced: dict[str, str] = {}

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
        file_changes, file_kept, file_synced = plan_file(name, path.read_text(encoding="utf-8"), new_text, base)
        changes.extend(file_changes)
        kept.extend(file_kept)
        synced.update(file_synced)

    disciplines, discipline_notes = expected_disciplines(skill_path)
    notes.extend(discipline_notes)
    integrating: dict[str, dict] = {}
    for rel, new_text in disciplines.items():
        if rel.startswith(INCIDENTS_DIR):
            continue
        path = sanctum / rel
        if not path.is_file():
            changes.append({"file": rel, "kind": "create-file", "heading": None, "safe": True,
                            "new": new_text, "diff": diff_text("", new_text, rel)})
            continue
        live = path.read_text(encoding="utf-8")
        if norm(live) == norm(new_text):
            synced[rel] = new_text
            continue
        change = _unit_change(rel, None, live, new_text, base.get(rel))
        if change is None:
            continue
        if change["kind"] == "kept":
            kept.append(f"{rel} (kept on purpose)")
            continue
        changes.append(change)
        if change["kind"] == "integrate-file":
            integrating[rel.rsplit("/", 1)[1]] = change
    for rel, new_text in disciplines.items():
        if not rel.startswith(INCIDENTS_DIR) or (sanctum / rel).is_file():
            continue
        owner = integrating.get(rel.rsplit("/", 1)[1])
        if owner is not None:
            # The owner's stories for this discipline go here as part of its integration.
            owner["incident"] = rel
            owner["incident_template"] = new_text
            continue
        changes.append({"file": rel, "kind": "create-file", "heading": None, "safe": True,
                        "new": new_text, "diff": diff_text("", new_text, rel)})

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
        "has_base_record": bool(base),
        "changes": changes,
        "owner_sections_kept": kept,
        "synced": synced,
        "notes": notes,
    }


def pending_summary(report: dict) -> dict:
    """Counts for the wake: safe changes pending and integrations waiting on Mac."""
    changes = report.get("changes", [])
    return {
        "safe": sum(1 for c in changes if c.get("safe")),
        "integrate": [c["id"] for c in changes if c["kind"].startswith("integrate")],
    }


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


class Writer:
    """Backs up each file once before its first write and keeps the base record."""

    def __init__(self, sanctum: Path, report: dict, today: str | None = None):
        self.sanctum = sanctum
        self.today = today or date.today().isoformat()
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.backup = sanctum.parent / f".{sanctum.name}-upgrade-backup-{stamp}"
        n = 2
        while self.backup.exists():  # two runs in one second never share a backup
            self.backup = sanctum.parent / f".{sanctum.name}-upgrade-backup-{stamp}-{n}"
            n += 1
        self.backed: set[str] = set()
        self.base = _seed.load_template_base(sanctum)
        for key, text in report.get("synced", {}).items():
            if key not in self.base or norm(self.base[key]["text"]) != norm(text):
                self.base[key] = {"text": text, "status": "taken", "date": self.today}

    def back_up(self, rel: str) -> None:
        path = self.sanctum / rel
        if rel in self.backed or not path.exists():
            return
        (self.backup / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, self.backup / rel)
        self.backed.add(rel)

    def record(self, key: str, text: str, status: str = "taken") -> None:
        self.base[key] = {"text": text, "status": status, "date": self.today}

    def record_file(self, rel: str, text: str) -> None:
        for key, entry in _seed.base_entries(rel, text, self.today).items():
            self.base[key] = entry

    def write_unit(self, change: dict, text: str) -> None:
        path = self.sanctum / change["file"]
        self.back_up(change["file"])
        if change.get("heading") is None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
            return
        sections = split(path.read_text(encoding="utf-8"))
        headings = [h for h, _ in sections]
        i = headings.index(change["heading"])
        if i < len(sections) - 1 and not text.endswith("\n\n"):
            text = text.rstrip("\n") + "\n\n"
        sections[i] = (change["heading"], text)
        path.write_text(join(sections), encoding="utf-8")

    def archive(self, change: dict, distilled_to: list[str], dropped: list[dict]) -> str:
        """The unit's previous text into raw/, marked distilled into where it went."""
        slug = _seed._slug(change["key"].replace("/", " ").replace("#", " "))
        rel = f"raw/{self.today}-upgrade-{slug}.md"
        n = 2
        while (self.sanctum / rel).exists():
            rel = f"raw/{self.today}-upgrade-{slug}-{n}.md"
            n += 1
        lines = [
            "---", "status: distilled", f"distilled_to: {json.dumps(distilled_to)}",
            f"note: \"{change['key']} before the {self.today} template upgrade; its lines were carried "
            "into the new format (checked by upgrade-sanctum.py --integrate).\"",
            "---", "", f"# {change['key']} — before the {self.today} upgrade", "", change["live"].rstrip(), "",
        ]
        if dropped:
            lines += ["## Lines not carried over, and why", ""]
            lines += [f"- `{d['line']}` — {d['why']}" for d in dropped]
            lines.append("")
        out = self.sanctum / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines), encoding="utf-8")
        return rel

    def save(self) -> None:
        _seed.save_template_base(self.sanctum, self.base)

    @property
    def backup_path(self) -> str | None:
        return str(self.backup) if self.backup.exists() else None


def apply_changes(sanctum: Path, report: dict, selection: set[str], today: str | None = None) -> dict:
    """Apply the selected changes ('safe' and/or ids). Integrations are refused here."""
    ids = {c["id"] for c in report["changes"]}
    unknown = sorted(s for s in selection if s != "safe" and s not in ids)
    needs = sorted(c["id"] for c in report["changes"]
                   if c["id"] in selection and c["kind"].startswith("integrate"))
    chosen = [c for c in report["changes"]
              if not c["kind"].startswith("integrate")
              and (c["id"] in selection or ("safe" in selection and c["safe"]))]
    if not chosen:
        if selection == {"safe"} and not any(c["safe"] for c in report["changes"]):
            return {**report, "status": "nothing-to-apply", "applied": [], "unknown_ids": [],
                    "needs_integration": []}
        return {**report, "status": "nothing-applied", "applied": [], "unknown_ids": unknown,
                "needs_integration": needs}

    writer = Writer(sanctum, report, today)

    for change in chosen:
        if change["kind"] == "create-folder":
            (sanctum / change["file"]).mkdir(parents=True, exist_ok=True)

    for change in chosen:
        kind = change["kind"]
        if kind == "create-folder":
            continue
        path = sanctum / change["file"]
        if kind == "create-file":
            if path.exists():
                continue  # appeared since planning; never overwrite
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(change["new"], encoding="utf-8")
            if not change["file"].startswith(INCIDENTS_DIR) and change["file"] != "CAPABILITIES.md":
                writer.record_file(change["file"], change["new"])
        elif kind == "add-section":
            writer.back_up(change["file"])
            sections = split(path.read_text(encoding="utf-8"))
            headings = [h for h, _ in sections]
            after = change["after"]
            i = headings.index(after) + 1 if after in headings else len(sections)
            new_body = change["new"].rstrip("\n") + ("\n\n" if i < len(sections) else "\n")
            if i > 0 and not sections[i - 1][1].endswith("\n\n"):
                prev_h, prev_b = sections[i - 1]
                sections[i - 1] = (prev_h, prev_b.rstrip("\n") + "\n\n")
            sections.insert(i, (change["heading"], new_body))
            path.write_text(join(sections), encoding="utf-8")
            writer.record(change["key"], change["new"])
        elif kind == "regenerate-section":
            writer.write_unit(change, change["new"])
        elif kind.split("-")[0] in ("update", "merge"):
            writer.write_unit(change, change["result"])
            writer.record(change["key"], change["new"])
    writer.save()
    return {
        **report,
        "status": "applied",
        "applied": [c["id"] for c in chosen],
        "backup_path": writer.backup_path,
        "unknown_ids": unknown,
        "needs_integration": needs,
    }


def keep_changes(sanctum: Path, report: dict, selection: set[str], today: str | None = None) -> dict:
    """The owner's text stays as it is; the new template becomes its base."""
    by_id = {c["id"]: c for c in report["changes"]}
    unknown = sorted(s for s in selection if s not in by_id or by_id[s]["kind"].split("-")[0] not in UNIT_KINDS)
    chosen = [by_id[s] for s in sorted(selection) if s not in unknown]
    if not chosen:
        return {**report, "status": "nothing-kept", "kept": [], "unknown_ids": unknown}
    writer = Writer(sanctum, report, today)
    for change in chosen:
        writer.record(change["key"], change["new"], status="kept")
    writer.save()
    return {**report, "status": "kept", "kept": [c["id"] for c in chosen], "unknown_ids": unknown}


def integrate_change(sanctum: Path, report: dict, change_id: str, text: str,
                     also: list[str], dropped: list[dict], today: str | None = None) -> dict:
    """Write Mac's integrated text once every owner line is accounted for."""
    by_id = {c["id"]: c for c in report["changes"]}
    change = by_id.get(change_id)
    if change is None or change["kind"].split("-")[0] not in UNIT_KINDS:
        return {**report, "status": "nothing-integrated", "unknown_ids": [change_id]}
    problems: list[str] = []
    if change.get("heading") is not None and split(text)[0][0] != change["heading"]:
        problems.append(f"the text must be the whole section, starting with its heading ({change['heading']})")
    destinations = [flat(text)]
    for rel in also:
        path = (sanctum / rel).resolve()
        if not path.is_relative_to(sanctum.resolve()) or not path.is_file():
            problems.append(f"--also {rel}: not a file in the sanctum (write it first)")
            continue
        destinations.append(flat(path.read_text(encoding="utf-8")))
    bad_drops = [d for d in dropped if not isinstance(d, dict) or not str(d.get("line", "")).strip()
                 or not str(d.get("why", "")).strip()]
    if bad_drops:
        problems.append("--dropped: every entry needs a non-empty \"line\" and \"why\"")
    dropped_keys = {line_key(str(d.get("line", ""))) for d in dropped if isinstance(d, dict)}
    unaccounted = [
        line for line in change.get("owner_lines", [])
        if line_key(line) not in dropped_keys and not any(line_key(line) in dest for dest in destinations)
    ]
    if problems or unaccounted:
        return {**report, "status": "integration-refused", "integrated": [], "unknown_ids": [],
                "problems": problems, "unaccounted": unaccounted}
    writer = Writer(sanctum, report, today)
    writer.write_unit(change, text)
    writer.record(change["key"], change["new"], status="integrated")
    raw = writer.archive(change, [change["file"], *also], [d for d in dropped if isinstance(d, dict)])
    writer.save()
    return {**report, "status": "integrated", "integrated": [change_id], "unknown_ids": [],
            "archived_to": raw, "backup_path": writer.backup_path}


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
        if c["kind"].startswith("integrate"):
            flag = f"integrate ({len(c.get('owner_lines', []))} line(s) of the owner's to carry)"
        else:
            flag = "safe" if c["safe"] else "review"
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
    if report["status"] == "kept":
        out.append(f"Kept as they are: {', '.join(report['kept'])}")
    if report["status"] == "integrated":
        out.append(f"Integrated: {', '.join(report['integrated'])}; previous text in {report['archived_to']}")
        out.append(f"Backup: {report.get('backup_path')}")
    if report["status"] == "integration-refused":
        out.append("Integration refused; nothing was written.")
        out += [f"  ! {p}" for p in report.get("problems", [])]
        if report.get("unaccounted"):
            out.append("  Owner lines not found in the text, an --also file or --dropped:")
            out += [f"    - {line}" for line in report["unaccounted"]]
    if report["status"] in ("nothing-applied", "nothing-kept", "nothing-integrated"):
        out.append("Nothing was done: no change this plan proposes was named for that action.")
    if report["status"] == "nothing-to-apply":
        out.append("Nothing to apply: no safe change is pending.")
    if report.get("needs_integration"):
        out.append("Not applied (they hold the owner's lines; use --integrate or --keep): "
                   + ", ".join(report["needs_integration"]))
    if report.get("unknown_ids"):
        out.append(f"Unknown ids (not applied): {', '.join(report['unknown_ids'])}")
    if report["status"] == "dry-run":
        for c in changes:
            out += ["", f"----- {c['id']} {c['kind']} -----"]
            if c["kind"].startswith("integrate"):
                if c.get("template_diff"):
                    out += ["What the template changed since this sanctum took it:", c["template_diff"].rstrip(), ""]
                out += ["The owner's lines to carry into the new format:"]
                out += [f"  | {line}" for line in c.get("owner_lines", [])]
                if c.get("incident"):
                    out.append(f"Stories go to {c['incident']} (missing; write it as part of this integration).")
                out += ["", "Live vs the new template:"]
            out.append(c["diff"].rstrip())
        out += [
            "",
            "Nothing was written. --apply safe writes the safe changes (folders, missing files, additions, "
            "the generated roster, updates and clean merges); each integrate change goes through "
            "--integrate ID --text FILE once its lines are carried into the new format, or --keep ID when "
            "the owner's text stays as it is.",
        ]
    return "\n".join(out) + "\n"


def _ids(value: str | None) -> set[str]:
    return {s.strip() for s in (value or "").split(",") if s.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan and apply the upgrade of an existing v7 sanctum to the shipped templates, "
                    "carrying the owner's own text into the new format."
    )
    parser.add_argument("--project-root", default=".", help="Project root (where _bmad/ lives).")
    parser.add_argument(
        "--sanctum-dir",
        default=None,
        help="Override the sanctum directory (default: <project-root>/_bmad/memory/suno-agent-band-manager).",
    )
    parser.add_argument("--skill-path", default=None, help="Skill dir (assets/, references/). Default: inferred.")
    parser.add_argument("--apply", default=None, help="'safe' and/or comma-separated change ids. Omit for a dry run.")
    parser.add_argument("--keep", default=None, help="Comma-separated change ids whose live text stays, on purpose.")
    parser.add_argument("--integrate", default=None, help="One change id to write from --text.")
    parser.add_argument("--text", default=None, help="File holding the integrated section or discipline file.")
    parser.add_argument("--also", action="append", default=[],
                        help="Sanctum-relative file that also received the owner's lines (repeatable).")
    parser.add_argument("--dropped", default=None,
                        help='JSON file: [{"line": ..., "why": ...}] for lines that were earlier shipped wording.')
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    sanctum, _ = _seed.locate_sanctum(project_root, args.sanctum_dir)
    sanctum = sanctum.resolve()
    skill_path = Path(args.skill_path).resolve() if args.skill_path else Path(__file__).resolve().parent.parent

    report = plan(project_root, sanctum, skill_path)
    acting = any(v is not None for v in (args.apply, args.keep, args.integrate))
    if report["status"] == "dry-run":
        if args.keep is not None:
            report = keep_changes(sanctum, report, _ids(args.keep))
            if report["status"] == "kept" and (args.apply is not None or args.integrate):
                report = plan(project_root, sanctum, skill_path)
        if args.integrate:
            if not args.text:
                parser.error("--integrate needs --text FILE")
            dropped = json.loads(Path(args.dropped).read_text(encoding="utf-8")) if args.dropped else []
            if not isinstance(dropped, list):
                parser.error("--dropped must hold a JSON list")
            report = integrate_change(sanctum, report, args.integrate.strip(),
                                      Path(args.text).read_text(encoding="utf-8"), args.also, dropped)
            if report["status"] == "integrated" and args.apply is not None:
                report = plan(project_root, sanctum, skill_path)
        if args.apply is not None and report["status"] == "dry-run":
            selection = _ids(args.apply)
            if selection:
                report = apply_changes(sanctum, report, selection)
            else:
                report = {**report, "status": "nothing-applied", "applied": [], "unknown_ids": []}

    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")
    if args.format == "json":
        slim = {**report, "changes": [{k: v for k, v in c.items() if k not in ("new", "live", "result")}
                                      for c in report["changes"]]}
        slim.pop("synced", None)
        print(json.dumps(slim, indent=2, ensure_ascii=False))
    else:
        sys.stdout.write(render_text(report))
    return exit_code(report, acting)


def exit_code(report: dict, acting: bool) -> int:
    """0 for a dry run or a clean action; 1 when an action did not do what it was asked."""
    if not acting:
        return 0
    if report.get("unknown_ids") or report.get("needs_integration"):
        return 1
    return 0 if report["status"] in ("applied", "nothing-to-apply", "kept", "integrated") else 1


if __name__ == "__main__":
    sys.exit(main())
