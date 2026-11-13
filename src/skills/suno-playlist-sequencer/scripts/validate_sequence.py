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
  - With --archive PATH (the playlist's audio archive,
    docs/audio-analysis/playlists/<album-slug>.json): adds `seams`, the measured
    transition across every adjacent pair of the proposed order (or the current one):
    tempo folded to felt BPM with its `bpm_quality` (smooth < 3%, ok < 6%, else
    "jump (N%)"; `unknown` when a tempo read 0), the loudness step with its
    `loudness_quality`, and the key relation. Describe seams with these labels; new
    seams a reorder creates are covered too. A pair with a track the archive has no
    analysis for carries `missing` instead of labels: that seam is unmeasured. A
    playlist `felt_bpm:` that isn't a positive number is not applied and is listed
    under `felt_bpm_ignored`.
  - With --order FILE --write: rewrites the YAML's `tracks:` list in the new
    order, only if every check passed. Everything outside the list (album,
    audio_dir, comments above it, later keys) is kept verbatim, and each track
    keeps its own text: quoting, field order and the comment lines just above it.
    The report's `rewrite` says which happened: `verbatim`, or `re-rendered` when
    the list isn't a plain `- ` block list (a flow-style list, say) and had to be
    written out again, which loses the comments and quoting inside the list.

Locked arcs come from `--locked "A > B > C"` (repeatable) and from an optional
top-level `locked_arcs:` list in the YAML (each item a list of names or an
"A > B > C" string).

The order file has one track name per line. A line that is exactly a track
name is taken as that name, whatever it starts with ("#1 Crush", "- Dash",
"99. Luftballons"). Otherwise blank lines and lines starting with # are
ignored, and leading numbering ("3.", "3)") and "- " are stripped.

Track names must be unique in the playlist: an order names tracks, so two
entries sharing a name can't be told apart and a rewrite would lose one.

Exit codes:
  0 = checks passed (and the YAML was written, with --write)
  1 = a check failed (nothing written)
  2 = error: a usage error, pyyaml not importable (run the script with
      `uv run`), the playlist, order, archive or rationale file missing,
      unreadable or not UTF-8, the YAML has no tracks or a track without a
      name, an empty order file, an --archive that is not a
      playlist-sequencing-data report, an -o folder that can't be created, or
      a --locked arc with fewer than two tracks
"""

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT = "validate-sequence"


def parse_arc(text):
    return [part.strip() for part in str(text).split(">") if part.strip()]


def yaml_arcs(config):
    """(arcs, errors): each `locked_arcs:` item as a list of names; an item under two tracks is an error."""
    arcs, errors = [], []
    items = config.get("locked_arcs") or []
    if not isinstance(items, list):
        items = [items]  # a lone "A > B" string is one arc, not a list of characters
    for i, item in enumerate(items, start=1):
        arc = [str(x).strip() for x in item if str(x).strip()] if isinstance(item, list) else parse_arc(item)
        if len(arc) >= 2:
            arcs.append(arc)
        else:
            errors.append(f"locked_arcs item {i} names fewer than two tracks: {item!r}")
    return arcs, errors


def read_order(text, known=()):
    """Track names from an order file. `known` is the playlist's names: a line that is
    exactly one of them is that track, so a name starting with #, "- " or a number survives."""
    known = set(known)
    names = []
    for line in text.splitlines():
        line = line.strip()
        if line in known:
            names.append(line)
            continue
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
    have = Counter(current)
    if proposed is not None:
        # Two playlist entries sharing a name can't be told apart by an order file, and a
        # rewrite would keep one and lose the other, however many times the order lists it.
        for name, n in have.items():
            if n > 1:
                where = [i + 1 for i, x in enumerate(current) if x == name]
                errors.append(f"duplicated in the playlist: {name} (tracks {', '.join(map(str, where))}); "
                              "give each a unique name before reordering")
    for name, n in Counter(order).items():
        if n > 1 and not (proposed is not None and have[name] > 1):
            where = [i + 1 for i, x in enumerate(order) if x == name]
            errors.append(f"duplicated: {name} (positions {', '.join(map(str, where))})")
    if proposed is not None:
        want = Counter(proposed)
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


