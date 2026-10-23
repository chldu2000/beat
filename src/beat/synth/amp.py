"""Tube amps. Guitar: pedals, preamp triode stages (4x oversampled), tone stack, power stage, cabinet.

Each triode stage is an asymmetric soft clipper (the grid-conduction side clips harder) with a
coupling-cap highpass and a Miller-capacitance lowpass, and inverts like a real common-cathode stage.
The lead tone's supply sags under a sustained note, so the pick attack stands above the sustain.
Bass: one gentle stage, tone stack, speaker rolloff (no cabinet IR, which would cut the lows).

The pedals sit between the strings and the amp, in `rig.PEDALS` order, oversampled like the preamp. A
part can switch its tone and pedals mid-song (`controls`): each setting runs over its own stretch and the
stretches crossfade before the shared cabinet, so a note still ringing at a switch changes with it.
"""

import numpy as np
from scipy.signal import butter, lfilter, resample_poly, sosfilt

from . import rig
from .cab import cabinet
from .eq import biquad

OS = 4
# tone -> preamp stage gains, pre-distortion highpass (Hz), tone stack (bass, mid, treble dB), power drive,
# supply sag (how much a sustained note pulls the level down after the attack)
TONES = {
    "clean": {"stages": [2.0], "tight_hz": 60, "stack": (2.0, 0.0, 2.0), "power": 0.8},
    "crunch": {"stages": [6.0, 4.0], "tight_hz": 110, "stack": (2.0, -1.5, 1.5), "power": 1.2},
    "lead": {"stages": [5.0, 4.0, 2.0], "tight_hz": 150, "stack": (1.0, 2.5, 1.0), "power": 1.4, "sag": 0.6},
}
BIAS = 0.2
SAG_S = 0.06  # supply sag: the voltage drops under a sustained load and recovers in about this long
BASS_DRIVE = 2.0
# Pedals. Levels are in string-signal units: a firm pick attack peaks around 0.3-0.8.
OD_V = 0.1  # where the overdrive's diodes clip
FUZZ_V = 0.15  # the fuzz's clipping level
FUZZ_BIAS = 0.4  # its transistor bias: one side clips harder (even harmonics)
BOOST_RAIL = 3.0  # the boost's op-amp swings this far before it clips
# Output gain at level 0.5 that keeps the pedal about as loud as bypass (measured on the demo's riffs);
# level moves it +-12 dB.
OD_MAKEUP_DB = -6.0
FUZZ_MAKEUP_DB = 1.0
PRE_S = 0.5  # a stretch of the song starts this much early so the filters and clippers settle
FADE_S = 0.01  # crossfade at a tone or pedal switch


def _triode(x: np.ndarray) -> np.ndarray:
    x = x + BIAS
    y = np.where(x > 0, np.tanh(x), x / (1 + np.abs(x) / 1.5))
    return -(y - np.tanh(BIAS))


def _lp(x: np.ndarray, hz: float, sr: int) -> np.ndarray:
    return sosfilt(butter(1, hz, "lp", fs=sr, output="sos"), x)


def _hp(x: np.ndarray, hz: float, sr: int) -> np.ndarray:
    return sosfilt(butter(1, hz, "hp", fs=sr, output="sos"), x)


def _level(level: float, makeup_db: float = 0.0) -> float:
    return 10 ** ((makeup_db + 24 * (level - 0.5)) / 20)


def overdrive(x: np.ndarray, sr: int, drive: float, tone: float, level: float) -> np.ndarray:
    """Tube Screamer: an op-amp stage whose gain leg is highpassed at 720 Hz and clipped softly by the
    diodes in its feedback, added to the dry signal, so the lows pass unclipped (the mid hump); then a
    treble-cut tone control (800 Hz to 6.4 kHz)."""
    leg = _lp(_hp(x, 720, sr) * (1 + 120 * drive ** 2), 6000, sr)  # up to about 41 dB, rolled off up high
    u = leg / OD_V
    y = x + OD_V * u / (1 + np.abs(u) ** 2.5) ** 0.4
    return _lp(y, 800 * 8 ** tone, sr) * _level(level, OD_MAKEUP_DB)


def fuzz(x: np.ndarray, sr: int, drive: float, tone: float, level: float) -> np.ndarray:
    """Two-transistor fuzz: high gain into a biased clipper (one side clips harder), a second clipping
    stage after an interstage lowpass, and a tone control that blends a lowpass with a highpass, scooping
    the mids in the middle."""
    u = _hp(x, 80, sr) * (10 + 500 * drive ** 2) / FUZZ_V
    y = np.tanh(u + FUZZ_BIAS) - np.tanh(FUZZ_BIAS)
    y = np.tanh(3 * _lp(y, 3000, sr))
    y = (1 - tone) * _lp(y, 400, sr) + tone * _hp(y, 1200, sr)
    return FUZZ_V * _hp(y, 30, sr) * _level(level, FUZZ_MAKEUP_DB)  # the coupling cap takes out the offset


