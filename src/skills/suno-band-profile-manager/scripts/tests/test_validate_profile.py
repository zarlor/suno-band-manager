#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for validate-profile.py"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

# Add parent directory to path for import
sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_resolver import install_resolver  # noqa: E402

# Import the module
spec = spec_from_file_location(
    "validate_profile",
    Path(__file__).parent.parent / "validate-profile.py"
)
validate_profile_mod = module_from_spec(spec)
spec.loader.exec_module(validate_profile_mod)
validate_profile = validate_profile_mod.validate_profile
derive_filename = validate_profile_mod.derive_filename


def write_profile(tmp_path, data, filename="test-band.yaml"):
    """Helper to write a YAML profile and return its path."""
    profile_path = tmp_path / filename
    with open(profile_path, "w") as f:
        yaml.dump(data, f)
    return profile_path


VALID_PROFILE = {
    "name": "Test Band",
    "genre": "indie rock",
    "mood": "melancholic",
    "model_preference": "v6-mini",
    "tier": "free",
    "style_baseline": "Indie rock with warm guitars and atmospheric pads",
    "vocal": {
        "gender": "male",
        "tone": "warm, breathy",
        "delivery": "intimate",
        "energy": "restrained",
    },
}

VALID_INSTRUMENTAL_PROFILE = {
    "name": "Ambient Waves",
    "genre": "ambient electronic",
    "mood": "contemplative, spacious",
    "model_preference": "v6-mini",
    "tier": "free",
    "style_baseline": "Ambient electronic with lush pads and field recordings",
    "instrumental": True,
}


