#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for validate-path.py"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location(
    "validate_path",
    Path(__file__).parent.parent / "validate-path.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402


TEMPLATE = Path(__file__).parent.parent.parent / "assets" / "ACCESS-BOUNDARIES-template.md"


def _template_boundaries(tmp_path):
    text = TEMPLATE.read_text(encoding="utf-8").replace("{project-root}", "/proj")
    path = tmp_path / "access-boundaries.md"
    path.write_text(text)
    return mod.parse_boundaries(path)


def _cli(*argv):
    import json
    out = io.StringIO()
    code = 0
    with patch.object(sys, "argv", ["validate-path.py", *argv]), redirect_stdout(out):
        try:
            mod.main()
        except SystemExit as exc:
            code = exc.code or 0
    return code, json.loads(out.getvalue())


class ValidatePathTests(TempDirMixin, unittest.TestCase):
    def test_parse_legacy_access_boundaries(self):
        """A legacy standalone access-boundaries.md (top-level ## sections) still parses."""
        boundaries_file = self.tmp_path / "access-boundaries.md"
        boundaries_file.write_text(
            "# Access Boundaries\n\n"
            "## Read Access\n"
            "- docs/band-profiles/\n"
            "- {project-root}/_bmad/_memory/band-manager-sidecar/\n\n"
            "## Write Access\n"
            "- {project-root}/_bmad/_memory/band-manager-sidecar/\n\n"
            "## Deny Zones\n"
            "- All other directories\n"
        )

        boundaries = mod.parse_boundaries(boundaries_file)
        self.assertIn("docs/band-profiles/", boundaries["read"])
        self.assertIn("_bmad/_memory/band-manager-sidecar/", boundaries["read"])
        self.assertIn("_bmad/_memory/band-manager-sidecar/", boundaries["write"])

    def test_validate_read_allowed(self):
        boundaries = {"read": ["docs/band-profiles/"], "write": []}
        result = mod.validate_path("docs/band-profiles/midnight-orchid.yaml", "read", boundaries)
        self.assertIs(result["allowed"], True)

    def test_validate_read_denied(self):
        boundaries = {"read": ["docs/band-profiles/"], "write": []}
        result = mod.validate_path("src/secret.py", "read", boundaries)
        self.assertIs(result["allowed"], False)

    def test_validate_write_allowed(self):
        boundaries = {"read": [], "write": ["_bmad/_memory/band-manager-sidecar/"]}
        result = mod.validate_path("_bmad/_memory/band-manager-sidecar/index.md", "write", boundaries)
        self.assertIs(result["allowed"], True)

    def test_validate_write_denied(self):
        boundaries = {"read": [], "write": ["_bmad/_memory/band-manager-sidecar/"]}
        result = mod.validate_path("docs/band-profiles/test.yaml", "write", boundaries)
        self.assertIs(result["allowed"], False)

    def test_template_parses_backticked_entries(self):
        b = _template_boundaries(self.tmp_path)
        self.assertIn("docs/wip-*.md", b["write"])
        self.assertIn("{skill-root}/", b["read"])
        self.assertIn("src/", b["deny"])
        # Prose bullets are not treated as paths.
        self.assertFalse(any(" " in p for p in b["read"] + b["write"] + b["deny"]))

    def test_template_write_rules(self):
        b = _template_boundaries(self.tmp_path)
        ok = lambda p, op: mod.validate_path(p, op, b, project_root="/proj", skill_root="/proj/src/skills/mac")["allowed"]
        self.assertTrue(ok("/proj/_bmad/memory/suno-agent-band-manager/memory/work/current.md", "write"))
        self.assertFalse(ok("/proj/_bmad/_memory/band-manager-sidecar/MEMORY.md", "write"))  # the legacy store
        self.assertTrue(ok("docs/wip-new-song-fragments.md", "write"))
        self.assertTrue(ok("docs/voice-context-sam.md", "write"))
        self.assertFalse(ok("docs/band-profiles/x.yaml", "write"))      # via the profile skill only
        self.assertFalse(ok("src/skills/mac/references/creed.md", "write"))  # deny zone
        self.assertFalse(ok("/proj/_bmad/config.yaml", "write"))
        self.assertFalse(ok("README.md", "write"))

    def test_template_bundle_carve_out_allows_reads(self):
        b = _template_boundaries(self.tmp_path)
        ok = lambda p, op: mod.validate_path(p, op, b, project_root="/proj", skill_root="/proj/src/skills/mac")["allowed"]
        # src/ is a deny zone for writes, but the skill's own bundle is readable.
        self.assertTrue(ok("src/skills/mac/references/create-song.md", "read"))
        self.assertFalse(ok("src/other/thing.py", "read"))
        self.assertTrue(ok("docs/band-profiles/x.yaml", "read"))

    # --- v7: the Dominion inside the sanctum's CREED.md ---

    def test_parse_creed_dominion_subsections(self):
        root, sanctum = self.make_v7_project()
        b = mod.parse_boundaries(sanctum / "CREED.md")
        self.assertEqual(b["read"], ["_bmad/memory/suno-agent-band-manager/", "docs/band-profiles/"])
        self.assertEqual(b["write"], ["_bmad/memory/suno-agent-band-manager/", "docs/wip-*.md"])
        self.assertEqual(b["deny"], ["src/"])
        # Write Rule prose and the sections outside the Dominion are not rules.
        everything = b["read"] + b["write"] + b["deny"]
        self.assertNotIn("docs/not-a-rule.md", everything)
        self.assertNotIn("docs/also-not-a-rule.md", everything)

    def test_creed_dominion_decisions(self):
        root, sanctum = self.make_v7_project()
        b = mod.parse_boundaries(sanctum / "CREED.md")
        ok = lambda p, op: mod.validate_path(p, op, b, project_root=str(root))["allowed"]
        self.assertTrue(ok(str(sanctum / "memory" / "work" / "current.md"), "write"))
        self.assertTrue(ok("docs/wip-dock.md", "write"))
        self.assertTrue(ok("docs/band-profiles/x.yaml", "read"))
        self.assertFalse(ok("docs/band-profiles/x.yaml", "write"))
        self.assertFalse(ok("src/skills/x.py", "write"))
        self.assertFalse(ok("docs/not-a-rule.md", "write"))

    def test_scaffolded_creed_carries_the_template_dominion(self):
        """init-sanctum renders the access-boundaries template into CREED.md; it parses
        the same as the template itself."""
        init_spec = spec_from_file_location("init_sanctum", Path(__file__).parent.parent / "init-sanctum.py")
        init = module_from_spec(init_spec)
        init_spec.loader.exec_module(init)
        init.scaffold(self.tmp_path, Path(__file__).parent.parent.parent)
        creed = self.tmp_path / "_bmad" / "memory" / "suno-agent-band-manager" / "CREED.md"
        from_creed = mod.parse_boundaries(creed)
        template_text = TEMPLATE.read_text(encoding="utf-8").replace("{project-root}", str(self.tmp_path))
        legacy = self.tmp_path / "access-boundaries.md"
        legacy.write_text(template_text, encoding="utf-8")
        from_template = mod.parse_boundaries(legacy)
        self.assertEqual(from_creed, from_template)
        self.assertIn("docs/wip-*.md", from_creed["write"])

    def test_cli_defaults_to_the_sanctum_creed(self):
        root, _ = self.make_v7_project()
        code, out = _cli("docs/wip-dock.md", "write", "--project-root", str(root))
        self.assertEqual(code, 0)
        self.assertIs(out["allowed"], True)
        code, out = _cli("src/x.py", "write", "--project-root", str(root))
        self.assertEqual(code, 1)
        self.assertEqual(out["reason"], "deny zone")

    def test_cli_explicit_boundaries_and_missing_file(self):
        root, sanctum = self.make_v7_project()
        code, out = _cli("docs/band-profiles/a.yaml", "read",
                         "--boundaries", str(sanctum / "CREED.md"), "--project-root", str(root))
        self.assertEqual(code, 0)
        self.assertIs(out["allowed"], True)
        code, out = _cli("docs/a.md", "read", "--project-root", str(root / "nowhere"))
        self.assertEqual(code, 1)
        self.assertIs(out["error"], True)
        self.assertIn("CREED.md", out["message"])

    def test_labeled_bullet_names_its_path_in_parentheses(self):
        creed = self.tmp_path / "CREED.md"
        creed.write_text(
            "# Creed\n\n## Dominion (Access Boundaries)\n\n### Write Access\n\n"
            "- WIP files (`docs/wip-*.md`) when capturing creative fragments\n"
            "- Band profile writes happen via the `suno-band-profile-manager` skill, not directly\n"
            "  - nested note (`docs/nested-not-a-rule.md`) stays prose\n"
            "- Plain prose (e.g. `docs/inline-not-a-rule.md`) mid-sentence\n",
            encoding="utf-8")
        b = mod.parse_boundaries(creed)
        self.assertEqual(b["write"], ["docs/wip-*.md"])


if __name__ == "__main__":
    unittest.main()
