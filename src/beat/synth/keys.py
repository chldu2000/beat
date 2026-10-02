"""Keyboards: drawbar organ (additive + crude Leslie) and a simple inharmonic piano."""

import numpy as np

from ..compile import Event

# 16', 8', 5 1/3', 4' footages as multiples of the played pitch.
DRAWBARS = [(0.5, 1.0), (1.0, 1.0), (1.5, 0.8), (2.0, 0.5)]


def organ_note(ev: Event, sr: int, rng: np.random.Generator) -> np.ndarray:
    f0 = 440.0 * 2 ** ((ev.pitch - 69) / 12)
    n = int((ev.dur + 0.06) * sr)
    t = np.arange(n) / sr
    y = sum(level * np.sin(2 * np.pi * f0 * mult * t + rng.uniform(0, 2 * np.pi)) for mult, level in DRAWBARS)
    env = np.minimum(1.0, t / 0.004)
    off = int(ev.dur * sr)
    env[off:] *= np.exp(-np.arange(n - off) / (0.012 * sr))
    click = np.zeros(n)
    k = min(n, int(0.003 * sr))
    click[:k] = rng.uniform(-1, 1, k) * 0.15
    return (y * env + click) * (0.4 + 0.6 * ev.velocity)


def leslie(x: np.ndarray, sr: int, rate: float = 6.3) -> np.ndarray:
    """Rotating speaker approximation: Doppler via a modulated delay plus amplitude modulation."""
    t = np.arange(len(x)) / sr
    phase = 2 * np.pi * rate * t
    delay = (0.0015 + 0.0004 * np.sin(phase)) * sr
    idx = np.arange(len(x)) - delay
    y = np.interp(idx, np.arange(len(x)), x, left=0.0)
    y *= 0.85 + 0.15 * np.sin(phase + 0.5)
    return np.tanh(1.3 * y)


def piano_note(ev: Event, sr: int, rng: np.random.Generator) -> np.ndarray:
    f0 = 440.0 * 2 ** ((ev.pitch - 69) / 12)
    base_t60 = float(np.clip(10.0 * (65.4 / f0) ** 0.5, 1.5, 12.0))
    n = int((ev.dur + 0.3) * sr)
    t = np.arange(n) / sr
    B = 0.0004  # string stiffness -> partials sharpen with index
    y = np.zeros(n)
    for k in range(1, 13):
        fk = k * f0 * np.sqrt(1 + B * k * k)
        if fk > sr / 2.2:
            break
        amp = ev.velocity ** (0.5 + 0.15 * k) / k ** 1.1
        y += amp * np.sin(2 * np.pi * fk * t) * 10 ** (-3 * t / (base_t60 / (1 + 0.35 * k)))
    k = min(n, int(0.004 * sr))
    y[:k] += rng.uniform(-1, 1, k) * 0.05 * ev.velocity
    off = int(ev.dur * sr)
    y[off:] *= np.exp(-np.arange(n - off) / (0.08 * sr))
    return y
