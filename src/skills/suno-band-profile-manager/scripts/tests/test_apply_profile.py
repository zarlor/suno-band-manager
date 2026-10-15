#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for apply-profile.py"""

import sys
import tempfile
import unittest
from pathlib import Path

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


class TmpPathTestCase(unittest.TestCase):
    """Gives each test a fresh temporary directory as self.tmp_path."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name).resolve()


class TestHelpersAndCommands(TmpPathTestCase):
    # --- pure helpers ---

    def test_derive_slug(self):
        self.assertEqual(_derive_slug("Test Band"), "test-band")
        self.assertEqual(_derive_slug("Rider's Hymn!"), "riders-hymn")
        self.assertEqual(_derive_slug("  Multiple   Spaces "), "multiple-spaces")

    def test_set_nested_changes(self):
        d = {"vocal": {"tone": "warm"}}
        self.assertIs(_set_nested(d, "vocal.tone", "bright"), True)
        self.assertEqual(d["vocal"]["tone"], "bright")
        # no-op set returns False
        self.assertIs(_set_nested(d, "vocal.tone", "bright"), False)

    def test_set_nested_creates_path(self):
        d = {}
        self.assertIs(_set_nested(d, "sliders.weirdness", 65), True)
        self.assertEqual(d["sliders"]["weirdness"], 65)

    def test_flatten(self):
        flat = _flatten({"a": 1, "b": {"c": 2, "d": {"e": 3}}})
        self.assertEqual(flat, {"a": 1, "b.c": 2, "b.d.e": 3})

    # --- profiles-dir resolution ---
    def test_resolve_profiles_dir_default(self):
        # No --profiles-dir: default to {project-root}/docs/band-profiles — unchanged.
        args = Args(project_root="/proj")
        self.assertEqual(_resolve_profiles_dir(args), Path("/proj") / "docs" / "band-profiles")

    def test_resolve_profiles_dir_override(self):
        # --profiles-dir wins when provided.
        args = Args(project_root="/proj", profiles_dir="/custom/store")
        self.assertEqual(_resolve_profiles_dir(args), Path("/custom/store"))

    # --- cmd_set ---
    def test_cmd_set_merges_fields(self):
        tmp_path = self.tmp_path
        _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
        args = Args(slug="test-band", profiles_dir=str(tmp_path),
                    set_json='{"tier": "pro", "vocal": {"tone": "bright"}}')
        result = cmd_set(args)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(set(result["fields_changed"]), {"tier", "vocal.tone"})
        saved = _read_yaml(tmp_path / "test-band.yaml")
        self.assertEqual(saved["tier"], "pro")
        self.assertEqual(saved["vocal"]["tone"], "bright")
        # untouched fields survive
        self.assertEqual(saved["vocal"]["gender"], "male")
        self.assertEqual(saved["genre"], "indie rock")

    def test_cmd_set_missing_profile(self):
        tmp_path = self.tmp_path
        args = Args(slug="nope", profiles_dir=str(tmp_path), set_json='{"tier": "pro"}')
        result = cmd_set(args)
        self.assertEqual(result["status"], "fail")
        self.assertIn("not found", result["error"].lower())

    def test_cmd_set_no_change(self):
        tmp_path = self.tmp_path
        _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
        args = Args(slug="test-band", profiles_dir=str(tmp_path), set_json='{"tier": "free"}')
        result = cmd_set(args)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["fields_changed"], [])

    # --- cmd_duplicate ---
    def test_cmd_duplicate(self):
        tmp_path = self.tmp_path
        _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
        args = Args(slug="test-band", profiles_dir=str(tmp_path), duplicate="Test Band V2")
        result = cmd_duplicate(args)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["slug"], "test-band-v2")
        self.assertTrue((tmp_path / "test-band-v2.yaml").exists())
        saved = _read_yaml(tmp_path / "test-band-v2.yaml")
        self.assertEqual(saved["name"], "Test Band V2")  # the clone gets its own display name
        self.assertEqual(saved["version"], 1)  # not bumped by default
        self.assertEqual(_read_yaml(tmp_path / "test-band.yaml")["name"], "Test Band")  # source untouched

    def test_cmd_duplicate_bump_version(self):
        tmp_path = self.tmp_path
        _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
        args = Args(slug="test-band", profiles_dir=str(tmp_path),
                    duplicate="Test Band V2", bump_version=True)
        result = cmd_duplicate(args)
        saved = _read_yaml(tmp_path / "test-band-v2.yaml")
        self.assertEqual(saved["version"], 2)

    def test_cmd_duplicate_existing_no_force(self):
        tmp_path = self.tmp_path
        _write_yaml(tmp_path / "test-band.yaml", dict(SAMPLE))
        _write_yaml(tmp_path / "test-band-v2.yaml", dict(SAMPLE))
        args = Args(slug="test-band", profiles_dir=str(tmp_path), duplicate="Test Band V2")
        result = cmd_duplicate(args)
        self.assertEqual(result["status"], "fail")
        self.assertIn("already exists", result["error"].lower())

    def test_cmd_duplicate_missing_source(self):
        tmp_path = self.tmp_path
        args = Args(slug="nope", profiles_dir=str(tmp_path), duplicate="New Name")
        result = cmd_duplicate(args)
        self.assertEqual(result["status"], "fail")
        self.assertIn("not found", result["error"].lower())


# --- comment preservation, append semantics, load, delete (v3.0.0) ---

import json
import shutil
import subprocess
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_resolver import install_resolver  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "commented-profile.yaml"
SLUG = "copper-lantern-choir"
cmd_append = apply_mod.cmd_append
cmd_save = apply_mod.cmd_save
cmd_load = apply_mod.cmd_load
cmd_delete = apply_mod.cmd_delete
_segments = apply_mod._segments


def make_store(tmp_path):
    """A profiles folder holding the commented fixture profile."""
    profiles = tmp_path / "docs" / "band-profiles"
    profiles.mkdir(parents=True)
    shutil.copy(FIXTURE, profiles / f"{SLUG}.yaml")
    return profiles


def _block(text, key):
    segs, _ = _segments(text)
    seg = next(s for s in segs if s["key"] == key)
    return "".join(seg["head"] + seg["body"])


class TestCommentPreservingEdits(TmpPathTestCase):
    def test_set_keeps_untouched_blocks_byte_identical(self):
        store = make_store(self.tmp_path)
        before = (store / f"{SLUG}.yaml").read_text()
        result = cmd_set(Args(slug=SLUG, profiles_dir=str(store), set_json='{"tier": "premier"}'))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["fields_changed"], ["tier"])
        after = (store / f"{SLUG}.yaml").read_text()
        self.assertEqual(after, before.replace("tier: pro\n", "tier: premier\n"))

    def test_set_preserves_header_and_section_comments_and_order(self):
        store = make_store(self.tmp_path)
        cmd_set(Args(slug=SLUG, profiles_dir=str(store),
                     set_json='{"model_preference": "v6-wild", "vocal": {"tone": "bright"}}'))
        after = (store / f"{SLUG}.yaml").read_text()
        for comment in ("# Band Profile — Copper Lantern Choir",
                        '# NOTE: "sludge" in the prompt triggers harsh vocals',
                        "# Generation History", "#   - date: \"2026-03-19\""):
            self.assertIn(comment, after)
        # nested NOTE comments survive (in place with ruamel, end of block without)
        self.assertIn("# NOTE: Personas pull the sound", _block(after, "vocal"))
        keys = [s["key"] for s in _segments(after)[0]]
        self.assertEqual(keys, [s["key"] for s in _segments(FIXTURE.read_text())[0]])
        # quoting of untouched values survives
        self.assertIn('name: "Copper Lantern Choir"', after)
        self.assertIn("mood: 'brooding, then triumphant'", after)
        self.assertIn("style_baseline: >\n", after)

    def test_set_refuses_silent_list_replace(self):
        store = make_store(self.tmp_path)
        before = (store / f"{SLUG}.yaml").read_text()
        result = cmd_set(Args(slug=SLUG, profiles_dir=str(store),
                              set_json='{"generation_learnings": ["one new learning"]}'))
        self.assertEqual(result["status"], "fail")
        self.assertIn("--lists", result["error"])
        self.assertEqual((store / f"{SLUG}.yaml").read_text(), before)  # nothing written

    def test_set_lists_append_keeps_existing_entries(self):
        store = make_store(self.tmp_path)
        result = cmd_set(Args(slug=SLUG, profiles_dir=str(store), lists="append",
                              set_json='{"generation_learnings": ["one new learning"]}'))
        self.assertEqual(result["status"], "complete")
        saved = _read_yaml(store / f"{SLUG}.yaml")["generation_learnings"]
        self.assertEqual(len(saved), 3)
        self.assertEqual(saved[-1], "one new learning")

    def test_set_lists_replace_is_explicit(self):
        store = make_store(self.tmp_path)
        cmd_set(Args(slug=SLUG, profiles_dir=str(store), lists="replace",
                     set_json='{"exclusion_defaults": ["no autotune"]}'))
        self.assertEqual(_read_yaml(store / f"{SLUG}.yaml")["exclusion_defaults"], ["no autotune"])

    def test_set_into_empty_list_needs_no_mode(self):
        store = make_store(self.tmp_path)
        result = cmd_set(Args(slug=SLUG, profiles_dir=str(store),
                              set_json='{"known_working_patterns": ["heavy groove works"]}'))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(_read_yaml(store / f"{SLUG}.yaml")["known_working_patterns"], ["heavy groove works"])

    def test_append_history_trims_to_schema_cap(self):
        store = make_store(self.tmp_path)
        for i in range(12):
            result = cmd_append(Args(slug=SLUG, profiles_dir=str(store), append="generation_history",
                                     append_json=json.dumps({"date": f"2026-10-{i + 1:02d}",
                                                             "note": f"round {i + 1}"})))
            self.assertEqual(result["status"], "complete")
        hist = _read_yaml(store / f"{SLUG}.yaml")["generation_history"]
        self.assertEqual(len(hist), 10)
        self.assertEqual(hist[0]["note"], "round 3")
        self.assertEqual(hist[-1]["note"], "round 12")
        self.assertEqual(result["trimmed"], 1)
        self.assertEqual(result["cap"], 10)
        text = (store / f"{SLUG}.yaml").read_text()
        self.assertEqual(text.count("# Each entry:"), 1)  # trailing comments not duplicated

    def test_append_max_override(self):
        store = make_store(self.tmp_path)
        for i in range(3):
            cmd_append(Args(slug=SLUG, profiles_dir=str(store), append="generation_learnings",
                            append_json=json.dumps(f"learning {i}"), max=2))
        self.assertEqual(_read_yaml(store / f"{SLUG}.yaml")["generation_learnings"], ["learning 1", "learning 2"])

    def test_append_schema_violation_fails_without_writing(self):
        store = make_store(self.tmp_path)
        before = (store / f"{SLUG}.yaml").read_text()
        bad_entry = cmd_append(Args(slug=SLUG, profiles_dir=str(store), append="generation_history",
                                    append_json='"not a mapping"'))
        not_a_list = cmd_append(Args(slug=SLUG, profiles_dir=str(store), append="tier",
                                     append_json='"x"'))
        self.assertEqual(bad_entry["status"], "fail")
        self.assertIn("mappings", bad_entry["error"])
        self.assertEqual(not_a_list["status"], "fail")
        self.assertIn("not a list", not_a_list["error"])
        self.assertEqual((store / f"{SLUG}.yaml").read_text(), before)

    def test_set_replace_over_cap_fails(self):
        store = make_store(self.tmp_path)
        entries = [{"date": f"2026-01-{i + 1:02d}"} for i in range(11)]
        result = cmd_set(Args(slug=SLUG, profiles_dir=str(store), lists="replace",
                              set_json=json.dumps({"generation_history": entries})))
        self.assertEqual(result["status"], "fail")
        self.assertIn("cap is 10", result["error"])

    def test_stage_writes_elsewhere(self):
        tmp_path = self.tmp_path
        store = make_store(self.tmp_path)
        before = (store / f"{SLUG}.yaml").read_text()
        stage = tmp_path / "stage" / f"{SLUG}.yaml"
        result = cmd_set(Args(slug=SLUG, profiles_dir=str(store), stage=str(stage),
                              set_json='{"tier": "premier"}'))
        self.assertEqual(result["staged_path"], str(stage))
        self.assertEqual(_read_yaml(stage)["tier"], "premier")
        self.assertEqual((store / f"{SLUG}.yaml").read_text(), before)

    def test_save_is_verbatim_and_refuses_overwrite(self):
        store = make_store(self.tmp_path)
        text = FIXTURE.read_text().replace("Copper Lantern Choir", "Tin Roof Parade")
        result = cmd_save(Args(profiles_dir=str(store), input=str(_write_tmp(store, text))))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["slug"], "tin-roof-parade")
        self.assertEqual((store / "tin-roof-parade.yaml").read_text(), text)
        again = cmd_save(Args(profiles_dir=str(store), input=str(_write_tmp(store, text))))
        self.assertEqual(again["status"], "fail")
        self.assertIn("already exists", again["error"])

    def test_save_flags_orphan_decision_log(self):
        store = make_store(self.tmp_path)
        (store / "tin-roof-parade.decision-log.md").write_text("# old band\n")
        text = FIXTURE.read_text().replace("Copper Lantern Choir", "Tin Roof Parade")
        result = cmd_save(Args(profiles_dir=str(store), input=str(_write_tmp(store, text))))
        self.assertTrue(result["existing_decision_log"].endswith("tin-roof-parade.decision-log.md"))


def _write_tmp(store, text):
    p = store.parent / "incoming.yaml"
    p.write_text(text)
    return p


class TestDuplicateAndLoad(TmpPathTestCase):
    def test_duplicate_keeps_comments(self):
        store = make_store(self.tmp_path)
        cmd_duplicate(Args(slug=SLUG, profiles_dir=str(store), duplicate="Copper Lantern Choir II"))
        text = (store / "copper-lantern-choir-ii.yaml").read_text()
        self.assertIn("# Band Profile — Copper Lantern Choir", text)
        self.assertEqual(_read_yaml(store / "copper-lantern-choir-ii.yaml")["name"], "Copper Lantern Choir II")

    def test_load_returns_parsed_profile(self):
        store = make_store(self.tmp_path)
        result = cmd_load(Args(slug=SLUG, profiles_dir=str(store)))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["profile"]["vocal"]["tone"], "warm, weathered baritone")


def _band_files(store):
    docs = store.parent
    (store / f"{SLUG}.decision-log.md").write_text("# log\n")
    (docs / f"{SLUG}-playlist.yaml").write_text("album: x\ntracks: []\n")
    (docs / "songbook" / SLUG).mkdir(parents=True)
    (docs / "songbook" / SLUG / "song.md").write_text("---\ntitle: S\n---\n")
    return docs


class TestDeleteAndConfiguredStore(TmpPathTestCase):
    def test_delete_needs_confirmation(self):
        store = make_store(self.tmp_path)
        docs = _band_files(store)
        result = cmd_delete(Args(slug=SLUG, profiles_dir=str(store),
                                 project_root=str(docs.parent)))
        self.assertEqual(result["status"], "confirm_required")
        self.assertEqual(len(result["would_remove"]), 3)
        self.assertTrue((store / f"{SLUG}.yaml").exists())
        self.assertTrue((docs / f"{SLUG}-playlist.yaml").exists())

    def test_delete_archives_profile_log_and_playlist(self):
        store = make_store(self.tmp_path)
        docs = _band_files(store)
        result = cmd_delete(Args(slug=SLUG, profiles_dir=str(store), confirm=True,
                                 project_root=str(docs.parent)))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["action"], "archive")
        archive = Path(result["archive_dir"])
        self.assertEqual({p.name for p in archive.iterdir()}, {
            f"{SLUG}.yaml", f"{SLUG}.decision-log.md", f"{SLUG}-playlist.yaml"})
        self.assertFalse((store / f"{SLUG}.decision-log.md").exists())  # a new band won't inherit it
        self.assertTrue((docs / "songbook" / SLUG / "song.md").exists())  # songbook left alone
        self.assertTrue(result["left_in_place"])
        self.assertTrue(result["warnings"])

    def test_delete_purge(self):
        store = make_store(self.tmp_path)
        docs = _band_files(store)
        result = cmd_delete(Args(slug=SLUG, profiles_dir=str(store), confirm=True, purge=True,
                                 project_root=str(docs.parent)))
        self.assertEqual(result["action"], "delete")
        self.assertEqual(len(result["removed"]), 3)
        self.assertFalse((store / "archive").exists())

    def test_profiles_dir_from_module_config(self):
        tmp_path = self.tmp_path
        (tmp_path / "_bmad").mkdir()
        (tmp_path / "_bmad" / "config.toml").write_text(
            "[modules.suno]\nband_profiles_folder = 'music/profiles'\n")
        install_resolver(tmp_path)
        args = Args(project_root=str(tmp_path))
        self.assertEqual(_resolve_profiles_dir(args), tmp_path / "music" / "profiles")


# --- end to end through `uv run`, where ruamel.yaml is provisioned ---

needs_uv = unittest.skipIf(shutil.which("uv") is None, "uv not on PATH")
SCRIPT = Path(__file__).parent.parent / "apply-profile.py"


def _run(*argv):
    proc = subprocess.run(["uv", "run", "--quiet", str(SCRIPT), *argv],
                          capture_output=True, text=True, timeout=180)
    return proc.returncode, json.loads(proc.stdout)


class TestEndToEnd(TmpPathTestCase):
    @needs_uv
    def test_uv_set_keeps_nested_comments_in_place_and_quote_style(self):
        store = make_store(self.tmp_path)
        code, result = _run(SLUG, "--set", "--set-json",
                            '{"vocal": {"tone": "bright tenor"}, "model_preference": "v6-wild"}',
                            "--profiles-dir", str(store))
        self.assertEqual(code, 0, result)
        self.assertNotIn("warnings", result)
        after = (store / f"{SLUG}.yaml").read_text()
        before = FIXTURE.read_text()
        vocal_before = _block(before, "vocal").replace('"warm, weathered baritone"', '"bright tenor"')
        self.assertEqual(_block(after, "vocal"), vocal_before)  # comments in place, quotes kept
        self.assertIn('model_preference: "v6-wild"', after)
        self.assertIn("# moved to v6 2026-09-12", after)

    @needs_uv
    def test_uv_append_cli_contract(self):
        store = make_store(self.tmp_path)
        code, result = _run(SLUG, "--append", "generation_history", "--append-json",
                            '{"date": "2026-10-03", "note": "kept"}', "--max", "1",
                            "--profiles-dir", str(store))
        self.assertEqual(code, 0)
        self.assertEqual(result["length"], 1)
        code, result = _run(SLUG, "--append", "generation_history", "--append-json", '"bad"',
                            "--profiles-dir", str(store))
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "fail")

    def test_nested_edit_changes_only_that_key(self):
        store = make_store(self.tmp_path)
        import difflib
        before = (store / f"{SLUG}.yaml").read_text().splitlines()
        cmd_set(Args(slug=SLUG, profiles_dir=str(store),
                     set_json='{"vocal": {"energy": "slow burn"}, "sliders": {"weirdness": 50}}'))
        after = (store / f"{SLUG}.yaml").read_text().splitlines()
        changed = [ln for ln in difflib.unified_diff(before, after, lineterm="", n=0)
                   if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
        self.assertEqual(sorted(changed), sorted(["-  energy: restrained, building", "+  energy: slow burn",
                                                  "-  weirdness: 45", "+  weirdness: 50"]))

    @needs_uv
    def test_uv_folded_scalar_keeps_its_style(self):
        store = make_store(self.tmp_path)
        code, result = _run(SLUG, "--set", "--set-json", '{"style_baseline": "Swamp rock, brass stabs."}',
                            "--profiles-dir", str(store))
        self.assertEqual(code, 0, result)
        self.assertIn("style_baseline: >\n  Swamp rock, brass stabs.\n", (store / f"{SLUG}.yaml").read_text())


if __name__ == "__main__":
    unittest.main()
