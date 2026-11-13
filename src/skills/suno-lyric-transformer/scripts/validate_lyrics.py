#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate transformed lyrics structure for Suno compatibility.

Checks metatag formatting (unrecognized or unclosed tags, several tags on one
line), section structure (lyric lines before the first section tag, blank line
separators), style cue contamination, reasonable song length, [End] placement
(last line, nothing after it), and narrative section labels such as
[Verse 1 — THE ROOM] that Suno has no signal for. Parameterized section tags
([Verse 1: hushed], [Verse | whispered], [Verse 1 - riff continues]) count as
sections. Which tags open a section and which are recognized comes from
tag_vocab.py, shared with the other lyric scripts.

Usage:
    uv run validate_lyrics.py <lyrics-file-or-text> [options]

    # Validate lyrics from a file
    uv run validate_lyrics.py lyrics.txt

    # Validate lyrics from stdin
    echo "[Verse 1]\\nHello world" | uv run validate_lyrics.py --stdin

    # Validate with text argument
    uv run validate_lyrics.py --text "[Verse 1]\\nHello world"

    # Output to file
    uv run validate_lyrics.py lyrics.txt -o results.json
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "_shared"))
sys.path.insert(0, str(_HERE))
from script_io import fail, read_text_input, write_output
from tag_vocab import classify, is_sung_section, is_tag_line, line_tags, section_opener, split_section_tag

try:
    from suno_constants import SUNO_LYRICS_HARD_LIMIT, SUNO_LYRICS_QUALITY_BUDGET
except ImportError as exc:
    fail(f"{exc}: this skill's scripts/_shared folder is missing or incomplete; reinstall the skill")

SCRIPT_NAME = "validate-lyrics"
VERSION = "1.4.0"

# Style cues that should NOT be in lyrics
STYLE_CONTAMINATION_PATTERNS = [
    r'\b(?:BPM|bpm)\b',
    r'\b(?:stereo|mono)\s+(?:field|mix)\b',
    r'\b(?:radio[- ]ready|lo[- ]fi|hi[- ]fi)\b',
    r'\b(?:punchy|warm|crisp)\s+(?:drums|bass|mix|production)\b',
]


def _instrumental_section(tag_text: str) -> bool:
    """True when a section is instrumental by nature or says so in its cue."""
    return "instrumental" in tag_text.lower() or not is_sung_section(tag_text)


def narrative_label(tag_text: str) -> str | None:
    """Return the label when a section tag carries a narrative title.

    An em/en-dash label in title or capital case ([Verse 1 — THE ROOM],
    [Breakdown – The Turn]) or an all-caps colon label ([Verse 1: THE ROOM])
    reads as a story title, not a direction. Lower-case cues
    ([Verse 1: hushed, tense]) are directions and pass.
    """
    parts = split_section_tag(tag_text)
    if not parts or not parts["cue"]:
        return None
    label = parts["cue"]
    if parts["separator"] in ("–", "—"):
        words = re.findall(r"[^\W\d_]+", label)
        if words and all(w[0].isupper() for w in words):
            return label
    elif parts["separator"] == ":":
        letters = [c for c in label if c.isalpha()]
        if len(letters) >= 2 and all(c.isupper() for c in letters):
            return label
    return None


# Reasonable song length bounds (in non-empty, non-tag lines)
MIN_LYRIC_LINES = 8
MAX_LYRIC_LINES = 80
RECOMMENDED_MAX_SECTIONS = 12



def parse_lyrics(text: str) -> dict:
    """Parse lyrics into structured sections with line data."""
    lines = text.split('\n')
    sections = []
    current_section = None
    all_tags = []
    orphan_lines = []      # lyric lines before the first section tag
    multi_tag_lines = []   # lines holding more than one tag

    for i, line in enumerate(lines, 1):
        tags = line_tags(line)
        if tags:
            all_tags.extend({"text": tag, "line": i} for tag in tags)
            if len(tags) > 1:
                multi_tag_lines.append(i)
            # Only a section tag opens a section: a descriptor, a delivery cue
            # ([Harmonized]) or [End] stays inside the section it sits in.
            opener = section_opener(line)
            if opener:
                current_section = {
                    "tag": opener,
                    "line": i,
                    "lyric_lines": [],
                    "lyric_line_numbers": []
                }
                sections.append(current_section)
            continue

        stripped = line.strip()
        if stripped:
            if current_section:
                current_section["lyric_lines"].append(stripped)
                current_section["lyric_line_numbers"].append(i)
            else:
                orphan_lines.append(i)

    return {
        "sections": sections,
        "all_tags": all_tags,
        "orphan_lines": orphan_lines,
        "multi_tag_lines": multi_tag_lines,
        "total_lines": len(lines),
        "raw_text": text
    }


