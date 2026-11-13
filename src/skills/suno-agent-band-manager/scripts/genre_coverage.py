#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
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

The songbook and band profiles are read from the module's `songbook_folder` and
`band_profiles_folder` answers (`modules.suno.*`, through BMad's resolver);
`docs/songbook` and `docs/band-profiles` by default.

Usage:
    uv run {skill-root}/scripts/genre_coverage.py <project-root> [--band <slug>]
    uv run {skill-root}/scripts/genre_coverage.py <project-root> --check [--band <slug>]
Writes docs/<band>-genre-coverage.md. Text outside the AUTOGEN markers is kept;
a doc that has no markers is kept whole below the new index
(`kept_unmarked_text` in the JSON row), never replaced.
`--check` writes nothing and exits 1 when any band's index is stale or missing.

Exit codes: 0 clean (an absent songbook is an empty catalog: 0); 1 when a band
profile fails to parse or a songbook entry is not UTF-8 text (the index is
still written, with the error recorded in it; `--check` reports
`profile_error`) or when `--check` finds a stale or missing index; 2 when the
project root does not exist, the module config cannot be read, PyYAML is
missing, or `--band` names a band with no songbook folder.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(json.dumps({
        "status": "error",
        "message": "PyYAML required. Run via `uv run` so the PEP 723 inline dependency block installs it automatically.",
    }))
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
import bmad_config  # noqa: E402  (vendored from src/_shared/ by dev-tools/sync-shared.py)

AUTOGEN_START = "<!-- AUTOGEN-START: genre-coverage -->"
AUTOGEN_END = "<!-- AUTOGEN-END: genre-coverage -->"
FINGERPRINT_RE = re.compile(r"<!-- sources-sha256: ([0-9a-f]{64}) -->")


def read(p):
    # utf-8-sig: a file saved with a byte-order mark reads the same as one without.
    with open(p, "r", encoding="utf-8-sig") as f:
        return f.read()


def content_dirs(project_root):
    """(songbook folder, band-profiles folder) as path strings.

    The module's `songbook_folder` and `band_profiles_folder` answers, read
    through BMad's resolver (`modules.suno.*`); `docs/songbook` and
    `docs/band-profiles` under the project root when there is no answer or no
    BMad config. A config that exists and cannot be read exits 2 with the reason.
    """
    try:
        cfg = bmad_config.module_config(project_root)
    except bmad_config.ConfigError as exc:
        print(f"ERROR: module config unreadable: {exc}", file=sys.stderr)
        sys.exit(2)

    def folder(key, default):
        value = cfg.get(key) or default
        return value if os.path.isabs(value) else os.path.join(project_root, value)

    return (folder("songbook_folder", os.path.join("docs", "songbook")),
            folder("band_profiles_folder", os.path.join("docs", "band-profiles")))


def rel_to(project_root, path):
    """`path` relative to the project root (the name it is fingerprinted and shown
    under); the path itself when it lies outside the project."""
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:  # another drive
        return path
    return path if rel.startswith("..") else rel


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


def profile_path(project_root, band, profiles_dir=None):
    return os.path.join(profiles_dir or content_dirs(project_root)[1], f"{band}.yaml")


def band_sources(project_root, band, songbook_dir, profiles_dir=None):
    """The files a band's index is built from, as (relpath, abspath) pairs."""
    files = [(rel_to(project_root, os.path.join(songbook_dir, fn)), os.path.join(songbook_dir, fn))
             for fn in sorted(os.listdir(songbook_dir)) if fn.endswith(".md")]
    profile = profile_path(project_root, band, profiles_dir)
    if os.path.exists(profile):
        files.append((rel_to(project_root, profile), profile))
    return files


def fingerprint(sources):
    h = hashlib.sha256()
    for rel, path in sources:
        h.update(rel.replace(os.sep, "/").encode("utf-8"))
        with open(path, "rb") as f:
            h.update(hashlib.sha256(f.read()).digest())
    return h.hexdigest()


def load_profile(project_root, band, profiles_dir=None):
    """(fields, scanned, error) for a band's profile; error is a message or None."""
    profile = profile_path(project_root, band, profiles_dir)
    if not os.path.exists(profile):
        return {}, False, None
    try:
        return profile_fields(yaml.safe_load(read(profile))), True, None
    except (yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
        return {}, True, f"{rel_to(project_root, profile)}: {_one_line(exc)}"


def collect_band(project_root, band, songbook_dir, profiles_dir=None):
    """(songs, territory, profile fields, profile scanned, profile error).

    An entry that cannot be read as UTF-8 text stays in `songs` with status
    `unreadable` and an `error`, so it is listed in the index instead of
    stopping the run or dropping out of it.
    """
    songs, territory = [], []
    for fn in sorted(os.listdir(songbook_dir)):
        if not fn.endswith(".md"):
            continue
        try:
            text = read(os.path.join(songbook_dir, fn))
        except (OSError, UnicodeDecodeError) as exc:
            songs.append({"title": fn[:-3], "status": "unreadable", "style_prompt": None,
                          "error": f"{rel_to(project_root, os.path.join(songbook_dir, fn))}: {_one_line(exc)}"})
            continue
        title = title_of(text, fn[:-3])
        for t in labeled_territory(text):
            territory.append((title, t))
        songs.append({"title": title, "status": status_of(text),
                      "style_prompt": first_style_prompt(text)})
    fields, profile_scanned, profile_error = load_profile(project_root, band, profiles_dir)
    return songs, territory, fields, profile_scanned, profile_error


def render(band, songs, territory, fields, profile_scanned, ts, digest, profile_error=None):
    with_prompt = [s for s in songs if s["style_prompt"]]
    L = [AUTOGEN_START, f"<!-- sources-sha256: {digest} -->", f"# {band} — Genre Coverage",
         f"_Generated by `genre_coverage.py` on {ts}. Extracted fields only — curated "
         f"band-profile fields, labeled reference-territory lines, and every style prompt "
         f"verbatim. Nothing here is inferred from prose. Read it before any fresh / "
         f"never-done / variety claim, and judge coverage from what is written: a genre is "
         f"often covered under an artist name. Absence here does not prove a direction is "
         f"fresh — grep the songbook and profile before saying it was never done._", "",
         f"**{len(songs)} songbook entries ({len(with_prompt)} with a style prompt) · "
         f"band profile {'scanned' if profile_scanned else 'NOT FOUND'}.**", ""]
    if profile_error:
        L += ["## PROFILE ERROR — profile fields missing from this index", "",
              f"The band profile failed to parse, so its curated fields are absent below: "
              f"{profile_error}", ""]
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
        prompt = (_one_line(s["style_prompt"]) if s["style_prompt"]
                  else "_(entry could not be read: not UTF-8 text; its style prompt is missing here)_" if s.get("error")
                  else "_(no style prompt block)_")
        L.append(f"- **{s['title']}** ({s['status']}): {prompt}")
    L.append(AUTOGEN_END)
    return "\n".join(L) + "\n"


def doc_path(project_root, band):
    return os.path.join(project_root, "docs", f"{band}-genre-coverage.md")


def write_doc(project_root, band, body):
    """Write the index; returns (path, kept_unmarked).

    Text outside the AUTOGEN markers is kept. A doc that exists without both
    markers (hand-written, or a marker was deleted) is never replaced: the
    index goes on top and the text that was there follows it, whole
    (`kept_unmarked` is then True).
    """
    out = doc_path(project_root, band)
    kept_unmarked = False
    if os.path.exists(out):
        ex = read(out)
        if AUTOGEN_START in ex and AUTOGEN_END in ex:
            new = re.sub(re.escape(AUTOGEN_START) + r".*?" + re.escape(AUTOGEN_END),
                         lambda _m: body.strip(), ex, flags=re.DOTALL)
            with open(out, "w", encoding="utf-8") as f:
                f.write(new)
            return out, kept_unmarked
        if ex.strip():
            body = body + "\n" + ex
            kept_unmarked = True
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)
    return out, kept_unmarked


def check_band(project_root, band, songbook_dir, profiles_dir=None):
    """'current' | 'stale' | 'missing' | 'profile_error' for one band's index."""
    if load_profile(project_root, band, profiles_dir)[2]:
        return "profile_error"
    out = doc_path(project_root, band)
    if not os.path.exists(out):
        return "missing"
    try:
        m = FINGERPRINT_RE.search(read(out))
    except (OSError, UnicodeDecodeError):
        return "stale"
    digest = fingerprint(band_sources(project_root, band, songbook_dir, profiles_dir))
    return "current" if m and m.group(1) == digest else "stale"


def main():
    ap = argparse.ArgumentParser(
        description="Build the per-band genre-coverage index from extracted fields "
        "(profile genre, reference_tracks, style_alternatives, voice use_case, catalog "
        "genre_applied, labeled reference-territory lines, verbatim style prompts). "
        "Writes docs/<band>-genre-coverage.md (AUTOGEN section preserved-around). "
        "--check reports stale or missing indexes without writing.")
    ap.add_argument("project_root", help="Project root directory (exit 2 when it does not exist)")
    ap.add_argument("--band", help="Limit to a single band slug (default: all bands); exit 2 when "
                    "the band has no songbook folder")
    ap.add_argument("--timestamp", default=None,
                    help="Timestamp for the doc header (default: now, ISO 8601 UTC)")
    ap.add_argument("--check", action="store_true",
                    help="Write nothing; exit 1 when any band's index is stale or missing, "
                    "or its band profile fails to parse")
    ap.add_argument("--format", choices=["text", "json"], default="text",
                    help="Output format for the run summary (default: text)")
    args = ap.parse_args()
    if not os.path.isdir(args.project_root):
        # A wrong path is not an empty catalog: say so instead of "nothing to index".
        msg = f"project root not found: {args.project_root}"
        if args.format == "json":
            print(json.dumps({"status": "error", "error": msg}, indent=2))
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 2
    songbook, profiles = content_dirs(args.project_root)
    songbook_shown = rel_to(args.project_root, songbook).replace(os.sep, "/")
    if not os.path.isdir(songbook) and not args.band:
        # Empty catalog (fresh project, first session) is a normal no-op, not an
        # error: a Pulse wake or a first save calls this before any song exists.
        if args.format == "json":
            print(json.dumps({"bands": [], "band_count": 0}, indent=2))
        else:
            print(f"No songbook at {songbook} yet — empty catalog, nothing to index.")
        return 0
    known = sorted(d for d in os.listdir(songbook)
                   if os.path.isdir(os.path.join(songbook, d))) if os.path.isdir(songbook) else []
    if args.band and args.band not in known:
        msg = (f"Unknown band '{args.band}': no folder {songbook_shown}/{args.band}/. "
               f"Known bands: {', '.join(known) or '(none)'}.")
        if args.format == "json":
            print(json.dumps({"status": "error", "error": msg, "known_bands": known}, indent=2))
        else:
            print(msg, file=sys.stderr)
        return 2
    bands = [args.band] if args.band else known
    ts = args.timestamp or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = []
    for band in bands:
        bd = os.path.join(songbook, band)
        if args.check:
            state = check_band(args.project_root, band, bd, profiles)
            row = {"band": band, "index": state, "output": doc_path(args.project_root, band)}
            if state == "profile_error":
                row["profile_error"] = load_profile(args.project_root, band, profiles)[2]
            results.append(row)
            if args.format == "text":
                print(f"{band}: {state}" + (f" ({row['profile_error']})" if "profile_error" in row else ""))
            continue
        songs, territory, fields, scanned, perr = collect_band(args.project_root, band, bd, profiles)
        digest = fingerprint(band_sources(args.project_root, band, bd, profiles))
        out, kept_unmarked = write_doc(args.project_root, band,
                                       render(band, songs, territory, fields, scanned, ts, digest, perr))
        unreadable = [s["error"] for s in songs if s.get("error")]
        results.append({
            "band": band,
            "entries": len(songs),
            "style_prompts": sum(1 for s in songs if s["style_prompt"]),
            "profile_scanned": scanned,
            "influences": len(fields.get("reference_tracks", [])),
            "applied": len(fields.get("genre_applied", [])),
            "labeled_territory": len(territory),
            "profile_error": perr,
            # Entries that are not UTF-8 text: listed in the index without a style prompt.
            "unreadable_entries": unreadable,
            # True when the doc had no AUTOGEN markers: its text was kept below the new index.
            "kept_unmarked_text": kept_unmarked,
            "output": out,
        })
        if args.format == "text":
            print(f"{band}: {len(songs)} entries, profile={'ERROR' if perr else 'yes' if scanned else 'NO'}, "
                  f"{results[-1]['influences']} influences, {results[-1]['applied']} applied, "
                  f"{len(territory)} labeled territory -> {out}")
            if perr:
                print(f"{band}: profile error, index written without profile fields: {perr}",
                      file=sys.stderr)
            for item in unreadable:
                print(f"{band}: entry unreadable, listed without a style prompt: {item}", file=sys.stderr)
            if kept_unmarked:
                print(f"{band}: {out} had no AUTOGEN markers; its text was kept below the new index.",
                      file=sys.stderr)
    if args.format == "json":
        print(json.dumps({"bands": results, "band_count": len(results)}, indent=2))
    if args.check and any(r["index"] != "current" for r in results):
        return 1
    if any(r.get("profile_error") or r.get("unreadable_entries") for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
