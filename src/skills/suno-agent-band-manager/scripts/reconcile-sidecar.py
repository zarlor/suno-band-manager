#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Post-unpack reconciliation helper for the Mac sanctum.

After `unpack-portable.sh/.ps1` extracts a sync archive on a receiving
machine, the sanctum (`{project-root}/_bmad/memory/suno-agent-band-manager/`,
per-machine; it never travels) still reflects this machine's prior local state,
even though the freshly-arrived docs/ files (WIPs, songbook entries, band
profiles, playlist docs, the voice file) may hold updates its memory should
take in.

The store-freshness reference is the newest file Mac wrote under `memory/`
(standing files, session notes, chronology, `memory/.tended`). The generated
`memory/catalog/` files are left out: regenerating them is not Mac having seen
a doc.

This script produces a punch list for the agent to walk through:

  1. **Files modified more recently than the store** — candidates for the
     standing files (memory/work/current.md, memory/work/parked.md...) or a
     session note.
  2. **Validator findings** — calls `validate-sidecar.py` so drift between
     the sanctum and the unpacked file state surfaces immediately.

The script does not edit files. The agent is responsible for reading each
candidate and deciding whether the sanctum's memory should integrate its
content, surfacing the decision to the user via the usual handoff
checkpoint.

Usage:
    uv run scripts/reconcile-sidecar.py [project_root]
    uv run scripts/reconcile-sidecar.py --format json
    uv run scripts/reconcile-sidecar.py --sanctum-dir PATH  # test a staging copy

Exit codes:
    0 — sanctum and files are in sync (or sanctum absent — nothing to check)
    1 — candidates found or validator reported errors (agent should reconcile)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_sanctum_seed():
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("_sanctum_seed", Path(__file__).resolve().parent / "_sanctum_seed.py")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_seed = _load_sanctum_seed()

# memory/ subfolders whose files do not count toward the store's freshness:
# the catalog is generated from the songbook, not written from what Mac saw.
DERIVED_DIRS = ("catalog",)


def resolve_sanctum_dir(project_root: Path, sanctum_dir: str | None) -> Path:
    """The v7 sanctum, or the --sanctum-dir override.

    The override exists so the memory scripts can be tested against a staging
    copy without touching live data.
    """
    return _seed.sanctum_dir(project_root, sanctum_dir).resolve()


def store_files(sanctum: Path) -> list[Path]:
    """Files under memory/ that say what Mac has seen (everything but the catalog)."""
    memory = sanctum / "memory"
    if not memory.is_dir():
        return []
    out = []
    for path in memory.rglob("*"):
        rel = path.relative_to(memory)
        if path.is_file() and not (len(rel.parts) > 1 and rel.parts[0] in DERIVED_DIRS):
            out.append(path)
    return out


def _format_mtime(mtime: float) -> str:
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def find_newer_docs(project_root: Path, store_mtime: float) -> list[dict[str, Any]]:
    """Return docs/*.md files whose mtime is newer than the sanctum store.

    These are the most likely candidates for the sanctum's memory —
    a freshly unpacked WIP update, session-context edit, or songbook
    addition that hasn't yet shown up in the sanctum's story.
    """
    docs_root = project_root / "docs"
    if not docs_root.is_dir():
        return []

    candidates: list[dict[str, Any]] = []
    for path in sorted(docs_root.rglob("*.md")):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime <= store_mtime:
            continue
        rel = str(path.relative_to(project_root))
        candidates.append(
            {
                "path": rel,
                "mtime": _format_mtime(mtime),
                "delta_seconds": int(mtime - store_mtime),
            }
        )
    return candidates


def run_validator(project_root: Path, sanctum_dir: str | None = None) -> dict[str, Any]:
    """Invoke validate-sidecar.py and return its JSON payload.

    Soft-fail if the validator isn't present — older installs or partial
    checkouts shouldn't break the reconcile flow.
    """
    validator = Path(__file__).parent / "validate-sidecar.py"
    if not validator.is_file():
        return {"status": "skipped", "reason": "validate-sidecar.py not found"}

    # The validator needs PyYAML (PEP 723 header); `uv run` provisions it. Without
    # uv, fall back to this interpreter (works when PyYAML is installed).
    uv = shutil.which("uv")
    launcher = [uv, "run", "-q", "--script"] if uv else [sys.executable]
    cmd = [
        *launcher,
        str(validator),
        str(project_root),
        "--format",
        "json",
        "--warn-only",
    ]
    if sanctum_dir:
        cmd += ["--sanctum-dir", sanctum_dir]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {"status": "error", "reason": f"could not invoke validator: {exc}"}

    if result.returncode not in (0, 1):
        return {
            "status": "error",
            "reason": f"validator exited {result.returncode}",
            "stderr": result.stderr.strip(),
        }

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"status": "error", "reason": f"validator output unparseable: {exc}"}


