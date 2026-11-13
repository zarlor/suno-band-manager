"""Read this module's answers through BMad's own resolver (BMad v7).

`bmad setup suno` writes the answers to `{project-root}/_bmad/config.toml` as
`[modules.suno]`; teams and users override them in the other layers. Merging
those layers is the resolver's job, so scripts ask
`{project-root}/_bmad/scripts/resolve_config.py` for `modules.suno` instead of
reading the TOML themselves. It runs with this interpreter (it is stdlib-only
and needs Python 3.11+, which every script here declares).

Config values hold `{project-root}`; it is filled in here. A project without
BMad's resolver gives no answers (scripts fall back to their flags and defaults):
that covers no `_bmad/` at all and a `_bmad/` holding only Mac's memory, which a
standalone install creates. A resolver that runs and fails raises ConfigError
with its reason, never a silent {}.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MODULE_CODE = "suno"
RESOLVER_REL = ("_bmad", "scripts", "resolve_config.py")


class ConfigError(RuntimeError):
    """BMad's config could not be resolved; the message says why."""


def resolve(project_root, *keys: str) -> dict:
    """{key: value} for the dotted keys resolve_config.py finds. Missing keys are absent."""
    root = Path(project_root)
    script = root.joinpath(*RESOLVER_REL)
    if not script.is_file():
        return {}
    cmd = [sys.executable, str(script), "--project-root", str(root)]
    for key in keys:
        cmd += ["--key", key]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ConfigError(f"could not run resolve_config.py: {exc}") from exc
    if proc.returncode != 0:
        reason = (proc.stderr or proc.stdout).strip().splitlines()
        raise ConfigError(reason[-1] if reason else f"resolve_config.py exited {proc.returncode}")
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise ConfigError(f"resolve_config.py printed no JSON: {exc}") from exc


def module_config(project_root) -> dict:
    """This module's answers as strings, `{project-root}` filled in. {} when unset."""
    root = Path(project_root)
    section = resolve(root, f"modules.{MODULE_CODE}").get(f"modules.{MODULE_CODE}") or {}
    return {
        key: str(value).replace("{project-root}", str(root))
        for key, value in section.items()
        if not isinstance(value, (dict, list))
    }


def module_path(project_root, key: str, default: str) -> Path:
    """A folder answer as a path; `default` may hold `{project-root}`. Relative values resolve from the root."""
    root = Path(project_root)
    value = module_config(root).get(key) or default.replace("{project-root}", str(root))
    path = Path(value)
    return path if path.is_absolute() else root / path
