#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
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
auto-generates CAPABILITIES.md.

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
import re
import sys
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


def parse_yaml_config(config_path: Path) -> dict:
    """Simple YAML key-value parser. Handles top-level scalar values only."""
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


def parse_frontmatter(file_path: Path) -> dict:
    """Extract YAML frontmatter (key: value lines) from a markdown file."""
    meta: dict[str, str] = {}
    content = file_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return meta
    for line in match.group(1).strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip("'\"")
    return meta


def discover_capabilities(references_dir: Path) -> list[dict]:
    """Scan references/ for capability prompt files with name+code frontmatter."""
    capabilities: list[dict] = []
    if not references_dir.is_dir():
        return capabilities
    for md_file in sorted(references_dir.glob("*.md")):
        meta = parse_frontmatter(md_file)
        if meta.get("name") and meta.get("code"):
            capabilities.append(
                {
                    "name": meta["name"],
                    "description": meta.get("description", ""),
                    "code": meta["code"],
                    "source": f"references/{md_file.name}",
                }
            )
    return capabilities


def generate_capabilities_md(capabilities: list[dict]) -> str:
    """Generate CAPABILITIES.md content.

    When no capability frontmatter is present (Mac's references use a roster in
    capabilities.md rather than per-file frontmatter), fall back to a pointer at
    that roster so the generated file is still useful.
    """
    lines = ["# Capabilities", "", "## Built-in", ""]
    if capabilities:
        lines += [
            "| Code | Name | Description | Source |",
            "|------|------|-------------|--------|",
        ]
        for cap in capabilities:
            lines.append(
                f"| [{cap['code']}] | {cap['name']} | {cap['description']} | "
                f"`{cap['source']}` |"
            )
    else:
        lines += [
            "_No capability frontmatter found in references/. Mac's capability "
            "roster (external skills, audio analysis, playlist sequencing) lives "
            "in the skill's `references/capabilities.md`. Load it for the full "
            "list._",
        ]
    lines += [
        "",
        "## Learned",
        "",
        "_Capabilities added by the owner over time. Prompts live in "
        "`capabilities/`._",
        "",
        "| Code | Name | Description | Source | Added |",
        "|------|------|-------------|--------|-------|",
        "",
        "## How to Add a Capability",
        "",
        'Tell Mac "I want you to be able to do X" and you build it together. '
        "The prompt is saved to `capabilities/` and registered here.",
        "",
    ]
    return "\n".join(lines) + "\n"


def substitute_vars(content: str, variables: dict) -> str:
    """Replace {var_name} placeholders with values from the variables dict."""
    for key, value in variables.items():
        content = content.replace(f"{{{key}}}", value)
    return content


def fresh_birth_history(content: str, birth_date: str) -> str:
    """Blank fabricated history out of a template for a FRESH birth.

    The MEMORY/PERSONA templates carry a seeded "First Breath / sanctum
    migration" / "Reborn into the v2 sanctum … memories migrated" line. That
    framing is accurate for a *migrated* sanctum, but for a *freshly born* one
    there were no prior memories to migrate — it would be fiction. Replace those
    specific seed lines with a neutral first-session marker so a fresh birth
    starts with an honest, empty history. Idempotent and order-independent: it
    only rewrites the known seed lines, leaving everything else untouched.
    """
    # MEMORY-template Session History seed line.
    content = re.sub(
        r"^- \{birth_date\}: First Breath / sanctum migration — initial setup\.$",
        f"- {birth_date}: First Breath — initial setup.",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        rf"^- {re.escape(birth_date)}: First Breath / sanctum migration — initial setup\.$",
        f"- {birth_date}: First Breath — initial setup.",
        content,
        flags=re.MULTILINE,
    )
    # PERSONA-template Evolution Log seed line (the "memories migrated" fiction).
    content = re.sub(
        r"^- \*\*\{birth_date\}\*\* — Reborn into the v2 sanctum\. .*$",
        f"- **{birth_date}** — First Breath. Mac woke into a fresh sanctum carrying "
        "the full NOLA character forward from the skill persona. No prior memories "
        "to migrate — the history starts here.",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        rf"^- \*\*{re.escape(birth_date)}\*\* — Reborn into the v2 sanctum\. .*$",
        f"- **{birth_date}** — First Breath. Mac woke into a fresh sanctum carrying "
        "the full NOLA character forward from the skill persona. No prior memories "
        "to migrate — the history starts here.",
        content,
        flags=re.MULTILINE,
    )
    return content


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

    # Config-driven substitution map.
    config: dict[str, str] = {}
    for config_file in ("config.yaml", "config.user.yaml"):
        config.update(parse_yaml_config(bmad_dir / config_file))

    variables = {
        "user_name": config.get("user_name", "friend"),
        "communication_language": config.get("communication_language", "English"),
        "birth_date": date.today().isoformat(),
        "project_root": str(project_root),
    }

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
        content = substitute_vars(template_path.read_text(encoding="utf-8"), variables)
        # A fresh birth has no prior history to migrate — strip the seeded
        # "First Breath / sanctum migration" / "memories migrated" lines so the
        # MEMORY/PERSONA history starts honestly empty.
        content = fresh_birth_history(content, variables["birth_date"])
        (sanctum_path / output_name).write_text(content, encoding="utf-8")
        created.append(output_name)

    # access-boundaries.md — the Dominion contract that loads FIRST on every
    # rebirth. Seeded from assets/ACCESS-BOUNDARIES-template.md via the shared
    # seed module so a fresh birth and a migration converge on the same shape.
    ab_written = _seed.write_access_boundaries(sanctum_path, assets_dir, variables)
    if ab_written:
        created.append(ab_written)

    # On-demand creed shards + the non-loaded incident log — sliced from
    # references/creed.md by the SAME shard_creed() the migration tool uses.
    shards_written = _seed.write_creed_shards(sanctum_path, references_dir)
    created.extend(shards_written)

    # CAPABILITIES.md (auto-generated).
    capabilities = discover_capabilities(references_dir)
    (sanctum_path / "CAPABILITIES.md").write_text(
        generate_capabilities_md(capabilities), encoding="utf-8"
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
