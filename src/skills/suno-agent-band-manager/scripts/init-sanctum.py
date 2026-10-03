#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""First Breath — deterministic v2 sanctum scaffolding for Mac.

Adapted from the bmad-agent-builder sample-init-sanctum.py for the
suno-agent-band-manager skill ("Mac"). Two deliberate divergences from the v2
default are preserved here on purpose:

  1. SANCTUM LOCATION: the sanctum lives at
         {project-root}/_bmad/_memory/band-manager-sidecar/
     NOT {project-root}/_bmad/memory/{skill-name}/. The double-underscore path
     is load-bearing — portable sync + the reconcile tooling depend on it. Do
     not "fix" it to the v2 default.

  2. PRESERVED BESPOKE FILES: Mac's sanctum keeps its own superior machinery
         access-boundaries.md  (Dominion contract; loads first)
         patterns.md, chronology.md  (organic learned-knowledge / timeline)
         sessions/  (raw per-date session logs, two-tier memory)
         _collection_*.txt  (working catalog exports)
     This script only scaffolds a FRESH sanctum. For an existing sidecar, use
     migrate-sidecar-to-v2.py instead.

This script runs BEFORE the conversational awakening. It creates the sanctum
folder structure, copies template files with config values substituted, and
generates CAPABILITIES.md from module-help.csv (the same source as the menu).

Usage:
    init-sanctum.py <project-root> <skill-path>
    init-sanctum.py --help

    project-root: The root of the project (where _bmad/ lives)
    skill-path:   Path to the skill directory (where SKILL.md, assets/ live)

Example:
    uv run scripts/init-sanctum.py /path/to/project /path/to/suno-agent-band-manager
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
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

SKILL_NAME = "suno-agent-band-manager"
# Preserved divergence: bespoke sanctum location (double underscore + fixed name).
SANCTUM_PARENT = "_memory"
SANCTUM_DIR = "band-manager-sidecar"

TEMPLATE_FILES = [
    "INDEX-template.md",
    "PERSONA-template.md",
    "CREED-template.md",
    "BOND-template.md",
    "MEMORY-template.md",
    "PULSE-template.md",
]


def builtin_roster(project_root: Path, skill_path: Path) -> list[dict]:
    """Mac's built-in capabilities, from the module-help.csv that drives the menu."""
    csv_path = _seed.find_module_csv(project_root, skill_path)
    if csv_path is None:
        return []
    return _seed.menu_rows(csv_path, [_seed.MODULE_CODE])


def scaffold(project_root: Path, skill_path: Path) -> dict:
    """Create the sanctum. Returns a result dict (CLI-friendly)."""
    bmad_dir = project_root / "_bmad"
    sanctum_path = bmad_dir / SANCTUM_PARENT / SANCTUM_DIR
    assets_dir = skill_path / "assets"
    references_dir = skill_path / "references"

    if sanctum_path.exists():
        return {
            "status": "exists",
            "sanctum_path": str(sanctum_path),
            "message": (
                f"Sanctum already exists at {sanctum_path}. This agent has "
                "already been born — skipping First Breath scaffolding. For an "
                "existing sidecar, use migrate-sidecar-to-v2.py."
            ),
            "created": [],
        }

    # Config-driven substitution map (same resolver pre-activate uses).
    variables = _seed.template_variables(project_root)

    created: list[str] = []

    # Sanctum structure + the bespoke raw layers.
    sanctum_path.mkdir(parents=True, exist_ok=True)
    (sanctum_path / "capabilities").mkdir(exist_ok=True)
    (sanctum_path / "sessions").mkdir(exist_ok=True)
    created.append("capabilities/")
    created.append("sessions/")

    # Templates → ALLCAPS sanctum files.
    for template_name in TEMPLATE_FILES:
        template_path = assets_dir / template_name
        if not template_path.exists():
            continue
        output_name = template_name.replace("-template", "").upper()
        output_name = output_name[:-3] + ".md"  # .MD -> .md
        content = _seed.substitute_vars(template_path.read_text(encoding="utf-8"), variables)
        (sanctum_path / output_name).write_text(content, encoding="utf-8")
        created.append(output_name)

    # access-boundaries.md — the Dominion contract that loads FIRST on every
    # waking. Seeded from assets/ACCESS-BOUNDARIES-template.md via the shared
    # seed module so a fresh birth and a migration converge on the same shape.
    ab_written = _seed.write_access_boundaries(sanctum_path, assets_dir, variables)
    if ab_written:
        created.append(ab_written)

    # On-demand creed shards + the non-loaded incident log — sliced from
    # references/creed.md by the SAME shard_creed() the migration tool uses.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        shards_written = _seed.write_creed_shards(sanctum_path, references_dir)
    created.extend(shards_written)
    seed_warnings = sorted({str(w.message) for w in caught})

    # CAPABILITIES.md — the built-in roster from module-help.csv (the menu's
    # own source), plus an empty Learned table.
    capabilities = builtin_roster(project_root, skill_path)
    (sanctum_path / "CAPABILITIES.md").write_text(
        _seed.generate_capabilities_md(capabilities), encoding="utf-8"
    )
    created.append("CAPABILITIES.md")

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
        description="Scaffold a fresh v2 sanctum for Mac (suno-agent-band-manager)."
    )
    parser.add_argument("project_root", help="Project root (where _bmad/ lives)")
    parser.add_argument("skill_path", help="Path to the skill directory (assets/ live here)")
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

    result = scaffold(project_root, skill_path)
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(result["message"])
        for name in result["created"]:
            print(f"  + {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
