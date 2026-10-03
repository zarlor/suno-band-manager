#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "ruamel.yaml>=0.18"]
# ///

"""Deterministic read/write owner for band profile YAML.

Profiles are owner data: craft notes live in YAML comments, list fields hold
months of accumulated learnings. Every write here keeps both.

Operations (exactly one per call):

  --save        Write a full profile (stdin or --in) under the derived/given
                slug. The input text is written verbatim, comments included.
                Refuses to overwrite an existing profile unless --force.
  --set         Merge field overrides (YAML mapping on stdin/--in, or
                --set-json) into an existing profile. Nested keys merge by
                dot path. A list override that would replace a non-empty list
                is refused unless --lists append|replace says which you mean.
  --append F    Append one entry (--append-json) to list field F (dot path
                allowed). Oldest entries are trimmed to --max, which defaults
                to the schema cap (generation_history: 10).
  --duplicate N Copy the profile to the slug of new name N and set its `name`
                to N; --bump-version increments `version`.
  --load        Emit the parsed profile as JSON (no transcription by hand).
  --delete      Archive the profile together with its decision log, draft and
                playlist YAML to {profiles}/archive/{slug}-{UTC stamp}/
                (--purge deletes instead). Without --confirm it only reports
                what it would touch. The songbook is never touched.

--stage PATH writes the result of --set/--append/--duplicate to PATH instead
of the profile, so it can be validated and diffed before the real write.

Comment preservation: the file is split into top-level key blocks; untouched
blocks are copied byte for byte, and only changed blocks are re-rendered.
Changed blocks are rendered with ruamel.yaml round-trip (keeps nested comments,
quote style and key order). Without ruamel the PyYAML fallback re-renders
changed blocks without their inner comments and reports `comments_dropped`.

Folders: --profiles-dir > suno.band_profiles_folder in
{project-root}/_bmad/config.yaml > {project-root}/docs/band-profiles. The
playlist YAML lives in --docs-dir, default the profiles folder's parent.

Output: JSON on stdout. Exit codes: 0=success, 1=fail (bad input, schema
violation, confirmation needed), 2=error.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_paths import resolve_dirs  # noqa: E402

SCRIPT_NAME = "apply-profile"

try:
    import yaml
except ImportError:
    print(json.dumps({
        "script": SCRIPT_NAME,
        "status": "error",
        "error": (
            "pyyaml is not installed. Run this script with `uv run` (which installs "
            "its dependencies), or do the profile write by hand following "
            "references/profile-schema.md, keeping every comment."
        ),
    }))
    sys.exit(2)

try:
    from ruamel.yaml import YAML as _RuamelYAML
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
    from ruamel.yaml.scalarstring import (
        DoubleQuotedScalarString, FoldedScalarString,
        LiteralScalarString, SingleQuotedScalarString,
    )
    HAVE_RUAMEL = True
    _STYLED = (DoubleQuotedScalarString, SingleQuotedScalarString,
               FoldedScalarString, LiteralScalarString)
except ImportError:  # pragma: no cover - exercised only without ruamel
    HAVE_RUAMEL = False
    _STYLED = ()

# Hard caps from references/profile-schema.md. Appends trim oldest to the cap.
LIST_CAPS = {"generation_history": 10}
# Entry shape per known list field: "str" or "map".
LIST_ENTRY_TYPES = {
    "generation_history": "map",
    "voices": "map",
    "generation_learnings": "str",
    "known_working_patterns": "str",
    "known_limitations": "str",
    "exclusion_defaults": "str",
    "reference_tracks": "str",
    "writer_voice.sample_quotes": "str",
}


class SchemaError(ValueError):
    """Input that would break the profile schema (exit 1, nothing written)."""


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def _derive_slug(band_name: str) -> str:
    """Convert a band name to a kebab-case slug (no extension)."""
    name = band_name.strip().lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_plain(value):
    """Strip ruamel wrapper types so values compare and serialize as plain data."""
    if isinstance(value, dict):
        return {str(k) if not isinstance(k, (int, float, bool)) else k: _to_plain(v)
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(v) for v in value]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, str):
        return str(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    return value


def _resolve_profiles_dir(args) -> Path:
    return resolve_dirs(args.project_root, profiles_dir=args.profiles_dir)["profiles_dir"]


def _fail(error: str, **extra) -> dict:
    return {"script": SCRIPT_NAME, "status": "fail", "error": error, **extra}


# --------------------------------------------------------------------------
# YAML backend: load / dump with comments where possible
# --------------------------------------------------------------------------

def _seq_indent(text: str) -> tuple[int, int]:
    """Detect list indentation (sequence, offset) from the existing file so a
    re-rendered block matches its neighbours. Default: dash flush with key."""
    prev = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and prev is not None and prev.rstrip().endswith(":"):
            key_indent = len(prev) - len(prev.lstrip())
            offset = max(0, (len(line) - len(line.lstrip())) - key_indent)
            return offset + 2, offset
        prev = line
    return 2, 0


def _ruamel(text: str = ""):
    y = _RuamelYAML()
    y.preserve_quotes = True
    y.width = 4096  # never re-wrap: wrapping long plain scalars adds trailing spaces
    seq, off = _seq_indent(text)
    y.indent(mapping=2, sequence=seq, offset=off)
    return y


def _load_tree(text: str):
    """Load YAML for editing: ruamel round-trip tree when available."""
    if HAVE_RUAMEL:
        return _ruamel(text).load(text)
    return yaml.safe_load(text)


def _dump_tree(tree, like_text: str) -> str:
    if HAVE_RUAMEL:
        buf = io.StringIO()
        _ruamel(like_text).dump(tree, buf)
        return buf.getvalue()
    return yaml.safe_dump(_to_plain(tree), sort_keys=False, allow_unicode=True,
                          default_flow_style=False)


_KEY_RE = re.compile(r"""("(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s#'"?\-][^#]*?)\s*:(?=\s|$)""")
_INLINE_RE = re.compile(r"""\s(#\s.*)$""")


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_standalone(line: str) -> bool:
    """A whole-line comment or a blank line."""
    s = line.strip()
    return not s or s.startswith("#")


def _lines(text_or_lines) -> list[str]:
    lines = (text_or_lines.splitlines(keepends=True) if isinstance(text_or_lines, str)
             else list(text_or_lines))
    return [ln if ln.endswith("\n") else ln + "\n" for ln in lines]


def _segments(text_or_lines, indent: int = 0):
    """Split YAML lines into the key blocks of one mapping level.

    Returns (segments, tail). Each segment is {"key", "head", "body"}: head is
    the blank/comment lines just above the key (no deeper than `indent`), kept
    from the original file; body is the key line plus everything nested under
    it. Tail is trailing blank/comment lines after the last block."""
    segs, pending, cur = [], [], None
    for line in _lines(text_or_lines):
        stripped = line.strip()
        trivia = (not stripped or stripped.startswith("---") or stripped.startswith("...")
                  or (stripped.startswith("#") and _indent_of(line) <= indent))
        m = _KEY_RE.match(line, indent) if _indent_of(line) == indent else None
        if m:
            key = m.group(1)
            if key[:1] in ("'", '"'):
                key = key[1:-1]
            cur = {"key": key.strip(), "head": pending, "body": [line]}
            pending = []
            segs.append(cur)
        elif trivia or cur is None:
            pending.append(line)
        else:
            cur["body"].extend(pending)
            pending = []
            cur["body"].append(line)
    return segs, pending


def _child_indent(body: list[str]):
    for ln in body[1:]:
        if not _is_standalone(ln):
            return _indent_of(ln)
    return None


def _merge_block(orig_body: list[str], new_body: list[str]) -> tuple[list[str], bool, bool]:
    """Fit a re-rendered block's comments to the original block.

    The renderer may move comments that belong to neighbouring blocks into
    this one (those are emitted from the original instead), and may lose
    comments of its own. Keep the block's own comment lines once each; append
    any it lost at the end of the block. Returns (lines, relocated, inline_dropped)."""
    want: dict[str, int] = {}
    for ln in orig_body[1:]:
        if _is_standalone(ln):
            want[ln.strip()] = want.get(ln.strip(), 0) + 1
    out = [new_body[0]]
    for ln in new_body[1:]:
        if _is_standalone(ln):
            key = ln.strip()
            if want.get(key, 0) > 0:
                want[key] -= 1
                out.append(ln)
            continue
        out.append(ln)
    while len(out) > 1 and not out[-1].strip():
        out.pop()
    lost = []
    for ln in orig_body[1:]:
        key = ln.strip()
        if key.startswith("#") and want.get(key, 0) > 0:
            want[key] -= 1
            lost.append(ln)
    out += lost
    merged = "".join(out)
    inline_dropped = any(
        m and m.group(1).strip() not in merged
        for m in (_INLINE_RE.search(ln.rstrip("\n")) for ln in orig_body))
    return out, bool(lost), inline_dropped


def _list_fast_path(key: str, body: list[str], old, new, like_text: str):
    """Keep a list block's existing item text when the edit only trims items
    from the front and/or appends at the end (the --append shape). Returns the
    new block lines, or None when the edit has another shape."""
    if not (isinstance(old, list) and isinstance(new, list) and old):
        return None
    if not body[0].split(" #", 1)[0].rstrip().endswith(":"):
        return None  # flow style like `key: [a, b]`
    items, pre, ind = [], [], None
    for ln in body[1:]:
        m = re.match(r"^( *)-(?: |$)", ln)
        if m and (ind is None or len(m.group(1)) == ind):
            ind = len(m.group(1))
            items.append([ln])
        elif items:
            items[-1].append(ln)
        else:
            pre.append(ln)
    if len(items) != len(old):
        return None
    for k in range(len(old) + 1):
        kept = old[k:]
        if new[:len(kept)] == kept:
            extras = new[len(kept):]
            break
    else:
        return None
    rendered = []
    if extras:
        lines = _lines(_dump_tree({key: extras}, like_text))[1:]
        m = re.match(r"^( *)-", lines[0]) if lines else None
        shift = ind - len(m.group(1)) if m else 0
        for ln in lines:
            if shift > 0 and ln.strip():
                ln = " " * shift + ln
            elif shift < 0 and ln.startswith(" " * -shift):
                ln = ln[-shift:]
            rendered.append(ln)
    return [body[0]] + pre + [ln for item in items[k:] for ln in item] + rendered


def _splice(o_lines, n_lines, old: dict, new: dict, indent: int, like_text: str,
            report: dict, prefix: str = "") -> list[str]:
    """Rebuild one mapping level: unchanged keys verbatim from the original,
    changed nested mappings recursively, other changed keys re-rendered."""
    o_segs, o_tail = _segments(o_lines, indent)
    n_by_key = {s["key"]: s for s in _segments(n_lines, indent)[0]}
    out, seen = [], set()
    for seg in o_segs:
        key, body = seg["key"], seg["body"]
        seen.add(key)
        out += seg["head"]
        if key in new and old.get(key) == new.get(key):
            out += body
            continue
        if key not in n_by_key:
            continue  # key removed
        n_body = n_by_key[key]["body"]
        ov, nv = old.get(key), new.get(key)
        if isinstance(ov, dict) and isinstance(nv, dict) and ov:
            ci, nci = _child_indent(body), _child_indent(n_body)
            if ci is not None and ci == nci and ci > indent:
                out += [body[0]] + _splice(body[1:], n_body[1:], ov, nv, ci, like_text,
                                           report, f"{prefix}{key}.")
                continue
        fast = _list_fast_path(key, body, ov, nv, like_text)
        if fast is not None:
            out += fast
            continue
        block, moved, lost_inline = _merge_block(body, n_body)
        out += block
        if moved:
            report["relocated"].append(prefix + key)
        if lost_inline:
            report["dropped"].append(prefix + key)
    out += o_tail
    for key, seg in n_by_key.items():
        if key not in seen:
            out += [ln for ln in seg["body"] if not _is_standalone(ln)]
    return out


def render_preserving(orig_text: str, tree) -> dict:
    """Render `tree`, reusing every untouched block of `orig_text` verbatim and
    re-rendering only what changed, down to the changed nested key.

    Returns {"text", "relocated": [keys], "dropped": [keys]}: relocated keys had
    comments moved to the end of their block; dropped keys lost an inline
    comment (only without ruamel)."""
    orig_plain = _to_plain(yaml.safe_load(orig_text)) or {}
    new_plain = _to_plain(tree)
    new_text = _dump_tree(tree, orig_text)
    report = {"relocated": [], "dropped": []}
    result = "".join(_splice(_lines(orig_text), _lines(new_text), orig_plain, new_plain,
                             0, orig_text, report))
    # Safety net: the spliced text must parse to exactly the new data.
    try:
        ok = _to_plain(yaml.safe_load(result)) == new_plain
    except yaml.YAMLError:
        ok = False
    if not ok:
        result, report["relocated"] = new_text, []
        if not HAVE_RUAMEL and "#" in orig_text:
            report["dropped"] = ["(whole file)"]
    return {"text": result, **report}


# --------------------------------------------------------------------------
# Tree edits
# --------------------------------------------------------------------------

def _match_style(old, new):
    """Keep the quote/block style of the value being replaced."""
    if HAVE_RUAMEL and isinstance(new, str) and isinstance(old, _STYLED):
        if isinstance(old, (FoldedScalarString, LiteralScalarString)) \
                and old.endswith("\n") and not new.endswith("\n"):
            new += "\n"  # keep the block scalar's chomping (`>` stays `>`)
        return type(old)(new)
    return new


def _block_list(items):
    if HAVE_RUAMEL:
        seq = CommentedSeq(items)
        seq.fa.set_block_style()
        return seq
    return list(items)


def _parent_and_leaf(data, dotted_key: str, create: bool = True):
    parts = dotted_key.split(".")
    cursor = data
    for part in parts[:-1]:
        nxt = cursor.get(part)
        if not isinstance(nxt, dict):
            if not create:
                return None, parts[-1]
            nxt = CommentedMap() if HAVE_RUAMEL else {}
            cursor[part] = nxt
        cursor = nxt
    return cursor, parts[-1]


def _set_nested(data: dict, dotted_key: str, value) -> bool:
    """Set a dot-notation key in a nested dict. Returns True if the value changed."""
    cursor, leaf = _parent_and_leaf(data, dotted_key)
    old = cursor.get(leaf)
    if _to_plain(old) == _to_plain(value):
        return False
    if isinstance(value, list):
        value = _block_list(value)
    cursor[leaf] = _match_style(old, value)
    return True


def _flatten(d: dict, prefix: str = "") -> dict:
    """Flatten a nested dict into dot-notation keys (for --set merge sources)."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and v:
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


def _check_entries(field: str, entries: list) -> None:
    kind = LIST_ENTRY_TYPES.get(field)
    for entry in entries:
        if kind == "str" and not (isinstance(entry, str) and entry.strip()):
            raise SchemaError(f"{field} entries must be non-empty strings; got {entry!r}.")
        if kind == "map" and not isinstance(entry, dict):
            raise SchemaError(f"{field} entries must be mappings; got {entry!r}.")
        if field == "voices" and not str(entry.get("voice_id") or "").strip():
            raise SchemaError("voices entries need a non-empty voice_id.")


def _append_entries(data: dict, field: str, entries: list, cap: int | None) -> dict:
    """Append entries to a list field, trimming oldest to the cap."""
    _check_entries(field, entries)
    cursor, leaf = _parent_and_leaf(data, field)
    current = cursor.get(leaf)
    if current is None:
        current = _block_list([])
    elif not isinstance(current, list):
        raise SchemaError(f"{field} is not a list (found {type(current).__name__}); "
                          "use --set to replace it.")
    elif HAVE_RUAMEL and isinstance(current, CommentedSeq) and current.fa.flow_style():
        current.fa.set_block_style()
    current.extend(entries)
    trimmed = 0
    if cap is not None and cap >= 0 and len(current) > cap:
        trimmed = len(current) - cap
        del current[:trimmed]
    cursor[leaf] = current
    return {"field": field, "appended": len(entries), "trimmed": trimmed, "length": len(current)}


def _check_caps(data: dict) -> None:
    for field, cap in LIST_CAPS.items():
        cursor, leaf = _parent_and_leaf(data, field, create=False)
        value = cursor.get(leaf) if cursor is not None else None
        if isinstance(value, list) and len(value) > cap:
            raise SchemaError(f"{field} holds {len(value)} entries; the schema cap is {cap}. "
                              f"Use --append (which trims oldest) or send at most {cap}.")


# --------------------------------------------------------------------------
# File-level helpers (kept for tests and simple callers)
# --------------------------------------------------------------------------

def _read_yaml(path: Path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _write_yaml(path: Path, data: dict) -> None:
    """Write plain data as a fresh file (no original text to preserve)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(_to_plain(data), sort_keys=False, allow_unicode=True,
                                   default_flow_style=False), encoding="utf-8")


