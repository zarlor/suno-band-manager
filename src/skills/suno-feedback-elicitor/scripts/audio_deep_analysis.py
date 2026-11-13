#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"  # librosa>=1.0 requires Python 3.12
# dependencies = ["librosa>=1.0", "numpy>=2.1"]
# ///
"""Deep audio analysis -- chord progression, energy over time, spectral features,
section boundaries, and harmonic/percussive separation analysis.

Usage:
    uv run audio_deep_analysis.py <audio-file> [options]

    # Analyze a single track
    uv run audio_deep_analysis.py track.mp3

    # JSON output to file
    uv run audio_deep_analysis.py track.mp3 --format json -o results.json

Windows cover the whole track: a tail of half a window or more is its own
window, a shorter one joins the last window, and a track shorter than one
window is read as one window, so no track comes back with empty arrays.

Either format honours -o, and either archives the JSON (default ON) to
docs/audio-analysis/songs/[<band-slug>/]<song-slug>.json under the project that
holds the audio (the nearest folder above it with `_bmad/`), or under the
working directory when there is none.

Exit codes:
  0 = success
  1 = usage error, file not found, a file that could not be read or analyzed
      (corrupt, empty, too short), or an -o file that could not be written.
      The reason is the JSON failure object on stdout and one line on stderr.
  2 = missing dependencies
"""

import argparse
import contextlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
from audio_deps import require_audio_deps
from json_archiver import find_project_root, resolve_archive_arg, write_archive

SCRIPT_NAME = "audio-deep-analysis"
VERSION = "1.1.0"
HOP_LENGTH = 512


def fail(message):
    """Exit 1 with the JSON failure object on stdout and the reason on stderr.

    Usage errors come here too: exit 2 is kept for missing dependencies, which is
    how the skill's prompts read it.
    """
    print(json.dumps({"script": SCRIPT_NAME, "status": "fail", "error": message}))
    print(message, file=sys.stderr)
    sys.exit(1)


def write_output(text, path):
    """Print the report, or write it to -o (creating its folder); an unwritable path fails with a reason."""
    if not path:
        print(text)
        return
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text + "\n", encoding="utf-8")
    except OSError as exc:
        fail(f"Cannot write {path}: {exc.strerror or exc}; nothing archived")


def window_bounds(n_frames, frames_per_window):
    """[(start_frame, end_frame)] windows that cover every frame.

    A tail of half a window or more is its own window; a shorter tail joins the
    last window (a sliver on its own reads as a false shift); a track shorter
    than one window is one window.
    """
    if n_frames <= 0:
        return []
    full, rest = divmod(n_frames, frames_per_window)
    count = full + (1 if full == 0 or rest * 2 >= frames_per_window else 0)
    bounds = [(i * frames_per_window, (i + 1) * frames_per_window) for i in range(count)]
    bounds[-1] = (bounds[-1][0], n_frames)
    return bounds


def band_folder_for(filepath):
    """Band sub-folder name when the file lives in an audio/{band-slug}/ folder.

    Per-band layout: docs/audio/{band-slug}/Song.mp3 -> "band-slug". A file
    directly in an audio/ folder (legacy flat layout), or anywhere else,
    returns None and archives without a band sub-folder.
    """
    parent = Path(filepath).resolve().parent
    if parent.parent.name == "audio":
        return parent.name
    return None


def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    frac = int((seconds % 1) * 10)
    return f"{m}:{s:02d}.{frac}"


