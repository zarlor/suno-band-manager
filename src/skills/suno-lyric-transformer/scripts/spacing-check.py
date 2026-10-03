#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check that a transform kept the writer's spacing verbatim.

The writer's indentation, internal spacing ("Day   by   Day"), line breaks and
blank lines are authored. A transform may add metatags, section tags and blank
lines at section breaks, plus the word and line edits it reports. Everything
else in the writer's lines must come through unchanged.

How it compares: tag-only lines, and bracket tags placed at the start or end of
a line, are set aside on both sides. The remaining lines are aligned on their
words, then compared whitespace-exact.

  - whitespace-only change on a line (indentation, internal spacing) -> high
  - trailing-whitespace-only change -> low
  - a writer's blank line removed -> high
  - blank lines added (section breaks) -> counted, not a finding
  Gaps are compared only where two neighbouring writer lines are still
  neighbours; a gap inside an edited stretch shows up as that line edit.
  - word or line edits -> info, one finding each, so every edit can be checked
    against the reported changes; with --word-fidelity, any change to the
    writer's word sequence -> high

It also reports flat_saved_chars: how many characters a flattened copy of the
transformed lyrics would save (indentation and trailing whitespace stripped,
internal runs collapsed to one space, blank-line runs collapsed to one). With
--flatten it returns that copy as flat_copy. The flat copy is only ever a paste
aid for Suno's lyrics field; the spaced version stays canonical.

Usage:
    uv run spacing-check.py --original orig.txt --transformed trans.txt
    uv run spacing-check.py --original-text "..." --transformed-text "..."
    uv run spacing-check.py --original orig.txt --transformed trans.txt --word-fidelity
    uv run spacing-check.py --original orig.txt --transformed trans.txt --flatten