def _read_input_text(args) -> str:
    return Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()


def _load_input_data(args) -> dict:
    data = yaml.safe_load(_read_input_text(args))
    if not isinstance(data, dict):
        raise ValueError("Input is not a YAML mapping")
    return data


def _edit_profile(args, target: Path, mutate) -> dict:
    """Load target, apply mutate(tree) -> result fields, write comment-preserving."""
    if not target.exists():
        return _fail(f"Profile not found: {target}")
    orig_text = target.read_text(encoding="utf-8")
    tree = _load_tree(orig_text)
    if not isinstance(tree, dict):
        return _fail(f"Existing profile is not a YAML mapping: {target}")
    try:
        fields = mutate(tree)
        _check_caps(tree)
    except SchemaError as e:
        return _fail(str(e))
    rendered = render_preserving(orig_text, tree)
    out_path = Path(args.stage) if getattr(args, "stage", None) else target
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered["text"], encoding="utf-8")
    result = {"script": SCRIPT_NAME, "status": "complete", "slug": args.slug,
              "profile_path": str(target), **fields, "timestamp": _now()}
    if getattr(args, "stage", None):
        result["staged_path"] = str(out_path)
    warnings = []
    if rendered["relocated"]:
        warnings.append("Comments kept but moved to the end of their block: "
                        + ", ".join(rendered["relocated"]))
    if rendered["dropped"]:
        result["comments_dropped"] = True
        warnings.append("ruamel.yaml unavailable; inline comments dropped in: "
                        + ", ".join(rendered["dropped"]))
    if warnings:
        result["warnings"] = warnings
    return result


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_save(args) -> dict:
    raw = _read_input_text(args)
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("Input is not a YAML mapping")
    slug = args.slug or _derive_slug(str(data.get("name", "")))
    if not slug:
        return _fail("No slug provided and profile has no 'name' to derive one from.")
    tmp = dict(data)
    _check_caps(tmp)
    profiles_dir = _resolve_profiles_dir(args)
    target = profiles_dir / f"{slug}.yaml"
    if target.exists() and not args.force:
        return _fail(f"Profile already exists: {target}. Use --set to edit it, or pass "
                     "--force to overwrite it.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(raw if raw.endswith("\n") else raw + "\n", encoding="utf-8")
    result = {"script": SCRIPT_NAME, "status": "complete", "operation": "save",
              "slug": slug, "profile_path": str(target), "timestamp": _now()}
    log = profiles_dir / f"{slug}.decision-log.md"
    if log.exists():
        result["existing_decision_log"] = str(log)
        result["warnings"] = [f"A decision log already exists for slug '{slug}'. It may "
                              "belong to an earlier band; confirm before appending to it."]
    return result


def cmd_set(args) -> dict:
    target = _resolve_profiles_dir(args) / f"{args.slug}.yaml"
    if args.set_json:
        overrides = json.loads(args.set_json)
    else:
        overrides = _load_input_data(args)
    if not isinstance(overrides, dict):
        return _fail("Override input is not a mapping.")
    mode = getattr(args, "lists", None)

    def mutate(tree):
        flat = _flatten(overrides)
        if mode is None:
            clobbered = []
            for dotted, value in flat.items():
                cursor, leaf = _parent_and_leaf(tree, dotted, create=False)
                current = cursor.get(leaf) if cursor is not None else None
                if (isinstance(value, list) and isinstance(current, list) and current
                        and _to_plain(current) != _to_plain(value)):
                    clobbered.append(dotted)
            if clobbered:
                raise SchemaError(
                    "List override would replace existing entries in: "
                    + ", ".join(clobbered)
                    + ". Pass --lists append to add to them, or --lists replace to overwrite.")
        changed, appends = [], []
        for dotted, value in flat.items():
            if mode == "append" and isinstance(value, list):
                cap = LIST_CAPS.get(dotted)
                info = _append_entries(tree, dotted, list(value), cap)
                appends.append(info)
                if info["appended"] or info["trimmed"]:
                    changed.append(dotted)
                continue
            if isinstance(value, list):
                _check_entries(dotted, value)
            if _set_nested(tree, dotted, value):
                changed.append(dotted)
        out = {"operation": "set", "fields_changed": changed}
        if appends:
            out["appends"] = appends
        return out

    return _edit_profile(args, target, mutate)


def cmd_append(args) -> dict:
    target = _resolve_profiles_dir(args) / f"{args.slug}.yaml"
    if args.append_json is not None:
        entry = json.loads(args.append_json)
    else:
        entry = yaml.safe_load(_read_input_text(args))
    if entry is None:
        return _fail("No entry given. Pass --append-json '<entry JSON>' (or the entry on stdin).")
    cap = args.max if args.max is not None else LIST_CAPS.get(args.append)

    def mutate(tree):
        info = _append_entries(tree, args.append, [entry], cap)
        return {"operation": "append", "fields_changed": [args.append], **info, "cap": cap}

    return _edit_profile(args, target, mutate)


def cmd_duplicate(args) -> dict:
    profiles_dir = _resolve_profiles_dir(args)
    source = profiles_dir / f"{args.slug}.yaml"
    if not source.exists():
        return _fail(f"Source profile not found: {source}")
    new_slug = _derive_slug(args.duplicate)
    if not new_slug:
        return _fail(f"Could not derive a slug from new name {args.duplicate!r}.")
    target = profiles_dir / f"{new_slug}.yaml"
    if target.exists() and not args.force and not getattr(args, "stage", None):
        return _fail(f"Target already exists: {target}. Pass --force to overwrite.")

    def mutate(tree):
        tree["name"] = _match_style(tree.get("name"), args.duplicate.strip())
        if args.bump_version:
            tree["version"] = int(tree.get("version") or 1) + 1
        return {}

    staged = getattr(args, "stage", None)
    if not staged:
        args.stage = str(target)  # write the copy to the new slug, not the source
    result = _edit_profile(args, source, mutate)
    if not staged:
        args.stage = None
        result.pop("staged_path", None)
    if result["status"] == "complete":
        result.update({"operation": "duplicate", "source": str(source),
                       "slug": new_slug, "profile_path": str(target)})
        log = profiles_dir / f"{new_slug}.decision-log.md"
        if log.exists():
            result["existing_decision_log"] = str(log)
    return result


def cmd_load(args) -> dict:
    target = _resolve_profiles_dir(args) / f"{args.slug}.yaml"
    if not target.exists():
        return _fail(f"Profile not found: {target}")
    data = _read_yaml(target)
    if not isinstance(data, dict):
        return _fail(f"Profile is not a YAML mapping: {target}")
    return {"script": SCRIPT_NAME, "status": "complete", "operation": "load",
            "slug": args.slug, "profile_path": str(target),
            "profile": json.loads(json.dumps(data, default=str))}


def cmd_delete(args) -> dict:
    dirs = resolve_dirs(args.project_root, profiles_dir=args.profiles_dir,
                        docs_dir=args.docs_dir, songbook_dir=args.songbook_dir)
    profiles_dir, slug = dirs["profiles_dir"], args.slug
    profile = profiles_dir / f"{slug}.yaml"
    if not profile.exists():
        return _fail(f"Profile not found: {profile}")
    candidates = [profile,
                  profiles_dir / f"{slug}.decision-log.md",
                  profiles_dir / "drafts" / f"{slug}.yaml",
                  dirs["docs_dir"] / f"{slug}-playlist.yaml"]
    found = [p for p in candidates if p.exists()]
    songbook = dirs["songbook_dir"] / slug
    left = [str(songbook)] if songbook.is_dir() else []
    action = "delete" if args.purge else "archive"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = profiles_dir / "archive" / f"{slug}-{stamp}"
    base = {"script": SCRIPT_NAME, "operation": "delete", "slug": slug, "action": action,
            "profile_path": str(profile), "left_in_place": left}
    if left:
        base["warnings"] = [f"Songbook entries at {songbook} were left in place."]
    if not args.confirm:
        return {**base, "status": "confirm_required",
                "would_remove": [str(p) for p in found],
                **({"archive_dir": str(archive_dir)} if action == "archive" else {}),
                "error": "Nothing removed. Re-run with --confirm once the owner has agreed."}
    removed = []
    if action == "archive":
        archive_dir.mkdir(parents=True, exist_ok=True)
    for p in found:
        if action == "archive":
            shutil.move(str(p), str(archive_dir / p.name))
        else:
            p.unlink()
        removed.append(str(p))
    out = {**base, "status": "complete", "removed": removed, "timestamp": _now()}
    if action == "archive":
        out["archive_dir"] = str(archive_dir)
    return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Deterministic read/write owner for band profile YAML (comment-preserving).",
        epilog="Exit codes: 0=success, 1=fail or confirmation needed, 2=error",
    )
    parser.add_argument("slug", nargs="?",
                        help="Band slug (kebab-case, no extension). Required except for --save, "
                             "which derives it from the profile's `name`.")
    ops = parser.add_argument_group("operations (pick one)")
    ops.add_argument("--save", action="store_true", help="Save a full profile (stdin or --in), verbatim.")
    ops.add_argument("--set", dest="do_set", action="store_true",
                     help="Merge field overrides into an existing profile.")
    ops.add_argument("--append", metavar="FIELD",
                     help="Append one entry to a list field (dot path allowed).")
    ops.add_argument("--duplicate", metavar="NEW_NAME",
                     help="Copy the profile to NEW_NAME's slug and set its name to NEW_NAME.")
    ops.add_argument("--load", action="store_true", help="Emit the profile as JSON.")
    ops.add_argument("--delete", action="store_true",
                     help="Archive (or --purge) the profile, decision log, draft and playlist YAML.")
    parser.add_argument("--set-json", metavar="JSON", help="Inline JSON overrides for --set.")
    parser.add_argument("--lists", choices=["append", "replace"],
                        help="How --set treats list values that meet an existing non-empty list.")
    parser.add_argument("--append-json", metavar="JSON", help="The entry for --append, as JSON.")
    parser.add_argument("--max", type=int, metavar="N",
                        help="Keep at most N entries after --append (default: schema cap, if any).")
    parser.add_argument("--bump-version", action="store_true", help="Increment version on --duplicate.")
    parser.add_argument("--stage", metavar="PATH",
                        help="Write the --set/--append/--duplicate result to PATH instead of saving.")
    parser.add_argument("--confirm", action="store_true", help="Carry out --delete.")
    parser.add_argument("--purge", action="store_true", help="With --delete: delete instead of archive.")
    parser.add_argument("--in", dest="input", metavar="PATH", help="Read input YAML from a file.")
    parser.add_argument("--project-root", default=".", help="Project root (default: cwd).")
    parser.add_argument("--profiles-dir",
                        help="Profiles folder (default: band_profiles_folder from config, "
                             "else {project-root}/docs/band-profiles).")
    parser.add_argument("--docs-dir", help="Folder holding {slug}-playlist.yaml "
                                           "(default: the profiles folder's parent).")
    parser.add_argument("--songbook-dir", help="Songbook folder (default: songbook_folder from config).")
    parser.add_argument("--force", action="store_true",
                        help="Allow --save/--duplicate to overwrite an existing profile.")
    parser.add_argument("-o", "--output", help="Write JSON result to a file instead of stdout.")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostics to stderr.")
    args = parser.parse_args()

    selected = [args.save, args.do_set, bool(args.append), bool(args.duplicate),
                args.load, args.delete]
    if sum(bool(s) for s in selected) != 1:
        parser.error("Exactly one of --save, --set, --append, --duplicate, --load, --delete is required.")
    if args.slug and args.slug.endswith((".yaml", ".yml")):
        args.slug = Path(args.slug).stem
    if not args.save and not args.slug:
        parser.error("This operation requires a <slug> positional argument.")
    if args.verbose:
        print(f"ruamel.yaml available: {HAVE_RUAMEL}", file=sys.stderr)

    try:
        if args.save:
            result = cmd_save(args)
        elif args.do_set:
            result = cmd_set(args)
        elif args.append:
            result = cmd_append(args)
        elif args.duplicate:
            result = cmd_duplicate(args)
        elif args.load:
            result = cmd_load(args)
        else:
            result = cmd_delete(args)
    except SchemaError as e:
        result = _fail(str(e))
    except (ValueError, yaml.YAMLError, json.JSONDecodeError, OSError) as e:
        result = {"script": SCRIPT_NAME, "status": "error", "error": str(e)}

    output = json.dumps(result, indent=2, default=str)
    if args.output:
        Path(args.output).write_text(output)
        if args.verbose:
            print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)

    status = result.get("status")
    sys.exit(0 if status == "complete" else 1 if status in ("fail", "confirm_required") else 2)


if __name__ == "__main__":
    main()
