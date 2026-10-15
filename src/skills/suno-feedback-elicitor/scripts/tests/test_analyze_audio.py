#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Exit-code contract test for analyze-audio.py.

analyze-audio.py is one of the single-song intake scripts Step 2 invokes. A full
analysis test needs real audio fixtures and a heavy librosa provision, so this
test pins the deterministic contract the skill relies on: the script returns a
meaningful non-zero exit code when its audio directory is missing or empty,
rather than crashing with a traceback. It invokes via `uv run` so the librosa
PEP 723 deps are provisioned (the directory guard fires after the dep check).
Skips when uv is unavailable.
"""

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "analyze-audio.py")
UV = shutil.which("uv")
TIMEOUT = 600


def run_uv(args: list[str], cwd=None) -> int:
    return subprocess.run([UV, "run", SCRIPT, *args], capture_output=True, text=True, timeout=TIMEOUT,
                          cwd=cwd).returncode


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@unittest.skipIf(UV is None, "uv not available to provision librosa deps")
class AnalyzeAudioTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp_path = Path(td.name)

    def test_missing_dir_exits_1(self):
        self.assertEqual(run_uv(["/nonexistent-audio-dir-xyz"]), 1)

    def test_empty_dir_exits_1(self):
        self.assertEqual(run_uv([str(self.tmp_path)]), 1)

    def test_every_file_failing_exits_1_and_writes_nothing(self):
        audio = self.tmp_path / "docs" / "audio" / "band-a"
        audio.mkdir(parents=True)
        (audio / "Broken.mp3").write_bytes(b"not audio at all")
        code = run_uv([str(audio), "--tempo-source", "librosa"], cwd=self.tmp_path)
        self.assertEqual(code, 1)
        self.assertFalse((self.tmp_path / "docs" / "audio-analysis").exists())
        self.assertFalse((self.tmp_path / "docs" / "audio-analysis-reference.md").exists())

    def test_single_file_that_is_not_mp3_exits_1(self):
        f = self.tmp_path / "notes.txt"
        f.write_text("x")
        self.assertEqual(run_uv([str(f)]), 1)

    def test_find_mp3s_recurses_and_labels_band_folders(self):
        m = load("analyze_audio")
        tmp_path = self.tmp_path
        (tmp_path / "band-a").mkdir()
        (tmp_path / ".hidden").mkdir()
        for rel in ("band-a/Song.mp3", "Loose.mp3", ".hidden/Skip.mp3", "notes.txt"):
            (tmp_path / rel).write_bytes(b"x")
        found = m.find_mp3s(str(tmp_path))
        self.assertEqual([m.rel_label(p, str(tmp_path)) for p in found], ["Loose.mp3", "band-a/Song.mp3"])

    def test_text_and_json_report_loudness(self):
        m = load("analyze_audio_fmt")
        results = [
            {"file": "band-a/One.mp3", "duration": "3:10", "bpm_librosa": 152.0, "key": "F major", "key_confidence": 0.81,
             "loudness": {"integrated_lufs": -14.02, "lra_lu": 7.44, "thirds_lufs": [-16, -14, -13], "build_lu": 3.0}},
            {"file": "band-a/Two.mp3", "duration": "0:04", "bpm_librosa": 95.7, "key": "C minor", "key_confidence": 0.69,
             "loudness": {"integrated_lufs": -20.5, "lra_lu": None, "thirds_lufs": [None, None, None], "build_lu": None}},
        ]
        text = m.format_text_output(results, 2)
        self.assertIn("LUFS", text)
        self.assertNotIn("aub", text)
        self.assertIn("-14.02", text)
        self.assertIn("Loudness range (integrated): -20.5 to -14.0 LUFS", text)
        data = m.format_json_output(results, 2)
        self.assertEqual(data["metrics"]["integrated_lufs_range"], {"min": -20.5, "max": -14.02})

    def test_beat_this_tempo_preferred_with_librosa_kept(self):
        m = load("analyze_audio_bt")
        loud = {"integrated_lufs": -14.0, "lra_lu": 6.0, "thirds_lufs": [-15, -14, -13], "build_lu": 2.0}
        results = [
            {"file": "a.mp3", "duration": "2:37", "bpm": 76.9, "bpm_beat_this": 76.9, "tempo_relation": "librosa_double",
             "tempo_source": "beat-this", "bpm_librosa": 152.0, "key": "F major", "key_confidence": 0.8, "loudness": loud},
            {"file": "b.mp3", "duration": "3:11", "bpm": 96.8, "bpm_beat_this": 96.8, "tempo_relation": "agree",
             "tempo_source": "beat-this", "bpm_librosa": 95.7, "key": "C minor", "key_confidence": 0.7, "loudness": loud},
        ]
        text = m.format_text_output(results, 2)
        self.assertIn("BPM range (Beat This!): 77 - 97", text)
        self.assertIn("different pulse on 1 track", text)
        metrics = m.format_json_output(results, 2)["metrics"]
        self.assertEqual(metrics["tempo_source"], "beat-this")
        self.assertEqual(metrics["bpm_range"], {"min": 76.9, "max": 96.8})
        self.assertEqual(metrics["bpm_range_librosa"], {"min": 95.7, "max": 152.0})

    def test_slow_prior_reading_and_halftime_note(self):
        m = load("analyze_audio_slow")
        loud = {"integrated_lufs": -15.9, "lra_lu": 5.5, "thirds_lufs": [-17, -16, -15], "build_lu": 2.0}
        slow = {"file": "slow.mp3", "duration": "3:59", "bpm": 117.5, "tempo_source": "librosa", "bpm_librosa": 117.5,
                "bpm_librosa_slow_prior": 60.1, "librosa_prior_relation": "double", "key": "G# major",
                "key_confidence": 0.85, "loudness": loud}
        agree = {**slow, "file": "agree.mp3", "bpm": 95.7, "bpm_librosa": 95.7, "bpm_librosa_slow_prior": 95.7,
                 "librosa_prior_relation": "agree"}
        text = m.format_text_output([slow, agree], 2)
        self.assertIn("Slow80", text)
        self.assertIn("60.1 (x2)", text)
        self.assertIn("     95.7      95.7 ", text)
        self.assertIn("Likely halftime ambiguity: librosa reads 117.5 BPM at its default and 60.1", text)
        two = m.format_text_output([slow, {**slow, "file": "slow2.mp3"}], 2)
        self.assertIn("Likely halftime ambiguity on 2 tracks", two)
        metrics = m.format_json_output([slow, agree], 2)["metrics"]
        self.assertEqual(metrics["librosa_prior_doubles"], 1)
        self.assertEqual(metrics["bpm_range_librosa"], {"min": 95.7, "max": 117.5})
        self.assertEqual(metrics["tracks"][0]["bpm_librosa"], 117.5)  # the default reading keeps its field and value


if __name__ == "__main__":
    unittest.main()