def validate_lyrics(text: str) -> list[dict]:
    """Validate lyrics text and return findings."""
    findings = []
    lines = text.split('\n')

    if not text.strip():
        findings.append({
            "severity": "critical",
            "category": "structure",
            "issue": "Lyrics text is empty.",
            "fix": "Provide lyrics with at least one section and content."
        })
        return findings

    parsed = parse_lyrics(text)
    sections = parsed["sections"]

    # Check for at least one section tag
    if not sections:
        findings.append({
            "severity": "high",
            "category": "structure",
            "issue": "No section metatags found. Suno uses tags like [Verse], [Chorus] to structure songs.",
            "fix": "Add section tags to define song structure."
        })
    elif parsed["orphan_lines"]:
        orphans = parsed["orphan_lines"]
        span = str(orphans[0]) if len(orphans) == 1 else f"{orphans[0]}-{orphans[-1]}"
        findings.append({
            "severity": "medium",
            "category": "structure",
            "location": {"line": orphans[0]},
            "issue": f"{len(orphans)} lyric line(s) before the first section tag (line {span}). Suno has no section to sing them in.",
            "fix": "Move the first section tag above these lines, or remove them (a title line is not a lyric)."
        })

    for line_num in parsed["multi_tag_lines"]:
        findings.append({
            "severity": "medium",
            "category": "structure",
            "location": {"line": line_num},
            "issue": f"Several tags on line {line_num}: {lines[line_num - 1].strip()[:60]}",
            "fix": "Put each tag on its own line."
        })

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('[') and ']' not in stripped:
            findings.append({
                "severity": "high",
                "category": "structure",
                "location": {"line": i},
                "issue": f"Unclosed tag at line {i}: '{stripped[:60]}'. Without its closing bracket Suno sings it as a lyric.",
                "fix": "Close the bracket."
            })

    # Check for blank lines between sections
    for section in sections:
        line_num = section["line"]
        if line_num > 1:
            prev_line = lines[line_num - 2] if line_num - 1 < len(lines) else ""
            if prev_line.strip() and not is_tag_line(prev_line):
                findings.append({
                    "severity": "medium",
                    "category": "structure",
                    "location": {"line": line_num},
                    "issue": f"No blank line before section tag [{section['tag']}] at line {line_num}.",
                    "fix": "Add a blank line before each section tag for cleaner Suno parsing."
                })

    # Check for style cues in lyrics
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or is_tag_line(line):
            continue
        for pattern in STYLE_CONTAMINATION_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                findings.append({
                    "severity": "high",
                    "category": "structure",
                    "location": {"line": i},
                    "issue": f"Possible style cue in lyrics at line {i}: '{stripped[:60]}...'",
                    "fix": "Style descriptions belong in the style prompt, not in lyrics."
                })
                break

    # Check for asterisks
    for i, line in enumerate(lines, 1):
        if '*' in line:
            findings.append({
                "severity": "medium",
                "category": "structure",
                "location": {"line": i},
                "issue": f"Asterisk found in lyrics at line {i}. Suno doesn't use markdown.",
                "fix": "Remove asterisks from lyrics."
            })

    # Count actual lyric lines (non-empty, non-tag)
    lyric_lines = [line.strip() for line in lines if line.strip() and not is_tag_line(line)]
    lyric_count = len(lyric_lines)

    if lyric_count < MIN_LYRIC_LINES:
        findings.append({
            "severity": "low",
            "category": "structure",
            "issue": f"Very short lyrics ({lyric_count} lines). May produce a very short song.",
            "fix": "Consider adding more content or sections for a full-length song."
        })

    # Character count check (Suno counts everything including metatags)
    char_count = len(text) - (1 if text.endswith("\n") else 0)  # closing newline not pasted
    if char_count > SUNO_LYRICS_HARD_LIMIT:
        findings.append({
            "severity": "high",
            "category": "structure",
            "issue": f"Total character count ({char_count}) exceeds Suno's {SUNO_LYRICS_HARD_LIMIT}-character limit. Suno will truncate your lyrics.",
            "fix": f"Trim lyrics to stay under {SUNO_LYRICS_HARD_LIMIT:,} characters (hard limit). For best quality, aim for ~{SUNO_LYRICS_QUALITY_BUDGET:,} characters."
        })
    elif char_count > SUNO_LYRICS_QUALITY_BUDGET:
        findings.append({
            "severity": "medium",
            "category": "structure",
            "issue": f"Total character count ({char_count}) is approaching Suno's {SUNO_LYRICS_HARD_LIMIT}-character limit.",
            "fix": f"Consider trimming — quality degrades above ~{SUNO_LYRICS_QUALITY_BUDGET:,} characters. Hard limit is {SUNO_LYRICS_HARD_LIMIT:,}."
        })

    if lyric_count > MAX_LYRIC_LINES:
        findings.append({
            "severity": "medium",
            "category": "structure",
            "issue": f"Very long lyrics ({lyric_count} lines). Suno may not render all content.",
            "fix": "Consider trimming to a more standard song length (20-50 lyric lines)."
        })

    # Check section count
    if len(sections) > RECOMMENDED_MAX_SECTIONS:
        findings.append({
            "severity": "low",
            "category": "structure",
            "issue": f"High section count ({len(sections)}). Songs typically have 6-10 sections.",
            "fix": "Consider consolidating sections for a cleaner structure."
        })

    # Check for invalid metatags: anything the shared vocabulary doesn't know
    for tag_info in parsed["all_tags"]:
        tag_text = tag_info["text"]
        if classify(tag_text) == "unknown":
            findings.append({
                "severity": "low",
                "category": "consistency",
                "location": {"line": tag_info["line"]},
                "issue": f"Unrecognized metatag [{tag_text}] at line {tag_info['line']}. May not be interpreted by Suno.",
                "fix": "Use standard section tags or descriptor tags (Mood/Energy/Vocal Style/Instrument)."
            })

    # Punctuation density check
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or is_tag_line(line):
            continue
        words = stripped.split()
        word_count = len(words)
        if word_count == 0:
            continue
        # Count commas, dashes, semicolons, colons, ellipses
        punct_count = (
            stripped.count(',') + stripped.count('-') + stripped.count(';')
            + stripped.count(':') + stripped.count('...')
        )
        density = punct_count / word_count
        if density > 0.5:
            findings.append({
                "severity": "low",
                "category": "rhythm",
                "location": {"line": i},
                "issue": f"Heavy punctuation density ({density:.2f}) at line {i}: '{stripped[:60]}'. Heavy punctuation can confuse Suno's cadence.",
                "fix": "Simplify punctuation to let Suno interpret natural phrasing."
            })

    # Narrative section labels: Suno has no signal for them and may sing them.
    for tag_info in parsed["all_tags"]:
        label = narrative_label(tag_info["text"])
        if label:
            findings.append({
                "severity": "medium",
                "category": "structure",
                "location": {"line": tag_info["line"]},
                "issue": f"Narrative section label [{tag_info['text']}] at line {tag_info['line']}: '{label}' gives Suno no direction and may be sung.",
                "fix": "Translate the label to Suno-actionable direction (e.g. [Verse 1: hushed, tense]); keep the narrative label in songbook notes."
            })

    # [End] placement: the absolute last line, nothing below it.
    end_lines = [i for i, line in enumerate(lines, 1) if line.strip().lower() == "[end]"]
    if sections and not end_lines:
        findings.append({
            "severity": "low",
            "category": "structure",
            "issue": "No [End] tag.",
            "fix": "Add [End] as the final line of the lyrics."
        })
    for line_num in end_lines[:-1]:
        findings.append({
            "severity": "medium",
            "category": "structure",
            "location": {"line": line_num},
            "issue": f"[End] at line {line_num} is not the last line; more lyrics follow it.",
            "fix": "Keep a single [End] on the final line."
        })
    if end_lines:
        last = end_lines[-1]
        after = lines[last:]
        tail = lines[last - 1][lines[last - 1].lower().index("[end]") + len("[end]"):]
        if any(line.strip() for line in after):
            findings.append({
                "severity": "medium",
                "category": "structure",
                "location": {"line": last},
                "issue": f"Text follows the final [End] at line {last}.",
                "fix": "Move [End] to the absolute last line."
            })
        elif tail or len(after) > 1 or (after and after[0] != ""):
            # One terminating newline (a file's last line) is fine; anything more is not.
            findings.append({
                "severity": "low",
                "category": "structure",
                "location": {"line": last},
                "issue": f"Whitespace or blank lines after [End] at line {last}.",
                "fix": "End the lyrics block on [End] with nothing below it, not even a blank line."
            })

    # Check for empty sections. Instrumental-by-nature sections ([Intro - guitar, instrumental],
    # [Guitar Solo], [Break], [Outro], [End]) are meant to be empty; only sung sections are flagged.
    for section in sections:
        if not section["lyric_lines"] and not _instrumental_section(section["tag"]):
            findings.append({
                "severity": "low",
                "category": "structure",
                "location": {"line": section["line"]},
                "issue": f"Empty section [{section['tag']}] at line {section['line']}.",
                "fix": "Add lyrics to this section or remove the tag if it's meant to be instrumental."
            })

    return findings


