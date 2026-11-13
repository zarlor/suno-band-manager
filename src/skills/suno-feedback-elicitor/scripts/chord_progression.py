#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"  # librosa>=1.0 requires Python 3.12
# dependencies = ["librosa>=1.0", "numpy>=2.1"]
# ///
"""Chord/key progression analysis -- shows estimated chords over time
using chroma features with beat-synchronized analysis for cleaner results.

Measures come from Beat This! downbeats (real bar lines, via beat_grid.py) when
the PyTorch audio tools are turned on in the module config
(`pytorch_audio_tools`), otherwise from librosa beats grouped in fours;
`--tempo-source` overrides the choice for one run.

Usage:
    uv run chord_progression.py <audio-file> [options]

    # Analyze a single track
    uv run chord_progression.py track.mp3

    # JSON output to file
    uv run chord_progression.py track.mp3 --format json -o results.json

Either format honours -o.

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
from tempo_source import (SOURCE_LABELS, add_tempo_source_arg, beat_this_readings, slow_prior_fields,
                          resolve_tempo_source, usable)

SCRIPT_NAME = "chord-progression"
VERSION = "1.1.0"
TOO_FEW_BEATS = "Too few beats for measure analysis"


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
        fail(f"Cannot write {path}: {exc.strerror or exc}")

PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def _build_chord_templates():
    """Build chord templates. Requires numpy, so called after dependency check."""
    import numpy as np

    templates = {}
    for i, note in enumerate(PITCH_CLASSES):
        # Major triad: root, major 3rd, perfect 5th
        major = np.zeros(12)
        major[i] = 1.0
        major[(i + 4) % 12] = 0.8
        major[(i + 7) % 12] = 0.8
        templates[f"{note}"] = major

        # Minor triad: root, minor 3rd, perfect 5th
        minor = np.zeros(12)
        minor[i] = 1.0
        minor[(i + 3) % 12] = 0.8
        minor[(i + 7) % 12] = 0.8
        templates[f"{note}m"] = minor

        # Power chord (5th): root, perfect 5th
        power = np.zeros(12)
        power[i] = 1.0
        power[(i + 7) % 12] = 0.9
        templates[f"{note}5"] = power

    return templates


def match_chord(chroma_vector, chord_templates):
    """Match a chroma vector to the best chord template."""
    import numpy as np

    best_score = -1
    best_chord = "?"
    norm = np.linalg.norm(chroma_vector)
    if norm < 0.001:
        return "silence", 0.0

    chroma_norm = chroma_vector / norm

    for name, template in chord_templates.items():
        t_norm = template / np.linalg.norm(template)
        score = np.dot(chroma_norm, t_norm)
        if score > best_score:
            best_score = score
            best_chord = name

    return best_chord, best_score


def measure_spans(y, sr, filepath, tempo_source="librosa"):
    """(bpm, [(start_frame, end_frame, start_time)], source used, basis) for the measures chords are read over.

    Beat This!, when it's the tempo source and read the track, gives real bar
    lines from its downbeats; librosa's beats are grouped in fours.
    """
    import numpy as np

    if tempo_source == "beat-this":
        readings = beat_this_readings([filepath], include_beats=True)
        reading = readings[0] if readings else None
        if usable(reading) and len(reading.get("downbeats_s") or []) > 1:
            bars = np.array(reading["downbeats_s"])
            frames = librosa.time_to_frames(bars, sr=sr)
            spans = [(int(a), int(b), float(t)) for a, b, t in zip(frames, frames[1:], bars)]
            return float(reading["bpm"]), spans, "beat-this", "downbeats"
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)
    spans = [(int(beats[i]), int(beats[min(i + 4, len(beats) - 1)]), float(beat_times[i]))
             for i in range(0, len(beats) - 4, 4)]
    return float(np.atleast_1d(tempo)[0]), spans, "librosa", "4-beat groups"


def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def analyze_chords_text(filepath, chord_templates, tempo_source="librosa"):
    """Run chord analysis with text output (original format)."""
    import numpy as np

    print(f"Loading: {os.path.basename(filepath)}")
    y, sr = librosa.load(filepath, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)
    print(f"Duration: {format_time(duration)}\n")

    # Measure-synchronous chroma for cleaner chord detection
    tempo, spans, source_used, basis = measure_spans(y, sr, filepath, tempo_source)
    print(f"Measures: {basis} ({SOURCE_LABELS[source_used]})")
    slow = slow_prior_fields(y, sr, tempo) if source_used == "librosa" else {}
    if slow:
        print(f"Tempo: {tempo:.1f} BPM; slow-prior reading (start_bpm=80): {slow['bpm_librosa_slow_prior']} "
              f"({slow['librosa_prior_relation']})")
        if slow.get("tempo_note"):
            print(slow["tempo_note"])
    print()

    # Use CQT chroma (better for music)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

    # Aggregate chroma by measures (every 4 beats)
    print(f"{'Time':<10} {'Chord':<8} {'Conf':>5}  {'Chroma Profile'}")
    print("-" * 70)

    prev_chord = None
    chord_sequence = []

    for start_frame, end_frame, start_time in spans:

        if start_frame >= chroma.shape[1] or end_frame >= chroma.shape[1]:
            break

        measure_chroma = np.mean(chroma[:, start_frame:end_frame], axis=1)
        chord, conf = match_chord(measure_chroma, chord_templates)

        # Show top 3 pitch classes
        top_3_idx = np.argsort(measure_chroma)[-3:][::-1]
        top_3 = [PITCH_CLASSES[p] for p in top_3_idx]

        marker = " <<<" if chord != prev_chord and prev_chord is not None else ""
        print(f"{format_time(start_time):<10} {chord:<8} {conf:>5.2f}  [{', '.join(top_3)}]{marker}")

        chord_sequence.append((start_time, chord, conf))
        prev_chord = chord

    if not chord_sequence:
        print(f"{TOO_FEW_BEATS}: no measure could be read (an ambient, silent or very short track).")

    # Summary: chord changes
    print(f"\n{'='*50}")
    print("CHORD CHANGE SUMMARY")
    print("=" * 50)

    changes = []
    for i in range(1, len(chord_sequence)):
        if chord_sequence[i][1] != chord_sequence[i-1][1]:
            changes.append((
                chord_sequence[i][0],
                chord_sequence[i-1][1],
                chord_sequence[i][1]
            ))

    if changes:
        print(f"{len(changes)} chord changes detected:\n")
        for t, from_c, to_c in changes:
            print(f"  {format_time(t)} \u2014 {from_c} \u2192 {to_c}")
    else:
        print("No chord changes detected (single chord throughout)")

    # Key center summary
    print(f"\n{'='*50}")
    print("KEY CENTER SUMMARY (by section)")
    print("=" * 50)

    section_size = 30
    num_sections = int(np.ceil(duration / section_size))

    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    for s in range(num_sections):
        start_sec = s * section_size
        end_sec = min((s + 1) * section_size, duration)
        start_frame = int(start_sec * sr / 512)
        end_frame = int(end_sec * sr / 512)
        end_frame = min(end_frame, chroma.shape[1])

        if start_frame >= end_frame:
            break

        section_chroma = np.mean(chroma[:, start_frame:end_frame], axis=1)

        best_corr = -1
        best_key = "Unknown"
        for i in range(12):
            rolled = np.roll(section_chroma, -i)
            for profile, mode in [(major_profile, "major"), (minor_profile, "minor")]:
                corr = np.corrcoef(rolled, profile)[0, 1]
                if corr > best_corr:
                    best_corr = corr
                    best_key = f"{PITCH_CLASSES[i]} {mode}"

        print(f"  {format_time(start_sec)}-{format_time(end_sec)}: {best_key} (conf: {best_corr:.3f})")


def analyze_chords_json(filepath, chord_templates, tempo_source="librosa"):
    """Run chord analysis and return structured data for JSON output."""
    import numpy as np

    y, sr = librosa.load(filepath, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)

    tempo, spans, source_used, basis = measure_spans(y, sr, filepath, tempo_source)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

    prev_chord = None
    chord_sequence = []
    measures = []

    for start_frame, end_frame, start_time in spans:

        if start_frame >= chroma.shape[1] or end_frame >= chroma.shape[1]:
            break

        measure_chroma = np.mean(chroma[:, start_frame:end_frame], axis=1)
        chord, conf = match_chord(measure_chroma, chord_templates)

        top_3_idx = np.argsort(measure_chroma)[-3:][::-1]
        top_3 = [PITCH_CLASSES[p] for p in top_3_idx]

        measures.append({
            "time": round(start_time, 2),
            "chord": chord,
            "confidence": round(float(conf), 3),
            "dominant_notes": top_3,
            "is_change": chord != prev_chord and prev_chord is not None,
        })

        chord_sequence.append((start_time, chord, conf))
        prev_chord = chord

    # Chord changes
    transitions = []
    for i in range(1, len(chord_sequence)):
        if chord_sequence[i][1] != chord_sequence[i-1][1]:
            transitions.append({
                "time": round(chord_sequence[i][0], 2),
                "from": chord_sequence[i-1][1],
                "to": chord_sequence[i][1],
            })

    # Key centers by section
    section_size = 30
    num_sections = int(np.ceil(duration / section_size))
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    key_centers = []
    for s in range(num_sections):
        start_sec = s * section_size
        end_sec = min((s + 1) * section_size, duration)
        sf = int(start_sec * sr / 512)
        ef = min(int(end_sec * sr / 512), chroma.shape[1])

        if sf >= ef:
            break

        section_chroma = np.mean(chroma[:, sf:ef], axis=1)
        best_corr = -1
        best_key = "Unknown"
        for i in range(12):
            rolled = np.roll(section_chroma, -i)
            for profile, mode in [(major_profile, "major"), (minor_profile, "minor")]:
                corr = np.corrcoef(rolled, profile)[0, 1]
                if corr > best_corr:
                    best_corr = corr
                    best_key = f"{PITCH_CLASSES[i]} {mode}"

        key_centers.append({
            "time_start": start_sec,
            "time_end": round(end_sec, 2),
            "key": best_key,
            "confidence": round(float(best_corr), 3),
        })

    tempo_val = float(tempo[0]) if hasattr(tempo, '__len__') else float(tempo)

    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "metrics": {
            "file": os.path.basename(filepath),
            "duration_seconds": round(duration, 2),
            "bpm": round(tempo_val, 1),
            "tempo_source": source_used,
            **(slow_prior_fields(y, sr, tempo_val) if source_used == "librosa" else {}),
            "measure_basis": basis,
            # No measure read (ambient, silent or very short track): say so, so zero isn't taken as a result.
            **({} if measures else {"note": TOO_FEW_BEATS}),
            "total_measures_analyzed": len(measures),
            "chord_changes": len(transitions),
            "measures": measures,
            "transitions": transitions,
            "key_centers": key_centers,
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

    chord_templates = _build_chord_templates()

    parser = argparse.ArgumentParser(
        description="Beat-synchronized chord/key progression analysis.",
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
    add_tempo_source_arg(parser)
    parser.error = lambda message: fail(f"usage: {message}")
    args = parser.parse_args()

    if not os.path.isfile(args.audio_file):
        fail(f"Audio file not found: {args.audio_file}")

    source = resolve_tempo_source(args.tempo_source)
    try:
        if args.output_format == "text":
            # The text report prints as it measures: capture it so -o gets it too.
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                analyze_chords_text(args.audio_file, chord_templates, source)
            output = captured.getvalue().rstrip("\n")
        else:
            output = json.dumps(analyze_chords_json(args.audio_file, chord_templates, source), indent=2)
    except Exception as exc:  # corrupt, empty or too-short audio: a reason, not a traceback
        fail(f"Could not analyze {args.audio_file}: {type(exc).__name__}: {exc}")

    write_output(output, args.output)
    sys.exit(0)


if __name__ == "__main__":
    main()
