#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///

"""Validate a band profile YAML file against the profile schema.

Checks required fields, value constraints, tier/model consistency,
instrumental mode, style_baseline length, Voice and Custom Model gating,
the filename-matches-name rule, and the band's playlist YAML. Returns
structured JSON findings.

  validate-profile.py <slug>                    the saved profile {profiles}/<slug>.yaml
  validate-profile.py <path.yaml>               a profile file; its stem is the slug
  validate-profile.py <slug> --staged <path>    a draft/staged copy of band <slug>
                                                (e.g. {profiles}/drafts/<slug>.yaml)

Folders come from --project-root's module config (profile_paths.resolve_dirs),
so a staged file in drafts/ is checked against the band's real playlist and
songbook folders, not folders guessed from the draft's location.

--derive-filename "Band Name" prints the kebab-case filename and exits.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print(json.dumps({
        "script": "validate-profile",
        "status": "error",
        "error": "pyyaml is not installed. Run this script with `uv run`, which installs it.",
    }))
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
try:
    from suno_constants import (
        VALID_MODELS, VALID_TIERS, STYLE_PROMPT_LIMITS, STYLE_PROMPT_DEFAULT_MAX, FREE_TIER_MODEL,
        RETIRED_MODELS, MODEL_RETIREMENT_DATE, DEFAULT_MODEL,
    )
    from profile_paths import derive_slug, resolve_dirs
except ImportError as exc:
    print(json.dumps({
        "script": "validate-profile",
        "status": "error",
        "error": (
            f"Could not import this skill's helpers ({exc}). The skill's scripts/ folder "
            "is incomplete; reinstall the suno module."
        ),
    }))
    sys.exit(2)

VALID_GENDERS = {"male", "female", "nonbinary", "any"}
VALID_CREATIVITY = {"conservative", "balanced", "experimental"}
STYLE_BASELINE_MAX = STYLE_PROMPT_DEFAULT_MAX
STYLE_BASELINE_MAX_V4 = STYLE_PROMPT_LIMITS["v4 Pro"]
MAX_GENERATION_HISTORY = 10


def derive_filename(band_name: str) -> str:
    """A band name as its profile filename (the shared slug plus .yaml)."""
    return f"{derive_slug(band_name)}.yaml"


def validate_profile(profile_path: Path, docs_dir: Path | None = None,
                     songbook_dir: Path | None = None, slug: str | None = None) -> dict:
    """Validate a profile YAML file and return structured findings.

    slug: the band this file belongs to. Defaults to the file's stem; pass it
    for a staged copy whose filename is not the band's.
    docs_dir: the folder holding the canonical playlist YAML
    (`{docs_dir}/{slug}-playlist.yaml`). Defaults to the profile's
    grandparent, i.e. the parent of the band-profiles folder.
    songbook_dir: the songbook root (`{songbook_dir}/{slug}/` holds the band's
    entries). Defaults to `{docs_dir}/songbook`.
    """
    findings = []
    script_name = "validate-profile"

    if not profile_path.exists():
        return {
            "script": script_name,
            "version": "2.0.0",
            "skill_path": str(profile_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "fail",
            "findings": [{
                "severity": "critical",
                "category": "structure",
                "location": {"file": str(profile_path)},
                "issue": "Profile file does not exist",
                "fix": f"Create the profile at {profile_path}"
            }],
            "summary": {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0}
        }

    try:
        with open(profile_path) as f:
            profile = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return {
            "script": script_name,
            "version": "2.0.0",
            "skill_path": str(profile_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "fail",
            "findings": [{
                "severity": "critical",
                "category": "structure",
                "location": {"file": str(profile_path)},
                "issue": f"Invalid YAML: {e}",
                "fix": "Fix YAML syntax errors"
            }],
            "summary": {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0}
        }

    if not isinstance(profile, dict):
        return {
            "script": script_name,
            "version": "2.0.0",
            "skill_path": str(profile_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "fail",
            "findings": [{
                "severity": "critical",
                "category": "structure",
                "location": {"file": str(profile_path)},
                "issue": "Profile is not a YAML mapping",
                "fix": "Profile must be a YAML dictionary/mapping at the top level"
            }],
            "summary": {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0}
        }

    is_instrumental = profile.get("instrumental", False) is True

    # Required top-level string fields
    for field in ["name", "genre", "mood", "model_preference", "tier", "style_baseline"]:
        val = profile.get(field)
        if not val or not isinstance(val, str) or not val.strip():
            findings.append({
                "severity": "critical",
                "category": "structure",
                "location": {"file": str(profile_path), "field": field},
                "issue": f"Required field '{field}' is missing or empty",
                "fix": f"Add a non-empty '{field}' field to the profile"
            })

    # model_preference validation
    model = profile.get("model_preference", "")
    if model and model not in VALID_MODELS:
        findings.append({
            "severity": "high",
            "category": "consistency",
            "location": {"file": str(profile_path), "field": "model_preference"},
            "issue": f"Invalid model_preference '{model}'",
            "fix": f"Must be one of: {', '.join(sorted(VALID_MODELS))}"
        })
    elif model in RETIRED_MODELS:
        findings.append({
            "severity": "medium",
            "category": "consistency",
            "location": {"file": str(profile_path), "field": "model_preference"},
            "issue": (
                f"model_preference '{model}' was retired by Suno on {MODEL_RETIREMENT_DATE} "
                "and can no longer generate — new generations run on the v6 family"
            ),
            "fix": (
                f"Set model_preference to '{DEFAULT_MODEL}' ('v6-wild' for exploratory work, "
                f"'{FREE_TIER_MODEL}' on the Free tier)"
            )
        })

    # tier validation
    tier = profile.get("tier", "")
    if tier and tier not in VALID_TIERS:
        findings.append({
            "severity": "high",
            "category": "consistency",
            "location": {"file": str(profile_path), "field": "tier"},
            "issue": f"Invalid tier '{tier}'",
            "fix": f"Must be one of: {', '.join(sorted(VALID_TIERS))}"
        })

    # style_baseline length — model-aware
    baseline = profile.get("style_baseline", "")
    if isinstance(baseline, str):
        max_len = STYLE_BASELINE_MAX_V4 if model == "v4 Pro" else STYLE_BASELINE_MAX
        if len(baseline) > max_len:
            findings.append({
                "severity": "high",
                "category": "consistency",
                "location": {"file": str(profile_path), "field": "style_baseline"},
                "issue": f"style_baseline is {len(baseline)} chars (max {max_len} for {model or 'this model'})",
                "fix": f"Trim style_baseline to {max_len} characters. Front-load essential descriptors in the first 200 chars."
            })

    # vocal section — skip required checks if instrumental
    vocal = profile.get("vocal", {})
    if not is_instrumental:
        if not isinstance(vocal, dict):
            findings.append({
                "severity": "high",
                "category": "structure",
                "location": {"file": str(profile_path), "field": "vocal"},
                "issue": "'vocal' must be a mapping",
                "fix": "Define vocal as a YAML mapping with gender, tone, delivery, energy fields"
            })
        else:
            # A Voice defines gender and timbre, so gender is optional with voice_id (rule 17).
            has_voice = bool(str(vocal.get("voice_id") or "").strip())
            required_vocal = ["tone", "delivery", "energy"] if has_voice else ["gender", "tone", "delivery", "energy"]
            for vfield in required_vocal:
                val = vocal.get(vfield)
                if not val or not isinstance(val, str) or not val.strip():
                    findings.append({
                        "severity": "high",
                        "category": "structure",
                        "location": {"file": str(profile_path), "field": f"vocal.{vfield}"},
                        "issue": f"Required vocal field '{vfield}' is missing or empty",
                        "fix": f"Add a non-empty 'vocal.{vfield}' field (or set instrumental: true for instrumental projects)"
                    })

            gender = vocal.get("gender", "")
            if gender and gender not in VALID_GENDERS:
                findings.append({
                    "severity": "medium",
                    "category": "consistency",
                    "location": {"file": str(profile_path), "field": "vocal.gender"},
                    "issue": f"Invalid vocal gender '{gender}'",
                    "fix": f"Must be one of: {', '.join(sorted(VALID_GENDERS))}"
                })
    elif isinstance(vocal, dict):
        # Instrumental but vocal present — validate gender if provided
        gender = vocal.get("gender", "")
        if gender and gender not in VALID_GENDERS:
            findings.append({
                "severity": "medium",
                "category": "consistency",
                "location": {"file": str(profile_path), "field": "vocal.gender"},
                "issue": f"Invalid vocal gender '{gender}'",
                "fix": f"Must be one of: {', '.join(sorted(VALID_GENDERS))}"
            })

    # Tier-model consistency
    if tier == "free" and model and model != FREE_TIER_MODEL:
        findings.append({
            "severity": "medium",
            "category": "consistency",
            "location": {"file": str(profile_path), "field": "model_preference"},
            "issue": f"Free tier can only use '{FREE_TIER_MODEL}', but profile specifies '{model}'",
            "fix": f"Change model_preference to '{FREE_TIER_MODEL}' or upgrade tier"
        })

    # Slider warnings for free tier
    sliders = profile.get("sliders", {})
    if tier == "free" and isinstance(sliders, dict) and sliders:
        has_values = any(
            k in ("weirdness", "style_influence") and v is not None and v != 50
            for k, v in sliders.items()
        )
        if has_values:
            findings.append({
                "severity": "medium",
                "category": "consistency",
                "location": {"file": str(profile_path), "field": "sliders"},
                "issue": "Slider values set but free tier does not support Weirdness/Style Influence sliders",
                "fix": "Remove sliders section or upgrade to Pro/Premier tier"
            })

    # Slider range validation
    if isinstance(sliders, dict):
        for sname in ["weirdness", "style_influence", "audio_influence"]:
            sval = sliders.get(sname)
            if sval is not None:
                if not isinstance(sval, (int, float)) or sval < 0 or sval > 100:
                    findings.append({
                        "severity": "medium",
                        "category": "consistency",
                        "location": {"file": str(profile_path), "field": f"sliders.{sname}"},
                        "issue": f"Slider '{sname}' value {sval} out of range",
                        "fix": "Must be an integer between 0 and 100"
                    })

    # Exclusion defaults length check
    exclusions = profile.get("exclusion_defaults", [])
    if isinstance(exclusions, list):
        if len(exclusions) > 5:
            findings.append({
                "severity": "low",
                "category": "consistency",
                "location": {"file": str(profile_path), "field": "exclusion_defaults"},
                "issue": f"{len(exclusions)} exclusions defined (recommended max 5)",
                "fix": "Too many negatives can confuse the model. Prioritize the most important."
            })

    # creativity_default validation
    creativity = profile.get("creativity_default")
    if creativity is not None:
        if not isinstance(creativity, str) or creativity not in VALID_CREATIVITY:
            findings.append({
                "severity": "medium",
                "category": "consistency",
                "location": {"file": str(profile_path), "field": "creativity_default"},
                "issue": f"Invalid creativity_default '{creativity}'",
                "fix": f"Must be one of: {', '.join(sorted(VALID_CREATIVITY))}"
            })

    # language validation
    language = profile.get("language")
    if language is not None:
        if not isinstance(language, str) or not language.strip():
            findings.append({
                "severity": "low",
                "category": "consistency",
                "location": {"file": str(profile_path), "field": "language"},
                "issue": "language field is present but empty",
                "fix": "Provide a language value (e.g., 'English', 'Spanish') or remove the field"
            })

    # generation_history validation
    gen_history = profile.get("generation_history")
    if gen_history is not None:
        if not isinstance(gen_history, list):
            findings.append({
                "severity": "low",
                "category": "structure",
                "location": {"file": str(profile_path), "field": "generation_history"},
                "issue": "generation_history must be a list",
                "fix": "Set generation_history to a list of snapshot entries"
            })
        elif len(gen_history) > MAX_GENERATION_HISTORY:
            findings.append({
                "severity": "low",
                "category": "consistency",
                "location": {"file": str(profile_path), "field": "generation_history"},
                "issue": f"generation_history has {len(gen_history)} entries (max {MAX_GENERATION_HISTORY})",
                "fix": f"Keep only the {MAX_GENERATION_HISTORY} most recent or significant entries"
            })

    # studio_preferences validation — warn if not premier
    studio = profile.get("studio_preferences", {})
    if isinstance(studio, dict) and any(v is not None and v != "" for v in studio.values()):
        if tier and tier != "premier":
            findings.append({
                "severity": "medium",
                "category": "consistency",
                "location": {"file": str(profile_path), "field": "studio_preferences"},
                "issue": f"Studio preferences set but '{tier}' tier does not support Studio features",
                "fix": "Remove studio_preferences or upgrade to Premier tier"
            })
        # Validate BPM if present
        bpm = studio.get("bpm")
        if bpm is not None and not isinstance(bpm, (int, float)):
            findings.append({
                "severity": "low",
                "category": "consistency",
                "location": {"file": str(profile_path), "field": "studio_preferences.bpm"},
                "issue": f"BPM must be a number, got {type(bpm).__name__}",
                "fix": "Set bpm to a numeric value (e.g., 120)"
            })

    # Rule 17: a Voice defines gender and timbre; a stored gender invites
    # gender descriptors back into the style prompt.
    if isinstance(vocal, dict) and str(vocal.get("voice_id") or "").strip() \
            and str(vocal.get("gender") or "").strip():
        findings.append({
            "severity": "low",
            "category": "consistency",
            "location": {"file": str(profile_path), "field": "vocal.gender"},
            "issue": "vocal.gender is set alongside vocal.voice_id; the Voice already defines gender and timbre",
            "fix": "Clear vocal.gender and keep gender and timbre words out of style_baseline",
        })

    # Rule 19: Custom Models are Pro/Premier only.
    if str(profile.get("custom_model_id") or "").strip() and tier == "free":
        findings.append({
            "severity": "medium",
            "category": "consistency",
            "location": {"file": str(profile_path), "field": "custom_model_id"},
            "issue": "custom_model_id is set but the free tier cannot use Custom Models",
            "fix": "Clear custom_model_id, or set tier to pro or premier",
        })

    # Multi-Voice mapping validation (schema rules 20-21). Optional v5.5
    # Pro/Premier feature: a list of {voice_id, label, use_case} entries for
    # bands that use more than one cloned Voice. vocal.voice_id stays the
    # primary/default; `voices` carries the rest.
    voices = profile.get("voices")
    if voices is not None:
        if not isinstance(voices, list):
            findings.append({
                "severity": "low",
                "category": "structure",
                "location": {"file": str(profile_path), "field": "voices"},
                "issue": "voices must be a list of {voice_id, label, use_case} entries",
                "fix": "Set voices to a list, or remove it and keep the single vocal.voice_id",
            })
        else:
            listed_ids = []
            for i, entry in enumerate(voices):
                if not isinstance(entry, dict):
                    findings.append({
                        "severity": "low",
                        "category": "structure",
                        "location": {"file": str(profile_path), "field": f"voices[{i}]"},
                        "issue": "Each voices entry must be a mapping with at least voice_id",
                        "fix": "Use {voice_id, label, use_case} per entry",
                    })
                    continue
                vid = entry.get("voice_id")
                if not vid or not isinstance(vid, str) or not vid.strip():
                    findings.append({
                        "severity": "medium",
                        "category": "structure",
                        "location": {"file": str(profile_path), "field": f"voices[{i}].voice_id"},
                        "issue": "voices entry is missing a non-empty voice_id",
                        "fix": "Every voices entry needs a voice_id (a Voice with no use-case is just vocal.voice_id)",
                    })
                else:
                    listed_ids.append(vid)
                if not entry.get("use_case"):
                    findings.append({
                        "severity": "low",
                        "category": "consistency",
                        "location": {"file": str(profile_path), "field": f"voices[{i}].use_case"},
                        "issue": "voices entry has no use_case (which track types it serves)",
                        "fix": "Add a use_case so the Style Prompt Builder can pick the per-track Voice",
                    })
            primary = vocal.get("voice_id") if isinstance(vocal, dict) else None
            if listed_ids and primary and primary not in listed_ids:
                findings.append({
                    "severity": "low",
                    "category": "consistency",
                    "location": {"file": str(profile_path), "field": "vocal.voice_id"},
                    "issue": "vocal.voice_id names a Voice absent from the voices list",
                    "fix": "Set vocal.voice_id to one of the listed voices entries (the primary/default)",
                })

    # Per-band playlist YAML check: a band with songbook entries needs its
    # {docs}/{slug}-playlist.yaml, the canonical source of track order.
    band_slug = slug or profile_path.stem  # e.g. docs/band-profiles/paper-lanterns.yaml -> paper-lanterns

    # Rule 16: the filename is the kebab-case slug of the band's name, so a
    # lookup by name finds the file.
    name_val = profile.get("name")
    if isinstance(name_val, str) and name_val.strip():
        expected = derive_slug(name_val)
        if expected and band_slug != expected:
            findings.append({
                "severity": "low",
                "category": "structure",
                "location": {"file": str(profile_path), "field": "name"},
                "issue": (f"Filename slug '{band_slug}' does not match the name "
                          f"'{name_val}' (expected '{expected}.yaml')"),
                "fix": (f"Keep the name and file in step: rename the profile to {expected}.yaml "
                        "(Duplicate under the name, then Delete the old slug), or restore the name"),
            })
    # Playlist folder: explicit docs_dir, else the band-profiles folder's parent.
    resolved_docs_dir = docs_dir if docs_dir is not None else profile_path.parent.parent
    songbook_root = songbook_dir if songbook_dir is not None else resolved_docs_dir / "songbook"
    songbook_dir = songbook_root / band_slug
    playlist_yaml = resolved_docs_dir / f"{band_slug}-playlist.yaml"
    if songbook_dir.is_dir() and any(songbook_dir.glob("*.md")):
        if not playlist_yaml.exists():
            findings.append({
                "severity": "high",
                "category": "structure",
                "location": {"file": str(profile_path), "expected_file": str(playlist_yaml)},
                "issue": (
                    f"Band has songbook entries at {songbook_dir} but no canonical "
                    f"playlist YAML at {playlist_yaml}. Per-band playlist YAML is the "
                    f"single source of truth for sequencing."
                ),
                "fix": (
                    f"Run scaffold-playlist.py {band_slug} --from-songbook to bootstrap it from "
                    f"the songbook entries, then fill in the audio file names."
                ),
            })

    # Deprecated: an in-profile `playlist:` block (track order lives in the playlist YAML).
    if "playlist" in profile and isinstance(profile["playlist"], (dict, list)):
        findings.append({
            "severity": "medium",
            "category": "deprecation",
            "location": {"file": str(profile_path), "field": "playlist"},
            "issue": (
                "The profile carries a deprecated `playlist:` block. Track order lives only in "
                "the band's {slug}-playlist.yaml; two copies drift apart."
            ),
            "fix": (
                f"Move the track list to {playlist_yaml} (scaffold-playlist.py {band_slug} "
                f"bootstraps it), then remove the `playlist:` block "
                f"from this profile YAML. Sequencing-history narrative notes can move to "
                f"the band's playlist-ordering.md if you maintain one."
            ),
        })

    # Summary
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = f.get("severity", "low")
        if sev in severity_counts:
            severity_counts[sev] += 1

    status = "pass"
    if severity_counts["critical"] > 0:
        status = "fail"
    elif severity_counts["high"] > 0:
        status = "fail"
    elif severity_counts["medium"] > 0:
        status = "warning"

    return {
        "script": script_name,
        "version": "2.2.0",
        "skill_path": str(profile_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "findings": findings,
        "summary": {
            "total": len(findings),
            **severity_counts
        }
    }


def _looks_like_path(value: str) -> bool:
    return value.endswith((".yaml", ".yml")) or "/" in value or "\\" in value


def main():
    parser = argparse.ArgumentParser(
        description="Validate a band profile YAML file against the profile schema.",
        epilog="Exit codes: 0=pass or warning, 1=fail, 2=error",
    )
    parser.add_argument(
        "profile", nargs="?",
        help=("Band slug (validates {profiles}/<slug>.yaml) or a path to a profile file "
              "(its stem is the slug). With --staged, the slug of the band the staged file belongs to."),
    )
    parser.add_argument(
        "--staged", metavar="PATH",
        help="Validate this staged/draft file as band <profile> (e.g. {profiles}/drafts/<slug>.yaml).",
    )
    parser.add_argument("-o", "--output", help="Output file (defaults to stdout)")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostics to stderr")
    parser.add_argument(
        "--derive-filename", metavar="BAND_NAME",
        help="Convert a band name to its kebab-case filename and exit",
    )
    parser.add_argument(
        "--project-root",
        help=("Project root; folders come from its module config (modules.suno). Without it, "
              "a profile path's own folder is the profiles folder (drafts/ counts as its parent)."),
    )
    parser.add_argument("--profiles-dir", help="Band profiles folder (overrides config).")
    parser.add_argument(
        "--docs-dir",
        help="Folder holding the band's {slug}-playlist.yaml (default: the profiles folder's parent).",
    )
    parser.add_argument(
        "--songbook-dir",
        help="Songbook root holding {slug}/ entries (default: songbook_folder from config, else {docs-dir}/songbook).",
    )
    args = parser.parse_args()

    if args.derive_filename:
        output = json.dumps({
            "band_name": args.derive_filename,
            "slug": derive_slug(args.derive_filename),
            "filename": derive_filename(args.derive_filename),
        }, indent=2)
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)
        sys.exit(0)

    if not args.profile:
        parser.error("a band slug or profile path is required (unless --derive-filename)")

    if args.staged:
        slug = Path(args.profile).stem if _looks_like_path(args.profile) else args.profile
        target = Path(args.staged)
    elif _looks_like_path(args.profile):
        target = Path(args.profile)
        slug = target.stem
    else:
        slug, target = args.profile, None

    profiles_dir = args.profiles_dir
    if profiles_dir is None and args.project_root is None and target is not None and not args.staged:
        # No project root: the file's own folder is the profiles folder; a file
        # in drafts/ is a draft of a profile one level up.
        folder = target.resolve().parent
        profiles_dir = folder.parent if folder.name == "drafts" else folder
    dirs = resolve_dirs(args.project_root or ".", profiles_dir=profiles_dir,
                        docs_dir=args.docs_dir, songbook_dir=args.songbook_dir)
    if target is None:
        target = dirs["profiles_dir"] / f"{slug}.yaml"

    if args.verbose:
        print(f"Validating {target} as band '{slug}' (docs: {dirs['docs_dir']}, "
              f"songbook: {dirs['songbook_dir']})", file=sys.stderr)

    result = validate_profile(target, docs_dir=dirs["docs_dir"],
                              songbook_dir=dirs["songbook_dir"], slug=slug)
    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output)
        if args.verbose:
            print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)

    sys.exit(1 if result["status"] == "fail" else 0)


if __name__ == "__main__":
    main()
