#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["librosa>=1.0", "numpy>=2.1", "pyloudnorm>=0.2", "pyyaml>=6.0"]
# ///
"""
Generate playlist sequencing data: Camelot codes, entry/exit keys,
energy levels, BS.1770 loudness, and transition compatibility (key, BPM, and
the loudness step across each seam) for an audio catalog.

Tempo (overall, entry, exit) comes from Beat This! (beat-grid.py) when the
PyTorch audio tools are turned on in the module config (`pytorch_audio_tools`),
otherwise from librosa; `--tempo-source` overrides the choice for one run.

When given a --playlist YAML config, uses the specified track order and
album name. Without a config, auto-discovers all .mp3 files in the
audio directory (sorted alphabetically). A track's optional `felt_bpm:` in the
YAML (the ear-verified tempo) corrects that track's half/double-time misreads
in the seam math.

The JSON also reports, so nobody has to work them out by hand:
  - `dropped[]` and `analyzed_count`: playlist entries that were not analyzed
    (audio file missing, or analysis error).
  - per seam: `key_relation` (same / relative / parallel / adjacent / two-step /
    distant) and `key_compat` (compatible / near / distant). Both describe the
    KEY relationship only; a seam's smoothness also depends on tempo, energy,
    loudness, and genre register, which is a listening judgment.
  - per seam: `pulse_pair` (the two tempos sit about 2x apart, sharing a grid).
  - per track (librosa tempo): `bpm_librosa_slow_prior` (librosa read again with
    a slow starting tempo, start_bpm=80) and `librosa_prior_relation` (agree /
    double / other). `double` = the default reading is ~2x the slow one, a
    likely halftime ambiguity; the ear (or Beat This!) decides.
  - per track: `felt_bpm_check` (no `felt_bpm:` is recorded and the measured
    tempo is in a half/double-time danger range, or librosa's two readings are
    a `double`).
  - `runs[]`: same-key runs longer than 2, and tempo-bucket runs.
  - `compare`: what moved against the prior archive (read BEFORE the archive is
    overwritten): per-track deltas and per-seam label changes.

Exit codes:
  0 = analysis completed successfully
  1 = invalid arguments or no audio files found
  2 = missing dependencies (librosa/numpy/pyloudnorm)
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
from audio_deps import require_audio_deps
from companion_writer import update_companion, resolve_companion_path
from json_archiver import archive_path, resolve_archive_arg, write_archive
from loudness import load_native, seam_quality, seam_step, summarize as loudness_summary
from tempo_source import (SOURCE_LABELS, add_tempo_source_arg, beat_this_readings, bpm_cell,
                          librosa_tempo_pair, resolve_tempo_source, source_summary, usable)

SCRIPT_NAME = "playlist-sequencing-data"

PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Camelot wheel mapping
CAMELOT = {
    'C major': '8B', 'A minor': '8A',
    'G major': '9B', 'E minor': '9A',
    'D major': '10B', 'B minor': '10A',
    'A major': '11B', 'F# minor': '11A',
    'E major': '12B', 'C# minor': '12A',
    'B major': '1B', 'G# minor': '1A',
    'F# major': '2B', 'D# minor': '2A',
    'C# major': '3B', 'A# minor': '3A',
    'G# major': '4B', 'F minor': '4A',
    'D# major': '5B', 'C minor': '5A',
    'A# major': '6B', 'G minor': '6A',
    'F major': '7B', 'D minor': '7A',
    # Enharmonic equivalents
    'Db major': '3B', 'Bb minor': '3A',
    'Ab major': '4B', 'Eb minor': '2A',
    'Eb major': '5B', 'Bb major': '6B',
    'Gb major': '2B',
}


def detect_key(chroma_segment):
    """Detect key from a chroma segment."""
    import numpy as np

    MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    avg = np.mean(chroma_segment, axis=1)
    best_corr = -1
    best_key = "Unknown"
    for i in range(12):
        rolled = np.roll(avg, -i)
        for profile, mode in [(MAJOR_PROFILE, "major"), (MINOR_PROFILE, "minor")]:
            corr = np.corrcoef(rolled, profile)[0, 1]
            if corr > best_corr:
                best_corr = corr
                best_key = f"{PITCH_CLASSES[i]} {mode}"
    return best_key, best_corr


def get_camelot(key):
    """Convert key name to Camelot code."""
    return CAMELOT.get(key, "??")


def camelot_distance(code1, code2):
    """Calculate distance on Camelot wheel. 0=same, 1=adjacent, etc."""
    if code1 == "??" or code2 == "??":
        return -1
    num1, letter1 = int(code1[:-1]), code1[-1]
    num2, letter2 = int(code2[:-1]), code2[-1]

    # Same position
    if code1 == code2:
        return 0
    # Relative major/minor (same number, different letter)
    if num1 == num2:
        return 0.5
    # Adjacent numbers, same letter
    num_dist = min(abs(num1 - num2), 12 - abs(num1 - num2))
    if letter1 == letter2 and num_dist == 1:
        return 1
    if letter1 == letter2 and num_dist == 2:
        return 2
    # Different letter + different number
    return num_dist + 0.5


FLAT_TO_SHARP = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}


def _split_key(key):
    """'Eb minor' -> ('D#', 'minor'); None when the name isn't '<tonic> <mode>'."""
    parts = (key or "").split()
    if len(parts) != 2 or parts[1] not in ("major", "minor"):
        return None
    return FLAT_TO_SHARP.get(parts[0], parts[0]), parts[1]


