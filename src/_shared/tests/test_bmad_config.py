"""bmad_config: defaults without BMad's resolver, answers with it, errors when it fails."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bmad_config  # noqa: E402
from fake_resolver import install_resolver  # noqa: E402


class ResolveTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def test_no_bmad_folder_gives_defaults(self):
        self.assertEqual(bmad_config.module_config(self.root), {})

    def test_bmad_folder_without_resolver_gives_defaults(self):
        # A standalone install: Mac's memory creates _bmad/ but BMad isn't set up.
        (self.root / "_bmad" / "memory" / "suno-agent-band-manager").mkdir(parents=True)
        self.assertEqual(bmad_config.module_config(self.root), {})

    def test_resolver_answers_are_returned_with_project_root_filled(self):
        install_resolver(self.root)
        (self.root / "_bmad" / "config.toml").write_text(
            '[modules.suno]\nband_profiles_folder = "{project-root}/bands"\n'
        )
        cfg = bmad_config.module_config(self.root)
        self.assertEqual(cfg.get("band_profiles_folder"), f"{self.root}/bands")

    def test_failing_resolver_raises(self):
        scripts = self.root / "_bmad" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "resolve_config.py").write_text("import sys\nsys.exit('resolver broke')\n")
        with self.assertRaises(bmad_config.ConfigError) as ctx:
            bmad_config.module_config(self.root)
        self.assertIn("resolver broke", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
