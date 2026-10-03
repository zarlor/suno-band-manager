#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for merge-config.py — config merge, anti-zombie, user-key split,
value priority (answers > existing > legacy > defaults), truthful preview,
per-module bridge scope, malformed-YAML handling, --create-dirs and the
unresolved-token guard."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve().parent.parent / "merge-config.py"

MODULE_YAML = """\
code: suno
name: "Suno Band Manager"
description: "Test module"
module_version: 1.8.3
default_selected: false
suno_tier:
  prompt: "What plan?"
  default: "free"
  result: "{value}"
band_profiles_folder:
  prompt: "Where?"
  default: "docs/band-profiles"
  result: "{project-root}/{value}"
api_key:
  prompt: "API key?"
  default: ""
  result: "{value}"
  user_setting: true
directories:
  - "{band_profiles_folder}"
"""


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def run(args: list[str]) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, data


def setup(tmp: Path, answers: dict) -> dict:
    """Write module.yaml + answers and return the standard merge args."""
    module_yaml = write(tmp / "module.yaml", MODULE_YAML)
    answers_file = write(tmp / "answers.json", json.dumps(answers))
    return {
        "config": str(tmp / "config.yaml"),
        "user_config": str(tmp / "config.user.yaml"),
        "module_yaml": str(module_yaml),
        "answers": str(answers_file),
    }


def merge_args(a: dict) -> list[str]:
    return [
        "--config-path", a["config"],
        "--user-config-path", a["user_config"],
        "--module-yaml", a["module_yaml"],
        "--answers", a["answers"],
    ]


def test_fresh_install_writes_core_and_module():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        a = setup(tmp, {
            "core": {"user_name": "Ada", "communication_language": "English",
                     "output_folder": "{project-root}/_bmad-output"},
            "module": {"suno_tier": "pro"},
        })
        code, data = run(merge_args(a))
        assert code == 0, data
        config = yaml.safe_load(Path(a["config"]).read_text())
        # core at root, module section present
        assert config["output_folder"] == "{project-root}/_bmad-output"
        assert config["suno"]["suno_tier"] == "pro"
        # user-only keys NOT in shared config
        assert "user_name" not in config
        assert "communication_language" not in config
        # user keys in user config
        user = yaml.safe_load(Path(a["user_config"]).read_text())
        assert user["user_name"] == "Ada"
        assert user["communication_language"] == "English"


def test_user_setting_module_var_goes_to_user_config():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        a = setup(tmp, {"module": {"api_key": "secret123"}})
        code, data = run(merge_args(a))
        assert code == 0, data
        user = yaml.safe_load(Path(a["user_config"]).read_text())
        assert user["api_key"] == "secret123"


def test_result_template_no_double_prefix():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        a = setup(tmp, {"module": {"band_profiles_folder": "docs/bands"}})
        code, data = run(merge_args(a))
        assert code == 0, data
        config = yaml.safe_load(Path(a["config"]).read_text())
        assert config["suno"]["band_profiles_folder"] == "{project-root}/docs/bands"
        # Re-running with an already-prefixed value must not double-prefix
        a2 = setup(tmp, {"module": {"band_profiles_folder": "{project-root}/docs/bands"}})
        code, _ = run(merge_args(a2))
        assert code == 0
        config = yaml.safe_load(Path(a2["config"]).read_text())
        assert config["suno"]["band_profiles_folder"] == "{project-root}/docs/bands"


def test_anti_zombie_removes_stale_keys():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        a = setup(tmp, {"module": {"suno_tier": "pro"}})
        run(merge_args(a))
        # Inject a stale key into the module section, then re-merge
        config = yaml.safe_load(Path(a["config"]).read_text())
        config["suno"]["stale_key"] = "zombie"
        Path(a["config"]).write_text(yaml.dump(config))
        a2 = setup(tmp, {"module": {"suno_tier": "free"}})
        run(merge_args(a2))
        config = yaml.safe_load(Path(a["config"]).read_text())
        assert "stale_key" not in config["suno"]
        assert config["suno"]["suno_tier"] == "free"


