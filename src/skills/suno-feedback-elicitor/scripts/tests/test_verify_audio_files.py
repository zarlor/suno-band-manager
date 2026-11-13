#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tests for verify_audio_files.py.

verify_audio_files.py is the receiving-machine half of the multi-machine
audio-drift pair: it compares local audio files against a canonical
audio-files-manifest.yaml and classifies each as matched / missing /
size_mismatch / extra. These tests round-trip with the manifest generator and
pin the three mismatch classes, the size-tolerance behavior, and the exit-code
contract (0 = clean, 1 = mismatches, 2 = error).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
MANIFEST_SCRIPT = str(SCRIPTS / "audio_files_manifest.py")
VERIFY_SCRIPT = str(SCRIPTS / "verify_audio_files.py")


def run(script: str, args: list[str]) -> tuple[int, dict]:
    result = subprocess.run([sys.executable, script, *args], capture_output=True, text=True)
    try:
        out = json.loads(result.stdout)
    except json.JSONDecodeError:
        out = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, out


class VerifyAudioFilesTest(unittest.TestCase):
    def make_tempdir(self) -> Path:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return Path(td.name)

    def make_project(self, files: dict[str, int]) -> Path:
        root = self.make_tempdir()
        audio = root / "docs" / "audio"
        audio.mkdir(parents=True)
        for name, size in files.items():
            (audio / name).parent.mkdir(parents=True, exist_ok=True)
            (audio / name).write_bytes(b"x" * size)
        return root

    def test_verify_clean_round_trip_exits_0(self):
        root = self.make_project({"Song A.mp3": 1000, "Song B.mp3": 2000})
        run(MANIFEST_SCRIPT, [str(root)])
        code, out = run(VERIFY_SCRIPT, [str(root)])
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["summary"]["missing"], 0)
        self.assertEqual(out["summary"]["size_mismatch"], 0)
        self.assertEqual(out["summary"]["extra"], 0)

    def test_verify_detects_missing_and_extra_and_mismatch(self):
        root = self.make_project({"Song A.mp3": 1000, "Song B.mp3": 2000})
        run(MANIFEST_SCRIPT, [str(root)])
        audio = root / "docs" / "audio"
        (audio / "Song B.mp3").unlink()              # missing
        (audio / "Song A.mp3").write_bytes(b"x" * 50000)  # size_mismatch
        (audio / "Song C.mp3").write_bytes(b"x" * 3000)   # extra
        code, out = run(VERIFY_SCRIPT, [str(root)])
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "mismatch")
        self.assertEqual(out["summary"]["missing"], 1)
        self.assertEqual(out["summary"]["size_mismatch"], 1)
        self.assertEqual(out["summary"]["extra"], 1)

    def test_verify_missing_manifest_exits_2(self):
        root = self.make_project({"Song A.mp3": 1000})
        code, out = run(VERIFY_SCRIPT, [str(root)])
        self.assertEqual(code, 2)
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["error"], "manifest-not-found")

    def test_verify_size_tolerance_absorbs_id3_variance(self):
        root = self.make_project({"Song A.mp3": 100000})
        run(MANIFEST_SCRIPT, [str(root)])
        (root / "docs" / "audio" / "Song A.mp3").write_bytes(b"x" * 100512)  # +512, within 1024
        code, out = run(VERIFY_SCRIPT, [str(root)])
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["size_mismatch"], 0)

    def test_verify_filename_variant_matches(self):
        """A -v2 variant of the canonical name still matches by normalized identity."""
        root = self.make_project({"Song A.mp3": 100000})
        run(MANIFEST_SCRIPT, [str(root)])
        audio = root / "docs" / "audio"
        (audio / "Song A.mp3").rename(audio / "Song A-v2.mp3")
        code, out = run(VERIFY_SCRIPT, [str(root)])
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["matched"], 1)

    def test_verify_band_folders_round_trip(self):
        """Same title in two band folders: both tracked separately and both match."""
        root = self.make_project({"band-a/Song.mp3": 100000, "band-b/Song.mp3": 200000})
        run(MANIFEST_SCRIPT, [str(root)])
        code, out = run(VERIFY_SCRIPT, [str(root)])
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["matched"], 2)

    def test_verify_same_title_in_other_band_does_not_cross_match(self):
        """A band folder is part of the identity: band-b/Song never satisfies band-a/Song."""
        root = self.make_project({"band-a/Song.mp3": 100000})
        run(MANIFEST_SCRIPT, [str(root)])
        audio = root / "docs" / "audio"
        (audio / "band-b").mkdir()
        (audio / "band-a" / "Song.mp3").rename(audio / "band-b" / "Song.mp3")
        code, out = run(VERIFY_SCRIPT, [str(root)])
        self.assertEqual(code, 1)
        self.assertEqual([m["name"] for m in out["missing"]], ["band-a/Song.mp3"])
        self.assertEqual([e["name"] for e in out["extra"]], ["band-b/Song.mp3"])

    def test_verify_legacy_flat_manifest_matches_band_layout(self):
        """A manifest generated before the per-band move still verifies after it."""
        root = self.make_project({"Song.mp3": 100000})
        run(MANIFEST_SCRIPT, [str(root)])
        audio = root / "docs" / "audio"
        (audio / "band-a").mkdir()
        (audio / "Song.mp3").rename(audio / "band-a" / "Song.mp3")
        code, out = run(VERIFY_SCRIPT, [str(root)])
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["matched"], 1)

    def test_verify_manifest_outside_project_root(self):
        """--manifest may point outside the project (e.g. a saved copy) without crashing."""
        root = self.make_project({"Song.mp3": 100000})
        run(MANIFEST_SCRIPT, [str(root)])
        outside = self.make_tempdir() / "saved-manifest.yaml"
        outside.write_text((root / "docs" / "audio-files-manifest.yaml").read_text())
        code, out = run(VERIFY_SCRIPT, [str(root), "--manifest", str(outside)])
        self.assertEqual(code, 0)
        self.assertEqual(out["manifest_path"], str(outside))

    def test_verify_legacy_flat_manifest_root_variant_does_not_block_band_file(self):
        """Flat manifest with Song.mp3 + Song (1).mp3; after the move only Song.mp3 goes
        into a band folder. The root-level variant must not shadow the moved file."""
        root = self.make_project({"Song.mp3": 100000, "Song (1).mp3": 150000})
        run(MANIFEST_SCRIPT, [str(root)])
        audio = root / "docs" / "audio"
        (audio / "band-a").mkdir()
        (audio / "Song.mp3").rename(audio / "band-a" / "Song.mp3")
        code, out = run(VERIFY_SCRIPT, [str(root)])
        self.assertEqual(code, 0, out)
        self.assertEqual(out["summary"]["matched"], 2)

    def test_verify_malformed_manifest_exits_2_with_a_reason(self):
        """Exit 1 means mismatches, so a manifest that can't be read must not exit 1 via a traceback."""
        root = self.make_project({"Song.mp3": 1000})
        manifest = root / "docs" / "audio-files-manifest.yaml"
        for body in ("", "- just\n- a list\n", "files: [unclosed\n", "files:\n- size_bytes: 1000\n",
                     "files:\n- Song.mp3\n", "files: Song.mp3\n"):
            manifest.write_text(body, encoding="utf-8")
            code, out = run(VERIFY_SCRIPT, [str(root)])
            self.assertEqual((code, out.get("status"), out.get("error")), (2, "error", "manifest-malformed"), body)

    def test_verify_exact_name_is_not_claimed_by_a_sibling_entry(self):
        """Manifest lists Foo.mp3 and Foo-v2.mp3; only Foo-v2.mp3 is here. Foo is the missing one."""
        root = self.make_project({"Foo-v2.mp3": 150000})
        manifest = root / "docs" / "audio-files-manifest.yaml"
        entries = {"Foo.mp3": 100000, "Foo-v2.mp3": 150000}
        for order in (["Foo.mp3", "Foo-v2.mp3"], ["Foo-v2.mp3", "Foo.mp3"]):  # whichever entry is read first
            manifest.write_text("files:\n" + "".join(
                f"- name: {name}\n  size_bytes: {entries[name]}\n" for name in order), encoding="utf-8")
            code, out = run(VERIFY_SCRIPT, [str(root)])
            self.assertEqual(code, 1, order)
            self.assertEqual([m["name"] for m in out["missing"]], ["Foo.mp3"], order)
            self.assertEqual(out["size_mismatch"], [], order)
            self.assertEqual(out["summary"]["matched"], 1, order)

    def test_verify_exact_name_in_a_band_folder_is_kept_for_its_flat_manifest_entry(self):
        """Legacy flat manifest, per-band local layout: the sibling entry still can't take the file."""
        root = self.make_project({"band-a/Foo-v2.mp3": 150000})
        manifest = root / "docs" / "audio-files-manifest.yaml"
        manifest.write_text("files:\n- name: Foo.mp3\n  size_bytes: 100000\n"
                            "- name: Foo-v2.mp3\n  size_bytes: 150000\n", encoding="utf-8")
        code, out = run(VERIFY_SCRIPT, [str(root)])
        self.assertEqual(code, 1)
        self.assertEqual([m["name"] for m in out["missing"]], ["Foo.mp3"])
        self.assertEqual(out["summary"]["matched"], 1)

    def test_verify_playlist_context_keeps_each_bands_position(self):
        """Two bands list the same filename: a mismatch carries its own band's playlist position."""
        root = self.make_project({"band-a/Night Shift.mp3": 100000, "band-b/Night Shift.mp3": 200000})
        run(MANIFEST_SCRIPT, [str(root)])
        docs = root / "docs"
        (docs / "band-a-playlist.yaml").write_text(
            'album: "Band A"\naudio_dir: "docs/audio/band-a"\ntracks:\n'
            '  - {name: "Opener", file: "Other.mp3"}\n  - {name: "Night Shift", file: "Night Shift.mp3"}\n',
            encoding="utf-8")
        (docs / "band-b-playlist.yaml").write_text(
            'album: "Band B"\ntracks:\n  - {name: "Night Shift", file: "Night Shift.mp3"}\n', encoding="utf-8")
        for band in ("band-a", "band-b"):
            (docs / "audio" / band / "Night Shift.mp3").unlink()
        code, out = run(VERIFY_SCRIPT, [str(root), "--playlist-context"])
        self.assertEqual(code, 1)
        ctx = {m["name"]: m["playlist_context"] for m in out["missing"]}
        self.assertEqual((ctx["band-a/Night Shift.mp3"]["band"], ctx["band-a/Night Shift.mp3"]["position"]),
                         ("Band A", 2))
        self.assertEqual((ctx["band-b/Night Shift.mp3"]["band"], ctx["band-b/Night Shift.mp3"]["position"]),
                         ("Band B", 1))

    def test_verify_playlist_context_for_a_flat_name_only_when_one_band_lists_it(self):
        root = self.make_project({"Solo.mp3": 100000, "Shared.mp3": 100000})
        run(MANIFEST_SCRIPT, [str(root)])
        docs = root / "docs"
        (docs / "band-a-playlist.yaml").write_text(
            'album: "Band A"\ntracks:\n  - {name: "Solo", file: "Solo.mp3"}\n'
            '  - {name: "Shared", file: "Shared.mp3"}\n', encoding="utf-8")
        (docs / "band-b-playlist.yaml").write_text(
            'album: "Band B"\ntracks:\n  - {name: "Shared", file: "Shared.mp3"}\n', encoding="utf-8")
        for name in ("Solo.mp3", "Shared.mp3"):
            (docs / "audio" / name).unlink()
        code, out = run(VERIFY_SCRIPT, [str(root), "--playlist-context"])
        missing = {m["name"]: m for m in out["missing"]}
        self.assertEqual(missing["Solo.mp3"]["playlist_context"]["band"], "Band A")
        self.assertNotIn("playlist_context", missing["Shared.mp3"])


if __name__ == "__main__":
    unittest.main()
