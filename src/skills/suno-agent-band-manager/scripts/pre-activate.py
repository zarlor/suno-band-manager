#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Pre-activation script for Band Manager agent.

Checks first-run status, scaffolds the v2 sanctum if needed (by delegating to
init-sanctum.py — NOT by writing the old inline stubs), and renders the
capability menu from module-help.csv.

Usage:
    python3 scripts/pre-activate.py <project-root> [--scaffold] [--sanctum-dir PATH] [-o OUTPUT]
    python3 scripts/pre-activate.py --help

Arguments:
    project-root    Project root directory path

Options:
    --scaffold      Scaffold the v2 sanctum (via init-sanctum.py) if missing
    --sanctum-dir   Override the sanctum directory (for first-run detection /
                    scaffolding against a staging copy). Default is the real
                    sanctum under the project root.
    -o, --output    Write JSON output to file instead of stdout
"""

import argparse
import csv
import json
import subprocess
import sys
from io import StringIO
from pathlib import Path

AGENT_SKILL_NAME = "suno-agent-band-manager"
SETUP_SKILL_NAME = "suno-setup"
MODULE_CODE = "Suno Band Manager"
VOICE_FILE_PREFIX = "voice-context-"
VOICE_FILE_SUFFIX = ".md"

# Default sanctum location (preserved bespoke divergence: double-underscore parent,
# fixed dir name). The v2 sanctum is scaffolded by init-sanctum.py.
DEFAULT_SANCTUM_REL = ("_bmad", "_memory", "band-manager-sidecar")

# Files the agent loads on every rebirth (per references/activation.md). Surfaced
# in the pre-activate output so the activation router references the new file set.
SANCTUM_LOAD_ORDER = [
    "access-boundaries.md",  # Dominion contract — loads FIRST, before any file op
    "INDEX.md",              # thin map of the sanctum
    "MEMORY.md",             # curated long-term memory (carries derived sections)
    "CREED.md",              # always-loaded creed CORE (Package Assembly Rule core)
    "PERSONA.md",            # Mac's living self
]


def resolve_sanctum_dir(project_root: Path, sanctum_dir: str | None) -> Path:
    """Resolve the sanctum directory, honoring a --sanctum-dir override."""
    if sanctum_dir:
        return Path(sanctum_dir)
    return project_root.joinpath(*DEFAULT_SANCTUM_REL)


def normalize_username(name: str) -> str:
    """Normalize a user name for use in filenames: lowercase, spaces to hyphens."""
    return name.strip().lower().replace(" ", "-")


def detect_voice_files(project_root: Path, user_name: str | None) -> dict:
    """Detect voice/context files in the docs/ directory.

    Scans for files matching voice-context-*.md and checks if one matches
    the current user_name from config.

    Returns:
        Dict with voice_files (list of relative paths), matched_file
        (relative path or None), and normalized user_name.
    """
    docs_dir = project_root / "docs"
    result: dict = {
        "voice_files": [],
        "matched_file": None,
        "expected_filename": None,
    }

    if user_name:
        normalized = normalize_username(user_name)
        result["expected_filename"] = f"{VOICE_FILE_PREFIX}{normalized}{VOICE_FILE_SUFFIX}"

    if not docs_dir.is_dir():
        return result

    for path in sorted(docs_dir.glob(f"{VOICE_FILE_PREFIX}*{VOICE_FILE_SUFFIX}")):
        rel_path = str(path.relative_to(project_root))
        result["voice_files"].append(rel_path)
        if result["expected_filename"] and path.name == result["expected_filename"]:
            result["matched_file"] = rel_path

    return result


def detect_sync_package(project_root: Path) -> dict:
    """Check for a portable-sync archive to unpack.

    Checks docs/ first (canonical location), then project root (backward compat).

    Returns:
        Dict with found (bool) and path (relative path or None).
    """
    for rel_path in ("docs/portable-sync.tar.gz", "portable-sync.tar.gz"):
        if (project_root / rel_path).is_file():
            return {"found": True, "path": rel_path}
    return {"found": False, "path": None}


def check_first_run(project_root: Path, sanctum_dir: str | None = None) -> bool:
    """Check if the sanctum directory exists (first run when it doesn't)."""
    sanctum = resolve_sanctum_dir(project_root, sanctum_dir)
    return not sanctum.exists()


def scaffold_sidecar(
    project_root: Path, skill_dir: Path, sanctum_dir: str | None = None
) -> dict:
    """Scaffold the v2 sanctum by delegating to init-sanctum.py.

    The old inline 3-stub scaffold (access-boundaries.md / patterns.md /
    chronology.md) is superseded — init-sanctum.py builds the full v2 sanctum
    from the templates in assets/ (INDEX.md, MEMORY.md, PERSONA.md, CREED.md,
    BOND.md, PULSE.md, CAPABILITIES.md + sessions/ + capabilities/). After
    scaffolding, the conversational First Breath (references/init.md) calibrates.
    """
    init_script = skill_dir / "scripts" / "init-sanctum.py"
    if not init_script.is_file():
        return {
            "scaffolded": False,
            "error": True,
            "message": f"init-sanctum.py not found at {init_script}",
        }

    cmd = [
        sys.executable,
        str(init_script),
        str(project_root),
        str(skill_dir),
        "--format",
        "json",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as exc:
        return {
            "scaffolded": False,
            "error": True,
            "message": f"could not invoke init-sanctum.py: {exc}",
        }

    payload: dict = {}
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {"raw_output": result.stdout.strip()}

    sanctum = resolve_sanctum_dir(project_root, sanctum_dir)
    return {
        "scaffolded": result.returncode == 0,
        "via": "init-sanctum.py",
        "sanctum_path": str(sanctum),
        "init_result": payload,
        "files_created": payload.get("created", []),
    }


def find_module_csv(project_root: Path, skill_dir: Path) -> Path | None:
    """Find module-help.csv — installed location first, then setup skill assets.

    Search order:
    1. BMad installed location (_bmad/module-help.csv)
    2. Setup skill assets (sibling of this skill in the discovery directory)
    3. Setup skill assets (in src/skills/ — standalone/source installs)
    """
    # 1. BMad installed location
    installed = project_root / "_bmad" / "module-help.csv"
    if installed.is_file():
        return installed

    # 2. Setup skill assets (sibling directory — works for symlinked and copied skills)
    skills_dir = skill_dir.parent
    setup_csv = skills_dir / SETUP_SKILL_NAME / "assets" / "module-help.csv"
    if setup_csv.is_file():
        return setup_csv

    # 3. Source directory fallback (standalone install without BMad)
    source_csv = project_root / "src" / "skills" / SETUP_SKILL_NAME / "assets" / "module-help.csv"
    if source_csv.is_file():
        return source_csv

    return None


def parse_csv(csv_path: Path, include_modules: list[str] | None = None) -> list[dict]:
    """Parse module-help.csv and return rows filtered by module (excluding setup).

    Args:
        csv_path: Path to module-help.csv
        include_modules: If provided, only include rows whose 'module' column
            matches one of these values. If None, include all rows.
    """
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            # Skip the setup skill's own entry
            if row.get("skill", "").strip() == SETUP_SKILL_NAME:
                continue
            # Filter by module if specified
            if include_modules is not None:
                module = row.get("module", "").strip()
                if module not in include_modules:
                    continue
            rows.append(row)
    return rows


def render_menu(csv_path: Path, include_modules: list[str] | None = None) -> str:
    """Render capability menu from module-help.csv."""
    rows = parse_csv(csv_path, include_modules)

    lines = ["What would you like to do today?\n"]
    for i, row in enumerate(rows, 1):
        code = row.get("menu-code", "??").strip()
        display = row.get("display-name", "").strip()
        desc = row.get("description", "No description").strip()
        lines.append(f"{i}. [{code}] {display} — {desc}")

    return "\n".join(lines)


def build_routing_table(csv_path: Path, include_modules: list[str] | None = None) -> dict:
    """Build menu-code to capability routing table."""
    rows = parse_csv(csv_path, include_modules)

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
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="Scaffold the v2 sanctum (via init-sanctum.py) if missing",
    )
    parser.add_argument(
        "--sanctum-dir",
        default=None,
        help=(
            "Override the sanctum directory for first-run detection (default: "
            "<project_root>/_bmad/_memory/band-manager-sidecar)."
        ),
    )
    parser.add_argument("--user-name", help="Current user name (for voice file matching)")
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

    # Only show this module's own capabilities in the menu.
    menu_modules = [MODULE_CODE]

    result = {
        "first_run": check_first_run(project_root, args.sanctum_dir),
        "sync_package": detect_sync_package(project_root),
        "menu": render_menu(csv_path, menu_modules),
        "routing_table": build_routing_table(csv_path, menu_modules),
        "voice_context": detect_voice_files(project_root, args.user_name),
        # The activation router loads these sanctum files, in this order, on rebirth.
        "sanctum_load_order": SANCTUM_LOAD_ORDER,
    }

    if args.scaffold and result["first_run"]:
        result["scaffold"] = scaffold_sidecar(
            project_root, skill_dir, args.sanctum_dir
        )

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
    sys.exit(0)