def boost(x: np.ndarray, sr: int, level: float) -> np.ndarray:
    """Clean boost: 0 to 20 dB of flat gain, clean until its op-amp runs out of swing."""
    return BOOST_RAIL * np.tanh(x * 10 ** level / BOOST_RAIL)  # level 1: 10x


PEDALS = {"fuzz": fuzz, "od": overdrive, "boost": boost}


def pedalboard(x: np.ndarray, sr: int, on: tuple[str, ...], knobs: dict[str, dict[str, float]]) -> np.ndarray:
    if not on:
        return x
    up = resample_poly(x, OS, 1)
    for name in rig.PEDALS:
        if name in on:
            up = PEDALS[name](up, sr * OS, **knobs[name])
    return resample_poly(up, 1, OS)[: len(x)]


def amp(x: np.ndarray, sr: int, tone: str) -> np.ndarray:
    return cabinet(_head(x, sr, tone), sr)


def _head(x: np.ndarray, sr: int, tone: str) -> np.ndarray:
    """The amp without its cabinet: preamp, tone stack, power stage."""
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
        b, a = biquad(kind, f0, g, sr)
        y = lfilter(b, a, y)
    drive = cfg["power"]
    y = np.tanh(drive * y) / np.tanh(drive)
    sag = cfg.get("sag", 0.0)
    if sag:
        a = np.exp(-1 / (SAG_S * sr))
        env = np.sqrt(lfilter([1 - a], [1, -a], y * y))
        y = y / (1 + sag * env)
    return y


def guitar_rig(x: np.ndarray, sr: int, tone: str, pedals: tuple[str, ...], model: dict,
               controls=()) -> np.ndarray:
    """Pedals, amp and cabinet, following the part's `tone` and `pedals` controls (the first setting holds
    from the start; `tone` and `pedals` are the instrument's defaults)."""
    knobs, _ = rig.knobs(model)
    spans = _settings(controls, tone, pedals, len(x), sr)
    if len(spans) == 1:
        (_, (tone, on)), = spans
        return cabinet(_head(pedalboard(x, sr, on, knobs), sr, tone), sr)
    # Each setting's weight is a smoothed step up at its start minus one at its end, so the weights add to 1.
    n, h, pre = len(x), max(1, int(FADE_S * sr / 2)), int(PRE_S * sr)
    y = np.zeros(n)
    for k, (s, (tone, on)) in enumerate(spans):
        e = spans[k + 1][0] if k + 1 < len(spans) else n
        a, b = max(0, s - h - pre), min(n, e + h + pre // 10)
        t = np.arange(a, b)
        w = (_step(t - s, h) if k else 1.0) - (_step(t - e, h) if e < n else 0.0)
        y[a:b] += w * _head(pedalboard(x[a:b], sr, on, knobs), sr, tone)
    return cabinet(y, sr)


def _step(t: np.ndarray, h: int) -> np.ndarray:
    """0 before t = -h, 1 from t = h, a raised-cosine rise in between."""
    return 0.5 - 0.5 * np.cos(np.pi * np.clip((t + h) / (2 * h), 0, 1))


def _settings(controls, tone: str, pedals: tuple[str, ...], n: int, sr: int) -> list[tuple[int, tuple]]:
    """(start sample, (tone, pedals on)) for each stretch with one setting."""
    spans: list[tuple[int, tuple]] = []
    for k, c in enumerate(sorted((c for c in controls if c.name in ("tone", "pedals")), key=lambda c: c.time)):
        if c.name == "tone":
            tone = c.value
        else:
            pedals = rig.split(c.value)
        at = min(n, int(c.time * sr)) if spans else 0
        if spans and spans[-1][0] == at:
            spans.pop()
        if not spans or spans[-1][1] != (tone, pedals):
            spans.append((at, (tone, pedals)))
    return spans or [(0, (tone, pedals))]


def bass_amp(x: np.ndarray, sr: int) -> np.ndarray:
    """Bass amp: soft tube saturation, tone stack (full lows, less box, some growl), speaker rolloff."""
    x = sosfilt(butter(2, 30, "hp", fs=sr, output="sos"), x)
    up = resample_poly(x, OS, 1)
    up = np.tanh(BASS_DRIVE * up + BIAS) - np.tanh(BIAS)
    y = resample_poly(up, 1, OS)[: len(x)] / BASS_DRIVE
    for kind, f0, g in (("low", 90, 3.0), ("peak", 400, -2.0), ("peak", 1200, 2.0)):
        b, a = biquad(kind, f0, g, sr)
        y = lfilter(b, a, y)
    return sosfilt(butter(2, 4500, "lp", fs=sr, output="sos"), y)