def analyze_chords(y, sr, *, collect=False):
    """Estimate chord/key progression over time using chroma features.

    Returns the per-window data; prints it as a table too unless collect=True.
    """
    import numpy as np

    pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    hop_length = HOP_LENGTH
    window_seconds = 10

    frames_per_window = int(window_seconds * sr / hop_length)
    bounds = window_bounds(chroma.shape[1], frames_per_window)

    results = []

    if not collect:
        print("\n=== KEY/CHORD PROGRESSION ===")
        print(f"{'Time':<15} {'Estimated Key':<15} {'Confidence':>10} {'Dominant Notes'}")
        print("-" * 65)

    for i, (start_frame, end_frame) in enumerate(bounds):
        chunk = chroma[:, start_frame:end_frame]
        avg = np.mean(chunk, axis=1)

        best_corr = -1
        best_key = "Unknown"
        for j in range(12):
            rolled = np.roll(avg, -j)
            maj_corr = np.corrcoef(rolled, major_profile)[0, 1]
            min_corr = np.corrcoef(rolled, minor_profile)[0, 1]
            if maj_corr > best_corr:
                best_corr = maj_corr
                best_key = f"{pitch_classes[j]} major"
            if min_corr > best_corr:
                best_corr = min_corr
                best_key = f"{pitch_classes[j]} minor"

        top_3 = np.argsort(avg)[-3:][::-1]
        dominant = ", ".join([pitch_classes[p] for p in top_3])

        start_time = i * window_seconds
        end_time = (i + 1) * window_seconds
        if end_frame != (i + 1) * frames_per_window:  # the last window ends where the track does
            end_time = round(end_frame * hop_length / sr, 2)

        results.append({
            "time_start": start_time,
            "time_end": end_time,
            "key": best_key,
            "confidence": round(float(best_corr), 3),
            "dominant_notes": [pitch_classes[p] for p in top_3],
        })
        if not collect:
            print(f"{format_time(start_time)}-{format_time(end_time):<8} {best_key:<15} {best_corr:>10.3f} {dominant}")

    return results


def analyze_energy(y, sr, *, collect=False):
    """Show energy/loudness over time.

    Returns the windows and shifts; prints them too unless collect=True.
    """
    import numpy as np

    rms = librosa.feature.rms(y=y)[0]
    hop_length = HOP_LENGTH
    window_seconds = 5
    frames_per_window = int(window_seconds * sr / hop_length)

    max_rms = np.max(rms)
    if max_rms == 0:
        max_rms = 1

    bounds = window_bounds(len(rms), frames_per_window)

    if not collect:
        print("\n=== ENERGY / LOUDNESS ARC ===")
        print(f"{'Time':<15} {'Energy':>7} {'Bar (visual)'}")
        print("-" * 60)

    energies = []
    windows = []
    for i, (start, end) in enumerate(bounds):
        avg = np.mean(rms[start:end])
        pct = int((avg / max_rms) * 100)
        energies.append(pct)

        start_time = i * window_seconds
        windows.append({
            "time": start_time,
            "energy_pct": pct,
        })
        if not collect:
            bar = "\u2588" * (pct // 2)
            print(f"{format_time(start_time):<15} {pct:>5}%  {bar}")

    # Detect significant energy shifts
    shifts = []
    if not collect:
        print("\n--- Energy Shifts (>20% change) ---")

    found = False
    for i in range(1, len(energies)):
        diff = energies[i] - energies[i-1]
        if abs(diff) > 20:
            t = i * window_seconds
            direction = "UP" if diff > 0 else "DOWN"
            shifts.append({
                "time": t,
                "direction": direction,
                "change_pct": abs(diff),
                "from_pct": energies[i-1],
                "to_pct": energies[i],
            })
            if not collect:
                print(f"  {format_time(t)} \u2014 energy {direction} {abs(diff)}% ({energies[i-1]}% \u2192 {energies[i]}%)")
            found = True

    if not collect and not found:
        print("  No dramatic energy shifts detected (all changes < 20%)")

    return {"windows": windows, "shifts": shifts}


def analyze_sections(y, sr, *, collect=False):
    """Detect section boundaries using spectral novelty.

    Returns the boundaries; prints them too unless collect=True.
    """
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    bounds = librosa.segment.agglomerative(mfcc, k=8)
    bound_times = librosa.frames_to_time(bounds, sr=sr)

    results = []

    if not collect:
        print("\n=== SECTION BOUNDARIES (spectral novelty) ===")
        print("Detected section changes at:")

    for i, t in enumerate(bound_times):
        if t > 0.5:  # Skip very start
            results.append({
                "section": i + 1,
                "time": round(float(t), 2),
            })
            if not collect:
                print(f"  Section {i+1}: {format_time(t)}")

    return results


def analyze_spectral_balance(y, sr, *, collect=False):
    """Show low vs mid vs high frequency balance over time.

    Returns the per-window data; prints it too unless collect=True.
    """
    import numpy as np

    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)

    low_mask = freqs < 250
    mid_mask = (freqs >= 250) & (freqs < 2000)
    high_mask = freqs >= 2000

    window_seconds = 10
    hop_length = HOP_LENGTH
    frames_per_window = int(window_seconds * sr / hop_length)
    bounds = window_bounds(S.shape[1], frames_per_window)

    if not collect:
        print("\n=== SPECTRAL BALANCE (low/mid/high) ===")
        print(f"{'Time':<15} {'Low(<250Hz)':>12} {'Mid(250-2k)':>12} {'High(>2kHz)':>12} {'Balance'}")
        print("-" * 70)

    results = []
    for i, (start, end) in enumerate(bounds):
        chunk = S[:, start:end]
        low = np.mean(chunk[low_mask, :])
        mid = np.mean(chunk[mid_mask, :])
        high = np.mean(chunk[high_mask, :])

        total = low + mid + high
        if total == 0:
            total = 1
        l_pct = int(low / total * 100)
        m_pct = int(mid / total * 100)
        h_pct = int(high / total * 100)

        dominant = "BASS-heavy" if l_pct > 45 else "MID-heavy" if m_pct > 50 else "balanced"

        start_time = i * window_seconds
        results.append({
            "time": start_time,
            "low_pct": l_pct,
            "mid_pct": m_pct,
            "high_pct": h_pct,
            "balance": dominant,
        })
        if not collect:
            print(f"{format_time(start_time):<15} {l_pct:>10}% {m_pct:>10}% {h_pct:>10}%  {dominant}")

    return results


