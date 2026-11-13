#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""First Breath — deterministic v7 sanctum scaffolding for Mac.

Creates the BMad v7 memory-agent sanctum at
    {project-root}/_bmad/memory/suno-agent-band-manager/
with the identity files from the templates (PERSONA, CREED with the Dominion
folded in, BOND, HOW-I-REMEMBER, PULSE), CAPABILITIES.md from assets/menu.csv
(the same source as the menu), the standing files seeded from the sections of
MEMORY-template.md, the disciplines and incidents sliced from the skill's
authored creed (`_sanctum_seed.CREED_SOURCE_REL`), and the empty
memory/<kind>/, raw/ and capabilities/ folders.

It runs BEFORE the conversational awakening and only scaffolds a FRESH
sanctum. It never writes into an existing one, and it refuses while an old
store sits at `_bmad/_memory/band-manager-sidecar/` (that store converts with
migrate_sanctum_to_v7.py instead).

Usage:
    init_sanctum.py <project-root> <skill-path> [--sanctum-dir DIR] [--format json]
    init_sanctum.py --help

    project-root: The root of the project (where _bmad/ lives)
    skill-path:   Path to the skill directory (where SKILL.md, assets/ live)
    --sanctum-dir: Scaffold into DIR instead of the project's sanctum (staging, tests)

Result `status` and exit code:
    created     the sanctum was scaffolded                                  (0)
    exists      a complete sanctum is already there; nothing written         (0)
    incomplete  a sanctum is there but identity files are missing (`missing`);
                nothing written: upgrade_sanctum.py --apply safe restores them (1)
    refused     an old store is at the legacy path (`legacy_store`); convert it (1)
    error       the skill lacks a template or the creed source (`missing`), or
                a write failed; nothing usable was scaffolded                (1)
Bad arguments exit 2.

Example:
    uv run {skill-root}/scripts/init_sanctum.py /path/to/project /path/to/suno-agent-band-manager
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import date
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

# Templates -> identity files at the sanctum root. MEMORY-template.md is not
# copied whole: its sections seed the standing files under memory/.
TEMPLATE_FILES = [
    "PERSONA-template.md",
    "CREED-template.md",
    "BOND-template.md",
    "HOW-I-REMEMBER-template.md",
    "PULSE-template.md",
]
MEMORY_TEMPLATE = "MEMORY-template.md"


def builtin_roster(project_root: Path, skill_path: Path) -> list[dict]:
    """Mac's built-in capabilities, from the assets/menu.csv that drives the menu."""
    csv_path = _seed.find_menu_csv(skill_path)
    if csv_path is None:
        return []
    return _seed.menu_rows(csv_path)


def missing_sources(skill_path: Path) -> list[str]:
    """Skill files the scaffold reads that are not there (skill-relative names)."""
    assets_dir = skill_path / "assets"
    names = [*TEMPLATE_FILES, MEMORY_TEMPLATE, _seed.ACCESS_BOUNDARIES_TEMPLATE]
    missing = [f"assets/{name}" for name in names if not (assets_dir / name).is_file()]
    if not _seed.creed_source(skill_path).is_file():
        missing.append(_seed.CREED_SOURCE_LABEL)
    return missing


