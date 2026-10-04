from fractions import Fraction

import numpy as np
import pytest

from beat.compile import Event
from beat.song import Instrument
from beat.synth import amp
from beat.synth.bass import BASS
from beat.synth.fretboard import assign
from beat.synth.plucked import strings_signal

SR = 44100
STANDARD = (28, 33, 38, 43)
INST = Instrument(id="bs", type="bass", tuning=STANDARD, frets=21)


def ev(pitch: int, t: float = 0.0, d: float = 3.0, v: float = 0.8, beat: float | None = None, **arts) -> Event:
    b = Fraction(beat if beat is not None else t).limit_denominator(64)
    return Event("bs", b, Fraction(1), pitch, None, v, dict(arts), {}, time=t, dur=d)


def strings(events: list[Event], sec: float, seed: int = 0) -> np.ndarray:
    return strings_signal(BASS, INST, events, int(sec * SR), SR, np.random.default_rng(seed))


def cents_off(y: np.ndarray, target: float, t0: float, win: float) -> float:
    n = int(win * SR)
    seg = y[int(t0 * SR):int(t0 * SR) + n] * np.hanning(n)
    spec = np.abs(np.fft.rfft(seg, 16 * n))
    f = np.fft.rfftfreq(16 * n, 1 / SR)
    i = int(np.argmax(np.where((f > target * 0.95) & (f < target * 1.05), spec, 0)))
    a, b, c = np.log(spec[i - 1:i + 2])
    return 1200 * np.log2((f[i] + 0.5 * (a - c) / (a - 2 * b + c) * (f[1] - f[0])) / target)


@pytest.mark.parametrize("pitch", [28, 33, 40, 50, 60])
def test_pitch_settles_within_a_few_cents(pitch):
    target = 440 * 2 ** ((pitch - 69) / 12)
    assert abs(cents_off(strings([ev(pitch)], 3.0), target, 1.0, 1.0)) < 4


def test_hard_notes_start_sharp_and_settle():
    target = 440 * 2 ** ((40 - 69) / 12)
    y = strings([ev(40, v=1.0)], 3.0)
    early, late = cents_off(y, target, 0.0, 0.1), cents_off(y, target, 1.0, 1.0)
    assert early > late + 1.5


def test_bass_sustains_longer_than_a_palm_mute_and_damps_on_release():
    rms = lambda y, t0, t1: np.sqrt(np.mean(y[int(t0 * SR):int(t1 * SR)] ** 2))
    open_ = strings([ev(28, d=1.0)], 1.5)
    muted = strings([ev(28, d=1.0, pm=True)], 1.5)
    assert rms(open_, 0.8, 0.95) > 0.5 * rms(open_, 0.05, 0.2)
    assert rms(muted, 0.8, 0.95) < 0.05 * rms(muted, 0.05, 0.2)
    assert rms(open_, 1.15, 1.25) < 0.05 * rms(open_, 0.8, 0.95)


def test_line_uses_four_strings_and_renders_finite():
    line = [ev(p, t=i * 0.25, d=0.25, beat=i * 0.5) for i, p in enumerate((28, 35, 40, 38, 33, 40, 45, 43))]
    assert {s for s, _ in assign(line, STANDARD, 21)} <= {0, 1, 2, 3}
    out = amp.bass_amp(strings(line, 2.5), SR)
    assert np.isfinite(out).all() and np.abs(out).max() > 0
