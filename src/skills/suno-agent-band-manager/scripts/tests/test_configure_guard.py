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
import unittest
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


class ConfigureGuardTests(unittest.TestCase):
    def test_no_targets_exit_1(self):
        code, data = run([])
        self.assertEqual(code, 1, (code, data))
        self.assertEqual(statuses(data), ["error"])

    def test_claude_hook_configured_then_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / ".claude" / "settings.local.json"
            code, data = run([
                "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
            ])
            self.assertEqual(code, 0, data)
            self.assertEqual(statuses(data), ["configured"])
            written = json.loads(settings.read_text())
            cmd = written["hooks"]["Stop"][0]["hooks"][0]["command"]
            self.assertIn("pipeline-guard", cmd)
            self.assertIn("$CLAUDE_PROJECT_DIR", cmd)
            # Re-run: idempotent
            code, data = run([
                "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
            ])
            self.assertEqual(code, 0)
            self.assertEqual(statuses(data), ["already_configured"])
            # Still just one hook entry
            written = json.loads(settings.read_text())
            self.assertEqual(len(written["hooks"]["Stop"]), 1)

    def test_claude_hook_preserves_other_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / "settings.local.json"
            settings.write_text(json.dumps({"permissions": {"allow": ["Bash"]}}))
            code, _ = run([
                "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
            ])
            self.assertEqual(code, 0)
            written = json.loads(settings.read_text())
            self.assertEqual(written["permissions"]["allow"], ["Bash"])
            self.assertIn("Stop", written["hooks"])

    def test_malformed_settings_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / "settings.local.json"
            settings.write_text("{ not valid json")
            code, data = run([
                "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
            ])
            self.assertEqual(code, 2, (code, data))
            self.assertEqual(statuses(data), ["error"])

    def test_agents_md_created_then_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp) / "AGENTS.md"
            code, data = run(["--agents-md-path", str(agents)])
            self.assertEqual(code, 0, data)
            self.assertEqual(statuses(data), ["configured"])
            self.assertIn("Suno Pipeline Rule", agents.read_text())
            code, data = run(["--agents-md-path", str(agents)])
            self.assertEqual(code, 0)
            self.assertEqual(statuses(data), ["already_configured"])

    def test_agents_md_appends_preserving_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp) / "AGENTS.md"
            agents.write_text("# Existing instructions\n\nKeep me.\n")
            code, _ = run(["--agents-md-path", str(agents)])
            self.assertEqual(code, 0)
            content = agents.read_text()
            self.assertIn("Keep me.", content)
            self.assertIn("Suno Pipeline Rule", content)

    def test_unresolved_project_root_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, data = run(["--agents-md-path", "{project-root}/AGENTS.md"])
            self.assertEqual(code, 1, (code, data))
            self.assertEqual(statuses(data), ["error"])
            self.assertFalse(Path("{project-root}").exists())
            code, data = run(["--settings-path", str(Path(tmp) / "s.json"),
                              "--guard-script-path", "{project-root}/x/pipeline-guard.py"])
            self.assertEqual(code, 1, (code, data))

    def test_dominion_hook_installed_beside_stop_then_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / ".claude" / "settings.local.json"
            args = ["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"]
            code, data = run(args)
            self.assertEqual(code, 0, data)
            self.assertEqual([(r["target"], r["status"]) for r in data["results"]], [
                ("claude_hook", "configured"), ("dominion_hook", "configured")])
            written = json.loads(settings.read_text())
            pre = written["hooks"]["PreToolUse"]
            self.assertEqual(len(pre), 1)
            self.assertTrue("Write" in pre[0]["matcher"] and "Edit" in pre[0]["matcher"])
            cmd = pre[0]["hooks"][0]["command"]
            self.assertTrue(cmd.startswith("python3 ") and cmd.endswith("pipeline-guard.py --dominion"))
            self.assertNotIn("--dominion", written["hooks"]["Stop"][0]["hooks"][0]["command"])
            code, data = run(args)
            self.assertEqual(code, 0)
            self.assertEqual(statuses(data), ["already_configured", "already_configured"])
            written = json.loads(settings.read_text())
            self.assertTrue(len(written["hooks"]["PreToolUse"]) == 1 and len(written["hooks"]["Stop"]) == 1)

    def test_dominion_hook_added_to_existing_stop_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / "settings.local.json"
            run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH])
            code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
            self.assertEqual(code, 0)
            self.assertEqual(statuses(data), ["already_configured", "configured"])

    def test_dominion_hook_preserves_other_pretooluse_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / "settings.local.json"
            other = {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo hi"}]}
            settings.write_text(json.dumps({"hooks": {"PreToolUse": [other]}}))
            code, _ = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
            self.assertEqual(code, 0)
            pre = json.loads(settings.read_text())["hooks"]["PreToolUse"]
            self.assertTrue(pre[0] == other and len(pre) == 2)

    def test_dominion_hook_without_settings_paths_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, data = run(["--dominion-hook", "--agents-md-path", str(Path(tmp) / "AGENTS.md")])
            self.assertEqual(code, 1, (code, data))
            self.assertEqual(statuses(data), ["error"])
            self.assertFalse((Path(tmp) / "AGENTS.md").exists())

    def test_malformed_settings_with_dominion_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / "settings.local.json"
            settings.write_text("{ not valid json")
            code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
            self.assertEqual(code, 2, (code, data))
            self.assertEqual(statuses(data), ["error", "error"])
            self.assertEqual(settings.read_text(), "{ not valid json")


if __name__ == "__main__":
    unittest.main()
