#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Tests for validate-sequence.py: the pre-write gate on the playlist YAML."""

import importlib.util
import json
from pathlib import Path

import yaml

SCRIPT = str(Path(__file__).parent.parent / "validate-sequence.py")

PLAYLIST = """album: "Band A"
audio_dir: "docs/audio/band-a"
# Order in this list = playlist order.
tracks:
  - name: "One"
    file: "One.mp3"
  - name: "Two"
    file: "Two.mp3"
    felt_bpm: 72
  - name: "Three"
    file: "Three.mp3"
  - name: "Four"
    file: "Four.mp3"

locked_arcs:
  - "Two > Three"
"""


def load():
    spec = importlib.util.spec_from_file_location("validate_sequence", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def setup(tmp_path, order=None):
    p = tmp_path / "band-a-playlist.yaml"
    p.write_text(PLAYLIST)
    o = None
    if order is not None:
        o = tmp_path / "order.txt"
        o.write_text(order)
    return p, o


def run(m, tmp_path, capsys, *args):
    code = m.main([*map(str, args)])
    return code, json.loads(capsys.readouterr().out)


def test_read_order_strips_numbering_and_comments():
    m = load()
    assert m.read_order("# proposal\n1. One\n2) Two\n\n- Three\nFour\n") == ["One", "Two", "Three", "Four"]


def test_current_order_surfaces_locked_arcs(tmp_path, capsys):
    m = load()
    p, _ = setup(tmp_path)
    code, out = run(m, tmp_path, capsys, p, "--locked", "One > Two")
    assert code == 0 and out["status"] == "ok" and out["moves"] == []
    assert out["locked_arcs"] == [{"tracks": ["Two", "Three"], "status": "intact"},
                                  {"tracks": ["One", "Two"], "status": "intact"}]


def test_permutation_errors_name_the_track(tmp_path, capsys):
    m = load()
    p, o = setup(tmp_path, "Four\nTwo\nThree\nTwo\nFive\n")
    code, out = run(m, tmp_path, capsys, p, "--order", o, "--write")
    assert code == 1 and out["written"] is False
    errs = " | ".join(out["errors"])
    assert "duplicated: Two (positions 2, 4)" in errs
    assert "dropped: One" in errs and "unknown: Five" in errs
    assert p.read_text() == PLAYLIST  # nothing written


def test_split_and_reordered_arcs_fail(tmp_path, capsys):
    m = load()
    p, o = setup(tmp_path, "Two\nOne\nThree\nFour\n")
    code, out = run(m, tmp_path, capsys, p, "--order", o)
    assert code == 1 and "locked arc split: Two > Three" in out["errors"]
    p, o = setup(tmp_path, "Three\nTwo\nOne\nFour\n")
    code, out = run(m, tmp_path, capsys, p, "--order", o)
    assert "locked arc out-of-order: Two > Three" in out["errors"]
    code, out = run(m, tmp_path, capsys, p, "--locked", "One > Ghost")
    assert any("not in the playlist: Ghost" in e for e in out["errors"])


def test_preview_then_write_keeps_everything_but_order(tmp_path, capsys):
    m = load()
    p, o = setup(tmp_path, "Four\nTwo\nThree\nOne\n")
    code, out = run(m, tmp_path, capsys, p, "--order", o)
    assert code == 0 and out["written"] is False and p.read_text() == PLAYLIST  # preview only
    assert out["moves"] == [{"name": "Four", "from": 4, "to": 1}, {"name": "One", "from": 1, "to": 4}]
    assert out["unchanged"] == 2
    code, out = run(m, tmp_path, capsys, p, "--order", o, "--write")
    assert code == 0 and out["written"] is True
    text = p.read_text()
    assert text.startswith('album: "Band A"\naudio_dir: "docs/audio/band-a"\n# Order in this list = playlist order.\n')
    data = yaml.safe_load(text)
    assert [t["name"] for t in data["tracks"]] == ["Four", "Two", "Three", "One"]
    assert data["tracks"][1] == {"name": "Two", "file": "Two.mp3", "felt_bpm": 72}
    assert data["locked_arcs"] == ["Two > Three"]


def test_write_needs_order(tmp_path, capsys):
    m = load()
    p, _ = setup(tmp_path)
    code, out = run(m, tmp_path, capsys, p, "--write")
    assert code == 2 and out["status"] == "error"
