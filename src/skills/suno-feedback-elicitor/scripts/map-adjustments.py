#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Map feedback dimension categories to Suno parameter adjustment recommendations.

Takes structured feedback dimensions (from parse-feedback.py or LLM triage)
and returns baseline parameter adjustment recommendations as structured JSON.
The LLM then refines these recommendations with contextual judgment.

Two further modes work on finished text instead of dimensions:
  --check-final  descriptors in a finished style prompt that an exclusion cancels
  --diff         the descriptor- and word-level micro-diff between two style prompts
                 (and, optionally, two exclusion prompts)

Status (dimensions mode): pass when every dimension mapped; warning when some
did not (listed in `unmapped`); fail when none did or none were given.

Exit codes:
  0 = pass or warning
  1 = invalid input, or status fail (nothing mapped)
  2 = runtime error / usage error
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
from suno_constants import (
    CRITICAL_ZONE,
    EXCLUSION_RECOMMENDED_MAX,
    PAID_TIERS,
    STYLE_PROMPT_DEFAULT_MAX,
    STYLE_PROMPT_LIMITS,
)

# Adjustment lookup tables
# Each dimension maps to a set of possible adjustments categorized by direction

STYLE_PROMPT_ADJUSTMENTS: dict[str, dict[str, dict[str, Any]]] = {
    "instrumentation": {
        "too_much": {
            "add": ["minimal arrangement", "sparse instrumentation", "stripped-back"],
            "remove_patterns": ["lush", "layered", "full", "dense", "wall of sound"],
            "exclude_add": ["no dense layering"],
        },
        "too_little": {
            "add": ["lush arrangement", "layered instrumentation", "full sound"],
            "remove_patterns": ["minimal", "sparse", "stripped"],
            "exclude_add": [],
        },
        "wrong_type": {
            "add": [],
            "remove_patterns": [],
            "exclude_add": [],
            "note": "Specify the unwanted instrument in exclusions and desired instrument in style prompt",
        },
    },
    "vocals": {
        "too_polished": {
            "add": ["raw vocal", "imperfect delivery", "organic phrasing"],
            "remove_patterns": ["polished", "clean vocal", "perfect"],
            "exclude_add": ["no overproduced vocals"],
        },
        "too_rough": {
            "add": ["polished vocal", "smooth delivery", "clean singing"],
            "remove_patterns": ["raw", "rough", "gritty"],
            "exclude_add": ["no raspy vocals"],
        },
        "too_quiet": {
            "add": ["prominent vocals", "voice-forward mix"],
            "remove_patterns": [],
            "exclude_add": [],
        },
        "too_loud": {
            "add": ["balanced mix", "instrument-forward"],
            "remove_patterns": ["prominent vocal", "voice-forward"],
            "exclude_add": [],
        },
        "wrong_character": {
            "add": [],
            "remove_patterns": [],
            "exclude_add": [],
            "note": "Specify desired vocal character: gender, age, tone, delivery style",
        },
    },
    "energy": {
        "too_high": {
            "add": ["gentle", "soft", "understated", "subtle"],
            "remove_patterns": ["high energy", "powerful", "driving", "intense"],
            "exclude_add": [],
            "slider": {"weirdness": "unchanged", "style_influence": "unchanged"},
        },
        "too_low": {
            "add": ["high energy", "powerful", "dynamic", "driving"],
            "remove_patterns": ["gentle", "soft", "subtle", "laid-back"],
            "exclude_add": [],
            "slider": {"style_influence": "decrease_slightly"},
        },
        "flat": {
            "add": ["dynamic shifts", "building energy", "crescendo", "varied sections"],
            "remove_patterns": [],
            "exclude_add": [],
            "slider": {"weirdness": "increase_slightly"},
        },
    },
    "tempo": {
        "too_fast": {
            "add": ["slow tempo", "laid-back", "relaxed groove"],
            "remove_patterns": ["uptempo", "fast", "driving rhythm", "energetic pace"],
            "exclude_add": [],
        },
        "too_slow": {
            "add": ["uptempo", "driving rhythm", "energetic pace"],
            "remove_patterns": ["slow", "laid-back", "relaxed", "gentle pace"],
            "exclude_add": [],
        },
    },
    "production": {
        "too_polished": {
            "add": ["lo-fi", "raw production", "analog warmth", "rough edges"],
            "remove_patterns": ["radio-ready", "clean production", "crisp", "polished"],
            "exclude_add": [],
            "slider": {"weirdness": "increase"},
        },
        "too_rough": {
            "add": ["radio-ready mix", "clean production", "crisp", "polished"],
            "remove_patterns": ["lo-fi", "raw", "rough", "analog"],
            "exclude_add": [],
            "slider": {"weirdness": "decrease"},
        },
        "too_reverb": {
            "add": ["dry mix", "close mic", "intimate"],
            "remove_patterns": ["spacious", "reverb", "ambient", "atmospheric"],
            "exclude_add": [],
        },
        "too_dry": {
            "add": ["spacious", "reverb", "ambient", "atmospheric"],
            "remove_patterns": ["dry", "close mic"],
            "exclude_add": [],
        },
    },
    "vibe": {
        "too_happy": {
            "add": ["melancholic", "bittersweet", "minor key", "moody"],
            "remove_patterns": ["uplifting", "bright", "happy", "cheerful", "major key"],
            "exclude_add": [],
        },
        "too_dark": {
            "add": ["uplifting", "bright", "major key", "hopeful"],
            "remove_patterns": ["melancholic", "dark", "moody", "minor key"],
            "exclude_add": [],
        },
        "too_generic": {
            "add": ["distinctive", "unique", "unconventional"],
            "remove_patterns": ["classic", "traditional", "conventional"],
            "exclude_add": [],
            "slider": {"weirdness": "increase_significantly"},
        },
        "too_weird": {
            "add": ["familiar", "classic", "conventional", "straightforward"],
            "remove_patterns": ["experimental", "unexpected", "unconventional"],
            "exclude_add": [],
            "slider": {"weirdness": "decrease_significantly"},
        },
    },
    "music": {
        "general_issue": {
            "add": [],
            "remove_patterns": [],
            "exclude_add": [],
            "note": "Music feedback requires further narrowing — which aspect of the music? Instrumentation, tempo, energy, production?",
        },
    },
    "structure": {
        "needs_bridge": {
            "lyric_change": "Add [Bridge] section between second chorus and outro",
        },
        "chorus_weak": {
            "lyric_change": "Add [Energy: High] before chorus, consider [Build-Up] section",
        },
        "too_long": {
            "lyric_change": "Remove repeated sections or shorten verses",
        },
        "too_short": {
            "lyric_change": "Add additional verse or extend instrumental sections",
        },
    },
    "lyrics": {
        "phrasing_unnatural": {
            "lyric_change": "Run syllable counter, normalize line lengths within sections",
        },
        "content_mismatch": {
            "lyric_change": "Review lyrics against intended mood/theme, revise for alignment",
        },
        "vocal_style_inconsistent": {
            "lyric_change": "Add consistent [Vocal Style: ...] tags before each section",
        },
    },
    "quality": {
        "artifacts": {
            "note": "Audio artifacts are generation-specific. Regenerate 3-5 times before modifying prompt. If persistent, simplify style prompt.",
        },
        "robotic_vocals": {
            "add": ["natural vocal", "organic phrasing", "human delivery", "breathy"],
            "remove_patterns": [],
            "exclude_add": ["no auto-tune", "no robotic vocals"],
        },
        "clipping": {
            "add": ["clean mix", "dynamic range", "headroom"],
            "remove_patterns": ["heavy", "distorted", "loud", "wall of sound"],
            "exclude_add": [],
        },
        "muffled": {
            "add": ["crisp", "clear mix", "defined frequencies", "bright"],
            "remove_patterns": ["warm", "lo-fi", "analog"],
            "exclude_add": [],
        },
    },
    "length": {
        "too_short": {
            "lyric_change": "Add sections in lyrics (additional verse, bridge, instrumental break) or use Suno extend feature",
        },
        "too_long": {
            "lyric_change": "Remove repeated sections, trim [Outro] content, remove non-essential [Breakdown]",
        },
        "intro_too_long": {
            "lyric_change": "Shorten or remove [Intro] content, add [Verse 1] tag earlier",
        },
        "outro_cuts_off": {
            "lyric_change": "Add explicit [Outro] section with 2-4 lines, add [Fade Out] metatag",
        },
        "pacing_drags": {
            "lyric_change": "Add [Energy: building] metatags, shorten dragging sections, add [Breakdown] or [Build-Up] for variety",
        },
    },
}

