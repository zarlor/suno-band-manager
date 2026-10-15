#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Waking for Mac (suno-agent-band-manager).

One script decides the mode and gathers what activation needs:

  - config: BMad v7's `modules.suno` answers and output_folder, plus the
    owner's name and language from the sanctum's BOND.md — no separate step
  - the sanctum state: absent / v7 / v2 / v1 / damaged (case-sensitive
    markers; an incomplete identity set is damaged). The v7 sanctum is
    `_bmad/memory/suno-agent-band-manager/`; a v1/v2 store at the legacy
    `_bmad/_memory/band-manager-sidecar/` routes to its conversion
  - the dynamic menu and a code-keyed routing table from assets/menu.csv
    (null with a warning when the CSV is missing — the sanctum still wakes)
  - the voice file and docs/mac-preferences.md, with their sizes

Default output is JSON (headless callers, tests). `--wake` prints a MODE line,
the state as compact JSON, the menu as its own block, the identity files in load order and a generated map of
memory/ and raw/ (plus memory/pending.md when it has content) in one pass, so
the agent becomes itself in a single read. `--pulse` adds PULSE.md.

Usage:
    uv run {skill-root}/scripts/pre-activate.py <project-root> [--wake] [--pulse] [--scaffold]
                                   [--user-name NAME] [--sanctum-dir PATH] [-o OUTPUT]

Options:
    --wake          Print MODE + state + sanctum files (one-pass wake).
    --pulse         Pulse wake: also print PULSE.md (implies --wake).
    --scaffold      Scaffold the v7 sanctum (via init-sanctum.py) if it is absent.
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
SANCTUM_LOAD_ORDER = _seed.SANCTUM_LOAD_ORDER
PULSE_LOAD_ORDER = _seed.PULSE_LOAD_ORDER
MENU_ALIASES = _seed.MENU_ALIASES
find_menu_csv = _seed.find_menu_csv
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
        "preference_shards": [],
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
    if docs_dir.is_dir():
        result["preference_shards"] = [
            str(p.relative_to(project_root)) for p in sorted(docs_dir.glob("mac-preferences-*.md"))
            if p.stem != "mac-preferences-archive"
        ]
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


def locate(project_root: Path, sanctum_dir: str | None = None) -> tuple[Path, dict]:
    """The sanctum to wake from: the v7 path, or a v1/v2 store at the legacy path."""
    return _seed.locate_sanctum(project_root, sanctum_dir)


def detect_sidecar_format(project_root: Path, sanctum_dir: str | None = None) -> dict:
    """absent / v7 / v2 / v1 / damaged — see _sanctum_seed.classify_sanctum."""
    return locate(project_root, sanctum_dir)[1]


def check_first_run(project_root: Path, sanctum_dir: str | None = None) -> bool:
    """True only when the sanctum is absent."""
    return detect_sidecar_format(project_root, sanctum_dir)["sidecar_format"] == "absent"


def scaffold_sidecar(project_root: Path, skill_dir: Path, sanctum_dir: str | None = None) -> dict:
    """Scaffold the v7 sanctum by delegating to init-sanctum.py."""
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


def learned_warnings(sanctum: Path, builtin_codes: set[str]) -> list[str]:
    """Learned-table rows that would silently miss the menu: malformed, or a code clash."""
    path = sanctum / "CAPABILITIES.md"
    if not path.is_file():
        return []
    out: list[str] = []
    in_learned = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_learned = line.strip() == "## Learned"
            continue
        row = line.strip()
        if not in_learned or not row.startswith("|") or set(row) <= set("|-: "):
            continue
        if row.lower().startswith("| code "):
            continue
        match = LEARNED_ROW_RE.match(row)
        if not match:
            out.append(f"CAPABILITIES.md Learned row not readable, left off the menu: {row[:80]}")
        elif match.group(1).strip() in builtin_codes:
            out.append(f"Learned capability [{match.group(1).strip()}] clashes with a built-in menu code, left off the menu: pick another code.")
    return out