def test_bridge_config_written_for_module_only():
    """Standalone (no installer): the suno bridge is written; core/config.yaml never is."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bmad = tmp / "_bmad"
        bmad.mkdir()
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        answers = write(tmp / "answers.json", json.dumps(
            {"core": {"output_folder": "{project-root}/out"}, "module": {"suno_tier": "pro"}}
        ))
        code, data = run([
            "--config-path", str(bmad / "config.yaml"),
            "--user-config-path", str(bmad / "config.user.yaml"),
            "--module-yaml", str(module_yaml),
            "--answers", str(answers),
        ])
        assert code == 0, data
        assert not (bmad / "core" / "config.yaml").exists()
        bridge = (bmad / "suno" / "config.yaml").read_text()
        assert bridge.startswith("# Written by suno-setup")
        assert yaml.safe_load(bridge)["suno_tier"] == "pro"
        assert data["init_configs_written"] == [str(bmad / "suno" / "config.yaml")]


def test_bridge_skipped_and_core_untouched_when_installer_managed():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bmad = tmp / "_bmad"
        (bmad / "_config").mkdir(parents=True)
        (bmad / "core").mkdir()
        (bmad / "suno").mkdir()
        write(bmad / "_config" / "manifest.yaml", "modules:\n  - name: core\n")
        core_text = "# Generated by BMAD installer\nuser_name: Ada\nproject_name: demo\n"
        write(bmad / "core" / "config.yaml", core_text)
        suno_text = "# Generated by BMAD installer\nuser_name: Ada\n"
        write(bmad / "suno" / "config.yaml", suno_text)
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        answers = write(tmp / "answers.json", json.dumps({"module": {"suno_tier": "pro"}}))
        code, data = run([
            "--config-path", str(bmad / "config.yaml"),
            "--user-config-path", str(bmad / "config.user.yaml"),
            "--module-yaml", str(module_yaml),
            "--answers", str(answers),
            "--legacy-dir", str(bmad),
        ])
        assert code == 0, data
        assert (bmad / "core" / "config.yaml").read_text() == core_text
        assert (bmad / "suno" / "config.yaml").read_text() == suno_text
        assert data["init_configs_written"] == []
        assert data["init_configs_skipped"][0]["reason"] == "installer_managed"
        # Installer core values still seed the user config (read only).
        assert yaml.safe_load((bmad / "config.user.yaml").read_text())["user_name"] == "Ada"


def test_existing_values_beat_legacy_and_preview_is_truthful():
    """Regression: the preview said 'no changes' while the merge reset hand-edited
    values to core/config.yaml's. Existing values must win and the preview must
    equal the written delta."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bmad = tmp / "_bmad"
        (bmad / "core").mkdir(parents=True)
        write(bmad / "core" / "config.yaml",
              "user_name: Installer\noutput_folder: '{project-root}/_bmad-output'\n")
        write(bmad / "config.yaml",
              "output_folder: '{project-root}/hand-edited'\ndocument_output_language: English\n"
              "suno:\n  version: 1.8.2\n  suno_tier: pro\n"
              "  band_profiles_folder: '{project-root}/docs/band-profiles'\n")
        write(bmad / "config.user.yaml", "user_name: Grace\ncommunication_language: English\napi_key: k\n")
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        answers = write(tmp / "answers.json", json.dumps({}))
        common = ["--config-path", str(bmad / "config.yaml"), "--module-yaml", str(module_yaml),
                  "--answers", str(answers), "--legacy-dir", str(bmad)]
        code, preview = run(["--detect-mode", *common])
        assert code == 0, preview
        assert preview["changes"] == []
        code, data = run([*common, "--user-config-path", str(bmad / "config.user.yaml")])
        assert code == 0, data
        assert data["changes"] == []
        config = yaml.safe_load((bmad / "config.yaml").read_text())
        user = yaml.safe_load((bmad / "config.user.yaml").read_text())
        assert config["output_folder"] == "{project-root}/hand-edited"
        assert config["suno"]["suno_tier"] == "pro"  # omitted from answers, kept
        assert user["user_name"] == "Grace"
        assert config["suno"]["version"] == "1.8.3"


def test_preview_equals_written_delta_on_change():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bmad = tmp / "_bmad"
        bmad.mkdir()
        write(bmad / "config.yaml",
              "output_folder: '{project-root}/out'\ndocument_output_language: English\n"
              "suno:\n  suno_tier: free\n  band_profiles_folder: '{project-root}/docs/band-profiles'\n"
              "  retired_key: zombie\n")
        write(bmad / "config.user.yaml", "user_name: Grace\ncommunication_language: English\napi_key: k\n")
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        answers = write(tmp / "answers.json", json.dumps(
            {"core": {"user_name": "Ada"}, "module": {"suno_tier": "pro"}}))
        common = ["--config-path", str(bmad / "config.yaml"), "--module-yaml", str(module_yaml),
                  "--answers", str(answers)]
        _, preview = run(["--detect-mode", *common])
        _, merged = run([*common, "--user-config-path", str(bmad / "config.user.yaml")])
        assert preview["changes"] == merged["changes"]
        assert sorted((c["file"], c["key"], c["old"], c["new"]) for c in preview["changes"]) == [
            ("config", "retired_key", "zombie", None),
            ("config", "suno_tier", "free", "pro"),
            ("user_config", "user_name", "Grace", "Ada"),
        ]


