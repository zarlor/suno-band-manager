#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Validate a Suno style prompt package: limits, structure and enumerable safety triggers.

Checks the primary style prompt and, when given, the wild-card style prompt:
- Character count against the model's limit (1,000 for the v6 family; 200 for the retired v4 Pro)
- Critical zone (essentials belong in the first 200 chars) and genre front-loading
- Section tags and asterisks that don't belong in a style prompt
- Enumerable safety triggers: unpaired scream-trigger genres, keyboard-pull words,
  the "live" word family and crowd/audience words, inline negatives ("no X",
  "without X"), and '!'
Also checks the Exclude Styles text (length, item count, vagueness) and, when given,
Audio Influence against its slot's range (Persona 15-25%, Voice 35-95%) and a
Vocal Gender set alongside a Voice.

The script DETECTS; the calling LLM decides each rewrite or substitution.

Usage:
    # Whole package as JSON on stdin (preferred: no shell quoting of long prompts)
    echo '{"style_prompt": "...", "exclusion_prompt": "...", "model": "v6",
           "wild_card": {"style_prompt": "..."}}' | uv run validate-prompt.py --stdin

    # Package from a file (.json; .yaml/.yml when pyyaml is available)
    uv run validate-prompt.py --input-file package.json

    # Flags (short prompts)
    uv run validate-prompt.py --style "indie folk-rock, warm..." --exclude "autotune" --model v6

Exit codes: 0 = pass, 1 = warning or fail (see "status"), 2 = bad input.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
import suno_constants  # noqa: E402
from suno_constants import (  # noqa: E402
    STYLE_PROMPT_LIMITS, STYLE_PROMPT_DEFAULT_MAX, CRITICAL_ZONE,
    EXCLUSION_RECOMMENDED_MAX, EXCLUSION_HARD_MAX,
    GENRE_SIGNALS, HEAVY_VOCAL_TRIGGERS, VOCAL_SAFE_PAIRINGS,
    KEYBOARD_PULL_WORDS, SHOUT_TRIGGER_CHAR,
)

SCRIPT_NAME = "validate-prompt"
VERSION = "1.3.0"

# Constants not (yet) in the shared module. getattr lets a later shared-module
# version take over without a code change here.
CROWD_NOISE_WORDS = getattr(suno_constants, "CROWD_NOISE_WORDS", frozenset({
    # the "live" word family pulls "live album" crowd texture (live recording,
    # live-band drums, live energy...); crowd/audience words invite group
    # vocals and audience noise by association
    "live", "crowd", "audience", "concert", "festival", "stadium", "anthemic",
}))
PERSONA_AUDIO_INFLUENCE_RANGE = getattr(suno_constants, "PERSONA_AUDIO_INFLUENCE_RANGE", (15, 25))
VOICE_AUDIO_INFLUENCE_RANGE = getattr(suno_constants, "VOICE_AUDIO_INFLUENCE_RANGE", (35, 95))

# Inline negation: Suno reads the noun and drops the negation, so these add the
# very thing they mean to remove. Negatives belong in Exclude Styles.
# "no X" / "without X" are unambiguous; "not X" / "avoid X" / "don't X" usually are
# but get a softer flag. "never" is deliberately absent: persistence phrasing such
# as "the riff continues under the verse, never stops" is v6-endorsed direction.
NEGATION_STRONG = (r"\bno\s+[a-z][\w'-]*", r"\bwithout\s+[a-z][\w'-]*")
NEGATION_SOFT = (
    r"\bnot\s+[a-z][\w'-]*",
    r"\bavoid(?:s|ing)?\s+[a-z][\w'-]*",
    r"\b(?:do not|don't)\s+[a-z][\w'-]*",
)
NEGATION_PREFIXES = ("no ", "without ", "not ", "avoid")


def _word_re(term: str) -> str:
    """Delimiter match: the term must not sit inside a longer word."""
    return r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"


