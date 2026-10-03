#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Waking for Mac (suno-agent-band-manager).

One script decides the mode and gathers what activation needs:

  - config (core settings + the `suno:` module section), resolved here on
    BMad v6.12 — no separate config step
  - the sanctum state: absent / v1 / v2 / damaged (case-sensitive markers; an
    incomplete spine is damaged)
  - the dynamic menu and routing table from module-help.csv (null with a
    warning when the CSV is missing — the sanctum still wakes)
  - the voice file and docs/mac-preferences.md, with their sizes

Default output is JSON (headless callers, tests). `--wake` prints a MODE line,
the state JSON, and then the sanctum files in load order in one pass, so the
agent becomes itself in a single read. `--pulse` (with `--wake`) prints the
Pulse set instead: access-boundaries, CREED, PERSONA, PULSE.

Usage:
    uv run scripts/pre-activate.py <project-root> [--wake] [--pulse] [--scaffold]
                                   [--user-name NAME] [--sanctum-dir PATH] [-o OUTPUT]

Options:
    --wake          Print MODE + state + sanctum files (one-pass wake).
    --pulse         Pulse wake: print the maintenance set (implies --wake).
    --scaffold      Scaffold the v2 sanctum (via init-sanctum.py) if it is absent.
    --user-name     Override the configured user name (voice-file matching).
    --sanctum-dir   Override the sanctum directory (staging copies, tests).
    -o, --output    Write the output to a file instead of stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_sanctum_seed():
    seed_path = Path(__file__).resolve().parent / "_sanctum_seed.py"
    spec = spec_from_file_location("_sanctum_seed", seed_path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_seed = _load_sanctum_seed()

AGENT_SKILL_NAME = _seed.AGENT_SKILL_NAME
SETUP_SKILL_NAME = _seed.SETUP_SKILL_NAME
MODULE_CODE = _seed.MODULE_CODE
SANCTUM_LOAD_ORDER = _seed.SANCTUM_LOAD_ORDER
PULSE_LOAD_ORDER = _seed.PULSE_LOAD_ORDER
MENU_ALIASES = _seed.MENU_ALIASES
find_module_csv = _seed.find_module_csv
normalize_username = _seed.normalize_username

VOICE_FILE_PREFIX = "voice-context-"
VOICE_FILE_SUFFIX = ".md"
PREFERENCES_FILE = "docs/mac-preferences.md"


def resolve_sanctum_dir(project_root: Path, sanctum_dir: str | None) -> Path:
    return _seed.sanctum_dir(project_root, sanctum_dir)


def file_size(path: Path) -> dict:
    """Size facts for a loaded file. tokens_est is chars/4 (a rough guide)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "chars": len(text),
        "lines": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        "tokens_est": round(len(text) / 4),
    }


def detect_voice_files(project_root: Path, user_name: str | None) -> dict:
    """Voice files in docs/, the one matching the user, and docs/mac-preferences.md."""
    docs_dir = project_root / "docs"
    result: dict = {
        "voice_files": [],
        "matched_file": None,
        "expected_filename": None,
        "mac_preferences": None,
        "sizes": {},
    }
    if user_name:
        result["expected_filename"] = f"{VOICE_FILE_PREFIX}{normalize_username(user_name)}{VOICE_FILE_SUFFIX}"
    if docs_dir.is_dir():
        for path in sorted(docs_dir.glob(f"{VOICE_FILE_PREFIX}*{VOICE_FILE_SUFFIX}")):
            rel_path = str(path.relative_to(project_root))
            result["voice_files"].append(rel_path)
            if result["expected_filename"] and path.name == result["expected_filename"]:
                result["matched_file"] = rel_path
    prefs = project_root / PREFERENCES_FILE
    if prefs.is_file():
        result["mac_preferences"] = PREFERENCES_FILE
    for rel in (result["matched_file"], result["mac_preferences"]):
        if rel:
            result["sizes"][rel] = file_size(project_root / rel)
    return result


def detect_sync_package(project_root: Path) -> dict:
    """A portable-sync archive waiting to be unpacked (docs/ first, then root)."""
    for rel_path in ("docs/portable-sync.tar.gz", "portable-sync.tar.gz"):
        if (project_root / rel_path).is_file():
            return {"found": True, "path": rel_path}
    return {"found": False, "path": None}


def detect_sidecar_format(project_root: Path, sanctum_dir: str | None = None) -> dict:
    """absent / v1 / v2 / damaged — see _sanctum_seed.classify_sanctum."""
    return _seed.classify_sanctum(resolve_sanctum_dir(project_root, sanctum_dir))


def check_first_run(project_root: Path, sanctum_dir: str | None = None) -> bool:
    """True only when the sanctum is absent."""
    return detect_sidecar_format(project_root, sanctum_dir)["sidecar_format"] == "absent"


def scaffold_sidecar(project_root: Path, skill_dir: Path, sanctum_dir: str | None = None) -> dict:
    """Scaffold the v2 sanctum by delegating to init-sanctum.py."""
    init_script = skill_dir / "scripts" / "init-sanctum.py"
    if not init_script.is_file():
        return {"scaffolded": False, "error": True, "message": f"init-sanctum.py not found at {init_script}"}
    cmd = [sys.executable, str(init_script), str(project_root), str(skill_dir), "--format", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as exc:
        return {"scaffolded": False, "error": True, "message": f"could not invoke init-sanctum.py: {exc}"}
    payload: dict = {}
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {"raw_output": result.stdout.strip()}
    return {
        "scaffolded": result.returncode == 0,
        "via": "init-sanctum.py",
        "sanctum_path": str(resolve_sanctum_dir(project_root, sanctum_dir)),
        "init_result": payload,
        "files_created": payload.get("created", []),
    }


# ---------------------------------------------------------------------------
# Menu + routing
# ---------------------------------------------------------------------------

LEARNED_ROW_RE = re.compile(r"^\|\s*\[([A-Za-z0-9]+)\]\s*\|([^|]*)\|([^|]*)\|([^|]*)\|")


def learned_capabilities(sanctum: Path) -> list[dict]:
    """Rows of the `## Learned` table in the sanctum's CAPABILITIES.md."""
    path = sanctum / "CAPABILITIES.md"
    if not path.is_file():
        return []
    rows: list[dict] = []
    in_learned = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_learned = line.strip() == "## Learned"
            continue
        if not in_learned:
            continue
        match = LEARNED_ROW_RE.match(line.strip())
        if match:
            source = match.group(4).strip().strip("`")
            if source.startswith("External:"):
                target_type, target = "skill", source.split(":", 1)[1].strip().strip("`")
            else:
                target_type, target = "learned", str(sanctum / source) if source else ""
            rows.append(
                {
                    "code": match.group(1).strip(),
                    "name": match.group(2).strip(),
                    "description": match.group(3).strip(),
                    "type": target_type,
                    "target": target,
                }
            )
    return rows


def render_menu(csv_path: Path, include_modules: list[str] | None = None, learned: list[dict] | None = None) -> str:
    """Mac's menu: module-help.csv rows (minus setup and FL) + learned capabilities."""
    rows = _seed.menu_rows(csv_path, include_modules)
    lines = ["What would you like to do today?\n"]
    codes = set()
    for i, row in enumerate(rows, 1):
        code = (row.get("menu-code") or "??").strip()
        codes.add(code)
        display = (row.get("display-name") or "").strip()
        desc = (row.get("description") or "No description").strip()
        lines.append(f"{i}. [{code}] {display} — {desc}")
    n = len(rows)
    for cap in learned or []:
        if cap["code"] in codes:
            continue
        n += 1
        lines.append(f"{n}. [{cap['code']}] {cap['name']} — {cap['description']} (learned)")
    return "\n".join(lines)


def build_routing_table(
    csv_path: Path, include_modules: list[str] | None = None, learned: list[dict] | None = None
) -> dict:
    """Menu code / position -> {name, type, target}. Aliases (FL -> RS) included."""
    rows = _seed.menu_rows(csv_path, include_modules)
    table: dict = {}
    for i, row in enumerate(rows, 1):
        entry = _seed.route_for(row)
        table[(row.get("menu-code") or "").strip()] = entry
        table[str(i)] = entry
    n = len(rows)
    for cap in learned or []:
        if cap["code"] in table:
            continue
        n += 1
        entry = {"name": cap["name"], "type": cap["type"], "target": cap["target"]}
        table[cap["code"]] = entry
        table[str(n)] = entry
    for alias, code in MENU_ALIASES.items():
        if code in table and alias not in table:
            table[alias] = dict(table[code], alias_of=code)
    return table


# ---------------------------------------------------------------------------
# State + wake
# ---------------------------------------------------------------------------


def mode_for(state: dict, pulse: bool) -> str:
    fmt = state["sidecar_format"]
    if pulse:
        return "PULSE" if fmt == "v2" else "PULSE_SKIPPED"
    return {"absent": "FIRST_BREATH", "v1": "UPGRADE_V1", "v2": "WAKING", "damaged": "DAMAGED"}[fmt]


def build_state(args, project_root: Path, skill_dir: Path) -> dict:
    config = _seed.resolve_config(project_root)
    user_name = args.user_name or config["values"].get("user_name")
    sanctum = resolve_sanctum_dir(project_root, args.sanctum_dir)
    warnings: list[str] = list(config["warnings"])
    if args.user_name:
        warnings = [w for w in warnings if not w.startswith("user_name")]

    sidecar = detect_sidecar_format(project_root, args.sanctum_dir)
    if args.scaffold and sidecar["sidecar_format"] == "absent":
        scaffold = scaffold_sidecar(project_root, skill_dir, args.sanctum_dir)
        sidecar = detect_sidecar_format(project_root, args.sanctum_dir)
    else:
        scaffold = None

    csv_path = find_module_csv(project_root, skill_dir)
    learned = learned_capabilities(sanctum) if sidecar["sidecar_format"] in ("v2", "damaged") else []
    if csv_path is None:
        menu_text = None
        routing_table = None
        warnings.append(
            "module-help.csv not found: the menu is unavailable. Wake normally and "
            "tell the owner the suno-setup skill restores the menu."
        )
    else:
        menu_text = render_menu(csv_path, [MODULE_CODE], learned)
        routing_table = build_routing_table(csv_path, [MODULE_CODE], learned)

    pulse = bool(getattr(args, "pulse", False))
    state = {
        "mode": mode_for(sidecar, pulse),
        "first_run": sidecar["sidecar_format"] == "absent",
        "sidecar_format": sidecar["sidecar_format"],
        "needs_migration": sidecar["needs_migration"],
        "missing_spine": sidecar["missing_spine"],
        "config": {**config["values"], "user_name": user_name},
        "config_sources": config["sources"],
        "sync_package": detect_sync_package(project_root),
        "menu_text": menu_text,
        "routing_table": routing_table,
        "menu_aliases": dict(MENU_ALIASES),
        "voice_context": detect_voice_files(project_root, user_name),
        "sanctum_path": str(sanctum),
        "sanctum_load_order": PULSE_LOAD_ORDER if pulse else SANCTUM_LOAD_ORDER,
        "warnings": warnings,
    }
    if scaffold is not None:
        state["scaffold"] = scaffold
        if scaffold.get("scaffolded"):
            # Just born: the sanctum now exists, but this is still First Breath.
            state["mode"] = "FIRST_BREATH"
    return state


WAKE_GUIDANCE = {
    "FIRST_BREATH": (
        "No sanctum yet. Re-run with --scaffold to create it from the templates; "
        "the output will print the newborn sanctum. Then load references/init.md."
    ),
    "UPGRADE_V1": (
        "A v1 memory store from an earlier version is here. Load references/upgrade-v1.md: "
        "back it up and migrate it. Never re-scaffold over it."
    ),
    "DAMAGED": (
        "The sanctum is incomplete (see missing_spine). The files that exist are printed "
        "below. Follow references/activation.md 'Damaged sanctum'."
    ),
    "PULSE_SKIPPED": "No complete sanctum, so there is nothing for Pulse to maintain. Stop.",
}


def render_wake(state: dict) -> str:
    """MODE line, state JSON, then the sanctum files in load order."""
    mode = state["mode"]
    out = [f"MODE: {mode}", f"Sanctum: {state['sanctum_path']}"]
    if mode == "FIRST_BREATH" and state.get("scaffold", {}).get("scaffolded"):
        out.append("Sanctum created from the templates and printed below. Become it, then load references/init.md.")
    elif mode in WAKE_GUIDANCE:
        out.append(WAKE_GUIDANCE[mode])
    out += ["", "===== STATE =====", json.dumps(state, indent=2, ensure_ascii=False)]
    if mode in ("WAKING", "PULSE", "DAMAGED") or (
        mode == "FIRST_BREATH" and state.get("scaffold", {}).get("scaffolded")
    ):
        sanctum = Path(state["sanctum_path"])
        for name in state["sanctum_load_order"]:
            path = sanctum / name
            out.append(f"\n===== {name} =====")
            if path.is_file():
                out.append(path.read_text(encoding="utf-8").rstrip())
            else:
                out.append(f"(missing: {name})")
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Mac waking: config, sanctum state, menu, one-pass load")
    parser.add_argument("project_root", help="Project root directory")
    parser.add_argument("--wake", action="store_true", help="Print MODE + state + sanctum files")
    parser.add_argument("--pulse", action="store_true", help="Pulse wake (maintenance set); implies --wake")
    parser.add_argument("--scaffold", action="store_true", help="Scaffold the v2 sanctum if absent")
    parser.add_argument("--sanctum-dir", default=None, help="Override the sanctum directory")
    parser.add_argument("--user-name", help="Override the configured user name (voice-file matching)")
    parser.add_argument("-o", "--output", help="Output file path")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    skill_dir = Path(__file__).resolve().parent.parent
    state = build_state(args, project_root, skill_dir)
    output = render_wake(state) if (args.wake or args.pulse) else json.dumps(state, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        reconfigure = getattr(sys.stdout, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
        sys.stdout.write(output if output.endswith("\n") else output + "\n")


if __name__ == "__main__":
    main()
    sys.exit(0)
