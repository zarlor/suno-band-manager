#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Genre coverage index (v3): what a band has actually used, extracted, not inferred.

The point: Mac must not claim "X is fresh / never done" when the band has done
it. Earlier versions guessed which prose phrases were artist references (Title
Case regexes, stop lists, a noise filter) and treated a style prompt's first
clause as its genre. Both guesses failed silently: references with digits
("Blink-182") vanished, and a v6 prompt's first clause is often not a genre.

v3 only extracts. Per band it writes `docs/<band>-genre-coverage.md` with:
  - the profile's curated fields: genre, reference_tracks, style_alternatives,
    each voice profile's use_case, and each catalog entry's genre_applied
  - explicitly labeled "Reference territory:" lines from songbook entries
  - every songbook entry's style prompt, verbatim, with its status

The model judges coverage by reading that compact set. Absence from the index
never proves a direction is fresh on its own — grep the songbook and profile
before any never-done claim.

Each index records a fingerprint of its sources (songbook entries + profile),
so `--check` can say deterministically whether it is stale.

Usage:
    uv run scripts/genre-coverage.py <project-root> [--band <slug>]
    uv run scripts/genre-coverage.py <project-root> --check [--band <slug>]
Writes docs/<band>-genre-coverage.md (text outside the AUTOGEN markers is kept).
`--check` writes nothing and exits 1 when any band's index is stale or missing.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys

import yaml

AUTOGEN_START = "<!-- AUTOGEN-START: genre-coverage -->"
AUTOGEN_END = "<!-- AUTOGEN-END: genre-coverage -->"
FINGERPRINT_RE = re.compile(r"<!-- sources-sha256: ([0-9a-f]{64}) -->")


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def title_of(text, fb):
    m = re.search(r'^title:\s*"?(.*?)"?\s*$', text, re.M)
    if m and m.group(1).strip():
        return m.group(1).strip()
    m = re.search(r'^#\s+(.+)$', text, re.M)
    return m.group(1).strip() if m else fb


def status_of(text):
    m = re.search(r'^status:\s*(.+)$', text, re.M)
    return m.group(1).strip().lower() if m else "unknown"


def first_style_prompt(text):
    m = re.search(r'^#{2,}\s.*style prompt.*$', text, re.I | re.M)
    if not m:
        return None
    cb = re.search(r'```[a-zA-Z0-9]*\n(.*?)```', text[m.end():], re.S)
    return cb.group(1).strip() if cb else None


def _one_line(s):
    return re.sub(r"\s+", " ", str(s)).strip()


def labeled_territory(text):
    """Explicitly labeled `Reference territory:` lines (a curated label)."""
    return [_one_line(m.group(1)).strip("*").strip()
            for m in re.finditer(r'Reference territory\**\s*:\**\s*([^\n]+)', text, re.I)]


def profile_fields(profile):
    """Curated fields from a parsed band profile, verbatim."""
    if not isinstance(profile, dict):
        return {}
    out = {}
    if profile.get("genre"):
        out["genre"] = _one_line(profile["genre"])
    refs = profile.get("reference_tracks") or []
    if isinstance(refs, list):
        out["reference_tracks"] = [_one_line(r) for r in refs if str(r).strip()]
    alts = profile.get("style_alternatives") or {}
    if isinstance(alts, dict):
        out["style_alternatives"] = [(str(k), _one_line(v)) for k, v in alts.items() if str(v).strip()]
    elif isinstance(alts, list):
        out["style_alternatives"] = [("", _one_line(v)) for v in alts if str(v).strip()]
    voices = profile.get("voice_profiles") or []
    if isinstance(voices, list):
        out["voice_use_cases"] = [
            (str(v.get("name", "")), _one_line(v["use_case"]))
            for v in voices if isinstance(v, dict) and v.get("use_case")
        ]
    catalog = profile.get("catalog") or []
    if isinstance(catalog, list):
        out["genre_applied"] = [
            (str(c.get("title", "")), _one_line(c["genre_applied"]))
            for c in catalog if isinstance(c, dict) and c.get("genre_applied")
        ]
    return {k: v for k, v in out.items() if v}


