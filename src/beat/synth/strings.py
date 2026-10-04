"""Plucked strings (guitar, bass): Karplus-Strong with a fractional-delay allpass, plus a simple amp.

Placeholder for the real physical models: no dispersion, single polarization, no string state.
"""

import numpy as np
from scipy.signal import butter, lfilter, resample_poly, sosfilt

from ..compile import Event
from ..song import Instrument
from .engine import mix_notes

DAMP_TAU = 0.025  # seconds; how fast a fretting hand silences the string at note-off
DRIVE = {"clean": 1.2, "crunch": 10.0, "lead": 28.0}


def pluck(f0: float, n: int, sr: int, t60: float, excitation: np.ndarray) -> np.ndarray:
    """One Karplus-Strong voice. Loop = delay N + allpass (fractional) + two-point lowpass."""
    period = sr / f0
    N = int(np.floor(period - 0.6))
    frac = period - 0.5 - N  # in [0.1, 1.1): the lowpass already contributes half a sample
    a = (1 - frac) / (1 + frac)
    g = 10 ** (-3.0 / (t60 * f0))
    # y = x + g * L(z) A(z) z^-N y, with L = (1+z^-1)/2, A = (a+z^-1)/(1+a z^-1)
    den = np.zeros(N + 3)
    den[0], den[1] = 1.0, a
    den[N] -= 0.5 * g * a
    den[N + 1] -= 0.5 * g * (1 + a)
    den[N + 2] -= 0.5 * g
    x = np.zeros(n)
    x[:len(excitation)] = excitation[:n]
    return lfilter([1.0, a], den, x)


def _excitation(period: int, velocity: float, pluck_pos: float, darkness: float,
                rng: np.random.Generator) -> np.ndarray:
    noise = rng.uniform(-1, 1, period)
    d = max(1, int(round(pluck_pos * period)))
    exc = noise.copy()
    exc[d:] -= noise[:-d]  # comb: plucking at a fraction of the string length cancels those modes
    # Harder plucks are brighter.
    c = float(np.clip(darkness + 0.35 * (1 - velocity), 0, 0.97))
    exc = lfilter([1 - c], [1, -c], exc)
    return exc / (np.max(np.abs(exc)) + 1e-9) * velocity


def render_note(ev: Event, inst: Instrument, sr: int, rng: np.random.Generator) -> np.ndarray:
    f0 = 440.0 * 2 ** ((ev.pitch - 69) / 12)
    is_bass = inst.type == "bass"
    velocity = ev.velocity
    darkness = 0.55 if is_bass else 0.2
    t60 = (7.0 if is_bass else 4.0) * min(1.5, (82.4 / f0) ** 0.4)
    if ev.arts.get("h") or ev.arts.get("p"):
        velocity *= 0.6
        darkness += 0.2
    if ev.arts.get("pm"):
        t60, darkness = 0.25, darkness + 0.45
    if ev.arts.get("x"):
        t60, darkness = 0.04, 0.0

    n = int((ev.dur + 0.15) * sr)
    exc = _excitation(int(sr / f0), velocity, rng.uniform(0.12, 0.18), darkness, rng)
    y = pluck(f0, n, sr, t60, exc)

    off = int(ev.dur * sr)
    if off < n:
        y[off:] *= np.exp(-np.arange(n - off) / (DAMP_TAU * sr))
    return y


def amp(x: np.ndarray, sr: int, tone: str) -> np.ndarray:
    """Guitar amp + cab: tighten lows, 4x-oversampled asymmetric tanh, speaker-like band limit."""
    x = sosfilt(butter(2, 110, "hp", fs=sr, output="sos"), x)
    drive, bias = DRIVE[tone], 0.15
    up = resample_poly(x, 4, 1)
    up = np.tanh(drive * up + bias) - np.tanh(bias)
    y = resample_poly(up, 1, 4)[:len(x)]
    cutoff = 6500 if tone == "clean" else 4800
    y = sosfilt(butter(4, cutoff, "lp", fs=sr, output="sos"), y)
    return sosfilt(butter(2, 80, "hp", fs=sr, output="sos"), y)


def bass_chain(x: np.ndarray, sr: int) -> np.ndarray:
    y = np.tanh(1.5 * x)
    return sosfilt(butter(2, 3000, "lp", fs=sr, output="sos"), y)


def render_part(inst: Instrument, events: list[Event], n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    out = mix_notes(events, n, sr, lambda ev: render_note(ev, inst, sr, rng))
    return amp(out, sr, inst.tone) if inst.type == "guitar" else bass_chain(out, sr)
