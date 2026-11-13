#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
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

  1. **Files modified more recently than the store** (`newer_files`) —
     candidates for the standing files (memory/work/current.md,
     memory/work/parked.md...) or a session note.
  2. **Files that arrived after the store was written but carry an older edit
     time** (`arrived_files`, the most recently edited first, at most 25;
     `arrived_count` is the total). An unpack keeps each file's edit time from
     the other machine, so a doc edited there before this machine's last
     memory write is not in list 1 although the sanctum never saw it. An unpack
     rewrites every file, so most entries are unchanged: this list informs, it
     does not by itself raise `needs_reconciliation`.
  3. **Validator findings** — calls `validate_sanctum.py` so drift between
     the sanctum and the unpacked file state surfaces immediately. A validator
     that crashes or returns `status: error` validated nothing, so the report
     is `needs_reconciliation`, never `clean`.

The script does not edit files. The agent is responsible for reading each
candidate and deciding whether the sanctum's memory should integrate its
content, surfacing the decision to the user via the usual handoff
checkpoint.

Usage:
    uv run {skill-root}/scripts/reconcile_sanctum.py [project_root]
    uv run {skill-root}/scripts/reconcile_sanctum.py --format json
    uv run {skill-root}/scripts/reconcile_sanctum.py --sanctum-dir PATH  # test a staging copy

Exit codes:
    0 — sanctum and files are in sync (or sanctum absent — nothing to check)
    1 — newer files found, the validator reported errors, or the validator
        itself failed (agent should reconcile)
    2 — project root not found
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


# How many arrived files the report lists (the most recently edited first).
ARRIVED_LIMIT = 25


def find_arrived_docs(project_root: Path, store_mtime: float) -> list[dict[str, Any]]:
    """docs/*.md files that landed on this machine after the store was last
    written, though their edit time is older than the store.

    An unpacked archive keeps each file's edit time from the machine that wrote
    it (`tar xzf`). A doc edited there before this machine's last memory write
    is therefore not "newer" by its mtime, yet this machine's memory has never
    seen it. The file's change time (when it was written to this disk, where
    the platform records that) tells it arrived since. An unpack rewrites every
    file, so most of these are unchanged: they are listed apart from
    `newer_files`, most recently edited first, for a look at the top of the list.
    """
    docs_root = project_root / "docs"
    if not docs_root.is_dir():
        return []
    arrived: list[tuple[float, float, Path]] = []
    for path in docs_root.rglob("*.md"):
        try:
            st = path.stat()
        except OSError:
            continue
        if st.st_mtime <= store_mtime < st.st_ctime:
            arrived.append((st.st_mtime, st.st_ctime, path))
    arrived.sort(key=lambda item: (-item[0], str(item[2])))
    return [
        {"path": str(path.relative_to(project_root)), "mtime": _format_mtime(mtime), "arrived": _format_mtime(ctime)}
        for mtime, ctime, path in arrived
    ]


def run_validator(project_root: Path, sanctum_dir: str | None = None) -> dict[str, Any]:
    """Invoke validate_sanctum.py and return its JSON payload.

    Soft-fail if the validator isn't present — older installs or partial
    checkouts shouldn't break the reconcile flow.
    """
    validator = Path(__file__).parent / "validate_sanctum.py"
    if not validator.is_file():
        return {"status": "skipped", "reason": "validate_sanctum.py not found"}

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

    arrived_count = payload.get("arrived_count", 0)
    if arrived_count:
        arrived = payload.get("arrived_files", [])
        lines.append(
            f"Files that arrived after the store was last written, with an older edit time: {arrived_count}"
        )
        lines.append(
            "An unpack rewrites every file, so most of these are unchanged. Any edited on the other "
            "machine since this one last synced is new to the sanctum; the most recently edited come first"
            + (f" (showing {len(arrived)} of {arrived_count}):" if arrived_count > len(arrived) else ":")
        )
        lines.append("")
        for item in arrived:
            lines.append(f"  - {item['path']}  (edited {item['mtime']})")
        lines.append("")

    validator = payload.get("validator", {})
    v_status = validator.get("status", "unknown")
    lines.append(f"Validator: {v_status}")
    if v_status == "error":
        detail = "; ".join(str(validator[k]) for k in ("reason", "message", "stderr") if validator.get(k))
        lines.append(f"  The validator did not complete, so nothing was validated: {detail or 'no reason given'}")
        lines.append("")
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
            "arrived_count": 0,
            "arrived_files": [],
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
    arrived = find_arrived_docs(project_root, store_mtime)
    payload["arrived_count"] = len(arrived)
    payload["arrived_files"] = arrived[:ARRIVED_LIMIT]
    payload["validator"] = run_validator(project_root, sanctum_dir)
    if not isinstance(payload["validator"], dict):
        payload["validator"] = {"status": "error", "reason": "validator output was not a JSON object"}

    validator_findings = payload["validator"].get("findings", []) or []
    has_errors = any(isinstance(f, dict) and f.get("severity") == "error" for f in validator_findings)
    # A validator that crashed or reported an error validated nothing: that is
    # not a clean report.
    validator_failed = payload["validator"].get("status") == "error"
    payload["needs_reconciliation"] = bool(payload["newer_files"]) or has_errors or validator_failed
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
