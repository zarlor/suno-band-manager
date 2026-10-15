#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Shared sanctum logic for Mac (suno-agent-band-manager).

One home for everything the waking, birth, migration and upgrade scripts must
agree on:

  - the BMad v7 sanctum path, the identity files that load at waking
    (SANCTUM_LOAD_ORDER) and the classification (absent / v7 / v2 / v1 /
    damaged, the legacy path checked when the v7 one is empty), matched
    case-sensitively
  - the waking map of memory/ and raw/
  - config resolution (BMad v7 `modules.suno` answers; the owner from BOND.md)
  - the menu roster (assets/menu.csv) that drives Mac's menu and CAPABILITIES.md
  - the Dominion (access boundaries) rendered into CREED.md
  - the disciplines and incidents sliced from `references/creed.md`

Imported by pre-activate.py, init-sanctum.py, migrate-sidecar-to-v2.py and
upgrade-sanctum.py. As a CLI it is the recovery path: re-seed a missing
discipline or incident file into an existing sanctum. It writes only
files that are missing unless `--force` is given, so shards that have grown new
learnings are never overwritten by accident.

Usage:
    _sanctum_seed.py --out DIR [--skill-path DIR] [--force]
    _sanctum_seed.py --help
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import warnings
from pathlib import Path

# ---------------------------------------------------------------------------
# The sanctum and its classification
# ---------------------------------------------------------------------------

# BMad v7 memory-agent layout (Continuity of Self): the sanctum lives at the
# standard path; five identity files load at waking, the memory itself is many
# small files under memory/ and raw/ that the waking map summarizes.
SANCTUM_REL = ("_bmad", "memory", "suno-agent-band-manager")
# Where the v1/v2 stores lived. A store found here is converted, never woken.
LEGACY_SANCTUM_REL = ("_bmad", "_memory", "band-manager-sidecar")

# The always-loaded set, in load order. This list is the single home of the
# load order: docs point here (via pre-activate's output) instead of copying it.
IDENTITY_FILES = [
    "PERSONA.md",         # Mac's living self
    "CREED.md",           # creed core: Constitution, Package Assembly core, Dominion
    "BOND.md",            # thin owner-model orienting file
    "HOW-I-REMEMBER.md",  # the memory layout and how it is written and tended
    "CAPABILITIES.md",    # built-in + learned capability roster
]
SANCTUM_LOAD_ORDER = IDENTITY_FILES
# The Pulse wake loads the same self plus the routine.
PULSE_LOAD_ORDER = [*IDENTITY_FILES, "PULSE.md"]

# The memory kinds a fresh sanctum starts with (HOW-I-REMEMBER.md explains each).
MEMORY_KINDS = ("work", "owner", "bands", "catalog", "module", "disciplines", "incidents", "chronology", "sessions")

# v1 and v2 markers, for stores still at the legacy path.
V1_MARKER = "index.md"
V2_SPINE = [
    "access-boundaries.md",
    "INDEX.md",
    "MEMORY.md",
    "CREED.md",
    "PERSONA.md",
    "BOND.md",
    "CAPABILITIES.md",
]
V2_MARKERS = [n for n in V2_SPINE if n != "access-boundaries.md"]


def sanctum_dir(project_root: Path, override: str | None = None) -> Path:
    return Path(override) if override else Path(project_root).joinpath(*SANCTUM_REL)


def legacy_sanctum_dir(project_root: Path) -> Path:
    return Path(project_root).joinpath(*LEGACY_SANCTUM_REL)