def format_json_output(filepath, duration, energy_data, chord_data, section_data, spectral_data):
    """Build structured JSON output."""
    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "metrics": {
            "file": os.path.basename(filepath),
            "duration_seconds": round(duration, 2),
            "energy_arc": energy_data,
            "chord_progression": chord_data,
            "section_boundaries": section_data,
            "spectral_balance": spectral_data,
        },
        "findings": [],
        "summary": {"total": 0},
    }


def main():
    require_audio_deps()

    import librosa as _librosa  # noqa: E402
    import numpy as np  # noqa: E402, F401

    # Make librosa available to module-level helper functions
    globals()["librosa"] = _librosa

    parser = argparse.ArgumentParser(
        description="Deep single-track audio analysis — energy, chords, sections, spectral balance.",
    )
    parser.add_argument(
        "audio_file",
        help="Path to the audio file to analyze",
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
            "Persist full JSON output to a per-song archive. "
            "With no path: writes to docs/audio-analysis/songs/[<band-slug>/]<song-slug>.json "
            "(band sub-folder when the file lives in docs/audio/<band-slug>/). "
            "Pass an explicit path to override. Default: ON."
        ),
    )
    parser.add_argument(
        "--no-archive", dest="archive", action="store_const", const=None,
        help="Skip writing the JSON archive.",
    )
    parser.error = lambda message: fail(f"usage: {message}")
    args = parser.parse_args()

    filepath = args.audio_file
    if not os.path.isfile(filepath):
        fail(f"Audio file not found: {filepath}")

    text = args.output_format == "text"
    try:
        y, sr = _librosa.load(filepath, sr=22050)
        duration = _librosa.get_duration(y=y, sr=sr)
        # Text mode prints as it measures: capture it, so -o gets the report and
        # the same measurements still reach the archive.
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            if text:
                print(f"Loading: {os.path.basename(filepath)}")
                print(f"Duration: {int(duration//60)}:{int(duration%60):02d}\n")
            energy_data = analyze_energy(y, sr, collect=not text)
            chord_data = analyze_chords(y, sr, collect=not text)
            section_data = analyze_sections(y, sr, collect=not text)
            spectral_data = analyze_spectral_balance(y, sr, collect=not text)
    except Exception as exc:  # corrupt, empty or too-short audio: a reason, not a traceback
        fail(f"Could not analyze {filepath}: {type(exc).__name__}: {exc}")

    result = format_json_output(filepath, duration, energy_data, chord_data, section_data, spectral_data)
    write_output(captured.getvalue().rstrip("\n") if text else json.dumps(result, indent=2), args.output)

    # Per-song JSON archive (default ON unless --no-archive), in either format
    song_slug = os.path.splitext(os.path.basename(filepath))[0]
    band = band_folder_for(filepath)
    archive_id = f"{band}/{song_slug}" if band else song_slug
    archive_target = resolve_archive_arg("songs", archive_id, args.archive, find_project_root(filepath))
    if archive_target is not None:
        res = write_archive(archive_target, result)
        print(f"  ARCHIVED: {res['path']} ({res['bytes_written']} bytes)", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