def format_text(payload: dict[str, Any]) -> str:
    lines = [
        "Sanctum Reconciliation Report",
        "=" * 29,
        "",
    ]

    status = payload.get("status", "unknown")
    lines.append(f"Status: {status}")
    lines.append(f"Sanctum store: {payload.get('store_path', 'unknown')}")
    if payload.get("store_mtime"):
        lines.append(f"Store last updated: {payload['store_mtime']}")
    lines.append("")

    candidates = payload.get("newer_files", [])
    lines.append(
        f"Files modified more recently than the sanctum store: {len(candidates)}"
    )
    if candidates:
        lines.append("")
        lines.append(
            "These are candidates for the sanctum's memory. Review each and "
            "decide whether a standing file (current work, parked threads) or a "
            "session note should take it in before continuing:"
        )
        lines.append("")
        for item in candidates:
            lines.append(f"  - {item['path']}  (modified {item['mtime']})")
        lines.append("")

    validator = payload.get("validator", {})
    v_status = validator.get("status", "unknown")
    lines.append(f"Validator: {v_status}")
    findings = validator.get("findings", []) or []
    if findings:
        by_category: dict[str, list[dict[str, Any]]] = {}
        for f in findings:
            by_category.setdefault(f.get("category", "other"), []).append(f)
        for category, items in sorted(by_category.items()):
            lines.append(f"  [{category.upper()}] ({len(items)})")
            for f in items:
                lines.append(
                    f"    ({f.get('severity', 'warning')}) "
                    f"{f.get('path', '')} — {f.get('message', '')}"
                )
        lines.append("")

    if payload.get("needs_reconciliation"):
        lines.append(
            "ACTION NEEDED: walk the punch list above with the user and "
            "integrate changes into the sanctum's memory before packing "
            "a return sync."
        )
    else:
        lines.append("CLEAN: sanctum is in sync with unpacked file state.")

    return "\n".join(lines)


def build_report(
    project_root: Path, sanctum_dir: str | None = None
) -> dict[str, Any]:
    sanctum = resolve_sanctum_dir(project_root, sanctum_dir)

    # The store-freshness reference is the newest file under memory/ (catalog
    # aside): a memory write newer than a doc means the store has seen its state.
    files = store_files(sanctum)

    def _display(path: Path) -> str:
        try:
            return str(path.relative_to(project_root))
        except ValueError:
            return str(path)

    if not files:
        # Nothing to reconcile against — report the would-be store path.
        payload: dict[str, Any] = {
            "store_path": _display(sanctum / "memory"),
            "status": "no_sidecar",
            "newer_files": [],
            "validator": {
                "status": "skipped",
                "reason": "no sanctum memory (memory/ is empty or absent)",
            },
            "needs_reconciliation": False,
        }
        return payload

    # Use the freshest store file as the reference; report it as the store path.
    reference_file = max(files, key=lambda p: p.stat().st_mtime)
    store_mtime = reference_file.stat().st_mtime
    payload = {"store_path": _display(reference_file)}
    payload["store_mtime"] = _format_mtime(store_mtime)
    payload["newer_files"] = find_newer_docs(project_root, store_mtime)
    payload["validator"] = run_validator(project_root, sanctum_dir)

    validator_findings = payload["validator"].get("findings", []) or []
    has_errors = any(f.get("severity") == "error" for f in validator_findings)
    payload["needs_reconciliation"] = bool(payload["newer_files"]) or has_errors
    payload["status"] = (
        "needs_reconciliation" if payload["needs_reconciliation"] else "clean"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Post-unpack reconciliation helper for the Mac sanctum."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--sanctum-dir",
        default=None,
        help=(
            "Override the sanctum directory (default: "
            "<project_root>/_bmad/memory/suno-agent-band-manager). Use to test "
            "against a staging copy without touching live data."
        ),
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(f"ERROR: project root not found: {project_root}", file=sys.stderr)
        return 2

    payload = build_report(project_root, args.sanctum_dir)

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(payload))

    return 1 if payload.get("needs_reconciliation") else 0


if __name__ == "__main__":
    sys.exit(main())
