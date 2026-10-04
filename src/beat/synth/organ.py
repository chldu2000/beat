"""Tonewheel organ (Hammond B-3 style): 91 tonewheels -> key contacts and drawbars -> vibrato scanner ->
expression pedal -> preamp and Leslie amp (tube overdrive) -> Leslie rotary speaker (stereo).

The wheels turn all the time and are shared by the keys, so two keys that use the same wheel add up
in phase. Each key closes nine contacts, one per drawbar, a fraction of a millisecond apart and with
some bounce; switching a running wheel on and off is the key click. Percussion takes the 2nd or 3rd
harmonic of the keys held when it fires, and fires only when every key was up (single trigger).
There is no touch sensitivity: note velocity sets the expression pedal, which sets the level into the
preamp and so how hard the organ is driven.
"""

import numpy as np
from numba import njit
from scipy.signal import butter, resample_poly, sosfilt

from ..compile import Control, Event
from ..song import Instrument
from . import leslie, registration
from .registration import FOOTAGES, Registration

# Tonewheel generator: a 20 Hz synchronous motor drives 12 gear pairs; within a gear pair the wheels
# have 2, 4, 8 ... teeth (one wheel per octave). Wheel 0 is C1.
MOTOR_HZ = 20.0
GEARS = ((85, 104), (71, 82), (67, 73), (105, 108), (103, 100), (84, 77),
         (74, 64), (98, 80), (96, 74), (88, 64), (67, 46), (108, 70))
N_WHEELS = 91
WHEEL0_PITCH = 24
LEAK_DB = (-52.0, -40.0)  # crosstalk from the other wheels in a wheel's compartment (+-24, +-48)
TRIM_DB = 1.0  # wheel-to-wheel level spread
OS = 4

CONTACT_SPREAD_S = 0.0015  # the nine contacts of a key close this far apart
RELEASE_SPREAD_S = 0.001
PERC_TAU = {"fast": 0.07, "slow": 0.25}  # percussion decay time constant, s
PERC_LEVEL = 1.0
PERC_DRAWBAR_DB = -3.0  # drawbars drop when percussion is on (and the 1' drawbar is cut)

GEN_LEVEL = 0.05  # generator into the preamp: a three-note chord on rock drawbars peaks near 0.4
EXPRESSION_DB = 30.0  # expression pedal range per unit of velocity; velocity 0.63 (mf, the default) is 0 dB
EXPRESSION_REF = 0.63
EXPRESSION_S = 0.04  # how fast the pedal follows a new dynamic
DRIVE_DB = 30.0  # preamp gain at drive 1
BIAS = 0.15

SCANNER_HZ = 6.87
SCANNER_DEPTH_S = {"1": 0.0004, "2": 0.0007, "3": 0.0011}  # peak-to-peak delay sweep for V1-V3 / C1-C3