def key_relation(from_key, to_key, cam_dist):
    """Name the key relationship across a seam. Parallel keys (same tonic, other
    mode) sit far apart on the wheel but share a harmonic center, so they get
    their own name rather than reading as 'distant'."""
    a, b = _split_key(from_key), _split_key(to_key)
    if cam_dist < 0 or a is None or b is None:
        return "unknown"
    if a == b or cam_dist == 0:
        return "same"
    if a[0] == b[0]:
        return "parallel"
    if cam_dist == 0.5:
        return "relative"
    if cam_dist == 1:
        return "adjacent"
    if cam_dist == 2:
        return "two-step"
    return "distant"


def key_compat(cam_dist):
    """Camelot key compatibility only — not the seam's smoothness."""
    if cam_dist < 0:
        return "unknown"
    return "compatible" if cam_dist <= 1 else "near" if cam_dist <= 2 else "distant"


# Measured tempos most often read half or double time in these ranges.
FELT_CHECK_RANGES = ((70, 100), (130, 180))
PULSE_PAIR_TOLERANCE = 0.06  # within 6% of an exact 2:1 ratio
# Tempo buckets for run counting (felt BPM when recorded, else measured).
TEMPO_BUCKETS = (("slow", 0, 90), ("mid", 90, 125), ("up", 125, 10_000))
RUN_LIMITS = {"same-key": 3, "slow": 2, "mid": 3, "up": 3}  # report runs this long or longer


def octave_correct(measured, felt):
    """Fold a measured tempo by x0.5 / x1 / x2 to whichever lands nearest the felt BPM.

    Keeps a track's real entry/exit tempo drift while undoing half/double reads."""
    if not felt or not measured:
        return measured
    return min((measured * f for f in (0.5, 1, 2)), key=lambda v: abs(v - felt))


def needs_felt_check(bpm, felt, prior_relation=None):
    """True when no felt BPM is recorded and the measured tempo is in a danger range,
    or librosa's default reading is ~2x its slow-prior one (a likely halftime ambiguity)."""
    if felt is not None or bpm is None:
        return False
    return prior_relation == 'double' or any(lo <= bpm <= hi for lo, hi in FELT_CHECK_RANGES)


def is_pulse_pair(a, b):
    if not a or not b:
        return False
    ratio = max(a, b) / min(a, b)
    return abs(ratio - 2) / 2 <= PULSE_PAIR_TOLERANCE


def tempo_bucket(bpm):
    for name, lo, hi in TEMPO_BUCKETS:
        if lo <= bpm < hi:
            return name
    return None


def format_time(seconds):
    return f"{int(seconds//60)}:{int(seconds%60):02d}"


