#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for metatag_sections.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "metatag_sections.py")

CATALOG = """# Catalog

Intro text.

## Alpha Tags

alpha body

### Ending Control — Recipe

recipe body

```
## Not a heading (in a fence)
```

### Ending Control — Practice

practice body

## Beta Tags

beta body
"""


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


class TestMetatagSections(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.file = Path(tmp.name) / "catalog.md"
        self.file.write_text(CATALOG, encoding="utf-8")

    def test_list_headings_with_spans(self):
        result = run("--list", "--file", str(self.file))
        self.assertEqual(result.returncode, 0)
        heads = json.loads(result.stdout)["headings"]
        self.assertEqual([h["heading"] for h in heads],
                         ["Catalog", "Alpha Tags", "Ending Control — Recipe", "Ending Control — Practice", "Beta Tags"])
        alpha = heads[1]
        self.assertEqual(alpha["level"], 2)
        self.assertEqual(alpha["end_line"], heads[4]["start_line"] - 1)

    def test_section_includes_subsections(self):
        out = run("--section", "alpha tags", "--file", str(self.file)).stdout
        self.assertTrue(out.startswith("## Alpha Tags"))
        self.assertIn("recipe body", out)
        self.assertIn("practice body", out)
        self.assertNotIn("beta body", out)

    def test_prefix_matches_every_section(self):
        out = run("--section", "Ending Control", "--file", str(self.file)).stdout
        self.assertIn("recipe body", out)
        self.assertIn("practice body", out)
        self.assertNotIn("alpha body", out)

    def test_nested_match_not_printed_twice(self):
        out = run("--section", "Alpha Tags", "--section", "Ending Control — Recipe", "--file", str(self.file)).stdout
        self.assertEqual(out.count("recipe body"), 1)

    def test_unmatched_name_exits_2(self):
        result = run("--section", "Gamma", "--file", str(self.file))
        self.assertEqual(result.returncode, 2)
        self.assertIn("'Gamma'", result.stderr)
        self.assertIn("Alpha Tags", result.stderr)

    def test_missing_file_exits_2(self):
        self.assertEqual(run("--list", "--file", "/nonexistent/catalog.md").returncode, 2)

    def test_mode_required(self):
        self.assertEqual(run("--file", str(self.file)).returncode, 2)

    def test_empty_name_matches_nothing(self):
        for name in ("", "   ", "#", "## "):
            with self.subTest(name=name):
                result = run("--section", name, "--file", str(self.file))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("no heading matches", result.stderr)

    def test_names_from_a_routing_table_resolve(self):
        # A catalog's routing table hands its Load names to --section: a full
        # heading, a heading prefix, any case, with or without the leading #s.
        for name, body in (("Alpha Tags", "alpha body"), ("ending control", "recipe body"),
                           ("## Beta Tags", "beta body"), ("Ending Control — Practice", "practice body")):
            with self.subTest(name=name):
                result = run("--section", name, "--file", str(self.file))
                self.assertEqual(result.returncode, 0)
                self.assertIn(body, result.stdout)

    def test_non_ascii_section_prints_under_an_ascii_locale(self):
        self.file.write_text(CATALOG + "\n## Gamma — Tags\n\ngamma → body ⚠\n", encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("LC_", "LANG", "PYTHON"))}
        env.update(LC_ALL="C", PYTHONUTF8="0", PYTHONCOERCECLOCALE="0")
        result = subprocess.run([sys.executable, SCRIPT, "--section", "Gamma", "--file", str(self.file)],
                                capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("gamma → body ⚠", result.stdout.decode("utf-8"))

    def test_default_file_is_the_skills_catalog(self):
        result = run("--list")
        self.assertEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertTrue(report["file"].endswith("references/metatag-reference.md"))
        self.assertTrue(report["headings"])


if __name__ == "__main__":
    unittest.main()
