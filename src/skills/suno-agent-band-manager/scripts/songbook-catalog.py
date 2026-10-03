#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Per-song songbook extract for browsing, lookup and pattern tallies.

Browse Songbook, Refine Song's song lookup and save-memory's pattern pass used
to read every songbook entry by hand to list, filter or count. This script does
the extraction once and emits compact JSON; the model keeps the judgment
(mood or genre search, "how has my sound evolved", whether a tally is a pattern
worth recording).

Per song: band, title, status (published = frontmatter and body marker agree),
date, published date, model, settings (from the entry's Settings table or
bullets), style prompt (preview, or full with --full-prompts), source_wip, path.
Per band: song and published counts, model counts, and slider value counts.

Filters: --band SLUG, --since YYYY-MM-DD (song date or publish date on/after),
--model TEXT (substring of the model), --status published|wip, --title TEXT
(case-insensitive substring — for "which one are we refining?" lookups).

Songbook parsing reuses validate-sidecar.py (load_all_songs), so there is one
songbook parser.

Usage:
    uv run scripts/songbook-catalog.py "{project-root}" [--band SLUG] [--since DATE]
        [--model TEXT] [--status published|wip] [--title TEXT] [--full-prompts]
        [--format json|text]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_validate_sidecar():
    mod_path = Path(__file__).resolve().parent / "validate-sidecar.py"
    spec = spec_from_file_location("validate_sidecar", mod_path)
    mod = module_from_spec(spec)
    sys.modules["validate_sidecar"] = mod
    spec.loader.exec_module(mod)
    return mod


_vs = _load_validate_sidecar()

SETTING_KEYS = (
    "Model",
    "Voice",
    "Persona",
    "Custom Model",
    "Vocal Gender",
    "Lyrics Mode",
    "Duration",
    "Max Mode",
    "Weirdness",
    "Style Influence",
    "Audio Influence",
    "Variety",
    "Personalize",
)
SLIDERS = ("Weirdness", "Style Influence", "Audio Influence", "Variety", "Max Mode")
PREVIEW_CHARS = 120

_KEY_ALT = "|".join(re.escape(k) for k in sorted(SETTING_KEYS, key=len, reverse=True))
_TABLE_ROW_RE = re.compile(rf"^\|\s*({_KEY_ALT})\s*\|\s*([^|]+?)\s*\|", re.MULTILINE | re.IGNORECASE)
_INLINE_RE = re.compile(rf"(?<![\w-])({_KEY_ALT})\s*:?\s*\**\s*([^·|\n*]+?)\s*\**\s*(?=·|\n|$)", re.IGNORECASE)


def _section(text: str, heading_re: str) -> str | None:
    m = re.search(rf"^#{{2,}}\s*{heading_re}.*$", text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    nxt = re.search(r"^#{1,2}\s", text[m.end():], re.MULTILINE)
    return text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():]


def extract_settings(text: str) -> dict[str, str]:
    """Settings from the entry's `## Settings` section (table rows or bullets)."""
    block = _section(text, r"Settings\b")
    if block is None:
        return {}
    canon = {k.casefold(): k for k in SETTING_KEYS}
    out: dict[str, str] = {}
    for key, value in _TABLE_ROW_RE.findall(block):
        out.setdefault(canon[key.casefold()], value.strip().strip("*").strip())
    for line in block.splitlines():
        if line.lstrip().startswith("|"):
            continue
        for key, value in _INLINE_RE.findall(line):
            out.setdefault(canon[key.casefold()], value.strip().strip("*").strip())
    return out


