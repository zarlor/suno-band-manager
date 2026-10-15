"""Read this module's answers from BMad's central config (BMad v7).

`bmad setup suno` writes the answers to `{project-root}/_bmad/config.toml` as
`[modules.suno]`; teams and users override them in `config.user.toml` and the
two `custom/` layers. Skills read them through `_bmad/scripts/resolve_config.py`;
scripts read the same four layers here, with tables deep-merged and later layers
winning, so they need no subprocess and no third-party parser.

Folder answers are relative to the project root (`docs/songbook`); a value that
still carries a `{project-root}` token is filled in, and an absolute path is kept.
"""

from __future__ import annotations

from pathlib import Path

MODULE_CODE = "suno"
LAYERS = ("config.toml", "config.user.toml", "custom/config.toml", "custom/config.user.toml")


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_layers(project_root) -> dict:
    """The four BMad config layers of a project, merged. {} when none can be read."""
    try:
        import tomllib
    except ModuleNotFoundError:  # Python < 3.11
        return {}
    bmad = Path(project_root) / "_bmad"
    merged: dict = {}
    for rel in LAYERS:
        path = bmad / rel
        if not path.is_file():
            continue
        try:
            merged = _merge(merged, tomllib.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return merged


def module_config(project_root) -> dict:
    """This module's answers as strings, `{project-root}` filled in. {} when unset."""
    root = Path(project_root)
    section = (load_layers(root).get("modules") or {}).get(MODULE_CODE) or {}
    return {
        key: str(value).replace("{project-root}", str(root))
        for key, value in section.items()
        if not isinstance(value, (dict, list))
    }


def module_path(project_root, key: str, default: str) -> Path:
    """A folder answer resolved against the project root (absolute values kept)."""
    root = Path(project_root)
    value = module_config(root).get(key) or default
    path = Path(value)
    return path if path.is_absolute() else root / path