def _contains_term(lowered: str, term: str, plural: bool = False) -> bool:
    suffix = "s?" if plural else ""
    pattern = r"(?<![a-z0-9])" + re.escape(term) + suffix + r"(?![a-z0-9])"
    return re.search(pattern, lowered) is not None


def find_negations(text: str, patterns: tuple = NEGATION_STRONG + NEGATION_SOFT) -> list[str]:
    """Return the inline-negation phrases found in a style prompt, in order."""
    lowered = text.lower()
    hits = []
    for pattern in patterns:
        for m in re.finditer(pattern, lowered):
            hits.append((m.start(), m.group(0)))
    seen, ordered = set(), []
    for start, phrase in sorted(hits):
        if start not in seen:  # "do not X" would also match "not X"
            seen.update(range(start, start + len(phrase)))
            ordered.append(phrase)
    return ordered


def find_positive_pairings(lowered: str) -> list[str]:
    """Positive vocal phrases present in the prompt.

    A negative phrase ("no screaming") is never a pairing, and a positive phrase
    that only appears negated ("without clean vocals") doesn't count either.
    """
    found = []
    for phrase in VOCAL_SAFE_PAIRINGS:
        if phrase.startswith(NEGATION_PREFIXES):
            continue
        for m in re.finditer(_word_re(phrase), lowered):
            before = lowered[max(0, m.start() - 12):m.start()]
            if re.search(r"\b(no|without|not|never|avoid\w*)\s+$", before):
                continue
            found.append(phrase)
            break
    return sorted(set(found))


def detect_triggers(text: str, instrumental: bool = False) -> list[dict]:
    """Flag enumerable safety triggers in a style prompt.

    Detection only — the substitution or rewrite decision stays with the LLM.
    """
    findings = []
    lowered = text.lower()

    # Heavy-genre scream triggers. Always reported; a positive vocal pairing
    # lowers the severity but the LLM still judges whether it protects the vocal.
    found_triggers = sorted({
        word for word in HEAVY_VOCAL_TRIGGERS if re.search(_word_re(word), lowered)
    })
    if found_triggers:
        pairings = find_positive_pairings(lowered)
        if instrumental:
            severity = "info"
            issue = (f"Heavy-genre scream trigger(s) {found_triggers} in an instrumental prompt. "
                     "No vocal to protect, so this is usually a non-issue.")
            fix = "Note it as handled; don't add a vocal phrase to an instrumental prompt."
        elif pairings:
            severity = "low"
            issue = (f"Heavy-genre scream trigger(s) {found_triggers}, paired with positive vocal "
                     f"phrase(s) {pairings}. Confirm the pairing really sits on the lead vocal.")
            fix = "Keep the pairing close to the vocal description; put 'screaming' in Exclude Styles."
        else:
            severity = "high"
            issue = (f"Heavy-genre scream trigger(s) without a positive vocal instruction: "
                     f"{found_triggers}. These pull screaming/harsh vocals.")
            fix = ("Pair with a positive vocal phrase (e.g. 'raw melodic singing', 'gritty male vocals') "
                   "and put 'screaming' in Exclude Styles, or substitute a safe heavy term "
                   "(e.g. 'progressive heavy groove'). LLM decides which.")
        findings.append({
            "severity": severity,
            "category": "trigger",
            "issue": issue,
            "fix": fix,
            "data": {"triggers": found_triggers, "paired": bool(pairings),
                     "pairings": pairings, "instrumental": instrumental},
        })

    # Keyboard-pull / cinematic-light dangerous words.
    found_kb = sorted({word for word in KEYBOARD_PULL_WORDS if re.search(_word_re(word), lowered)})
    if found_kb:
        findings.append({
            "severity": "medium",
            "category": "trigger",
            "issue": f"Keyboard-pull dangerous word(s): {found_kb}. These pull theatrical/keyboard/synth-heavy or cinematic-light arrangements when guitars/bass should lead.",
            "fix": "Replace per the Dangerous Words table — e.g. 'cinematic' -> 'dynamic shifts, building from gentle to crushing'; 'orchestral' -> 'cello, heavy strings, kettle drums'; 'rock opera' -> 'power ballad, dynamic shifts, building from gentle to crushing'; avoid 'baroque' (describe the qualities instead).",
            "data": {"words": found_kb},
        })

    # The "live" word family and crowd/audience words pull crowd noise.
    found_crowd = sorted({w for w in CROWD_NOISE_WORDS if _contains_term(lowered, w, plural=True)})
    if found_crowd:
        findings.append({
            "severity": "medium",
            "category": "trigger",
            "issue": f"Crowd-noise word(s): {found_crowd}. The 'live' word family and crowd/audience words pull audience texture and crowd vocals, even when the intent is band-in-a-room energy.",
            "fix": "Say the quality, not the venue: 'unpolished room sound', 'natural room ambience', 'single-take band performance'.",
            "data": {"words": found_crowd},
        })

    # Inline negatives read as inclusion.
    for patterns, severity, label in ((NEGATION_STRONG, "high", "Inline negative(s)"),
                                      (NEGATION_SOFT, "medium", "Likely inline negative(s)")):
        negations = find_negations(text, patterns)
        if negations:
            findings.append({
                "severity": severity,
                "category": "negation",
                "issue": f"{label} in the style prompt: {negations}. Suno keeps the noun and drops the negation, so these invite what they mean to remove.",
                "fix": "Rewrite each as what you DO want (e.g. 'no reverb' -> 'dry, close-mic'd') and move the negated term to Exclude Styles.",
                "data": {"phrases": negations},
            })

    # Exclamation marks push delivery toward shouting/screaming.
    if SHOUT_TRIGGER_CHAR in text:
        findings.append({
            "severity": "low",
            "category": "trigger",
            "issue": "Exclamation mark(s) found. '!' pushes vocal delivery toward shouting/screaming.",
            "fix": "Remove exclamation marks unless a shouted delivery is intended.",
            "data": {"count": text.count(SHOUT_TRIGGER_CHAR)},
        })

    return findings


