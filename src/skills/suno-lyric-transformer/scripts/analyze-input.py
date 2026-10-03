#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Pre-analyze raw input text to extract deterministic metrics before LLM processing.

Detects existing structure, counts lines/words/characters, finds repeated phrases,
lists line-ending suffix matches (rhyme candidates only -- spelling is not sound),
classifies each line's script (Latin / non-Latin), flags unbroken prose, records
the writer's spatial layout (indentation, internal space runs, blank-line gaps),
and estimates needed structure.

Usage:
    uv run analyze-input.py <text-file> [options]

    # Analyze input from a file
    uv run analyze-input.py input.txt

    # Analyze from text argument
    uv run analyze-input.py --text "Some raw lyrics text"

    # Output to file
    uv run analyze-input.py input.txt -o results.json
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
from suno_constants import SUNO_LYRICS_HARD_LIMIT, SUNO_LYRICS_QUALITY_BUDGET

SCRIPT_NAME = "analyze-input"
VERSION = "1.1.0"


def find_metatags(text: str) -> list[str]:
    """Find all metatag-style brackets in text."""
    return re.findall(r'\[([^\]]+)\]', text)


def find_repeated_phrases(text: str, min_words: int = 3, min_count: int = 2) -> list[dict]:
    """Find exact phrase matches of min_words+ words appearing min_count+ times."""
    lines = text.split('\n')
    # Collect all non-empty, non-tag lines
    content_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not re.match(r'^\[.*\]$', stripped):
            content_lines.append(stripped)

    # Build n-grams from all content
    all_words = []
    for line in content_lines:
        words = re.findall(r"[a-zA-Z']+", line.lower())
        all_words.extend(words)

    phrases = Counter()
    for n in range(min_words, min(8, len(all_words) + 1)):
        for i in range(len(all_words) - n + 1):
            phrase = " ".join(all_words[i:i + n])
            phrases[phrase] += 1

    # Filter and deduplicate (remove sub-phrases if a longer phrase has same count)
    results = {}
    for phrase, count in phrases.items():
        if count >= min_count:
            results[phrase] = count

    # Remove sub-phrases where a longer phrase has the same count
    filtered = {}
    sorted_phrases = sorted(results.keys(), key=len, reverse=True)
    for phrase in sorted_phrases:
        count = results[phrase]
        # Check if this is a sub-phrase of an already-kept longer phrase with same count
        is_sub = False
        for kept in filtered:
            if phrase in kept and filtered[kept] == count:
                is_sub = True
                break
        if not is_sub:
            filtered[phrase] = count

    return [{"phrase": p, "count": c} for p, c in sorted(filtered.items(), key=lambda x: -x[1])]


def find_suffix_matches(text: str) -> list[dict]:
    """List line-ending words that share their last 2-3 letters.

    This is an orthographic candidate list, not a rhyme judgment: love/move
    match here and through/blue do not. The model judges rhyme strength.
    """
    lines = text.split('\n')
    content_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not re.match(r'^\[.*\]$', stripped):
            content_lines.append(stripped)

    # Extract last word of each line
    line_endings = []
    for i, line in enumerate(content_lines):
        words = re.findall(r"[a-zA-Z']+", line)
        if words:
            line_endings.append((i, words[-1].lower()))

    pairs = []
    seen = set()

    for idx in range(len(line_endings)):
        # Check consecutive and alternating lines
        for offset in (1, 2):
            if idx + offset < len(line_endings):
                i, word_a = line_endings[idx]
                j, word_b = line_endings[idx + offset]

                if word_a == word_b:
                    continue

                # Check if last 2 or 3 characters match
                match_len = 0
                if len(word_a) >= 2 and len(word_b) >= 2 and word_a[-2:] == word_b[-2:]:
                    match_len = 2
                if len(word_a) >= 3 and len(word_b) >= 3 and word_a[-3:] == word_b[-3:]:
                    match_len = 3

                if match_len > 0:
                    pair_key = tuple(sorted([word_a, word_b]))
                    if pair_key not in seen:
                        seen.add(pair_key)
                        pairs.append({
                            "words": [word_a, word_b],
                            "ending_match": word_a[-match_len:],
                            "pattern": "consecutive" if offset == 1 else "alternating"
                        })

    return pairs


TAG_ONLY_LINE = re.compile(r'^\s*\[[^\]]*\]\s*$')

# Unbroken prose: running text with few or no poem-style line breaks.
# Free verse with long lines averages well under this many words per line.
PROSE_WORDS_PER_LINE = 25


def classify_script(line: str) -> str:
    """Classify a line's letters as latin, non_latin, mixed, or none."""
    latin = non_latin = 0
    for ch in line:
        if not ch.isalpha():
            continue
        try:
            name = unicodedata.name(ch)
        except ValueError:
            name = ""
        if name.startswith("LATIN"):
            latin += 1
        else:
            non_latin += 1
    if latin and non_latin:
        return "mixed"
    if latin:
        return "latin"
    if non_latin:
        return "non_latin"
    return "none"


