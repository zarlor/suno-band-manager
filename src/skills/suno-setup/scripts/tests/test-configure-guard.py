#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for configure-guard.py — Claude hook merge, AGENTS.md standing order,
idempotency, malformed-settings handling, and exit codes."""

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


if __name__ == "__main__":
    tests = [
        test_no_targets_exit_1,
        test_claude_hook_configured_then_idempotent,
        test_claude_hook_preserves_other_settings,
        test_malformed_settings_exit_2,
        test_agents_md_created_then_idempotent,
        test_agents_md_appends_preserving_content,
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
