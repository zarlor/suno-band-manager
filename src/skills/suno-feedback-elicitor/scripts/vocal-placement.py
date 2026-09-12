#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["demucs>=4.0.1", "torch>=2.1", "librosa>=1.0", "numpy", "pyloudnorm>=0.2"]
# ///
"""Vocal placement — how loud the voice sits against the band (Demucs stems + BS.1770 loudness).

Separates each track with Demucs (htdemucs) into vocals, drums, bass, and other.
It then measures the vocal stem's loudness minus the loudness of everything
else, in LU. At 0 the voice is as loud as the whole band combined; higher means
more forward. Reported for the whole song and by thirds, plus the drift from
first third to last.

There's no "right" number — this describes placement. On an 83-track reference
catalog (two bands, v5.5-era renders):
- the band sung by a user voice sample had a median of -0.7 LU (range -3.8 to +2.2)
- the heavier band had a median of -2.2 LU (range -4.6 to +5.0)
- in both, the voice sank about 1.2-1.4 LU from first third to last as the
  arrangement built

Useful for comparing renderings of the same song (a voice-sample re-record
against the original, one model against another) and for tracking how a model
places a given voice. A third with no real vocal (an instrumental ending) is
flagged in `vocal_present_thirds`.

Optional and heavy: PyTorch plus the htdemucs weights (~80 MB), downloaded on
first use. A CUDA GPU takes about 5 seconds per track; CPU works but takes
minutes per track.

Usage:
    uv run vocal-placement.py [audio-file-or-directory] [options]

    uv run vocal-placement.py "docs/audio/my-band/Song.mp3"
    uv run vocal-placement.py docs/audio/my-band --format text

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
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from audio_deps import require_modules
from json_archiver import input_archive_identifier, resolve_archive_arg, write_archive
from loudness import integrated, thirds

SCRIPT_NAME = "vocal-placement"
VERSION = "1.0.0"
AUDIO_EXTS = (".mp3", ".wav", ".flac", ".ogg", ".m4a")
INSTALL_CMD = "pip install demucs torch librosa numpy pyloudnorm"
MODEL_NAME = "htdemucs"
# A third whose vocal stem sits this far below the band is residual bleed, not singing.
VOCAL_ABSENT_LU = -15.0


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
    if os.path.isfile(base):
        return os.path.basename(filepath)
    return os.path.relpath(filepath, base).replace(os.sep, "/")


def _diff(a, b):
    return None if a is None or b is None else round(a - b, 2)


def placement(vocal_lufs, band_lufs, vocal_thirds, band_thirds):
    """Vocal-minus-band loudness overall and by thirds, drift, and which thirds carry a vocal."""
    by_third = [_diff(v, b) for v, b in zip(vocal_thirds, band_thirds)]
    present = [d is not None and d > VOCAL_ABSENT_LU for d in by_third]
    drift = _diff(by_third[2], by_third[0]) if present[0] and present[2] else None
    return {
        "vocal_minus_band_lu": _diff(vocal_lufs, band_lufs),
        "vocal_minus_band_thirds_lu": by_third,
        "vocal_drift_lu": drift,
        "vocal_present_thirds": present,
    }


def resolve_device(requested):
    import torch

    if requested != "auto":
        return requested
    return "cuda" if torch.cuda.is_available() else "cpu"


def separate(model, wav, device):
    """Run Demucs on a (channels, samples) float array -> {stem name: (channels, samples) array}."""
    import torch
    from demucs.apply import apply_model

    mix = torch.tensor(wav, dtype=torch.float32)
    ref = mix.mean(0)
    mean, std = ref.mean(), ref.std() + 1e-8
    with torch.no_grad():
        stems = apply_model(model, ((mix - mean) / std)[None], split=True, overlap=0.25,
                            progress=False, device=device)[0]
    stems = (stems * std + mean).cpu().numpy()
    return dict(zip(model.sources, stems))


def analyze_file(path, model, meter, device):
    import librosa
    import numpy as np

    y, _ = librosa.load(path, sr=model.samplerate, mono=False)
    if y.ndim == 1:
        y = np.stack([y, y])
    y = y[: model.audio_channels]
    stems = separate(model, y, device)
    vocals = stems["vocals"]
    band = sum(v for k, v in stems.items() if k != "vocals")
    vocal_lufs, band_lufs = integrated(meter, vocals.T), integrated(meter, band.T)
    return {
        "duration_s": round(y.shape[1] / model.samplerate, 1),
        "vocals_lufs": vocal_lufs,
        "band_lufs": band_lufs,
        **placement(vocal_lufs, band_lufs, thirds(meter, vocals.T), thirds(meter, band.T)),
        "stems_lufs": {k: integrated(meter, v.T) for k, v in stems.items()},
    }


def _fmt(v, width):
    return f"{'-' if v is None else v:>{width}}"


def format_text(results):
    lines = [
        f"{'Track':<50} {'Vocal-band LU':>13}  {'By thirds':<24} {'Drift':>6}",
        "-" * 100,
    ]
    for r in results:
        if "error" in r:
            lines.append(f"{r['file']:<50} ERROR: {r['error']}")
            continue
        parts = [("-" if d is None else f"{d:+.1f}") + ("" if p else "*")
                 for d, p in zip(r["vocal_minus_band_thirds_lu"], r["vocal_present_thirds"])]
        lines.append(f"{r['file']:<50} {_fmt(r['vocal_minus_band_lu'], 13)}  {' / '.join(parts):<24} "
                     f"{_fmt(r['vocal_drift_lu'], 6)}")
    vals = [r["vocal_minus_band_lu"] for r in results if "error" not in r and r["vocal_minus_band_lu"] is not None]
    if vals:
        lines.append("")
        lines.append(f"Median vocal-minus-band: {statistics.median(vals):+.1f} LU "
                     f"(range {min(vals):+.1f} to {max(vals):+.1f}); * = no real vocal in that third")
    return "\n".join(lines)


def format_json(results, device):
    valid = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]
    vals = [r["vocal_minus_band_lu"] for r in valid if r["vocal_minus_band_lu"] is not None]
    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not errors else "partial" if valid else "fail",
        "metrics": {
            "tracks_found": len(results),
            "tracks_analyzed": len(valid),
            "tracks_errored": len(errors),
            "model": MODEL_NAME,
            "device": device,
            "median_vocal_minus_band_lu": round(statistics.median(vals), 2) if vals else None,
            "tracks": results,
        },
        "findings": [{"file": r["file"], "level": "error", "message": r["error"]} for r in errors],
        "summary": {"total": len(errors)},
    }


def main():
    parser = argparse.ArgumentParser(
        description="Vocal placement: vocal-stem loudness against the band (Demucs htdemucs + BS.1770).",
    )
    parser.add_argument("input", nargs="?", default="docs/audio",
                        help="Audio file, or a directory searched recursively (default: docs/audio)")
    parser.add_argument("--device", default="auto",
                        help="Torch device: auto (CUDA when available, else CPU), cpu, cuda, cuda:1 ...")
    parser.add_argument("--format", choices=["json", "text"], default="json", dest="output_format",
                        help="Output format (default: json)")
    parser.add_argument("-o", "--output", default=None, help="Output file path (default: stdout)")
    parser.add_argument("--archive", nargs="?", const="", default="",
                        help=("Persist the JSON to the analysis archive. With no path: a directory run writes "
                              "docs/audio-analysis/catalog/<YYYY-MM-DD>-vocal-placement.json, a single file "
                              "docs/audio-analysis/songs/[{band-slug}/]{song}-vocal-placement.json. Default: ON."))
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

    require_modules(["torch", "demucs", "librosa", "numpy", "pyloudnorm"], INSTALL_CMD, "Vocal placement")
    import pyloudnorm as pyln
    from demucs.pretrained import get_model

    device = resolve_device(args.device)
    try:
        model = get_model(MODEL_NAME)
        model.to(device).eval()
    except Exception as exc:
        print(json.dumps({"script": SCRIPT_NAME, "status": "fail",
                          "error": f"Could not load Demucs {MODEL_NAME} on {device}: {exc}"}), file=sys.stderr)
        sys.exit(1)
    meter = pyln.Meter(model.samplerate)

    results = []
    for i, path in enumerate(files, 1):
        label = rel_label(path, args.input)
        print(f"  [{i}/{len(files)}] {label}", file=sys.stderr, flush=True)
        try:
            r = {"file": label, **analyze_file(path, model, meter, device)}
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