def get_limit_for_model(model: str) -> int:
    """Return the style prompt character limit for a given Suno model."""
    return STYLE_PROMPT_LIMITS.get(model, STYLE_PROMPT_DEFAULT_MAX)


def validate_style_prompt(text: str, model: str = "", instrumental: bool = False) -> list[dict]:
    """Validate a style prompt and return findings."""
    findings = []
    char_count = len(text)
    limit = get_limit_for_model(model) if model else STYLE_PROMPT_DEFAULT_MAX

    if char_count > limit:
        findings.append({
            "severity": "critical",
            "category": "structure",
            "issue": f"Style prompt exceeds {limit:,} character limit for {model or 'default'} ({char_count} chars). Suno will silently truncate.",
            "fix": f"Trim {char_count - limit} characters. Cut from the end — genre/mood at the start are most important.",
            "data": {"char_count": char_count, "limit": limit, "over_by": char_count - limit, "model": model},
        })
    elif char_count > limit * 0.9:
        findings.append({
            "severity": "low",
            "category": "structure",
            "issue": f"Style prompt is near the {limit:,} character limit ({char_count} chars). Limited room for iteration.",
            "fix": "Consider trimming less essential descriptors to leave room for refinement.",
            "data": {"char_count": char_count, "limit": limit},
        })

    if char_count > CRITICAL_ZONE:
        remaining = text[CRITICAL_ZONE:]
        if len(remaining.strip()) > 100:
            findings.append({
                "severity": "low",
                "category": "consistency",
                "issue": f"Style prompt has {len(remaining.strip())} chars beyond the critical zone (first {CRITICAL_ZONE} chars). Front-loaded terms have the strongest influence; later content adds nuance.",
                "fix": "Ensure essential genre, mood, and vocal descriptors appear within the first 200 characters. This is a priority guide, not a character limit.",
                "data": {"critical_zone": CRITICAL_ZONE, "beyond_zone_chars": len(remaining.strip())},
            })

    if not text.strip():
        findings.append({
            "severity": "critical",
            "category": "structure",
            "issue": "Style prompt is empty.",
            "fix": "Provide at minimum a genre and mood description.",
        })
        return findings

    # Genre front-loading — delimiter match, so 'soulful' doesn't count as 'soul'
    # and 'synthetic' doesn't count as 'synth'.
    first_segment = text[:CRITICAL_ZONE].lower()
    if not any(re.search(_word_re(g), first_segment) for g in GENRE_SIGNALS):
        findings.append({
            "severity": "medium",
            "category": "consistency",
            "issue": "No obvious genre keyword found in the first 200 characters. Genre should be front-loaded.",
            "fix": "Move genre and mood descriptors to the beginning of the style prompt.",
        })

    style_contamination = re.findall(r'\[(?:Verse|Chorus|Bridge|Intro|Outro|Pre-Chorus)\]', text, re.IGNORECASE)
    if style_contamination:
        findings.append({
            "severity": "high",
            "category": "structure",
            "issue": f"Lyric metatags found in style prompt: {style_contamination}. These belong in lyrics, not the style prompt.",
            "fix": "Remove all section tags ([Verse], [Chorus], etc.) from the style prompt. These go in the lyrics input.",
        })

    if '*' in text:
        findings.append({
            "severity": "medium",
            "category": "structure",
            "issue": "Asterisks found in style prompt. Suno does not use markdown formatting in style prompts.",
            "fix": "Remove all asterisks from the style prompt.",
        })

    findings.extend(detect_triggers(text, instrumental=instrumental))
    return findings