def test_legacy_files_are_never_deleted():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bmad = tmp / "_bmad"
        (bmad / "core").mkdir(parents=True)
        core_text = "user_name: Ada\nproject_name: demo\n"
        write(bmad / "core" / "config.yaml", core_text)
        a = setup(tmp, {"module": {"suno_tier": "pro"}})
        code, data = run([
            "--config-path", str(bmad / "config.yaml"),
            "--user-config-path", str(bmad / "config.user.yaml"),
            "--module-yaml", a["module_yaml"], "--answers", a["answers"], "--legacy-dir", str(bmad),
        ])
        assert code == 0, data
        assert (bmad / "core" / "config.yaml").read_text() == core_text
        assert data["legacy_configs_read"] == [str(bmad / "core" / "config.yaml")]


def test_unresolved_project_root_rejected_in_every_mode():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        a = setup(tmp, {"module": {}})
        bad = "{project-root}/_bmad/config.yaml"
        for extra in (
            ["--user-config-path", a["user_config"], "--answers", a["answers"]],
            ["--detect-mode"],
            ["--create-dirs", "--project-root", str(tmp)],
        ):
            code, data = run(["--config-path", bad, "--module-yaml", a["module_yaml"], *extra])
            assert code == 1, (extra, data)
            assert "{project-root}" in data["error"]
        code, data = run(["--create-dirs", "--config-path", a["config"], "--module-yaml", a["module_yaml"],
                          "--project-root", "{project-root}"])
        assert code == 1, data


def test_malformed_existing_config_clean_error():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        a = setup(tmp, {"module": {"suno_tier": "pro"}})
        # corrupt existing config
        Path(a["config"]).write_text("key: [unterminated\n")
        code, data = run(merge_args(a))
        assert code == 1, (code, data)
        assert data["status"] == "error"
        assert "Malformed YAML" in data["error"]


def test_missing_module_yaml_errors():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        answers = write(tmp / "answers.json", json.dumps({"module": {}}))
        code, _ = run([
            "--config-path", str(tmp / "config.yaml"),
            "--user-config-path", str(tmp / "config.user.yaml"),
            "--module-yaml", str(tmp / "missing.yaml"),
            "--answers", str(answers),
        ])
        assert code == 1


def test_create_dirs_honors_declaration():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        a = setup(tmp, {
            "core": {"output_folder": "{project-root}/_bmad-output"},
            "module": {"band_profiles_folder": "docs/bands"},
        })
        run(merge_args(a))  # writes config.yaml with resolved values
        proj = tmp / "proj"
        proj.mkdir()
        code, data = run([
            "--create-dirs",
            "--config-path", a["config"],
            "--module-yaml", a["module_yaml"],
            "--project-root", str(proj),
        ])
        assert code == 0, data
        assert (proj / "_bmad-output").is_dir()
        assert (proj / "docs" / "bands").is_dir()
        assert "{project-root}/_bmad-output" in data["created"]
        # Second run reports them as existed
        code, data = run([
            "--create-dirs",
            "--config-path", a["config"],
            "--module-yaml", a["module_yaml"],
            "--project-root", str(proj),
        ])
        assert code == 0
        assert data["created"] == []
        assert len(data["existed"]) == 2


def test_create_dirs_requires_project_root():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        write(tmp / "config.yaml", "output_folder: '{project-root}/out'\n")
        code, data = run([
            "--create-dirs",
            "--config-path", str(tmp / "config.yaml"),
            "--module-yaml", str(module_yaml),
        ])
        assert code == 1
        assert data["status"] == "error"


def test_detect_mode_fresh_and_standalone():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        bmad = tmp / "_bmad"
        bmad.mkdir()
        # _bmad/ exists, no module section, no legacy → fresh
        code, data = run([
            "--detect-mode",
            "--config-path", str(bmad / "config.yaml"),
            "--module-yaml", str(module_yaml),
        ])
        assert code == 0, data
        assert data["mode"] == "fresh"
        assert data["has_module_section"] is False
        assert data["version_transition"]["to"] == "1.8.3"
        # no _bmad/ dir → standalone
        code, data = run([
            "--detect-mode",
            "--config-path", str(tmp / "nodir" / "config.yaml"),
            "--module-yaml", str(module_yaml),
        ])
        assert code == 0, data
        assert data["mode"] == "standalone"


