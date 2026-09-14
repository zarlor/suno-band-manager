#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["librosa>=1.0", "numpy>=2.1"]
# ///
"""Detailed tempo analysis -- shows BPM over time to detect tempo changes
and off-beats.

Beats come from Beat This! (beat-grid.py) when the PyTorch audio tools are
turned on in the module config (`pytorch_audio_tools`), otherwise from librosa;
`--tempo-source` overrides the choice for one run.

Usage:
    uv run tempo-detail.py <audio-file> [options]

    # Analyze a single track
    uv run tempo-detail.py track.mp3

    # JSON output to file
    uv run tempo-detail.py track.mp3 --format json -o results.json

Exit codes:
  0 = success
  1 = invalid arguments or runtime error
  2 = missing dependencies
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from audio_deps import require_audio_deps
from tempo_source import SOURCE_LABELS, add_tempo_source_arg, beat_this_readings, resolve_tempo_source, usable

SCRIPT_NAME = "tempo-detail"
VERSION = "1.1.0"


def get_beats(y, sr, filepath, tempo_source="librosa"):
    """(overall BPM, beat times in seconds, source used).

    Beat This! beats when it's the tempo source and read the track; otherwise librosa's.
    """
    import numpy as np

    if tempo_source == "beat-this":
        readings = beat_this_readings([filepath], include_beats=True)
        reading = readings[0] if readings else None
        if usable(reading) and reading.get("beats_s"):
            return float(reading["bpm"]), np.array(reading["beats_s"]), "beat-this"
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    return float(np.atleast_1d(tempo)[0]), librosa.frames_to_time(beats, sr=sr), "librosa"


STABILITY_TEXT = {"steady": "steady", "slight_variation": "slight variation", "tempo_change": "TEMPO CHANGE"}


def window_stats(beat_times, local_bpms, duration, robust, window_size=15):
    """Per-window tempo rows.

    robust (Beat This!): the centre is the median and stability is the share of
    beats within 10% of it, so one stray beat doesn't flag a tempo change.
    Otherwise (librosa): the mean, with stability from the standard deviation.
    """
    import numpy as np

    rows = []
    for i in range(int(np.ceil(duration / window_size))):
        start = i * window_size
        end = min((i + 1) * window_size, duration)
        mask = (beat_times[:-1] >= start) & (beat_times[:-1] < end)
        w = local_bpms[mask]
        if len(w) == 0:
            continue
        std = float(np.std(w))
        if robust:
            center = float(np.median(w))
            share = float(np.mean(np.abs(w / center - 1) <= 0.10))
            stability = "steady" if share >= 0.9 else "slight_variation" if share >= 0.75 else "tempo_change"
        else:
            center = float(np.mean(w))
            stability = "steady" if std < 5 else "slight_variation" if std < 15 else "tempo_change"
        rows.append({
            "time_start": start,
            "time_end": round(end, 2),
            ("median_bpm" if robust else "avg_bpm"): round(center, 1),
            "min_bpm": round(float(np.min(w)), 1),
            "max_bpm": round(float(np.max(w)), 1),
            "std_bpm": round(std, 2),
            "stability": stability,
        })
    return rows


def find_tempo_events(beat_times, local_bpms, windows, robust):
    """Tempo events. robust (Beat This!): a window median moving 10%+ from the last window's.
    Otherwise (librosa): a beat-to-beat jump of more than 20 BPM."""
    if robust:
        return [
            {"time": b["time_start"], "from_bpm": a["median_bpm"], "to_bpm": b["median_bpm"],
             "delta": round(abs(b["median_bpm"] - a["median_bpm"]), 1)}
            for a, b in zip(windows, windows[1:])
            if abs(b["median_bpm"] / a["median_bpm"] - 1) >= 0.10
        ]
    events = []
    for i in range(len(local_bpms) - 1):
        diff = abs(local_bpms[i + 1] - local_bpms[i])
        if diff > 20:
            events.append({
                "time": round(float(beat_times[i + 1]), 2),
                "from_bpm": round(float(local_bpms[i]), 1),
                "to_bpm": round(float(local_bpms[i + 1]), 1),
                "delta": round(float(diff), 1),
            })
    return events


def analyze_tempo_text(filepath, tempo_source="librosa"):
    """Run tempo analysis with text output (original format)."""
    import numpy as np

    print(f"Loading: {filepath}")
    y, sr = librosa.load(filepath, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)
    print(f"Duration: {int(duration//60)}:{int(duration%60):02d}")

    # Overall tempo and beat times
    tempo_val, beat_times, source_used = get_beats(y, sr, filepath, tempo_source)
    print(f"\nOverall BPM: {tempo_val:.1f} ({SOURCE_LABELS[source_used]})")

    if len(beat_times) < 4:
        print("Too few beats detected for detailed analysis.")
        return

    # Inter-beat intervals
    ibis = np.diff(beat_times)
    local_bpms = 60.0 / ibis

    # Tempo in ~15-second windows
    robust = source_used == "beat-this"
    rows = window_stats(beat_times, local_bpms, duration, robust)
    center_label = "Med BPM" if robust else "Avg BPM"
    print(f"\n{'Time Window':<20} {center_label:>8} {'Min BPM':>8} {'Max BPM':>8} {'Stability':>10}")
    print("-" * 60)
    for row in rows:
        start, end = row["time_start"], row["time_end"]
        time_label = f"{int(start//60)}:{int(start%60):02d}-{int(end//60)}:{int(end%60):02d}"
        center = row.get("median_bpm", row.get("avg_bpm"))
        print(f"{time_label:<20} {center:>8.1f} {row['min_bpm']:>8.1f} {row['max_bpm']:>8.1f} "
              f"{STABILITY_TEXT[row['stability']]:>10}")

    # Tempo events
    print("\n--- Potential Tempo Events ---")
    events = find_tempo_events(beat_times, local_bpms, rows, robust)
    for e in events:
        t = e["time"]
        print(f"  {int(t//60)}:{int(t%60):02d}.{int((t%1)*10)} \u2014 BPM jumps from {e['from_bpm']:.0f} "
              f"to {e['to_bpm']:.0f} (\u0394{e['delta']:.0f})")
    if not events:
        print("  No significant tempo shifts detected ("
              + ("15 s window medians within 10%" if robust else "all beat-to-beat changes < 20 BPM") + ")")

    # Odd time / irregular beat detection
    print("\n--- Beat Regularity ---")
    median_ibi = np.median(ibis)
    irregular = []
    for i, ibi in enumerate(ibis):
        ratio = ibi / median_ibi
        if ratio < 0.75 or ratio > 1.33:
            t = beat_times[i]
            pct = (ratio - 1) * 100
            irregular.append((t, ratio, pct))

    if irregular:
        print(f"  {len(irregular)} irregular beats detected (>33% deviation from median):")
        for t, ratio, pct in irregular[:15]:
            label = "shorter" if ratio < 1 else "longer"
            print(f"    {int(t//60)}:{int(t%60):02d}.{int((t%1)*10)} \u2014 beat is {abs(pct):.0f}% {label} than expected")
    else:
        print("  All beats within normal variance \u2014 consistent 4/4 feel")


def analyze_tempo_json(filepath, tempo_source="librosa"):
    """Run tempo analysis and return structured data for JSON output."""
    import numpy as np

    y, sr = librosa.load(filepath, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)

    tempo_val, beat_times, source_used = get_beats(y, sr, filepath, tempo_source)

    if len(beat_times) < 4:
        return {
            "script": SCRIPT_NAME,
            "version": VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "pass",
            "metrics": {
                "file": str(Path(filepath).name),
                "duration_seconds": round(duration, 2),
                "bpm_overall": round(tempo_val, 1),
                "tempo_source": source_used,
                "beats_detected": len(beat_times),
                "note": "Too few beats for detailed analysis",
            },
            "findings": [],
            "summary": {"total": 0},
        }

    ibis = np.diff(beat_times)
    local_bpms = 60.0 / ibis

    # Tempo windows and events
    robust = source_used == "beat-this"
    windows = window_stats(beat_times, local_bpms, duration, robust)
    tempo_events = find_tempo_events(beat_times, local_bpms, windows, robust)

    # Beat regularity
    median_ibi = float(np.median(ibis))
    irregular_beats = []
    for i, ibi in enumerate(ibis):
        ratio = ibi / median_ibi
        if ratio < 0.75 or ratio > 1.33:
            t = float(beat_times[i])
            pct = (ratio - 1) * 100
            irregular_beats.append({
                "time": round(t, 2),
                "ratio": round(float(ratio), 3),
                "deviation_pct": round(float(abs(pct)), 1),
                "direction": "shorter" if ratio < 1 else "longer",
            })

    return {
        "script": SCRIPT_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "metrics": {
            "file": str(Path(filepath).name),
            "duration_seconds": round(duration, 2),
            "bpm_overall": round(tempo_val, 1),
            "tempo_source": source_used,
            "beats_detected": len(beat_times),
            "median_inter_beat_interval": round(median_ibi, 4),
            "tempo_windows": windows,
            "tempo_events": tempo_events,
            "irregular_beats": irregular_beats,
            "irregular_beat_count": len(irregular_beats),
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
        description="Detailed tempo analysis -- BPM over time, stability, beat regularity.",
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
    args = parser.parse_args()

    if not Path(args.audio_file).is_file():
        print(f"Audio file not found: {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    source = resolve_tempo_source(args.tempo_source)
    if args.output_format == "text":
        analyze_tempo_text(args.audio_file, source)
    else:
        result = analyze_tempo_json(args.audio_file, source)
        output = json.dumps(result, indent=2)

        if args.output:
            Path(args.output).write_text(output + "\n")
        else:
            print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