class TmpPathTestCase(unittest.TestCase):
    """Gives each test a fresh temporary directory as self.tmp_path."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name).resolve()


class TestValidateProfile(TmpPathTestCase):
    def test_valid_profile(self):
        tmp_path = self.tmp_path
        path = write_profile(tmp_path, VALID_PROFILE)
        result = validate_profile(path)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["summary"]["total"], 0)

    def test_missing_file(self):
        tmp_path = self.tmp_path
        path = tmp_path / "nonexistent.yaml"
        result = validate_profile(path)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["summary"]["critical"], 1)

    def test_invalid_yaml(self):
        tmp_path = self.tmp_path
        path = tmp_path / "bad.yaml"
        path.write_text(": invalid: yaml: {{{{")
        result = validate_profile(path)
        self.assertEqual(result["status"], "fail")
        self.assertGreaterEqual(result["summary"]["critical"], 1)

    def test_missing_required_fields(self):
        tmp_path = self.tmp_path
        path = write_profile(tmp_path, {"name": "Test"})
        result = validate_profile(path)
        self.assertEqual(result["status"], "fail")
        self.assertGreaterEqual(result["summary"]["critical"], 1)

    def test_invalid_model(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "model_preference": "v99 Ultra"}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any(f.get("location", {}).get("field") == "model_preference"
                            for f in result["findings"]))

    def test_invalid_tier(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "tier": "ultimate"}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("tier" in str(f) for f in result["findings"]))

    def test_style_baseline_too_long(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "style_baseline": "x" * 1001}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("style_baseline" in str(f) for f in result["findings"]))

    def test_style_baseline_v4_pro_200_limit(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "model_preference": "v4 Pro", "tier": "pro",
                "style_baseline": "x" * 201}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("style_baseline" in str(f) and "200" in str(f)
                            for f in result["findings"]))

    def test_free_tier_wrong_model(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "tier": "free", "model_preference": "v5 Pro"}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("free" in f.get("issue", "").lower() or "free" in f.get("fix", "").lower()
                            for f in result["findings"]))

    def test_free_tier_slider_warning(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "sliders": {"weirdness": 80, "style_influence": 30}}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("slider" in f.get("issue", "").lower() for f in result["findings"]))

    def test_slider_out_of_range(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "tier": "pro", "model_preference": "v5 Pro",
                "sliders": {"weirdness": 150}}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("out of range" in f.get("issue", "").lower() for f in result["findings"]))

    def test_audio_influence_slider_validation(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "tier": "pro", "model_preference": "v5 Pro",
                "sliders": {"audio_influence": 200}}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("audio_influence" in str(f) and "out of range" in f.get("issue", "").lower()
                            for f in result["findings"]))

    def test_invalid_vocal_gender(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE}
        data["vocal"] = {**VALID_PROFILE["vocal"], "gender": "robot"}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("gender" in str(f) for f in result["findings"]))

    def test_missing_vocal_fields(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "vocal": {"gender": "male"}}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertGreaterEqual(result["summary"]["high"], 1)

    def test_too_many_exclusions(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "exclusion_defaults": [f"no thing {i}" for i in range(7)]}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("exclusion" in f.get("issue", "").lower() for f in result["findings"]))

    def test_pro_tier_valid_with_sliders(self):
        tmp_path = self.tmp_path
        data = {
            **VALID_PROFILE,
            "tier": "pro",
            "model_preference": "v6",
            "sliders": {"weirdness": 70, "style_influence": 40},
        }
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertEqual(result["status"], "pass")

    # --- Instrumental profile tests ---
    def test_instrumental_profile_valid_without_vocal(self):
        tmp_path = self.tmp_path
        path = write_profile(tmp_path, VALID_INSTRUMENTAL_PROFILE, "ambient-waves.yaml")
        result = validate_profile(path)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["summary"]["total"], 0)

    def test_instrumental_profile_with_optional_vocal(self):
        tmp_path = self.tmp_path
        data = {**VALID_INSTRUMENTAL_PROFILE, "vocal": {"gender": "any"}}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertEqual(result["status"], "pass")

    def test_non_instrumental_requires_vocal(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE}
        del data["vocal"]
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertEqual(result["status"], "fail")
        self.assertGreaterEqual(result["summary"]["high"], 1)

    # --- New field tests ---
    def test_valid_creativity_default(self):
        tmp_path = self.tmp_path
        for mode in ["conservative", "balanced", "experimental"]:
            data = {**VALID_PROFILE, "creativity_default": mode}
            path = write_profile(tmp_path, data)
            result = validate_profile(path)
            self.assertFalse(any(f.get("location", {}).get("field") == "creativity_default"
                                 for f in result["findings"]), f"Failed for {mode}")

    def test_invalid_creativity_default(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "creativity_default": "wild"}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("creativity_default" in str(f) for f in result["findings"]))

    def test_valid_language(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "language": "Spanish"}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertFalse(any(f.get("location", {}).get("field") == "language"
                             for f in result["findings"]))

    def test_empty_language(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "language": ""}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("language" in str(f) for f in result["findings"]))

    def test_generation_history_valid(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "generation_history": [
            {"date": "2026-03-19", "style_prompt": "test", "model": "v4.5-all"}
        ]}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertFalse(any(f.get("location", {}).get("field") == "generation_history"
                             for f in result["findings"]))

    def test_generation_history_too_many(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "generation_history": [
            {"date": f"2026-03-{i:02d}"} for i in range(1, 15)
        ]}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("generation_history" in str(f) for f in result["findings"]))

    def test_generation_history_not_list(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "generation_history": "not a list"}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("generation_history" in str(f) for f in result["findings"]))

    def test_studio_preferences_non_premier_warning(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "tier": "pro", "model_preference": "v5 Pro",
                "studio_preferences": {"bpm": 120, "key": "C minor"}}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("studio" in f.get("issue", "").lower() for f in result["findings"]))

    def test_studio_preferences_premier_valid(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "tier": "premier", "model_preference": "v5 Pro",
                "studio_preferences": {"bpm": 120, "key": "C minor", "time_signature": "4/4"}}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertFalse(any("studio" in f.get("issue", "").lower() for f in result["findings"]))

    def test_studio_preferences_invalid_bpm(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "tier": "premier", "model_preference": "v5 Pro",
                "studio_preferences": {"bpm": "fast"}}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("bpm" in str(f).lower() for f in result["findings"]))


# --- multi-Voice (voices) tests ---

PRO_PROFILE = {
    **VALID_PROFILE,
    "tier": "pro",
    "model_preference": "v6",
}


class TestVoicesAndFilenames(TmpPathTestCase):
    def test_voices_valid_list(self):
        tmp_path = self.tmp_path
        data = {**PRO_PROFILE, "voices": [
            {"voice_id": "v-rock", "label": "Narrative Rock", "use_case": "mid-tempo rock"},
            {"voice_id": "v-ballad", "label": "Ballad Intimate", "use_case": "tender tracks"},
        ]}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertFalse(any("voices" in str(f.get("location", {}).get("field", "")) for f in result["findings"]))

    def test_voices_not_a_list(self):
        tmp_path = self.tmp_path
        data = {**PRO_PROFILE, "voices": "v-rock"}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any(f.get("location", {}).get("field") == "voices" for f in result["findings"]))

    def test_voices_entry_missing_voice_id(self):
        tmp_path = self.tmp_path
        data = {**PRO_PROFILE, "voices": [{"label": "No id", "use_case": "tracks"}]}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("voice_id" in str(f.get("location", {}).get("field", ""))
                            and f.get("severity") == "medium" for f in result["findings"]))

    def test_voices_entry_missing_use_case(self):
        tmp_path = self.tmp_path
        data = {**PRO_PROFILE, "voices": [{"voice_id": "v-rock", "label": "Rock"}]}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any("use_case" in str(f.get("location", {}).get("field", "")) for f in result["findings"]))

    def test_voices_primary_not_in_list(self):
        tmp_path = self.tmp_path
        data = {**PRO_PROFILE, "voices": [
            {"voice_id": "v-rock", "label": "Rock", "use_case": "rock"},
        ]}
        data["vocal"] = {**PRO_PROFILE["vocal"], "voice_id": "v-missing"}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertTrue(any(f.get("location", {}).get("field") == "vocal.voice_id"
                            and "absent from the voices list" in f.get("issue", "")
                            for f in result["findings"]))

    def test_voices_primary_in_list_no_warning(self):
        tmp_path = self.tmp_path
        data = {**PRO_PROFILE, "voices": [
            {"voice_id": "v-rock", "label": "Rock", "use_case": "rock"},
        ]}
        data["vocal"] = {**PRO_PROFILE["vocal"], "voice_id": "v-rock"}
        path = write_profile(tmp_path, data)
        result = validate_profile(path)
        self.assertFalse(any("absent from the voices list" in f.get("issue", "") for f in result["findings"]))

    # --- derive_filename tests ---
    def test_derive_filename_basic(self):
        self.assertEqual(derive_filename("Test Band"), "test-band.yaml")

    def test_derive_filename_special_chars(self):
        self.assertEqual(derive_filename("The Band's Name!"), "the-bands-name.yaml")

    def test_derive_filename_multiple_spaces(self):
        self.assertEqual(derive_filename("  My   Cool  Band  "), "my-cool-band.yaml")

    def test_derive_filename_already_kebab(self):
        self.assertEqual(derive_filename("already-kebab"), "already-kebab.yaml")


# --- docs-dir / playlist-location tests ---

def _make_standard_layout(root: Path, slug: str = "test-band", published: bool = True):
    """Build {root}/docs/band-profiles/{slug}.yaml plus a songbook entry.

    Returns the profile path. With published=True the songbook entry has
    `status: published`, which is what trips the "missing playlist YAML"
    high-severity finding (a band with songbook entries needs a canonical
    playlist YAML).
    """
    profiles_dir = root / "docs" / "band-profiles"
    profiles_dir.mkdir(parents=True)
    profile_path = profiles_dir / f"{slug}.yaml"
    with open(profile_path, "w") as f:
        yaml.dump(VALID_PROFILE, f)
    songbook_dir = root / "docs" / "songbook" / slug
    songbook_dir.mkdir(parents=True)
    status = "published" if published else "draft"
    (songbook_dir / "song.md").write_text(
        f'---\ntitle: "A Song"\nstatus: {status}\n---\nbody\n'
    )
    return profile_path


def _has_missing_playlist_finding(result) -> bool:
    return any(
        "playlist YAML" in f.get("issue", "")
        and f.get("severity") == "high"
        for f in result["findings"]
    )


class TestDocsDirAndModels(TmpPathTestCase):
    def test_default_docs_dir_flags_missing_playlist(self):
        tmp_path = self.tmp_path
        # Standard layout, no playlist YAML, songbook has a published entry.
        # Default derivation (grandparent of profile = {root}/docs) must find the
        # songbook and flag the missing playlist — identical to prior behavior.
        profile_path = _make_standard_layout(tmp_path)
        result = validate_profile(profile_path)
        self.assertTrue(_has_missing_playlist_finding(result))

    def test_default_docs_dir_satisfied_when_playlist_present(self):
        tmp_path = self.tmp_path
        profile_path = _make_standard_layout(tmp_path)
        # Create the canonical playlist YAML at the default location.
        (tmp_path / "docs" / "test-band-playlist.yaml").write_text('album: "X"\ntracks: []\n')
        result = validate_profile(profile_path)
        self.assertFalse(_has_missing_playlist_finding(result))

    def test_docs_dir_override_redirects_lookup(self):
        tmp_path = self.tmp_path
        # Profile lives under the standard band-profiles dir, but the songbook +
        # playlist live under a RELOCATED docs root. Pointing --docs-dir there
        # must make the playlist check honor the new location.
        profile_path = _make_standard_layout(tmp_path)
        # The default grandparent ({tmp_path}/docs) has the songbook but no
        # playlist -> would flag. Now relocate docs.
        alt_docs = tmp_path / "alt-docs"
        songbook_dir = alt_docs / "songbook" / "test-band"
        songbook_dir.mkdir(parents=True)
        (songbook_dir / "song.md").write_text('---\ntitle: "A Song"\nstatus: published\n---\nbody\n')
        # No playlist YAML under alt-docs -> should flag against alt-docs.
        result_flag = validate_profile(profile_path, docs_dir=alt_docs)
        self.assertTrue(_has_missing_playlist_finding(result_flag))
        finding = next(f for f in result_flag["findings"] if "playlist YAML" in f.get("issue", ""))
        self.assertIn(str(alt_docs), finding["issue"])

        # Add the playlist YAML under alt-docs -> the finding clears, even though
        # the default-derived {tmp_path}/docs has no playlist YAML.
        (alt_docs / "test-band-playlist.yaml").write_text('album: "X"\ntracks: []\n')
        result_ok = validate_profile(profile_path, docs_dir=alt_docs)
        self.assertFalse(_has_missing_playlist_finding(result_ok))

    def test_docs_dir_default_matches_grandparent(self):
        tmp_path = self.tmp_path
        # Passing docs_dir explicitly as the grandparent must be identical to the
        # default (None) derivation.
        profile_path = _make_standard_layout(tmp_path)
        default_result = validate_profile(profile_path)
        explicit_result = validate_profile(profile_path, docs_dir=tmp_path / "docs")
        self.assertEqual(_has_missing_playlist_finding(default_result), _has_missing_playlist_finding(explicit_result))

    # --- v6 retirement tests ---
    def test_retired_model_is_recognized_but_flagged(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "tier": "pro", "model_preference": "v5.5 Pro"}
        result = validate_profile(write_profile(tmp_path, data))
        retired = [f for f in result["findings"] if "retired" in f.get("issue", "")]
        self.assertTrue(retired)
        self.assertEqual(retired[0]["severity"], "medium")
        self.assertIn("v6", retired[0]["fix"])
        self.assertEqual(result["status"], "warning")  # recognized, not invalid

    def test_v6_family_profiles_are_clean(self):
        tmp_path = self.tmp_path
        for model in ("v6", "v6-wild", "v6-mini"):
            data = {**VALID_PROFILE, "tier": "pro", "model_preference": model}
            result = validate_profile(write_profile(tmp_path, data))
            self.assertFalse(any(f.get("location", {}).get("field") == "model_preference"
                                 for f in result["findings"]), model)

    def test_free_tier_model_is_v6_mini(self):
        tmp_path = self.tmp_path
        data = {**VALID_PROFILE, "tier": "free", "model_preference": "v6"}
        result = validate_profile(write_profile(tmp_path, data))
        self.assertTrue(any("v6-mini" in f.get("fix", "") for f in result["findings"]))

    def test_songbook_dir_override_follows_config_location(self):
        tmp_path = self.tmp_path
        # songbook_folder relocated: the default {docs}/songbook no longer holds the
        # entries, so only an explicit songbook_dir finds them.
        profile_path = _make_standard_layout(tmp_path)
        moved = tmp_path / "music" / "songbook"
        moved.parent.mkdir()
        (tmp_path / "docs" / "songbook").rename(moved)
        self.assertFalse(_has_missing_playlist_finding(validate_profile(profile_path)))
        self.assertTrue(_has_missing_playlist_finding(validate_profile(profile_path, songbook_dir=moved)))

    def test_cli_reads_songbook_folder_from_config(self):
        tmp_path = self.tmp_path
        import subprocess
        profile_path = _make_standard_layout(tmp_path)
        moved = tmp_path / "music" / "songbook"
        moved.parent.mkdir()
        (tmp_path / "docs" / "songbook").rename(moved)
        (tmp_path / "_bmad").mkdir()
        (tmp_path / "_bmad" / "config.toml").write_text(
            "[modules.suno]\nsongbook_folder = 'music/songbook'\n")
        install_resolver(tmp_path)
        script = Path(__file__).parent.parent / "validate-profile.py"
        proc = subprocess.run([sys.executable, str(script), str(profile_path),
                               "--project-root", str(tmp_path)], capture_output=True, text=True)
        self.assertTrue(_has_missing_playlist_finding(json.loads(proc.stdout)))


def _run_cli(*args):
    import subprocess
    script = Path(__file__).parent.parent / "validate-profile.py"
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          capture_output=True, text=True)


def _configured_project(root: Path):
    """A standard layout whose module config names both folders, as `bmad setup suno` writes them."""
    profile_path = _make_standard_layout(root)
    (root / "_bmad").mkdir()
    (root / "_bmad" / "config.toml").write_text(
        "[modules.suno]\n"
        "band_profiles_folder = '{project-root}/docs/band-profiles'\n"
        "songbook_folder = '{project-root}/docs/songbook'\n")
    install_resolver(root)
    (root / "docs" / "test-band-playlist.yaml").write_text('album: "X"\ntracks: []\n')
    draft = profile_path.parent / "drafts" / "test-band.yaml"
    draft.parent.mkdir()
    draft.write_text(profile_path.read_text())
    return profile_path, draft


class TestStagedDrafts(TmpPathTestCase):
    """A draft in {profiles}/drafts/ is checked against the band's real folders."""

    def test_staged_draft_of_band_with_songs_passes(self):
        _, draft = _configured_project(self.tmp_path)
        proc = _run_cli("test-band", "--staged", draft, "--project-root", self.tmp_path)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        result = json.loads(proc.stdout)
        self.assertEqual(result["status"], "pass")
        self.assertFalse(_has_missing_playlist_finding(result))

    def test_draft_path_with_project_root_passes(self):
        # The pre-fix call form: before, docs resolved to the band-profiles folder
        # and every Edit of a band with songs failed on a phantom missing playlist.
        _, draft = _configured_project(self.tmp_path)
        proc = _run_cli(draft, "--project-root", self.tmp_path)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertFalse(_has_missing_playlist_finding(json.loads(proc.stdout)))

    def test_draft_path_without_project_root_uses_profiles_parent(self):
        _, draft = _configured_project(self.tmp_path)
        proc = _run_cli(draft)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertFalse(_has_missing_playlist_finding(json.loads(proc.stdout)))

    def test_staged_draft_still_flags_a_truly_missing_playlist(self):
        _, draft = _configured_project(self.tmp_path)
        (self.tmp_path / "docs" / "test-band-playlist.yaml").unlink()
        proc = _run_cli("test-band", "--staged", draft, "--project-root", self.tmp_path)
        self.assertEqual(proc.returncode, 1)
        result = json.loads(proc.stdout)
        self.assertTrue(_has_missing_playlist_finding(result))
        finding = next(f for f in result["findings"] if "playlist YAML" in f.get("issue", ""))
        self.assertEqual(finding["location"]["expected_file"],
                         str(self.tmp_path / "docs" / "test-band-playlist.yaml"))

    def test_staged_slug_wins_over_draft_filename(self):
        _, draft = _configured_project(self.tmp_path)
        odd = draft.parent / "scratch-copy.yaml"
        draft.rename(odd)
        result = json.loads(_run_cli("test-band", "--staged", odd,
                                     "--project-root", self.tmp_path).stdout)
        self.assertEqual(result["status"], "pass")
        self.assertFalse(any(f.get("location", {}).get("field") == "name" for f in result["findings"]))

    def test_slug_positional_validates_saved_profile(self):
        _configured_project(self.tmp_path)
        proc = _run_cli("test-band", "--project-root", self.tmp_path)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertTrue(json.loads(proc.stdout)["skill_path"].endswith("band-profiles/test-band.yaml"))

    def test_unknown_slug_fails_with_reason(self):
        _configured_project(self.tmp_path)
        proc = _run_cli("no-such-band", "--project-root", self.tmp_path)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("does not exist", proc.stdout)

    def test_derive_filename_reports_slug(self):
        out = json.loads(_run_cli("--derive-filename", "Ember Hollow - Redux").stdout)
        self.assertEqual(out["slug"], "ember-hollow-redux")
        self.assertEqual(out["filename"], "ember-hollow-redux.yaml")