def _reorder_items(block_lines, new_order):
    """Reorder a block list's items as written: each item keeps its own text (quoting,
    comments, field order). Comment lines just above an item travel with it. Returns
    None when the block isn't a plain `- ` list whose items each name one track."""
    import yaml

    starts = [i for i, l in enumerate(block_lines) if re.match(r"^\s*- ", l)]  # zero indent is valid YAML
    if not starts:
        return None
    indent = len(block_lines[starts[0]]) - len(block_lines[starts[0]].lstrip())
    starts = [i for i in starts if len(block_lines[i]) - len(block_lines[i].lstrip()) == indent]
    # Each item's text runs from its comment lead-in to the line before the next item's lead-in.
    def lead(i):
        j = i
        while j > 0 and block_lines[j - 1].strip().startswith("#"):
            j -= 1
        return j
    bounds = [lead(i) for i in starts]
    preamble = block_lines[:bounds[0]]
    chunks = [block_lines[b:e] for b, e in zip(bounds, bounds[1:] + [len(block_lines)])]
    trailing = []
    while chunks[-1] and not chunks[-1][-1].strip():  # blank lines after the list stay at the end
        trailing.insert(0, chunks[-1].pop())
    by_name = {}
    for chunk in chunks:
        body = [l for l in chunk if not l.strip().startswith("#")]
        try:
            item = yaml.safe_load("".join(l[indent:] if len(l) > indent else l.lstrip() for l in body))
        except yaml.YAMLError:
            return None
        if not isinstance(item, list) or len(item) != 1 or not isinstance(item[0], dict):
            return None
        name = str(item[0].get("name") or "").strip()
        if not name or name in by_name:
            return None
        while chunk and not chunk[-1].strip():  # one item's trailing blanks are separators, not content
            chunk = chunk[:-1]
        by_name[name] = chunk
    if sorted(by_name) != sorted(new_order):
        return None
    sep = "\n" if any(not l.strip() for c in chunks for l in c) else ""
    out = "".join(preamble)
    for k, n in enumerate(new_order):
        out += "".join(by_name[n]) + (sep if k < len(new_order) - 1 else "")
    return out + "".join(trailing)


def render(original_text, tracks, new_order):
    """(text, verbatim): the YAML text with only the `tracks:` list reordered. `verbatim` is
    False when the list had to be re-rendered, which loses its comments and quoting."""
    import yaml

    lines = original_text.splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if re.match(r"^tracks:\s*(#.*)?$", l)), None)
    if start is None:
        raise ValueError("no top-level `tracks:` key found")
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^[A-Za-z_]", lines[i])), len(lines))
    block = _reorder_items(lines[start + 1:end], new_order)
    verbatim = block is not None
    if block is None:  # not a plain block list: re-render it
        by_name = {}
        for t in tracks:
            by_name.setdefault(str(t["name"]).strip(), t)
        body = yaml.safe_dump([by_name[n] for n in new_order], allow_unicode=True, sort_keys=False,
                              default_flow_style=False, width=10_000)
        block = "".join(f"  {l}\n" for l in body.splitlines())
    tail = lines[end:]
    if not verbatim and tail and not block.endswith("\n\n") and tail[0].strip():
        block += "\n"
    return "".join(lines[:start + 1]) + block + "".join(tail), verbatim


