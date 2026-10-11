from fractions import Fraction

import numpy as np
import pytest

from beat.compile import Event
from beat.song import Instrument
from beat.synth import amp
from beat.synth.guitar import GUITAR
from beat.synth.plucked import strings_signal
from beat.synth.fretboard import assign

SR = 44100
STANDARD = (40, 45, 50, 55, 59, 64)
INST = Instrument(id="gt", type="guitar", tuning=STANDARD, frets=22, tone="clean")


def ev(pitch: int, t: float = 0.0, d: float = 2.0, v: float = 0.8, beat: float | None = None, **arts) -> Event:
    b = Fraction(beat if beat is not None else t).limit_denominator(64)
    return Event("gt", b, Fraction(1), pitch, None, v, dict(arts), {}, time=t, dur=d)


def strings(events: list[Event], sec: float, seed: int = 0) -> np.ndarray:
    return strings_signal(GUITAR, INST, events, int(sec * SR), SR, np.random.default_rng(seed))


def f0_of(y: np.ndarray, guess: float) -> float:
    seg = y[int(0.1 * SR):int(1.1 * SR)] * np.hanning(SR)
    spec = np.abs(np.fft.rfft(seg, 8 * SR))
    f = np.fft.rfftfreq(8 * SR, 1 / SR)
    i = int(np.argmax(np.where((f > guess * 0.9) & (f < guess * 1.1), spec, 0)))
    a, b, c = np.log(spec[i - 1:i + 2])
    return f[i] + 0.5 * (a - c) / (a - 2 * b + c) * (f[1] - f[0])


def band_rms(y: np.ndarray, f0: float, t0: float, t1: float) -> float:
    seg = y[int(t0 * SR):int(t1 * SR)]
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    return float(np.sqrt(np.sum(spec[(f > f0 * 0.97) & (f < f0 * 1.03)] ** 2)))


@pytest.mark.parametrize("pitch", [40, 47, 55, 64, 71, 81, 86])
def test_pitch_within_a_few_cents(pitch):
    target = 440 * 2 ** ((pitch - 69) / 12)
    cents = 1200 * np.log2(f0_of(strings([ev(pitch)], 2.0), target) / target)
    assert abs(cents) < 4  # includes the deliberate ~1 cent random detune


def test_same_string_note_replaces_the_ringing_one():
    a2 = 110.0
    alone = strings([ev(45, d=0.5)], 1.5)
    # A2 then A#2 on the same (A) string: the A2 pitch must not keep ringing.
    both = strings([ev(45, d=0.5), ev(46, t=0.5, d=1.0, beat=1)], 1.5)
    assert assign([ev(45, d=0.5), ev(46, t=0.5, d=1.0, beat=1)], STANDARD, 22)[1][0] == 1
    assert band_rms(both, a2, 0.7, 1.2) < 0.1 * band_rms(alone, a2, 0.1, 0.45)


def test_notes_on_other_strings_keep_ringing():
    a2 = 110.0
    y = strings([ev(45, d=2.0), ev(52, t=0.5, d=1.5, beat=1)], 2.0)
    assert band_rms(y, a2, 0.8, 1.2) > 0.4 * band_rms(y, a2, 0.1, 0.45)


def test_release_damps_quickly():
    y = strings([ev(45, d=0.5)], 1.0)
    rms = lambda t0, t1: np.sqrt(np.mean(y[int(t0 * SR):int(t1 * SR)] ** 2))
    assert rms(0.62, 0.7) < 0.03 * rms(0.3, 0.45)


def test_palm_mute_is_shorter_than_open_note():
    def tail(y):
        return np.sqrt(np.mean(y[int(0.3 * SR):int(0.4 * SR)] ** 2)) / np.sqrt(np.mean(y[:int(0.05 * SR)] ** 2))
    assert tail(strings([ev(40, d=1.0, pm=True)], 0.5)) < 0.2 * tail(strings([ev(40, d=1.0)], 0.5))


def test_hammer_on_stays_on_the_string_without_a_new_stroke():
    notes = [ev(57, d=0.25), ev(59, t=0.25, d=0.75, beat=0.5, h=True)]
    pos = assign(notes, STANDARD, 22)
    assert pos[0][0] == pos[1][0]
    y = strings(notes, 1.0)
    picked = strings([ev(57, d=0.25), ev(59, t=0.25, d=0.75, beat=0.5)], 1.0)
    attack = lambda s: np.abs(s[int(0.25 * SR):int(0.27 * SR)]).max()
    assert attack(y) < attack(picked)
    assert band_rms(y, 246.94, 0.4, 0.9) > 0.2 * band_rms(picked, 246.94, 0.4, 0.9)


def test_chord_takes_the_open_position_shape():
    c_major = [ev(p) for p in (48, 52, 55, 60, 64)]
    assert sorted(assign(c_major, STANDARD, 22)) == [(1, 3), (2, 2), (3, 0), (4, 1), (5, 0)]