SLIDER_DIRECTION_MAP = {
    "increase_slightly": "+5-10 from current",
    "increase": "+15-20 from current",
    "increase_significantly": "+25-35 from current (cap at 85)",
    "decrease_slightly": "-5-10 from current",
    "decrease": "-15-20 from current",
    "decrease_significantly": "-25-35 from current (floor at 15)",
    "unchanged": "no change recommended",
}


def check_style_prompt_overflow(
    style_prompt: str,
    add_descriptors: list[str],
    model: str,
) -> dict[str, Any] | None:
    """Project post-edit style-prompt length against the model's character limit.

    v4 Pro silently truncates at 200 chars; other models cap at 1000. Returns a
    warning dict when the projected length (current prompt + added descriptors)
    exceeds the model's limit, else None.
    """
    if not style_prompt:
        return None

    limit = STYLE_PROMPT_LIMITS.get(model, STYLE_PROMPT_DEFAULT_MAX)
    current_len = len(style_prompt)
    # Added descriptors are appended ", "-joined onto the existing prompt.
    added_len = sum(len(d) + 2 for d in add_descriptors)
    projected = current_len + added_len

    if projected <= limit:
        return None

    return {
        "type": "style_prompt_overflow",
        "model": model or "unknown (default 1000-char limit assumed)",
        "limit": limit,
        "current_chars": current_len,
        "projected_chars": projected,
        "overflow_chars": projected - limit,
        "detail": (
            f"Projected style prompt (~{projected} chars after adds) exceeds the "
            f"{limit}-char limit for model '{model or 'default'}' by ~{projected - limit} chars. "
            f"Content beyond {limit} is silently truncated — prioritize the strongest descriptors "
            f"in the first {CRITICAL_ZONE} chars and drop or shorten the rest."
        ),
    }


