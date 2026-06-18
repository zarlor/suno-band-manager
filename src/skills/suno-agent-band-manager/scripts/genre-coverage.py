#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Genre coverage index (v2) — COMPREHENSIVE: genre anchors AND artist / reference territory.

The point: Mac must KNOW what a band has actually used so it never again claims
"X is fresh / never done" when it isn't. v1 was an abject failure — it only read
songbook style-prompt anchors plus explicitly-labeled "Reference territory:" lines,
so inline artist references (e.g. From Now Until's "(Songs:Ohia / Red House Painters
/ Magnolia Electric Co territory)") — which live in the BAND PROFILE catalog's
genre_applied / reference_tracks / voice_profiles use_case — slipped right through.

v2 scans, per band:
  - every songbook entry's published style-prompt genre anchor
  - artist / reference-territory CLAUSES from BOTH the songbook entries AND the
    band-profile YAML (reference_tracks, genre_applied, voice use_case, notes):
      * parenthetical clauses naming a territory/direction/lineage/era/adjacent/signature
      * slash-separated proper-name lists (Counting Crows / Wallflowers / Wilco ...)
      * "X territory|direction|lineage|era" inline phrases
      * reference_tracks artists (the "Artist — description" list)
      * explicit "Reference territory:" lines

Usage:
    python genre-coverage.py <project-root> [--band <slug>] [--timestamp <iso>]