class TestSchemaRules16To19(TmpPathTestCase):
    def _field_findings(self, data, field, filename="test-band.yaml"):
        path = self.tmp_path / filename
        path.write_text(yaml.dump(data))
        return [f for f in validate_profile(path)["findings"]
                if f.get("location", {}).get("field") == field]

    def test_rule16_filename_matches_name(self):
        self.assertEqual(self._field_findings(VALID_PROFILE, "name"), [])

    def test_rule16_filename_mismatch_is_low(self):
        found = self._field_findings({**VALID_PROFILE, "name": "Renamed Band"}, "name")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["severity"], "low")
        self.assertIn("renamed-band.yaml", found[0]["issue"])

    def test_rule16_punctuated_name_matches_its_slug(self):
        data = {**VALID_PROFILE, "name": "Rosa's Voice"}
        self.assertEqual(self._field_findings(data, "name", "rosas-voice.yaml"), [])

    def test_rule17_voice_with_gender_warns_low(self):
        data = {**PRO_PROFILE, "vocal": {**PRO_PROFILE["vocal"], "voice_id": "v-1"}}
        found = self._field_findings(data, "vocal.gender")
        self.assertEqual([f["severity"] for f in found], ["low"])

    def test_rule17_voice_without_gender_is_valid(self):
        vocal = {k: v for k, v in PRO_PROFILE["vocal"].items() if k != "gender"}
        data = {**PRO_PROFILE, "vocal": {**vocal, "voice_id": "v-1"}}
        path = self.tmp_path / "test-band.yaml"
        path.write_text(yaml.dump(data))
        result = validate_profile(path)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["findings"], [])

    def test_gender_still_required_without_voice(self):
        vocal = {k: v for k, v in PRO_PROFILE["vocal"].items() if k != "gender"}
        found = self._field_findings({**PRO_PROFILE, "vocal": vocal}, "vocal.gender")
        self.assertEqual([f["severity"] for f in found], ["high"])

    def test_rule19_custom_model_on_free_warns(self):
        found = self._field_findings({**VALID_PROFILE, "custom_model_id": "cm-1"}, "custom_model_id")
        self.assertEqual([f["severity"] for f in found], ["medium"])

    def test_rule19_custom_model_on_pro_is_fine(self):
        self.assertEqual(self._field_findings({**PRO_PROFILE, "custom_model_id": "cm-1"},
                                              "custom_model_id"), [])


if __name__ == "__main__":
    unittest.main()


class TestDeprecatedPlaylistBlock(TmpPathTestCase):
    def test_playlist_block_flagged_as_mapping_or_list(self):
        for block in ({"tracks": ["a", "b"]}, ["a", "b"]):
            with self.subTest(block=type(block).__name__):
                path = write_profile(self.tmp_path, {**VALID_PROFILE, "playlist": block})
                result = validate_profile(path)
                deprecations = [f for f in result["findings"] if f["category"] == "deprecation"]
                self.assertTrue(deprecations, result["findings"])