def build_report(findings: list, text: str, skill_path: str = "") -> dict:
    """Build the standard output report."""
    for f in findings:
        if "location" not in f:
            f["location"] = {"file": "lyrics"}

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1

    status = "pass"
    if severity_counts["critical"] > 0:
        status = "fail"
    elif severity_counts["high"] > 0:
        status = "warning"

    parsed = parse_lyrics(text)
    lyric_lines = [line.strip() for line in text.split('\n')
                   if line.strip() and not is_tag_line(line)]

    # Derive the lyrics-vs-metatags character split so the LLM reads it from
    # JSON instead of counting brackets by hand (Suno counts everything; the
    # split lets the budget breakout attribute chars to words vs. tags).
    metatag_character_count = sum(
        len(line) for line in text.split('\n')
        if is_tag_line(line)
    )
    # A file's or heredoc's closing newline isn't pasted into Suno: the count matches the
    # lyrics as returned (no trailing newline).
    pasted_length = len(text) - (1 if text.endswith("\n") else 0)
    lyric_character_count = pasted_length - metatag_character_count

    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "skill_path": skill_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "metrics": {
            "total_lines": parsed["total_lines"],
            "lyric_lines": len(lyric_lines),
            "character_count": pasted_length,
            "lyric_character_count": lyric_character_count,
            "metatag_character_count": metatag_character_count,
            "section_count": len(parsed["sections"]),
            "sections": [s["tag"] for s in parsed["sections"]]
        },
        "findings": findings,
        "summary": {
            "total": len(findings),
            **severity_counts
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate transformed lyrics structure for Suno compatibility.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s lyrics.txt
  %(prog)s --text "[Verse 1]\\nHello world"
  %(prog)s --stdin < lyrics.txt
  %(prog)s lyrics.txt -o results.json --verbose

Exit codes: 0=pass, 1=fail/warning, 2=unreadable input or unwritable output
        """
    )
    parser.add_argument("file", nargs="?", help="Path to lyrics text file")
    parser.add_argument("--text", help="Lyrics text to validate directly")
    parser.add_argument("--stdin", action="store_true", help="Read lyrics from stdin")
    parser.add_argument("-o", "--output", help="Output file path (defaults to stdout)")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostics to stderr")
    parser.add_argument("--skill-path", default="", help="Skill path for report context")

    args = parser.parse_args()

    text = read_text_input(args, parser)

    if args.verbose:
        print(f"Validating lyrics ({len(text)} chars, {len(text.splitlines())} lines)...", file=sys.stderr)

    findings = validate_lyrics(text)
    report = build_report(findings, text, args.skill_path)

    output_json = json.dumps(report, indent=2)

    write_output(output_json, args.output)
    if args.output and args.verbose:
        print(f"Report written to {args.output}", file=sys.stderr)

    sys.exit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