"""

import argparse
import difflib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_NAME = "spacing-check"
VERSION = "1.0.0"

TAG_ONLY_LINE = re.compile(r'^\s*(?:\[[^\]]*\]\s*)+$')
LEADING_TAGS = re.compile(r'^(\s*)(?:\[[^\]]*\]\s*)+(?=\S)')
TRAILING_TAGS = re.compile(r'(?<=\S)(?:\s*\[[^\]]*\])+\s*$')


def normalize_newlines(text: str) -> str:
    """Line-ending style is not authored spacing; compare on LF."""
    return text.replace('\r\n', '\n').replace('\r', '\n')


def core_lines(text: str) -> list[tuple[int, str]]:
    """Return (1-based line number, line) with bracket tags set aside."""
    out = []
    for n, line in enumerate(normalize_newlines(text).split('\n'), 1):
        if line.strip() and TAG_ONLY_LINE.match(line):
            continue
        line = LEADING_TAGS.sub(r'\1', line)
        line = TRAILING_TAGS.sub('', line)
        out.append((n, line))
    return out


def squash(line: str) -> str:
    """Whitespace-insensitive form used only for alignment."""
    return ' '.join(line.split())


def classify_whitespace_change(original: str, transformed: str) -> str:
    """Name what changed when two lines differ only in whitespace."""
    lead_o = original[:len(original) - len(original.lstrip())]
    lead_t = transformed[:len(transformed) - len(transformed.lstrip())]
    if lead_o != lead_t:
        return "indentation"
    if original.strip() != transformed.strip():
        return "internal_spacing"
    return "trailing_whitespace"


def flatten(text: str) -> str:
    """A flat paste copy: no indentation, single internal spaces, single blank lines."""
    lines = [' '.join(line.split()) for line in normalize_newlines(text).split('\n')]
    out = []
    for line in lines:
        if not line and out and not out[-1]:
            continue
        out.append(line)
    return '\n'.join(out)


def gaps_between(content_pos: list[int]) -> list[int]:
    """Blank lines between each pair of consecutive content lines."""
    return [content_pos[k + 1] - content_pos[k] - 1 for k in range(len(content_pos) - 1)]


def check_spacing(original: str, transformed: str, word_fidelity: bool = False) -> dict:
    orig = core_lines(original)
    trans = core_lines(transformed)
    o_pos = [i for i, (_, line) in enumerate(orig) if line.strip()]
    t_pos = [i for i, (_, line) in enumerate(trans) if line.strip()]
    a = [squash(orig[i][1]) for i in o_pos]
    b = [squash(trans[i][1]) for i in t_pos]

    findings = []
    whitespace_changes = []
    text_changes = []
    pairs = {}  # writer content index -> transformed content index

    # 1. Align the writer's content lines on their words; compare whitespace-exact.
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                pairs[i1 + k] = j1 + k
                (on, ol), (tn, tl) = orig[o_pos[i1 + k]], trans[t_pos[j1 + k]]
                if ol != tl:
                    whitespace_changes.append({
                        "kind": classify_whitespace_change(ol, tl),
                        "original_line": on, "transformed_line": tn,
                        "original": ol, "transformed": tl,
                    })
            continue
        o_text = [orig[o_pos[i]] for i in range(i1, i2)]
        t_text = [trans[t_pos[j]] for j in range(j1, j2)]
        text_changes.append({
            "type": {"replace": "modified", "delete": "removed", "insert": "added"}[tag],
            "original_lines": [n for n, _ in o_text],
            "transformed_lines": [n for n, _ in t_text],
            "original": [line for _, line in o_text],
            "transformed": [line for _, line in t_text],
        })

    # 2. Vertical gaps: where two neighbouring writer lines both survive as
    #    neighbours, the blank lines between them must not shrink.
    o_gaps = gaps_between(o_pos)
    t_gaps = gaps_between(t_pos)
    blank_removed = blank_added = 0
    gap_changes = []
    for k, o_gap in enumerate(o_gaps):
        j = pairs.get(k)
        if j is None or pairs.get(k + 1) != j + 1:
            continue
        t_gap = t_gaps[j]
        if t_gap < o_gap:
            blank_removed += o_gap - t_gap
            gap_changes.append({"after_original_line": orig[o_pos[k]][0],
                                "original_blank_lines": o_gap, "transformed_blank_lines": t_gap})
        elif t_gap > o_gap:
            blank_added += t_gap - o_gap

    for c in whitespace_changes:
        low = c["kind"] == "trailing_whitespace"
        findings.append({
            "severity": "low" if low else "high",
            "category": "spacing",
            "location": {"original_line": c["original_line"], "transformed_line": c["transformed_line"]},
            "issue": f"Writer's {c['kind'].replace('_', ' ')} changed: {c['original']!r} became {c['transformed']!r}.",
            "fix": "Restore the writer's line exactly as given.",
        })

    for g in gap_changes:
        findings.append({
            "severity": "high",
            "category": "spacing",
            "location": {"original_line": g["after_original_line"]},
            "issue": f"Writer's gap after line {g['after_original_line']} shrank from {g['original_blank_lines']} to {g['transformed_blank_lines']} blank line(s).",
            "fix": "Restore the writer's vertical gaps; add blank lines at section breaks only, never take theirs away.",
        })

    for c in text_changes:
        findings.append({
            "severity": "info",
            "category": "edit",
            "location": {"original_lines": c["original_lines"], "transformed_lines": c["transformed_lines"]},
            "issue": f"Line edit ({c['type']}): {c['original']} -> {c['transformed']}.",
            "fix": "Confirm this edit is listed in the reported changes.",
        })

    words_changed = False
    if word_fidelity:
        ow = [w for _, line in orig for w in line.split()]
        tw = [w for _, line in trans for w in line.split()]
        if ow != tw:
            words_changed = True
            sm = difflib.SequenceMatcher(None, ow, tw, autojunk=False)
            first = next(op for op in sm.get_opcodes() if op[0] != 'equal')
            _, i1, i2, j1, j2 = first
            findings.append({
                "severity": "high",
                "category": "word_fidelity",
                "issue": f"Word Fidelity: writer's words changed, first at word {i1 + 1}: {' '.join(ow[i1:i2]) or '(none)'!r} -> {' '.join(tw[j1:j2]) or '(none)'!r}.",
                "fix": "In WF mode keep the writer's exact words; only add structure.",
            })

    flat = flatten(transformed)
    return {
        "findings": findings,
        "metrics": {
            "writer_lines": len(o_pos),
            "whitespace_changes": len([c for c in whitespace_changes if c["kind"] != "trailing_whitespace"]),
            "trailing_whitespace_changes": len([c for c in whitespace_changes if c["kind"] == "trailing_whitespace"]),
            "blank_lines_removed": blank_removed,
            "blank_lines_added": blank_added,
            "line_edits": len(text_changes),
            "word_fidelity_checked": word_fidelity,
            "word_fidelity_broken": words_changed,
            "flat_saved_chars": len(normalize_newlines(transformed)) - len(flat),
        },
        "flat_copy": flat,
    }


def build_report(result: dict, include_flat: bool, skill_path: str = "") -> dict:
    findings = result["findings"]
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        severity_counts[f["severity"]] += 1
    if severity_counts["high"] or severity_counts["critical"]:
        status = "fail"
    elif severity_counts["low"] or severity_counts["medium"]:
        status = "warning"
    else:
        status = "pass"
    report = {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "skill_path": skill_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "metrics": result["metrics"],
        "findings": findings,
        "summary": {"total": len(findings), **severity_counts},
    }
    if include_flat:
        report["flat_copy"] = result["flat_copy"]
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Check that a transform kept the writer's spacing verbatim.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --original orig.txt --transformed trans.txt
  %(prog)s --original-text "Day   by   Day" --transformed-text "[Verse]\\nDay   by   Day"
  %(prog)s --original orig.txt --transformed trans.txt --word-fidelity
  %(prog)s --original orig.txt --transformed trans.txt --flatten

Exit codes: 0=pass, 1=spacing changed (fail/warning), 2=error
        """
    )
    parser.add_argument("--original", help="Path to the writer's source text")
    parser.add_argument("--transformed", help="Path to the transformed lyrics")
    parser.add_argument("--original-text", help="Writer's source text directly (literal \\n = newline)")
    parser.add_argument("--transformed-text", help="Transformed lyrics directly (literal \\n = newline)")
    parser.add_argument("--word-fidelity", action="store_true", help="Also require the writer's exact word sequence (WF mode)")
    parser.add_argument("--flatten", action="store_true", help="Include flat_copy (paste aid only; the spaced version stays canonical)")
    parser.add_argument("-o", "--output", help="Output file path (defaults to stdout)")
    parser.add_argument("--skill-path", default="", help="Skill path for report context")
    args = parser.parse_args()

    if args.original_text is not None and args.transformed_text is not None:
        original = args.original_text.replace('\\n', '\n')
        transformed = args.transformed_text.replace('\\n', '\n')
    elif args.original and args.transformed:
        paths = [Path(args.original), Path(args.transformed)]
        for p in paths:
            if not p.exists():
                print(f"Error: File not found: {p}", file=sys.stderr)
                sys.exit(2)
        original, transformed = (p.read_text(encoding="utf-8") for p in paths)
    else:
        print("Error: Provide --original and --transformed files, or --original-text and --transformed-text.", file=sys.stderr)
        sys.exit(2)

    result = check_spacing(original, transformed, args.word_fidelity)
    report = build_report(result, args.flatten, args.skill_path)
    output_json = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
    else:
        print(output_json)
    sys.exit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
