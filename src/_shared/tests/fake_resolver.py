"""A test stand-in for BMad's resolve_config.py, so config tests run without a BMad install."""

from pathlib import Path


# Test stand-in for BMad's _bmad/scripts/resolve_config.py: merges the four
# layers and prints the requested keys, failing like the real one on bad TOML.
FAKE_RESOLVER = r'''
import argparse, json, sys, tomllib
from pathlib import Path
p = argparse.ArgumentParser(); p.add_argument("--project-root"); p.add_argument("--key", action="append", default=[])
a = p.parse_args(); bmad = Path(a.project_root) / "_bmad"
def merge(b, o):
    out = dict(b)
    for k, v in o.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out
data = {}
for rel in ("config.toml", "config.user.toml", "custom/config.toml", "custom/config.user.toml"):
    f = bmad / rel
    if f.is_file():
        try:
            data = merge(data, tomllib.loads(f.read_text()))
        except tomllib.TOMLDecodeError as e:
            sys.stderr.write(f"error: failed to parse {f}: {e}\n"); sys.exit(1)
out = {}
for key in a.key:
    cur = data
    for part in key.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
    if cur is not None:
        out[key] = cur
print(json.dumps(out))
'''


def install_resolver(root):
    """Give a temp project BMad's resolver (a test stand-in)."""
    scripts = Path(root) / "_bmad" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / "resolve_config.py").write_text(FAKE_RESOLVER)