def generate_adjustments(
    dimensions: list[dict[str, str]],
    current_tier: str = "",
    style_prompt: str = "",
    model: str = "",
) -> dict[str, Any]:
    """Generate adjustment recommendations from feedback dimensions."""
    style_add: list[str] = []
    style_remove: list[str] = []
    exclude_add: list[str] = []
    slider_adjustments: dict[str, str] = {}
    lyric_changes: list[str] = []
    notes: list[str] = []
    unmapped: list[dict[str, str]] = []

    for dim_entry in dimensions:
        if not isinstance(dim_entry, dict):
            unmapped.append({"dimension": str(dim_entry), "direction": "", "reason": "not an object"})
            notes.append(f"Entry {dim_entry!r} is not a {{dimension, direction}} object — requires LLM judgment")
            continue
        dimension = dim_entry.get("dimension", "")
        direction = dim_entry.get("direction", "")

        if dimension not in STYLE_PROMPT_ADJUSTMENTS:
            unmapped.append({"dimension": dimension, "direction": direction, "reason": "unknown dimension"})
            notes.append(f"Unknown dimension '{dimension}' — requires LLM judgment")
            continue

        dim_adjustments = STYLE_PROMPT_ADJUSTMENTS[dimension]
        if direction not in dim_adjustments:
            available = list(dim_adjustments.keys())
            unmapped.append({"dimension": dimension, "direction": direction, "reason": "unknown direction"})
            notes.append(
                f"Unknown direction '{direction}' for dimension '{dimension}'. "
                f"Available: {', '.join(available)}"
            )
            continue

        adj = dim_adjustments[direction]

        if "add" in adj:
            style_add.extend(adj["add"])
        if "remove_patterns" in adj:
            style_remove.extend(adj["remove_patterns"])
        if "exclude_add" in adj:
            exclude_add.extend(adj["exclude_add"])
        if "slider" in adj:
            for slider_name, slider_dir in adj["slider"].items():
                slider_adjustments[slider_name] = SLIDER_DIRECTION_MAP.get(
                    slider_dir, slider_dir
                )
        if "lyric_change" in adj:
            lyric_changes.append(adj["lyric_change"])
        if "note" in adj:
            notes.append(adj["note"])

    is_paid = current_tier.lower() in PAID_TIERS if current_tier else False

    result: dict[str, Any] = {
        "style_prompt": {
            "add_descriptors": list(dict.fromkeys(style_add)),  # dedupe preserving order
            "remove_patterns": list(dict.fromkeys(style_remove)),
        },
        "exclusions": {
            "add": list(dict.fromkeys(exclude_add)),
        },
    }

    if slider_adjustments:
        if is_paid:
            result["sliders"] = slider_adjustments
        else:
            result["sliders"] = {
                "note": "Slider adjustments recommended but not available on free tier. Compensate through style prompt wording.",
                "recommended_if_upgraded": slider_adjustments,
            }

    if lyric_changes:
        result["lyrics"] = {"changes": lyric_changes}

    if notes:
        result["notes"] = notes

    result["mapped"] = len(dimensions) - len(unmapped)
    result["unmapped"] = unmapped

    consistency_warnings = check_adjustment_consistency(result)
    if consistency_warnings:
        if "notes" not in result:
            result["notes"] = []
        result["consistency_warnings"] = consistency_warnings

    overflow = check_style_prompt_overflow(
        style_prompt, result["style_prompt"]["add_descriptors"], model
    )
    if overflow:
        result.setdefault("consistency_warnings", []).append(overflow)

    return result


