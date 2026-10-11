"""Plucked electric strings (guitar, bass): fret assignment -> one persistent waveguide per string -> pickup.

Notes become commands to the string they are played on: a stroke (excitation plus a partial stop
of what was ringing), a fret change without a new stroke for `!h` / `!p` / `!sl`, and damping when
the fretting hand releases the note. Palm mutes and dead notes are loss settings of the same loop.
Bends (and their release on a tied note), vibrato, slides and falls are a pitch curve per note
(cents against the written pitch) that moves the loop delay sample by sample; a natural harmonic (`!harm`) is the loop of the string section
between the bridge and the node, excited the way the full string would be.
Instruments differ only in their `StringModel` and in the amp chain after the pickup.
"""

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, lfilter, sosfilt

from ..checks import HARMONICS
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
LEGATO_GAP = 0.03  # s; a legato note (h / p / sl) this soon after the previous one keeps it ringing
BEND_S = (0.08, 0.04)  # time to reach a bend: base + per semitone
VIB_HZ = 5.5
VIB_DELAY_S = 0.12  # vibrato on a note's own onset starts after this ...
VIB_RAMP_S = 0.2  # ... and reaches full depth over this
SLIDE_S = (0.03, 0.012)  # slide time: base + per fret, at most SLIDE_MAX of the note
SLIDE_MAX = 0.4
SLIDE_STEP_S = 0.006  # crossing one fret
SLIDE_IN = 3  # frets below the target that a slide with nothing before it starts from
SLIDE_NOISE = 0.03  # finger friction on a wound string, relative to a full stroke (plain strings: a third)
FALL_S = 0.25  # a fall takes the last this-much of the note (at most half of it) ...
FALL_FRETS = 7  # ... to slide down this many frets
FALL_LOSS = (0.3, 0.05)  # the finger eases off while it slides away
HOLD_S = 0.1  # a bend or vibrato holds this long into the damped release
HARM_LEVEL = 0.5


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
    vib_cents: float = 35.0  # vibrato depth; a fretted string can only be pushed sharp, so it only goes up

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
        self.mods: list[tuple[int, np.ndarray]] = []  # (start, delay offset per sample); no overlaps

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
        cols = list(zip(*segs))
        waveguide.run_string(
            out, int(np.ceil(np.log2(max_period + 16))),
            np.array(cols[0], dtype=np.int64), *(np.array(col, dtype=np.float64) for col in cols[1:7]),
            np.array(cols[7], dtype=np.int64), *_blocks(_merge(self.excs)), *_blocks(self.mods))


def _merge(blocks: list[tuple[int, np.ndarray]]) -> list[tuple[int, np.ndarray]]:
    """Sum overlapping excitations (the loop plays one at a time)."""
    out: list[tuple[int, np.ndarray]] = []
    for start, data in sorted(blocks, key=lambda b: b[0]):
        if out and start < out[-1][0] + len(out[-1][1]):
            s0, d0 = out[-1]
            d = np.zeros(max(len(d0), start - s0 + len(data)))
            d[:len(d0)] += d0
            d[start - s0:start - s0 + len(data)] += data
            out[-1] = (s0, d)
        else:
            out.append((start, data))
    return out


def _blocks(blocks: list[tuple[int, np.ndarray]]) -> tuple[np.ndarray, ...]:
    """(starts, offsets, lengths, data) for the numba loop."""
    blocks = sorted(blocks, key=lambda b: b[0])
    lens = np.array([len(d) for _, d in blocks], dtype=np.int64)
    offs = np.concatenate([[0], np.cumsum(lens)[:-1]]).astype(np.int64) if blocks else lens
    data = np.concatenate([d for _, d in blocks]) if blocks else np.zeros(1)
    return np.array([s for s, _ in blocks], dtype=np.int64), offs, lens, data


