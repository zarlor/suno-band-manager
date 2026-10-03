#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Check a track order against the playlist YAML, and rewrite the YAML only when it passes.

The playlist YAML (docs/{band-slug}-playlist.yaml) is the band's single source
of truth, so a reorder is a batch edit to it. This script is the gate:

  - Without --order: checks the CURRENT order (duplicate entries, locked arcs
    split or out of order). Use it to surface locked arcs before sequencing.
  - With --order FILE: checks the proposed order is a permutation of the
    current tracks (nothing dropped, duplicated, or unknown) and that every
    locked arc stays together and in order. Prints a preview of the moves.
  - With --order FILE --write: rewrites the YAML's `tracks:` list in the new
    order, only if every check passed. Everything outside the list (album,
    audio_dir, comments above it, later keys) is kept verbatim, and each track
    keeps all its fields. Comments inside the list are not kept.

Locked arcs come from `--locked "A > B > C"` (repeatable) and from an optional
top-level `locked_arcs:` list in the YAML (each item a list of names or an
"A > B > C" string).

The order file has one track name per line. Blank lines and lines starting
with # are ignored; leading numbering ("3.", "3)") and "- " are stripped.

Exit codes:
  0 = checks passed (and the YAML was written, with --write)
  1 = a check failed (nothing written)
  2 = error: playlist or order file missing or unreadable
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT = "validate-sequence"


def parse_arc(text):
    return [part.strip() for part in str(text).split(">") if part.strip()]


def yaml_arcs(config):
    arcs = []
    for item in config.get("locked_arcs") or []:
        arc = [str(x).strip() for x in item] if isinstance(item, list) else parse_arc(item)
        if len(arc) >= 2:
            arcs.append(arc)
    return arcs


def read_order(text):
    names = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^(\d+[.)]\s*|-\s+)", "", line).strip()
        if line:
            names.append(line)
    return names


def arc_status(order, arc):
    """'intact', 'split', 'out-of-order', or 'unknown-track' for one locked arc in an order."""
    positions = []
    for name in arc:
        if name not in order:
            return "unknown-track"
        positions.append(order.index(name))
    if positions != sorted(positions):
        return "out-of-order"
    if positions[-1] - positions[0] != len(arc) - 1:
        return "split"
    return "intact"


def check(current, proposed, arcs):
    """Errors (each naming the track) and per-arc status for an order.

    `proposed` None checks the current order on its own."""
    errors = []
    order = current if proposed is None else proposed
    for name, n in Counter(order).items():
        if n > 1:
            where = [i + 1 for i, x in enumerate(order) if x == name]
            errors.append(f"duplicated: {name} (positions {', '.join(map(str, where))})")
    if proposed is not None:
        have, want = Counter(current), Counter(proposed)
        for name in current:
            if name not in want:
                errors.append(f"dropped: {name} is in the playlist but not in the new order")
        for name in dict.fromkeys(proposed):
            if name not in have:
                errors.append(f"unknown: {name} is not in the playlist (check the spelling)")
    arc_report = []
    for arc in arcs:
        status = arc_status(order, arc)
        arc_report.append({"tracks": arc, "status": status})
        if status == "unknown-track":
            missing = [n for n in arc if n not in current]
            errors.append(f"locked arc names a track not in the playlist: {', '.join(missing)}")
        elif status != "intact":
            errors.append(f"locked arc {status}: {' > '.join(arc)}")
    return errors, arc_report


def moves(current, proposed):
    out = []
    for new_pos, name in enumerate(proposed, start=1):
        if name in current:
            old_pos = current.index(name) + 1
            if old_pos != new_pos:
                out.append({"name": name, "from": old_pos, "to": new_pos})
    return out


def render(original_text, tracks, new_order):
    """The YAML text with only the `tracks:` list reordered."""
    import yaml

    lines = original_text.splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if re.match(r"^tracks:\s*(#.*)?$", l)), None)
    if start is None:
        raise ValueError("no top-level `tracks:` key found")
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^[A-Za-z_]", lines[i])), len(lines))
    by_name = {}
    for t in tracks:
        by_name.setdefault(t["name"], t)
    body = yaml.safe_dump([by_name[n] for n in new_order], allow_unicode=True, sort_keys=False,
                          default_flow_style=False, width=10_000)
    block = "".join(f"  {l}\n" for l in body.splitlines())
    tail = lines[end:]
    if tail and not block.endswith("\n\n") and tail[0].strip():
        block += "\n"
    return "".join(lines[:start + 1]) + block + "".join(tail)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("playlist", help="Path to the playlist YAML (docs/{band-slug}-playlist.yaml).")
    parser.add_argument("--order", help="File with the proposed order, one track name per line.")
    parser.add_argument("--locked", action="append", default=[],
                        help='A locked arc as "A > B > C" (repeatable). Adds to the YAML\'s locked_arcs.')
    parser.add_argument("--write", action="store_true",
                        help="Rewrite the YAML in the new order if every check passes (needs --order).")
    parser.add_argument("-o", "--output", help="Write the JSON report here instead of stdout.")
    args = parser.parse_args(argv)

    def emit(report, code):
        text = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        return code

    import yaml

    path = Path(args.playlist)
    try:
        original = path.read_text(encoding="utf-8")
        config = yaml.safe_load(original) or {}
        tracks = [t for t in config.get("tracks") or [] if isinstance(t, dict) and t.get("name")]
        proposed = read_order(Path(args.order).read_text(encoding="utf-8")) if args.order else None
    except (OSError, yaml.YAMLError) as exc:
        return emit({"script": SCRIPT, "status": "error", "error": str(exc)}, 2)
    if args.write and proposed is None:
        return emit({"script": SCRIPT, "status": "error", "error": "--write needs --order"}, 2)

    current = [t["name"] for t in tracks]
    arcs = yaml_arcs(config) + [a for a in (parse_arc(x) for x in args.locked) if len(a) >= 2]
    errors, arc_report = check(current, proposed, arcs)
    report = {
        "script": SCRIPT,
        "status": "fail" if errors else "ok",
        "playlist": str(path),
        "track_count": len(current),
        "errors": errors,
        "locked_arcs": arc_report,
        "moves": moves(current, proposed) if proposed is not None else [],
        "written": False,
    }
    if proposed is not None and not errors:
        report["unchanged"] = len(current) - len(report["moves"])
    if errors or not args.write:
        return emit(report, 1 if errors else 0)

    try:
        new_text = render(original, tracks, proposed)
        reparsed = yaml.safe_load(new_text) or {}
    except (ValueError, yaml.YAMLError) as exc:
        report.update(status="fail", errors=[f"rewrite failed, YAML left unchanged: {exc}"])
        return emit(report, 1)
    same_rest = {k: v for k, v in reparsed.items() if k != "tracks"} == {k: v for k, v in config.items() if k != "tracks"}
    if [t.get("name") for t in reparsed.get("tracks") or []] != proposed or not same_rest:
        report.update(status="fail", errors=["rewrite did not round-trip, YAML left unchanged"])
        return emit(report, 1)
    path.write_text(new_text, encoding="utf-8")
    report["written"] = True
    print(f"WROTE: {path} ({len(report['moves'])} moves)", file=sys.stderr)
    return emit(report, 0)


if __name__ == "__main__":
    sys.exit(main())