def _add_exclude_conflicts(style_items, exclude_items) -> list[dict[str, Any]]:
    """Style descriptors that an exclusion would cancel (simple substring check, either way)."""
    warnings = []
    for add_desc in style_items:
        for excl in exclude_items:
            term = excl.lower().removeprefix("no ").strip()
            if not add_desc.strip() or not term:
                continue
            if add_desc.lower() in excl.lower() or term in add_desc.lower():
                warnings.append({
                    "type": "add_exclude_conflict",
                    "detail": f"Style descriptor '{add_desc}' conflicts with exclusion '{excl}'",
                })
    return warnings


def check_final_package(style_prompt: str, exclusions: str) -> list[dict[str, Any]]:
    """Check a finished style prompt against its finished exclusions before it is presented.

    Splits both on commas and flags descriptors an exclusion would cancel. Character limits
    are the suno-style-prompt-builder validator's job, so they are not repeated here.
    """
    style_items = [d.strip() for d in style_prompt.split(",") if d.strip()]
    exclude_items = [e.strip() for e in exclusions.split(",") if e.strip()]
    return _add_exclude_conflicts(style_items, exclude_items)


def _descriptors(text: str) -> list[str]:
    return [d.strip() for d in text.split(",") if d.strip()]


def _starts(text: str, items: list[str]) -> list[int]:
    """Character offset where each comma-separated descriptor starts in `text`."""
    offsets, cursor = [], 0
    for item in items:
        at = text.find(item, cursor)
        offsets.append(at if at >= 0 else cursor)
        cursor = (at if at >= 0 else cursor) + len(item)
    return offsets


def _words(text: str) -> list[str]:
    return re.findall(r"[\w'-]+", text.lower())


