#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Checks a path against Mac's Dominion (access boundaries).

Run before a durable write where no human reviews it (headless runs, Pulse).
The boundaries live in the sanctum's CREED.md
(`{project-root}/_bmad/memory/suno-agent-band-manager/CREED.md`), in the
`## Dominion (Access Boundaries)` section: its `### Read Access`,
`### Write Access` and `### Deny Zones` subsections are read; `### The Write
Rule` and `### Notes` are prose. A legacy standalone access-boundaries.md (with
`## Read Access` etc. at the top level) is still accepted.

Deny Zones win over everything; then a path is allowed if a Write Access entry
(for writes) or a Read or Write Access entry (for reads) matches it. Entries are
the backticked paths at the start of each bullet: directories end with `/`,
globs (`*`) and placeholders (`{username}`) match any run of characters, and
`{project-root}` / `{skill-root}` resolve from the flags.

Usage:
    uv run scripts/validate-path.py <path> <read|write> [--boundaries FILE]
                                    [--project-root DIR] [--skill-root DIR]

Without --boundaries, the sanctum's CREED.md under --project-root (default: the
current directory) is used.

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
DOMINION_RE = re.compile(r"^##\s+Dominion\b", re.IGNORECASE)


def _load_sanctum_seed():
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("_sanctum_seed", Path(__file__).resolve().parent / "_sanctum_seed.py")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def default_boundaries(project_root: str | None) -> Path:
    """The sanctum's CREED.md, which carries the Dominion."""
    return _load_sanctum_seed().sanctum_dir(Path(project_root or ".")) / "CREED.md"


def boundary_lines(text: str) -> list[str]:
    """The lines to parse: the CREED.md Dominion section when there is one
    (up to the next `# `/`## ` heading), else the whole file (legacy
    access-boundaries.md)."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if DOMINION_RE.match(line)), None)
    if start is None:
        return lines
    out = []
    for line in lines[start + 1:]:
        if re.match(r"^#{1,2}\s", line):
            break
        out.append(line)
    return out


def parse_boundaries(boundaries_path: Path) -> dict:
    """{read, write, deny}: the path patterns listed under each heading."""
    boundaries: dict[str, list[str]] = {"read": [], "write": [], "deny": []}
    current = None
    for line in boundary_lines(boundaries_path.read_text(encoding="utf-8")):
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
    parser = argparse.ArgumentParser(description="Validate a path against Mac's Dominion (access boundaries in CREED.md)")
    parser.add_argument("path", help="File path to validate")
    parser.add_argument("operation", choices=["read", "write"], help="Operation type")
    parser.add_argument(
        "--boundaries",
        help=(
            "The sanctum's CREED.md (its Dominion section) or a legacy access-boundaries.md. "
            "Default: <project-root>/_bmad/memory/suno-agent-band-manager/CREED.md"
        ),
    )
    parser.add_argument("--project-root", default=None, help="Resolves {project-root} and absolute paths")
    parser.add_argument("--skill-root", default=None, help="Resolves {skill-root}")
    args = parser.parse_args()

    boundaries_path = Path(args.boundaries) if args.boundaries else default_boundaries(args.project_root)
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
