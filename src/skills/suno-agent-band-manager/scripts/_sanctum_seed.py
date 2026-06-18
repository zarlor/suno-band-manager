#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Shared sanctum-seeding logic for Mac (suno-agent-band-manager).

Single source of truth for the parts of sanctum scaffolding that BOTH the fresh
birth (`init-sanctum.py`) and the legacy migration (`migrate-sidecar-to-v2.py`)
must produce identically:

  - the loaded-FIRST Dominion contract `access-boundaries.md`
  - the on-demand creed shards (`creed-disciplines.md`,
    `creed-workshop-capture.md`, `creed-package-assembly.md`) +
    the non-loaded `creed-incident-log.md`

Before this module existed, only the migration path produced these files, so a
*freshly born* sanctum was contract-incomplete: the activation router loaded an
`access-boundaries.md` that didn't exist and the first package-assembly run
reached for a `creed-package-assembly.md` shard that was never written. Both
scaffolders now import this module so birth and migration converge on one shape.

Primarily an import target for init-sanctum.py / migrate-sidecar-to-v2.py. It
also exposes a small recovery CLI — `_sanctum_seed.py --out DIR --skill-path
DIR` — that re-seeds just the access-boundaries + creed shards into an existing
sanctum dir (the "if a shard went missing, re-seed it" recovery path). It writes
ONLY into the caller-supplied output directory; it never touches the live
sanctum unless that is the dir you point it at.

Usage:
    _sanctum_seed.py --out DIR [--skill-path DIR] [--project-root DIR]
    _sanctum_seed.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# access-boundaries.md (the loaded-first Dominion contract)
# ---------------------------------------------------------------------------

ACCESS_BOUNDARIES_TEMPLATE = "ACCESS-BOUNDARIES-template.md"


def render_access_boundaries(assets_dir: Path, variables: dict) -> str | None:
    """Render the access-boundaries.md body from its asset template.

    Returns the substituted text, or None if the template is missing (caller
    decides how to handle the absence). Generalizing placeholders like
    `{project_root}` are substituted from `variables`.
    """
    template_path = assets_dir / ACCESS_BOUNDARIES_TEMPLATE
    if not template_path.exists():
        return None
    text = template_path.read_text(encoding="utf-8")
    for key, value in variables.items():
        text = text.replace(f"{{{key}}}", value)
    return text


def write_access_boundaries(out_dir: Path, assets_dir: Path, variables: dict) -> str | None:
    """Write access-boundaries.md into out_dir from the template.

    Returns the output filename written, or None if the template was missing.
    NEVER overwrites a file the caller already preserved/copied — the caller is
    responsible for not invoking this when a bespoke access-boundaries.md is
    being preserved verbatim instead.
    """
    body = render_access_boundaries(assets_dir, variables)
    if body is None:
        return None
    (out_dir / "access-boundaries.md").write_text(body, encoding="utf-8")
    return "access-boundaries.md"


# ---------------------------------------------------------------------------
# Creed sharding (lifted verbatim from migrate-sidecar-to-v2.py so both
# scaffolders shard the source creed identically)
# ---------------------------------------------------------------------------

SECTION_SPLIT_RE = re.compile(r"(?m)^(?=##\s)")

# Map source creed "## " headings to shard destinations. Headings not listed
# stay in the core (they are reproduced by the CREED-template anyway). The
# always-load CORE comes from the template; the shards carry the heavy
# disciplines + incident narratives lifted out of the source creed verbatim.
SHARD_ROUTING = {
    "creed-workshop-capture.md": ["Workshop Capture Discipline"],
    "creed-disciplines.md": [
        "Research Discipline",
        "Thematic Discipline",
        "Catalog Verification Discipline",
        "Document State Marker Discipline",
        "Hedge Preservation Discipline",
        "Pre-Presentation Review",
        "Milestone Auto-Save",
    ],
    "creed-package-assembly.md": ["Package Assembly Rule"],
}


def _heading_of(section: str) -> str:
    return section.splitlines()[0].strip() if section.strip() else ""


