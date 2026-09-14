#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["librosa>=1.0", "numpy>=2.1", "pyloudnorm>=0.2"]
# ///
"""Batch audio analysis for a song catalog.

Extracts BPM, estimated key, duration, and BS.1770 loudness (integrated LUFS
and loudness range) for all MP3s in a directory.

Tempo comes from Beat This! (beat-grid.py) when the PyTorch audio tools are
turned on in the module config (`pytorch_audio_tools`), otherwise from librosa.
librosa's reading is always kept as `bpm_librosa`; `--tempo-source` overrides
the choice for one run.

Usage:
    uv run analyze-audio.py [audio-directory] [options]

    # Analyze default directory
    uv run analyze-audio.py

    # Analyze specific directory
    uv run analyze-audio.py /path/to/audio

    # JSON output to file
    uv run analyze-audio.py /path/to/audio --format json -o results.json

Exit codes:
  0 = success
  1 = invalid arguments or runtime error
  2 = missing dependencies
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from audio_deps import require_audio_deps
from companion_writer import update_companion, resolve_companion_path
from json_archiver import resolve_archive_arg, write_archive
from loudness import load_native, summarize as loudness_summary
from tempo_source import (SOURCE_LABELS, add_tempo_source_arg, beat_this_readings, resolve_tempo_source,
                          source_summary, tempo_relation, usable)

SCRIPT_NAME = "analyze-audio"
VERSION = "1.2.0"


def get_key(y, sr):
    """Estimate musical key using chroma features."""
    import numpy as np

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_avg = np.mean(chroma, axis=1)

    pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Major and minor profiles (Krumhansl-Kessler)
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    best_corr = -1
    best_key = "Unknown"

    for i in range(12):
        rolled = np.roll(chroma_avg, -i)
        maj_corr = np.corrcoef(rolled, major_profile)[0, 1]
        min_corr = np.corrcoef(rolled, minor_profile)[0, 1]

        if maj_corr > best_corr:
            best_corr = maj_corr
            best_key = f"{pitch_classes[i]} major"
        if min_corr > best_corr:
            best_corr = min_corr
            best_key = f"{pitch_classes[i]} minor"

    return best_key, best_corr


def analyze_file(filepath, beat_reading=None):
    """Analyze a single audio file. `beat_reading` is its Beat This! reading, when that's the tempo source."""
    import numpy as np

    filename = os.path.basename(filepath)

    try:
        y, sr = librosa.load(filepath, sr=22050)
        duration = librosa.get_duration(y=y, sr=sr)

        # BPM via librosa
        tempo_librosa, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm_librosa = round(float(tempo_librosa[0]) if hasattr(tempo_librosa, '__len__') else float(tempo_librosa), 1)
        tempo = {'bpm': bpm_librosa, 'tempo_source': 'librosa'}
        if usable(beat_reading):
            tempo = {
                'bpm': beat_reading['bpm'],
                'bpm_beat_this': beat_reading['bpm'],
                'tempo_relation': tempo_relation(beat_reading['bpm'], bpm_librosa),
                'tempo_source': 'beat-this',
            }

        # Loudness (BS.1770) at the file's native rate and channels
        samples, native_sr = load_native(filepath)
        loudness = loudness_summary(samples, native_sr)

        # Key estimation
        key, confidence = get_key(y, sr)

        mins = int(duration // 60)
        secs = int(duration % 60)

        return {
            'file': filename,
            'duration': f"{mins}:{secs:02d}",
            **tempo,
            'bpm_librosa': bpm_librosa,
            'loudness': loudness,
            'key': key,
            'key_confidence': round(confidence, 3),
        }
    except Exception as e:
        return {
            'file': filename,
            'error': str(e)
        }


def _fmt(value):
    return "-" if value is None else value


def _bpm(result):
    """The preferred BPM (Beat This! or librosa); older results carry only bpm_librosa."""
    return result.get('bpm', result.get('bpm_librosa'))


def _lufs_values(results):
    return [r['loudness']['integrated_lufs'] for r in results
            if (r.get('loudness') or {}).get('integrated_lufs') is not None]


def format_text_output(results, mp3_count):
    """Format results as human-readable text (original output format)."""
    lines = []
    lines.append(f"Analyzing {mp3_count} tracks...\n")
    lines.append(f"{'Track':<50} {'Duration':>8} {'BPM':>9} {'LUFS':>7} {'LRA':>5} {'Key':<15} {'Conf':>5}")
    lines.append("-" * 106)

    for result in results:
        if 'error' in result:
            lines.append(f"{result['file']:<50} ERROR: {result['error']}")
        else:
            loud = result.get('loudness') or {}
            lines.append(
                f"{result['file']:<50} {result['duration']:>8} {_bpm(result):>9} "
                f"{_fmt(loud.get('integrated_lufs')):>7} {_fmt(loud.get('lra_lu')):>5} "
                f"{result['key']:<15} {result['key_confidence']:>5}"
            )

    # Summary stats
    valid = [r for r in results if 'error' not in r]
    if valid:
        bpms = [_bpm(r) for r in valid]
        source = source_summary(valid)
        lines.append(f"\n{'='*100}")
        lines.append(f"BPM range ({SOURCE_LABELS[source]}): {min(bpms):.0f} - {max(bpms):.0f}")
        differ = [r for r in valid if r.get('tempo_relation') not in (None, 'agree')]
        if differ:
            lines.append(f"librosa reads a different pulse on {len(differ)} track(s) "
                         "(bpm_librosa / tempo_relation in the JSON); felt BPM is the ear's call")
        lufs = _lufs_values(valid)
        if lufs:
            lines.append(f"Loudness range (integrated): {min(lufs):.1f} to {max(lufs):.1f} LUFS")
        lines.append(f"Tracks analyzed: {len(valid)}/{mp3_count}")

    return "\n".join(lines)


def format_json_output(results, mp3_count):
    """Format results as structured JSON."""
    valid = [r for r in results if 'error' not in r]
    errors = [r for r in results if 'error' in r]
    findings = []

    for r in results:
        if 'error' in r:
            findings.append({
                "file": r["file"],
                "level": "error",
                "message": r["error"],
            })

    bpms = [_bpm(r) for r in valid]
    lib_bpms = [r['bpm_librosa'] for r in valid if r.get('bpm_librosa') is not None]
    lufs = _lufs_values(valid)

    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not errors else "partial" if valid else "fail",
        "metrics": {
            "tracks_found": mp3_count,
            "tracks_analyzed": len(valid),
            "tracks_errored": len(errors),
            "tempo_source": source_summary(valid),
            "bpm_range": {
                "min": min(bpms) if bpms else None,
                "max": max(bpms) if bpms else None,
            },
            "bpm_range_librosa": {
                "min": min(lib_bpms) if lib_bpms else None,
                "max": max(lib_bpms) if lib_bpms else None,
            },
            "integrated_lufs_range": {
                "min": min(lufs) if lufs else None,
                "max": max(lufs) if lufs else None,
            },
            "tracks": results,
        },
        "findings": findings,
        "summary": {"total": len(findings)},
    }