def _smoothstep(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def _bend_schedule(arts: dict, beats: float, dur: float) -> list[tuple[float, float]]:
    """(seconds into the note, semitones the string is bent to) for each bend move, in order."""
    moves = [(0.0, arts["bend"])] if "bend" in arts else []
    for t in arts.get("tied", []):
        if "bend" in t or t.get("release"):
            moves.append((t["at"] / beats * dur, t.get("bend", 0.0) if "bend" in t else 0.0))
    return moves


def _vib_start(arts: dict, beats: float, dur: float) -> float | None:
    if arts.get("vib"):
        return min(VIB_DELAY_S, 0.3 * dur)
    return next((t["at"] / beats * dur for t in arts.get("tied", []) if t.get("vib")), None)


def _steps(t: np.ndarray, t0: float, T: float, k: int, ease_in: bool = False) -> np.ndarray:
    """Frets crossed (0 .. k) by a slide of k frets starting at t0 and taking T seconds."""
    w = min(SLIDE_STEP_S, T / k)
    at = [(j + 0.5) / k for j in range(k)]
    if ease_in:
        at = [np.sqrt(a) for a in at]  # starts slowly, then lets go
    return sum(_smoothstep((t - t0 - a * T) / w + 0.5) for a in at)


def _pitch_curve(m: StringModel, arts: dict, slide: int, fall: tuple[float, int] | None, beats: float,
                 dur: float, length: int, sr: int, rng: np.random.Generator) -> np.ndarray | None:
    """Cents against the written pitch over `length` samples from the onset, or None if flat.

    `slide`: frets from where a slide starts to the written note (negative = from below).
    `fall`: (seconds into the note, frets) of a slide down and away at the end of the note.
    """
    bends = _bend_schedule(arts, beats, dur)
    vib_at = _vib_start(arts, beats, dur)
    if not (slide or bends or vib_at is not None or fall):
        return None
    t = np.arange(length) / sr
    cents = np.zeros(length)
    if slide:
        # Fret by fret: the pitch steps over each fret wire, smoothed by the finger.
        k = abs(slide)
        T = min(SLIDE_S[0] + SLIDE_S[1] * k, SLIDE_MAX * dur)
        cents += 100 * slide * (1 - _steps(t, 0.0, T, k) / k)
    bent = np.zeros(length)
    level = 0.0
    for t0, target in bends:
        move = target - level
        bent += 100 * move * _smoothstep((t - t0) / (BEND_S[0] + BEND_S[1] * abs(move)))
        level = target
    cents += bent
    if vib_at is not None:
        rate = VIB_HZ * rng.uniform(0.92, 1.08) * (1 + 0.04 * np.sin(2 * np.pi * rng.uniform(0.3, 0.7) * t))
        phase = 2 * np.pi * np.cumsum(rate) / sr
        depth = m.vib_cents * rng.uniform(0.85, 1.15) * _smoothstep((t - vib_at) / VIB_RAMP_S)
        wave = depth * (0.5 - 0.5 * np.cos(phase - phase[min(length - 1, int(vib_at * sr))]))
        cents += wave * (1 - 2 * np.clip(bent / 100, 0, 1))  # on a bent string the hand lets it down a little
    if fall:
        t0, k = fall
        cents -= 100 * _steps(t, t0, dur - t0, k, ease_in=True)
    return cents


def _slide_noise(length: int, wound: bool, vel: float, sr: int, rng: np.random.Generator) -> np.ndarray:
    sos = butter(2, (600.0, min(4000.0, 0.45 * sr)), "bandpass", fs=sr, output="sos")
    env = np.hanning(length + 2)[1:-1]
    return sosfilt(sos, rng.normal(0, 1, length)) * env * SLIDE_NOISE * vel * (1.0 if wound else 0.33)


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
        f_open = 440.0 * 2 ** ((open_pitch - 69) / 12)
        for i, (ev, fret) in enumerate(notes):
            start = max(0, int(round(ev.time * sr)))
            if start >= n:
                break
            arts = ev.arts
            prev = notes[i - 1] if i > 0 else None
            joined = prev is not None and ev.time - (prev[0].time + prev[0].dur) < LEGATO_GAP
            cents = rng.normal(0, 1.0)
            harm = HARMONICS.get(ev.pitch - open_pitch) if arts.get("harm") else None
            if harm:
                # Touched over the node: only the section from the bridge to the node keeps ringing.
                k, _ = harm
                f0 = f_open * k * 2 ** (cents / 1200)
                B = model.stiffness(open_pitch, 0) * k * k
                fret_len = 12 * np.log2(k)
            else:
                f0 = 440.0 * 2 ** ((ev.pitch - 69) / 12 + cents / 1200)
                B = model.stiffness(open_pitch, fret)
                fret_len = fret
            period = sr / f0
            length = model.scale_m * 2 ** (-fret_len / 12)
            vel = float(np.clip(ev.velocity * rng.normal(1, 0.04), 0.05, 1.0))
            t60 = DEAD if arts.get("x") else PALM_MUTE if arts.get("pm") else model.sustain(f0)
            slide = 0

            if not harm and (arts.get("h") or arts.get("p") or arts.get("sl")) and joined:
                # Fret change on a ringing string: no stroke, only the finger's tap, pluck or slide.
                if arts.get("sl"):
                    string.seg(start, f0, fret, B, t60, sr)
                    p_bends = _bend_schedule(prev[0].arts, float(prev[0].beats) or 1.0, prev[0].dur)
                    p_from = prev[0].pitch + (p_bends[-1][1] if p_bends else 0.0)
                    slide = int(round(p_from - ev.pitch))
                    if slide:
                        T = min(SLIDE_S[0] + SLIDE_S[1] * abs(slide), SLIDE_MAX * ev.dur)
                        string.excs.append((start, _slide_noise(max(2, int(T * sr)),
                                                                open_pitch < model.plain_from, vel, sr, rng)))
                else:
                    string.seg(start, f0, fret, B, t60, sr, glide=int(LEGATO_GLIDE_S * sr))
                    beta, amp_ = (0.08, 0.35 * vel) if arts.get("h") else (0.06, 0.5 * vel)
                    string.excs.append((start, _excitation(period, beta, amp_, 0.0008, 0.0, sr, rng)))
            else:
                if model.tension_cents > 0:
                    # A hard stroke stretches the string: start sharp, settle to pitch.
                    sharp = f0 * 2 ** (model.tension_cents * vel * vel / 1200)
                    string.seg(start, sharp, fret_len, B, t60, sr, stop=STOP)
                    string.seg(start + 1, f0, fret_len, B, t60, sr, glide=int(TENSION_GLIDE_S * sr))
                else:
                    string.seg(start, f0, fret_len, B, t60, sr, stop=STOP)
                if arts.get("sl") and not harm:
                    slide = -min(SLIDE_IN, fret)  # nothing to slide from: slide in from a few frets below
                beta = min(0.45, model.pluck_m / length * rng.uniform(0.9, 1.1))
                width = (model.width_soft - (model.width_soft - model.width_hard) * vel) * rng.uniform(0.85, 1.15)
                noise = 0.6 if arts.get("x") else model.noise
                amp_ = vel ** 1.2
                if harm:
                    width, amp_ = width * 2, amp_ * HARM_LEVEL
                string.excs.append((start, _excitation(period, beta, amp_, width, noise, sr, rng)))

            end = int(round((ev.time + ev.dur) * sr))
            fall = None
            if not harm and fret > 0 and (arts.get("fall") or any(t.get("fall") for t in arts.get("tied", []))):
                # Slide down and away: the finger eases off, the pitch drops a few frets, friction noise.
                t0 = ev.dur - min(FALL_S, 0.5 * ev.dur)
                fall = (t0, min(FALL_FRETS, fret))
                f_start = start + int(t0 * sr)
                string.seg(f_start, f0, fret, B, FALL_LOSS, sr, glide=int(DAMP_GLIDE_S * sr))
                string.excs.append((f_start, _slide_noise(max(2, end - f_start), open_pitch < model.plain_from,
                                                          vel, sr, rng)))
            nxt = notes[i + 1][0] if i + 1 < len(notes) else None
            legato_next = nxt is not None and nxt.time - (ev.time + ev.dur) < LEGATO_GAP \
                and any(nxt.arts.get(a) for a in ("h", "p", "sl")) and not nxt.arts.get("harm")
            if end < n and not legato_next and (nxt is None or nxt.time > ev.time + ev.dur + RELEASE_GAP):
                string.seg(end, f0, fret_len, B, DAMPED, sr, glide=int(DAMP_GLIDE_S * sr))

            if not harm:
                stop_at = min(n, end + int(HOLD_S * sr))
                if nxt is not None:
                    stop_at = min(stop_at, max(0, int(round(nxt.time * sr))))
                curve = _pitch_curve(model, arts, slide, fall, float(ev.beats) or 1.0, ev.dur,
                                     stop_at - start, sr, rng) if stop_at > start else None
                if curve is not None:
                    string.mods.append((start, period * (2 ** (-curve / 1200) - 1)))
        string.run(out, sr, sr / f_open * 1.1)

    b, a = _pickup_filter(model, sr)
    return lfilter(b, a, out) * model.level
