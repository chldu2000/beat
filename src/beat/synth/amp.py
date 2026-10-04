"""Tube guitar amp: preamp triode stages (4x oversampled), tone stack, power stage, cabinet.

Each triode stage is an asymmetric soft clipper (the grid-conduction side clips harder) with a
coupling-cap highpass and a Miller-capacitance lowpass, and inverts like a real common-cathode stage.
"""

import numpy as np
from scipy.signal import butter, lfilter, resample_poly, sosfilt

from .cab import cabinet

OS = 4
# tone -> preamp stage gains, pre-distortion highpass (Hz), tone stack (bass, mid, treble dB), power drive
TONES = {
    "clean": {"stages": [2.0], "tight_hz": 60, "stack": (2.0, 0.0, 2.0), "power": 0.8},
    "crunch": {"stages": [6.0, 4.0], "tight_hz": 110, "stack": (2.0, -1.5, 1.5), "power": 1.2},
    "lead": {"stages": [8.0, 6.0, 3.0], "tight_hz": 150, "stack": (1.0, 2.5, 1.0), "power": 1.4},
}
BIAS = 0.2


def _triode(x: np.ndarray) -> np.ndarray:
    x = x + BIAS
    y = np.where(x > 0, np.tanh(x), x / (1 + np.abs(x) / 1.5))
    return -(y - np.tanh(BIAS))


def _biquad(kind: str, f0: float, gain_db: float, sr: int, q: float = 0.7) -> tuple[np.ndarray, np.ndarray]:
    """RBJ cookbook shelves and peak."""
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


def amp(x: np.ndarray, sr: int, tone: str) -> np.ndarray:
    cfg = TONES[tone]
    x = sosfilt(butter(1, cfg["tight_hz"], "hp", fs=sr, output="sos"), x)
    up = resample_poly(x, OS, 1)
    osr = sr * OS
    coupling = butter(1, 20, "hp", fs=osr, output="sos")
    miller = butter(1, 9000, "lp", fs=osr, output="sos")
    for gain in cfg["stages"]:
        up = sosfilt(miller, sosfilt(coupling, _triode(gain * up)))
    y = resample_poly(up, 1, OS)[: len(x)]

    bass, mid, treble = cfg["stack"]
    for kind, f0, g in (("low", 120, bass), ("peak", 750, mid), ("high", 3000, treble)):
        b, a = _biquad(kind, f0, g, sr)
        y = lfilter(b, a, y)
    drive = cfg["power"]
    y = np.tanh(drive * y) / np.tanh(drive)
    return cabinet(y, sr)