def find_mp3s(audio_dir):
    """All .mp3 files under audio_dir, recursively, sorted.

    Recursive so the per-band layout (docs/audio/{band-slug}/Song.mp3) is
    covered by the default docs/audio scan; a flat docs/audio/ still works.
    Hidden directories are skipped.
    """
    found = []
    for root, dirs, files in os.walk(audio_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.'))
        found.extend(os.path.join(root, f) for f in files if f.endswith('.mp3'))
    return sorted(found)


def rel_label(filepath, audio_dir):
    """Display label for a file: its path relative to audio_dir, POSIX-style.

    A file in a band sub-folder is labelled "band-slug/Song.mp3", so two bands'
    renderings of the same title stay distinguishable in reports.
    """
    return os.path.relpath(filepath, audio_dir).replace(os.sep, '/')


def main():
    require_audio_deps(extra=("pyloudnorm",))

    import librosa  # noqa: E402
    import numpy as np  # noqa: E402, F401

    # Make librosa available to module-level helper functions
    globals()["librosa"] = librosa

    parser = argparse.ArgumentParser(
        description="Batch audio analysis — BPM, key, duration, and loudness for all MP3s in a directory.",
    )
    parser.add_argument(
        "audio_dir",
        nargs="?",
        default="docs/audio",
        help="Directory containing MP3 files, searched recursively so per-band sub-folders are included (default: docs/audio)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        dest="output_format",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--archive", nargs="?", const="", default="",
        help=(
            "Persist full JSON output to a dated catalog archive. "
            "With no path: writes to docs/audio-analysis/catalog/<YYYY-MM-DD>-summary.json. "
            "Pass an explicit path to override. Default: ON."
        ),
    )
    parser.add_argument(
        "--no-archive", dest="archive", action="store_const", const=None,
        help="Skip writing the JSON archive.",
    )
    parser.add_argument(
        "--companion", nargs="?", const="", default="",
        help=(
            "Refresh the canonical Markdown companion file. "
            "With no path: writes to docs/audio-analysis-reference.md. "
            "Pass an explicit path to override. Hand-curated sections "
            "outside the AUTOGEN markers are preserved. Default: ON."
        ),
    )
    parser.add_argument(
        "--no-companion", dest="companion", action="store_const", const=None,
        help="Skip refreshing the Markdown companion file.",
    )
    add_tempo_source_arg(parser)
    args = parser.parse_args()

    audio_dir = args.audio_dir

    if not os.path.isdir(audio_dir):
        print(f"Audio directory not found: {audio_dir}", file=sys.stderr)
        sys.exit(1)

    mp3s = find_mp3s(audio_dir)

    if not mp3s:
        print(f"No .mp3 files found in {audio_dir}", file=sys.stderr)
        sys.exit(1)

    source = resolve_tempo_source(args.tempo_source)
    readings = beat_this_readings(mp3s) if source == "beat-this" else None

    results = []
    for i, filepath in enumerate(mp3s):
        result = analyze_file(filepath, readings[i] if readings else None)
        result['file'] = rel_label(filepath, audio_dir)
        results.append(result)

    json_data = format_json_output(results, len(mp3s))

    if args.output_format == "text":
        output = format_text_output(results, len(mp3s))
    else:
        output = json.dumps(json_data, indent=2)

    if args.output:
        Path(args.output).write_text(output + "\n")
    else:
        print(output)

    # JSON archive (default ON unless --no-archive). Identifier suffix "-summary"
    # to distinguish from batch-full-analysis.py's "-deep" archive.
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d") + "-summary"
    archive_target = resolve_archive_arg("catalog", today, args.archive)
    if archive_target is not None:
        res = write_archive(archive_target, json_data)
        print(f"  ARCHIVED: {res['path']} ({res['bytes_written']} bytes)", file=sys.stderr)

    # Companion .md refresh (default ON unless --no-companion). The companion
    # docs/audio-analysis-reference.md has hand-curated sections (Felt BPM
    # Corrections, LLM BPM Comparison) preserved OUTSIDE the AUTOGEN markers.
    # Title + timestamp live inside the markers so each refresh updates them.
    companion_target = resolve_companion_path(SCRIPT_NAME, args.companion)
    if companion_target is not None:
        timestamp = datetime.now(timezone.utc).isoformat()
        title_block = (
            "# Audio Analysis Reference — Catalog Summary\n"
            f"_Generated by `{SCRIPT_NAME}` on {timestamp}_\n"
            f"_Tempo: {SOURCE_LABELS[source_summary(results)]} (librosa's reading kept as bpm_librosa) "
            "| Key detection: Krumhansl-Kessler "
            "chroma correlation | Loudness: ITU-R BS.1770 via pyloudnorm (LUFS integrated; LRA in LU)_\n\n"
        )
        body_lines = format_text_output(results, len(mp3s)).split("\n")
        cut = 0
        while cut < len(body_lines):
            line = body_lines[cut]
            if line.startswith("##") or (line.strip() and not line.startswith("#")):
                break
            cut += 1
        md_body = title_block + "\n".join(body_lines[cut:])
        res = update_companion(companion_target, SCRIPT_NAME, md_body)
        print(f"  COMPANION: {res['status']} {res['path']} ({res['bytes_written']} bytes)", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
