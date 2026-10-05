"""Equalizers: RBJ cookbook shelves and peaks, and a highpass, for amps and mixer channel strips."""

import numpy as np
from scipy.signal import butter, lfilter, sosfilt


def biquad(kind: str, f0: float, gain_db: float, sr: int, q: float = 0.7) -> tuple[np.ndarray, np.ndarray]:
    """RBJ cookbook `low` / `high` shelf or `peak`."""
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / sr
    alpha = np.sin(w) / (2 * q)
    cw = np.cos(w)
    if kind == "peak":
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    else:
        s = 1 if kind == "low" else -1
        sq = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) - s * (A - 1) * cw + sq), s * 2 * A * ((A - 1) - s * (A + 1) * cw),
             A * ((A + 1) - s * (A - 1) * cw - sq)]
        a = [(A + 1) + s * (A - 1) * cw + sq, -s * 2 * ((A - 1) + s * (A + 1) * cw),
             (A + 1) + s * (A - 1) * cw - sq]
    return np.array(b) / a[0], np.array(a) / a[0]


def equalize(x: np.ndarray, sr: int, bands: list[tuple[str, float, float, float]]) -> np.ndarray:
    """Apply (kind, f0, gain_dB, q) bands along axis 0 (mono or stereo); 0 dB bands are skipped."""
    for kind, f0, gain_db, q in bands:
        if gain_db:
            b, a = biquad(kind, f0, gain_db, sr, q)
            x = lfilter(b, a, x, axis=0)
    return x


def highpass(x: np.ndarray, sr: int, hz: float, order: int = 2) -> np.ndarray:
    return sosfilt(butter(order, hz, "hp", fs=sr, output="sos"), x, axis=0) if hz else x
