#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for validate_path.py

The boundaries the tests judge against are rendered from the synthetic skill
(helpers.make_skill), never from the shipped ACCESS-BOUNDARIES template, so no
test depends on what that template happens to list.
"""

import contextlib
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
    Path(__file__).parent.parent / "validate_path.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin, load_script, make_skill  # noqa: E402

seed = load_script("_sanctum_seed", "_sanctum_seed.py")


def _rendered_boundaries(skill, project_root):
    """The synthetic access-boundaries template, rendered as the seed renders it for a project."""
    variables = seed.template_variables(Path(project_root), {"values": {}})
    return seed.render_access_boundaries(skill / "assets", variables)


def _template_boundaries(tmp_path):
    """Parsed boundaries of the synthetic template for a project at /proj (default folders)."""
    skill = make_skill(tmp_path, name="boundaries-skill")
    path = tmp_path / "access-boundaries.md"
    path.write_text(_rendered_boundaries(skill, "/proj"), encoding="utf-8")
    return mod.parse_boundaries(path)


def _cli(*argv):
    import json
    out = io.StringIO()
    code = 0
    with patch.object(sys, "argv", ["validate_path.py", *argv]), redirect_stdout(out):
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
        , encoding="utf-8")

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
        # The folder placeholders were rendered: no entry is a bare `{...}/` that would match anything.
        self.assertIn("docs/songbook/", b["write"])
        self.assertIn("docs/band-profiles/", b["read"])
        self.assertFalse(any(p.startswith("{") and p != "{skill-root}/" for p in b["read"] + b["write"] + b["deny"]))
        # Prose bullets are not treated as paths.
        self.assertFalse(any(" " in p for p in b["read"] + b["write"] + b["deny"]))

    def test_template_write_rules(self):
        b = _template_boundaries(self.tmp_path)
        ok = lambda p, op: mod.validate_path(p, op, b, project_root="/proj", skill_root="/proj/src/skills/mac")["allowed"]
        self.assertTrue(ok("/proj/_bmad/memory/suno-agent-band-manager/memory/work/current.md", "write"))
        self.assertFalse(ok("/proj/_bmad/_memory/band-manager-sidecar/MEMORY.md", "write"))  # the legacy store
        self.assertTrue(ok("docs/wip-new-song-fragments.md", "write"))
        self.assertTrue(ok("docs/voice-context-sam.md", "write"))
        self.assertTrue(ok("docs/songbook/band/song.md", "write"))
        self.assertFalse(ok("docs/band-profiles/x.yaml", "write"))      # via the profile skill only
        self.assertFalse(ok("src/skills/mac/assets/creed.md", "write"))  # deny zone
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
        the same as the rendered template itself."""
        init = load_script("init_sanctum", "init_sanctum.py")
        skill = make_skill(self.tmp_path)
        project = self.tmp_path / "project"
        project.mkdir()
        self.assertEqual(init.scaffold(project, skill)["status"], "created")
        creed = project / "_bmad" / "memory" / "suno-agent-band-manager" / "CREED.md"
        from_creed = mod.parse_boundaries(creed)
        legacy = self.tmp_path / "access-boundaries.md"
        legacy.write_text(_rendered_boundaries(skill, project), encoding="utf-8")
        from_template = mod.parse_boundaries(legacy)
        self.assertEqual(from_creed, from_template)
        self.assertIn("docs/wip-*.md", from_creed["write"])

    def test_a_moved_songbook_is_writable_and_the_old_place_is_not(self):
        """The Dominion rendered for a project whose songbook and profiles were moved in
        `bmad setup suno` allows the configured folders, not docs/."""
        skill = make_skill(self.tmp_path)
        project = self.tmp_path / "project"
        outside = self.tmp_path / "shared" / "bands"
        variables = seed.template_variables(project, {"values": {
            "songbook_folder": "{project-root}/music/book", "band_profiles_folder": str(outside)}})
        path = self.tmp_path / "access-boundaries.md"
        path.write_text(seed.render_access_boundaries(skill / "assets", variables), encoding="utf-8")
        b = mod.parse_boundaries(path)
        ok = lambda p, op: mod.validate_path(p, op, b, project_root=str(project))["allowed"]
        self.assertTrue(ok("music/book/band/song.md", "write"))
        self.assertTrue(ok(str(project / "music" / "book" / "band" / "song.md"), "write"))
        self.assertFalse(ok("docs/songbook/band/song.md", "write"))
        self.assertTrue(ok(str(outside / "tidewater.yaml"), "read"))
        self.assertFalse(ok(str(outside / "tidewater.yaml"), "write"))
        self.assertFalse(ok(str(outside.parent / "other.yaml"), "read"))

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


    # --- the access boundary cannot be walked around ---

    def test_dot_dot_segments_are_judged_as_the_file_they_name(self):
        """`docs/songbook/../../src/x.py` is `src/x.py`: a Deny Zone, not a songbook write."""
        b = _template_boundaries(self.tmp_path)
        check = lambda p, op: mod.validate_path(p, op, b, project_root="/proj", skill_root="/proj/src/skills/mac")
        for sneaky in (
            "docs/songbook/../../src/x.py",
            "/proj/docs/songbook/../../src/x.py",
            "{project-root}/docs/songbook/../../src/x.py",
            "docs\\songbook\\..\\..\\src\\x.py",
        ):
            with self.subTest(path=sneaky):
                result = check(sneaky, "write")
                self.assertIs(result["allowed"], False)
                self.assertEqual(result["reason"], "deny zone")
                self.assertEqual(result["matched_rule"], "src/")
        # Climbing out of the project is not a songbook write either.
        self.assertIs(check("docs/songbook/../../../etc/passwd", "write")["allowed"], False)
        self.assertIs(check("docs/songbook/../../README.md", "read")["allowed"], False)
        # A path that stays inside an allowed place is still allowed.
        self.assertIs(check("docs/songbook/../wip-new-song-fragments.md", "write")["allowed"], True)
        self.assertIs(check("docs/./songbook/band/song.md", "write")["allowed"], True)

    def test_cli_refuses_a_dot_dot_path_into_a_deny_zone(self):
        root, _ = self.make_v7_project()
        code, out = _cli("docs/band-profiles/../../src/x.py", "read", "--project-root", str(root))
        self.assertEqual(code, 1)
        self.assertIs(out["allowed"], False)
        code, out = _cli("docs/../src/wip-x.md", "write", "--project-root", str(root))
        self.assertEqual(code, 1)
        self.assertEqual(out["reason"], "deny zone")

    def test_unresolved_skill_root_entry_matches_nothing(self):
        """Without a skill root the `{skill-root}/` entry is not an empty pattern
        that every absolute path starts with."""
        b = _template_boundaries(self.tmp_path)
        self.assertIn("{skill-root}/", b["read"])
        for outside in ("/etc/passwd", "/proj/src/other/thing.py", "/home/someone/.ssh/id_rsa"):
            with self.subTest(path=outside):
                result = mod.validate_path(outside, "read", b, project_root="/proj")
                self.assertIs(result["allowed"], False)
                self.assertNotEqual(result.get("matched_rule"), "{skill-root}/")
        # The listed places still read, and the bundle reads once the root is known.
        self.assertIs(mod.validate_path("docs/band-profiles/x.yaml", "read", b, project_root="/proj")["allowed"], True)
        self.assertIs(mod.validate_path("/opt/skills/mac/SKILL.md", "read", b, project_root="/proj",
                                        skill_root="/opt/skills/mac")["allowed"], True)
        # A path written with the placeholder cannot be judged without the root.
        result = mod.validate_path("{skill-root}/SKILL.md", "read", b, project_root="/proj")
        self.assertIs(result["allowed"], False)
        self.assertIn("skill root", result["reason"])

    def test_empty_pattern_matches_nothing(self):
        self.assertIs(mod.validate_path("/etc/passwd", "read", {"read": [""], "write": []})["allowed"], False)

    def test_cli_without_skill_root_refuses_an_outside_read(self):
        root, sanctum = self.make_v7_project()
        creed = sanctum / "CREED.md"
        creed.write_text(creed.read_text(encoding="utf-8").replace(
            "### Write Access", "- `{skill-root}/` — the bundle\n\n### Write Access"), encoding="utf-8")
        code, out = _cli("/etc/passwd", "read", "--project-root", str(root))
        self.assertEqual(code, 1)
        self.assertIs(out["allowed"], False)

    def test_cli_absolute_in_project_path_without_project_root(self):
        """The project root defaults to the current directory, so an absolute
        path inside it is judged by its project-relative form."""
        root, sanctum = self.make_v7_project()
        root = root.resolve()
        with contextlib.chdir(root):
            code, out = _cli(str(root / "docs" / "wip-dock.md"), "write")
            self.assertEqual(code, 0)
            self.assertIs(out["allowed"], True)
            code, out = _cli(str(root / "docs" / "wip-dock.md"), "write", "--boundaries", str(sanctum / "CREED.md"))
            self.assertEqual(code, 0)
            code, out = _cli(str(root / "src" / "x.py"), "write")
            self.assertEqual(code, 1)
            self.assertEqual(out["reason"], "deny zone")


if __name__ == "__main__":
    unittest.main()
