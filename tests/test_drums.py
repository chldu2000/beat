import dataclasses
from fractions import Fraction

import numpy as np
from scipy.signal import butter, oaconvolve, sosfiltfilt

from beat.compile import Event
from beat.synth import drums, membrane, room

SR = 44100
FLOOR = membrane.TOMS["t3"]


def ev(lane: str, t: float, v: float = 0.63, **arts) -> Event:
    return Event("dr", Fraction(0), Fraction(1), 0, lane, v, arts, {}, time=t)


def hit(drum: membrane.Drum, v: float, sec: float = 1.0, times=(0.0,)) -> tuple[np.ndarray, np.ndarray]:
    """(mic signal, stick force) of hits at the usual strike point."""
    sh = drum.sh
    return drum._run(list(times), [v] * len(times), [(sh.strike, 0.0)] * len(times), int(sec * SR))[:2]


def freq(y: np.ndarray, pitch: float, t0: float, t1: float) -> float:
    """Frequency near `pitch` from rising zero crossings between t0 and t1."""
    band = sosfiltfilt(butter(4, [pitch * 0.7, pitch * 1.4], "bp", fs=SR, output="sos"), y)
    seg = band[int(t0 * SR):int(t1 * SR)]
    z = np.nonzero(np.diff(np.sign(seg)) > 0)[0]
    return (len(z) - 1) / ((z[-1] - z[0]) / SR)


def centroid(y: np.ndarray) -> float:
    spec = np.abs(np.fft.rfft(y))
    return float((spec * np.fft.rfftfreq(len(y), 1 / SR)).sum() / spec.sum())


def rms(y: np.ndarray, t0: float, t1: float) -> float:
    return float(np.sqrt(np.mean(y[int(t0 * SR):int(t1 * SR)] ** 2)))


def test_lowest_mode_is_tuned_to_the_pitch():
    for sh in membrane.DRUMS.values():
        assert abs(membrane._lowest_mode(sh, membrane.tune(sh)) / sh.pitch - 1) < 0.01


def test_hard_hits_decay_and_stay_finite():
    for sh in (FLOOR, membrane.KICK):
        drum = membrane.Drum(sh, SR, np.random.default_rng(0))
        y, _ = hit(drum, 1.0, 3.0)
        assert np.isfinite(y).all()
        assert rms(y, 2.0, 2.5) < 1e-3 * rms(y, 0.0, 0.1)


def test_port_resonates_with_the_cavity_at_its_frequency():
    md = membrane.build(membrane.KICK, np.random.default_rng(0))
    port = md.head == 2
    assert port.sum() == 1
    w = np.sqrt(md.k_air * md.air[port][0] ** 2 / md.mass[port][0])
    assert abs(w / (2 * np.pi) / membrane.KICK.port - 1) < 1e-9


def test_kick_pitch_drops_on_hard_hits():
    drum = membrane.Drum(membrane.KICK, SR, np.random.default_rng(0))
    hard, _ = hit(drum, 1.0)
    assert freq(hard, membrane.KICK.pitch, 0.0, 0.06) > 1.05 * freq(hard, membrane.KICK.pitch, 0.15, 0.35)


def test_hard_hits_start_sharp_and_glide_down():
    drum = membrane.Drum(FLOOR, SR, np.random.default_rng(0))
    soft, _ = hit(drum, 0.2)
    hard, _ = hit(drum, 1.0)
    assert freq(hard, FLOOR.pitch, 0.0, 0.05) > 1.03 * freq(hard, FLOOR.pitch, 0.4, 0.6)
    assert freq(hard, FLOOR.pitch, 0.0, 0.05) > 1.04 * freq(soft, FLOOR.pitch, 0.0, 0.05)


def test_harder_hits_are_shorter_and_brighter():
    drum = membrane.Drum(membrane.TOMS["t1"], SR, np.random.default_rng(0))
    (soft, f_soft), (hard, f_hard) = hit(drum, 0.2, 0.3), hit(drum, 1.0, 0.3)
    assert np.count_nonzero(f_hard) < np.count_nonzero(f_soft)
    assert centroid(hard) > 1.1 * centroid(soft)