def classify_sanctum(sanctum: Path) -> dict:
    """Classify a sanctum dir. Names are compared exactly (case-sensitive).

    - absent  : no directory, or an empty one -> First Breath
    - v7      : every identity file present -> wake normally
    - v2      : the old seven-file spine (INDEX.md, MEMORY.md...) -> convert to v7
    - v1      : an `index.md` content store and no v2 spine file -> migrate to v2, then v7
    - damaged : anything else, including a partial v7 identity -> recovery route

    `os.listdir` returns the real directory entries, so on case-insensitive
    filesystems (macOS APFS, Windows NTFS) a v1 `index.md` is never mistaken
    for the v2 `INDEX.md`.
    """
    if not sanctum.exists():
        return {"sidecar_format": "absent", "needs_migration": False, "missing_spine": []}
    if not sanctum.is_dir():
        return {"sidecar_format": "damaged", "needs_migration": False, "missing_spine": list(IDENTITY_FILES)}
    names = set(os.listdir(sanctum))
    if not names:
        return {"sidecar_format": "absent", "needs_migration": False, "missing_spine": []}
    missing = [n for n in IDENTITY_FILES if n not in names]
    if not missing:
        return {"sidecar_format": "v7", "needs_migration": False, "missing_spine": []}
    if "HOW-I-REMEMBER.md" not in names:
        if not any(n in names for n in V2_MARKERS) and V1_MARKER in names:
            return {"sidecar_format": "v1", "needs_migration": True, "missing_spine": missing}
        if all(n in names for n in V2_SPINE):
            return {"sidecar_format": "v2", "needs_migration": True, "missing_spine": []}
    return {"sidecar_format": "damaged", "needs_migration": False, "missing_spine": missing}


def locate_sanctum(project_root: Path, override: str | None = None) -> tuple[Path, dict]:
    """The sanctum to wake from and its classification.

    The v7 path wins. Only when nothing lives there does a store at the legacy
    path count: it is reported (v1/v2) so the waking routes to its conversion.
    """
    sanctum = sanctum_dir(project_root, override)
    state = classify_sanctum(sanctum)
    if override or state["sidecar_format"] != "absent":
        return sanctum, state
    legacy = legacy_sanctum_dir(project_root)
    legacy_state = classify_sanctum(legacy)
    if legacy_state["sidecar_format"] in ("v1", "v2"):
        return legacy, legacy_state
    return sanctum, state


# ---------------------------------------------------------------------------
# The waking map (memory/ and raw/ summarized, never printed)
# ---------------------------------------------------------------------------

RECENT_COUNT = 8
DATED_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
STATUS_RAW_RE = re.compile(r"^status:\s*raw\s*$", re.MULTILINE)


def _folder_lines(root: Path, label: str) -> list[str]:
    if not root.is_dir():
        return []
    lines = []
    direct = [p for p in root.iterdir() if p.is_file() and not p.name.startswith(".")]
    if direct:
        lines.append(f"{label}/ ({len(direct)} files)")
    for folder in sorted(p for p in root.rglob("*") if p.is_dir()):
        count = sum(1 for p in folder.iterdir() if p.is_file() and not p.name.startswith("."))
        lines.append(f"{folder.relative_to(root.parent).as_posix()}/ ({count} files)")
    return lines


def _recent_dated(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    dated = [p for p in root.rglob("*") if p.is_file() and DATED_RE.match(p.name)]
    dated.sort(key=lambda p: (DATED_RE.match(p.name).group(1), p.name), reverse=True)
    return [p.relative_to(root.parent).as_posix() for p in dated[:RECENT_COUNT]]


def undistilled_raw(sanctum: Path) -> list[str]:
    raw = sanctum / "raw"
    if not raw.is_dir():
        return []
    out = []
    for p in sorted(raw.iterdir()):
        if not p.is_file():
            continue
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:2000]
        except OSError:
            continue
        if STATUS_RAW_RE.search(head):
            out.append(p.name)
    return out


def tending_state(sanctum: Path) -> dict:
    """When memory was last tended and the session notes written since."""
    stamp = sanctum / "memory" / ".tended"
    tended = stamp.read_text(encoding="utf-8").strip()[:10] if stamp.is_file() else ""
    sessions = sanctum / "memory" / "sessions"
    notes = [p.name for p in sessions.iterdir() if p.is_file() and DATED_RE.match(p.name)] if sessions.is_dir() else []
    since = [n for n in notes if DATED_RE.match(n).group(1) > tended] if tended else notes
    return {"tended": tended or None, "session_notes_since": len(since)}


