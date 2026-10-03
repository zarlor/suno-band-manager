#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Find references to an old value across the catalog docs and the sanctum.

Reconciliation used to have the model search a dozen locations by hand for an
old song title, band name or file name after it changed. This script does the
search; the model keeps the judgment (is a hit an intentional historical
reference such as "formerly known as", or drift?) and the in-context rewrite
after the owner approves.

Searched (relative to the project root):
  docs/songbook/**/*.md            docs/band-profiles/*.yaml|*.md
  docs/*-playlist.yaml             docs/*-playlist-ordering.md
  docs/*-playlist-sequencing.md    docs/voice-context-*.md
  docs/wip-*.md                    every file in a voice file's Companion Files table
  sanctum MEMORY.md, INDEX.md, chronology.md, patterns.md
  sanctum sessions/*.md            only with --include-sessions (raw logs are history)

Match kinds, per line (strongest only):
  exact     the old value as written
  casefold  the old value in different casing
  subtitle  the old value's main title without its subtitle / parenthetical /
            version suffix (only when the old value has one)
  partial   the first significant word of a multi-word old value, as a whole
            word (only with --partial; noisy by design)

Also lists `docs/...` file references (backticked paths) in the searched files
whose target is not on disk.

Usage:
    uv run scripts/find-stale-refs.py "{project-root}" --old "Old Title" [--new "New Title"]
    uv run scripts/find-stale-refs.py "{project-root}" --paths-only
    uv run scripts/find-stale-refs.py --help

Output: JSON (default) or text. Exit 0 on a completed scan, 2 on bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SANCTUM_REL = ("_bmad", "_memory", "band-manager-sidecar")
SANCTUM_FILES = ("MEMORY.md", "INDEX.md", "chronology.md", "patterns.md")
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".txt"}

_SUBTITLE_SPLIT_RE = re.compile(r"\s+[—–-]\s+|:\s+|\s*\(|\|")
_VERSION_RE = re.compile(r"\s+v\d+$", re.IGNORECASE)
_STOPWORDS = {"the", "and", "for", "from", "with", "into", "that", "this", "your", "our"}
_DOCS_REF_RE = re.compile(r"`(docs/[^`\s]+)`")
_COMPANION_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|", re.MULTILINE)


def companion_paths(voice_text: str) -> list[str]:
    """First-column paths of a voice file's Companion Files table."""
    m = re.search(
        r"^##\s+Companion Files.*?$(.*?)(?=^##\s)", voice_text + "\n## ", re.MULTILINE | re.DOTALL
    )
    return [p.strip() for p in _COMPANION_ROW_RE.findall(m.group(1))] if m else []


def search_set(project_root: Path, sanctum: Path, include_sessions: bool) -> list[Path]:
    """The defined file set, deduplicated, in a stable order."""
    docs = project_root / "docs"
    files: list[Path] = []
    if docs.is_dir():
        files += sorted((docs / "songbook").rglob("*.md")) if (docs / "songbook").is_dir() else []
        bp = docs / "band-profiles"
        if bp.is_dir():
            files += sorted(p for p in bp.iterdir() if p.suffix in (".yaml", ".yml", ".md"))
        for pattern in (
            "*-playlist.yaml",
            "*-playlist-ordering.md",
            "*-playlist-sequencing.md",
            "voice-context-*.md",
            "wip-*.md",
        ):
            files += sorted(docs.glob(pattern))
        for voice in sorted(docs.glob("voice-context-*.md")):
            try:
                text = voice.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for ref in companion_paths(text):
                target = project_root / ref
                if target.is_file() and target.suffix in TEXT_SUFFIXES:
                    files.append(target)
    for name in SANCTUM_FILES:
        if (sanctum / name).is_file():
            files.append(sanctum / name)
    if include_sessions and (sanctum / "sessions").is_dir():
        files += sorted((sanctum / "sessions").glob("*.md"))
    seen: set[Path] = set()
    unique = []
    for f in files:
        r = f.resolve()
        if r not in seen:
            seen.add(r)
            unique.append(f)
    return unique


def base_title(old: str) -> str | None:
    """The old value without a subtitle, parenthetical or version suffix."""
    base = _SUBTITLE_SPLIT_RE.split(old, 1)[0].strip()
    base = _VERSION_RE.sub("", base).strip()
    return base if base and base != old.strip() and len(base) >= 4 else None


def first_word(old: str) -> str | None:
    words = re.findall(r"[\w']+", old)
    if len(words) < 2:
        return None
    for w in words:
        if len(w) >= 4 and w.casefold() not in _STOPWORDS:
            return w
    return None


def classify(line: str, old: str, base: str | None, word_re: re.Pattern | None) -> str | None:
    if old in line:
        return "exact"
    folded = line.casefold()
    if old.casefold() in folded:
        return "casefold"
    if base and base.casefold() in folded:
        return "subtitle"
    if word_re is not None and word_re.search(line):
        return "partial"
    return None


def preview(line: str, old: str, new: str) -> str:
    return re.sub(re.escape(old), lambda _m: new, line, flags=re.IGNORECASE)


def scan(
    project_root: Path,
    old: str | None,
    new: str | None = None,
    sanctum: Path | None = None,
    include_sessions: bool = False,
    partial: bool = False,
) -> dict:
    sanctum = sanctum or project_root.joinpath(*DEFAULT_SANCTUM_REL)
    files = search_set(project_root, sanctum, include_sessions)
    base = base_title(old) if old else None
    word = first_word(old) if (old and partial) else None
    word_re = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE) if word else None

    hits: list[dict] = []
    missing: list[dict] = []
    seen_missing: set[tuple[str, str]] = set()
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            rel = path.relative_to(project_root).as_posix()
        except ValueError:
            rel = str(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if old:
                kind = classify(line, old, base, word_re)
                if kind:
                    hit = {
                        "file": rel,
                        "line": lineno,
                        "match_kind": kind,
                        "context": line.strip()[:240],
                    }
                    if new is not None and kind in ("exact", "casefold"):
                        hit["preview"] = preview(line.strip(), old, new)[:240]
                    hits.append(hit)
            for ref in _DOCS_REF_RE.findall(line):
                target = ref.split("#", 1)[0].rstrip(".,;:")
                if any(c in target for c in "*?{}<>\u2013"):
                    continue  # templates and globs, not single files
                if (project_root / target).exists() or (rel, target) in seen_missing:
                    continue
                seen_missing.add((rel, target))
                missing.append({"file": rel, "line": lineno, "target": target})

    by_kind: dict[str, int] = {}
    for h in hits:
        by_kind[h["match_kind"]] = by_kind.get(h["match_kind"], 0) + 1
    return {
        "status": "ok",
        "old": old,
        "new": new,
        "files_searched": len(files),
        "sessions_included": include_sessions,
        "hit_count": len(hits),
        "hits_by_kind": by_kind,
        "hits": hits,
        "missing_targets": missing,
    }


def format_text(report: dict) -> str:
    lines = [
        f"Stale-reference scan — old={report['old']!r}"
        + (f" new={report['new']!r}" if report["new"] is not None else ""),
        f"{report['files_searched']} files searched"
        + ("" if report["sessions_included"] else " (sanctum sessions/ skipped)")
        + f"; {report['hit_count']} hit(s) {report['hits_by_kind']}",
        "",
    ]
    for h in report["hits"]:
        lines.append(f"[{h['match_kind']}] {h['file']}:{h['line']}  {h['context']}")
        if "preview" in h:
            lines.append(f"    -> {h['preview']}")
    if report["missing_targets"]:
        lines += ["", "Referenced files not on disk:"]
        lines += [f"  {m['file']}:{m['line']}  {m['target']}" for m in report["missing_targets"]]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Find references to an old value (song title, band name, file name) "
            "across the songbook, band profiles, playlist YAMLs and docs, voice "
            "files and their Companion Files, WIPs and the sanctum. Reports each "
            "hit with file, line, context and match kind; lists docs/ file "
            "references whose target is missing. Deciding which hits are drift "
            "stays with the caller."
        )
    )
    parser.add_argument("project_root", nargs="?", default=".", help="Project root (default: .)")
    parser.add_argument("--old", help="The value being replaced")
    parser.add_argument("--new", help="The new value — adds a per-hit replacement preview")
    parser.add_argument("--paths-only", action="store_true", help="Only list missing file targets")
    parser.add_argument("--partial", action="store_true", help="Also match the old value's first significant word")
    parser.add_argument("--include-sessions", action="store_true", help="Also search the sanctum's raw sessions/ logs")
    parser.add_argument("--sanctum-dir", default=None, help="Override the sanctum directory")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format (default: json)")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(json.dumps({"status": "error", "message": f"project root not found: {project_root}"}))
        return 2
    if not args.old and not args.paths_only:
        print(json.dumps({"status": "error", "message": "give --old VALUE, or --paths-only"}))
        return 2
    if args.old is not None and not args.old.strip():
        print(json.dumps({"status": "error", "message": "--old must not be empty"}))
        return 2

    report = scan(
        project_root,
        None if args.paths_only else args.old,
        args.new,
        Path(args.sanctum_dir).resolve() if args.sanctum_dir else None,
        args.include_sessions,
        args.partial,
    )
    print(json.dumps(report, indent=2) if args.format == "json" else format_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
