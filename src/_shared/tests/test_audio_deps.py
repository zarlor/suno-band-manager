#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for audio_deps: the missing-dependency exit (JSON on stdout, exit code 2).

tempo_source reads exit code 2 as "Beat This! is not installed" and the audio
routes relay the JSON's install command, so both the code and the shape are pinned.
"""
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import audio_deps  # noqa: E402

ABSENT = "no_such_module_xyz"


def run_check(check, *args, **kwargs):
    """(exit code, or None when the check returned; parsed stdout JSON, or None when it printed nothing)."""
    out = io.StringIO()
    code = None
    with redirect_stdout(out):
        try:
            check(*args, **kwargs)
        except SystemExit as exc:
            code = exc.code
    return code, (json.loads(out.getvalue()) if out.getvalue() else None)


class TestRequireModules(unittest.TestCase):
    def test_missing_module_exits_2_with_json_on_stdout(self):
        code, report = run_check(audio_deps.require_modules, [ABSENT], "pip install it")
        self.assertEqual(code, 2)
        self.assertEqual(report["script"], "audio-dependency-check")
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["error"], "missing_dependencies")
        self.assertEqual(report["missing"], [ABSENT])
        self.assertEqual(report["install_command"], "pip install it")
        self.assertIn(ABSENT, report["message"])
        self.assertIn("pip install it", report["message"])

    def test_only_the_missing_modules_are_listed(self):
        code, report = run_check(audio_deps.require_modules, ["json", ABSENT, "os", "also_absent_xyz"], "cmd")
        self.assertEqual(code, 2)
        self.assertEqual(report["missing"], [ABSENT, "also_absent_xyz"])

    def test_purpose_names_what_needs_the_modules(self):
        _, report = run_check(audio_deps.require_modules, [ABSENT], "cmd", "Beat This! beat tracking")
        self.assertTrue(report["message"].startswith("Beat This! beat tracking requires: "))

    def test_present_modules_return_without_exiting_or_printing(self):
        self.assertEqual(run_check(audio_deps.require_modules, ["json", "os"], "cmd"), (None, None))
        self.assertIsNone(audio_deps.require_modules(["json"], "cmd"))

    def test_no_modules_asked_for_returns(self):
        self.assertEqual(run_check(audio_deps.require_modules, [], "cmd"), (None, None))


class TestRequireAudioDeps(unittest.TestCase):
    def test_missing_extra_exits_2_and_the_install_command_names_every_dependency(self):
        code, report = run_check(audio_deps.require_audio_deps, extra=(ABSENT,))
        self.assertEqual(code, 2)
        self.assertEqual(report["error"], "missing_dependencies")
        self.assertIn(ABSENT, report["missing"])
        for name in ("librosa", "numpy", ABSENT):
            self.assertIn(name, report["install_command"])
        self.assertIn("uv run", report["install_command"])

    def test_checks_librosa_and_numpy_plus_the_extras(self):
        with mock.patch.object(audio_deps, "require_modules") as check:
            audio_deps.require_audio_deps(extra=("pyloudnorm",))
        self.assertEqual(tuple(check.call_args.args[0]), ("librosa", "numpy", "pyloudnorm"))

    def test_missing_librosa_is_reported_by_name(self):
        import importlib.util
        real = importlib.util.find_spec
        with mock.patch("importlib.util.find_spec", lambda name, *a: None if name == "librosa" else real(name, *a)):
            code, report = run_check(audio_deps.require_audio_deps)
        self.assertEqual(code, 2)
        self.assertIn("librosa", report["missing"])


if __name__ == "__main__":
    unittest.main()