def test_detect_mode_update_not_migration_with_init_files():
    """A consolidated section + leftover init bridge files is an update, not
    a migration — the installer's own per-module configs aren't legacy."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        bmad = tmp / "_bmad"
        (bmad / "suno").mkdir(parents=True)
        (bmad / "core").mkdir()
        write(bmad / "config.yaml",
              "suno:\n  version: 1.8.2\n  suno_tier: free\n")
        write(bmad / "suno" / "config.yaml", "suno_tier: free\n")
        write(bmad / "core" / "config.yaml", "output_folder: x\n")
        code, data = run([
            "--detect-mode",
            "--config-path", str(bmad / "config.yaml"),
            "--module-yaml", str(module_yaml),
            "--legacy-dir", str(bmad),
        ])
        assert code == 0, data
        assert data["mode"] == "update"
        assert data["has_module_section"] is True
        assert data["has_legacy"] is True
        assert data["version_transition"] == {"from": "1.8.2", "to": "1.8.3"}


def test_detect_mode_migration_legacy_without_section():
    """Legacy init config but NO consolidated section → genuine migration."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        bmad = tmp / "_bmad"
        (bmad / "suno").mkdir(parents=True)
        write(bmad / "suno" / "config.yaml", "suno_tier: pro\n")
        code, data = run([
            "--detect-mode",
            "--config-path", str(bmad / "config.yaml"),
            "--module-yaml", str(module_yaml),
            "--legacy-dir", str(bmad),
        ])
        assert code == 0, data
        assert data["mode"] == "migration"
        assert data["has_module_section"] is False
        assert data["has_legacy"] is True


def test_detect_mode_changes_diff():
    """With --answers, detect-mode returns a result-template-aware diff of only
    the values that actually change, tagged with the file they land in."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        bmad = tmp / "_bmad"
        bmad.mkdir()
        write(bmad / "config.yaml",
              "output_folder: '{project-root}/_bmad-output'\ndocument_output_language: English\n"
              "suno:\n  version: 1.8.2\n  suno_tier: free\n"
              "  band_profiles_folder: '{project-root}/docs/band-profiles'\n")
        write(bmad / "config.user.yaml", "user_name: Ada\ncommunication_language: English\napi_key: ''\n")
        answers = write(tmp / "answers.json", json.dumps({
            "core": {"output_folder": "{project-root}/_bmad-output", "user_name": "Ada"},
            "module": {"suno_tier": "pro", "band_profiles_folder": "docs/band-profiles"},
        }))
        code, data = run([
            "--detect-mode",
            "--config-path", str(bmad / "config.yaml"),
            "--module-yaml", str(module_yaml),
            "--answers", str(answers),
        ])
        assert code == 0, data
        assert data["changes"] == [{"file": "config", "key": "suno_tier", "old": "free", "new": "pro"}]


def test_detect_mode_defaults_in_answer_form():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        bmad = tmp / "_bmad"
        bmad.mkdir()
        write(bmad / "config.yaml", "suno:\n  band_profiles_folder: '{project-root}/my/bands'\n")
        code, data = run(["--detect-mode", "--config-path", str(bmad / "config.yaml"),
                          "--module-yaml", str(module_yaml)])
        assert code == 0, data
        assert data["defaults"]["module"]["band_profiles_folder"] == {"value": "my/bands", "source": "existing"}
        assert data["defaults"]["module"]["suno_tier"] == {"value": "free", "source": "default"}
        assert data["defaults"]["core"]["user_name"] == {"value": "BMad", "source": "default"}
        assert data["has_core"] is False


def test_detect_mode_installer_managed_is_fresh_not_migration():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        module_yaml = write(tmp / "module.yaml", MODULE_YAML)
        bmad = tmp / "_bmad"
        (bmad / "_config").mkdir(parents=True)
        (bmad / "core").mkdir()
        write(bmad / "_config" / "manifest.yaml", "modules:\n  - name: core\n")
        write(bmad / "core" / "config.yaml", "user_name: Ada\n")
        code, data = run(["--detect-mode", "--config-path", str(bmad / "config.yaml"),
                          "--module-yaml", str(module_yaml), "--legacy-dir", str(bmad)])
        assert code == 0, data
        assert data["mode"] == "fresh"
        assert data["installer_managed"] is True
        assert data["has_legacy"] is False
        assert data["cleanup_needed"] is False
        assert data["defaults"]["core"]["user_name"] == {"value": "Ada", "source": "legacy"}


if __name__ == "__main__":
    tests = [
        test_fresh_install_writes_core_and_module,
        test_user_setting_module_var_goes_to_user_config,
        test_result_template_no_double_prefix,
        test_anti_zombie_removes_stale_keys,
        test_bridge_config_written_for_module_only,
        test_bridge_skipped_and_core_untouched_when_installer_managed,
        test_existing_values_beat_legacy_and_preview_is_truthful,
        test_preview_equals_written_delta_on_change,
        test_legacy_files_are_never_deleted,
        test_unresolved_project_root_rejected_in_every_mode,
        test_malformed_existing_config_clean_error,
        test_missing_module_yaml_errors,
        test_create_dirs_honors_declaration,
        test_create_dirs_requires_project_root,
        test_detect_mode_fresh_and_standalone,
        test_detect_mode_update_not_migration_with_init_files,
        test_detect_mode_migration_legacy_without_section,
        test_detect_mode_changes_diff,
        test_detect_mode_defaults_in_answer_form,
        test_detect_mode_installer_managed_is_fresh_not_migration,
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
