#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0", "pyyaml>=6.0"]
# ///
"""Tests for apply-profile.py"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location(
    "apply_profile",
    Path(__file__).parent.parent / "apply-profile.py"
)
apply_mod = module_from_spec(spec)
spec.loader.exec_module(apply_mod)

_derive_slug = apply_mod._derive_slug
_set_nested = apply_mod._set_nested
_flatten = apply_mod._flatten
_write_yaml = apply_mod._write_yaml
_read_yaml = apply_mod._read_yaml
_resolve_profiles_dir = apply_mod._resolve_profiles_dir
cmd_set = apply_mod.cmd_set
cmd_duplicate = apply_mod.cmd_duplicate


SAMPLE = {
    "name": "Test Band",
    "genre": "indie rock",
    "tier": "free",
    "version": 1,
    "vocal": {"gender": "male", "tone": "warm"},
}


class Args:
    """Lightweight argparse.Namespace stand-in."""
    def __init__(self, **kw):
        self.slug = None
        self.profiles_dir = None
        self.project_root = "/nonexistent-project-root"  # never read the real config
        self.input = None
        self.set_json = None
        self.duplicate = None
        self.bump_version = False
        self.force = False
        self.lists = None
        self.stage = None
        self.append = None
        self.append_json = None
        self.max = None
        self.confirm = False
        self.purge = False
        self.docs_dir = None
        self.songbook_dir = None
        for k, v in kw.items():
            setattr(self, k, v)


# --- pure helpers ---

def test_derive_slug():
    assert _derive_slug("Test Band") == "test-band"
    assert _derive_slug("Rider's Hymn!") == "riders-hymn"
    assert _derive_slug("  Multiple   Spaces ") == "multiple-spaces"


def test_set_nested_changes():
    d = {"vocal": {"tone": "warm"}}
    assert _set_nested(d, "vocal.tone", "bright") is True
    assert d["vocal"]["tone"] == "bright"
    # no-op set returns False
    assert _set_nested(d, "vocal.tone", "bright") is False


def test_set_nested_creates_path():
    d = {}
    assert _set_nested(d, "sliders.weirdness", 65) is True
    assert d["sliders"]["weirdness"] == 65


def test_flatten():
    flat = _flatten({"a": 1, "b": {"c": 2, "d": {"e": 3}}})
    assert flat == {"a": 1, "b.c": 2, "b.d.e": 3}


# --- profiles-dir resolution ---

def test_resolve_profiles_dir_default():
    # No --profiles-dir: default to {project-root}/docs/band-profiles — unchanged.
    args = Args(project_root="/proj")
    assert _resolve_profiles_dir(args) == Path("/proj") / "docs" / "band-profiles"


def test_resolve_profiles_dir_override():
    # --profiles-dir wins when provided.
    args = Args(project_root="/proj", profiles_dir="/custom/store")
    assert _resolve_profiles_dir(args) == Path("/custom/store")


# --- cmd_set ---

def test_cmd_set_merges_fields(tmp_path):
    _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
    args = Args(slug="test-band", profiles_dir=str(tmp_path),
                set_json='{"tier": "pro", "vocal": {"tone": "bright"}}')
    result = cmd_set(args)
    assert result["status"] == "complete"
    assert set(result["fields_changed"]) == {"tier", "vocal.tone"}
    saved = _read_yaml(tmp_path / "test-band.yaml")
    assert saved["tier"] == "pro"
    assert saved["vocal"]["tone"] == "bright"
    # untouched fields survive
    assert saved["vocal"]["gender"] == "male"
    assert saved["genre"] == "indie rock"


def test_cmd_set_missing_profile(tmp_path):
    args = Args(slug="nope", profiles_dir=str(tmp_path), set_json='{"tier": "pro"}')
    result = cmd_set(args)
    assert result["status"] == "fail"
    assert "not found" in result["error"].lower()


def test_cmd_set_no_change(tmp_path):
    _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
    args = Args(slug="test-band", profiles_dir=str(tmp_path), set_json='{"tier": "free"}')
    result = cmd_set(args)
    assert result["status"] == "complete"
    assert result["fields_changed"] == []


# --- cmd_duplicate ---

def test_cmd_duplicate(tmp_path):
    _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
    args = Args(slug="test-band", profiles_dir=str(tmp_path), duplicate="Test Band V2")
    result = cmd_duplicate(args)
    assert result["status"] == "complete"
    assert result["slug"] == "test-band-v2"
    assert (tmp_path / "test-band-v2.yaml").exists()
    saved = _read_yaml(tmp_path / "test-band-v2.yaml")
    assert saved["name"] == "Test Band V2"  # the clone gets its own display name
    assert saved["version"] == 1  # not bumped by default
    assert _read_yaml(tmp_path / "test-band.yaml")["name"] == "Test Band"  # source untouched


def test_cmd_duplicate_bump_version(tmp_path):
    _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
    args = Args(slug="test-band", profiles_dir=str(tmp_path),
                duplicate="Test Band V2", bump_version=True)
    result = cmd_duplicate(args)
    saved = _read_yaml(tmp_path / "test-band-v2.yaml")
    assert saved["version"] == 2


def test_cmd_duplicate_existing_no_force(tmp_path):
    _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
    _write_yaml(tmp_path / "test-band-v2.yaml", dict(SAMPLE))
    args = Args(slug="test-band", profiles_dir=str(tmp_path), duplicate="Test Band V2")
    result = cmd_duplicate(args)
    assert result["status"] == "fail"
    assert "already exists" in result["error"].lower()


def test_cmd_duplicate_missing_source(tmp_path):
    args = Args(slug="nope", profiles_dir=str(tmp_path), duplicate="New Name")
    result = cmd_duplicate(args)
    assert result["status"] == "fail"
    assert "not found" in result["error"].lower()


# --- comment preservation, append semantics, load, delete (v3.0.0) ---

import json
import shutil
import subprocess

FIXTURE = Path(__file__).parent / "fixtures" / "commented-profile.yaml"
SLUG = "copper-lantern-choir"
cmd_append = apply_mod.cmd_append
cmd_save = apply_mod.cmd_save
cmd_load = apply_mod.cmd_load
cmd_delete = apply_mod.cmd_delete
_segments = apply_mod._segments


@pytest.fixture
def store(tmp_path):
    profiles = tmp_path / "docs" / "band-profiles"
    profiles.mkdir(parents=True)
    shutil.copy(FIXTURE, profiles / f"{SLUG}.yaml")
    return profiles


def _block(text, key):
    segs, _ = _segments(text)
    seg = next(s for s in segs if s["key"] == key)
    return "".join(seg["head"] + seg["body"])


def test_set_keeps_untouched_blocks_byte_identical(store):
    before = (store / f"{SLUG}.yaml").read_text()
    result = cmd_set(Args(slug=SLUG, profiles_dir=str(store), set_json='{"tier": "premier"}'))
    assert result["status"] == "complete" and result["fields_changed"] == ["tier"]
    after = (store / f"{SLUG}.yaml").read_text()
    assert after == before.replace("tier: pro\n", "tier: premier\n")


def test_set_preserves_header_and_section_comments_and_order(store):
    cmd_set(Args(slug=SLUG, profiles_dir=str(store),
                 set_json='{"model_preference": "v6-wild", "vocal": {"tone": "bright"}}'))
    after = (store / f"{SLUG}.yaml").read_text()
    for comment in ("# Band Profile — Copper Lantern Choir",
                    '# NOTE: "sludge" in the prompt triggers harsh vocals',
                    "# Generation History", "#   - date: \"2026-03-19\""):
        assert comment in after
    # nested NOTE comments survive (in place with ruamel, end of block without)
    assert "# NOTE: Personas pull the sound" in _block(after, "vocal")
    keys = [s["key"] for s in _segments(after)[0]]
    assert keys == [s["key"] for s in _segments(FIXTURE.read_text())[0]]
    # quoting of untouched values survives
    assert 'name: "Copper Lantern Choir"' in after
    assert "mood: 'brooding, then triumphant'" in after
    assert "style_baseline: >\n" in after


def test_set_refuses_silent_list_replace(store):
    before = (store / f"{SLUG}.yaml").read_text()
    result = cmd_set(Args(slug=SLUG, profiles_dir=str(store),
                          set_json='{"generation_learnings": ["one new learning"]}'))
    assert result["status"] == "fail"
    assert "--lists" in result["error"]
    assert (store / f"{SLUG}.yaml").read_text() == before  # nothing written


def test_set_lists_append_keeps_existing_entries(store):
    result = cmd_set(Args(slug=SLUG, profiles_dir=str(store), lists="append",
                          set_json='{"generation_learnings": ["one new learning"]}'))
    assert result["status"] == "complete"
    saved = _read_yaml(store / f"{SLUG}.yaml")["generation_learnings"]
    assert len(saved) == 3 and saved[-1] == "one new learning"


def test_set_lists_replace_is_explicit(store):
    cmd_set(Args(slug=SLUG, profiles_dir=str(store), lists="replace",
                 set_json='{"exclusion_defaults": ["no autotune"]}'))
    assert _read_yaml(store / f"{SLUG}.yaml")["exclusion_defaults"] == ["no autotune"]


def test_set_into_empty_list_needs_no_mode(store):
    result = cmd_set(Args(slug=SLUG, profiles_dir=str(store),
                          set_json='{"known_working_patterns": ["heavy groove works"]}'))
    assert result["status"] == "complete"
    assert _read_yaml(store / f"{SLUG}.yaml")["known_working_patterns"] == ["heavy groove works"]


def test_append_history_trims_to_schema_cap(store):
    for i in range(12):
        result = cmd_append(Args(slug=SLUG, profiles_dir=str(store), append="generation_history",
                                 append_json=json.dumps({"date": f"2026-10-{i + 1:02d}",
                                                         "note": f"round {i + 1}"})))
        assert result["status"] == "complete"
    hist = _read_yaml(store / f"{SLUG}.yaml")["generation_history"]
    assert len(hist) == 10
    assert hist[0]["note"] == "round 3" and hist[-1]["note"] == "round 12"
    assert result["trimmed"] == 1 and result["cap"] == 10
    text = (store / f"{SLUG}.yaml").read_text()
    assert text.count("# Each entry:") == 1  # trailing comments not duplicated


def test_append_max_override(store):
    for i in range(3):
        cmd_append(Args(slug=SLUG, profiles_dir=str(store), append="generation_learnings",
                        append_json=json.dumps(f"learning {i}"), max=2))
    assert _read_yaml(store / f"{SLUG}.yaml")["generation_learnings"] == ["learning 1", "learning 2"]


def test_append_schema_violation_fails_without_writing(store):
    before = (store / f"{SLUG}.yaml").read_text()
    bad_entry = cmd_append(Args(slug=SLUG, profiles_dir=str(store), append="generation_history",
                                append_json='"not a mapping"'))
    not_a_list = cmd_append(Args(slug=SLUG, profiles_dir=str(store), append="tier",
                                 append_json='"x"'))
    assert bad_entry["status"] == "fail" and "mappings" in bad_entry["error"]
    assert not_a_list["status"] == "fail" and "not a list" in not_a_list["error"]
    assert (store / f"{SLUG}.yaml").read_text() == before


def test_set_replace_over_cap_fails(store):
    entries = [{"date": f"2026-01-{i + 1:02d}"} for i in range(11)]
    result = cmd_set(Args(slug=SLUG, profiles_dir=str(store), lists="replace",
                          set_json=json.dumps({"generation_history": entries})))
    assert result["status"] == "fail" and "cap is 10" in result["error"]


def test_stage_writes_elsewhere(store, tmp_path):
    before = (store / f"{SLUG}.yaml").read_text()
    stage = tmp_path / "stage" / f"{SLUG}.yaml"
    result = cmd_set(Args(slug=SLUG, profiles_dir=str(store), stage=str(stage),
                          set_json='{"tier": "premier"}'))
    assert result["staged_path"] == str(stage)
    assert _read_yaml(stage)["tier"] == "premier"
    assert (store / f"{SLUG}.yaml").read_text() == before


def test_save_is_verbatim_and_refuses_overwrite(store):
    text = FIXTURE.read_text().replace("Copper Lantern Choir", "Tin Roof Parade")
    result = cmd_save(Args(profiles_dir=str(store), input=str(_write_tmp(store, text))))
    assert result["status"] == "complete" and result["slug"] == "tin-roof-parade"
    assert (store / "tin-roof-parade.yaml").read_text() == text
    again = cmd_save(Args(profiles_dir=str(store), input=str(_write_tmp(store, text))))
    assert again["status"] == "fail" and "already exists" in again["error"]


def test_save_flags_orphan_decision_log(store):
    (store / "tin-roof-parade.decision-log.md").write_text("# old band\n")
    text = FIXTURE.read_text().replace("Copper Lantern Choir", "Tin Roof Parade")
    result = cmd_save(Args(profiles_dir=str(store), input=str(_write_tmp(store, text))))
    assert result["existing_decision_log"].endswith("tin-roof-parade.decision-log.md")


def _write_tmp(store, text):
    p = store.parent / "incoming.yaml"
    p.write_text(text)
    return p


def test_duplicate_keeps_comments(store):
    cmd_duplicate(Args(slug=SLUG, profiles_dir=str(store), duplicate="Copper Lantern Choir II"))
    text = (store / "copper-lantern-choir-ii.yaml").read_text()
    assert "# Band Profile — Copper Lantern Choir" in text
    assert _read_yaml(store / "copper-lantern-choir-ii.yaml")["name"] == "Copper Lantern Choir II"


def test_load_returns_parsed_profile(store):
    result = cmd_load(Args(slug=SLUG, profiles_dir=str(store)))
    assert result["status"] == "complete"
    assert result["profile"]["vocal"]["tone"] == "warm, weathered baritone"


def _band_files(store):
    docs = store.parent
    (store / f"{SLUG}.decision-log.md").write_text("# log\n")
    (docs / f"{SLUG}-playlist.yaml").write_text("album: x\ntracks: []\n")
    (docs / "songbook" / SLUG).mkdir(parents=True)
    (docs / "songbook" / SLUG / "song.md").write_text("---\ntitle: S\n---\n")
    return docs


def test_delete_needs_confirmation(store):
    docs = _band_files(store)
    result = cmd_delete(Args(slug=SLUG, profiles_dir=str(store),
                             project_root=str(docs.parent)))
    assert result["status"] == "confirm_required"
    assert len(result["would_remove"]) == 3
    assert (store / f"{SLUG}.yaml").exists() and (docs / f"{SLUG}-playlist.yaml").exists()


def test_delete_archives_profile_log_and_playlist(store):
    docs = _band_files(store)
    result = cmd_delete(Args(slug=SLUG, profiles_dir=str(store), confirm=True,
                             project_root=str(docs.parent)))
    assert result["status"] == "complete" and result["action"] == "archive"
    archive = Path(result["archive_dir"])
    assert {p.name for p in archive.iterdir()} == {
        f"{SLUG}.yaml", f"{SLUG}.decision-log.md", f"{SLUG}-playlist.yaml"}
    assert not (store / f"{SLUG}.decision-log.md").exists()  # a new band won't inherit it
    assert (docs / "songbook" / SLUG / "song.md").exists()  # songbook left alone
    assert result["left_in_place"] and result["warnings"]


def test_delete_purge(store):
    docs = _band_files(store)
    result = cmd_delete(Args(slug=SLUG, profiles_dir=str(store), confirm=True, purge=True,
                             project_root=str(docs.parent)))
    assert result["action"] == "delete" and len(result["removed"]) == 3
    assert not (store / "archive").exists()


def test_profiles_dir_from_module_config(tmp_path):
    (tmp_path / "_bmad").mkdir()
    (tmp_path / "_bmad" / "config.yaml").write_text(
        "suno:\n  band_profiles_folder: '{project-root}/music/profiles'\n")
    args = Args(project_root=str(tmp_path))
    assert _resolve_profiles_dir(args) == tmp_path / "music" / "profiles"


# --- end to end through `uv run`, where ruamel.yaml is provisioned ---

needs_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="uv not on PATH")
SCRIPT = Path(__file__).parent.parent / "apply-profile.py"


def _run(*argv):
    proc = subprocess.run(["uv", "run", "--quiet", str(SCRIPT), *argv],
                          capture_output=True, text=True, timeout=180)
    return proc.returncode, json.loads(proc.stdout)


@needs_uv
def test_uv_set_keeps_nested_comments_in_place_and_quote_style(store):
    code, result = _run(SLUG, "--set", "--set-json",
                        '{"vocal": {"tone": "bright tenor"}, "model_preference": "v6-wild"}',
                        "--profiles-dir", str(store))
    assert code == 0, result
    assert "warnings" not in result
    after = (store / f"{SLUG}.yaml").read_text()
    before = FIXTURE.read_text()
    vocal_before = _block(before, "vocal").replace('"warm, weathered baritone"', '"bright tenor"')
    assert _block(after, "vocal") == vocal_before  # comments in place, quotes kept
    assert 'model_preference: "v6-wild"' in after
    assert "# moved to v6 2026-09-12" in after


@needs_uv
def test_uv_append_cli_contract(store):
    code, result = _run(SLUG, "--append", "generation_history", "--append-json",
                        '{"date": "2026-10-03", "note": "kept"}', "--max", "1",
                        "--profiles-dir", str(store))
    assert code == 0 and result["length"] == 1
    code, result = _run(SLUG, "--append", "generation_history", "--append-json", '"bad"',
                        "--profiles-dir", str(store))
    assert code == 1 and result["status"] == "fail"


def test_nested_edit_changes_only_that_key(store):
    import difflib
    before = (store / f"{SLUG}.yaml").read_text().splitlines()
    cmd_set(Args(slug=SLUG, profiles_dir=str(store),
                 set_json='{"vocal": {"energy": "slow burn"}, "sliders": {"weirdness": 50}}'))
    after = (store / f"{SLUG}.yaml").read_text().splitlines()
    changed = [ln for ln in difflib.unified_diff(before, after, lineterm="", n=0)
               if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
    assert sorted(changed) == sorted(["-  energy: restrained, building", "+  energy: slow burn",
                                      "-  weirdness: 45", "+  weirdness: 50"])


@needs_uv
def test_uv_folded_scalar_keeps_its_style(store):
    code, result = _run(SLUG, "--set", "--set-json", '{"style_baseline": "Swamp rock, brass stabs."}',
                        "--profiles-dir", str(store))
    assert code == 0, result
    assert "style_baseline: >\n  Swamp rock, brass stabs.\n" in (store / f"{SLUG}.yaml").read_text()
