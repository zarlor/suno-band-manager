#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for merge-config.py — config merge, anti-zombie, user-key split,
legacy fallback, malformed-YAML handling, and --create-dirs."""

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
            "core": {"user_name": "Lenny", "communication_language": "English",
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
        assert user["user_name"] == "Lenny"
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


def test_init_compatible_configs_written():
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
        assert (bmad / "core" / "config.yaml").exists()
        assert (bmad / "suno" / "config.yaml").exists()


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


if __name__ == "__main__":
    tests = [
        test_fresh_install_writes_core_and_module,
        test_user_setting_module_var_goes_to_user_config,
        test_result_template_no_double_prefix,
        test_anti_zombie_removes_stale_keys,
        test_init_compatible_configs_written,
        test_malformed_existing_config_clean_error,
        test_missing_module_yaml_errors,
        test_create_dirs_honors_declaration,
        test_create_dirs_requires_project_root,
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
