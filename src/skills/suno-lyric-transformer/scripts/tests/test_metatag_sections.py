#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for metatag-sections.py"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "metatag-sections.py")
REAL = Path(__file__).parent.parent.parent / "references" / "metatag-reference.md"

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

    def test_every_routing_name_resolves_in_the_real_catalog(self):
        # The catalog's routing table hands its Load names to --section; each must match.
        result = run("--section", "How to Load This File", "--file", str(REAL))
        self.assertEqual(result.returncode, 0)
        rows = [line for line in result.stdout.splitlines()
                if line.startswith("| ") and not line.startswith(("| When", "|---"))]
        names = [n.strip() for row in rows for n in row.split("|")[2].split("·")]
        self.assertGreater(len(names), 20)
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(run("--section", name, "--file", str(REAL)).returncode, 0)


if __name__ == "__main__":
    unittest.main()