def analyze_track(filepath, beat_reading=None):
    """Extract sequencing data for a single track. `beat_reading` is its Beat This! reading, when that's the tempo source."""
    import librosa
    import numpy as np

    y, sr = librosa.load(filepath, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)

    # Overall key
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    overall_key, overall_conf = detect_key(chroma)

    # Entry key (first 30 seconds)
    entry_frames = int(30 * sr / 512)
    entry_key, entry_conf = detect_key(chroma[:, :min(entry_frames, chroma.shape[1])])

    # Exit key (last 30 seconds)
    exit_start = max(0, chroma.shape[1] - entry_frames)
    exit_key, exit_conf = detect_key(chroma[:, exit_start:])

    # BPM — overall, plus entry/exit (first and last 30 s) for the seams. Beat This!
    # when it's the tempo source and read the track; otherwise librosa.
    def _bpm(segment):
        t, _ = librosa.beat.beat_track(y=segment, sr=sr)
        return float(np.atleast_1d(t)[0])

    slow = {}
    if usable(beat_reading):
        bpm = beat_reading['bpm']
        entry_bpm = beat_reading.get('entry_bpm') or bpm
        exit_bpm = beat_reading.get('exit_bpm') or bpm
        tempo_source = 'beat-this'
    else:
        # Overall tempo: librosa's default reading plus a slow-prior one (start_bpm=80),
        # reported only; the seams use the default readings as before.
        pair = librosa_tempo_pair(y, sr)
        bpm = pair['bpm_librosa']
        slow = {'bpm_librosa_slow_prior': pair['bpm_librosa_slow_prior'],
                'librosa_prior_relation': pair['librosa_prior_relation']}
        edge = int(30 * sr)
        entry_bpm = _bpm(y[:edge]) if len(y) > 2 * edge else bpm
        exit_bpm = _bpm(y[-edge:]) if len(y) > 2 * edge else bpm
        tempo_source = 'librosa'

    # Energy level (normalize to 1-10 scale)
    rms = librosa.feature.rms(y=y)[0]
    avg_energy = np.mean(rms)
    max_possible = np.max(rms) * 1.2  # leave headroom
    energy_pct = avg_energy / max_possible if max_possible > 0 else 0
    energy_level = max(1, min(10, int(energy_pct * 10) + 3))  # offset for rock/metal bias

    # Intro energy (first 15 sec)
    intro_frames = int(15 * sr / 512)
    intro_energy = np.mean(rms[:min(intro_frames, len(rms))])
    intro_pct = intro_energy / (np.max(rms) if np.max(rms) > 0 else 1) * 100

    # Outro energy (last 15 sec)
    outro_start = max(0, len(rms) - intro_frames)
    outro_energy = np.mean(rms[outro_start:])
    outro_pct = outro_energy / (np.max(rms) if np.max(rms) > 0 else 1) * 100

    # Loudness (BS.1770) at the file's native rate and channels
    samples, native_sr = load_native(filepath)

    return {
        'duration': duration,
        'bpm': round(bpm, 1),
        'entry_bpm': round(entry_bpm, 1),
        'exit_bpm': round(exit_bpm, 1),
        'tempo_source': tempo_source,
        **slow,
        'overall_key': overall_key,
        'overall_conf': round(overall_conf, 3),
        'overall_camelot': get_camelot(overall_key),
        'entry_key': entry_key,
        'entry_conf': round(entry_conf, 3),
        'entry_camelot': get_camelot(entry_key),
        'exit_key': exit_key,
        'exit_conf': round(exit_conf, 3),
        'exit_camelot': get_camelot(exit_key),
        'energy_level': energy_level,
        'intro_energy_pct': round(intro_pct),
        'outro_energy_pct': round(outro_pct),
        'loudness': loudness_summary(samples, native_sr),
    }


DEFAULT_AUDIO_ROOT = "docs/audio"


def resolve_audio_dir(cli_audio_dir, playlist_path=None, yaml_audio_dir=None):
    """Pick the directory a playlist's `file:` entries are relative to.

    Precedence: the --audio-dir flag > the YAML's `audio_dir:` key > the
    per-band folder docs/audio/{band-slug}/ derived from the playlist filename
    docs/{band-slug}-playlist.yaml (only when that folder exists) > the legacy
    flat docs/audio/.
    """
    if cli_audio_dir:
        return cli_audio_dir
    if yaml_audio_dir:
        return yaml_audio_dir
    if playlist_path:
        stem = Path(playlist_path).stem
        if stem.endswith("-playlist"):
            derived = os.path.join(DEFAULT_AUDIO_ROOT, stem[:-len("-playlist")])
            if os.path.isdir(derived):
                return derived
    return DEFAULT_AUDIO_ROOT


def load_playlist(playlist_path):
    """Load playlist config from a YAML file.

    Returns (album_name, track_list, audio_dir) — audio_dir is the YAML's
    optional `audio_dir:` key, or None when absent.
    """
    import yaml

    with open(playlist_path, 'r') as f:
        config = yaml.safe_load(f)

    album = config.get('album', 'Audio Analysis')
    tracks = [
        (t['name'], t['file'])
        for t in config.get('tracks', [])
    ]
    return album, tracks, config.get('audio_dir')