def scaffold(project_root: Path, skill_path: Path, sanctum_dir: str | None = None) -> dict:
    """Create the v7 sanctum. Returns a result dict (CLI-friendly)."""
    sanctum_path = _seed.sanctum_dir(project_root, sanctum_dir)
    assets_dir = skill_path / "assets"

    existing = _seed.classify_sanctum(sanctum_path)
    if existing["sidecar_format"] == "v7":
        return {
            "status": "exists",
            "sanctum_path": str(sanctum_path),
            "message": (
                f"Sanctum already exists at {sanctum_path}. This agent has "
                "already been born — skipping First Breath scaffolding."
            ),
            "created": [],
        }
    if existing["sidecar_format"] in ("v1", "v2"):
        return {
            "status": "refused",
            "sanctum_path": str(sanctum_path),
            "legacy_store": str(sanctum_path),
            "legacy_format": existing["sidecar_format"],
            "message": (
                f"{sanctum_path} holds an old memory store ({existing['sidecar_format']}); nothing was "
                "scaffolded. Convert it (migrate_sidecar_to_v2.py --in-place for v1, then migrate_sanctum_to_v7.py)."
            ),
            "created": [],
        }
    if existing["sidecar_format"] != "absent":
        return {
            "status": "incomplete",
            "sanctum_path": str(sanctum_path),
            "missing": existing["missing_spine"],
            "message": (
                f"A sanctum exists at {sanctum_path} but is incomplete (missing: "
                f"{', '.join(existing['missing_spine']) or 'nothing recognised'}). init_sanctum.py never "
                "writes into an existing sanctum; `uv run {skill-root}/scripts/upgrade_sanctum.py "
                "--project-root <project-root> --apply safe` restores missing files from the templates."
            ),
            "created": [],
        }
    if sanctum_dir is None:
        legacy = _seed.locate_sanctum(project_root)[1]
        if legacy.get("legacy_store"):
            return {
                "status": "refused",
                "sanctum_path": str(sanctum_path),
                "legacy_store": legacy["legacy_store"],
                "legacy_format": legacy["legacy_format"],
                "message": (
                    f"An old memory store ({legacy['legacy_format']}) is at {legacy['legacy_store']}. "
                    "A fresh sanctum would hide it from every later wake, so nothing was scaffolded. "
                    "Convert it (migrate_sidecar_to_v2.py --in-place for v1, then migrate_sanctum_to_v7.py); "
                    "a damaged one needs its missing files restored first."
                ),
                "created": [],
            }
    missing = missing_sources(skill_path)
    if missing:
        return {
            "status": "error",
            "sanctum_path": str(sanctum_path),
            "missing": missing,
            "message": (
                f"The skill at {skill_path} lacks {', '.join(missing)}; nothing was scaffolded. "
                "Reinstall the suno-agent-band-manager skill."
            ),
            "created": [],
        }

    variables = _seed.template_variables(project_root)
    variables["dominion"] = _seed.render_dominion(assets_dir, variables)
    created: list[str] = []

    for folder in ("raw", "capabilities", *(f"memory/{kind}" for kind in _seed.MEMORY_KINDS)):
        (sanctum_path / folder).mkdir(parents=True, exist_ok=True)
        created.append(folder + "/")

    # Templates -> identity files.
    for template_name in TEMPLATE_FILES:
        template_path = assets_dir / template_name
        output_name = template_name.replace("-template.md", ".md")
        content = _seed.substitute_vars(template_path.read_text(encoding="utf-8"), variables)
        (sanctum_path / output_name).write_text(content, encoding="utf-8")
        created.append(output_name)

    # The standing files, seeded from the sections of MEMORY-template.md.
    memory_template = assets_dir / MEMORY_TEMPLATE
    text = _seed.substitute_vars(memory_template.read_text(encoding="utf-8"), variables)
    _, sections = _seed.split_sections(text)
    for heading, body in sections:
        rel = _seed.memory_section_file(heading)
        if rel == "memory/pending.md" or not body:
            continue
        (sanctum_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (sanctum_path / rel).write_text(f"# {heading}\n\n{body}\n", encoding="utf-8")
        created.append(rel)

    # Disciplines and incidents, sliced from the skill's authored creed.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        created.extend(_seed.write_disciplines(sanctum_path, skill_path))
    seed_warnings = sorted({str(w.message) for w in caught})

    # CAPABILITIES.md — the built-in roster from assets/menu.csv (the menu's
    # own source), plus an empty Learned table.
    capabilities = builtin_roster(project_root, skill_path)
    (sanctum_path / "CAPABILITIES.md").write_text(
        _seed.generate_capabilities_md(capabilities), encoding="utf-8"
    )
    created.append("CAPABILITIES.md")

    # The shipped text this sanctum took, so upgrade_sanctum.py can tell an
    # untouched older template from the owner's own text.
    created.append(_seed.record_seeded_base(sanctum_path, date.today().isoformat()))

    return {
        "status": "created",
        "sanctum_path": str(sanctum_path),
        "message": (
            f"First Breath scaffolding complete. Sanctum: {sanctum_path}. "
            f"{len(capabilities)} built-in capabilities discovered."
        ),
        "created": created,
        "warnings": seed_warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a fresh v7 sanctum for Mac (suno-agent-band-manager)."
    )
    parser.add_argument("project_root", help="Project root (where _bmad/ lives)")
    parser.add_argument("skill_path", help="Path to the skill directory (assets/ live here)")
    parser.add_argument(
        "--sanctum-dir", default=None,
        help="Scaffold into this directory instead of the project's sanctum (staging copies, tests).",
    )
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format."
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    skill_path = Path(args.skill_path).resolve()

    if not project_root.is_dir():
        print(f"ERROR: project root not found: {project_root}", file=sys.stderr)
        return 2
    if not skill_path.is_dir():
        print(f"ERROR: skill path not found: {skill_path}", file=sys.stderr)
        return 2

    try:
        result = scaffold(project_root, skill_path, args.sanctum_dir)
    except (OSError, UnicodeDecodeError) as exc:
        # A write or read failed part-way: say so, never a traceback. What was
        # written stays for the wake to report as an incomplete sanctum.
        result = {
            "status": "error",
            "sanctum_path": str(_seed.sanctum_dir(project_root, args.sanctum_dir)),
            "message": f"Scaffolding failed: {exc}",
            "created": [],
        }
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(result["message"])
        for name in result["created"]:
            print(f"  + {name}")
    return 0 if result["status"] in ("created", "exists") else 1


if __name__ == "__main__":
    sys.exit(main())