def extract_style_prompt(text: str) -> str | None:
    """The first code block after the first `## Style Prompt` heading."""
    m = re.search(r"^#{2,}\s.*style prompt.*$", text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    cb = re.search(r"```[a-zA-Z0-9]*\n(.*?)```", text[m.end():], re.DOTALL)
    return cb.group(1).strip() if cb else None


def _model(settings: dict[str, str], frontmatter_model: str | None) -> str | None:
    return settings.get("Model") or frontmatter_model


def _slider_value(raw: str) -> str:
    m = re.match(r"\s*(\d+)\s*%?", raw)
    return m.group(1) if m else raw.split("—")[0].split("(")[0].strip()


def build_catalog(
    project_root: Path,
    band: str | None = None,
    since: str | None = None,
    model: str | None = None,
    status: str | None = None,
    title: str | None = None,
    full_prompts: bool = False,
) -> dict:
    songs, parse_findings = _vs.load_all_songs(project_root)
    entries = []
    for s in songs:
        text = (project_root / s.path).read_text(encoding="utf-8")
        fm = _vs.FRONTMATTER_RE.match(text)
        try:
            front = (_vs.yaml.safe_load(fm.group(1)) or {}) if fm else {}
        except _vs.yaml.YAMLError:
            front = {}
        settings = extract_settings(text)
        prompt = extract_style_prompt(text)
        published_date = s.body_date or s.frontmatter_published
        entry = {
            "band": s.band,
            "title": s.title,
            "status": "published" if s.is_published else (s.frontmatter_status or "unknown"),
            "date": s.frontmatter_date,
            "published": published_date if s.is_published else None,
            "model": _model(settings, str(front.get("model")) if front.get("model") else None),
            "settings": settings,
            "style_prompt": prompt if full_prompts or prompt is None else prompt[:PREVIEW_CHARS],
            "style_prompt_chars": len(prompt) if prompt else 0,
            "source_wip": s.source_wip,
            "path": s.path.as_posix(),
        }
        if band and s.band != band:
            continue
        if status == "published" and entry["status"] != "published":
            continue
        if status == "wip" and entry["status"] == "published":
            continue
        if model and model.casefold() not in (entry["model"] or "").casefold():
            continue
        if title and title.casefold() not in s.title.casefold():
            continue
        if since and max(entry["date"] or "", entry["published"] or "") < since:
            continue
        entries.append(entry)

    entries.sort(key=lambda e: (e["band"], e["published"] or e["date"] or "", e["title"]))
    bands: dict[str, dict] = {}
    for e in entries:
        b = bands.setdefault(e["band"], {"songs": 0, "published": 0, "models": {}, "sliders": {}})
        b["songs"] += 1
        b["published"] += e["status"] == "published"
        if e["model"]:
            b["models"][e["model"]] = b["models"].get(e["model"], 0) + 1
        for slider in SLIDERS:
            if slider in e["settings"]:
                v = _slider_value(e["settings"][slider])
                counts = b["sliders"].setdefault(slider, {})
                counts[v] = counts.get(v, 0) + 1
    return {
        "status": "ok",
        "song_count": len(entries),
        "parse_errors": [f.to_dict() for f in parse_findings],
        "bands": bands,
        "songs": entries,
    }


def format_text(report: dict) -> str:
    lines = [f"Songbook — {report['song_count']} song(s)", ""]
    current = None
    for e in report["songs"]:
        if e["band"] != current:
            current = e["band"]
            b = report["bands"][current]
            lines += ["", f"## {current or '(no band)'} — {b['songs']} song(s), {b['published']} published"]
        when = e["published"] or e["date"] or "?"
        lines.append(f"- {e['title']} — {e['status']} {when}, {e['model'] or 'model ?'}")
        if e["style_prompt"]:
            lines.append(f"    {e['style_prompt']}")
    for err in report["parse_errors"]:
        lines.append(f"! {err['path']}: {err['message']}")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract a compact per-song catalog from docs/songbook/ (band, title, "
            "status, dates, model, settings, style prompt preview, source_wip) "
            "with per-band model and slider tallies. For browsing, song lookup "
            "and pattern detection; judging mood or evolution stays with the caller."
        )
    )
    parser.add_argument("project_root", nargs="?", default=".", help="Project root (default: .)")
    parser.add_argument("--band", help="Only this band slug")
    parser.add_argument("--since", metavar="YYYY-MM-DD", help="Only songs dated or published on/after this date")
    parser.add_argument("--model", help="Only songs whose model contains this text (e.g. v6)")
    parser.add_argument("--status", choices=["published", "wip"], help="Only published, or only unpublished")
    parser.add_argument("--title", help="Only titles containing this text (case-insensitive)")
    parser.add_argument("--full-prompts", action="store_true", help="Full style prompts instead of a preview")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format (default: json)")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(json.dumps({"status": "error", "message": f"project root not found: {project_root}"}))
        return 2
    report = build_catalog(
        project_root, args.band, args.since, args.model, args.status, args.title, args.full_prompts
    )
    print(json.dumps(report, indent=2) if args.format == "json" else format_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
