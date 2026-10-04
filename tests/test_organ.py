from fractions import Fraction

import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt

from beat.compile import Control, Event
from beat.song import Instrument
from beat.synth import leslie, organ
from beat.synth.registration import Registration, parse

SR = 44100


def ev(pitch: int, t: float = 0.0, d: float = 1.0, v: float = 0.63) -> Event:
    return Event("org", Fraction(0), Fraction(1), pitch, None, v, {}, {}, time=t, dur=d)


def wheels(events: list[Event], drawbars: str, sec: float, **kw) -> np.ndarray:
    reg = Registration(drawbars, vibrato="off", **kw)
    return organ.tonewheels(events, reg, int(sec * SR), SR, np.random.default_rng(0))


def rms(y: np.ndarray, t0: float, t1: float) -> float:
    return float(np.sqrt(np.mean(y[int(t0 * SR):int(t1 * SR)] ** 2)))


def test_wheels_are_within_a_cent_of_equal_temperament():
    et = 440 * 2 ** ((np.arange(organ.N_WHEELS) + organ.WHEEL0_PITCH - 69) / 12)
    assert np.abs(1200 * np.log2(organ.wheel_freqs() / et)).max() < 1.0


def test_top_drawbars_fold_back_an_octave():
    top = organ.wheel_for(96 + 36)  # C7 at 1'
    assert top < organ.N_WHEELS and (top + organ.WHEEL0_PITCH) % 12 == 0
    assert organ.wheel_for(96 + 36) == organ.wheel_for(96 + 24)


def test_keys_sharing_a_wheel_add_in_phase():
    c4_8ft = wheels([ev(60)], "008000000", 1.0, click=0.0)
    c3_4ft = wheels([ev(48)], "000800000", 1.0, click=0.0)
    both = wheels([ev(60), ev(48)], "008800000", 1.0, click=0.0)
    single = rms(c4_8ft, 0.2, 0.8)
    assert abs(rms(c3_4ft, 0.2, 0.8) / single - 1) < 0.01
    # C3's 8' (C3) adds a second wheel; its 4' (C4) doubles C4's 8' rather than adding at a random phase
    assert rms(both, 0.2, 0.8) > 1.9 * single


def test_percussion_fires_only_after_all_keys_are_up():
    legato = wheels([ev(60, 0.0, 2.0), ev(64, 1.0, 1.0)], "000000000", 2.5, percussion="3rd")
    detached = wheels([ev(60, 0.0, 0.9), ev(64, 1.0, 1.0)], "000000000", 2.5, percussion="3rd")
    assert rms(detached, 1.0, 1.1) > 0.2
    assert rms(legato, 1.0, 1.1) < 0.01 * rms(detached, 1.0, 1.1)


def test_percussion_decay_fast_and_slow():
    fast = wheels([ev(60, d=2.0)], "000000000", 2.0, percussion="2nd")
    slow = wheels([ev(60, d=2.0)], "000000000", 2.0, percussion="2nd-slow")
    assert rms(fast, 0.3, 0.4) < 0.05 * rms(fast, 0.0, 0.05)
    assert rms(slow, 0.3, 0.4) > 0.2 * rms(slow, 0.0, 0.05)


def test_harder_click_has_more_high_frequency_at_the_onset():
    def onset_hf(click: float) -> float:
        y = wheels([ev(48, 0.1, 0.5)], "888000000", 0.7, click=click)
        hf = sosfiltfilt(butter(4, 4000, "hp", fs=SR, output="sos"), y)
        return rms(hf, 0.1, 0.105)
    assert onset_hf(1.0) > 3 * onset_hf(0.0)


def test_expression_pedal_follows_velocity():
    g = organ.expression([ev(60, 0.0, 1.0, 0.63), ev(60, 1.0, 1.0, 0.38)], 2 * SR, SR)
    assert abs(20 * np.log10(g[int(0.5 * SR)])) < 0.01
    assert g[int(1.5 * SR)] < 0.5 * g[int(0.5 * SR)]


def test_drive_adds_distortion():
    x = wheels([ev(60), ev(64), ev(67)], "888800000", 1.0) * organ.GEN_LEVEL
    lin = organ.preamp(x, 0.0, SR)[4000:]

    def residual_db(drive: float) -> float:
        y = organ.preamp(x, drive, SR)[4000:]
        r = y - np.dot(y, lin) / np.dot(lin, lin) * lin
        return 10 * np.log10(np.sum(r ** 2) / np.sum(y ** 2))
    assert residual_db(0.6) > residual_db(0.1) + 10


def leslie_am_rate(y: np.ndarray, band: tuple[float, float], t0: float, t1: float) -> float:
    b = sosfiltfilt(butter(4, band, "bp", fs=SR, output="sos"), y)
    env = np.abs(hilbert(b))[int(t0 * SR):int(t1 * SR)]
    env = (env - env.mean()) * np.hanning(len(env))
    spec = np.abs(np.fft.rfft(env, 8 * len(env)))
    f = np.fft.rfftfreq(8 * len(env), 1 / SR)
    mask = (f > 0.3) & (f < 12)
    return float(f[mask][np.argmax(spec[mask])])


def test_leslie_speeds_inertia_and_stereo():
    n = 9 * SR
    t = np.arange(n) / SR
    x = 0.3 * np.sin(2 * np.pi * 1760 * t) + 0.3 * np.sin(2 * np.pi * 220 * t)
    controls = [Control("org", 0.0, "leslie", "slow", {}), Control("org", 4.0, "leslie", "fast", {})]
    y = leslie.rotary(x, leslie.speed_track(controls, n, SR), SR)
    horn, drum = (1500, 2000), (150, 300)
    assert abs(leslie_am_rate(y[:, 0], horn, 0.5, 3.5) - 0.8) < 0.1
    assert abs(leslie_am_rate(y[:, 0], horn, 6.0, 9.0) - 6.8) < 0.2
    assert abs(leslie_am_rate(y[:, 0], drum, 0.5, 3.5) - 0.67) < 0.1
    # one second after switching the horn is nearly at speed, the heavy drum is not
    assert leslie_am_rate(y[:, 0], horn, 5.0, 6.0) > 6.0
    assert leslie_am_rate(y[:, 0], drum, 5.0, 6.0) < 4.5
    assert np.corrcoef(y[SR:, 0], y[SR:, 1])[0, 1] < 0.8


def test_render_part_is_stereo_and_finite():
    inst = Instrument(id="org", type="organ", model={"registration": "gospel"})
    assert parse(inst.model)[0].percussion == "2nd"
    events = [ev(p, 0.0, 0.5) for p in (52, 59, 64)] + [ev(p, 0.6, 0.5, 0.9) for p in (55, 62, 67)]
    y = organ.render_part(inst, events, int(1.5 * SR), SR, np.random.default_rng(0),
                          [Control("org", 0.0, "leslie", "fast", {})])
    assert y.shape == (int(1.5 * SR), 2)
    assert np.isfinite(y).all() and np.abs(y).max() > 0
