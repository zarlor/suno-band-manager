#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Post-unpack reconciliation helper for the Mac sanctum.

After `unpack-portable.sh/.ps1` extracts a sync archive on a receiving
machine, the sanctum's curated MEMORY.md still reflects the receiving machine's
prior local state — even though the freshly-arrived files (WIPs, songbook
entries, band profiles, playlist docs, session-context) may contain updates the
sanctum narrative should integrate.

(In the pre-v2 layout the reference file was `index.md`; the v2 sanctum's
curated narrative lives in `MEMORY.md`, with `INDEX.md` as a thin map. The
store-freshness reference is the newest mtime of MEMORY.md / INDEX.md.)

This script produces a punch list for the agent to walk through:

  1. **Files modified more recently than the store** — candidates for
     narrative integration (session history, current work, pending threads).
  2. **Validator findings** — calls `validate-sidecar.py` so drift between
     the sanctum narrative and the unpacked file state surfaces immediately.

The script does not edit files. The agent is responsible for reading each
candidate and deciding whether the sanctum narrative should integrate its
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
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Default sanctum location (preserved bespoke divergence: double-underscore parent,
# fixed dir name). The curated narrative lives in MEMORY.md; INDEX.md is a thin map.
DEFAULT_SANCTUM_REL = ("_bmad", "_memory", "band-manager-sidecar")
# Store-state files whose freshness defines "the store" for the newer-than punch list.
STORE_FILES = ("MEMORY.md", "INDEX.md")


def resolve_sanctum_dir(project_root: Path, sanctum_dir: str | None) -> Path:
    """Resolve the sanctum directory, honoring a --sanctum-dir override.

    Default is the real bespoke sanctum under the project root. The override
    exists so the memory scripts can be tested against a staging copy without
    touching live data.
    """
    if sanctum_dir:
        return Path(sanctum_dir).resolve()
    return project_root.joinpath(*DEFAULT_SANCTUM_REL)


def _format_mtime(mtime: float) -> str:
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def find_newer_docs(project_root: Path, store_mtime: float) -> list[dict[str, Any]]:
    """Return docs/*.md files whose mtime is newer than the sanctum store.

    These are the most likely candidates for sanctum narrative integration —
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

    cmd = [
        sys.executable,
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
            "These are candidates for narrative integration. Review each and "
            "decide whether the sanctum's session history, current work, or "
            "catalog status should be updated before continuing:"
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
            "integrate changes into the sanctum narrative before packing "
            "a return sync."
        )
    else:
        lines.append("CLEAN: sanctum is in sync with unpacked file state.")

    return "\n".join(lines)


def build_report(
    project_root: Path, sanctum_dir: str | None = None
) -> dict[str, Any]:
    sanctum = resolve_sanctum_dir(project_root, sanctum_dir)

    # The store-freshness reference is the newest mtime among MEMORY.md / INDEX.md.
    # MEMORY.md is the curated narrative; INDEX.md is the thin map. Either being
    # newer than a doc means the store has already seen that doc's state.
    store_files = [sanctum / name for name in STORE_FILES if (sanctum / name).is_file()]

    def _display(path: Path) -> str:
        try:
            return str(path.relative_to(project_root))
        except ValueError:
            return str(path)

    if not store_files:
        # Nothing to reconcile against — report the would-be primary store path.
        primary = sanctum / STORE_FILES[0]
        payload: dict[str, Any] = {
            "store_path": _display(primary),
            "status": "no_sidecar",
            "newer_files": [],
            "validator": {
                "status": "skipped",
                "reason": "no sanctum store (MEMORY.md / INDEX.md)",
            },
            "needs_reconciliation": False,
        }
        return payload

    # Use the freshest store file as the reference; report it as the store path.
    reference_file = max(store_files, key=lambda p: p.stat().st_mtime)
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
            "<project_root>/_bmad/_memory/band-manager-sidecar). Use to test "
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