def load_felt_bpm(playlist_path):
    """{track name: felt_bpm} for tracks whose playlist entry records one."""
    import yaml

    with open(playlist_path, 'r') as f:
        config = yaml.safe_load(f) or {}
    out = {}
    for t in config.get('tracks', []):
        felt = t.get('felt_bpm')
        if isinstance(felt, (int, float)) and felt > 0:
            out[t['name']] = float(felt)
    return out


def discover_tracks(audio_dir):
    """Auto-discover .mp3 files under a directory, recursively.

    Returns (album_name, track_list); each file is relative to audio_dir, so a
    per-band sub-folder shows up as "band-slug/Song.mp3".
    """
    mp3s = []
    for root, dirs, files in os.walk(audio_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.'))
        for f in files:
            if f.endswith('.mp3'):
                mp3s.append(os.path.relpath(os.path.join(root, f), audio_dir).replace(os.sep, '/'))
    tracks = [
        (os.path.splitext(os.path.basename(f))[0], f)
        for f in sorted(mp3s)
    ]
    return "Audio Analysis", tracks


def _fmt(value):
    return "-" if value is None else value


def transition_between(r, n):
    """Transition data from track r into track n: key, BPM, and loudness across the seam."""
    cam_dist = camelot_distance(r['exit_camelot'], n['entry_camelot'])
    # Seam tempo: this track's exit BPM against the next track's entry BPM when both
    # exist (first/last 30 s); older archives fall back to the overall BPMs. A recorded
    # felt BPM folds each reading to the felt octave.
    edges = r.get('exit_bpm') is not None and n.get('entry_bpm') is not None
    from_bpm = r['exit_bpm'] if edges else r['bpm']
    to_bpm = n['entry_bpm'] if edges else n['bpm']
    felt = bool(r.get('felt_bpm') or n.get('felt_bpm'))
    from_bpm = round(octave_correct(from_bpm, r.get('felt_bpm')), 1)
    to_bpm = round(octave_correct(to_bpm, n.get('felt_bpm')), 1)
    bpm_pct = abs(from_bpm - to_bpm) / from_bpm * 100 if from_bpm > 0 else 0
    step = seam_step(r.get('loudness'), n.get('loudness'))
    return {
        'to': n['name'],
        'camelot_distance': cam_dist,
        'key_relation': key_relation(r.get('exit_key'), n.get('entry_key'), cam_dist),
        'key_compat': key_compat(cam_dist),
        'bpm_from': from_bpm,
        'bpm_to': to_bpm,
        'bpm_basis': ('exit/entry' if edges else 'overall') + ('+felt' if felt else ''),
        'bpm_change': round(abs(from_bpm - to_bpm), 1),
        'bpm_quality': "smooth" if bpm_pct < 3 else "ok" if bpm_pct < 6 else f"jump ({bpm_pct:.0f}%)",
        'pulse_pair': is_pulse_pair(from_bpm, to_bpm),
        'loudness_step_lu': step,
        'loudness_quality': seam_quality(step),
    }


def compute_transitions(results):
    """Attach transition data to each track that has an analyzable successor."""
    for i in range(len(results) - 1):
        if 'error' in results[i] or 'error' in results[i+1]:
            continue
        results[i]['transition'] = transition_between(results[i], results[i+1])


def find_runs(results):
    """Runs of adjacent analyzed tracks sharing an overall key, or a tempo bucket.

    Reports same-key runs longer than 2 and tempo-bucket runs (slow: 2+, mid/up: 3+).
    A run is a fact; whether it is a deliberate block is a judgment."""
    runs = []

    def flush(kind, label, members):
        if label is not None and len(members) >= RUN_LIMITS.get(kind if kind == 'same-key' else label, 3):
            entry = {'kind': kind, 'value': label, 'tracks': [m['name'] for m in members]}
            if kind == 'tempo':
                entry['felt_verified'] = all(m.get('felt_bpm') for m in members)
            runs.append(entry)

    for kind, value_of in (('same-key', lambda r: r.get('overall_camelot') if r.get('overall_camelot') != '??' else None),
                           ('tempo', lambda r: tempo_bucket(r.get('felt_bpm') or r['bpm']))):
        members, label = [], None
        for r in results:
            value = None if 'error' in r else value_of(r)
            if value is not None and value == label:
                members.append(r)
                continue
            flush(kind, label, members)
            members, label = ([r], value) if value is not None else ([], None)
        flush(kind, label, members)
    return runs


def build_report(album_name, results):
    """The standard module JSON report as a dict."""
    tracks, dropped = [], []
    for i, r in enumerate(results):
        if 'error' in r:
            tracks.append({
                'position': i + 1,
                'name': r['name'],
                'file': r.get('file'),
                'status': 'error',
                'error': r['error'],
            })
            dropped.append({'position': i + 1, 'name': r['name'], 'file': r.get('file'), 'reason': r['error']})
            continue
        entry = {
            'position': i + 1,
            'name': r['name'],
            'duration': round(r['duration'], 1),
            'duration_display': format_time(r['duration']),
            'bpm': r['bpm'],
            'entry_bpm': r.get('entry_bpm'),
            'exit_bpm': r.get('exit_bpm'),
            'tempo_source': r.get('tempo_source'),
            'bpm_librosa_slow_prior': r.get('bpm_librosa_slow_prior'),
            'librosa_prior_relation': r.get('librosa_prior_relation'),
            'felt_bpm': r.get('felt_bpm'),
            'felt_bpm_check': needs_felt_check(r['bpm'], r.get('felt_bpm'), r.get('librosa_prior_relation')),
            'key': {
                'overall': r['overall_key'],
                'overall_confidence': r['overall_conf'],
                'overall_camelot': r['overall_camelot'],
                'entry': r['entry_key'],
                'entry_confidence': r['entry_conf'],
                'entry_camelot': r['entry_camelot'],
                'exit': r['exit_key'],
                'exit_confidence': r['exit_conf'],
                'exit_camelot': r['exit_camelot'],
            },
            'energy': {
                'level': r['energy_level'],
                'intro_pct': r['intro_energy_pct'],
                'outro_pct': r['outro_energy_pct'],
            },
            'loudness': r.get('loudness'),
        }
        # Add transition data if available
        if 'transition' in r:
            entry['transition_to_next'] = r['transition']
        tracks.append(entry)

    return {
        'script': 'playlist-sequencing-data',
        'status': 'ok',
        'album': album_name,
        'track_count': len(results),
        'analyzed_count': len(results) - len(dropped),
        'dropped': dropped,
        'tempo_source': source_summary(results),
        'runs': find_runs(results),
        'tracks': tracks,
    }


def format_json(album_name, results):
    """Format results as standard module JSON."""
    return json.dumps(build_report(album_name, results), indent=2)


# --- Re-evaluation compare -------------------------------------------------

BPM_DELTA = 2.0       # BPM shifts smaller than this are measurement noise
LUFS_DELTA = 1.0      # LU
LEGACY_KEY_QUALITY = {"PERFECT": "compatible", "GOOD": "compatible", "OK": "near", "JARRING": "distant"}
RANKS = {
    'key_compat': {"compatible": 0, "near": 1, "distant": 2},
    'bpm_quality': {"smooth": 0, "ok": 1, "jump": 2},
    'loudness_quality': {"smooth": 0, "noticeable": 1, "big jump": 2},
}


def _seam_labels(t):
    """Comparable labels for one seam; maps pre-rename archives (key_quality) forward."""
    compat = t.get('key_compat') or LEGACY_KEY_QUALITY.get(t.get('key_quality'))
    bpm = (t.get('bpm_quality') or '').split(' (')[0] or None
    loud = (t.get('loudness_quality') or '').split(' (')[0] or None
    return {'key_compat': compat, 'bpm_quality': bpm, 'loudness_quality': loud}


def compare_runs(prior, current):
    """What moved between two playlist-sequencing-data reports (parsed JSON dicts).

    Tracks are matched by name, seams by (from, to) pair. Returns added/removed
    tracks, per-track deltas past the noise floor, and seams whose key/BPM/loudness
    labels changed, each marked worse / better / mixed.
    """
    def analyzed(d):
        return {t['name']: t for t in d.get('tracks', []) if t.get('status') != 'error'}

    def seams(d):
        return {(t['name'], t['transition_to_next']['to']): t['transition_to_next']
                for t in d.get('tracks', []) if t.get('transition_to_next')}

    prior_names = [t['name'] for t in prior.get('tracks', [])]
    current_names = [t['name'] for t in current.get('tracks', [])]
    p, c = analyzed(prior), analyzed(current)

    track_changes = []
    for name, now in c.items():
        was = p.get(name)
        if was is None:
            continue
        deltas = {}
        for field in ('bpm', 'entry_bpm', 'exit_bpm'):
            a, b = was.get(field), now.get(field)
            if a is not None and b is not None and abs(b - a) >= BPM_DELTA:
                deltas[field] = [a, b]
        for field in ('overall_camelot', 'entry_camelot', 'exit_camelot'):
            a, b = (was.get('key') or {}).get(field), (now.get('key') or {}).get(field)
            if a != b and a is not None and b is not None:
                deltas[field] = [a, b]
        a, b = (was.get('energy') or {}).get('level'), (now.get('energy') or {}).get('level')
        if a != b and a is not None and b is not None:
            deltas['energy_level'] = [a, b]
        a, b = (was.get('loudness') or {}).get('integrated_lufs'), (now.get('loudness') or {}).get('integrated_lufs')
        if a is not None and b is not None and abs(b - a) >= LUFS_DELTA:
            deltas['integrated_lufs'] = [a, b]
        if was.get('position') != now.get('position'):
            deltas['position'] = [was.get('position'), now.get('position')]
        if deltas:
            track_changes.append({'name': name, 'changes': deltas})

    ps, cs = seams(prior), seams(current)
    seam_changes = []
    for pair, now in cs.items():
        was = ps.get(pair)
        if was is None:
            continue
        before, after = _seam_labels(was), _seam_labels(now)
        diff = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
        if not diff:
            continue
        moves = set()
        for k, (a, b) in diff.items():
            ra, rb = RANKS[k].get(a), RANKS[k].get(b)
            if ra is not None and rb is not None:
                moves.add('worse' if rb > ra else 'better')
        direction = moves.pop() if len(moves) == 1 else ('mixed' if moves else 'changed')
        seam_changes.append({'from': pair[0], 'to': pair[1], 'direction': direction, 'changes': diff})
    seam_changes.sort(key=lambda s: {'worse': 0, 'mixed': 1, 'changed': 2, 'better': 3}[s['direction']])

    return {
        'status': 'compared',
        'added_tracks': [n for n in current_names if n not in prior_names],
        'removed_tracks': [n for n in prior_names if n not in current_names],
        'reordered': [n for n in current_names if n in prior_names] != [n for n in prior_names if n in current_names],
        'track_changes': track_changes,
        'unchanged_tracks': sum(1 for n in c if n in p) - len(track_changes),
        'seam_changes': seam_changes,
        'new_seams': [{'from': a, 'to': b} for (a, b) in cs if (a, b) not in ps],
    }


def load_prior(path):
    """Read the prior archive before this run overwrites it. Returns (data, status)."""
    if not path or not os.path.isfile(path):
        return None, 'no-prior'
    try:
        with open(path) as f:
            return json.load(f), 'ok'
    except (OSError, ValueError) as exc:
        return None, f'unreadable: {exc}'


def format_text(album_name, results):
    """Format results as a Markdown report."""
    lines = []
    lines.append(f"# {album_name} -- Playlist Sequencing Data")
    tempo_label = SOURCE_LABELS[source_summary(results)]
    lines.append(f"# Generated via librosa analysis + Camelot wheel mapping + BS.1770 loudness | Tempo: {tempo_label}\n")

    lines.append("## Track Data (Playlist Order)\n")
    lines.append("| # | Track | BPM | BPM in→out | Key | Camelot | Entry Key | Exit Key | Energy | Intro% | Outro% | LUFS | LUFS in→out | LRA |")
    lines.append("|---|-------|-----|------------|-----|---------|-----------|----------|--------|--------|--------|------|-------------|-----|")
    for i, r in enumerate(results):
        if 'error' in r:
            continue
        loud = r.get('loudness') or {}
        bpm = bpm_cell(r['bpm'], r.get('bpm_librosa_slow_prior'), r.get('librosa_prior_relation'))
        lines.append(
            f"| {i+1} | {r['name']} | {bpm} | {_fmt(r.get('entry_bpm'))}→{_fmt(r.get('exit_bpm'))} | {r['overall_key']} "
            f"| {r['overall_camelot']} | {r['entry_key']} ({r['entry_camelot']}) "
            f"| {r['exit_key']} ({r['exit_camelot']}) | {r['energy_level']} "
            f"| {r['intro_energy_pct']}% | {r['outro_energy_pct']}% "
            f"| {_fmt(loud.get('integrated_lufs'))} "
            f"| {_fmt(loud.get('entry_lufs'))}→{_fmt(loud.get('exit_lufs'))} "
            f"| {_fmt(loud.get('lra_lu'))} |"
        )
    if any(r.get('librosa_prior_relation') not in (None, 'agree') for r in results if 'error' not in r):
        lines.append(
            "\n_BPM a / b = librosa's default reading / its reading with a slow starting tempo (start_bpm=80). "
            "(halftime?) = about 2x apart, a likely halftime ambiguity: the ear (or Beat This!) decides which is "
            "felt, and a `felt_bpm:` in the playlist settles it for the seams._"
        )

    lines.append("\n## Transition Analysis\n")
    lines.append("| From | To | Key Distance | Key Relation | BPM Change | Loudness Step |")
    lines.append("|------|----|-------------|------------|---------|---------------|")
    for i in range(len(results) - 1):
        if 'error' in results[i] or 'error' in results[i+1]:
            continue
        r = results[i]
        n = results[i+1]
        t = r.get('transition') or transition_between(r, n)
        step = t.get('loudness_step_lu')
        loud = "-" if step is None else f"{step:+.1f} LU ({t['loudness_quality']})"
        lines.append(
            f"| {r['name']} | {n['name']} | {t['camelot_distance']} "
            f"({r['exit_camelot']}->{n['entry_camelot']}) "
            f"| {t.get('key_relation', '-')} ({t.get('key_compat', '-')}) "
            f"| {t['bpm_change']:.0f} ({t['bpm_quality']}{', 2:1 pulse' if t.get('pulse_pair') else ''}) | {loud} |"
        )
    lines.append(
        f"\n_Tempo: {tempo_label}. BPM change = this track's exit tempo (last 30 s) against the next track's "
        "entry tempo (first 30 s). "
        "Loudness step = next track's entry loudness (first 15 s) minus this track's exit loudness (last 15 s), "
        "silence trimmed, in LU: "
        "smooth < 3, noticeable < 6, big jump >= 6. Key relation describes the keys only (Camelot), "
        "not how smooth the seam sounds. Descriptive, not a verdict: "
        "a quiet open after a loud close is often the point._"
    )

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Playlist sequencing analysis: keys, Camelot codes, energy, loudness, transitions."
    )
    parser.add_argument(
        "--playlist",
        help="Path to YAML playlist config file (for ordered analysis with album metadata).",
    )
    parser.add_argument(
        "--audio-dir", default=None,
        help=(
            "Directory the playlist's `file:` entries are relative to. Default: the "
            "playlist YAML's `audio_dir:` key, else docs/audio/{band-slug}/ when that "
            "folder exists, else docs/audio."
        ),
    )
    parser.add_argument(
        "--format", choices=["json", "text"], default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: stdout).",
    )
    parser.add_argument(
        "--archive", nargs="?", const="", default="",
        help=(
            "Persist full JSON output to a per-playlist archive. "
            "With no path: writes to docs/audio-analysis/playlists/<album>.json. "
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
            "With no path: writes the per-band companion docs/{band-slug}-playlist-sequencing.md "
            "(slug derived from the album/band name). "
            "Pass an explicit path to override. Default: ON."
        ),
    )
    parser.add_argument(
        "--no-companion", dest="companion", action="store_const", const=None,
        help="Skip refreshing the Markdown companion file.",
    )
    parser.add_argument(
        "--compare-to", nargs="?", const="", default="",
        help=(
            "Compare this run against a prior report and add a `compare` block to the JSON "
            "(per-track deltas, per-seam label changes). With no path: the canonical archive, "
            "read BEFORE this run overwrites it. Default: ON when that archive exists."
        ),
    )
    parser.add_argument(
        "--no-compare", dest="compare_to", action="store_const", const=None,
        help="Skip the compare against the prior archive.",
    )
    add_tempo_source_arg(parser)
    args = parser.parse_args()

    require_audio_deps(extra=("pyloudnorm",))
    import librosa  # noqa: F401
    import numpy as np  # noqa: F401

    # Build track list from playlist config or auto-discovery
    if args.playlist:
        if not os.path.isfile(args.playlist):
            print(json.dumps({
                "script": "playlist-sequencing-data",
                "status": "fail",
                "error": f"Playlist config not found: {args.playlist}",
            }), file=sys.stderr)
            sys.exit(1)
        album_name, track_list, yaml_audio_dir = load_playlist(args.playlist)
        felt_bpm = load_felt_bpm(args.playlist)
        audio_dir = resolve_audio_dir(args.audio_dir, args.playlist, yaml_audio_dir)
    else:
        felt_bpm = {}
        audio_dir = resolve_audio_dir(args.audio_dir)

    if not os.path.isdir(audio_dir):
        print(json.dumps({
            "script": "playlist-sequencing-data",
            "status": "fail",
            "error": f"Audio directory not found: {audio_dir}",
        }), file=sys.stderr)
        sys.exit(1)

    if not args.playlist:
        album_name, track_list = discover_tracks(audio_dir)

    if not track_list:
        print(json.dumps({
            "script": "playlist-sequencing-data",
            "status": "fail",
            "error": "No tracks found.",
        }), file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing playlist sequencing data for: {album_name} (audio: {audio_dir})\n", file=sys.stderr)

    # Read the prior report now: the archive step below overwrites the default path.
    prior, prior_status, prior_path = None, None, None
    if args.compare_to is not None:
        prior_path = args.compare_to or args.archive or archive_path("playlists", album_name)
        prior, prior_status = load_prior(prior_path)

    readings = {}
    if resolve_tempo_source(args.tempo_source) == "beat-this":
        present = list(dict.fromkeys(
            os.path.join(audio_dir, f) for _, f in track_list if os.path.exists(os.path.join(audio_dir, f))
        ))
        print(f"  Tempo: Beat This! ({len(present)} tracks)", file=sys.stderr)
        got = beat_this_readings(present)
        if got:
            readings = dict(zip(present, got))

    results = []
    for track_name, filename in track_list:
        filepath = os.path.join(audio_dir, filename)
        if not os.path.exists(filepath):
            print(f"  MISSING: {filename}", file=sys.stderr)
            results.append({'name': track_name, 'file': filename, 'error': 'missing audio file'})
            continue
        print(f"  {track_name}...", end="", flush=True, file=sys.stderr)
        try:
            data = analyze_track(filepath, readings.get(filepath))
        except Exception as exc:  # one bad file must not sink the whole playlist
            print(f" ERROR: {exc}", file=sys.stderr)
            results.append({'name': track_name, 'file': filename, 'error': f'analysis error: {exc}'})
            continue
        data['name'] = track_name
        data['felt_bpm'] = felt_bpm.get(track_name)
        results.append(data)
        print(
            f" {data['bpm']} BPM | {data['overall_key']} ({data['overall_camelot']}) "
            f"| Entry: {data['entry_camelot']} | Exit: {data['exit_camelot']} "
            f"| E:{data['energy_level']} | {_fmt(data['loudness']['integrated_lufs'])} LUFS",
            file=sys.stderr,
        )

    # Compute transition data for JSON output
    compute_transitions(results)

    report = build_report(album_name, results)
    if report['dropped']:
        names = ", ".join(f"{d['name']} ({d['reason']})" for d in report['dropped'])
        print(f"\n  DROPPED {len(report['dropped'])} of {report['track_count']}: {names}", file=sys.stderr)

    compare = None
    if args.compare_to is not None:
        compare = compare_runs(prior, report) if prior else {'status': prior_status}
        compare['prior'] = prior_path

    # Format output
    if args.format == "json":
        output = json.dumps({**report, 'compare': compare} if compare else report, indent=2)
    else:
        output = format_text(album_name, results)
        if compare:
            output += "\n## Compare With Prior Run\n\n```json\n" + json.dumps(compare, indent=2) + "\n```\n"

    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"\nReport saved to: {args.output}", file=sys.stderr)
    else:
        print(output)

    # JSON archive (default ON unless --no-archive)
    archive_target = resolve_archive_arg("playlists", album_name, args.archive)
    if archive_target is not None:
        res = write_archive(archive_target, report)
        print(f"  ARCHIVED: {res['path']} ({res['bytes_written']} bytes)", file=sys.stderr)

    # Companion .md refresh (default ON unless --no-companion).
    # The body includes its own title + timestamp at the top so each refresh
    # updates them. Hand-curated sections live OUTSIDE the AUTOGEN markers
    # in the companion file and are preserved across refreshes.
    # Per-album companion path: docs/{album-slug}-playlist-sequencing.md so
    # multiple bands don't overwrite each other's companions.
    companion_target = resolve_companion_path(SCRIPT_NAME, args.companion, album=album_name)
    if companion_target is not None:
        from datetime import datetime, timezone as _tz
        timestamp = datetime.now(_tz.utc).isoformat()
        title_block = (
            f"# {album_name} — Playlist Sequencing Data\n"
            f"_Generated by `{SCRIPT_NAME}` on {timestamp}_\n\n"
        )
        # Drop the script's built-in title (first 2 lines) and keep the rest
        body_lines = format_text(album_name, results).split("\n")
        cut = 0
        while cut < len(body_lines):
            line = body_lines[cut]
            if line.startswith("##") or (line.strip() and not line.startswith("#")):
                break
            cut += 1
        md_body = title_block + "\n".join(body_lines[cut:])
        res = update_companion(companion_target, SCRIPT_NAME, md_body)
        print(f"  COMPANION: {res['status']} {res['path']} ({res['bytes_written']} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