Writes docs/<band>-genre-coverage.md (AUTOGEN section preserved-around).
"""
import os
import re
import sys
import json
import argparse

AUTOGEN_START = "<!-- AUTOGEN-START: genre-coverage -->"
AUTOGEN_END = "<!-- AUTOGEN-END: genre-coverage -->"

# Capitalized terms that are NOT artist/territory references (reduce noise).
STOP = {
    "new orleans", "nola", "crescent city", "gulf coast", "camelot", "aeolian",
    "solitary fire", "lenny's voice", "lenny", "mac", "suno", "gemini", "bpm",
    "wip", "professional", "create", "creates", "voice", "intro", "verse",
    "chorus", "bridge", "outro", "breakdown", "fade out", "the room",
}

NAME = r"[A-Z][\w.'’&:!?+-]*(?:\s+[A-Z0-9][\w.'’&:!?+-]*){0,4}"


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


def anchors(prompt):
    parts = [p.strip() for p in prompt.replace("\n", " ").split(",") if p.strip()]
    return (parts[0] if parts else ""), (parts[1] if len(parts) > 1 else "")


def _clean(s):
    return re.sub(r'\s+', ' ', re.sub(r'\*+', '', s)).strip().strip('.,;')

# Free-text clauses are noise if they carry digits / stats / production-log words.
# (Does NOT apply to curated fields — reference_tracks / genre_applied — which may
# legitimately contain a year like "Round Here (1993)".)
NOISE_RE = re.compile(
    r'(\d|%|\bBPM\b|\bCamelot\b|\bvoice\b|\bgen\b|\bCreate|\bcredit|window|felt|'
    r'\bsession\b|\bHz\b|\bV\d|spectral|low-freq|chars?\b)', re.I)
# Title-Case proper-name token (no embedded digits) — for artist-list / territory matching.
TITLE = r"[A-Z][A-Za-z.'’&:+-]+(?:\s+[A-Z][A-Za-z.'’&:+-]+){0,3}"
# Suno section tags — reject slash-lists made of these (they're structure, not artists).
SECTION_WORDS = re.compile(
    r'\b(Intro|Verse|Pre-Chorus|Chorus|Post-Chorus|Bridge|Breakdown|Outro|'
    r'Final Chorus|Hook|Interlude|Drop|Build|Solo)\b', re.I)


def _noise(c):
    return (not c) or len(c) < 3 or c.lower() in STOP or bool(NOISE_RE.search(c))


def free_text_clauses(text):
    """Artist/territory mentions from prose — TIGHT filters so no stats/lyrics leak."""
    out = set()
    # slash-separated Title-Case proper-name lists (Counting Crows / Wallflowers / Wilco)
    for m in re.finditer(rf'({TITLE}(?:\s*/\s*{TITLE}){{1,}})', text):
        frag = _clean(m.group(1))
        if '/' in frag and not _noise(frag) and not SECTION_WORDS.search(frag):
            out.add(frag)
    # "ProperName ['song'] territory|direction|lineage|era|revival"
    for m in re.finditer(rf'({TITLE}(?:\s+["\'][^"\']{{1,40}}["\'])?)\s+(territory|direction|lineage|era|revival)\b', text):
        phrase = _clean(f"{m.group(1)} {m.group(2)}")
        if not _noise(phrase) and not SECTION_WORDS.search(phrase):
            out.add(phrase)
    # explicit "Reference territory:" labeled lines (curated; keep even with a year)
    for m in re.finditer(r'Reference territory[:\s]+([^\n]+)', text, re.I):
        out.add(_clean(m.group(1)))
    return out


def reference_tracks_block(profile_text):
    """Core influences — artist names from the profile reference_tracks list."""
    out = set()
    m = re.search(r'^reference_tracks:\s*\n(.*?)(?=^\S)', profile_text, re.M | re.S)
    if not m:
        return out
    for line in re.finditer(r'^\s*-\s*"([^"]+)"', m.group(1), re.M):
        artist = re.split(r'\s*[—(]\s*|\s+[-–]\s+', line.group(1), 1)[0]
        out.add(_clean(artist))
    return out


def genre_applied_map(profile_text):
    """Curated per-song genre+artist descriptions from the profile catalog (clean)."""
    out = []
    for m in re.finditer(r'-\s*title:\s*"?(.+?)"?\s*\n(.*?)(?=^\s*-\s*title:|\Z)',
                         profile_text, re.M | re.S):
        title = _clean(m.group(1))
        block = m.group(2)
        g = re.search(r'genre_applied:\s*(?:>\s*\n((?:[ \t]{5,}.*\n)+)|"?([^\n]+?)"?\s*$)',
                      block, re.M)
        if g:
            val = _clean(g.group(1) or g.group(2) or "")
            if val:
                out.append((title, val))
    return out


def collect_band(project_root, band, songbook_dir):
    rows, clauses = [], set()
    for fn in sorted(os.listdir(songbook_dir)):
        if not fn.endswith(".md"):
            continue
        text = read(os.path.join(songbook_dir, fn))
        clauses |= free_text_clauses(text)
        prompt = first_style_prompt(text)
        if prompt is None:
            continue
        a1, a2 = anchors(prompt)
        rows.append({"title": title_of(text, fn[:-3]), "status": status_of(text),
                     "anchor": a1, "anchor2": a2})
    influences, applied, profile_scanned = set(), [], False
    profile = os.path.join(project_root, "docs", "band-profiles", f"{band}.yaml")
    if os.path.exists(profile):
        ptext = read(profile)
        profile_scanned = True
        influences = {c for c in reference_tracks_block(ptext) if c and c.lower() not in STOP}
        applied = genre_applied_map(ptext)
        clauses |= free_text_clauses(ptext)
    clauses = {c for c in clauses if not _noise(c)}
    return (rows, sorted(influences, key=str.lower), applied,
            sorted(clauses, key=str.lower), profile_scanned)


def render(band, rows, influences, applied, clauses, profile_scanned, ts):
    L = [AUTOGEN_START, f"# {band} — Genre Coverage",
         f"_Generated by `genre-coverage.py` on {ts}. From published style prompts AND the "
         f"band-profile catalog (reference_tracks + per-song genre_applied) + filtered prose. "
         f"The source of truth for 'what has this band used' — consult BEFORE any "
         f"fresh/never-done/variety claim._", "",
         f"**{len(rows)} songbook entries · band profile {'scanned' if profile_scanned else 'NOT FOUND'}.**", ""]
    L += ["## Genre anchors used (style-prompt position 1, deduped)", ""]
    L += [f"- {a}" for a in sorted({r['anchor'].lower() for r in rows if r['anchor']})]
    if influences:
        L += ["", "## Core influences (band-profile reference_tracks)", ""]
        L += [f"- {c}" for c in influences]
    if applied:
        L += ["", "## Per-song applied genre + artist territory (profile catalog — curated)", ""]
        for title, val in applied:
            L.append(f"- **{title}:** {val}")
    L += ["", "## Other artist / reference territory cited (filtered prose)", "",
          "_A genre is often COVERED under an artist label — '90s alt' = Counting Crows / "
          "Wilco; sadcore = Songs:Ohia / Red House Painters. Check here too._", ""]
    L += [f"- {c}" for c in clauses]
    L += ["", "## Per-song genre anchor", "",
          "| Song | Status | Genre anchor | + 2nd descriptor |",
          "|------|--------|--------------|------------------|"]
    for r in sorted(rows, key=lambda x: x["title"].lower()):
        L.append(f"| {r['title']} | {r['status']} | {r['anchor']} | {r['anchor2']} |")
    L.append(AUTOGEN_END)
    return "\n".join(L) + "\n"


def write_doc(project_root, band, body):
    out = os.path.join(project_root, "docs", f"{band}-genre-coverage.md")
    if os.path.exists(out):
        ex = read(out)
        if AUTOGEN_START in ex and AUTOGEN_END in ex:
            new = re.sub(re.escape(AUTOGEN_START) + r".*?" + re.escape(AUTOGEN_END),
                         body.strip(), ex, flags=re.DOTALL)
            with open(out, "w", encoding="utf-8") as f:
                f.write(new)
            return out
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Build the genre-coverage index per band (anchors + artist/"
        "reference territory) so Mac never claims a direction is 'fresh' when it "
        "isn't. Writes docs/<band>-genre-coverage.md (AUTOGEN section preserved).")
    ap.add_argument("project_root", help="Project root directory")
    ap.add_argument("--band", help="Limit to a single band slug (default: all bands)")
    ap.add_argument("--timestamp", default="(unspecified)",
                    help="ISO timestamp stamped into the generated doc header")
    ap.add_argument("--format", choices=["text", "json"], default="text",
                    help="Output format for the run summary (default: text)")
    args = ap.parse_args()
    songbook = os.path.join(args.project_root, "docs", "songbook")
    if not os.path.isdir(songbook):
        print(f"ERROR: {songbook} not found", file=sys.stderr)
        sys.exit(2)
    bands = [args.band] if args.band else sorted(
        d for d in os.listdir(songbook) if os.path.isdir(os.path.join(songbook, d)))
    results = []
    for band in bands:
        bd = os.path.join(songbook, band)
        if not os.path.isdir(bd):
            continue
        rows, influences, applied, clauses, scanned = collect_band(args.project_root, band, bd)
        out = write_doc(args.project_root, band,
                        render(band, rows, influences, applied, clauses, scanned, args.timestamp))
        results.append({
            "band": band,
            "entries": len(rows),
            "profile_scanned": scanned,
            "influences": len(influences),
            "applied": len(applied),
            "prose_refs": len(clauses),
            "output": out,
        })
        if args.format == "text":
            print(f"{band}: {len(rows)} entries, profile={'yes' if scanned else 'NO'}, "
                  f"{len(influences)} influences, {len(applied)} applied, "
                  f"{len(clauses)} prose refs -> {out}")
    if args.format == "json":
        print(json.dumps({"bands": results, "band_count": len(results)}, indent=2))


if __name__ == "__main__":
    main()
