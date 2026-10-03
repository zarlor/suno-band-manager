#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Parse and validate structured feedback input for headless mode.

Accepts the skill's headless flags (--feedback, --style-prompt, --model,
--sliders, --lyrics, --band-profile, --iteration-log) or a JSON blob, and
extracts structured dimensions for the Feedback Elicitor skill. Validates
required fields and normalizes the input structure for downstream processing.
The flag-to-key translation lives here so the calling model doesn't do it.

Exit codes:
  0 = valid input, structured output returned
  1 = validation failed (invalid structure or missing required fields)
  2 = runtime error
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
from suno_constants import VALID_MODELS

VALID_DIMENSIONS = [
    "music",
    "vocals",
    "energy",
    "structure",
    "lyrics",
    "vibe",
    "production",
    "tempo",
    "instrumentation",
    "length",
    "quality",
]

VALID_FEEDBACK_TYPES = ["clear", "positive", "vague", "contradictory", "technical"]


def flags_to_input(args: argparse.Namespace) -> dict[str, Any]:
    """Translate the skill's headless flags into the input JSON keys (deterministic).

    --feedback may be plain text or a JSON object carrying feedback_text (or feedback) plus
    optional pre-categorization (feedback_type, dimensions). --lyrics and --iteration-log are
    file paths; lyrics are read, the iteration log is passed through as a path.
    Raises ValueError for unreadable files or malformed --sliders JSON.
    """
    data: dict[str, Any] = {}
    fb = args.feedback
    try:
        parsed = json.loads(fb)
    except (json.JSONDecodeError, TypeError):
        parsed = None
    if isinstance(parsed, dict):
        data.update(parsed)
        if "feedback_text" not in data and "feedback" in data:
            data["feedback_text"] = data.pop("feedback")
    else:
        data["feedback_text"] = fb
    if args.style_prompt is not None:
        data["original_style_prompt"] = args.style_prompt
    if args.model is not None:
        data["model"] = args.model
    if args.sliders is not None:
        try:
            data["slider_settings"] = json.loads(args.sliders)
        except json.JSONDecodeError as e:
            raise ValueError(f"--sliders is not valid JSON: {e}") from e
    if args.lyrics is not None:
        try:
            data["original_lyrics"] = Path(args.lyrics).read_text(encoding="utf-8")
        except OSError as e:
            raise ValueError(f"--lyrics file could not be read: {args.lyrics} ({e.strerror})") from e
    if args.band_profile is not None:
        data["band_profile"] = args.band_profile
    if args.title is not None:
        data["title"] = args.title
    if args.iteration_log is not None:
        if not Path(args.iteration_log).is_file():
            raise ValueError(f"--iteration-log file not found: {args.iteration_log}")
        data["iteration_log_path"] = args.iteration_log
    return data


