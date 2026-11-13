#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for configure_guard.py — Claude hook merge (Stop and the optional
Dominion PreToolUse hook), AGENTS.md standing order, idempotency,
malformed-settings handling, and exit codes."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "configure_guard.py"

GUARD_PATH = ".claude/skills/suno-agent-band-manager/scripts/pipeline_guard.py"


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


def project(tmp: str, guard: str = GUARD_PATH) -> Path:
    """A project folder with a guard script at `guard`; returns its settings path
    (not yet written)."""
    script = Path(tmp) / guard
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("# stand-in for pipeline_guard.py\n", encoding="utf-8")
    return Path(tmp) / ".claude" / "settings.local.json"


def write_settings(settings: Path, data) -> None:
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


class ConfigureGuardTests(unittest.TestCase):
    def test_no_targets_exit_1(self):
        code, data = run([])
        self.assertEqual(code, 1, (code, data))
        self.assertEqual(statuses(data), ["error"])

    def test_claude_hook_configured_then_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            code, data = run([
                "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
            ])
            self.assertEqual(code, 0, data)
            self.assertEqual(statuses(data), ["configured"])
            written = json.loads(settings.read_text(encoding="utf-8"))
            cmd = written["hooks"]["Stop"][0]["hooks"][0]["command"]
            self.assertIn("pipeline_guard.py", cmd)
            self.assertIn("$CLAUDE_PROJECT_DIR", cmd)
            # Re-run: idempotent
            code, data = run([
                "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
            ])
            self.assertEqual(code, 0)
            self.assertEqual(statuses(data), ["already_configured"])
            # Still just one hook entry
            written = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(len(written["hooks"]["Stop"]), 1)

    def test_claude_hook_preserves_other_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            write_settings(settings, {"permissions": {"allow": ["Bash"]}})
            code, _ = run([
                "--settings-path", str(settings), "--guard-script-path", GUARD_PATH,
            ])
            self.assertEqual(code, 0)
            written = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(written["permissions"]["allow"], ["Bash"])
            self.assertIn("Stop", written["hooks"])

    def test_malformed_settings_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            write_settings(settings, "{ not valid json")
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
            self.assertIn("Suno Pipeline Rule", agents.read_text(encoding="utf-8"))
            code, data = run(["--agents-md-path", str(agents)])
            self.assertEqual(code, 0)
            self.assertEqual(statuses(data), ["already_configured"])

    def test_agents_md_appends_preserving_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp) / "AGENTS.md"
            agents.write_text("# Existing instructions\n\nKeep me.\n", encoding="utf-8")
            code, _ = run(["--agents-md-path", str(agents)])
            self.assertEqual(code, 0)
            content = agents.read_text(encoding="utf-8")
            self.assertIn("Keep me.", content)
            self.assertIn("Suno Pipeline Rule", content)

    def test_unresolved_project_root_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, data = run(["--agents-md-path", "{project-root}/AGENTS.md"])
            self.assertEqual(code, 1, (code, data))
            self.assertEqual(statuses(data), ["error"])
            self.assertFalse(Path("{project-root}").exists())
            code, data = run(["--settings-path", str(Path(tmp) / "s.json"),
                              "--guard-script-path", "{project-root}/x/pipeline_guard.py"])
            self.assertEqual(code, 1, (code, data))

    def test_dominion_hook_installed_beside_stop_then_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            args = ["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"]
            code, data = run(args)
            self.assertEqual(code, 0, data)
            self.assertEqual([(r["target"], r["status"]) for r in data["results"]], [
                ("claude_hook", "configured"), ("dominion_hook", "configured")])
            written = json.loads(settings.read_text(encoding="utf-8"))
            pre = written["hooks"]["PreToolUse"]
            self.assertEqual(len(pre), 1)
            self.assertTrue("Write" in pre[0]["matcher"] and "Edit" in pre[0]["matcher"])
            cmd = pre[0]["hooks"][0]["command"]
            self.assertTrue(cmd.startswith("python3 ") and cmd.endswith("pipeline_guard.py --dominion"))
            self.assertNotIn("--dominion", written["hooks"]["Stop"][0]["hooks"][0]["command"])
            code, data = run(args)
            self.assertEqual(code, 0)
            self.assertEqual(statuses(data), ["already_configured", "already_configured"])
            written = json.loads(settings.read_text(encoding="utf-8"))
            self.assertTrue(len(written["hooks"]["PreToolUse"]) == 1 and len(written["hooks"]["Stop"]) == 1)

    def test_dominion_hook_added_to_existing_stop_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH])
            code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
            self.assertEqual(code, 0)
            self.assertEqual(statuses(data), ["already_configured", "configured"])

    def test_dominion_hook_preserves_other_pretooluse_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            other = {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo hi"}]}
            write_settings(settings, {"hooks": {"PreToolUse": [other]}})
            code, _ = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
            self.assertEqual(code, 0)
            pre = json.loads(settings.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
            self.assertTrue(pre[0] == other and len(pre) == 2)

    def test_dominion_hook_without_settings_paths_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, data = run(["--dominion-hook", "--agents-md-path", str(Path(tmp) / "AGENTS.md")])
            self.assertEqual(code, 1, (code, data))
            self.assertEqual(statuses(data), ["error"])
            self.assertFalse((Path(tmp) / "AGENTS.md").exists())

    def test_malformed_settings_with_dominion_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            write_settings(settings, "{ not valid json")
            code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
            self.assertEqual(code, 2, (code, data))
            self.assertEqual(statuses(data), ["error", "error"])
            self.assertEqual(settings.read_text(encoding="utf-8"), "{ not valid json")


    # --- the guard script must be there (a hook on a missing script blocks every turn) ---

    def test_missing_guard_script_installs_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / ".claude" / "settings.local.json"
            write_settings(settings, {"permissions": {"allow": ["Bash"]}})
            before = settings.read_text(encoding="utf-8")
            code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
            self.assertEqual(code, 2, (code, data))
            self.assertEqual(statuses(data), ["error", "error"])
            self.assertIn("not found", data["results"][0]["message"])
            self.assertEqual(settings.read_text(encoding="utf-8"), before)

    def test_missing_guard_script_does_not_create_the_settings_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / ".claude" / "settings.local.json"
            code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH])
            self.assertEqual(code, 2, (code, data))
            self.assertFalse(settings.exists())

    def test_absolute_guard_path_inside_the_project_is_written_relative(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            code, data = run(["--settings-path", str(settings), "--guard-script-path", str(Path(tmp) / GUARD_PATH)])
            self.assertEqual(code, 0, data)
            cmd = json.loads(settings.read_text(encoding="utf-8"))["hooks"]["Stop"][0]["hooks"][0]["command"]
            self.assertEqual(cmd, f'python3 "$CLAUDE_PROJECT_DIR"/{GUARD_PATH}')

    def test_guard_outside_the_project_runs_by_its_absolute_path(self):
        """A plugin or global install: the skill is not under the project."""
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as elsewhere:
            settings = Path(tmp) / ".claude" / "settings.local.json"
            guard = Path(elsewhere) / "skills" / "suno-agent-band-manager" / "scripts" / "pipeline_guard.py"
            guard.parent.mkdir(parents=True)
            guard.write_text("# stand-in\n", encoding="utf-8")
            code, data = run(["--settings-path", str(settings), "--guard-script-path", str(guard), "--dominion-hook"])
            self.assertEqual(code, 0, data)
            hooks = json.loads(settings.read_text(encoding="utf-8"))["hooks"]
            self.assertEqual(hooks["Stop"][0]["hooks"][0]["command"], f'python3 "{guard}"')
            self.assertEqual(hooks["PreToolUse"][0]["hooks"][0]["command"], f'python3 "{guard}" --dominion')
            self.assertNotIn("CLAUDE_PROJECT_DIR", hooks["Stop"][0]["hooks"][0]["command"])

    # --- a hook left from an older location is not "already configured" ---

    def test_stale_guard_command_is_replaced_not_reported_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            old = 'python3 "$CLAUDE_PROJECT_DIR"/old/place/pipeline_guard.py'
            write_settings(settings, {"hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": old, "timeout": 10}]}],
                "PreToolUse": [{"matcher": "Write|Edit", "hooks": [
                    {"type": "command", "command": old + " --dominion", "timeout": 10}]}],
            }})
            args = ["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"]
            code, data = run(args)
            self.assertEqual(code, 0, data)
            self.assertEqual(statuses(data), ["configured", "configured"])
            self.assertEqual(data["results"][0]["replaced_command"], old)
            self.assertEqual(data["results"][1]["replaced_command"], old + " --dominion")
            hooks = json.loads(settings.read_text(encoding="utf-8"))["hooks"]
            new = f'python3 "$CLAUDE_PROJECT_DIR"/{GUARD_PATH}'
            self.assertEqual([h["command"] for e in hooks["Stop"] for h in e["hooks"]], [new])
            self.assertEqual([h["command"] for e in hooks["PreToolUse"] for h in e["hooks"]], [new + " --dominion"])
            self.assertEqual(hooks["PreToolUse"][0]["matcher"], "Write|Edit")  # the entry is kept, only its command moves
            code, data = run(args)
            self.assertEqual(statuses(data), ["already_configured", "already_configured"])
            self.assertNotIn("replaced_command", data["results"][0])

    def test_hook_written_under_the_old_hyphenated_script_name_is_repointed(self):
        # Installs before the scripts were renamed wrote .../pipeline-guard.py; that file no longer
        # exists, so the hook must be found and repointed rather than left beside a second one.
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            old = 'python3 "$CLAUDE_PROJECT_DIR"/.claude/skills/suno-agent-band-manager/scripts/pipeline-guard.py'
            write_settings(settings, {"hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": old, "timeout": 10}]}]}})
            code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH])
            self.assertEqual(code, 0, data)
            self.assertEqual(data["results"][0]["replaced_command"], old)
            hooks = json.loads(settings.read_text(encoding="utf-8"))["hooks"]
            self.assertEqual([h["command"] for e in hooks["Stop"] for h in e["hooks"]],
                             [f'python3 "$CLAUDE_PROJECT_DIR"/{GUARD_PATH}'])

    # --- settings whose `hooks` has the wrong shape: the documented JSON error, not a traceback ---

    def test_wrongly_shaped_hooks_exit_2_and_leave_the_file_alone(self):
        shapes = {
            "hooks is null": {"hooks": None},
            "hooks is a list": {"hooks": []},
            "Stop is an object": {"hooks": {"Stop": {"hooks": []}}},
            "Stop is null": {"hooks": {"Stop": None}},
            "PreToolUse is a string": {"hooks": {"PreToolUse": "x"}},
        }
        for label, content in shapes.items():
            with self.subTest(shape=label), tempfile.TemporaryDirectory() as tmp:
                settings = project(tmp)
                write_settings(settings, content)
                before = settings.read_text(encoding="utf-8")
                code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH, "--dominion-hook"])
                self.assertEqual(code, 2, (code, data))
                self.assertEqual(statuses(data), ["error", "error"])
                self.assertIn("hooks", data["results"][0]["message"])
                self.assertEqual(settings.read_text(encoding="utf-8"), before)

    def test_odd_entries_inside_a_hook_list_are_stepped_over(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            odd = [None, "text", {"hooks": None}, {"hooks": [None, {"command": None}, {"type": "command"}]}]
            write_settings(settings, {"hooks": {"Stop": list(odd)}})
            code, data = run(["--settings-path", str(settings), "--guard-script-path", GUARD_PATH])
            self.assertEqual(code, 0, data)
            self.assertEqual(statuses(data), ["configured"])
            stop = json.loads(settings.read_text(encoding="utf-8"))["hooks"]["Stop"]
            self.assertEqual(stop[:4], odd)
            self.assertEqual(len(stop), 5)

    # --- half a hook request ---

    def test_settings_path_without_guard_path_exit_1_and_nothing_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = project(tmp)
            agents = Path(tmp) / "AGENTS.md"
            code, data = run(["--settings-path", str(settings), "--agents-md-path", str(agents)])
            self.assertEqual(code, 1, (code, data))
            self.assertEqual(statuses(data), ["error"])
            self.assertIn("--guard-script-path", data["results"][0]["message"])
            self.assertFalse(settings.exists())
            self.assertFalse(agents.exists())
            code, data = run(["--guard-script-path", GUARD_PATH, "--agents-md-path", str(agents)])
            self.assertEqual(code, 1, (code, data))
            self.assertEqual(statuses(data), ["error"])
            self.assertFalse(agents.exists())


if __name__ == "__main__":
    unittest.main()
