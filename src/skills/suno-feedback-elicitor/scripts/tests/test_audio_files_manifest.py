#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for audio_files_manifest.py.

The manifest script captures size_bytes (+ mtime) per audio file on the
canonical machine so the small, machine-readable manifest can travel in the
portable-sync archive instead of the large MP3s. These tests pin the generation
output (file count, on-disk manifest) and the exit-code contract (0 = written,
1 = audio dir not found). The verify half is tested in test_verify_audio_files.py.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT = str(Path(__file__).parent.parent / "audio_files_manifest.py")


def run(args: list[str]) -> tuple[int, dict]:
    result = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    try:
        out = json.loads(result.stdout)
    except json.JSONDecodeError:
        out = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, out


class AudioFilesManifestTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root = Path(td.name)

    def make_project(self, files: dict[str, int]) -> Path:
        root = self.root
        audio = root / "docs" / "audio"
        audio.mkdir(parents=True)
        for name, size in files.items():
            (audio / name).write_bytes(b"x" * size)
        return root

    def test_manifest_generation_and_exit_code(self):
        root = self.make_project({"Song A.mp3": 1000, "Song B.mp3": 2000})
        code, out = run([str(root)])
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["file_count"], 2)
        manifest_path = root / "docs" / "audio-files-manifest.yaml"
        self.assertTrue(manifest_path.is_file())
        data = yaml.safe_load(manifest_path.read_text())
        self.assertEqual({f["name"] for f in data["files"]}, {"Song A.mp3", "Song B.mp3"})

    def test_manifest_missing_audio_dir_exits_1(self):
        code, out = run([str(self.root)])
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["error"], "audio-dir-not-found")

    def test_manifest_skips_non_audio_files(self):
        root = self.make_project({"Song A.mp3": 1000})
        (root / "docs" / "audio" / "notes.txt").write_text("not audio")
        code, out = run([str(root)])
        self.assertEqual(code, 0)
        self.assertEqual(out["file_count"], 1)

    def test_manifest_records_band_subfolder_paths(self):
        """Per-band layout: names are paths relative to docs/audio; flat files stay bare; hidden dirs skipped."""
        root = self.root
        audio = root / "docs" / "audio"
        for rel, size in {"band-a/Song.mp3": 10, "band-b/Song.mp3": 20, "Loose.mp3": 5, ".cache/Skip.mp3": 1}.items():
            (audio / rel).parent.mkdir(parents=True, exist_ok=True)
            (audio / rel).write_bytes(b"x" * size)
        code, _ = run([str(root)])
        self.assertEqual(code, 0)
        manifest = yaml.safe_load((root / "docs" / "audio-files-manifest.yaml").read_text())
        self.assertEqual([f["name"] for f in manifest["files"]], ["Loose.mp3", "band-a/Song.mp3", "band-b/Song.mp3"])

    def test_empty_audio_dir_never_replaces_the_canonical_manifest(self):
        root = self.make_project({})
        manifest = root / "docs" / "audio-files-manifest.yaml"
        manifest.write_text("files:\n- name: Song.mp3\n  size_bytes: 1000\n", encoding="utf-8")
        before = manifest.read_text(encoding="utf-8")
        code, out = run([str(root)])
        self.assertEqual((code, out["status"], out["error"]), (1, "error", "no-audio-files"))
        self.assertEqual(manifest.read_text(encoding="utf-8"), before)

    def test_empty_audio_dir_still_prints_with_stdout(self):
        root = self.make_project({})
        result = subprocess.run([sys.executable, SCRIPT, str(root), "--stdout"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(yaml.safe_load(result.stdout)["file_count"], 0)

    def test_output_outside_the_project_root_reports_its_absolute_path(self):
        root = self.make_project({"Song.mp3": 1000})
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        outside = Path(td.name).resolve() / "saved" / "manifest.yaml"
        code, out = run([str(root), "--output", str(outside)])
        self.assertEqual((code, out["status"]), (0, "ok"), out)
        self.assertEqual(out["manifest_path"], str(outside))
        self.assertEqual(yaml.safe_load(outside.read_text(encoding="utf-8"))["file_count"], 1)


if __name__ == "__main__":
    unittest.main()