def validate_exclusion_prompt(text: str) -> list[dict]:
    """Validate an exclusion prompt and return findings."""
    findings = []

    if not text.strip():
        findings.append({
            "severity": "info",
            "category": "structure",
            "issue": "No exclusion prompt provided. This is optional but can improve results.",
            "fix": "Consider adding 2-3 specific exclusions to prevent unwanted elements.",
        })
        return findings

    char_count = len(text)

    if char_count > EXCLUSION_HARD_MAX:
        findings.append({
            "severity": "high",
            "category": "structure",
            "issue": f"Exclusion prompt is very long ({char_count} chars). Too many negatives can confuse the model.",
            "fix": "Trim to 2-3 most important exclusions. Prioritize the elements you most want to avoid.",
            "data": {"char_count": char_count, "recommended_max": EXCLUSION_RECOMMENDED_MAX},
        })
    elif char_count > EXCLUSION_RECOMMENDED_MAX:
        findings.append({
            "severity": "low",
            "category": "structure",
            "issue": f"Exclusion prompt is above recommended length ({char_count} chars, recommended ~{EXCLUSION_RECOMMENDED_MAX}).",
            "fix": "Consider trimming to the most impactful exclusions.",
            "data": {"char_count": char_count, "recommended_max": EXCLUSION_RECOMMENDED_MAX},
        })

    items = [i.strip() for i in re.split(r'[,;]', text) if i.strip()]
    if len(items) > 5:
        findings.append({
            "severity": "medium",
            "category": "consistency",
            "issue": f"Too many exclusion items ({len(items)}). More than 3-5 exclusions can confuse the model.",
            "fix": "Reduce to 2-3 most critical exclusions.",
        })

    vague_terms = ["no music", "no sound", "no instruments", "no singing", "nothing bad"]
    for term in vague_terms:
        if term in text.lower():
            findings.append({
                "severity": "medium",
                "category": "consistency",
                "issue": f"Vague exclusion term found: '{term}'. Be specific about what to exclude.",
                "fix": "Replace with specific terms: 'electric guitar' instead of 'instruments'.",
            })

    return findings


