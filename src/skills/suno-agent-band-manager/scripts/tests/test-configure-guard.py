#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for configure-guard.py — Claude hook merge (Stop and the optional
Dominion PreToolUse hook), AGENTS.md standing order, idempotency,
malformed-settings handling, and exit codes."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "configure-guard.py"

GUARD_PATH = ".claude/skills/suno-agent-band-manager/scripts/pipeline-guard.py"


def run(args: list[str]) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, data


def statuses(data: dict) -> list[str]:
    return [r.get("status") for r in data.get("results", [])]


def test_no_targets_exit_1():
    code, data = run([])
    assert code == 1, (code, data)
    assert statuses(data) == ["error"]


def test_claude_hook_configured_then_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / ".claude" / "settings.local.json"
        code, data = run([
            "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
        ])
        assert code == 0, data
        assert statuses(data) == ["configured"]
        written = json.loads(settings.read_text())
        cmd = written["hooks"]["Stop"][0]["hooks"][0]["command"]
        assert "pipeline-guard" in cmd
        assert "$CLAUDE_PROJECT_DIR" in cmd
        # Re-run: idempotent
        code, data = run([
            "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
        ])
        assert code == 0
        assert statuses(data) == ["already_configured"]
        # Still just one hook entry
        written = json.loads(settings.read_text())
        assert len(written["hooks"]["Stop"]) == 1


def test_claude_hook_preserves_other_settings():
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / "settings.local.json"
        settings.write_text(json.dumps({"permissions": {"allow": ["Bash"]}}))
        code, _ = run([
            "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
        ])
        assert code == 0
        written = json.loads(settings.read_text())
        assert written["permissions"]["allow"] == ["Bash"]
        assert "Stop" in written["hooks"]


def test_malformed_settings_exit_2():
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / "settings.local.json"
        settings.write_text("{ not valid json")
        code, data = run([
            "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
        ])
        assert code == 2, (code, data)
        assert statuses(data) == ["error"]


def test_agents_md_created_then_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        agents = Path(tmp) / "AGENTS.md"
        code, data = run(["--agents-md-path", str(agents)])
        assert code == 0, data
        assert statuses(data) == ["configured"]
        assert "Suno Pipeline Rule" in agents.read_text()
        code, data = run(["--agents-md-path", str(agents)])
        assert code == 0
        assert statuses(data) == ["already_configured"]


def test_agents_md_appends_preserving_content():
    with tempfile.TemporaryDirectory() as tmp:
        agents = Path(tmp) / "AGENTS.md"
        agents.write_text("# Existing instructions\n\nKeep me.\n")
        code, _ = run(["--agents-md-path", str(agents)])
        assert code == 0
        content = agents.read_text()
        assert "Keep me." in content
        assert "Suno Pipeline Rule" in content


def test_unresolved_project_root_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        code, data = run(["--agents-md-path", "{project-root}/AGENTS.md"])
        assert code == 1, (code, data)
        assert statuses(data) == ["error"]
        assert not Path("{project-root}").exists()
        code, data = run(["--settings-path", str(Path(tmp) / "s.json"),
                          "--guard-script-path", "{project-root}/x/pipeline-guard.py"])
        assert code == 1, (code, data)


def test_dominion_hook_installed_beside_stop_then_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / ".claude" / "settings.local.json"
        args = ["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"]
        code, data = run(args)
        assert code == 0, data
        assert [(r["target"], r["status"]) for r in data["results"]] == [
            ("claude_hook", "configured"), ("dominion_hook", "configured")]
        written = json.loads(settings.read_text())
        pre = written["hooks"]["PreToolUse"]
        assert len(pre) == 1
        assert "Write" in pre[0]["matcher"] and "Edit" in pre[0]["matcher"]
        cmd = pre[0]["hooks"][0]["command"]
        assert cmd.startswith("python3 ") and cmd.endswith("pipeline-guard.py --dominion")
        assert "--dominion" not in written["hooks"]["Stop"][0]["hooks"][0]["command"]
        code, data = run(args)
        assert code == 0
        assert statuses(data) == ["already_configured", "already_configured"]
        written = json.loads(settings.read_text())
        assert len(written["hooks"]["PreToolUse"]) == 1 and len(written["hooks"]["Stop"]) == 1


def test_dominion_hook_added_to_existing_stop_install():
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / "settings.local.json"
        run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH])
        code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
        assert code == 0
        assert statuses(data) == ["already_configured", "configured"]


def test_dominion_hook_preserves_other_pretooluse_hooks():
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / "settings.local.json"
        other = {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo hi"}]}
        settings.write_text(json.dumps({"hooks": {"PreToolUse": [other]}}))
        code, _ = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
        assert code == 0
        pre = json.loads(settings.read_text())["hooks"]["PreToolUse"]
        assert pre[0] == other and len(pre) == 2


def test_dominion_hook_without_settings_paths_exit_1():
    with tempfile.TemporaryDirectory() as tmp:
        code, data = run(["--dominion-hook", "--agents-md-path", str(Path(tmp) / "AGENTS.md")])
        assert code == 1, (code, data)
        assert statuses(data) == ["error"]
        assert not (Path(tmp) / "AGENTS.md").exists()


def test_malformed_settings_with_dominion_exit_2():
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / "settings.local.json"
        settings.write_text("{ not valid json")
        code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
        assert code == 2, (code, data)
        assert statuses(data) == ["error", "error"]
        assert settings.read_text() == "{ not valid json"


if __name__ == "__main__":
    tests = [
        test_unresolved_project_root_rejected,
        test_no_targets_exit_1,
        test_claude_hook_configured_then_idempotent,
        test_claude_hook_preserves_other_settings,
        test_malformed_settings_exit_2,
        test_agents_md_created_then_idempotent,
        test_agents_md_appends_preserving_content,
        test_dominion_hook_installed_beside_stop_then_idempotent,
        test_dominion_hook_added_to_existing_stop_install,
        test_dominion_hook_preserves_other_pretooluse_hooks,
        test_dominion_hook_without_settings_paths_exit_1,
        test_malformed_settings_with_dominion_exit_2,
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
