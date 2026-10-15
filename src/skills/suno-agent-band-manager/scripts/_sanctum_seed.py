#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Shared sanctum logic for Mac (suno-agent-band-manager).

One home for everything the waking, birth, migration and upgrade scripts must
agree on:

  - the always-loaded spine (SANCTUM_LOAD_ORDER) and sanctum classification
    (absent / v1 / v2 / damaged), matched case-sensitively
  - config resolution (BMad v7 `modules.suno` answers; the owner from BOND.md)
  - the menu roster (assets/menu.csv) that drives Mac's menu and CAPABILITIES.md
  - the loaded-first Dominion contract `access-boundaries.md`
  - the on-demand creed shards sliced from `references/creed.md`

Imported by pre-activate.py, init-sanctum.py, migrate-sidecar-to-v2.py and
upgrade-sanctum.py. As a CLI it is the recovery path: re-seed a missing
access-boundaries.md or creed shard into an existing sanctum. It writes only
files that are missing unless `--force` is given, so shards that have grown new
learnings are never overwritten by accident.

Usage:
    _sanctum_seed.py --out DIR [--skill-path DIR] [--project-root DIR] [--force]
    _sanctum_seed.py --help
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import warnings
from pathlib import Path

# ---------------------------------------------------------------------------
# The sanctum spine and its classification
# ---------------------------------------------------------------------------

# Preserved divergence: double-underscore parent, fixed dir name. Portable sync
# and the reconcile tooling depend on this path.
SANCTUM_REL = ("_bmad", "_memory", "band-manager-sidecar")

# The always-loaded set, in load order. This list is the single home of the
# load order: docs point here (via pre-activate's output) instead of copying it.
SANCTUM_LOAD_ORDER = [
    "access-boundaries.md",  # Dominion contract: loads first, governs later writes
    "INDEX.md",              # thin map of the sanctum
    "MEMORY.md",             # curated long-term memory (carries derived sections)
    "CREED.md",              # creed core (Package Assembly Rule core)
    "PERSONA.md",            # Mac's living self
    "BOND.md",               # thin owner-model orienting file
    "CAPABILITIES.md",       # built-in + learned capability roster
]

# The Pulse wake loads only what maintenance needs: the contract, the creed
# (Three Laws), the persona, and the routine itself.
PULSE_LOAD_ORDER = ["access-boundaries.md", "CREED.md", "PERSONA.md", "PULSE.md"]

V1_MARKER = "index.md"
# v1 stores already carried access-boundaries.md, so it is not a v2 marker.
V2_MARKERS = [n for n in SANCTUM_LOAD_ORDER if n != "access-boundaries.md"]


def sanctum_dir(project_root: Path, override: str | None = None) -> Path:
    return Path(override) if override else project_root.joinpath(*SANCTUM_REL)


def classify_sanctum(sanctum: Path) -> dict:
    """Classify a sanctum dir. Names are compared exactly (case-sensitive).

    - absent  : no directory -> First Breath
    - v1      : `index.md` content store and no v2 spine file -> migrate
    - v2      : every file of the spine present -> wake normally
    - damaged : anything else, including a partial v2 spine -> recovery route

    `os.listdir` returns the real directory entries, so on case-insensitive
    filesystems (macOS APFS, Windows NTFS) a v1 `index.md` is never mistaken
    for the v2 `INDEX.md`.
    """
    if not sanctum.exists():
        return {"sidecar_format": "absent", "needs_migration": False, "missing_spine": []}
    if not sanctum.is_dir():
        return {
            "sidecar_format": "damaged",
            "needs_migration": False,
            "missing_spine": list(SANCTUM_LOAD_ORDER),
        }
    names = set(os.listdir(sanctum))
    missing = [n for n in SANCTUM_LOAD_ORDER if n not in names]
    has_v2 = any(n in names for n in V2_MARKERS)
    if not has_v2 and V1_MARKER in names:
        return {"sidecar_format": "v1", "needs_migration": True, "missing_spine": missing}
    if not missing:
        return {"sidecar_format": "v2", "needs_migration": False, "missing_spine": []}
    return {"sidecar_format": "damaged", "needs_migration": False, "missing_spine": missing}


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
    "band_profiles_folder": "docs/band-profiles",
    "songbook_folder": "docs/songbook",
    "pytorch_audio_tools": "off",
}
VOICE_GLOB = "voice-context-*.md"


