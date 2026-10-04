"""Electric guitar: fret assignment -> one persistent waveguide per string -> pickup -> amp -> cabinet.

Notes become commands to the string they are played on: a pick stroke (excitation plus a partial
stop of what was ringing), a fret change without a new stroke for `!h` / `!p`, and damping when
the fretting hand releases the note. Palm mutes and dead notes are loss settings of the same loop.
"""

import numpy as np
from scipy.signal import lfilter

from ..compile import Event
from ..song import Instrument
from . import amp, fretboard, waveguide

SCALE_M = 0.648  # string length, nut to bridge
PICK_M = 0.12  # picking point, distance from the bridge
PICKUP_M = 0.04  # bridge pickup, distance from the bridge
PICKUP_HZ, PICKUP_Q = 3800.0, 1.4  # pickup inductance with cable capacitance: resonant lowpass
LEVEL = 0.35  # string signal into the amp, for a full-velocity single note

# Loss settings: t60 near DC and at F_HIGH, in seconds.
F_HIGH = 4000.0
RELEASE_GAP = 0.001  # s; a note on the same string within this of the release keeps the string undamped
DAMPED = (0.09, 0.012)  # fretting hand released (or muting an open string)
PALM_MUTE = (0.25, 0.035)
DEAD = (0.025, 0.008)
STOP = 0.7  # how much of the ringing a new pick stroke on the same string stops
LEGATO_GLIDE_S = 0.0003
DAMP_GLIDE_S = 0.002  # the loss change moves the loop's tuning delay; glide it so it does not click


def _sustain(f0: float) -> tuple[float, float]:
    t60 = float(np.clip(6.0 * (82.4 / f0) ** 0.5, 1.0, 8.0))
    return t60, t60 / (1 + (F_HIGH / 1500.0) ** 2)


def _stiffness(open_pitch: int, fret: int) -> float:
    """Inharmonicity coefficient: wound strings are less stiff; B grows as the fret shortens the string."""
    b_open = 1.5e-5 if open_pitch < 55 else 4e-5
    return b_open * 2 ** (fret / 6)


def _excitation(period: float, beta: float, amp_: float, width_s: float, noise: float, sr: int,
                rng: np.random.Generator) -> np.ndarray:
    """Velocity-wave pluck: a boxcar of beta * period (the pluck-position comb), smoothed by the pick."""
    box = np.ones(max(1, int(round(beta * period))))
    w = max(2, int(round(width_s * sr)))
    pick = np.hanning(w + 2)[1:-1]
    e = np.convolve(box, pick / pick.sum()) * amp_
    if noise > 0:
        k = min(len(e), int(0.002 * sr))
        e[:k] += rng.normal(0, 1, k) * noise * amp_ * np.linspace(1, 0, k)
    return e


def _pickup_filter(sr: int) -> tuple[np.ndarray, np.ndarray]:
    w = 2 * np.pi * PICKUP_HZ / sr
    alpha = np.sin(w) / (2 * PICKUP_Q)
    cw = np.cos(w)
    b = np.array([(1 - cw) / 2, 1 - cw, (1 - cw) / 2])
    a = np.array([1 + alpha, -2 * cw, 1 - alpha])
    return b / a[0], a / a[0]


class _String:
    def __init__(self) -> None:
        self.segs: list[tuple] = []  # (start, delay, g, a, c, tap, stop, glide)
        self.excs: list[tuple[int, np.ndarray]] = []

    def seg(self, start: int, f0: float, fret: int, B: float, t60: tuple[float, float], sr: int,
            stop: float = 0.0, glide: int = 0) -> None:
        d, g, a, c = waveguide.loop_params(f0, B, t60[0], t60[1], F_HIGH, sr)
        length = SCALE_M * 2 ** (-fret / 12)
        tap = max(1.0, PICKUP_M / length * sr / f0)
        self.segs.append((start, d, g, a, c, tap, stop, glide))

    def run(self, out: np.ndarray, sr: int, max_period: float) -> None:
        if not self.segs:
            return
        segs = sorted(self.segs, key=lambda s: s[0])
        excs = sorted(self.excs, key=lambda e: e[0])
        cols = list(zip(*segs))
        data = np.concatenate([e for _, e in excs]) if excs else np.zeros(1)
        lens = np.array([len(e) for _, e in excs], dtype=np.int64)
        offs = np.concatenate([[0], np.cumsum(lens)[:-1]]).astype(np.int64) if excs else lens
        waveguide.run_string(
            out, int(np.ceil(np.log2(max_period + 16))),
            np.array(cols[0], dtype=np.int64), *(np.array(col, dtype=np.float64) for col in cols[1:7]),
            np.array(cols[7], dtype=np.int64),
            np.array([s for s, _ in excs], dtype=np.int64), offs, lens, data)


def strings_signal(inst: Instrument, events: list[Event], n: int, sr: int,
                   rng: np.random.Generator) -> np.ndarray:
    """Pickup signal of all strings, before the amp."""
    positions = fretboard.assign(events, inst.tuning, inst.frets)
    per_string: dict[int, list[tuple[Event, int]]] = {}
    for ev, (s, fret) in zip(events, positions):
        per_string.setdefault(s, []).append((ev, fret))

    out = np.zeros(n)
    for s, notes in per_string.items():
        notes.sort(key=lambda nf: nf[0].time)
        string = _String()
        open_pitch = inst.tuning[s]
        for i, (ev, fret) in enumerate(notes):
            start = max(0, int(round(ev.time * sr)))
            if start >= n:
                break
            cents = rng.normal(0, 1.0)
            f0 = 440.0 * 2 ** ((ev.pitch - 69) / 12 + cents / 1200)
            period = sr / f0
            B = _stiffness(open_pitch, fret)
            length = SCALE_M * 2 ** (-fret / 12)
            vel = float(np.clip(ev.velocity * rng.normal(1, 0.04), 0.05, 1.0))
            arts = ev.arts
            t60 = DEAD if arts.get("x") else PALM_MUTE if arts.get("pm") else _sustain(f0)

            if (arts.get("h") or arts.get("p")) and i > 0:
                # Fret change on a ringing string: no pick stroke, only the finger's tap or pluck.
                string.seg(start, f0, fret, B, t60, sr, glide=int(LEGATO_GLIDE_S * sr))
                beta, amp_ = (0.08, 0.35 * vel) if arts.get("h") else (0.06, 0.5 * vel)
                string.excs.append((start, _excitation(period, beta, amp_, 0.0008, 0.0, sr, rng)))
            else:
                string.seg(start, f0, fret, B, t60, sr, stop=STOP)
                beta = min(0.45, PICK_M / length * rng.uniform(0.9, 1.1))
                width = (0.0010 - 0.0008 * vel) * rng.uniform(0.85, 1.15)
                noise = 0.6 if arts.get("x") else 0.05
                string.excs.append((start, _excitation(period, beta, vel ** 1.2, width, noise, sr, rng)))

            end = int(round((ev.time + ev.dur) * sr))
            nxt = notes[i + 1][0].time if i + 1 < len(notes) else None
            if end < n and (nxt is None or nxt > ev.time + ev.dur + RELEASE_GAP):
                string.seg(end, f0, fret, B, DAMPED, sr, glide=int(DAMP_GLIDE_S * sr))
        string.run(out, sr, sr / (440.0 * 2 ** ((open_pitch - 69) / 12)) * 1.1)

    b, a = _pickup_filter(sr)
    return lfilter(b, a, out) * LEVEL


def render_part(inst: Instrument, events: list[Event], n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    return amp.amp(strings_signal(inst, events, n, sr, rng), sr, inst.tone or "crunch")
