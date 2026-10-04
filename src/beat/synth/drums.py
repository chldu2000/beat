"""Drum kit by subtractive synthesis. Each lane gets a few round-robin variants rendered up front."""

import numpy as np
from scipy.signal import butter, sosfilt

from ..compile import Event
from ..song import Instrument

ROUND_ROBIN = 4
# lane -> (gain, pan)  pan from the audience's view, -1 left .. 1 right
LANE_MIX = {
    "bd": (1.0, 0.0), "sd": (0.85, 0.0), "ss": (0.5, 0.0),
    "hh": (0.3, 0.35), "ho": (0.3, 0.35), "hp": (0.22, 0.35),
    "t1": (0.7, 0.2), "t2": (0.7, -0.1), "t3": (0.75, -0.35),
    "cr": (0.35, 0.45), "cr2": (0.35, -0.45), "rd": (0.3, -0.5),
    "rb": (0.3, -0.5), "ch": (0.35, -0.6),
}
_HAT_FREQS = np.array([205.3, 304.4, 369.6, 522.7, 540.0, 800.0])


def _band(x, sr, lo=None, hi=None, order=2):
    if lo and hi:
        return sosfilt(butter(order, [lo, hi], "bp", fs=sr, output="sos"), x)
    if lo:
        return sosfilt(butter(order, lo, "hp", fs=sr, output="sos"), x)
    return sosfilt(butter(order, hi, "lp", fs=sr, output="sos"), x)


def _t(sr, seconds):
    return np.arange(int(seconds * sr)) / sr


def _metal(t, scale, rng):
    ph = rng.uniform(0, 2 * np.pi, len(_HAT_FREQS))
    return sum(np.sign(np.sin(2 * np.pi * f * scale * t + p)) for f, p in zip(_HAT_FREQS, ph)) / 6


def kick(sr, rng):
    t = _t(sr, 0.6)
    f = 48 + 110 * np.exp(-t / 0.035)
    body = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t / 0.3)
    click = _band(rng.uniform(-1, 1, len(t)), sr, lo=1500) * np.exp(-t / 0.004)
    return body + 0.4 * click


def snare(sr, rng):
    t = _t(sr, 0.5)
    f = 185 * rng.uniform(0.98, 1.02)
    tone = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 1.78 * f * t)) * np.exp(-t / 0.07)
    wires = _band(rng.uniform(-1, 1, len(t)), sr, 1500, 9000) * np.exp(-t / 0.16)
    return 0.6 * tone + 1.4 * wires


def side_stick(sr, rng):
    t = _t(sr, 0.15)
    return (_band(rng.uniform(-1, 1, len(t)), sr, 1500, 4500) * np.exp(-t / 0.015)
            + 0.5 * np.sin(2 * np.pi * 620 * t) * np.exp(-t / 0.03))


def hat(sr, rng, decay):
    t = _t(sr, max(0.15, decay * 6))
    metal = _metal(t, 1.0, rng) + 0.6 * rng.uniform(-1, 1, len(t))
    return _band(metal, sr, lo=7000, order=4) * np.exp(-t / decay)


def tom(sr, rng, f):
    t = _t(sr, 1.0)
    f = f * rng.uniform(0.99, 1.01) * (1 + 0.25 * np.exp(-t / 0.06))
    body = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t / 0.38)
    stick = _band(rng.uniform(-1, 1, len(t)), sr, 800, 5000) * np.exp(-t / 0.01)
    return body + 0.3 * stick


def cymbal(sr, rng, decay, low, noise):
    t = _t(sr, decay * 4)
    metal = _metal(t, 2.3, rng) + _metal(t, 3.7, rng) + noise * rng.uniform(-1, 1, len(t))
    env = np.minimum(1.0, t / 0.002) * np.exp(-t / decay)
    return _band(metal, sr, lo=low, order=4) * env


def bell(sr, rng):
    t = _t(sr, 2.0)
    y = sum(a * np.sin(2 * np.pi * 820 * m * t) for m, a in [(1, 1.0), (2.41, 0.6), (3.93, 0.4)])
    return 0.5 * y * np.exp(-t / 0.6) + 0.5 * cymbal(sr, rng, 0.5, 4000, 0.3)[:len(t)]


_VOICES = {
    "bd": kick, "sd": snare, "ss": side_stick,
    "hh": lambda sr, rng: hat(sr, rng, 0.045),
    "ho": lambda sr, rng: hat(sr, rng, 0.45),
    "hp": lambda sr, rng: 0.6 * hat(sr, rng, 0.03),
    "t1": lambda sr, rng: tom(sr, rng, 196), "t2": lambda sr, rng: tom(sr, rng, 147),
    "t3": lambda sr, rng: tom(sr, rng, 98),
    "cr": lambda sr, rng: cymbal(sr, rng, 1.4, 3000, 0.8),
    "cr2": lambda sr, rng: cymbal(sr, rng, 1.2, 3500, 0.8),
    "rd": lambda sr, rng: cymbal(sr, rng, 1.1, 5000, 0.15),
    "rb": bell,
    "ch": lambda sr, rng: cymbal(sr, rng, 0.9, 1500, 1.2),
}


def render_kit(events: list[Event], n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    """Render all drum events of one part into a stereo (n, 2) buffer."""
    out = np.zeros((n, 2))
    cache: dict[str, list[np.ndarray]] = {}
    chokers = sorted(ev.time for ev in events if ev.lane in ("hh", "hp", "ho"))

    for ev in events:
        if ev.lane not in cache:
            voices = [_VOICES[ev.lane](sr, rng) for _ in range(ROUND_ROBIN)]
            cache[ev.lane] = [v / (np.max(np.abs(v)) + 1e-9) for v in voices]
        hits = [(ev.time, ev.velocity)]
        if ev.arts.get("flam"):
            hits.append((ev.time - 0.025, ev.velocity * 0.5))
        for time, vel in hits:
            sample = cache[ev.lane][rng.integers(ROUND_ROBIN)].copy()
            if ev.lane == "ho":
                # An open hi-hat rings until the next closed hit or pedal chokes it.
                nxt = next((c for c in chokers if c > time + 1e-4), None)
                if nxt is not None:
                    k = int((nxt - time) * sr)
                    if k < len(sample):
                        sample[k:] *= np.exp(-np.arange(len(sample) - k) / (0.008 * sr))
            gain, pan = LANE_MIX[ev.lane]
            start = int(max(0.0, time) * sr)
            seg = sample[: max(0, n - start)] * gain * vel ** 1.4
            left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            out[start:start + len(seg), 0] += seg * left
            out[start:start + len(seg), 1] += seg * right
    return out


def render_part(inst: Instrument, events: list[Event], n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    return render_kit(events, n, sr, rng)
