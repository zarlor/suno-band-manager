#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["beat-this>=1.1", "torch>=2.1", "librosa>=1.0", "numpy>=2.1"]
# ///
"""Neural beat and downbeat tracking (Beat This!, CPJKU) — a second opinion on tempo.

librosa's beat tracker routinely lands on half or double the felt pulse. Beat
This! tracks beats and downbeats with a transformer model. On an 83-track
reference catalog it matched the human-verified felt BPM more often than
librosa (9 of 15 vs 7) and fixed most of librosa's halftime double-reads.
It does not settle felt tempo on its own: slow doom and ballad feels still read
double. Report both numbers; felt BPM stays a human call.

Per track: Beat This! BPM (median inter-beat interval), beats per bar (mode and
histogram), bars per minute, librosa's BPM, and how the two relate (agree,
librosa double, librosa half, 1.5x / 2/3x triplet-grid readings, or disagree).

Beats per bar reads how the pulse groups, not the notated meter. On the
reference catalog every song with a 6/8 *feel* read 4 — Suno renders
style-side 6/8 as a feel inside 4/4.

Optional and heavy: PyTorch (1-3 GB on first provision) plus the Beat This!
checkpoint, downloaded on first use. Uses a CUDA GPU when present; CPU works
at a few seconds per track.

Usage:
    uv run beat-grid.py [audio-file-or-directory] [options]

    # Every track under docs/audio (recursive)
    uv run beat-grid.py

    # One band, as a table
    uv run beat-grid.py docs/audio/my-band --format text

    # One song, with beat and downbeat timestamps
    uv run beat-grid.py "docs/audio/my-band/Song.mp3" --include-beats

Exit codes:
  0 = success
  1 = invalid arguments, no audio found, or runtime error
  2 = missing dependencies
"""

import argparse
import json
import os
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from audio_deps import require_modules
from json_archiver import input_archive_identifier, resolve_archive_arg, write_archive

SCRIPT_NAME = "beat-grid"
VERSION = "1.0.0"
AUDIO_EXTS = (".mp3", ".wav", ".flac", ".ogg", ".m4a")
INSTALL_CMD = "pip install beat-this torch librosa numpy"
CHECKPOINT = "final0"
ANALYSIS_SR = 22050

TEMPO_RELATIONS = (
    (1.0, "agree"),
    (2.0, "librosa_double"),
    (0.5, "librosa_half"),
    (1.5, "librosa_1.5x"),
    (2 / 3, "librosa_2/3x"),
)
RELATION_TEXT = {
    "agree": "agree",
    "librosa_double": "librosa ~2x (double-time read)",
    "librosa_half": "librosa ~1/2x (half-time read)",
    "librosa_1.5x": "librosa ~1.5x (triplet grid)",
    "librosa_2/3x": "librosa ~2/3x (triplet grid)",
    "disagree": "disagree",
}


def collect_inputs(path):
    """A single audio file, or every audio file under a directory (recursive, hidden dirs skipped)."""
    if os.path.isfile(path):
        return [path]
    found = []
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        found.extend(os.path.join(root, f) for f in files if f.lower().endswith(AUDIO_EXTS))
    return sorted(found)


def rel_label(filepath, base):
    """Label relative to the scanned directory ("band-slug/Song.mp3"), or the bare filename."""
    if os.path.isfile(base):
        return os.path.basename(filepath)
    return os.path.relpath(filepath, base).replace(os.sep, "/")


def beat_stats(beats, downbeats):
    """Tempo and bar grouping from beat and downbeat times (seconds)."""
    beats = sorted(float(b) for b in beats)
    downbeats = sorted(float(d) for d in downbeats)
    out = {
        "n_beats": len(beats),
        "n_downbeats": len(downbeats),
        "bpm": None,
        "beats_per_bar": None,
        "beats_per_bar_hist": {},
        "bars_per_minute": None,
    }
    if len(beats) > 4:
        ibi = statistics.median(b - a for a, b in zip(beats, beats[1:]))
        if ibi > 0:
            out["bpm"] = round(60.0 / ibi, 1)
    if len(downbeats) > 2:
        counts = [sum(1 for b in beats if a <= b < c) for a, c in zip(downbeats, downbeats[1:])]
        hist = Counter(counts)
        out["beats_per_bar"] = max(sorted(hist), key=hist.get)
        out["beats_per_bar_hist"] = {str(k): hist[k] for k in sorted(hist)}
        bar = statistics.median(c - a for a, c in zip(downbeats, downbeats[1:]))
        if bar > 0:
            out["bars_per_minute"] = round(60.0 / bar, 1)
    return out


def tempo_relation(beat_bpm, librosa_bpm, tolerance=0.05):
    """How librosa's BPM relates to Beat This!'s: agree, double, half, 1.5x, 2/3x, or disagree."""
    if not beat_bpm or not librosa_bpm:
        return None
    ratio = librosa_bpm / beat_bpm
    for target, label in TEMPO_RELATIONS:
        if abs(ratio / target - 1) <= tolerance:
            return label
    return "disagree"


def resolve_device(requested):
    import torch

    if requested != "auto":
        return requested
    return "cuda" if torch.cuda.is_available() else "cpu"