def analyze_scripts(lines: list[str]) -> dict:
    """Per-line script class for content lines (1-based line numbers)."""
    by_class = {"latin": [], "non_latin": [], "mixed": []}
    for n, line in enumerate(lines, 1):
        if not line.strip() or TAG_ONLY_LINE.match(line):
            continue
        cls = classify_script(line)
        if cls in by_class:
            by_class[cls].append(n)
    has_latin = bool(by_class["latin"] or by_class["mixed"])
    has_non_latin = bool(by_class["non_latin"] or by_class["mixed"])
    if has_latin and has_non_latin:
        script_type = "mixed"
    elif has_non_latin:
        script_type = "non_latin"
    elif has_latin:
        script_type = "latin"
    else:
        script_type = "none"
    return {
        "script_type": script_type,
        "mixed_script": script_type == "mixed",
        "script_lines": by_class,
    }


def analyze_spatial_layout(lines: list[str]) -> dict:
    """Record the writer's authored spacing so it can be carried verbatim.

    Leading whitespace, internal runs of 2+ whitespace characters (or any tab),
    and blank-line gaps are reported with 1-based line numbers. Nothing here
    is a defect: it is the layout the transform must preserve.
    """
    indented, internal_runs = [], []
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if line[:1].isspace():
            indented.append(n)
        core = line.strip()
        if re.search(r'\s{2,}|\t', core):
            internal_runs.append(n)

    gaps = []  # blank-line runs between content lines
    run_start, run_len, seen_content = None, 0, False
    for n, line in enumerate(lines, 1):
        if line.strip():
            if run_len and seen_content:
                gaps.append({"after_line": run_start - 1, "blank_lines": run_len})
            run_start, run_len, seen_content = None, 0, True
        else:
            if run_len == 0:
                run_start = n
            run_len += 1
    gap_sizes = sorted({g["blank_lines"] for g in gaps})
    irregular_gaps = len(gap_sizes) > 1 or any(size > 1 for size in gap_sizes)
    return {
        "has_spatial_layout": bool(indented or internal_runs or irregular_gaps),
        "indented_lines": indented,
        "internal_space_run_lines": internal_runs,
        "blank_line_gaps": gaps,
        "irregular_gaps": irregular_gaps,
    }


