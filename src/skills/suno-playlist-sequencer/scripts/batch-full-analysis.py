#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"  # librosa>=1.0 requires Python 3.12
# dependencies = ["librosa>=1.0", "numpy>=2.1"]
# ///
"""
Batch full analysis -- tempo stability, energy arc, section boundaries,
and spectral balance for every track in a catalog directory.

Outputs a summary report in JSON or Markdown text format.

Tempo and beat stability come from Beat This! (beat-grid.py) when the PyTorch
audio tools are turned on in the module config (`pytorch_audio_tools`),
otherwise from librosa; `--tempo-source` overrides the choice for one run.
With librosa, each track also gets a second reading at a slow starting tempo
(`bpm_librosa_slow_prior`, start_bpm=80) and how the two relate
(`librosa_prior_relation`: agree / double / other; double = a likely halftime
ambiguity, for the ear to settle).

Where the archive and companion go depends on the folder scanned, so a
per-band pass never overwrites the catalog-wide report:
  - the catalog root (an `audio/` folder, default docs/audio):
    audio-analysis/catalog/<date>-deep.json and catalog-analysis-report.md,
    both beside that `audio/` folder;
  - a band folder (audio/<band-slug>/) or any other folder:
    audio-analysis/catalog/<date>-deep-<folder-slug>.json and
    <folder-slug>-catalog-analysis-report.md.
The stdout JSON names both under `artifacts`, lists tracks that failed under
`failed[]` (status `partial` when some did), and says why tempo fell back from
Beat This! to librosa in `tempo_source_note`.

Exit codes:
  0 = analysis ran (status ok, or partial with failed[] listed)
  1 = invalid arguments, no audio files found, or every track failed (nothing written)
  2 = missing dependencies (librosa/numpy)
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
from audio_deps import require_audio_deps
from companion_writer import update_companion
from json_archiver import _slugify, write_archive
from tempo_source import (SOURCE_LABELS, BeatThisUnavailable, add_tempo_source_arg, bpm_cell, feel_sections,
                          librosa_tempo_pair, resolve_tempo_source, run_beat_grid, source_summary, usable,
                          window_tempos, windowed_stability)

SCRIPT_NAME = "batch-full-analysis"


def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def analyze_track(filepath, beat_reading=None):
    """Full analysis of a single track. Returns a dict of results.

    `beat_reading` is the track's Beat This! reading (with beat times), when that's the tempo source.
    """
    import librosa
    import numpy as np

    filename = os.path.basename(filepath)
    results = {'file': filename}

    try:
        y, sr = librosa.load(filepath, sr=22050)
        duration = librosa.get_duration(y=y, sr=sr)
        results['duration'] = duration

        # === BPM & TEMPO STABILITY ===
        # Beat This! beats when it's the tempo source and read the track; otherwise librosa's.
        if usable(beat_reading) and beat_reading.get('beats_s'):
            bpm = float(beat_reading['bpm'])
            beat_times = np.array(beat_reading['beats_s'])
            results['tempo_source'] = 'beat-this'
        else:
            tempo_overall, beats = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(np.atleast_1d(tempo_overall)[0])
            beat_times = librosa.frames_to_time(beats, sr=sr)
            results['tempo_source'] = 'librosa'
            # A second, slow-prior reading (start_bpm=80), reported only; stability uses the default beats.
            pair = librosa_tempo_pair(y, sr, default_bpm=bpm)
            results['bpm_librosa_slow_prior'] = pair['bpm_librosa_slow_prior']
            results['librosa_prior_relation'] = pair['librosa_prior_relation']
        results['bpm'] = round(bpm, 1)
        if results['tempo_source'] == 'beat-this':
            # Beat This!'s raw beats include the odd stray detection, so judge stability by
            # 15 s window medians rather than beat-to-beat spread, and name the feel changes.
            windows = window_tempos(beat_times)
            results['bpm_stability'], results['bpm_range'] = windowed_stability(windows)
            results['feel_sections'] = feel_sections(windows, bpm)
        elif len(beat_times) > 3:
            ibis = np.diff(beat_times)
            local_bpms = 60.0 / ibis
            bpm_std = np.std(local_bpms)
            results['bpm_stability'] = "steady" if bpm_std < 5 else "slight variation" if bpm_std < 15 else "TEMPO CHANGES"
            results['bpm_range'] = (round(np.percentile(local_bpms, 10), 0), round(np.percentile(local_bpms, 90), 0))
        else:
            results['bpm_stability'] = "too few beats"
            results['bpm_range'] = (0, 0)

        # === KEY ===
        pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_avg = np.mean(chroma, axis=1)
        best_corr = -1
        best_key = "Unknown"
        for i in range(12):
            rolled = np.roll(chroma_avg, -i)
            for profile, mode in [(major_profile, "major"), (minor_profile, "minor")]:
                corr = np.corrcoef(rolled, profile)[0, 1]
                if corr > best_corr:
                    best_corr = corr
                    best_key = f"{pitch_classes[i]} {mode}"
        results['key'] = best_key
        results['key_conf'] = round(best_corr, 3)

        # === ENERGY ARC ===
        rms = librosa.feature.rms(y=y)[0]
        hop_length = 512
        max_rms = np.max(rms) if np.max(rms) > 0 else 1

        # 5-second windows for energy
        window_frames = int(5 * sr / hop_length)
        num_windows = len(rms) // window_frames
        energies = []
        for i in range(num_windows):
            avg = np.mean(rms[i*window_frames:(i+1)*window_frames])
            pct = int((avg / max_rms) * 100)
            energies.append(pct)

        results['energy_min'] = min(energies) if energies else 0
        results['energy_max'] = max(energies) if energies else 0
        results['energy_range'] = results['energy_max'] - results['energy_min']

        # Detect significant energy shifts
        shifts = []
        for i in range(1, len(energies)):
            diff = energies[i] - energies[i-1]
            if abs(diff) > 20:
                t = i * 5
                direction = "UP" if diff > 0 else "DOWN"
                shifts.append(f"{format_time(t)} {direction} {abs(diff)}%")
        results['energy_shifts'] = shifts
        results['energy_profile'] = energies

        # Classify dynamic character
        if results['energy_range'] < 20:
            results['dynamic_character'] = "FLAT — minimal dynamics"
        elif results['energy_range'] < 40:
            results['dynamic_character'] = "MODERATE — some dynamic range"
        elif len(shifts) >= 3:
            results['dynamic_character'] = "HIGHLY DYNAMIC — big swings"
        else:
            results['dynamic_character'] = "DYNAMIC — wide range"

        # === SPECTRAL BALANCE ===
        S = np.abs(librosa.stft(y))
        freqs = librosa.fft_frequencies(sr=sr)
        low_mask = freqs < 250
        mid_mask = (freqs >= 250) & (freqs < 2000)
        high_mask = freqs >= 2000

        low = np.mean(S[low_mask, :])
        mid = np.mean(S[mid_mask, :])
        high = np.mean(S[high_mask, :])
        total = low + mid + high
        if total == 0:
            total = 1
        results['spectral_low'] = int(low / total * 100)
        results['spectral_mid'] = int(mid / total * 100)
        results['spectral_high'] = int(high / total * 100)

        # === SECTION BOUNDARIES ===
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        n_sections = min(8, max(3, int(duration / 30)))  # Scale sections by duration
        bounds = librosa.segment.agglomerative(mfcc, k=n_sections)
        bound_times = librosa.frames_to_time(bounds, sr=sr)
        results['sections'] = [format_time(t) for t in bound_times if t > 0.5]

    except Exception as e:
        results['error'] = str(e)

    return results


def build_report(all_results, tempo_note=None):
    """The standard module JSON report as a dict."""
    tracks = []
    for r in all_results:
        if 'error' in r:
            tracks.append({
                'file': r['file'],
                'status': 'error',
                'error': r['error'],
            })
            continue
        tracks.append({
            'file': r['file'],
            'duration': round(r['duration'], 1),
            'duration_display': format_time(r['duration']),
            'bpm': r['bpm'],
            'bpm_stability': r['bpm_stability'],
            'bpm_range': list(r['bpm_range']),
            'tempo_source': r.get('tempo_source', 'librosa'),
            **({k: r[k] for k in ('bpm_librosa_slow_prior', 'librosa_prior_relation') if k in r}),
            **({'feel_sections': r['feel_sections']} if 'feel_sections' in r else {}),
            'key': r['key'],
            'key_confidence': r['key_conf'],
            'dynamic_character': r['dynamic_character'],
            'energy': {
                'min': r['energy_min'],
                'max': r['energy_max'],
                'range': r['energy_range'],
                'shifts': r['energy_shifts'],
                'profile': r['energy_profile'],
            },
            'spectral_balance': {
                'low_pct': r['spectral_low'],
                'mid_pct': r['spectral_mid'],
                'high_pct': r['spectral_high'],
            },
            'sections': r['sections'],
        })

    failed = [{'file': r['file'], 'error': r['error']} for r in all_results if 'error' in r]
    return {
        'script': 'batch-full-analysis',
        'status': 'partial' if failed else 'ok',
        'track_count': len(all_results),
        'analyzed_count': len(all_results) - len(failed),
        'failed': failed,
        'tempo_source': source_summary(all_results),
        'tempo_source_note': tempo_note,
        'tracks': tracks,
    }


def format_json(all_results, tempo_note=None):
    """Format results as standard module JSON."""
    return json.dumps(build_report(all_results, tempo_note), indent=2)


def format_text(all_results):
    """Format results as a Markdown report."""
    lines = []
    lines.append("# Catalog Audio Analysis\n")
    lines.append("## Summary Table\n")
    lines.append("| Track | Duration | BPM | Stability | Key | Dyn Range | Character |")
    lines.append("|-------|----------|-----|-----------|-----|-----------|----------|")
    for r in all_results:
        if 'error' in r:
            continue
        dur = format_time(r['duration'])
        bpm = bpm_cell(r['bpm'], r.get('bpm_librosa_slow_prior'), r.get('librosa_prior_relation'))
        lines.append(
            f"| {r['file'].replace('.mp3','')} | {dur} | {bpm} "
            f"| {r['bpm_stability']} | {r['key']} | {r['energy_range']}% "
            f"| {r['dynamic_character']} |"
        )

    lines.append(f"\n_Tempo and stability: {SOURCE_LABELS[source_summary(all_results)]}._")
    if any(r.get('librosa_prior_relation') not in (None, 'agree') for r in all_results if 'error' not in r):
        lines.append("_BPM a / b = librosa's default reading / its reading with a slow starting tempo "
                     "(start_bpm=80). (halftime?) = about 2x apart, a likely halftime ambiguity: the ear "
                     "(or Beat This!) decides which is felt._")

    shifted = [r for r in all_results if 'error' not in r and r.get('feel_sections')]
    if shifted:
        lines.append("\n## Feel Sections (Beat This!, 15 s windows)\n")
        lines.append("_Stretches whose tempo departs from the track's by 10% or more. Descriptive: the ear decides the felt pulse._\n")
        for r in shifted:
            parts = [f"{format_time(f['start'])}–{format_time(f['end'])} {f['feel']} (~{f['bpm']:.0f})"
                     for f in r['feel_sections']]
            lines.append(f"- **{r['file'].replace('.mp3','')}** ({r['bpm']}): " + "; ".join(parts))

    lines.append("\n## Energy Shifts (>20% jumps)\n")
    for r in all_results:
        if 'error' in r or not r.get('energy_shifts'):
            continue
        lines.append(f"### {r['file'].replace('.mp3','')}")
        for shift in r['energy_shifts']:
            lines.append(f"- {shift}")
        lines.append("")

    lines.append("\n## Section Boundaries\n")
    lines.append("| Track | Sections |")
    lines.append("|-------|----------|")
    for r in all_results:
        if 'error' in r:
            continue
        sections = r.get('sections', [])
        lines.append(f"| {r['file'].replace('.mp3','')} | {' / '.join(sections)} |")

    lines.append("\n## Spectral Balance\n")
    lines.append("| Track | Low (<250Hz) | Mid (250-2kHz) | High (>2kHz) |")
    lines.append("|-------|-------------|----------------|-------------|")
    for r in all_results:
        if 'error' in r:
            continue
        lines.append(
            f"| {r['file'].replace('.mp3','')} | {r['spectral_low']}% "
            f"| {r['spectral_mid']}% | {r['spectral_high']}% |"
        )

    return "\n".join(lines) + "\n"


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


def output_scope(audio_dir):
    """(data root, scope slug) for a scanned folder.

    The catalog root is an `audio/` folder: scope None, so the outputs keep their
    catalog-wide names beside it. A band folder (audio/<band-slug>/) or any other
    folder gets its own slug, so a narrower pass never overwrites the catalog report."""
    p = Path(os.path.normpath(audio_dir))
    if p.name == "audio":
        return str(p.parent), None
    if p.parent.name == "audio":
        return str(p.parent.parent), _slugify(p.name)
    return "docs", _slugify(p.name)


def default_targets(audio_dir, today):
    """Default (archive, companion) paths for a scan of `audio_dir` on `today` (YYYY-MM-DD)."""
    root, scope = output_scope(audio_dir)
    suffix = f"-{scope}" if scope else ""
    archive = os.path.join(root, "audio-analysis", "catalog", f"{today}-deep{suffix}.json")
    companion = os.path.join(root, f"{scope}-catalog-analysis-report.md" if scope else "catalog-analysis-report.md")
    return archive, companion


def resolve_target(arg_value, default):
    """argparse `nargs="?", const=""` value: None = off, "" = the default path, else the path given."""
    if arg_value is None:
        return None
    return arg_value or default


def fail(error, code=1, **extra):
    """Print the failure as JSON on stdout (the caller reads it) and exit non-zero."""
    print(json.dumps({"script": SCRIPT_NAME, "status": "fail", "error": error, **extra}, indent=2))
    sys.exit(code)


def companion_body(all_results, timestamp, scope):
    title = f"# Catalog Audio Analysis — {scope}\n" if scope else "# Catalog Audio Analysis — Full\n"
    title_block = title + f"_Generated by `{SCRIPT_NAME}` on {timestamp}_\n\n"
    body_lines = format_text(all_results).split("\n")
    cut = 0
    while cut < len(body_lines):
        line = body_lines[cut]
        if line.startswith("##") or (line.strip() and not line.startswith("#")):
            break
        cut += 1
    return title_block + "\n".join(body_lines[cut:])


def main():
    parser = argparse.ArgumentParser(
        description="Batch audio analysis: tempo, energy, sections, spectral balance.",
        epilog="Exit codes: 0 analysis ran (status ok, or partial with failed[]); 1 bad arguments, no audio "
               "files, or every track failed; 2 missing audio dependencies.",
    )
    parser.add_argument(
        "--audio-dir", default="docs/audio",
        help=("Directory containing .mp3 files, searched recursively so per-band sub-folders are included "
              "(default: docs/audio). A band folder (audio/<band-slug>) writes band-scoped outputs."),
    )
    parser.add_argument(
        "--format", choices=["json", "text"], default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--archive", nargs="?", const="", default="",
        help=(
            "Persist the full JSON as a dated archive. With no path: "
            "audio-analysis/catalog/<YYYY-MM-DD>-deep[-<folder-slug>].json beside the audio/ folder. "
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
            "Refresh the Markdown companion. With no path: catalog-analysis-report.md for the catalog root, "
            "<folder-slug>-catalog-analysis-report.md for a band folder, beside the audio/ folder. "
            "Pass an explicit path to override. Default: ON."
        ),
    )
    parser.add_argument(
        "--no-companion", dest="companion", action="store_const", const=None,
        help="Skip refreshing the Markdown companion file.",
    )
    add_tempo_source_arg(parser)
    args = parser.parse_args()

    require_audio_deps()
    import librosa  # noqa: F401
    import numpy as np  # noqa: F401

    audio_dir = args.audio_dir
    if not os.path.isdir(audio_dir):
        fail(f"Audio directory not found: {audio_dir}")

    mp3s = find_mp3s(audio_dir)

    if not mp3s:
        fail(f"No .mp3 files found in: {audio_dir}")

    print(f"Analyzing {len(mp3s)} tracks...\n", file=sys.stderr)

    readings, tempo_note = None, None
    if resolve_tempo_source(args.tempo_source) == "beat-this":
        try:
            readings = run_beat_grid(mp3s, include_beats=True)
        except BeatThisUnavailable as exc:
            tempo_note = f"Beat This! unavailable ({exc}); tempo is librosa's for every track."
            print(f"  NOTE: {tempo_note}", file=sys.stderr)

    all_results, unread = [], []
    for i, filepath in enumerate(mp3s):
        label = rel_label(filepath, audio_dir)
        print(f"  Processing: {label}...", end="", flush=True, file=sys.stderr)
        reading = readings[i] if readings else None
        result = analyze_track(filepath, reading)
        result['file'] = label
        all_results.append(result)
        if 'error' in result:
            print(f" ERROR: {result['error']}", file=sys.stderr)
        else:
            if readings and result.get('tempo_source') != 'beat-this':
                unread.append(f"{label} ({(reading or {}).get('error') or 'no beats read'})")
            print(f" done ({result['bpm']} BPM, {result['key']}, {result['dynamic_character']})", file=sys.stderr)
    if unread:
        tempo_note = f"Beat This! could not read {len(unread)} track(s), librosa used for: {'; '.join(unread)}."

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    default_archive, default_companion = default_targets(audio_dir, now.strftime("%Y-%m-%d"))
    archive_target = resolve_target(args.archive, default_archive)
    companion_target = resolve_target(args.companion, default_companion)
    report = build_report(all_results, tempo_note)

    if report['analyzed_count'] == 0:
        skipped = {"status": "skipped", "reason": "every track failed; the prior files are untouched"}
        fail("Every track failed analysis (see failed[]). Nothing was written.",
             track_count=report['track_count'], failed=report['failed'],
             artifacts={"archive": {"path": archive_target, **skipped},
                        "companion": {"path": companion_target, **skipped}})

    artifacts = {}
    scope = output_scope(audio_dir)[1]
    for kind, target in (("archive", archive_target), ("companion", companion_target)):
        if target is None:
            artifacts[kind] = {"path": None, "status": "skipped"}
            continue
        try:
            if kind == "archive":
                res = write_archive(target, report)
            else:
                # Hand-curated sections live OUTSIDE the AUTOGEN markers and survive.
                res = update_companion(target, SCRIPT_NAME, companion_body(all_results, now.isoformat(), scope))
        except OSError as exc:
            artifacts[kind] = {"path": target, "status": "error", "reason": str(exc)}
            continue
        artifacts[kind] = {"path": target, "status": "written"}
        print(f"  {kind.upper()}: {res['status']} {res['path']} ({res['bytes_written']} bytes)", file=sys.stderr)

    # Format output
    if args.format == "json":
        output = json.dumps({**report, 'artifacts': artifacts}, indent=2)
    else:
        output = format_text(all_results)

    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"\nReport saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
