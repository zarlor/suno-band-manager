"""BS.1770 loudness helpers shared by the audio scripts (pyloudnorm).

Loudness is measured at the file's own sample rate and channel layout (stereo
stays stereo), per ITU-R BS.1770 / EBU R128:

- integrated loudness (LUFS) over the whole song
- loudness range (LRA, in LU) from the 3-second short-term curve, gated per EBU Tech 3342
- loudness by thirds, and the song's build (last third minus first third)
- the seam between two songs in a playlist: the next song's first third minus
  the previous song's last third

Reference catalog (83 tracks, measured 2026-09-12): median integrated loudness
about -13.2 LUFS, median LRA 4.7-6.1 LU per band, songs building 2-2.6 LU from
first third to last, and a median playlist seam of about 2.5 LU.
"""

SHORT_TERM_WINDOW_S = 3.0
SHORT_TERM_HOP_S = 1.0
ABSOLUTE_GATE_LUFS = -70.0
RELATIVE_GATE_LU = 20.0
SEAM_SMOOTH_LU = 3.0
SEAM_BIG_LU = 6.0


def load_native(path):
    """Decode at the file's own rate and channel count -> (samples, sr).

    samples is (n,) for mono or (n, channels) — the layout pyloudnorm expects.
    """
    import librosa

    y, sr = librosa.load(path, sr=None, mono=False)
    return (y.T if y.ndim == 2 else y), sr


def integrated(meter, x):
    """Integrated loudness in LUFS, or None for silence / audio shorter than one gating block."""
    import math

    try:
        v = meter.integrated_loudness(x)
    except Exception:
        return None
    return round(float(v), 2) if math.isfinite(v) else None


def short_term_curve(meter, x, sr, window_s=SHORT_TERM_WINDOW_S, hop_s=SHORT_TERM_HOP_S):
    """Short-term loudness (3 s window, 1 s hop) as a list of LUFS values (None where silent)."""
    w, h = int(window_s * sr), int(hop_s * sr)
    if len(x) < w:
        return []
    return [integrated(meter, x[s:s + w]) for s in range(0, len(x) - w + 1, h)]


def _percentile(sorted_vals, q):
    """Linear-interpolated percentile of an ascending list (numpy's default method)."""
    k = (len(sorted_vals) - 1) * q / 100.0
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def loudness_range(curve):
    """LRA in LU from a short-term curve.

    Absolute gate at -70 LUFS, relative gate 20 LU below the power mean of what
    survives, then the spread from the 10th to the 95th percentile. None when
    fewer than five values survive the gates.
    """
    import math

    vals = [v for v in curve if v is not None and v > ABSOLUTE_GATE_LUFS]
    if len(vals) < 5:
        return None
    mean = 10 * math.log10(sum(10 ** (v / 10) for v in vals) / len(vals))
    gated = sorted(v for v in vals if v > mean - RELATIVE_GATE_LU)
    if len(gated) < 5:
        return None
    return round(_percentile(gated, 95) - _percentile(gated, 10), 2)


def thirds(meter, x):
    """Integrated loudness of the first, middle, and last third."""
    n = len(x)
    return [integrated(meter, x[i * n // 3:(i + 1) * n // 3]) for i in range(3)]


def summarize(x, sr):
    """Loudness summary for one song: integrated LUFS, LRA, thirds, and build."""
    import pyloudnorm as pyln

    meter = pyln.Meter(sr)
    t = thirds(meter, x)
    return {
        "integrated_lufs": integrated(meter, x),
        "lra_lu": loudness_range(short_term_curve(meter, x, sr)),
        "thirds_lufs": t,
        "build_lu": None if t[0] is None or t[2] is None else round(t[2] - t[0], 2),
    }


def seam_step(prev, nxt):
    """LU step across a playlist seam: next song's first third minus previous song's last third."""
    try:
        a, b = prev["thirds_lufs"][2], nxt["thirds_lufs"][0]
    except (KeyError, IndexError, TypeError):
        return None
    return None if a is None or b is None else round(b - a, 2)


def seam_quality(step):
    """Describe a seam step: smooth (< 3 LU), noticeable (< 6 LU), or big jump — with direction.

    Descriptive, not a verdict: a quiet open after a loud close is often the point.
    """
    if step is None:
        return None
    size = abs(step)
    if size < SEAM_SMOOTH_LU:
        return "smooth"
    direction = "louder" if step > 0 else "quieter"
    return f"{'noticeable' if size < SEAM_BIG_LU else 'big jump'} ({direction})"