def test_a_new_hit_lands_on_the_ringing_head():
    drum = membrane.Drum(FLOOR, SR, np.random.default_rng(0))
    one, _ = hit(drum, 0.3)
    two, _ = hit(drum, 0.3, times=(0.0, 0.103))
    k = int(0.103 * SR)
    independent = one.copy()
    independent[k:] += one[:-k]
    # the stick meets a moving head, so the second stroke is not just added on top
    assert rms(two - independent, 0.1, 0.4) > 0.05 * rms(independent, 0.1, 0.4)


def test_modal_engine_keeps_the_other_lanes_and_adds_the_room():
    events = [ev("ss", 0.0), ev("hh", 0.25), ev("cr", 0.5)]
    n = SR
    kit = drums.render_part(None, events, n, SR, np.random.default_rng(3))
    modal = drums.render_modal(None, events, n, SR, np.random.default_rng(3))
    assert np.corrcoef(kit[:, 0], modal[:, 0])[0, 1] > 0.6  # the close mics are the same
    assert rms(modal[:, 0], 0.8, 1.0) > 1.5 * rms(kit[:, 0], 0.8, 1.0)  # the room rings on
    with_drums = drums.render_modal(None, events + [ev("t2", 0.1, flam=True), ev("bd", 0.2), ev("sd", 0.3)], n,
                                    SR, np.random.default_rng(3))
    assert np.isfinite(with_drums).all() and rms(with_drums - modal, 0.1, 0.5) > 0.01


def test_toms_set_off_the_snare_wires():
    tom = membrane.Drum(membrane.TOMS["t1"], SR, np.random.default_rng(0))
    _, _, radiated = tom.render([0.1], [0.8], SR, np.random.default_rng(1))
    snare = membrane.Drum(membrane.SNARE, SR, np.random.default_rng(0))
    _, _, quiet, _ = snare._run([], [], [], SR)
    y, _, wire, _ = snare._run([], [], [], SR, drums._arrive(radiated, "sd", "t1", SR))
    assert not quiet.any()
    assert np.isfinite(y).all() and np.abs(wire).max() > 0.1  # newtons: the wires lift and land


def test_room_decays_at_its_rt60():
    x = np.zeros(2 * SR)
    x[0] = 1.0
    wet = room.reverb(x, SR, rt60=0.6).mean(axis=1)
    drop = 20 * np.log10(rms(wet, 0.5, 0.6) / rms(wet, 0.1, 0.2))
    assert -48 < drop < -32  # 40 dB in 0.4 s at 0.6 s RT60, give or take the high end


def test_snare_wires_buzz_more_than_in_proportion():
    drum = membrane.Drum(membrane.SNARE, SR, np.random.default_rng(0))
    point = [(membrane.SNARE.strike, 0.0)]
    buzz = {}
    for v in (0.2, 1.0):
        modal, _, wire, _ = drum._run([0.0], [v], point, int(0.3 * SR))
        buzz[v] = rms(oaconvolve(wire, drum.buzz_ir)[:len(wire)] * drum.buzz, 0.0, 0.1) / rms(modal, 0.0, 0.1)
    assert buzz[1.0] > 1.15 * buzz[0.2] > 0


def test_snare_wires_rest_quietly_and_damp_the_head():
    wired = membrane.Drum(membrane.SNARE, SR, np.random.default_rng(0))
    silent, _, wire, _ = wired._run([0.5], [0.6], [(0.2, 0.0)], int(0.5 * SR))
    assert np.abs(wire).max() < 1e-9 and np.abs(silent).max() < 1e-12  # nothing moves before the hit
    bare = membrane.Drum(dataclasses.replace(membrane.SNARE, wires=None), SR, np.random.default_rng(0))
    y_wired, _ = hit(wired, 0.6)
    y_bare, _ = hit(bare, 0.6)
    assert np.isfinite(y_wired).all()
    assert rms(y_wired, 0.3, 0.6) < 0.7 * rms(y_bare, 0.3, 0.6)
