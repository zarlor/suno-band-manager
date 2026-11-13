#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for strategy_sections.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "strategy_sections.py")

CATALOG = """# Catalog

Intro text.

## Alpha Notes

alpha body

### Slider Guidelines — Recipe

recipe body

```
## Not a heading (in a fence)
```

### Slider Guidelines — Practice

practice body

## Beta Notes

beta body
"""


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


class TestStrategySections(unittest.TestCase):
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
                         ["Catalog", "Alpha Notes", "Slider Guidelines — Recipe", "Slider Guidelines — Practice", "Beta Notes"])
        alpha = heads[1]
        self.assertEqual(alpha["level"], 2)
        self.assertEqual(alpha["end_line"], heads[4]["start_line"] - 1)

    def test_section_includes_subsections(self):
        out = run("--section", "alpha notes", "--file", str(self.file)).stdout
        self.assertTrue(out.startswith("## Alpha Notes"))
        self.assertIn("recipe body", out)
        self.assertIn("practice body", out)
        self.assertNotIn("beta body", out)

    def test_prefix_matches_every_section(self):
        out = run("--section", "Slider Guidelines", "--file", str(self.file)).stdout
        self.assertIn("recipe body", out)
        self.assertIn("practice body", out)
        self.assertNotIn("alpha body", out)

    def test_nested_match_not_printed_twice(self):
        out = run("--section", "Alpha Notes", "--section", "Slider Guidelines — Recipe", "--file", str(self.file)).stdout
        self.assertEqual(out.count("recipe body"), 1)

    def test_unmatched_name_exits_2(self):
        result = run("--section", "Gamma", "--file", str(self.file))
        self.assertEqual(result.returncode, 2)
        self.assertIn("'Gamma'", result.stderr)
        self.assertIn("Alpha Notes", result.stderr)

    def test_missing_file_exits_2(self):
        self.assertEqual(run("--list", "--file", "/nonexistent/catalog.md").returncode, 2)

    def test_mode_required(self):
        self.assertEqual(run("--file", str(self.file)).returncode, 2)


    def test_non_ascii_sections_print_as_utf8_whatever_the_stream_encoding(self):
        result = subprocess.run([sys.executable, SCRIPT, "--section", "Slider Guidelines", "--file", str(self.file)],
                                capture_output=True, env={**os.environ, "PYTHONIOENCODING": "ascii"})
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertIn("### Slider Guidelines \u2014 Recipe", result.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
