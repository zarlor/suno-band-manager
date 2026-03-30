#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Pre-activation script for Band Manager agent.

Checks first-run status, scaffolds sidecar directory if needed, and
renders the capability menu from module-help.csv.

Usage:
    python3 scripts/pre-activate.py <project-root> [--scaffold] [-o OUTPUT]
    python3 scripts/pre-activate.py --help

Arguments:
    project-root    Project root directory path

Options:
    --scaffold      Create sidecar directory and static files if missing
    -o, --output    Write JSON output to file instead of stdout
"""

import argparse
import csv
import json
import sys
from io import StringIO
from pathlib import Path

AGENT_SKILL_NAME = "bmad-suno-agent-band-manager"
SETUP_SKILL_NAME = "bmad-suno-setup"
MODULE_CODE = "BMad Suno Band Manager"


def check_first_run(project_root: Path) -> bool:
    """Check if sidecar memory directory exists."""
    sidecar = project_root / "_bmad" / "_memory" / "band-manager-sidecar"
    return not sidecar.exists()


def scaffold_sidecar(project_root: Path) -> dict:
    """Create sidecar directory and static files."""
    sidecar = project_root / "_bmad" / "_memory" / "band-manager-sidecar"
    sidecar.mkdir(parents=True, exist_ok=True)

    created = []

    # access-boundaries.md - static template
    ab_path = sidecar / "access-boundaries.md"
    if not ab_path.exists():
        ab_path.write_text(
            "# Access Boundaries for Mac\n\n"
            "## Read Access\n"
            "- docs/band-profiles/\n"
            "- {project-root}/_bmad/_memory/band-manager-sidecar/\n\n"
            "## Write Access\n"
            "- {project-root}/_bmad/_memory/band-manager-sidecar/\n\n"
            "## Deny Zones\n"
            "- All other directories\n"
        )
        created.append("access-boundaries.md")

    # patterns.md - empty
    pat_path = sidecar / "patterns.md"
    if not pat_path.exists():
        pat_path.write_text("# Musical Patterns\n\nLearned preferences will appear here over time.\n")
        created.append("patterns.md")

    # chronology.md - empty
    chron_path = sidecar / "chronology.md"
    if not chron_path.exists():
        chron_path.write_text("# Session Chronology\n\nSession summaries will appear here.\n")
        created.append("chronology.md")

    return {"scaffolded": True, "files_created": created, "sidecar_path": str(sidecar)}


def find_module_csv(project_root: Path, skill_dir: Path) -> Path | None:
    """Find module-help.csv — installed location first, then setup skill assets."""
    # Installed location
    installed = project_root / "_bmad" / "module-help.csv"
    if installed.is_file():
        return installed

    # Setup skill assets (sibling directory)
    skills_dir = skill_dir.parent
    setup_csv = skills_dir / SETUP_SKILL_NAME / "assets" / "module-help.csv"
    if setup_csv.is_file():
        return setup_csv

    return None


def parse_csv(csv_path: Path) -> list[dict]:
    """Parse module-help.csv and return rows for this module (excluding setup)."""
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            # Skip the setup skill's own entry
            if row.get("skill", "").strip() == SETUP_SKILL_NAME:
                continue
            rows.append(row)
    return rows


def render_menu(csv_path: Path) -> str:
    """Render capability menu from module-help.csv."""
    rows = parse_csv(csv_path)

    lines = ["What would you like to do today?\n"]
    for i, row in enumerate(rows, 1):
        code = row.get("menu-code", "??").strip()
        display = row.get("display-name", "").strip()
        desc = row.get("description", "No description").strip()
        lines.append(f"{i}. [{code}] {display} — {desc}")

    return "\n".join(lines)


def build_routing_table(csv_path: Path) -> dict:
    """Build menu-code to capability routing table."""
    rows = parse_csv(csv_path)

    table = {}
    for i, row in enumerate(rows, 1):
        code = row.get("menu-code", "").strip()
        skill = row.get("skill", "").strip()
        action = row.get("action", "").strip()

        entry = {"name": action}
        if skill == AGENT_SKILL_NAME:
            # Agent's own capabilities — load reference prompt
            entry["type"] = "prompt"
            entry["target"] = f"./references/{action}.md"
        else:
            # External skill capabilities
            entry["type"] = "skill"
            entry["target"] = skill

        table[code] = entry
        table[str(i)] = entry

    return table


def main():
    parser = argparse.ArgumentParser(description="Band Manager pre-activation checks")
    parser.add_argument("project_root", help="Project root directory")
    parser.add_argument("--scaffold", action="store_true", help="Create sidecar if missing")
    parser.add_argument("-o", "--output", help="Output file path")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    skill_dir = Path(__file__).parent.parent

    csv_path = find_module_csv(project_root, skill_dir)
    if csv_path is None:
        print(json.dumps({
            "error": True,
            "message": "module-help.csv not found. Run the setup skill first.",
        }))
        sys.exit(1)

    result = {
        "first_run": check_first_run(project_root),
        "menu": render_menu(csv_path),
        "routing_table": build_routing_table(csv_path),
    }

    if args.scaffold and result["first_run"]:
        result["scaffold"] = scaffold_sidecar(project_root)

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
    sys.exit(0)