def test_hand_stays_in_position():
    # After a 5th-fret A minor barre, the pentatonic line stays there instead of jumping to open position.
    barre = [ev(p, d=1.0) for p in (45, 52, 57, 60, 64, 69)]
    line = [ev(p, t=1 + i * 0.25, d=0.25, beat=2 + i * 0.5) for i, p in enumerate((57, 60, 62, 64, 67, 69, 72))]
    pos = assign(barre + line, STANDARD, 22)
    assert sorted(f for _, f in pos[:6]) == [5, 5, 5, 5, 7, 7]
    frets = [f for _, f in pos[6:]]
    assert min(frets) >= 4 and max(frets) - min(frets) <= 4


def test_same_seed_same_audio_and_no_nans():
    notes = [ev(40, d=0.25, pm=True), ev(52, t=0.25, d=0.5, beat=0.5), ev(45, t=0.75, d=0.2, beat=1, x=True)]
    a, b = strings(notes, 1.5, seed=3), strings(notes, 1.5, seed=3)
    assert np.array_equal(a, b)
    out = amp.amp(a, SR, "lead")
    assert np.isfinite(out).all()


def test_unknown_engine_is_an_error():
    from beat.diagnostics import Diagnostics
    from beat.song import load_song
    from pathlib import Path

    text = Path("examples/demo.beat.yaml").read_text().replace(
        "gt1: { type: guitar, tone: crunch }", "gt1: { type: guitar, tone: crunch, model: { engine: wavguide } }")
    diags = Diagnostics()
    load_song(text, diags)
    assert any("did you mean 'waveguide'" in str(d) for d in diags.items)


def f0_at(y: np.ndarray, t0: float, t1: float, guess: float) -> float:
    seg = y[int(t0 * SR):int(t1 * SR)] * np.hanning(int(t1 * SR) - int(t0 * SR))
    nfft = 16 * len(seg)
    spec = np.abs(np.fft.rfft(seg, nfft))
    f = np.fft.rfftfreq(nfft, 1 / SR)
    return float(f[np.argmax(np.where((f > guess * 0.85) & (f < guess * 1.15), spec, 0))])


def cents(f: float, pitch: int) -> float:
    return 1200 * np.log2(f / (440 * 2 ** ((pitch - 69) / 12)))


def test_bend_reaches_the_target_and_avoids_open_strings():
    note = ev(64, d=2.0, bend=2.0)  # E4 bent a whole tone: on the B string, not the open high E
    assert assign([note], STANDARD, 22)[0] == (4, 5)
    y = strings([note], 2.0)
    assert abs(cents(f0_at(y, 0.02, 0.06, 330), 64)) < 60  # starts at the fretted pitch
    assert abs(cents(f0_at(y, 0.5, 1.5, 370), 66)) < 5


def test_vibrato_only_pushes_the_pitch_up():
    y = strings([ev(69, d=2.0, vib=True)], 2.0)
    track = [cents(f0_at(y, t, t + 0.06, 440), 69) for t in np.arange(0.5, 1.8, 0.02)]
    assert max(track) - min(track) > 20
    assert min(track) > -8


def test_vibrato_on_a_tied_note_starts_there():
    y = strings([ev(69, d=2.0, beat=0, vib=True, at={"vib": 0.5})], 2.0)
    early = [cents(f0_at(y, t, t + 0.06, 440), 69) for t in np.arange(0.1, 0.4, 0.02)]
    late = [cents(f0_at(y, t, t + 0.06, 440), 69) for t in np.arange(1.0, 1.8, 0.02)]
    assert max(early) - min(early) < 8 < max(late) - min(late)


def test_slide_moves_from_the_previous_note_without_a_new_stroke():
    notes = [ev(57, d=0.5), ev(62, t=0.5, d=1.5, beat=1, sl=True)]
    pos = assign(notes, STANDARD, 22)
    assert pos[0][0] == pos[1][0]
    y = strings(notes, 2.0)
    assert abs(cents(f0_at(y, 0.8, 1.8, 294), 62)) < 5
    picked = strings([ev(57, d=0.5), ev(62, t=0.5, d=1.5, beat=1)], 2.0)
    attack = lambda s: np.abs(s[int(0.5 * SR):int(0.52 * SR)]).max()
    assert attack(y) < attack(picked)


def test_natural_harmonic_sounds_its_written_pitch():
    note = ev(83, d=2.0, harm=True)  # B5: the 7th-fret harmonic of the high E, not the flat 4th-fret one of G
    assert assign([note], STANDARD, 22)[0] == (5, 7)
    y = strings([note], 2.0)
    assert abs(cents(f0_at(y, 0.2, 1.2, 988), 83)) < 6
    assert np.isfinite(y).all()