def diff_prompts(before: str, after: str, reword_ratio: float = 0.5) -> dict[str, Any]:
    """Descriptor-level micro-diff between two comma-separated prompts.

    Descriptors are compared case-insensitively. A removed and an added descriptor
    that share most of their words are reported once as `reworded`, with the words
    each side gained and lost. Kept descriptors that left the longest common order
    are `moved`. Every position is a character offset in its own prompt, and
    `in_critical_zone` says whether it starts inside the first CRITICAL_ZONE chars.
    """
    old, new = _descriptors(before), _descriptors(after)
    old_at, new_at = _starts(before, old), _starts(after, new)
    old_keys, new_keys = [d.lower() for d in old], [d.lower() for d in new]

    removed_idx = [i for i, k in enumerate(old_keys) if k not in new_keys]
    added_idx = [j for j, k in enumerate(new_keys) if k not in old_keys]

    reworded = []
    for i in list(removed_idx):
        best, best_ratio = None, reword_ratio
        for j in added_idx:
            ratio = difflib.SequenceMatcher(None, _words(old[i]), _words(new[j])).ratio()
            if ratio >= best_ratio:
                best, best_ratio = j, ratio
        if best is not None:
            ow, nw = _words(old[i]), _words(new[best])
            reworded.append({
                "from": old[i], "to": new[best],
                "words_added": [w for w in nw if w not in ow],
                "words_removed": [w for w in ow if w not in nw],
                "position": new_at[best], "in_critical_zone": new_at[best] < CRITICAL_ZONE,
            })
            removed_idx.remove(i)
            added_idx.remove(best)

    kept_old = [k for k in old_keys if k in new_keys]
    kept_new = [k for k in new_keys if k in old_keys]
    stay = set()
    for block in difflib.SequenceMatcher(None, kept_old, kept_new, autojunk=False).get_matching_blocks():
        stay.update(kept_new[block.b:block.b + block.size])
    moved = []
    for j, k in enumerate(new_keys):
        if k in old_keys and k not in stay:
            i = old_keys.index(k)
            moved.append({
                "text": new[j], "from": old_at[i], "to": new_at[j],
                "critical_zone_before": old_at[i] < CRITICAL_ZONE,
                "critical_zone_after": new_at[j] < CRITICAL_ZONE,
            })

    return {
        "added": [{"text": new[j], "position": new_at[j], "in_critical_zone": new_at[j] < CRITICAL_ZONE}
                  for j in added_idx],
        "removed": [{"text": old[i], "position": old_at[i], "in_critical_zone": old_at[i] < CRITICAL_ZONE}
                    for i in removed_idx],
        "reworded": reworded,
        "moved": moved,
        "unchanged": len(kept_new) - len(moved),
        "chars_before": len(before),
        "chars_after": len(after),
    }


def check_adjustment_consistency(adjustments: dict[str, Any]) -> list[dict[str, Any]]:
    """Check for internal contradictions in adjustment recommendations."""
    warnings = []

    style_add = set(adjustments.get("style_prompt", {}).get("add_descriptors", []))
    style_remove = set(adjustments.get("style_prompt", {}).get("remove_patterns", []))
    exclude_add = set(adjustments.get("exclusions", {}).get("add", []))

    # Check for add/remove conflicts
    conflicts = style_add & style_remove
    if conflicts:
        warnings.append({
            "type": "add_remove_conflict",
            "detail": f"Descriptors appear in both add and remove: {', '.join(conflicts)}",
        })

    warnings.extend(_add_exclude_conflicts(style_add, exclude_add))

    # Check style prompt estimated length
    total_add_chars = sum(len(d) + 2 for d in style_add)  # +2 for ", " separator
    if total_add_chars > CRITICAL_ZONE:
        warnings.append({
            "type": "critical_zone_overflow",
            "detail": f"Added descriptors total ~{total_add_chars} chars — prioritize most important for the first {CRITICAL_ZONE} chars of style prompt (critical zone)",
        })

    # Check exclusion estimated length
    total_excl_chars = sum(len(e) + 2 for e in exclude_add)
    if total_excl_chars > EXCLUSION_RECOMMENDED_MAX:
        warnings.append({
            "type": "exclusion_overflow",
            "detail": f"Exclusion additions total ~{total_excl_chars} chars — keep total exclusions under ~{EXCLUSION_RECOMMENDED_MAX} chars, prioritize 2-3 most important",
        })

    return warnings