def validate_controls(audio_influence=None, audio_source: str = "", vocal_gender: str = "") -> list[dict]:
    """Check Audio Influence against its slot's range and Vocal Gender against a Voice."""
    findings = []
    source = (audio_source or "").strip().lower()
    if audio_influence is not None and source in ("persona", "voice"):
        try:
            value = float(audio_influence)
        except (TypeError, ValueError):
            value = None
        lo, hi = PERSONA_AUDIO_INFLUENCE_RANGE if source == "persona" else VOICE_AUDIO_INFLUENCE_RANGE
        if value is None:
            findings.append({
                "severity": "high",
                "category": "range",
                "issue": f"Audio Influence '{audio_influence}' is not a number.",
                "fix": f"Give a percentage in the {source} range ({lo}-{hi}%).",
            })
        elif not lo <= value <= hi:
            other = "voice" if source == "persona" else "persona"
            findings.append({
                "severity": "high",
                "category": "range",
                "issue": f"Audio Influence {value:g}% is outside the {source} range ({lo}-{hi}%). A {other} value on a {source} slot is the usual cause.",
                "fix": f"Choose a value in {lo}-{hi}% for a {source}.",
                "data": {"audio_influence": value, "audio_source": source, "range": [lo, hi]},
            })
    if source == "voice" and (vocal_gender or "").strip():
        findings.append({
            "severity": "medium",
            "category": "consistency",
            "issue": f"Vocal Gender '{vocal_gender}' is set alongside a Voice. The Voice already defines the singer; a gender setting can fight it.",
            "fix": "Leave Vocal Gender empty when a Voice is active.",
        })
    return findings


def _tag(findings: list, field: str) -> list:
    for f in findings:
        f["location"] = {"field": field}
    return findings


def build_report(style_findings: list, exclusion_findings: list, style_text: str, exclusion_text: str,
                 skill_path: str = "", *, model: str = "", wild_card_findings: list | None = None,
                 wild_card_text: str = "", control_findings: list | None = None) -> dict:
    """Build the standard output report."""
    all_findings = (
        _tag(style_findings, "style_prompt")
        + _tag(exclusion_findings, "exclusion_prompt")
        + _tag(wild_card_findings or [], "wild_card_prompt")
        + _tag(control_findings or [], "controls")
    )

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in all_findings:
        severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1

    status = "pass"
    if severity_counts["critical"] > 0:
        status = "fail"
    elif severity_counts["high"] > 0:
        status = "warning"

    metrics = {
        "model": model,
        "style_prompt_chars": len(style_text),
        "style_prompt_limit": get_limit_for_model(model) if model else STYLE_PROMPT_DEFAULT_MAX,
        "critical_zone": CRITICAL_ZONE,
        "exclusion_prompt_chars": len(exclusion_text) if exclusion_text else 0,
        "exclusion_recommended_max": EXCLUSION_RECOMMENDED_MAX,
    }
    if wild_card_text:
        metrics["wild_card_prompt_chars"] = len(wild_card_text)

    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "skill_path": skill_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "metrics": metrics,
        "findings": all_findings,
        "summary": {"total": len(all_findings), **severity_counts},
    }


def _load_package_file(path: Path) -> dict:
    text = path.read_text()
    if path.suffix.lower() == ".json":
        return json.loads(text)
    try:
        import yaml
    except ImportError:
        # Minimal fallback for flat one-line YAML fields.
        data = {}
        for line in text.splitlines():
            key, sep, value = line.partition(":")
            if sep and key.strip() in ("style_prompt", "exclusion_prompt", "model", "wild_card_prompt"):
                data[key.strip()] = value.strip().strip('"').strip("'")
        return data
    return yaml.safe_load(text) or {}


def _wild_card_text(package: dict) -> str:
    wc = package.get("wild_card")
    if isinstance(wc, dict):
        return wc.get("style_prompt", "") or ""
    if isinstance(wc, str):
        return wc
    return package.get("wild_card_prompt", "") or ""