def band_sources(project_root, band, songbook_dir):
    """The files a band's index is built from, as (relpath, abspath) pairs."""
    files = [(os.path.join("docs", "songbook", band, fn), os.path.join(songbook_dir, fn))
             for fn in sorted(os.listdir(songbook_dir)) if fn.endswith(".md")]
    profile = os.path.join(project_root, "docs", "band-profiles", f"{band}.yaml")
    if os.path.exists(profile):
        files.append((os.path.join("docs", "band-profiles", f"{band}.yaml"), profile))
    return files


def fingerprint(sources):
    h = hashlib.sha256()
    for rel, path in sources:
        h.update(rel.replace(os.sep, "/").encode("utf-8"))
        with open(path, "rb") as f:
            h.update(hashlib.sha256(f.read()).digest())
    return h.hexdigest()


def collect_band(project_root, band, songbook_dir):
    songs, territory = [], []
    for fn in sorted(os.listdir(songbook_dir)):
        if not fn.endswith(".md"):
            continue
        text = read(os.path.join(songbook_dir, fn))
        title = title_of(text, fn[:-3])
        for t in labeled_territory(text):
            territory.append((title, t))
        songs.append({"title": title, "status": status_of(text),
                      "style_prompt": first_style_prompt(text)})
    fields, profile_scanned = {}, False
    profile = os.path.join(project_root, "docs", "band-profiles", f"{band}.yaml")
    if os.path.exists(profile):
        profile_scanned = True
        try:
            fields = profile_fields(yaml.safe_load(read(profile)))
        except yaml.YAMLError:
            fields = {}
    return songs, territory, fields, profile_scanned


def render(band, songs, territory, fields, profile_scanned, ts, digest):
    with_prompt = [s for s in songs if s["style_prompt"]]
    L = [AUTOGEN_START, f"<!-- sources-sha256: {digest} -->", f"# {band} — Genre Coverage",
         f"_Generated by `genre-coverage.py` on {ts}. Extracted fields only — curated "
         f"band-profile fields, labeled reference-territory lines, and every style prompt "
         f"verbatim. Nothing here is inferred from prose. Read it before any fresh / "
         f"never-done / variety claim, and judge coverage from what is written: a genre is "
         f"often covered under an artist name. Absence here does not prove a direction is "
         f"fresh — grep the songbook and profile before saying it was never done._", "",
         f"**{len(songs)} songbook entries ({len(with_prompt)} with a style prompt) · "
         f"band profile {'scanned' if profile_scanned else 'NOT FOUND'}.**", ""]
    if fields.get("genre"):
        L += ["## Band genre (profile)", "", fields["genre"], ""]
    if fields.get("reference_tracks"):
        L += ["## Core influences (profile reference_tracks)", ""]
        L += [f"- {r}" for r in fields["reference_tracks"]] + [""]
    if fields.get("style_alternatives"):
        L += ["## Style alternatives (profile)", ""]
        L += [f"- **{k}:** {v}" if k else f"- {v}" for k, v in fields["style_alternatives"]] + [""]
    if fields.get("voice_use_cases"):
        L += ["## Voice use cases (profile voice_profiles)", ""]
        L += [f"- **{n}:** {u}" for n, u in fields["voice_use_cases"]] + [""]
    if fields.get("genre_applied"):
        L += ["## Per-song applied genre (profile catalog)", ""]
        L += [f"- **{t}:** {g}" for t, g in fields["genre_applied"]] + [""]
    if territory:
        L += ["## Labeled reference territory (songbook)", ""]
        L += [f"- **{t}:** {v}" for t, v in territory] + [""]
    L += ["## Style prompts (verbatim)", ""]
    for s in sorted(songs, key=lambda x: x["title"].lower()):
        prompt = _one_line(s["style_prompt"]) if s["style_prompt"] else "_(no style prompt block)_"
        L.append(f"- **{s['title']}** ({s['status']}): {prompt}")
    L.append(AUTOGEN_END)
    return "\n".join(L) + "\n"


