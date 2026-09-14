#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Tempo source selection: Beat This! when the owner opted in, librosa otherwise.

The librosa scripts read tempo and beat positions with librosa's beat tracker.
Beat This! (beat-grid.py, optional, PyTorch) matched felt BPM more often on the
reference catalog and fixes most of librosa's halftime double-reads. So when the
owner has opted in to the PyTorch audio tools (`pytorch_audio_tools` in the suno
module config, asked by /suno-setup), those scripts take their beats from Beat
This! instead. Opted out, they use librosa exactly as before. If Beat This!
can't run (not provisioned yet, or an error), the script falls back to librosa
and says so.

beat-grid.py runs as its own `uv run` process, so the librosa scripts never
pull PyTorch into their own environments.
"""

import json
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

CONFIG_KEY = "pytorch_audio_tools"
MODULE_CODE = "suno"
TRUTHY = {"true", "yes", "on", "1"}
SOURCES = ("auto", "beat-this", "librosa")
SOURCE_LABELS = {
    "beat-this": "Beat This!",
    "librosa": "librosa",
    "mixed": "Beat This! (librosa for tracks it couldn't read)",
}
TEMPO_RELATIONS = (
    (1.0, "agree"),
    (2.0, "librosa_double"),
    (0.5, "librosa_half"),
    (1.5, "librosa_1.5x"),
    (2 / 3, "librosa_2/3x"),
)
WINDOW_S = 15.0
SHIFT_THRESHOLD = 0.10
FEEL_TOLERANCE = 0.08
BEAT_GRID = Path(__file__).resolve().parent.parent / "suno-feedback-elicitor" / "scripts" / "beat-grid.py"


class BeatThisUnavailable(RuntimeError):
    """Beat This! could not produce readings; the caller falls back to librosa."""


def _scalar(raw):
    """A YAML scalar from one line's value: comment stripped, quotes removed, lower-cased."""
    value = raw.split(" #", 1)[0].strip().strip("'\"")
    return value.lower()


def read_config_flag(root):
    """The `pytorch_audio_tools` value from a project root's BMad config, or None.

    Looks in the per-module file _bmad/suno/config.yaml (flat keys) first, then
    the `suno:` section of the shared _bmad/config.yaml. A line scan rather than
    a YAML parse, so the scripts that use it need no pyyaml.
    """
    root = Path(root)
    flat = root / "_bmad" / MODULE_CODE / "config.yaml"
    if flat.is_file():
        for line in flat.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{CONFIG_KEY}:"):
                return _scalar(line.split(":", 1)[1])
    shared = root / "_bmad" / "config.yaml"
    if shared.is_file():
        section = None
        for line in shared.read_text(encoding="utf-8").splitlines():
            if line and not line[0].isspace() and not line.startswith("#"):
                section = line.split(":", 1)[0].strip()
                continue
            if section == MODULE_CODE and line.strip().startswith(f"{CONFIG_KEY}:"):
                return _scalar(line.strip().split(":", 1)[1])
    return None


def find_config_flag(start=None):
    """Walk up from `start` (default: the working directory) to the first BMad config that sets the flag."""
    here = Path(start or os.getcwd()).resolve()
    for root in (here, *here.parents):
        value = read_config_flag(root)
        if value is not None:
            return value
    return None


def opted_in(start=None):
    """True when the owner has turned the PyTorch audio tools on."""
    return (find_config_flag(start) or "") in TRUTHY


def add_tempo_source_arg(parser):
    parser.add_argument(
        "--tempo-source", choices=SOURCES, default="auto",
        help=("Where tempo and beats come from. auto (default): Beat This! when the PyTorch audio tools "
              f"are turned on in the module config ({CONFIG_KEY}), otherwise librosa. beat-this / librosa "
              "force one for this run."),
    )


def resolve_tempo_source(requested="auto", start=None):
    """'beat-this' or 'librosa' for a --tempo-source value."""
    if requested in ("beat-this", "librosa"):
        return requested
    return "beat-this" if opted_in(start) else "librosa"


def _beat_grid_command(paths, include_beats):
    uv = shutil.which("uv")
    runner = [uv, "run", "--quiet", str(BEAT_GRID)] if uv else [sys.executable, str(BEAT_GRID)]
    cmd = [*runner, *[str(p) for p in paths], "--no-librosa", "--no-archive", "--format", "json"]
    if include_beats:
        cmd.append("--include-beats")
    return cmd