def validate_package(package: dict, skill_path: str = "") -> dict:
    """Validate a whole package dict (the headless shape) and return the report."""
    model = package.get("model", "") or ""
    instrumental = bool(package.get("instrumental", False))
    style_text = package.get("style_prompt", "") or ""
    exclusion_text = package.get("exclusion_prompt", package.get("exclude_styles", "")) or ""
    wild_text = _wild_card_text(package)
    wild_model = package.get("wild_card", {}).get("model", model) if isinstance(package.get("wild_card"), dict) else model
    sliders = package.get("sliders") or {}

    return build_report(
        validate_style_prompt(style_text, model=model, instrumental=instrumental),
        validate_exclusion_prompt(exclusion_text),
        style_text, exclusion_text, skill_path,
        model=model,
        wild_card_findings=validate_style_prompt(wild_text, model=wild_model, instrumental=instrumental) if wild_text else [],
        wild_card_text=wild_text,
        control_findings=validate_controls(
            sliders.get("audio_influence"), sliders.get("audio_source", "") or "",
            package.get("vocal_gender", "") or "",
        ),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Validate a Suno style prompt package for limits, structure and safety triggers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Package fields (JSON via --stdin / --input-file): style_prompt, exclusion_prompt, model,
instrumental, wild_card.style_prompt (or wild_card_prompt), vocal_gender,
sliders.audio_influence + sliders.audio_source (voice|persona).

Examples:
  echo '{"style_prompt": "heartland rock, ...", "model": "v6"}' | %(prog)s --stdin
  %(prog)s --input-file package.json
  %(prog)s --style "indie folk-rock, warm analog..." --exclude "autotune" --model v6
        """,
    )
    parser.add_argument("file", nargs="?", help="Package file (.json, or .yaml/.yml) — same as --input-file")
    parser.add_argument("--input-file", help="Package file (.json, or .yaml/.yml when pyyaml is available)")
    parser.add_argument("--stdin", action="store_true", help="Read the package as JSON from stdin")
    parser.add_argument("--style", help="Style prompt text to validate")
    parser.add_argument("--exclude", default="", help="Exclusion prompt text to validate")
    parser.add_argument("--wild-card", default="", help="Wild-card style prompt text to validate")
    parser.add_argument("--model", default="", help="Suno model name for model-specific limits (e.g., 'v6', 'v6-wild')")
    parser.add_argument("--instrumental", action="store_true", help="Instrumental track: scream triggers become informational")
    parser.add_argument("--audio-influence", type=float, default=None, help="Audio Influence percentage to range-check")
    parser.add_argument("--audio-source", default="", choices=["", "voice", "persona"], help="What the Audio Influence slot holds")
    parser.add_argument("--vocal-gender", default="", help="Vocal Gender setting (should be empty with a Voice)")
    parser.add_argument("-o", "--output", help="Output file path (defaults to stdout)")
    parser.add_argument("--verbose", action="store_true", help="Include debug information on stderr")
    parser.add_argument("--skill-path", default="", help="Skill path for report context")

    args = parser.parse_args()

    package_path = args.input_file or args.file
    try:
        if args.stdin:
            package = json.loads(sys.stdin.read() or "{}")
        elif package_path:
            path = Path(package_path)
            if not path.exists():
                print(f"Error: File not found: {package_path}", file=sys.stderr)
                sys.exit(2)
            package = _load_package_file(path)
        elif args.style is not None:
            package = {"style_prompt": args.style, "exclusion_prompt": args.exclude}
        else:
            parser.print_help()
            sys.exit(2)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Error: could not parse package: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(package, dict):
        print("Error: package must be a JSON/YAML object", file=sys.stderr)
        sys.exit(2)

    # Flags fill in (or override) package fields.
    if args.model:
        package["model"] = args.model
    if args.instrumental:
        package["instrumental"] = True
    if args.wild_card:
        package["wild_card_prompt"] = args.wild_card
        package.pop("wild_card", None)
    if args.audio_influence is not None or args.audio_source:
        sliders = dict(package.get("sliders") or {})
        if args.audio_influence is not None:
            sliders["audio_influence"] = args.audio_influence
        if args.audio_source:
            sliders["audio_source"] = args.audio_source
        package["sliders"] = sliders
    if args.vocal_gender:
        package["vocal_gender"] = args.vocal_gender

    if args.verbose:
        print(f"Validating style prompt ({len(package.get('style_prompt', '') or '')} chars)...", file=sys.stderr)

    report = validate_package(package, args.skill_path)
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
