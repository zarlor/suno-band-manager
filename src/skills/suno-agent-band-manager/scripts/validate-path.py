#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Checks a path against Mac's access-boundaries.md.

Run before a durable write where no human reviews it (headless runs, Pulse).
Deny Zones win over everything; then a path is allowed if a Write Access entry
(for writes) or a Read or Write Access entry (for reads) matches it. Entries are
the backticked paths at the start of each bullet: directories end with `/`,
globs (`*`) and placeholders (`{username}`) match any run of characters, and
`{project-root}` / `{skill-root}` resolve from the flags.

Usage:
    uv run scripts/validate-path.py <path> <read|write> --boundaries FILE
                                    [--project-root DIR] [--skill-root DIR]

Exit status: 0 when allowed, 1 when not (or on a usage error).
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path

ENTRY_RE = re.compile(r"^\s*[-*]\s+`([^`]+)`")
SECTIONS = {"read access": "read", "write access": "write", "deny zones": "deny"}


def parse_boundaries(boundaries_path: Path) -> dict:
    """{read, write, deny}: the path patterns listed under each heading."""
    boundaries: dict[str, list[str]] = {"read": [], "write": [], "deny": []}
    current = None
    for line in boundaries_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip().lower()
            current = next((v for k, v in SECTIONS.items() if title.startswith(k)), None)
            continue
        if current is None:
            continue
        match = ENTRY_RE.match(line)
        if match:
            boundaries[current].append(re.sub(r"^\{project-root\}/", "", match.group(1).strip()))
        elif stripped.startswith("- ") and current != "deny" and "`" not in stripped:
            # Plain bullet without backticks (older files): the item is the path
            # when it looks like one (no spaces); prose bullets are skipped.
            item = stripped[2:].split(" — ")[0].strip()
            if item and " " not in item:
                boundaries[current].append(re.sub(r"^\{project-root\}/", "", item))
    return boundaries


def _normalize(path: str, project_root: str | None, skill_root: str | None) -> str:
    """Project-relative form of a path or pattern, placeholders resolved."""
    path = path.replace("\\", "/")
    for token, value in (
        ("{project-root}/", project_root),
        ("{project_root}/", project_root),
        ("{skill-root}/", skill_root),
    ):
        if path.startswith(token):
            path = (value.rstrip("/") + "/" if value else "") + path[len(token):]
    if project_root:
        root = project_root.replace("\\", "/").rstrip("/") + "/"
        if path.startswith(root):
            path = path[len(root):]
    return path


def _matches(path: str, pattern: str) -> bool:
    glob = re.sub(r"\{[^}]+\}", "*", pattern)
    if glob.endswith("/"):
        return path.startswith(glob) or fnmatch.fnmatch(path, glob + "*")
    return path == glob or fnmatch.fnmatch(path, glob) or path.startswith(glob.rstrip("/") + "/")


def validate_path(
    file_path: str,
    operation: str,
    boundaries: dict,
    project_root: str | None = None,
    skill_root: str | None = None,
) -> dict:
    """Allowed or not, with the rule that decided it."""
    path = _normalize(file_path, project_root, skill_root)
    for pattern in boundaries.get("deny", []):
        rule = _normalize(pattern, project_root, skill_root)
        if _matches(path, rule):
            # A write-only deny does not block reads of the same zone.
            if operation == "read" and any(
                _matches(path, _normalize(p, project_root, skill_root)) for p in boundaries.get("read", [])
            ):
                break
            return {"allowed": False, "path": file_path, "operation": operation, "reason": "deny zone", "matched_rule": pattern}
    allowed = list(boundaries.get(operation, []))
    if operation == "read":
        allowed += boundaries.get("write", [])
    for pattern in allowed:
        if _matches(path, _normalize(pattern, project_root, skill_root)):
            return {"allowed": True, "path": file_path, "operation": operation, "matched_rule": pattern}
    return {
        "allowed": False,
        "path": file_path,
        "operation": operation,
        "reason": f"Path not in {operation} allowlist",
        "allowed_paths": allowed,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate a path against access boundaries")
    parser.add_argument("path", help="File path to validate")
    parser.add_argument("operation", choices=["read", "write"], help="Operation type")
    parser.add_argument("--boundaries", help="Path to access-boundaries.md")
    parser.add_argument("--project-root", default=None, help="Resolves {project-root} and absolute paths")
    parser.add_argument("--skill-root", default=None, help="Resolves {skill-root}")
    args = parser.parse_args()

    if not args.boundaries:
        print(json.dumps({"error": True, "message": "No --boundaries file specified"}))
        sys.exit(1)
    boundaries_path = Path(args.boundaries)
    if not boundaries_path.exists():
        print(json.dumps({"error": True, "message": f"Boundaries file not found: {boundaries_path}"}))
        sys.exit(1)

    result = validate_path(
        args.path,
        args.operation,
        parse_boundaries(boundaries_path),
        project_root=str(Path(args.project_root).resolve()) if args.project_root else None,
        skill_root=str(Path(args.skill_root).resolve()) if args.skill_root else None,
    )
    print(json.dumps(result, indent=2))
    if not result.get("allowed", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
    sys.exit(0)