def memory_map(sanctum: Path) -> str:
    """The generated map printed after the identity files at waking."""
    lines = _folder_lines(sanctum / "memory", "memory") + _folder_lines(sanctum / "raw", "raw")
    out = ["\n".join(lines) if lines else "(empty: nothing remembered yet)"]
    recent = _recent_dated(sanctum / "memory")
    if recent:
        out.append("Newest:\n" + "\n".join(f"  {r}" for r in recent))
    state = tending_state(sanctum)
    out.append(
        f"Tended: {state['tended']}; session notes since: {state['session_notes_since']}"
        if state["tended"] else f"Never tended; session notes: {state['session_notes_since']}"
    )
    raw = undistilled_raw(sanctum)
    if raw:
        out.append(f"Undistilled raw ({len(raw)}):\n" + "\n".join(f"  raw/{r}" for r in raw))
    return "\n\n".join(out)


def pending_text(sanctum: Path) -> str | None:
    pending = sanctum / "memory" / "pending.md"
    if pending.is_file():
        text = pending.read_text(encoding="utf-8").strip()
        return text or None
    return None


# ---------------------------------------------------------------------------
# Config resolution (BMad v7)
# ---------------------------------------------------------------------------

# BMad v7 config holds no owner keys: `bmad setup suno` asks only the module's
# questions (read as modules.suno.<key>) and core keeps output_folder. Who the
# owner is and which language they speak live in the sanctum's BOND.md, written
# at First Breath; before then, a lone voice file names them.
CORE_KEYS = ("output_folder",)
OWNER_KEYS = ("user_name", "communication_language", "document_output_language")
SUNO_KEYS = (
    "suno_tier",
    "default_mode",
    "band_profiles_folder",
    "songbook_folder",
    "pytorch_audio_tools",
)
CONFIG_DEFAULTS = {
    "user_name": None,
    "communication_language": "English",
    "document_output_language": "English",
    "output_folder": "{project-root}/_bmad-output",
    "suno_tier": None,
    "default_mode": "demo",
    "band_profiles_folder": "{project-root}/docs/band-profiles",
    "songbook_folder": "{project-root}/docs/songbook",
    "pytorch_audio_tools": "off",
}
VOICE_GLOB = "voice-context-*.md"
# What First Breath writes for an owner fact it hasn't learned yet. BOND.md
# carries it until the owner says what to call them; owner_from_bond never
# reads it as a name, and the wake treats it as an unfinished birth.
OWNER_UNSET = "_(not yet known)_"
RESOLVER_REL = ("_bmad", "scripts", "resolve_config.py")