def run_beat_grid(paths, include_beats=False):
    """Beat This! readings for each path, in the same order (a dict per track).

    A track Beat This! couldn't read comes back as {"error": ...}. Raises
    BeatThisUnavailable when the tool itself can't run.
    """
    paths = list(paths)
    if not paths:
        return []
    if not BEAT_GRID.is_file():
        raise BeatThisUnavailable(f"beat-grid.py not found at {BEAT_GRID}")
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    try:
        # Progress lines on beat-grid's stderr pass straight through to ours.
        proc = subprocess.run(_beat_grid_command(paths, include_beats), stdout=subprocess.PIPE,
                              text=True, env=env)
    except OSError as exc:
        raise BeatThisUnavailable(f"could not start beat-grid.py: {exc}") from exc
    if proc.returncode == 2:
        raise BeatThisUnavailable("PyTorch / Beat This! not installed (run it via `uv run` to provision)")
    try:
        data = json.loads(proc.stdout)
        tracks = data["metrics"]["tracks"]
    except (ValueError, KeyError, TypeError) as exc:
        raise BeatThisUnavailable(f"beat-grid.py exited {proc.returncode} without usable output") from exc
    if len(tracks) != len(paths):
        raise BeatThisUnavailable(f"beat-grid.py returned {len(tracks)} tracks for {len(paths)} files")
    return tracks


def beat_this_readings(paths, include_beats=False, log=sys.stderr):
    """Beat This! readings for `paths`, or None (with a note on `log`) when it can't run."""
    try:
        return run_beat_grid(paths, include_beats)
    except BeatThisUnavailable as exc:
        print(f"  NOTE: Beat This! unavailable ({exc}); using librosa for tempo.", file=log)
        return None


def tempo_relation(beat_bpm, librosa_bpm, tolerance=0.05):
    """How librosa's BPM relates to Beat This!'s: agree, double, half, 1.5x, 2/3x, or disagree."""
    if not beat_bpm or not librosa_bpm:
        return None
    ratio = librosa_bpm / beat_bpm
    for target, label in TEMPO_RELATIONS:
        if abs(ratio / target - 1) <= tolerance:
            return label
    return "disagree"


def source_summary(results):
    """'beat-this', 'librosa', or 'mixed' across analyzed results (errors skipped; unmarked = librosa)."""
    found = {r.get("tempo_source") or "librosa" for r in results if "error" not in r}
    if len(found) == 1:
        return found.pop()
    return "mixed" if found else "librosa"


def window_tempos(beat_times, window_s=WINDOW_S, min_beats=4):
    """Median beat-to-beat BPM per window: [{"start", "end", "bpm", "beats"}].

    Medians shrug off the odd stray or missed beat, which Beat This!'s raw
    detections have and librosa's fixed-tempo tracker never shows. Windows with
    fewer than `min_beats` intervals are skipped.
    """
    beats = sorted(float(b) for b in beat_times)
    buckets = {}
    for a, b in zip(beats, beats[1:]):
        if b > a:
            buckets.setdefault(int(a // window_s), []).append(60.0 / (b - a))
    last = beats[-1] if beats else 0.0
    return [
        {"start": k * window_s, "end": round(min((k + 1) * window_s, last), 2),
         "bpm": round(statistics.median(v), 1), "beats": len(v)}
        for k, v in sorted(buckets.items()) if len(v) >= min_beats
    ]


def windowed_stability(windows):
    """Stability label and (low, high) BPM from how far window medians stray from their overall median.

    steady within 4%, slight variation within 10%, TEMPO CHANGES beyond.
    """
    if not windows:
        return "too few beats", (0, 0)
    bpms = [w["bpm"] for w in windows]
    center = statistics.median(bpms)
    spread = max(abs(b / center - 1) for b in bpms)
    label = "steady" if spread < 0.04 else "slight variation" if spread < SHIFT_THRESHOLD else "TEMPO CHANGES"
    return label, (round(min(bpms)), round(max(bpms)))


def feel_name(ratio):
    """half-time, double-time, triplet grid, or shift for a tempo ratio against the track's."""
    for target, name in ((0.5, "half-time"), (2.0, "double-time"), (1.5, "triplet grid"), (2 / 3, "triplet grid")):
        if abs(ratio / target - 1) <= FEEL_TOLERANCE:
            return name
    return "shift"


def feel_sections(windows, overall_bpm, window_s=WINDOW_S):
    """Runs of windows whose tempo departs from the track's by 10% or more.

    Each: {"start", "end", "bpm" (median of the run's windows), "feel"}, where feel
    is half-time, double-time, triplet grid, or shift. Descriptive only: a
    half-time breakdown the arrangement asked for reads the same as one Suno
    invented, and the ear decides which pulse is felt.
    """
    runs = []
    if not overall_bpm:
        return runs
    for w in windows:
        ratio = w["bpm"] / overall_bpm
        if abs(ratio - 1) < SHIFT_THRESHOLD:
            continue
        feel = feel_name(ratio)
        if runs and runs[-1]["feel"] == feel and round(runs[-1]["_next"], 6) == round(w["start"], 6):
            runs[-1].update(end=w["end"], _next=w["start"] + window_s)
            runs[-1]["_bpms"].append(w["bpm"])
        else:
            runs.append({"start": w["start"], "end": w["end"], "feel": feel, "_bpms": [w["bpm"]],
                         "_next": w["start"] + window_s})
    return [{"start": r["start"], "end": r["end"], "bpm": round(statistics.median(r["_bpms"]), 1), "feel": r["feel"]}
            for r in runs]


def usable(reading):
    """A Beat This! reading with a tempo in it (not an error, not too few beats)."""
    return bool(reading) and "error" not in reading and reading.get("bpm") is not None
