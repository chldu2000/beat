"""Plucked electric strings (guitar, bass): fret assignment -> one persistent waveguide per string -> pickup.

Notes become commands to the string they are played on: a stroke (excitation plus a partial stop
of what was ringing), a fret change without a new stroke for `!h` / `!p`, and damping when the
fretting hand releases the note. Palm mutes and dead notes are loss settings of the same loop.
Instruments differ only in their `StringModel` and in the amp chain after the pickup.
"""

from dataclasses import dataclass

import numpy as np
from scipy.signal import lfilter

from ..compile import Event
from ..song import Instrument
from . import fretboard, waveguide

# Loss settings: t60 near DC and at F_HIGH, in seconds.
F_HIGH = 4000.0
RELEASE_GAP = 0.001  # s; a note on the same string within this of the release keeps the string undamped
DAMPED = (0.09, 0.012)  # fretting hand released (or muting an open string)
PALM_MUTE = (0.25, 0.035)
DEAD = (0.025, 0.008)
STOP = 0.7  # how much of the ringing a new stroke on the same string stops
LEGATO_GLIDE_S = 0.0003
DAMP_GLIDE_S = 0.002  # the loss change moves the loop's tuning delay; glide it so it does not click
TENSION_GLIDE_S = 0.12  # how long a hard stroke's pitch takes to settle


@dataclass(frozen=True)
class StringModel:
    scale_m: float  # string length, nut to bridge
    pluck_m: float  # picking / plucking point, distance from the bridge
    pickup_m: float  # pickup, distance from the bridge
    pickup_hz: float  # pickup inductance with cable capacitance: resonant lowpass
    pickup_q: float
    level: float  # string signal into the amp, for a full-velocity single note
    t60_ref: float  # sustain of the fundamental at f_ref, seconds; scales with (f_ref / f0) ** 0.5
    f_ref: float
    t60_range: tuple[float, float]
    damp_hz: float  # partials around this frequency decay twice as fast as the fundamental
    b_wound: float  # inharmonicity coefficient of an open wound string
    b_plain: float
    plain_from: int  # open strings at or above this MIDI pitch are plain (unwound)
    width_soft: float  # stroke pulse width at the lowest velocity, seconds (wider = darker)
    width_hard: float  # ... and at full velocity
    noise: float  # stroke noise (pick or finger) relative to the stroke
    tension_cents: float  # a full-velocity stroke starts this much sharp (tension modulation)

    def sustain(self, f0: float) -> tuple[float, float]:
        t60 = float(np.clip(self.t60_ref * (self.f_ref / f0) ** 0.5, *self.t60_range))
        return t60, t60 / (1 + (F_HIGH / self.damp_hz) ** 2)

    def stiffness(self, open_pitch: int, fret: int) -> float:
        """B grows as the fret shortens the string."""
        b_open = self.b_plain if open_pitch >= self.plain_from else self.b_wound
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


def _pickup_filter(m: StringModel, sr: int) -> tuple[np.ndarray, np.ndarray]:
    w = 2 * np.pi * m.pickup_hz / sr
    alpha = np.sin(w) / (2 * m.pickup_q)
    cw = np.cos(w)
    b = np.array([(1 - cw) / 2, 1 - cw, (1 - cw) / 2])
    a = np.array([1 + alpha, -2 * cw, 1 - alpha])
    return b / a[0], a / a[0]


class _String:
    def __init__(self, model: StringModel) -> None:
        self.model = model
        self.segs: list[tuple] = []  # (start, delay, g, a, c, tap, stop, glide)
        self.excs: list[tuple[int, np.ndarray]] = []

    def seg(self, start: int, f0: float, fret: int, B: float, t60: tuple[float, float], sr: int,
            stop: float = 0.0, glide: int = 0) -> None:
        d, g, a, c = waveguide.loop_params(f0, B, t60[0], t60[1], F_HIGH, sr)
        length = self.model.scale_m * 2 ** (-fret / 12)
        tap = max(1.0, self.model.pickup_m / length * sr / f0)
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


def strings_signal(model: StringModel, inst: Instrument, events: list[Event], n: int, sr: int,
                   rng: np.random.Generator) -> np.ndarray:
    """Pickup signal of all strings, before the amp."""
    positions = fretboard.assign(events, inst.tuning, inst.frets)
    per_string: dict[int, list[tuple[Event, int]]] = {}
    for ev, (s, fret) in zip(events, positions):
        per_string.setdefault(s, []).append((ev, fret))

    out = np.zeros(n)
    for s, notes in per_string.items():
        notes.sort(key=lambda nf: nf[0].time)
        string = _String(model)
        open_pitch = inst.tuning[s]
        for i, (ev, fret) in enumerate(notes):
            start = max(0, int(round(ev.time * sr)))
            if start >= n:
                break
            cents = rng.normal(0, 1.0)
            f0 = 440.0 * 2 ** ((ev.pitch - 69) / 12 + cents / 1200)
            period = sr / f0
            B = model.stiffness(open_pitch, fret)
            length = model.scale_m * 2 ** (-fret / 12)
            vel = float(np.clip(ev.velocity * rng.normal(1, 0.04), 0.05, 1.0))
            arts = ev.arts
            t60 = DEAD if arts.get("x") else PALM_MUTE if arts.get("pm") else model.sustain(f0)

            if (arts.get("h") or arts.get("p")) and i > 0:
                # Fret change on a ringing string: no stroke, only the finger's tap or pluck.
                string.seg(start, f0, fret, B, t60, sr, glide=int(LEGATO_GLIDE_S * sr))
                beta, amp_ = (0.08, 0.35 * vel) if arts.get("h") else (0.06, 0.5 * vel)
                string.excs.append((start, _excitation(period, beta, amp_, 0.0008, 0.0, sr, rng)))
            else:
                if model.tension_cents > 0:
                    # A hard stroke stretches the string: start sharp, settle to pitch.
                    sharp = f0 * 2 ** (model.tension_cents * vel * vel / 1200)
                    string.seg(start, sharp, fret, B, t60, sr, stop=STOP)
                    string.seg(start + 1, f0, fret, B, t60, sr, glide=int(TENSION_GLIDE_S * sr))
                else:
                    string.seg(start, f0, fret, B, t60, sr, stop=STOP)
                beta = min(0.45, model.pluck_m / length * rng.uniform(0.9, 1.1))
                width = (model.width_soft - (model.width_soft - model.width_hard) * vel) * rng.uniform(0.85, 1.15)
                noise = 0.6 if arts.get("x") else model.noise
                string.excs.append((start, _excitation(period, beta, vel ** 1.2, width, noise, sr, rng)))

            end = int(round((ev.time + ev.dur) * sr))
            nxt = notes[i + 1][0].time if i + 1 < len(notes) else None
            if end < n and (nxt is None or nxt > ev.time + ev.dur + RELEASE_GAP):
                string.seg(end, f0, fret, B, DAMPED, sr, glide=int(DAMP_GLIDE_S * sr))
        string.run(out, sr, sr / (440.0 * 2 ** ((open_pitch - 69) / 12)) * 1.1)

    b, a = _pickup_filter(model, sr)
    return lfilter(b, a, out) * model.level