def doc_path(project_root, band):
    return os.path.join(project_root, "docs", f"{band}-genre-coverage.md")


def write_doc(project_root, band, body):
    out = doc_path(project_root, band)
    if os.path.exists(out):
        ex = read(out)
        if AUTOGEN_START in ex and AUTOGEN_END in ex:
            new = re.sub(re.escape(AUTOGEN_START) + r".*?" + re.escape(AUTOGEN_END),
                         lambda _m: body.strip(), ex, flags=re.DOTALL)
            with open(out, "w", encoding="utf-8") as f:
                f.write(new)
            return out
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)
    return out


def check_band(project_root, band, songbook_dir):
    """'current' | 'stale' | 'missing' for one band's index."""
    out = doc_path(project_root, band)
    if not os.path.exists(out):
        return "missing"
    m = FINGERPRINT_RE.search(read(out))
    digest = fingerprint(band_sources(project_root, band, songbook_dir))
    return "current" if m and m.group(1) == digest else "stale"


def main():
    ap = argparse.ArgumentParser(
        description="Build the per-band genre-coverage index from extracted fields "
        "(profile genre, reference_tracks, style_alternatives, voice use_case, catalog "
        "genre_applied, labeled reference-territory lines, verbatim style prompts). "
        "Writes docs/<band>-genre-coverage.md (AUTOGEN section preserved-around). "
        "--check reports stale or missing indexes without writing.")
    ap.add_argument("project_root", help="Project root directory")
    ap.add_argument("--band", help="Limit to a single band slug (default: all bands)")
    ap.add_argument("--timestamp", default=None,
                    help="Timestamp for the doc header (default: now, ISO 8601 UTC)")
    ap.add_argument("--check", action="store_true",
                    help="Write nothing; exit 1 when any band's index is stale or missing")
    ap.add_argument("--format", choices=["text", "json"], default="text",
                    help="Output format for the run summary (default: text)")
    args = ap.parse_args()
    songbook = os.path.join(args.project_root, "docs", "songbook")
    if not os.path.isdir(songbook):
        # Empty catalog (fresh project, first session) is a normal no-op, not an
        # error: a Pulse wake or a first save calls this before any song exists.
        if args.format == "json":
            print(json.dumps({"bands": [], "band_count": 0}, indent=2))
        else:
            print(f"No songbook at {songbook} yet — empty catalog, nothing to index.")
        return 0
    bands = [args.band] if args.band else sorted(
        d for d in os.listdir(songbook) if os.path.isdir(os.path.join(songbook, d)))
    ts = args.timestamp or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = []
    for band in bands:
        bd = os.path.join(songbook, band)
        if not os.path.isdir(bd):
            continue
        if args.check:
            state = check_band(args.project_root, band, bd)
            results.append({"band": band, "index": state, "output": doc_path(args.project_root, band)})
            if args.format == "text":
                print(f"{band}: {state}")
            continue
        songs, territory, fields, scanned = collect_band(args.project_root, band, bd)
        digest = fingerprint(band_sources(args.project_root, band, bd))
        out = write_doc(args.project_root, band,
                        render(band, songs, territory, fields, scanned, ts, digest))
        results.append({
            "band": band,
            "entries": len(songs),
            "style_prompts": sum(1 for s in songs if s["style_prompt"]),
            "profile_scanned": scanned,
            "influences": len(fields.get("reference_tracks", [])),
            "applied": len(fields.get("genre_applied", [])),
            "labeled_territory": len(territory),
            "output": out,
        })
        if args.format == "text":
            print(f"{band}: {len(songs)} entries, profile={'yes' if scanned else 'NO'}, "
                  f"{results[-1]['influences']} influences, {results[-1]['applied']} applied, "
                  f"{len(territory)} labeled territory -> {out}")
    if args.format == "json":
        print(json.dumps({"bands": results, "band_count": len(results)}, indent=2))
    if args.check and any(r["index"] != "current" for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