def _sequencing_data():
    """playlist_sequencing_data.py, loaded for its seam math (one home for the thresholds)."""
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("playlist_sequencing_data", here / "playlist_sequencing_data.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _number(value):
    """`value` as a float when it is a real number (YAML `72`, not `"72"` or `true`), else None."""
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def felt_bpm_of(tracks):
    """({name: felt_bpm}, [ignored]) from the playlist's tracks. A `felt_bpm:` that isn't a
    positive number (a quoted "72", zero) is ignored, as playlist_sequencing_data.py ignores it."""
    felt, ignored = {}, []
    for t in tracks:
        raw = t.get("felt_bpm")
        if raw is None:
            continue
        value = _number(raw)
        if value and value > 0:
            felt[str(t["name"]).strip()] = value
        else:
            shown = raw if isinstance(raw, (str, int, float, bool)) else str(raw)  # keep the report JSON-safe
            ignored.append({"name": str(t["name"]).strip(), "value": shown, "reason": "not a positive number"})
    return felt, ignored


def archive_problem(archive):
    """Why `archive` isn't a playlist-sequencing-data report, or None when it is one."""
    if not isinstance(archive, dict) or not isinstance(archive.get("tracks"), list):
        return "it has no `tracks` list"
    if not any(isinstance(t, dict) and str(t.get("name") or "").strip() for t in archive["tracks"]):
        return "none of its tracks has a `name`"
    return None


def seams(order, archive, tracks):
    """Measured transition data for each adjacent pair in `order`, from the archive."""
    data = _sequencing_data()
    by_name = {str(t.get("name")).strip(): t for t in archive.get("tracks") or [] if isinstance(t, dict)}
    felt, _ = felt_bpm_of(tracks)
    out = []

    def unread(t):
        return not t or _number(t.get("bpm")) is None

    for a, b in zip(order, order[1:]):
        ra, rb = by_name.get(a), by_name.get(b)
        if unread(ra) or unread(rb):
            out.append({"from": a, "to": b, "missing": "no analysis for " + (a if unread(ra) else b)})
            continue

        def flat(t, name):
            # Only what the seam math can use: a field of another type reads as absent.
            key = t.get("key") if isinstance(t.get("key"), dict) else {}
            return {**t, "felt_bpm": felt.get(name) or _number(t.get("felt_bpm")),
                    "entry_bpm": _number(t.get("entry_bpm")), "exit_bpm": _number(t.get("exit_bpm")),
                    "exit_camelot": key.get("exit_camelot") or key.get("overall_camelot") or "??",
                    "entry_camelot": key.get("entry_camelot") or key.get("overall_camelot") or "??",
                    "exit_key": key.get("exit") or key.get("overall"),
                    "entry_key": key.get("entry") or key.get("overall")}
        seam = data.transition_between(flat(ra, a), flat(rb, b))
        out.append({"from": a, **seam})
    return out


NEGATED = re.compile(r"\b(?:not|isn't|is\s+not|never|no\s+longer|anything\s+but|far\s+from)\s+(?:\w+\s+){0,2}"
                     r"(?:smooth|seamless|clean|best|strongest|ideal|natural|easy)", re.I)
LEVEL_WORDS = re.compile(r"\b(?:loudness|level|levels|lufs|lu|volume)\b", re.I)
TEMPO_WORDS = re.compile(r"\b(?:tempo|bpm|pace|groove|feel)\b", re.I)
SMOOTH_WORDS = re.compile(r"\b(smooth(?:est|ly)?|seamless(?:ly)?|clean(?:est)?|best|strongest|ideal|natural|easy)\b", re.I)


def slot_table(order, name, archive, tracks, arcs):
    """For each slot `name` could take in `order`, the seams it makes and the one it replaces."""
    base = [t for t in order if t != name]
    rows = []
    for k in range(len(base) + 1):
        prev = base[k - 1] if k > 0 else None
        nxt = base[k] if k < len(base) else None
        trial = ([prev] if prev else []) + [name] + ([nxt] if nxt else [])
        made = seams(trial, archive, tracks)
        replaced = seams([prev, nxt], archive, tracks)[0] if prev and nxt else None
        split = [" > ".join(a) for a in arcs if prev in a and nxt in a and abs(a.index(prev) - a.index(nxt)) == 1]
        jumps = sum(1 for sm in made for key in ("bpm_quality", "loudness_quality") if "jump" in str(sm.get(key) or ""))
        was = sum(1 for key in ("bpm_quality", "loudness_quality") if replaced and "jump" in str(replaced.get(key) or ""))
        rows.append({"position": k + 1, "after": prev, "before": nxt, "seams": made,
                     "replaces": replaced, "splits_locked_arc": split,
                     "jump_labels_made": jumps, "jump_labels_removed": was, "net_jump_labels": jumps - was})
    return rows


def slot_summary(rows):
    """Comparative facts across slots, so "the only slot that..." claims come from here."""
    ok = [r for r in rows if not r["splits_locked_arc"]]
    best = min((r["net_jump_labels"] for r in ok), default=None)
    return {
        "note": "slots_at_fewest and slots_adding_no_jump_label count only slots that keep every locked arc; "
                "net_by_slot lists every slot, arc-splitting ones included",
        "slots_adding_no_jump_label": [r["position"] for r in ok if r["jump_labels_made"] == 0],
        "fewest_net_jump_labels": best,
        "slots_at_fewest": [r["position"] for r in ok if r["net_jump_labels"] == best],
        "slots_splitting_a_locked_arc": [r["position"] for r in rows if r["splits_locked_arc"]],
        "net_by_slot": {str(r["position"]): r["net_jump_labels"] for r in rows},
    }


SMOOTHNESS = re.compile(r"\b(?:smooth(?:est|ly)?|seamless(?:ly)?|clean(?:est)?)\b", re.I)
SLOT_REF = re.compile(r"\b(?:slot|position)\s+(\d+)\b", re.I)


PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
# Private-use characters that wrap a track name's token while a rationale is read.
MASK_OPEN, MASK_CLOSE = "\ue000", "\ue001"


def rationale_flags(text, seam_rows, order=None, slot_rows=None):
    """Clauses that call a seam smooth/seamless/clean when its label isn't `smooth`, or call
    a `jump` seam the best or strongest. A clause naming "slot N" with no track pair is read
    against the seams around position N of `order`."""
    flags = []
    # Track names are swapped for tokens before the text is split, so a name holding a
    # comma, " and ", a full stop or a word like "Clean" is neither cut in two nor read
    # as a claim. Longest first, so "One More" is taken before "One".
    names = sorted({str(n) for seam in seam_rows for n in (seam["from"], seam["to"])}, key=len, reverse=True)
    token = {n.lower(): f"{MASK_OPEN}{i}{MASK_CLOSE}" for i, n in enumerate(names)}
    shown = {token[n.lower()]: n for n in names}
    for n in names:
        text = re.sub(r"(?<!\w)" + re.escape(n) + r"(?!\w)", lambda _m, t=token[n.lower()]: t, text, flags=re.I)

    def unmask(s):
        return re.sub(f"{MASK_OPEN}\\d+{MASK_CLOSE}", lambda m: shown.get(m.group(0), m.group(0)), s)

    # Clauses, so a sentence that praises one seam and names another isn't misread.
    clauses = [c.strip() for c in re.split(r"(?<=[.!?;:])\s+|\n+|,\s+|\s+(?:and|but|while|whereas)\s+", text) if c.strip()]
    for masked in clauses:
        clause = unmask(masked)  # reported as written; every match below runs on `masked`
        by_pair = {}
        for seam in seam_rows:
            a, b = token[str(seam["from"]).lower()], token[str(seam["to"]).lower()]
            if a in masked and b in masked:
                ordered = masked.index(a) < masked.index(b)
                pair = frozenset((a, b))
                # The seam named in reading order wins over the reverse direction.
                if pair not in by_pair or (ordered and not by_pair[pair][0]):
                    by_pair[pair] = (ordered, seam)
        if not by_pair and slot_rows:
            # "Slot N" in a slot-table answer is the table's row N: the seams that slot makes.
            for m in SLOT_REF.finditer(masked):
                row = next((r for r in slot_rows if r["position"] == int(m.group(1))), None)
                for seam in (row or {}).get("seams", []):
                    by_pair[frozenset((seam["from"].lower(), seam["to"].lower()))] = (True, seam)
        # Without a slot table, "slot N" is ambiguous (a candidate slot or a position), so it isn't read.
        calls_smooth = bool(SMOOTHNESS.search(masked))
        # A clause about the level ("a smooth loudness step") is judged on the loudness
        # label, one about tempo on the tempo label, one about the whole seam on both.
        about_level = bool(LEVEL_WORDS.search(masked)) and not TEMPO_WORDS.search(masked)
        about_tempo = bool(TEMPO_WORDS.search(masked)) and not LEVEL_WORDS.search(masked)
        # A percentage beside a named seam is the label's own, never one worked out.
        quoted_pct = [float(x) for x in PERCENT.findall(masked)]
        if quoted_pct and by_pair:
            label_pct = [float(x) for _, sm in by_pair.values() for key in ("bpm_quality", "loudness_quality")
                         for x in PERCENT.findall(str(sm.get(key) or ""))]
            for q in quoted_pct:
                if not any(abs(q - lp) < 0.05 for lp in label_pct):
                    seam = next(iter(by_pair.values()))[1]
                    flags.append({"seam": f"{seam['from']} > {seam['to']}", "label": "", "kind": "percentage",
                                  "detail": f"{q}% is not a figure its labels give", "clause": clause})
        if not SMOOTH_WORDS.search(masked) or NEGATED.search(masked):
            continue
        for _, seam in by_pair.values():
            keys = (("loudness_quality",) if about_level else ("bpm_quality",) if about_tempo
                    else ("bpm_quality", "loudness_quality"))
            if seam.get("missing"):
                # No measurement stands behind any praise of this seam.
                flags.append({"seam": f"{seam['from']} > {seam['to']}", "label": "unmeasured", "clause": clause})
                continue
            for key in keys:
                label = str(seam.get(key) or "")
                base = label.split(" (")[0]
                # "smooth" and its kin need a smooth label; "best"/"strongest" only rule out a jump.
                bad = (base not in ("", "smooth")) if (about_level or calls_smooth) else ("jump" in label)
                if bad:
                    flags.append({"seam": f"{seam['from']} > {seam['to']}", "label": label, "clause": clause})
                    break
    return flags


BRIEF_KEYS = ("status", "errors", "locked_arcs", "seams", "moves", "slot_summary", "rationale_flags", "written",
              "rewrite")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("playlist", help="Path to the playlist YAML (docs/{band-slug}-playlist.yaml).")
    parser.add_argument("--order", help="File with the proposed order, one track name per line.")
    parser.add_argument("--locked", action="append", default=[],
                        help='A locked arc as "A > B > C" (repeatable). Adds to the YAML\'s locked_arcs.')
    parser.add_argument("--write", action="store_true",
                        help="Rewrite the YAML in the new order if every check passes (needs --order).")
    parser.add_argument("--archive", help="The playlist's audio archive JSON, or a playlist-sequencing-data report "
                                          "saved with its -o; adds measured `seams` for the order.")
    parser.add_argument("--slot-table", metavar="TRACK",
                        help="With --archive: every slot TRACK could take in the current order, with the seams each makes, "
                             "the seam it replaces and any locked arc it splits.")
    parser.add_argument("--rationale", metavar="FILE",
                        help="With --archive: flag sentences in FILE (the rationale and trade-offs you will return) that call "
                             "a measured `jump` seam smooth, clean or the best, praise a seam with no analysis, or quote "
                             "a percentage its labels don't give. Any flag fails the check.")
    parser.add_argument("-o", "--output", help="Write the JSON report here instead of stdout.")
    parser.add_argument("--brief", action="store_true",
                        help="Print only status, errors, locked_arcs, seams, moves, slot_summary, rationale_flags, written and rewrite: "
                             "the fields a reply cites, so nothing needs filtering.")

    def usage_error(message):
        # argparse would exit 2 with usage text alone; the caller reads stdout JSON.
        parser.print_usage(sys.stderr)
        print(json.dumps({"script": SCRIPT, "status": "error", "error": f"usage: {message}"}, indent=2))
        raise SystemExit(2)

    parser.error = usage_error
    args = parser.parse_args(argv)

    def emit(report, code):
        if args.brief:
            report = {k: report[k] for k in BRIEF_KEYS if k in report}
        text = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            try:
                Path(args.output).write_text(text + "\n", encoding="utf-8")
            except OSError as exc:  # the report must still reach the caller
                print(f"could not write {args.output} ({exc}); report printed to stdout", file=sys.stderr)
                print(text)
        else:
            print(text)
        return code

    def error(reason):
        return emit({"script": SCRIPT, "status": "error", "error": reason}, 2)

    if args.output:
        try:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            args.output = None
            return error(f"cannot create the folder for -o: {exc}")
    if importlib.util.find_spec("yaml") is None:
        return error("missing-dependency: pyyaml is not importable; run the script with `uv run`, "
                     "which installs it from the script's header")
    import yaml

    path = Path(args.playlist)
    try:
        original = path.read_text(encoding="utf-8")
        config = yaml.safe_load(original) or {}
        order_text = Path(args.order).read_text(encoding="utf-8") if args.order else None
    except UnicodeDecodeError as exc:
        return error(f"not UTF-8 text ({exc}): save the playlist and the order file as UTF-8")
    except (OSError, yaml.YAMLError) as exc:
        return error(str(exc))
    if args.write and order_text is None:
        return error("--write needs --order")
    if not isinstance(config, dict):
        return error(f"{path} must be a mapping with a `tracks:` list")
    tracks = config.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        return error(f"{path} has no `tracks:` list (or it is empty): nothing to check")
    for i, t in enumerate(tracks, start=1):
        # A nameless entry can't be matched to an order, and a rewrite would lose it.
        if not isinstance(t, dict) or not str(t.get("name") or "").strip():
            return error(f"track {i} in {path} has no `name:`; fix it before checking an order")
    current = [str(t["name"]).strip() for t in tracks]
    proposed = read_order(order_text, current) if order_text is not None else None
    if proposed is not None and not proposed:
        return error(f"{args.order} lists no track names")
    cli_arcs = [parse_arc(x) for x in args.locked]
    short = [x for x, a in zip(args.locked, cli_arcs) if len(a) < 2]
    if short:
        return error(f"--locked needs at least two tracks joined by '>': {', '.join(map(repr, short))}")

    arcs, arc_errors = yaml_arcs(config)
    arcs += cli_arcs
    errors, arc_report = check(current, proposed, arcs)
    errors = arc_errors + errors
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
    if args.archive:
        try:
            archive = json.loads(Path(args.archive).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:  # ValueError: not JSON, or not UTF-8
            return error(f"archive unreadable: {exc}")
        problem = archive_problem(archive)
        if problem:
            return error(f"archive is not a playlist-sequencing-data report ({problem}): {args.archive}")
        report["seams"] = seams(proposed if proposed is not None else current, archive, tracks)
        ignored = felt_bpm_of(tracks)[1]
        if ignored:
            report["felt_bpm_ignored"] = ignored
        if args.slot_table:
            if args.slot_table not in current:
                return error(f"--slot-table: {args.slot_table!r} is not in the playlist")
            report["slot_table"] = slot_table(current, args.slot_table, archive, tracks, arcs)
            report["slot_summary"] = slot_summary(report["slot_table"])
        if args.rationale:
            try:
                text = Path(args.rationale).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                return error(f"rationale unreadable: {exc}")
            rows = list(report["seams"])
            for row in report.get("slot_table", []):
                rows += row["seams"] + ([row["replaces"]] if row["replaces"] else [])
            flags = rationale_flags(text, rows, proposed or current, report.get("slot_table"))
            report["rationale_flags"] = flags
            if flags:
                report["status"] = "fail"
                report["errors"] = report["errors"] + [
                    (f"{f['seam']}: {f['detail']}: {f['clause']!r}" if f.get("kind") == "percentage"
                     else f"{f['seam']} is an unmeasured seam (no analysis), praised: {f['clause']!r}"
                     if f["label"] == "unmeasured"
                     else f"{f['seam']} is a {f['label']} seam, called smooth/clean/best: {f['clause']!r}") for f in flags]
                errors = report["errors"]
    elif args.slot_table or args.rationale:
        return error("--slot-table and --rationale need --archive")
    if errors or not args.write:
        return emit(report, 1 if errors else 0)

    try:
        new_text, verbatim = render(original, tracks, proposed)
        reparsed = yaml.safe_load(new_text) or {}
    except (ValueError, yaml.YAMLError) as exc:
        report.update(status="fail", errors=[f"rewrite failed, YAML left unchanged: {exc}"])
        return emit(report, 1)
    same_rest = {k: v for k, v in reparsed.items() if k != "tracks"} == {k: v for k, v in config.items() if k != "tracks"}
    # Every track comes back whole (file, felt_bpm, any other field), not only its name.
    by_name = {str(t["name"]).strip(): t for t in tracks}
    if reparsed.get("tracks") != [by_name[n] for n in proposed] or not same_rest:
        report.update(status="fail", errors=["rewrite did not round-trip, YAML left unchanged"])
        return emit(report, 1)
    try:
        path.write_text(new_text, encoding="utf-8")
    except OSError as exc:
        report.update(status="fail", errors=[f"could not write {path}, YAML left unchanged: {exc}"])
        return emit(report, 1)
    report["written"] = True
    report["rewrite"] = "verbatim" if verbatim else "re-rendered"
    note = "" if verbatim else "; the tracks list was re-rendered, so comments and quoting inside it were not kept"
    print(f"WROTE: {path} ({len(report['moves'])} moves){note}", file=sys.stderr)
    return emit(report, 0)


if __name__ == "__main__":
    sys.exit(main())
