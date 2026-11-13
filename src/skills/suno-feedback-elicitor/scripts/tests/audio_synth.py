"""Synthesized audio for the audio-script tests: numpy signals and a stdlib WAV writer.

No fixture files and no extra dependency: a few seconds of a known signal is
enough to drive the real librosa code paths.
"""

import wave

import numpy as np

SR = 22050


def click_triad(seconds=8.0, bpm=120.0, sr=SR):
    """An A-minor triad (A3, C4, E4) with a click on every beat, as float samples in [-1, 1]."""
    t = np.arange(int(seconds * sr)) / sr
    y = sum(np.sin(2 * np.pi * f * t) for f in (220.0, 261.63, 329.63)) / 6.0
    click = np.exp(-np.arange(int(0.03 * sr)) / (0.004 * sr)) * 0.6
    for start in np.arange(0.0, seconds, 60.0 / bpm):
        i = int(start * sr)
        n = min(len(click), len(y) - i)
        y[i:i + n] += click[:n]
    return np.clip(y, -1.0, 1.0)


def write_wav(path, samples, sr=SR):
    """Write mono float samples as 16-bit PCM."""
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(pcm.tobytes())
    return path