def estimate_structure(line_count: int) -> dict:
    """Estimate structure category and needed sections from line count."""
    if line_count < 16:
        return {
            "estimated_structure": "short",
            "estimated_sections_needed": max(3, line_count // 4)
        }
    elif line_count <= 30:
        return {
            "estimated_structure": "medium",
            "estimated_sections_needed": max(5, line_count // 5)
        }
    else:
        return {
            "estimated_structure": "long",
            "estimated_sections_needed": max(7, line_count // 5)
        }


def analyze_input(text: str) -> dict:
    """Analyze input text and extract metrics."""
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    content_lines = [line.strip() for line in lines if line.strip() and not re.match(r'^\[.*\]$', line.strip())]

    # Detect metatags
    existing_tags = find_metatags(text)
    has_existing_structure = any(
        re.match(r'^(verse|chorus|bridge|intro|outro|pre-chorus|hook|refrain|breakdown|build-up)', tag.lower())
        for tag in existing_tags
    )

    # Counts
    word_count = sum(len(line.split()) for line in content_lines)
    char_count = len(text)

    # sha256 of the exact source text — the LLM cannot compute this by hand,
    # so it is the authoritative value for the LT-STATE source_hash and the
    # headless contract's original_hash (change-tracking / version increment).
    source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    # Repeated phrases
    repeated = find_repeated_phrases(text)

    # Line-ending suffix matches (rhyme candidates; the model judges rhyme)
    suffixes = find_suffix_matches(text)

    # Structure estimate (based on content lines)
    structure = estimate_structure(len(content_lines))

    # Script class per line, unbroken-prose flag, authored spatial layout
    scripts = analyze_scripts(lines)
    words_per_line = word_count / len(content_lines) if content_lines else 0
    unbroken_prose = bool(content_lines) and words_per_line >= PROSE_WORDS_PER_LINE
    spatial = analyze_spatial_layout(lines)

    return {
        "has_existing_structure": has_existing_structure,
        "existing_tags": existing_tags,
        "line_count": len(lines),
        "non_empty_line_count": len(non_empty_lines),
        "word_count": word_count,
        "character_count": char_count,
        "source_hash": source_hash,
        "repeated_phrases": repeated,
        "suffix_matches": suffixes,
        "average_words_per_line": round(words_per_line, 1),
        "unbroken_prose": unbroken_prose,
        **scripts,
        "spatial_layout": spatial,
        **structure
    }


def build_report(analysis: dict, text: str, skill_path: str = "") -> dict:
    """Build the standard output report."""
    findings = []

    if analysis["has_existing_structure"]:
        findings.append({
            "severity": "info",
            "category": "structure",
            "issue": "Input already contains section metatags.",
            "fix": "May need restructuring rather than initial structuring."
        })

    if analysis["character_count"] > SUNO_LYRICS_HARD_LIMIT:
        findings.append({
            "severity": "high",
            "category": "length",
            "issue": f"Character count ({analysis['character_count']}) exceeds Suno's {SUNO_LYRICS_HARD_LIMIT}-character hard limit.",
            "fix": f"Trim to stay under {SUNO_LYRICS_HARD_LIMIT} characters. For best quality, aim for ~{SUNO_LYRICS_QUALITY_BUDGET}."
        })
    elif analysis["character_count"] > SUNO_LYRICS_QUALITY_BUDGET:
        findings.append({
            "severity": "medium",
            "category": "length",
            "issue": f"Character count ({analysis['character_count']}) exceeds the ~{SUNO_LYRICS_QUALITY_BUDGET}-character quality budget.",
            "fix": f"Consider trimming — quality degrades above ~{SUNO_LYRICS_QUALITY_BUDGET} characters. Hard limit is {SUNO_LYRICS_HARD_LIMIT}."
        })

    if analysis["unbroken_prose"]:
        findings.append({
            "severity": "info",
            "category": "structure",
            "issue": f"Input reads as unbroken prose (~{analysis['average_words_per_line']} words per line).",
            "fix": "Segment into candidate lines on clause and breath boundaries before line-based analysis; mark the breaks as inferred, not the writer's."
        })

    if analysis["script_type"] in ("non_latin", "mixed"):
        findings.append({
            "severity": "info",
            "category": "language",
            "issue": f"Script type is {analysis['script_type']} (see script_lines).",
            "fix": "Non-Latin lines get structure and arc work only; syllable, rhyme and cliche checks apply to Latin lines."
        })

    if analysis["spatial_layout"]["has_spatial_layout"]:
        findings.append({
            "severity": "info",
            "category": "spacing",
            "issue": "Writer's text carries authored spacing (indentation, internal space runs, or uneven blank-line gaps).",
            "fix": "Carry every space and blank line verbatim; check the result with spacing-check.py."
        })

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1

    status = "pass"
    if severity_counts["medium"] > 0:
        status = "info"

    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "skill_path": skill_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "metrics": {
            "has_existing_structure": analysis["has_existing_structure"],
            "existing_tags": analysis["existing_tags"],
            "line_count": analysis["line_count"],
            "non_empty_line_count": analysis["non_empty_line_count"],
            "word_count": analysis["word_count"],
            "character_count": analysis["character_count"],
            "source_hash": analysis["source_hash"],
            "repeated_phrases": analysis["repeated_phrases"],
            "suffix_matches": analysis["suffix_matches"],
            "average_words_per_line": analysis["average_words_per_line"],
            "unbroken_prose": analysis["unbroken_prose"],
            "script_type": analysis["script_type"],
            "mixed_script": analysis["mixed_script"],
            "script_lines": analysis["script_lines"],
            "spatial_layout": analysis["spatial_layout"],
            "estimated_structure": analysis["estimated_structure"],
            "estimated_sections_needed": analysis["estimated_sections_needed"],
        },
        "findings": findings,
        "summary": {
            "total": len(findings),
            **severity_counts
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Pre-analyze raw input text to extract deterministic metrics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.txt
  %(prog)s --text "Some raw lyrics\\nAnother line"
  %(prog)s --stdin < input.txt
  %(prog)s input.txt -o results.json --verbose

Metrics extracted:
  - Existing metatags and structure detection
  - Line, word, and character counts
  - sha256 source_hash (authoritative LT-STATE / headless change-tracking hash)
  - Repeated phrases (3+ words, 2+ occurrences)
  - Suffix matches (line endings sharing 2-3 letters; rhyme candidates only)
  - Script type per line (latin / non_latin / mixed) and a mixed_script flag
  - unbroken_prose flag (average words per line >= 25)
  - spatial_layout (indented lines, internal space runs, blank-line gaps)
  - Estimated structure size (short/medium/long)

Exit codes: 0=pass, 1=issues, 2=error
        """
    )
    parser.add_argument("file", nargs="?", help="Path to text file")
    parser.add_argument("--text", help="Text to analyze directly")
    parser.add_argument("--stdin", action="store_true", help="Read text from stdin")
    parser.add_argument("-o", "--output", help="Output file path (defaults to stdout)")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostics to stderr")
    parser.add_argument("--skill-path", default="", help="Skill path for report context")

    args = parser.parse_args()

    text = ""
    if args.text:
        text = args.text.replace('\\n', '\n')
    elif args.stdin:
        text = sys.stdin.read()
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(2)
        text = file_path.read_text()
    else:
        parser.print_help()
        sys.exit(2)

    if args.verbose:
        print(f"Analyzing input ({len(text)} chars, {len(text.splitlines())} lines)...", file=sys.stderr)

    analysis = analyze_input(text)
    report = build_report(analysis, text, args.skill_path)

    output_json = json.dumps(report, indent=2)

    if args.output:
        Path(args.output).write_text(output_json)
        if args.verbose:
            print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output_json)

    sys.exit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
