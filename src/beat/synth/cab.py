"""Synthesized guitar-cabinet impulse response (closed-back 4x12 with a close mic).

Built from a magnitude response in dB (low resonance, cone-breakup presence peaks, steep top
rolloff, small irregularities), made minimum-phase via the real cepstrum, plus a few weak early
reflections from inside the cabinet. Deterministic, so every render uses the same cabinet.
"""

from functools import lru_cache

import numpy as np
from scipy.signal import oaconvolve

IR_SEC = 0.08
NFFT = 16384
# (center Hz, gain dB, width in octaves) of bell-shaped bumps and dips
BUMPS = [(110, 5.0, 0.5), (400, -2.0, 0.8), (1300, -3.5, 0.4), (2300, 4.0, 0.35), (3800, 3.0, 0.3)]
HIGHPASS_HZ, LOWPASS_HZ = 75.0, 5200.0
REFLECTIONS = [(0.0011, -0.18), (0.0023, 0.10), (0.0041, -0.06)]  # (delay s, gain)


def _magnitude_db(f: np.ndarray) -> np.ndarray:
    f = np.maximum(f, 1.0)
    db = -10 * np.log10(1 + (HIGHPASS_HZ / f) ** 8) - 10 * np.log10(1 + (f / LOWPASS_HZ) ** 10)
    for fc, gain, width in BUMPS:
        db += gain * np.exp(-0.5 * (np.log2(f / fc) / width) ** 2)
    # Cone irregularities: smooth random ripple, absent in the lows, about +-2 dB in the highs.
    rng = np.random.default_rng(1234)
    grid = np.linspace(np.log2(20), np.log2(f[-1]), 160)
    ripple = np.convolve(rng.normal(0, 1, len(grid)), np.hanning(7) / np.hanning(7).sum(), "same")
    db += np.interp(np.log2(f), grid, ripple) * 2.5 * np.clip((np.log2(f) - np.log2(600)) / 2, 0, 1)
    return db


def _minimum_phase(log_mag: np.ndarray) -> np.ndarray:
    cep = np.fft.irfft(log_mag, NFFT)
    cep[1:NFFT // 2] *= 2
    cep[NFFT // 2 + 1:] = 0
    return np.fft.irfft(np.exp(np.fft.rfft(cep)), NFFT)


@lru_cache(maxsize=4)
def cab_ir(sr: int) -> np.ndarray:
    f = np.fft.rfftfreq(NFFT, 1 / sr)
    h = _minimum_phase(_magnitude_db(f) * np.log(10) / 20)
    out = h.copy()
    for delay, gain in REFLECTIONS:
        k = int(round(delay * sr))
        out[k:] += gain * np.convolve(h, [0.5, 0.5])[: NFFT - k]  # reflections lose some top end
    n = int(IR_SEC * sr)
    out = out[:n]
    fade = int(0.3 * n)
    out[-fade:] *= np.hanning(2 * fade)[fade:]
    ref = np.abs(np.fft.rfft(out, NFFT))[int(round(1000 * NFFT / sr))]
    return out / ref


def cabinet(x: np.ndarray, sr: int) -> np.ndarray:
    return oaconvolve(x, cab_ir(sr))[: len(x)]