def validate_feedback_input(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate structured feedback input and return findings."""
    findings = []

    # feedback_text is required
    if not isinstance(data.get("feedback_text"), str) or not data["feedback_text"].strip():
        findings.append({
            "severity": "critical",
            "category": "structure",
            "location": {"field": "feedback_text"},
            "issue": "Missing or empty feedback_text field",
            "fix": "Provide feedback_text with the user's feedback about their Suno generation",
        })

    # Validate optional fields if present
    if "model" in data and data["model"] not in VALID_MODELS:
        findings.append({
            "severity": "info",
            "category": "consistency",
            "location": {"field": "model"},
            "issue": f"Unrecognized model '{data['model']}' — recommendations may not be model-optimized. Known models: {', '.join(sorted(VALID_MODELS))}",
            "fix": "This is informational — the model name will be passed through. Known models receive model-specific recommendations.",
        })

    if "dimensions" in data:
        if not isinstance(data["dimensions"], list):
            findings.append({
                "severity": "high",
                "category": "structure",
                "location": {"field": "dimensions"},
                "issue": "dimensions must be an array",
                "fix": "Provide dimensions as an array of strings",
            })
        else:
            for dim in data["dimensions"]:
                if dim not in VALID_DIMENSIONS:
                    findings.append({
                        "severity": "low",
                        "category": "consistency",
                        "location": {"field": "dimensions", "value": dim},
                        "issue": f"Unknown dimension '{dim}'. Valid: {', '.join(VALID_DIMENSIONS)}",
                        "fix": f"Use one of: {', '.join(VALID_DIMENSIONS)}",
                    })

    if "feedback_type" in data and data["feedback_type"] not in VALID_FEEDBACK_TYPES:
        findings.append({
            "severity": "medium",
            "category": "consistency",
            "location": {"field": "feedback_type"},
            "issue": f"Unknown feedback_type '{data['feedback_type']}'. Valid: {', '.join(VALID_FEEDBACK_TYPES)}",
            "fix": f"Use one of: {', '.join(VALID_FEEDBACK_TYPES)}",
        })

    if "slider_settings" in data:
        sliders = data["slider_settings"]
        if not isinstance(sliders, dict):
            findings.append({
                "severity": "medium",
                "category": "structure",
                "location": {"field": "slider_settings"},
                "issue": "slider_settings must be an object",
                "fix": "Provide as {\"weirdness\": 50, \"style_influence\": 50}",
            })
        else:
            for key in ["weirdness", "style_influence"]:
                if key in sliders:
                    val = sliders[key]
                    if not isinstance(val, (int, float)) or val < 0 or val > 100:
                        findings.append({
                            "severity": "medium",
                            "category": "consistency",
                            "location": {"field": f"slider_settings.{key}"},
                            "issue": f"{key} must be a number between 0 and 100",
                            "fix": f"Set {key} to a value between 0 and 100",
                        })

    return findings


def extract_structured_output(data: dict[str, Any]) -> dict[str, Any]:
    """Extract and normalize structured feedback for downstream processing."""
    output = {
        "feedback_text": str(data.get("feedback_text", "")).strip(),
        "context": {
            "original_style_prompt": data.get("original_style_prompt", ""),
            "original_lyrics": data.get("original_lyrics", ""),
            "band_profile": data.get("band_profile", ""),
            "model": data.get("model", ""),
            "slider_settings": data.get("slider_settings", {}),
            "intent": data.get("intent", ""),
            "iteration_log_path": data.get("iteration_log_path", ""),
            "title": data.get("title", ""),
        },
        "pre_categorized": {
            "feedback_type": data.get("feedback_type", ""),
            "dimensions": data.get("dimensions", []),
        },
    }

    # Strip empty context fields
    output["context"] = {k: v for k, v in output["context"].items() if v}
    output["pre_categorized"] = {k: v for k, v in output["pre_categorized"].items() if v}

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Parse and validate structured feedback input for Suno Feedback Elicitor headless mode.",
        epilog="""
Input JSON schema:
  Required:
    feedback_text (string) - The user's feedback about their Suno generation

  Optional context:
    original_style_prompt (string) - Style prompt used for generation
    original_lyrics (string) - Lyrics used for generation
    band_profile (string) - Band profile name used
    model (string) - Suno model used (v6, v6-wild, v6-mini; retired names still recognized)
    slider_settings (object) - {weirdness: 0-100, style_influence: 0-100}
    intent (string) - What the user was going for

  Optional pre-categorization:
    feedback_type (string) - clear, positive, vague, contradictory
    dimensions (array) - Problem dimensions: music, vocals, energy, structure, lyrics, vibe, production, tempo, instrumentation

Skill flags (headless) -> JSON keys:
  --feedback -> feedback_text (or a JSON object with feedback_text/feedback, feedback_type, dimensions)
  --style-prompt -> original_style_prompt   --model -> model
  --sliders -> slider_settings (JSON)       --lyrics PATH -> original_lyrics (file contents)
  --band-profile -> band_profile            --iteration-log PATH -> iteration_log_path
  --title -> title                          --no-write -> parsed.write = false

Example:
  uv run parse-feedback.py --feedback "vocals too polished" --style-prompt "warm indie rock" --model v6
  echo '{"feedback_text": "The guitar is too loud", "model": "v6"}' | uv run parse-feedback.py --stdin
  uv run parse-feedback.py --input feedback.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", "-i", help="Path to feedback JSON file")
    input_group.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    input_group.add_argument("--feedback", help="Feedback text, or a JSON object (skill headless flag)")
    parser.add_argument("--style-prompt", help="Original style prompt (with --feedback)")
    parser.add_argument("--model", help="Suno model used (with --feedback)")
    parser.add_argument("--sliders", help='Slider JSON, e.g. \'{"weirdness": 50, "style_influence": 70}\' (with --feedback)')
    parser.add_argument("--lyrics", help="Path to the original lyrics file (with --feedback)")
    parser.add_argument("--band-profile", help="Band profile name (with --feedback)")
    parser.add_argument("--iteration-log", help="Path to the song's iteration log (with --feedback)")
    parser.add_argument("--title", help="Song title, which names the iteration log (with --feedback)")
    parser.add_argument("--no-write", action="store_true",
                        help="Caller wants no durable writes; echoed as parsed.write = false")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output to stderr")

    args = parser.parse_args()
    flag_only = [n for n in ("style_prompt", "model", "sliders", "lyrics", "band_profile", "iteration_log", "title")
                 if getattr(args, n) is not None]
    if flag_only and args.feedback is None:
        parser.error(f"--{flag_only[0].replace('_', '-')} needs --feedback (with --stdin/--input, put it in the JSON)")

    try:
        if args.feedback is not None:
            data = flags_to_input(args)
        elif args.stdin:
            raw = sys.stdin.read()
        else:
            with open(args.input, "r") as f:
                raw = f.read()

        if args.feedback is None:
            data = json.loads(raw)
    except ValueError as e:
        if isinstance(e, json.JSONDecodeError):
            issue, fix = f"Invalid JSON: {e}", "Provide valid JSON input"
        else:
            issue, fix = str(e), "Check the flag value or file path"
        result = {
            "script": "parse-feedback",
            "version": "1.0.0",
            "status": "fail",
            "findings": [{
                "severity": "critical",
                "category": "structure",
                "location": {"field": "root"},
                "issue": issue,
                "fix": fix,
            }],
            "summary": {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
        }
        output_json = json.dumps(result, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_json)
        else:
            print(output_json)
        sys.exit(1)
    except FileNotFoundError:
        print(json.dumps({
            "script": "parse-feedback",
            "version": "1.0.0",
            "status": "fail",
            "findings": [{
                "severity": "critical",
                "category": "structure",
                "location": {"field": "input"},
                "issue": f"File not found: {args.input}",
                "fix": "Provide a valid file path",
            }],
            "summary": {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
        }, indent=2))
        sys.exit(1)

    if not isinstance(data, dict):
        result = {
            "script": "parse-feedback",
            "version": "1.0.0",
            "status": "fail",
            "findings": [{
                "severity": "critical",
                "category": "structure",
                "location": {"field": "root"},
                "issue": "Input must be a JSON object",
                "fix": "Provide a JSON object with at least a feedback_text field",
            }],
            "summary": {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
        }
        output_json = json.dumps(result, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_json)
        else:
            print(output_json)
        sys.exit(1)

    findings = validate_feedback_input(data)

    has_critical = any(f["severity"] == "critical" for f in findings)
    has_high = any(f["severity"] == "high" for f in findings)
    has_actionable = any(f["severity"] in ("critical", "high", "medium", "low") for f in findings)

    if has_critical or has_high:
        status = "fail"
    elif has_actionable:
        status = "warning"
    else:
        status = "pass"

    structured_output = extract_structured_output(data) if not has_critical else None

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f["severity"]
        if sev in severity_counts:
            severity_counts[sev] += 1

    result = {
        "script": "parse-feedback",
        "version": "1.0.0",
        "status": status,
        "findings": findings,
        "summary": {
            "total": len(findings),
            **severity_counts,
        },
    }

    if structured_output:
        structured_output["write"] = not args.no_write
        result["parsed"] = structured_output

    if args.verbose:
        print(f"[parse-feedback] Status: {status}, Findings: {len(findings)}", file=sys.stderr)

    output_json = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_json)
        if args.verbose:
            print(f"[parse-feedback] Output written to {args.output}", file=sys.stderr)
    else:
        print(output_json)

    sys.exit(0 if status in ("pass", "warning") else 1)


if __name__ == "__main__":
    main()