def _load_toml_layers(bmad: Path) -> dict:
    """Merge BMad's four central TOML layers (tables deep-merge, scalars override)."""
    try:
        import tomllib
    except ModuleNotFoundError:  # Python < 3.11
        return {}

    def merge(base: dict, over: dict) -> dict:
        out = dict(base)
        for key, value in over.items():
            if isinstance(value, dict) and isinstance(out.get(key), dict):
                out[key] = merge(out[key], value)
            else:
                out[key] = value
        return out

    merged: dict = {}
    for rel in ("config.toml", "config.user.toml", "custom/config.toml", "custom/config.user.toml"):
        path = bmad / rel
        if path.is_file():
            try:
                merged = merge(merged, tomllib.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                continue
    return merged


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
            if "{" not in value:  # an unfilled template token is not a name
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

    Module answers and output_folder come from BMad's TOML layers; the owner's
    name and language from the sanctum's BOND.md, then a lone voice file, then
    defaults (greet generically, English).
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

    toml = _load_toml_layers(project_root / "_bmad")
    if toml:
        fill(toml.get("core") or {}, CORE_KEYS, "config.toml")
        fill((toml.get("modules") or {}).get("suno") or {}, SUNO_KEYS, "config.toml")

    fill(owner_from_bond(sanctum), OWNER_KEYS, "BOND.md")
    voice_name = owner_from_voice_file(project_root)
    if voice_name:
        fill({"user_name": voice_name}, ("user_name",), "voice file")
    if values.get("communication_language"):
        values.setdefault("document_output_language", values["communication_language"])

    warnings_out: list[str] = []
    for key, default in CONFIG_DEFAULTS.items():
        if values.get(key) in (None, ""):
            values[key] = default
    for key in ("band_profiles_folder", "songbook_folder"):
        values[key] = values[key].replace("{project-root}/", "")
    if not values.get("user_name"):
        warnings_out.append(
            "user_name not found (no BOND.md name, no single voice file); greet generically "
            "and ask what to call the owner."
        )
    if not toml.get("modules", {}).get("suno"):
        warnings_out.append(
            "No suno answers in BMad's config: the module defaults apply. "
            "`bmad setup suno` asks the questions."
        )
    return {"values": values, "sources": sources or ["defaults"], "warnings": warnings_out}


def normalize_username(name: str) -> str:
    """Lowercase, spaces to hyphens (the voice-file naming rule)."""
    return name.strip().lower().replace(" ", "-")


def template_variables(project_root: Path, config: dict | None = None, birth_date: str | None = None) -> dict:
    """The substitution map for sanctum templates."""
    from datetime import date

    values = (config or resolve_config(project_root))["values"]
    user = values.get("user_name") or "friend"
    root = str(project_root)
    return {
        "user_name": user,
        "user_slug": normalize_username(user),
        "communication_language": values.get("communication_language") or "English",
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
            "`uv run scripts/upgrade-sanctum.py`._"
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
# Recovery CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Re-seed Mac's access-boundaries.md and creed shards into a sanctum "
            "directory. Writes only missing files unless --force is given."
        )
    )
    parser.add_argument("--out", required=True, help="Target sanctum directory (or a test dir).")
    parser.add_argument(
        "--skill-path",
        default=None,
        help="Skill dir (assets/ + references/). Default: this script's parent dir.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root, substituted for {project-root} placeholders.",
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
    project_root = Path(args.project_root).resolve()
    variables = template_variables(project_root)

    written: list[str] = []
    skipped: list[str] = []
    if args.force or not (out_dir / "access-boundaries.md").exists():
        name = write_access_boundaries(out_dir, skill_path / "assets", variables)
        if name:
            written.append(name)
    else:
        skipped.append("access-boundaries.md")

    references_dir = skill_path / "references"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        shard_names = list(shard_creed((references_dir / "creed.md").read_text(encoding="utf-8")).keys()) if (
            references_dir / "creed.md"
        ).exists() else []
        written.extend(write_creed_shards(out_dir, references_dir, only_missing=not args.force))
    skipped.extend(n for n in shard_names if n not in written)

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