def analyze_file(path, a2b, with_librosa=True, include_beats=False):
    import librosa
    import numpy as np

    y, sr = librosa.load(path, sr=ANALYSIS_SR, mono=True)
    beats, downbeats = a2b(y, sr)
    result = {"duration_s": round(len(y) / sr, 1), **beat_stats(beats, downbeats)}
    if with_librosa:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        lib_bpm = round(float(np.atleast_1d(tempo)[0]), 1)
        result["librosa_bpm"] = lib_bpm
        result["tempo_relation"] = tempo_relation(result["bpm"], lib_bpm)
    if include_beats:
        result["beats_s"] = [round(float(b), 3) for b in beats]
        result["downbeats_s"] = [round(float(d), 3) for d in downbeats]
    return result


def _fmt(v, width):
    return f"{'-' if v is None else v:>{width}}"


def format_text(results):
    lines = [
        f"{'Track':<50} {'Dur(s)':>7} {'BPM(BT)':>8} {'Beats/bar':>9} {'BPM(lib)':>9}  Relation",
        "-" * 110,
    ]
    for r in results:
        if "error" in r:
            lines.append(f"{r['file']:<50} ERROR: {r['error']}")
            continue
        rel = RELATION_TEXT.get(r.get("tempo_relation"), "-")
        lines.append(
            f"{r['file']:<50} {_fmt(r['duration_s'], 7)} {_fmt(r['bpm'], 8)} "
            f"{_fmt(r['beats_per_bar'], 9)} {_fmt(r.get('librosa_bpm'), 9)}  {rel}"
        )
    rels = Counter(r.get("tempo_relation") for r in results if "error" not in r and r.get("tempo_relation"))
    if rels:
        lines.append("")
        lines.append("Relation counts: " + ", ".join(f"{RELATION_TEXT[k]} {v}" for k, v in rels.most_common()))
    lines.append("Felt BPM is a human call: where the two disagree by a clean ratio, the ear decides which pulse is felt.")
    return "\n".join(lines)


def format_json(results, device):
    valid = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]
    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not errors else "partial" if valid else "fail",
        "metrics": {
            "tracks_found": len(results),
            "tracks_analyzed": len(valid),
            "tracks_errored": len(errors),
            "model": f"beat-this {CHECKPOINT}",
            "device": device,
            "tracks": results,
        },
        "findings": [{"file": r["file"], "level": "error", "message": r["error"]} for r in errors],
        "summary": {"total": len(errors)},
    }


def main():
    parser = argparse.ArgumentParser(
        description="Beat This! neural beat/downbeat tracking — a second opinion on tempo and bar grouping.",
    )
    parser.add_argument("input", nargs="?", default="docs/audio",
                        help="Audio file, or a directory searched recursively (default: docs/audio)")
    parser.add_argument("--device", default="auto",
                        help="Torch device: auto (CUDA when available, else CPU), cpu, cuda, cuda:1, mps ...")
    parser.add_argument("--no-librosa", action="store_true",
                        help="Skip the librosa BPM comparison.")
    parser.add_argument("--include-beats", action="store_true",
                        help="Include every beat and downbeat timestamp in the JSON.")
    parser.add_argument("--format", choices=["json", "text"], default="json", dest="output_format",
                        help="Output format (default: json)")
    parser.add_argument("-o", "--output", default=None, help="Output file path (default: stdout)")
    parser.add_argument("--archive", nargs="?", const="", default="",
                        help=("Persist the JSON to the analysis archive. With no path: a directory run writes "
                              "docs/audio-analysis/catalog/<YYYY-MM-DD>-beat-grid.json, a single file "
                              "docs/audio-analysis/songs/[{band-slug}/]{song}-beat-grid.json. Default: ON."))
    parser.add_argument("--no-archive", dest="archive", action="store_const", const=None,
                        help="Skip writing the JSON archive.")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(json.dumps({"script": SCRIPT_NAME, "status": "fail", "error": f"Not found: {args.input}"}), file=sys.stderr)
        sys.exit(1)
    files = collect_inputs(args.input)
    if not files:
        print(json.dumps({"script": SCRIPT_NAME, "status": "fail", "error": f"No audio files in {args.input}"}), file=sys.stderr)
        sys.exit(1)

    require_modules(["torch", "beat_this", "librosa", "numpy"], INSTALL_CMD, "Beat This! beat tracking")
    from beat_this.inference import Audio2Beats

    device = resolve_device(args.device)
    try:
        a2b = Audio2Beats(checkpoint_path=CHECKPOINT, device=device, dbn=False)
    except Exception as exc:
        print(json.dumps({"script": SCRIPT_NAME, "status": "fail",
                          "error": f"Could not load the Beat This! model on {device}: {exc}"}), file=sys.stderr)
        sys.exit(1)

    results = []
    for i, path in enumerate(files, 1):
        label = rel_label(path, args.input)
        print(f"  [{i}/{len(files)}] {label}", file=sys.stderr, flush=True)
        try:
            r = {"file": label, **analyze_file(path, a2b, not args.no_librosa, args.include_beats)}
        except Exception as exc:
            r = {"file": label, "error": f"{type(exc).__name__}: {exc}"}
        results.append(r)

    json_data = format_json(results, device)
    output = format_text(results) if args.output_format == "text" else json.dumps(json_data, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n")
    else:
        print(output)

    category, identifier = input_archive_identifier(args.input, SCRIPT_NAME)
    target = resolve_archive_arg(category, identifier, args.archive)
    if target is not None:
        res = write_archive(target, json_data)
        print(f"  ARCHIVED: {res['path']} ({res['bytes_written']} bytes)", file=sys.stderr)

    sys.exit(0 if json_data["status"] != "fail" else 1)


if __name__ == "__main__":
    main()