def shard_creed(creed_text: str) -> dict[str, str]:
    """Slice the source creed into shard files by heading prefix-match.

    Returns {shard_filename: content}. Every source "## " discipline section is
    routed to exactly one shard; the incident-heavy narrative content rides
    along inside its discipline shard. A creed-incident-log.md is also produced
    aggregating the verbose "Recurring failure pattern" narratives so they can
    be referenced without loading.
    """
    parts = SECTION_SPLIT_RE.split(creed_text)
    sections = [p for p in parts if p.strip().startswith("##")]

    shard_content: dict[str, list[str]] = {name: [] for name in SHARD_ROUTING}
    incident_sections: list[str] = []

    for section in sections:
        heading = _heading_of(section)
        heading_body = heading.lstrip("#").strip()
        routed = False
        for shard_name, prefixes in SHARD_ROUTING.items():
            if any(heading_body.startswith(p) for p in prefixes):
                shard_content[shard_name].append(section.rstrip() + "\n")
                routed = True
                break
        if not routed:
            # Mission / Principles live in the core template; skip duplicating.
            continue
        # Collect the verbose failure-pattern narrative for the incident log.
        if "Recurring failure pattern" in section or "instance" in heading_body.lower():
            incident_sections.append(section.rstrip() + "\n")

    out: dict[str, str] = {}
    for shard_name, secs in shard_content.items():
        if not secs:
            continue
        title = shard_name.replace("creed-", "").replace(".md", "").replace("-", " ").title()
        header = (
            f"# Mac — Creed Shard: {title}\n\n"
            "> Loaded on demand. Lifted verbatim from the skill creed. The "
            "always-loaded CORE (Mission, Three Laws, Sacred Truth, Package "
            "Assembly core) lives in `CREED.md`.\n"
        )
        out[shard_name] = header + "\n" + "\n".join(secs).rstrip() + "\n"

    # Incident log — verbose narratives, NOT loaded on rebirth.
    incident_body = "\n".join(incident_sections).rstrip() if incident_sections else (
        "_No verbose incident narratives extracted._"
    )
    out["creed-incident-log.md"] = (
        "# Mac — Creed Incident Log\n\n"
        "> NOT loaded on rebirth. Verbose narratives behind the documented "
        "discipline-failure incidents — the 'why' archive. The rules themselves "
        "live in the creed shards; this is reference only.\n\n"
        + incident_body
        + "\n"
    )
    return out


def write_creed_shards(out_dir: Path, references_dir: Path) -> list[str]:
    """Seed the on-demand creed shards + incident log from references/creed.md.

    Returns the list of shard filenames written. If references/creed.md is
    missing, writes nothing and returns an empty list (caller decides whether
    that is acceptable for its context).
    """
    creed_src = references_dir / "creed.md"
    if not creed_src.exists():
        return []
    written: list[str] = []
    for shard_name, shard_text in shard_creed(
        creed_src.read_text(encoding="utf-8")
    ).items():
        (out_dir / shard_name).write_text(shard_text, encoding="utf-8")
        written.append(shard_name)
    return written


# ---------------------------------------------------------------------------
# Recovery CLI — re-seed access-boundaries + creed shards into a target dir
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Re-seed Mac's access-boundaries.md + creed shards into a target "
            "sanctum directory. Shared seeding logic; init-sanctum.py and "
            "migrate-sidecar-to-v2.py import this module. As a CLI it covers the "
            "'a shard went missing, re-seed it' recovery path."
        )
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Target directory to seed into (the sanctum dir, or a temp test dir).",
    )
    parser.add_argument(
        "--skill-path",
        default=None,
        help=(
            "Skill dir (assets/ + references/ live here). Default: inferred as "
            "the parent of this script's directory."
        ),
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root, substituted for {project_root} placeholders.",
    )
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format."
    )
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    if not out_dir.is_dir():
        print(f"ERROR: --out dir not found: {out_dir}", file=sys.stderr)
        return 2
    skill_path = (
        Path(args.skill_path).resolve()
        if args.skill_path
        else Path(__file__).resolve().parent.parent
    )
    assets_dir = skill_path / "assets"
    references_dir = skill_path / "references"
    variables = {"project_root": str(Path(args.project_root).resolve())}

    written: list[str] = []
    ab = write_access_boundaries(out_dir, assets_dir, variables)
    if ab:
        written.append(ab)
    written.extend(write_creed_shards(out_dir, references_dir))

    result = {"status": "seeded", "out_dir": str(out_dir), "written": written}
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Seeded {len(written)} file(s) into {out_dir}:")
        for name in written:
            print(f"  + {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