def resolve_bmad_config(project_root: Path) -> tuple[dict, list[str]]:
    """`core.output_folder` and `modules.suno` from BMad's resolve_config.py.

    Returns (values, warnings). Merging the config layers is the resolver's
    job; a missing or failing resolver is reported, never papered over.
    """
    root = Path(project_root)
    script = root.joinpath(*RESOLVER_REL)
    if not script.is_file():
        return {}, ["BMad is not set up here (no _bmad/scripts/resolve_config.py): offer `bmad setup suno`; module defaults apply."]
    cmd = [sys.executable, str(script), "--project-root", str(root), "--key", "core.output_folder", "--key", "modules.suno"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return {}, [f"BMad config could not be resolved ({exc}); module defaults apply."]
    if proc.returncode != 0:
        reason = (proc.stderr or proc.stdout).strip().splitlines()
        return {}, [f"BMad config is broken ({reason[-1] if reason else 'resolve_config.py exited ' + str(proc.returncode)}); module defaults apply until it is fixed."]
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {}, ["resolve_config.py printed no JSON; module defaults apply."]
    values = dict(payload.get("modules.suno") or {})
    if payload.get("core.output_folder"):
        values["output_folder"] = payload["core.output_folder"]
    warnings_out = [] if payload.get("modules.suno") else [
        "No suno answers in BMad's config: the module defaults apply. `bmad setup suno` asks the questions."
    ]
    return values, warnings_out


def owner_from_bond(sanctum: Path) -> dict:
    """`user_name` and `communication_language` from BOND.md's Owner Summary."""
    bond = sanctum / "BOND.md"
    found: dict = {}
    if not bond.is_file():
        return found
    labels = {"name": "user_name", "language": "communication_language"}
    for line in bond.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*-\s*\*\*(Name|Language):\*\*\s*(.+?)\s*$", line)
        if match:
            value = match.group(2)
            # An unfilled template token or the not-yet-known marker is not a name.
            if "{" not in value and value != OWNER_UNSET:
                found.setdefault(labels[match.group(1).lower()], value)
    return found


def owner_from_voice_file(project_root: Path) -> str | None:
    """The owner's name from the voice file, when exactly one exists.

    The file name holds the slug (`voice-context-mary-jane.md`); its title-cased
    form ("Mary Jane") slugs back to the same file.
    """
    docs = project_root / "docs"
    files = sorted(docs.glob(VOICE_GLOB)) if docs.is_dir() else []
    if len(files) != 1:
        return None
    slug = files[0].stem[len("voice-context-"):]
    return slug.replace("-", " ").title() or None


def resolve_config(project_root: Path, sanctum: Path | None = None) -> dict:
    """Resolve Mac's config. Never raises; missing pieces fall back to defaults.

    Module answers and output_folder come from BMad's resolve_config.py; the
    owner's name and language from the sanctum's BOND.md, then a lone voice
    file, then defaults (greet generically, English). Config values hold
    `{project-root}`; the model fills it in.
    """
    project_root = Path(project_root)
    sanctum = sanctum or sanctum_dir(project_root)
    values: dict = {}
    sources: list[str] = []

    def fill(source: dict, keys: tuple, label: str) -> None:
        took = False
        for key in keys:
            if values.get(key) in (None, "") and source.get(key) not in (None, ""):
                values[key] = str(source[key])
                took = True
        if took and label not in sources:
            sources.append(label)

    bmad_values, warnings_out = resolve_bmad_config(project_root)
    fill(bmad_values, CORE_KEYS + SUNO_KEYS, "resolve_config.py")

    fill(owner_from_bond(sanctum), OWNER_KEYS, "BOND.md")
    voice_name = owner_from_voice_file(project_root)
    if voice_name:
        fill({"user_name": voice_name}, ("user_name",), "voice file")
    if values.get("communication_language"):
        values.setdefault("document_output_language", values["communication_language"])

    for key, default in CONFIG_DEFAULTS.items():
        if values.get(key) in (None, ""):
            values[key] = default
    if not values.get("user_name"):
        warnings_out.append(
            "user_name not known yet (BOND.md has no name, no single voice file): ask what to call the owner."
        )
    return {"values": values, "sources": sources or ["defaults"], "warnings": warnings_out}


def normalize_username(name: str) -> str:
    """Lowercase, spaces to hyphens (the voice-file naming rule)."""
    return name.strip().lower().replace(" ", "-")


def template_variables(project_root: Path, config: dict | None = None, birth_date: str | None = None) -> dict:
    """The substitution map for sanctum templates. Owner facts not yet known stay OWNER_UNSET."""
    from datetime import date

    values = (config or resolve_config(project_root))["values"]
    user = values.get("user_name")
    known_language = user is not None and values.get("communication_language")
    root = str(project_root)
    return {
        "user_name": user or OWNER_UNSET,
        "user_slug": normalize_username(user) if user else "<owner>",
        "communication_language": known_language or OWNER_UNSET,
        "birth_date": birth_date or date.today().isoformat(),
        "project_root": root,
        "project-root": root,
    }


def substitute_vars(content: str, variables: dict) -> str:
    for key, value in variables.items():
        content = content.replace(f"{{{key}}}", value)
    return content


# ---------------------------------------------------------------------------
# assets/menu.csv -> menu roster and CAPABILITIES.md
# ---------------------------------------------------------------------------

AGENT_SKILL_NAME = "suno-agent-band-manager"
MODULE_CODE = "Suno Band Manager"
# BMad v7 has no module help CSV; Mac's menu rows ship in his own skill, in the
# old CSV columns so the menu, routing and CAPABILITIES.md share one source.
MENU_CSV_REL = ("assets", "menu.csv")

# Rows the menu file keeps for standalone use but Mac's own menu leaves out.
# Feedback Loop (FL) is folded into Refine Song (RS): Mac's refine flow calls
# the suno-feedback-elicitor skill inside it.
MAC_MENU_EXCLUDE = {("suno-feedback-elicitor", "elicit-feedback")}
# Codes a user may still type at Mac; they route to the target code.
MENU_ALIASES = {"FL": "RS"}


def find_menu_csv(skill_dir: Path) -> Path | None:
    """Mac's menu roster, shipped in his skill folder."""
    candidate = Path(skill_dir).joinpath(*MENU_CSV_REL)
    return candidate if candidate.is_file() else None


def menu_rows(csv_path: Path, include_modules: list[str] | None = None) -> list[dict]:
    """Rows for Mac's menu: this module's rows minus the folded-in FL."""
    rows: list[dict] = []
    with open(csv_path, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            skill = (row.get("skill") or "").strip()
            action = (row.get("action") or "").strip()
            if (skill, action) in MAC_MENU_EXCLUDE:
                continue
            if include_modules is not None and (row.get("module") or "").strip() not in include_modules:
                continue
            rows.append(row)
    return rows


def route_for(row: dict) -> dict:
    """Routing entry for a CSV row: `type` + `target` (no `./` prefix)."""
    skill = (row.get("skill") or "").strip()
    action = (row.get("action") or "").strip()
    if skill == AGENT_SKILL_NAME:
        return {"name": action, "type": "prompt", "target": f"references/{action}.md"}
    return {"name": action, "type": "skill", "target": skill}


def generate_capabilities_md(rows: list[dict]) -> str:
    """CAPABILITIES.md: the built-in roster from assets/menu.csv + the Learned table."""
    lines = ["# Capabilities", "", "## Built-in", ""]
    if rows:
        lines += [
            "_Generated from Mac's `assets/menu.csv` (the same source as the menu)._",
            "",
            "| Code | Name | What it does | Runs |",
            "|------|------|--------------|------|",
        ]
        for row in rows:
            route = route_for(row)
            runs = f"`{route['target']}`" if route["type"] == "prompt" else f"skill: `{route['target']}`"
            lines.append(
                f"| [{(row.get('menu-code') or '').strip()}] | {(row.get('display-name') or '').strip()} | "
                f"{(row.get('description') or '').strip()} | {runs} |"
            )
        lines += ["", "Typing FL or \"feedback loop\" routes to [RS] Refine Song, which runs the feedback skill inside it."]
    else:
        lines += [
            "_assets/menu.csv was not found, so the roster could not be generated. "
            "Reinstall the suno-agent-band-manager skill, then regenerate this section with "
            "`uv run {skill-root}/scripts/upgrade-sanctum.py`._"
        ]
    lines += [
        "",
        "## Learned",
        "",
        "_Capabilities the owner taught Mac. Prompts live in `capabilities/`; rows "
        "here appear on Mac's menu._",
        "",
        "| Code | Name | Description | Source | Added |",
        "|------|------|-------------|--------|-------|",
        "",
        "## How to Add a Capability",
        "",
        'Tell Mac "I want you to be able to do X" and you build it together. Mac '
        "loads `references/capability-authoring.md` (and holds the prompt-quality "
        "canon while authoring), saves the prompt to `capabilities/`, and registers "
        "it here.",
        "",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# access-boundaries.md (the loaded-first Dominion contract)
# ---------------------------------------------------------------------------

ACCESS_BOUNDARIES_TEMPLATE = "ACCESS-BOUNDARIES-template.md"


def render_access_boundaries(assets_dir: Path, variables: dict) -> str | None:
    """The access-boundaries.md body from its template, or None if it is missing."""
    template_path = assets_dir / ACCESS_BOUNDARIES_TEMPLATE
    if not template_path.exists():
        return None
    return substitute_vars(template_path.read_text(encoding="utf-8"), variables)


def write_access_boundaries(out_dir: Path, assets_dir: Path, variables: dict) -> str | None:
    """Write access-boundaries.md from the template. Returns the name, or None.

    The caller decides whether to call this: a preserved bespoke file must not
    be passed through here.
    """
    body = render_access_boundaries(assets_dir, variables)
    if body is None:
        return None
    (out_dir / "access-boundaries.md").write_text(body, encoding="utf-8")
    return "access-boundaries.md"


# ---------------------------------------------------------------------------
# Creed sharding
# ---------------------------------------------------------------------------

SECTION_SPLIT_RE = re.compile(r"(?m)^(?=##\s)")

# Source creed "## " headings -> shard destinations (prefix match).
SHARD_ROUTING = {
    "creed-workshop-capture.md": ["Workshop Capture Discipline"],
    "creed-disciplines.md": [
        "Research Discipline",
        "Thematic Discipline",
        "Catalog Verification Discipline",
        "Document State Marker Discipline",
        "Hedge Preservation Discipline",
        "Pre-Presentation Review",
        "Milestone Auto-Save",
    ],
    "creed-package-assembly.md": ["Package Assembly Rule"],
}
# Headings the CREED core template already carries; they are not sharded.
CORE_HEADINGS = ("Mission", "Principles")


def _heading_of(section: str) -> str:
    return section.splitlines()[0].strip() if section.strip() else ""


def unrouted_headings(creed_text: str) -> list[str]:
    """Source creed headings that no shard takes and the core does not carry."""
    out: list[str] = []
    for section in SECTION_SPLIT_RE.split(creed_text):
        if not section.strip().startswith("##"):
            continue
        body = _heading_of(section).lstrip("#").strip()
        if any(body.startswith(p) for prefixes in SHARD_ROUTING.values() for p in prefixes):
            continue
        if any(body.startswith(c) for c in CORE_HEADINGS):
            continue
        out.append(body)
    return out


def shard_creed(creed_text: str) -> dict[str, str]:
    """Slice the source creed into shard files by heading prefix.

    Returns {shard_filename: content}, plus a `creed-incident-log.md` that
    gathers the "Recurring failure pattern" narratives. A heading that no shard
    takes (and that the core does not carry) raises a UserWarning, so a new
    discipline added to creed.md cannot silently miss a freshly born sanctum.
    """
    for heading in unrouted_headings(creed_text):
        warnings.warn(
            f"creed.md heading not routed to any shard: '{heading}'. "
            "Add it to SHARD_ROUTING in _sanctum_seed.py.",
            UserWarning,
            stacklevel=2,
        )

    sections = [p for p in SECTION_SPLIT_RE.split(creed_text) if p.strip().startswith("##")]
    shard_content: dict[str, list[str]] = {name: [] for name in SHARD_ROUTING}
    incident_sections: list[str] = []

    for section in sections:
        heading_body = _heading_of(section).lstrip("#").strip()
        routed = False
        for shard_name, prefixes in SHARD_ROUTING.items():
            if any(heading_body.startswith(p) for p in prefixes):
                shard_content[shard_name].append(section.rstrip() + "\n")
                routed = True
                break
        if not routed:
            continue
        if "Recurring failure pattern" in section or "instance" in heading_body.lower():
            incident_sections.append(section.rstrip() + "\n")

    out: dict[str, str] = {}
    for shard_name, secs in shard_content.items():
        if not secs:
            continue
        title = shard_name.replace("creed-", "").replace(".md", "").replace("-", " ").title()
        header = (
            f"# Mac — Creed Shard: {title}\n\n"
            "> Loaded on demand. Lifted verbatim from the skill creed. The "
            "always-loaded CORE (Mission, Three Laws, Sacred Truth, Package "
            "Assembly core) lives in `CREED.md`.\n"
        )
        out[shard_name] = header + "\n" + "\n".join(secs).rstrip() + "\n"

    incident_body = "\n".join(incident_sections).rstrip() if incident_sections else (
        "_No verbose incident narratives extracted._"
    )
    out["creed-incident-log.md"] = (
        "# Mac — Creed Incident Log\n\n"
        "> Not loaded on waking. Verbose narratives behind the documented "
        "discipline-failure incidents — the 'why' archive. The rules themselves "
        "live in the creed shards; this is reference only.\n\n"
        + incident_body
        + "\n"
    )
    return out


def write_creed_shards(out_dir: Path, references_dir: Path, only_missing: bool = False) -> list[str]:
    """Seed the creed shards + incident log from references/creed.md.

    Returns the names written. With `only_missing`, existing shards are left
    alone (they may hold learnings the source creed does not).
    """
    creed_src = references_dir / "creed.md"
    if not creed_src.exists():
        return []
    written: list[str] = []
    for shard_name, shard_text in shard_creed(creed_src.read_text(encoding="utf-8")).items():
        target = out_dir / shard_name
        if only_missing and target.exists():
            continue
        target.write_text(shard_text, encoding="utf-8")
        written.append(shard_name)
    return written


# ---------------------------------------------------------------------------
# v7: disciplines and incidents as one file each, Dominion inside CREED.md
# ---------------------------------------------------------------------------

# Whole-shard headings that keep a fixed file name (the rest slug their heading).
FIXED_DISCIPLINE_FILES = {
    "Workshop Capture Discipline": "workshop-capture.md",
    "Package Assembly Rule": "package-assembly.md",
}


def _slug(text: str, limit: int = 60) -> str:
    text = re.sub(r"[`*_\[\]()\"'’“”]", "", text.lower())
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if len(text) > limit:
        text = text[:limit].rsplit("-", 1)[0]
    return text or "untitled"


# A v2 MEMORY.md section (lower-cased heading prefix) -> its v7 standing file.
# The converter and First Breath (which seeds from assets/MEMORY-template.md) share it.
MEMORY_SECTION_FILES = {
    "current work": "memory/work/current.md",
    "user preferences": "memory/owner/preferences.md",
    "downloads": "memory/work/downloads.md",
    "default exclusions": "memory/work/default-exclusions.md",
    "active band profiles": "memory/bands/active.md",
    "recently published": "memory/catalog/recently-published.md",
    "catalog status": "memory/catalog/status.md",
    "module state": "memory/module/state.md",
    "pending / parked work": "memory/work/parked.md",
    "pulse report": "memory/pending.md",
    "session history": "memory/work/session-history.md",
}


def split_sections(text: str, level: int = 2) -> tuple[str, list[tuple[str, str]]]:
    """(preamble, [(heading, body)]) split on headings of `level`; code fences respected."""
    marker = "#" * level + " "
    preamble: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith(marker):
            sections.append((line[len(marker):].strip(), []))
            continue
        (sections[-1][1] if sections else preamble).append(line)
    return "\n".join(preamble).strip(), [(h, "\n".join(b).strip()) for h, b in sections]


def memory_section_file(heading: str) -> str:
    """The standing file for a MEMORY.md section; unknown ones go to memory/misc/."""
    key = next((k for k in MEMORY_SECTION_FILES if heading.lower().startswith(k)), None)
    return MEMORY_SECTION_FILES[key] if key else f"memory/misc/{_slug(heading)}.md"


def discipline_file(heading: str) -> str:
    """memory/disciplines/<file> for a creed heading (the converter uses the same names)."""
    for prefix, name in FIXED_DISCIPLINE_FILES.items():
        if heading.startswith(prefix):
            return name
    return _slug(heading.split("—")[0]) + ".md"


def discipline_files(creed_text: str) -> dict[str, str]:
    """{sanctum-relative path: content} for every routed creed section.

    Each routed section becomes memory/disciplines/<file>; a section carrying a
    "Recurring failure pattern" narrative also seeds memory/incidents/<slug>.md.
    Unrouted headings warn, as shard_creed does.
    """
    for heading in unrouted_headings(creed_text):
        warnings.warn(
            f"creed.md heading not routed to any shard: '{heading}'. "
            "Add it to SHARD_ROUTING in _sanctum_seed.py.",
            UserWarning,
            stacklevel=2,
        )
    out: dict[str, str] = {}
    for section in SECTION_SPLIT_RE.split(creed_text):
        if not section.strip().startswith("##"):
            continue
        heading = _heading_of(section).lstrip("#").strip()
        if not any(heading.startswith(p) for prefixes in SHARD_ROUTING.values() for p in prefixes):
            continue
        body = section.split("\n", 1)[1].strip() if "\n" in section else ""
        name = discipline_file(heading)
        out[f"memory/disciplines/{name}"] = f"# {heading}\n\n{body}\n"
        if "Recurring failure pattern" in section:
            out[f"memory/incidents/{name}"] = f"# {heading}\n\n{body}\n"
    return out


def write_disciplines(sanctum: Path, references_dir: Path, only_missing: bool = False) -> list[str]:
    """Seed memory/disciplines/ and memory/incidents/ from references/creed.md.

    With `only_missing`, existing files are left alone: they may hold learnings
    the source creed does not.
    """
    creed_src = references_dir / "creed.md"
    if not creed_src.exists():
        return []
    written: list[str] = []
    for rel, text in discipline_files(creed_src.read_text(encoding="utf-8")).items():
        target = sanctum / rel
        if only_missing and target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        written.append(rel)
    return written


def render_dominion(assets_dir: Path, variables: dict) -> str:
    """The Dominion section body for CREED.md: the access-boundaries template's sections."""
    body = render_access_boundaries(assets_dir, variables)
    if body is None:
        return "_The access-boundaries template is missing; reinstall the skill._"
    parts = [p for p in SECTION_SPLIT_RE.split(body) if p.strip().startswith("##")]
    return "\n\n".join("#" + p.strip() for p in parts)


# ---------------------------------------------------------------------------
# Recovery CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Re-seed Mac's disciplines and incident files (memory/disciplines/, "
            "memory/incidents/) into a sanctum. Writes only missing files unless --force is given."
        )
    )
    parser.add_argument("--out", required=True, help="Target sanctum directory (or a test dir).")
    parser.add_argument(
        "--skill-path",
        default=None,
        help="Skill dir (references/). Default: this script's parent dir.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files too. Without it, existing files are skipped.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    if not out_dir.is_dir():
        print(f"ERROR: --out dir not found: {out_dir}", file=sys.stderr)
        return 2
    skill_path = Path(args.skill_path).resolve() if args.skill_path else Path(__file__).resolve().parent.parent
    references_dir = skill_path / "references"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        planned = list(discipline_files((references_dir / "creed.md").read_text(encoding="utf-8"))) if (
            references_dir / "creed.md"
        ).exists() else []
        written = write_disciplines(out_dir, references_dir, only_missing=not args.force)
    skipped = [n for n in planned if n not in written]

    result = {
        "status": "seeded",
        "out_dir": str(out_dir),
        "written": written,
        "skipped_existing": skipped,
        "warnings": sorted({str(w.message) for w in caught}),
    }
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Seeded {len(written)} file(s) into {out_dir}:")
        for name in written:
            print(f"  + {name}")
        for name in skipped:
            print(f"  = {name} (exists; use --force to overwrite)")
        for message in result["warnings"]:
            print(f"  ! {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