def wheel_freqs() -> np.ndarray:
    idx = np.arange(N_WHEELS)
    ratio = np.array([n / d for n, d in GEARS])[idx % 12]
    return MOTOR_HZ * ratio * 2 * 2.0 ** (idx // 12)


def wheel_for(pitch: int) -> int:
    """Wheel index for a pitch; above the top wheel (F#8) the drawbar folds back an octave."""
    w = pitch - WHEEL0_PITCH
    while w >= N_WHEELS:
        w -= 12
    while w < 0:
        w += 12
    return w


def _wheel_tables() -> tuple[np.ndarray, ...]:
    """Fixed per-instrument character: wheel phases, level trims, harmonics and crosstalk."""
    rng = np.random.default_rng(1955)
    phases = rng.uniform(0, 2 * np.pi, N_WHEELS)
    trims = 10 ** (rng.uniform(-TRIM_DB, TRIM_DB, N_WHEELS) / 20)
    idx = np.arange(N_WHEELS)
    h2 = np.full(N_WHEELS, 0.02)
    h3 = np.where(idx < 12, 0.08, 0.015)  # the bottom octave's wheels are less sinusoidal
    offsets = np.array([-48, -24, 24, 48])
    leak_w = idx[:, None] + offsets[None, :]
    leak_g = 10 ** (rng.uniform(*LEAK_DB, (N_WHEELS, 4)) / 20) * ((leak_w >= 0) & (leak_w < N_WHEELS))
    return phases, trims, h2, h3, np.clip(leak_w, 0, N_WHEELS - 1), leak_g


@njit(cache=True)
def _wheels_kernel(n, sr, omega, phases, trims, h2, h3, leak_w, leak_g,
                   s_wheel, s_start, s_end, s_gain, s_ramp, s_tau, s_t0):
    """Add each contact segment: wheel (plus crosstalk) times a trapezoid, optionally decaying."""
    out = np.zeros(n)
    for s in range(len(s_wheel)):
        i0 = max(0, int(s_start[s] * sr))
        i1 = min(n, int(s_end[s] * sr) + 1)
        w = s_wheel[s]
        ramp = s_ramp[s]
        for i in range(i0, i1):
            t = i / sr
            env = min(1.0, (t - s_start[s]) / ramp, (s_end[s] - t) / ramp)
            if env <= 0.0:
                continue
            if s_tau[s] > 0.0:
                env *= np.exp(-(t - s_t0[s]) / s_tau[s])
            env *= s_gain[s]
            acc = 0.0
            for k in range(5):
                if k == 0:
                    ww, g = w, 1.0
                else:
                    ww, g = leak_w[w, k - 1], leak_g[w, k - 1]
                    if g == 0.0:
                        continue
                th = omega[ww] * i + phases[ww]
                sn = np.sin(th)
                acc += g * trims[ww] * (sn + h2[ww] * 2.0 * sn * np.cos(th) + h3[ww] * (3.0 * sn - 4.0 * sn ** 3))
            out[i] += env * acc
    return out


def _contact(segs: list, wheel: int, on: float, off: float, gain: float, ramp: float, bounces: int,
             rng: np.random.Generator, tau: float = 0.0, t0: float = 0.0) -> None:
    """One key contact: a few bounces, then closed from `on` to `off`, maybe a bounce on release."""
    t = on
    for _ in range(int(rng.integers(0, bounces + 1))):
        length = rng.uniform(0.00005, 0.0003)
        segs.append((wheel, t, t + length, gain, ramp, tau, t0))
        t += length + rng.uniform(0.00005, 0.0004)
    off = max(off, t + 2 * ramp)
    segs.append((wheel, t, off, gain, ramp, tau, t0))
    for _ in range(int(rng.integers(0, bounces // 2 + 1))):
        t = off + rng.uniform(0.00005, 0.0004)
        segs.append((wheel, t, t + rng.uniform(0.00005, 0.0002), gain, ramp, tau, t0))


def contact_segments(events: list[Event], reg: Registration, rng: np.random.Generator) -> list[tuple]:
    levels = [10 ** (-3 * (8 - int(c)) / 20) if c != "0" else 0.0 for c in reg.drawbars]
    perc = reg.percussion != "off"
    if perc:
        levels = [lv * 10 ** (PERC_DRAWBAR_DB / 20) for lv in levels[:8]] + [0.0]
        perc_step = 12 if reg.percussion.startswith("2nd") else 19
        perc_tau = PERC_TAU["slow" if reg.percussion.endswith("slow") else "fast"]
    ramp = 0.002 * 0.015 ** reg.click  # contact make/break time: 2 ms at click 0, 0.03 ms at click 1
    bounces = round(4 * reg.click)

    segs: list[tuple] = []
    held_until = -1.0  # last release among the keys pressed so far
    trigger = 0.0
    for ev in sorted(events, key=lambda e: (e.time, e.pitch)):
        on, off = ev.time, ev.time + ev.dur
        if on >= held_until - 1e-3:  # every key was up: percussion fires again
            trigger = on
        held_until = max(held_until, off)
        for footage, level in zip(FOOTAGES, levels):
            if level > 0:
                _contact(segs, wheel_for(ev.pitch + footage), on + rng.uniform(0, CONTACT_SPREAD_S),
                         off + rng.uniform(0, RELEASE_SPREAD_S), level, ramp, bounces, rng)
        if perc:
            _contact(segs, wheel_for(ev.pitch + perc_step), on + rng.uniform(0, CONTACT_SPREAD_S),
                     off + rng.uniform(0, RELEASE_SPREAD_S), PERC_LEVEL, ramp, 0, rng, perc_tau, trigger)
    return segs


def tonewheels(events: list[Event], reg: Registration, n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    segs = contact_segments(events, reg, rng)
    if not segs:
        return np.zeros(n)
    cols = list(zip(*segs))
    phases, trims, h2, h3, leak_w, leak_g = _wheel_tables()
    omega = 2 * np.pi * wheel_freqs() / sr
    return _wheels_kernel(n, float(sr), omega, phases, trims, h2, h3, leak_w, leak_g,
                          np.array(cols[0], dtype=np.int64), *(np.array(c, dtype=np.float64) for c in cols[1:]))


def expression(events: list[Event], n: int, sr: int) -> np.ndarray:
    """Pedal gain: follows the velocity of the latest onset (the loudest note of a chord)."""
    onsets: dict[int, float] = {}
    for ev in events:
        i = int(ev.time * sr)
        onsets[i] = max(onsets.get(i, 0.0), ev.velocity)
    times = np.array(sorted(onsets))
    vel = np.array([onsets[i] for i in times])
    step = vel[np.clip(np.searchsorted(times, np.arange(n), "right") - 1, 0, None)]
    a = 1 - np.exp(-1 / (EXPRESSION_S * sr))
    smooth = sosfilt(np.array([[a, 0, 0, 1, a - 1, 0]]), step - step[0]) + step[0]
    return 10 ** (EXPRESSION_DB * (smooth - EXPRESSION_REF) / 20)


def scanner(x: np.ndarray, mode: str, sr: int) -> np.ndarray:
    """Vibrato scanner: a delay line swept by a triangle at 6.87 Hz; chorus mixes it with the dry signal."""
    if mode == "off":
        return x
    t = np.arange(len(x)) / sr
    tri = 2 * np.abs((t * SCANNER_HZ) % 1.0 - 0.5)
    delay = (0.0002 + SCANNER_DEPTH_S[mode[1]] * tri) * sr
    wet = np.interp(np.arange(len(x)) - delay, np.arange(len(x)), x, left=0.0)
    wet = sosfilt(butter(1, 6000, "lp", fs=sr, output="sos"), wet)  # the delay line's LC sections
    return 0.5 * (x + wet) if mode[0] == "c" else wet


def preamp(x: np.ndarray, drive: float, sr: int) -> np.ndarray:
    """Preamp and Leslie amp: an asymmetric tube stage pushed by `drive`, then a softer power stage."""
    up = resample_poly(x, OS, 1)
    k = 10 ** (DRIVE_DB * drive / 20)
    up = np.tanh(k * up + BIAS) - np.tanh(BIAS)
    up = np.tanh(1.5 * up) / 1.5
    y = resample_poly(up, 1, OS)[: len(x)]
    return sosfilt(butter(1, 40, "hp", fs=sr, output="sos"), y)


def render_part(inst: Instrument, events: list[Event], n: int, sr: int, rng: np.random.Generator,
                controls: list[Control] = ()) -> np.ndarray:
    reg, _ = registration.parse(inst.model)
    x = tonewheels(events, reg, n, sr, rng) * GEN_LEVEL
    x = scanner(x, reg.vibrato, sr) * expression(events, n, sr)
    return leslie.rotary(preamp(x, reg.drive, sr), leslie.speed_track(controls, n, sr), sr)