def resolve_customization(project_root: Path, skill_dir: Path) -> tuple[dict, str | None]:
    """The agent's v7 override arrays from BMad's resolve_customization.py."""
    empty = {"activation_steps_prepend": [], "activation_steps_append": [], "persistent_facts": []}
    script = project_root / "_bmad" / "scripts" / "resolve_customization.py"
    if not script.is_file():
        return empty, "BMad is not set up here (no resolve_customization.py): team overrides not applied; offer `bmad setup suno`."
    cmd = [sys.executable, str(script), "--skill", str(skill_dir), "--project-root", str(project_root), "--key", "agent"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        agent = (json.loads(proc.stdout or "{}") or {}).get("agent") or {}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return empty, f"customization could not be resolved ({exc}); shipped defaults apply."
    if proc.returncode != 0:
        return empty, f"customization could not be resolved ({(proc.stderr or '').strip()[-200:]}); shipped defaults apply."
    return {key: list(agent.get(key) or []) for key in empty}, None


def _menu_entries(csv_path: Path, learned: list[dict] | None) -> list[tuple[str, str, str, dict]]:
    """(code, name, description, route) per menu line, in menu order: built-ins then learned."""
    entries = [(r.get("code", "??"), r.get("name", ""), r.get("description", ""), _seed.route_for(r))
               for r in _seed.menu_rows(csv_path)]
    codes = {e[0] for e in entries}
    for cap in learned or []:
        if cap["code"] in codes:
            continue
        codes.add(cap["code"])
        entries.append((cap["code"], cap["name"], f"{cap['description']} (learned)",
                        {"name": cap["name"], "type": cap["type"], "target": cap["target"]}))
    return entries


def render_menu(csv_path: Path, learned: list[dict] | None = None) -> str:
    """Mac's menu: assets/menu.csv rows (minus FL) + learned capabilities, one numbered line each."""
    lines = ["What would you like to do today?\n"]
    for i, (code, name, desc, _) in enumerate(_menu_entries(csv_path, learned), 1):
        lines.append(f"{i}. [{code}] {name} — {desc or 'No description'}")
    return "\n".join(lines)


def build_routing_table(csv_path: Path, learned: list[dict] | None = None) -> dict:
    """Menu code -> {name, type, target}; an alias (FL) maps to its target code.

    Keyed by code only: a number the owner types is the menu line with that number.
    """
    table: dict = {code: route for code, _, _, route in _menu_entries(csv_path, learned)}
    for alias, code in MENU_ALIASES.items():
        if code in table and alias not in table:
            table[alias] = code
    return table


# ---------------------------------------------------------------------------
# State + wake
# ---------------------------------------------------------------------------


def mode_for(state: dict, pulse: bool) -> str:
    fmt = state["sidecar_format"]
    if pulse:
        return "PULSE" if fmt == "v7" else "PULSE_SKIPPED"
    return {
        "absent": "FIRST_BREATH",
        "v1": "UPGRADE_V1",
        "v2": "UPGRADE_V2",
        "v7": "WAKING",
        "damaged": "DAMAGED",
    }[fmt]


def build_state(args, project_root: Path, skill_dir: Path) -> dict:
    sanctum, _ = locate(project_root, args.sanctum_dir)
    config = _seed.resolve_config(project_root, sanctum)
    user_name = args.user_name or config["values"].get("user_name")
    warnings: list[str] = list(config["warnings"])
    if args.user_name:
        warnings = [w for w in warnings if not w.startswith("user_name")]

    sidecar = detect_sidecar_format(project_root, args.sanctum_dir)
    if args.scaffold and sidecar["sidecar_format"] == "absent":
        scaffold = scaffold_sidecar(project_root, skill_dir, args.sanctum_dir)
        sanctum, sidecar = locate(project_root, args.sanctum_dir)
        if not scaffold.get("scaffolded"):
            warnings.append(f"Scaffold failed: {scaffold.get('message') or scaffold.get('init_result')}")
    else:
        scaffold = None

    csv_path = find_menu_csv(skill_dir)
    learned = learned_capabilities(sanctum) if sidecar["sidecar_format"] in ("v7", "v2", "damaged") else []
    if csv_path is None:
        menu_text = None
        routing_table = None
        warnings.append(
            "assets/menu.csv not found: the menu is unavailable. Wake normally and "
            "tell the owner that reinstalling the suno-agent-band-manager skill restores the menu."
        )
    else:
        menu_text = render_menu(csv_path, learned)
        routing_table = build_routing_table(csv_path, learned)
        builtin = {r.get("code", "") for r in _seed.menu_rows(csv_path)}
        warnings.extend(learned_warnings(sanctum, builtin | set(MENU_ALIASES)))

    customization, customization_warning = resolve_customization(project_root, skill_dir)
    if customization_warning:
        warnings.append(customization_warning)

    pulse = bool(getattr(args, "pulse", False))
    resume = sidecar["sidecar_format"] == "v7" and not (sanctum / "memory" / ".born").is_file()
    mode = mode_for(sidecar, pulse)
    if resume and mode == "WAKING":
        mode = "FIRST_BREATH"
    if scaffold is not None and not scaffold.get("scaffolded"):
        mode = "SCAFFOLD_FAILED"
    state = {
        "mode": mode,
        "resume": resume,
        "first_run": sidecar["sidecar_format"] == "absent",
        "sidecar_format": sidecar["sidecar_format"],
        "needs_migration": sidecar["needs_migration"],
        "missing_spine": sidecar["missing_spine"],
        "config": {**config["values"], "user_name": user_name},
        "config_sources": config["sources"],
        "sync_package": detect_sync_package(project_root),
        "menu_text": menu_text,
        "routing_table": routing_table,
        "customization": customization,
        "voice_context": detect_voice_files(project_root, user_name),
        "sanctum_path": str(sanctum),
        "sanctum_load_order": (
            _seed.V2_SPINE if sidecar["sidecar_format"] == "v2"
            else PULSE_LOAD_ORDER if pulse else SANCTUM_LOAD_ORDER
        ),
        "memory": _seed.tending_state(sanctum) | {"undistilled_raw": len(_seed.undistilled_raw(sanctum))},
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
    "UPGRADE_V2": (
        "Your memory is still in the old layout (printed below, so you wake as yourself). "
        "Load references/upgrade-v2.md: back it up and convert it to the v7 sanctum. "
        "Never re-scaffold over it."
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
    "SCAFFOLD_FAILED": (
        "Creating the sanctum failed (see warnings and scaffold). Tell the owner what failed "
        "in a line; don't retry --scaffold until the cause is fixed."
    ),
}


def render_wake(state: dict) -> str:
    """MODE line, state JSON, then the sanctum files in load order."""
    mode = state["mode"]
    out = [f"MODE: {mode}", f"Sanctum: {state['sanctum_path']}"]
    if mode == "FIRST_BREATH" and state.get("scaffold", {}).get("scaffolded"):
        out.append("Sanctum created from the templates and printed below. Become it, then load references/init.md.")
    elif mode == "FIRST_BREATH" and state.get("resume"):
        out.append("First Breath was cut short (no memory/.born). Your sanctum is printed below; "
                   "load references/init.md and pick up from what is still unset.")
    elif mode in WAKE_GUIDANCE:
        out.append(WAKE_GUIDANCE[mode])
    if mode == "SCAFFOLD_FAILED":
        scaffold = state.get("scaffold") or {}
        out.append(f"Reason: {scaffold.get('message') or scaffold.get('init_result') or 'unknown'}")
    # The menu prints as its own block, so the state JSON stays compact and the
    # menu reads exactly as it should be shown.
    shown = {k: v for k, v in state.items() if k != "menu_text"}
    out += ["", "===== STATE =====", json.dumps(shown, separators=(",", ":"), ensure_ascii=False)]
    if mode in ("WAKING", "DAMAGED") or (mode == "FIRST_BREATH" and (state.get("scaffold") or state.get("resume"))):
        out += ["\n===== MENU =====", state.get("menu_text") or "(no menu: assets/menu.csv is missing; see warnings)"]
    sanctum = Path(state["sanctum_path"])
    newborn = mode == "FIRST_BREATH" and (state.get("scaffold", {}).get("scaffolded") or state.get("resume"))
    if mode in ("WAKING", "PULSE", "DAMAGED", "UPGRADE_V2") or newborn:
        for name in state["sanctum_load_order"]:
            path = sanctum / name
            out.append(f"\n===== {name} =====")
            if path.is_file():
                out.append(path.read_text(encoding="utf-8").rstrip())
            else:
                out.append(f"(missing: {name})")
    if mode in ("WAKING", "PULSE", "DAMAGED") or newborn:
        out += ["\n===== memory map =====", _seed.memory_map(sanctum)]
        pending = _seed.pending_text(sanctum)
        if pending:
            out += ["\n===== memory/pending.md =====", pending]
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Mac waking: config, sanctum state, menu, one-pass load")
    parser.add_argument("project_root", help="Project root directory")
    parser.add_argument("--wake", action="store_true", help="Print MODE + state + sanctum files")
    parser.add_argument("--pulse", action="store_true", help="Pulse wake (maintenance set); implies --wake")
    parser.add_argument("--scaffold", action="store_true", help="Scaffold the v7 sanctum if absent")
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
    return 1 if state["mode"] == "SCAFFOLD_FAILED" else 0


if __name__ == "__main__":
    sys.exit(main())