def main():
    parser = argparse.ArgumentParser(
        description="Map feedback dimensions to Suno parameter adjustment recommendations.",
        epilog="""
Input JSON schema:
  Required:
    dimensions (array of objects) - Each with:
      dimension (string) - Feedback dimension (one of the combinations listed below)
      direction (string) - Direction of the issue within the dimension

  Optional:
    tier (string) - User's Suno tier (free, pro, premier) — affects slider recommendations
    original_style_prompt (string) - Current style prompt; enables model-specific overflow validation
    model (string) - Suno model (v6, v6-wild, v6-mini; retired names keep their old limits) for overflow validation

  (CLI flags --style-prompt / --model override the JSON keys above.)

Dimension/Direction combinations:
  instrumentation: too_much, too_little, wrong_type
  vocals: too_polished, too_rough, too_quiet, too_loud, wrong_character
  energy: too_high, too_low, flat
  tempo: too_fast, too_slow
  production: too_polished, too_rough, too_reverb, too_dry
  vibe: too_happy, too_dark, too_generic, too_weird
  music: general_issue
  structure: needs_bridge, chorus_weak, too_long, too_short
  lyrics: phrasing_unnatural, content_mismatch, vocal_style_inconsistent
  quality: artifacts, robotic_vocals, clipping, muffled
  length: too_short, too_long, intro_too_long, outro_cuts_off, pacing_drags

Final check (before presenting a refined package):
  uv run map-adjustments.py --check-final --style-prompt "raw indie rock, dry vocal" --exclude "no reverb, no autotune"

Micro-diff (the "What Changed and Why" section):
  uv run map-adjustments.py --diff --style-prompt "OLD prompt" --new-style-prompt "NEW prompt"
      [--exclude "OLD excludes" --new-exclude "NEW excludes"]

Example:
  echo '{"dimensions": [{"dimension": "vocals", "direction": "too_polished"}, {"dimension": "energy", "direction": "too_low"}], "tier": "pro"}' | uv run map-adjustments.py --stdin
  echo '{"dimensions": [{"dimension": "vocals", "direction": "too_polished"}]}' | uv run map-adjustments.py --stdin --style-prompt "warm indie rock, ..." --model v6
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", "-i", help="Path to dimensions JSON file")
    input_group.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    input_group.add_argument(
        "--check-final", action="store_true",
        help="Check a finished --style-prompt against --exclude for descriptors an exclusion cancels "
        "(no dimensions input; run before presenting a refined package)",
    )
    input_group.add_argument(
        "--diff", action="store_true",
        help="Micro-diff --style-prompt (before) against --new-style-prompt (after), and --exclude against "
        "--new-exclude when either is given (no dimensions input)",
    )
    parser.add_argument("--exclude", default="", help="Finished exclusion prompt (with --check-final); "
                        "the before exclusions (with --diff)")
    parser.add_argument("--new-style-prompt", help="The after style prompt (with --diff)")
    parser.add_argument("--new-exclude", default="", help="The after exclusion prompt (with --diff)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument(
        "--style-prompt",
        help="Original style prompt text — enables model-specific overflow validation "
        "(overrides 'original_style_prompt'/'style_prompt' in the input JSON)",
    )
    parser.add_argument(
        "--model",
        help="Suno model (v6, v6-wild, v6-mini; retired names still recognized) — sets the style-prompt char "
        "limit for overflow validation (overrides 'model' in the input JSON)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output to stderr")

    args = parser.parse_args()

    if args.diff:
        if args.style_prompt is None or args.new_style_prompt is None:
            parser.error("--diff needs --style-prompt and --new-style-prompt")
        out: dict[str, Any] = {
            "script": "map-adjustments",
            "version": "1.1.0",
            "mode": "diff",
            "status": "pass",
            "style_prompt": diff_prompts(args.style_prompt, args.new_style_prompt),
        }
        if args.exclude or args.new_exclude:
            out["exclusions"] = diff_prompts(args.exclude, args.new_exclude)
        output_json = json.dumps(out, indent=2)
        if args.output:
            Path(args.output).write_text(output_json, encoding="utf-8")
        else:
            print(output_json)
        sys.exit(0)

    if args.check_final:
        if not args.style_prompt:
            parser.error("--check-final needs --style-prompt")
        warnings = check_final_package(args.style_prompt, args.exclude)
        output_json = json.dumps({
            "script": "map-adjustments",
            "version": "1.1.0",
            "mode": "check-final",
            "status": "warning" if warnings else "pass",
            "consistency_warnings": warnings,
        }, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_json)
        else:
            print(output_json)
        sys.exit(0)

    try:
        if args.stdin:
            raw = sys.stdin.read()
        else:
            with open(args.input, "r") as f:
                raw = f.read()

        data = json.loads(raw)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(json.dumps({
            "script": "map-adjustments",
            "version": "1.1.0",
            "status": "fail",
            "findings": [{
                "severity": "critical",
                "category": "structure",
                "issue": str(e),
                "fix": "Provide valid JSON input",
            }],
            "summary": {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0},
        }, indent=2))
        sys.exit(1)

    if not isinstance(data, dict) or "dimensions" not in data:
        print(json.dumps({
            "script": "map-adjustments",
            "version": "1.1.0",
            "status": "fail",
            "findings": [{
                "severity": "critical",
                "category": "structure",
                "issue": "Input must be a JSON object with a 'dimensions' array",
                "fix": 'Provide {"dimensions": [{"dimension": "...", "direction": "..."}]}',
            }],
            "summary": {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0},
        }, indent=2))
        sys.exit(1)

    dimensions = data["dimensions"]
    tier = data.get("tier", "")
    # CLI flags win; fall back to input-JSON keys (matching the headless contract's
    # original_style_prompt / model naming).
    style_prompt = args.style_prompt or data.get("original_style_prompt") or data.get("style_prompt", "")
    model = args.model or data.get("model", "")

    if not isinstance(dimensions, list):
        dimensions = [dimensions]
    adjustments = generate_adjustments(dimensions, tier, style_prompt, model)

    findings = []
    if not dimensions:
        findings.append({
            "severity": "high", "category": "input",
            "issue": "No dimensions given, so nothing was mapped",
            "fix": "Triage the feedback into at least one {dimension, direction} pair",
        })
    for miss in adjustments["unmapped"]:
        findings.append({
            "severity": "medium", "category": "unmapped",
            "issue": f"{miss['dimension']}/{miss['direction']}: {miss['reason']}",
            "fix": "Use a listed dimension/direction, or map this one by judgment from the map references",
        })
    if adjustments["mapped"] == 0:
        status = "fail"
    elif adjustments["unmapped"]:
        status = "warning"
    else:
        status = "pass"
    severities = [f["severity"] for f in findings]

    result = {
        "script": "map-adjustments",
        "version": "1.1.0",
        "status": status,
        "adjustments": adjustments,
        "input_dimensions": len(dimensions),
        "findings": findings,
        "summary": {"total": len(findings), "critical": 0, "high": severities.count("high"),
                    "medium": severities.count("medium"), "low": 0},
    }

    if args.verbose:
        print(f"[map-adjustments] Processed {len(dimensions)} dimensions", file=sys.stderr)

    output_json = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_json)
    else:
        print(output_json)

    sys.exit(1 if status == "fail" else 0)


if __name__ == "__main__":
    main()
