import numpy as np
import pytest

from beat.diagnostics import Diagnostics
from beat.mix import parse
from beat.song import load_song
from beat.synth.dynamics import compress, limit, loudness, true_peak

SR = 48000
PARTS = {"dr": "drums", "bs": "bass", "gt1": "guitar"}


def problems(raw) -> str:
    return "\n".join(f"[{level}] {where}: {msg}" for level, where, msg in parse(raw, PARTS)[1])


def test_loudness_of_a_sine_matches_bs1770():
    t = np.arange(5 * SR) / SR
    s = np.sin(2 * np.pi * 997 * t)
    assert loudness(np.stack([s, 0 * s], axis=1), SR) == pytest.approx(-3.01, abs=0.02)
    assert loudness(np.stack([s, s], axis=1) * 0.1, SR) == pytest.approx(-20.0, abs=0.02)


def test_compressor_reaches_the_static_curve():
    t = np.arange(SR) / SR
    s = np.sin(2 * np.pi * 440 * t)  # RMS -3 dBFS
    _, gr = compress(s, SR, threshold_db=-20, ratio=4, attack_ms=5, release_ms=50)
    assert gr[-1000:].mean() == pytest.approx(17 * 0.75, abs=0.1)
    _, gr = compress(s * 0.01, SR, threshold_db=-20, ratio=4, attack_ms=5, release_ms=50)
    assert gr.max() < 0.01  # far under the knee


def test_limiter_keeps_the_true_peak_under_the_ceiling():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 0.3, (2 * SR, 2))
    x[SR, 0] += 4
    x[SR + 500: SR + 600] *= 5
    y, gr = limit(x, SR, ceiling_db=-1)
    assert 20 * np.log10(true_peak(y).max()) <= -1.0
    quiet = 0.1 * x
    assert np.allclose(limit(quiet, SR)[0], quiet)  # under the ceiling: untouched


def test_defaults_per_instrument_type():
    mix, found = parse(None, PARTS)
    assert found == []
    assert mix.space == "studio" and mix.style == "rock" and mix.loudness == -14
    assert mix.parts["bs"].comp == "heavy" and mix.parts["bs"].reverb == "off"
    assert mix.parts["gt1"].hpf == 90 and mix.parts["dr"].peak > 0


def test_settings_are_applied():
    mix, found = parse({"space": "hall", "gt1": {"gain_db": -2, "pan": -0.6, "eq": {"mid": -2}, "hpf": "off",
                                                 "comp": "off", "reverb": "more"},
                        "master": {"style": "gentle", "loudness": -12, "gain_db": -1}}, PARTS)
    assert found == []
    gt = mix.parts["gt1"]
    assert (gt.gain_db, gt.pan, gt.hpf, gt.comp, gt.reverb) == (-2, -0.6, 0, "off", "more")
    assert ("peak", 800, -2.0, 0.7) in gt.eq
    assert mix.space == "hall" and mix.style == "gentle" and mix.loudness == -13


def test_mix_errors_name_the_key_and_the_fix():
    text = problems({"gt2": {"pan": 0.5}, "spcae": "hall", "space": "cave",
                     "gt1": {"pan": 1.5, "eq": {"mid": 20, "treble": 2}, "comp": "hard", "reverb": "lots"},
                     "master": {"loudness": -3}})
    assert "[error] mix > gt2: unknown part 'gt2' (did you mean 'gt1'?)" in text
    assert "[error] mix > spcae: unknown part 'spcae' (did you mean 'space'?)" in text
    assert "[error] mix > space: space must be one of dry, room, studio, hall, got 'cave'" in text
    assert "[error] mix > gt1 > pan: must be a number (-1 left, 1 right) from -1 to 1, got 1.5" in text
    assert "[error] mix > gt1 > eq > mid: must be a number (dB) from -12 to 12, got 20" in text
    assert "[warning] mix > gt1 > eq: unknown key 'treble'" in text
    assert "[error] mix > gt1 > comp: must be one of off, light, medium, heavy, got 'hard'" in text
    assert "[error] mix > gt1 > reverb: must be one of off, less, normal, more, got 'lots'" in text
    assert "[error] mix > master > loudness: must be a number (LUFS) from -30 to -6, got -3" in text


def test_song_reports_mix_problems():
    diags = Diagnostics()
    load_song("""
beat: 0.1
meta: { tempo: 120, time: 4/4 }
instruments:
  gt: { type: guitar }
sections:
  a: { bars: 1, parts: { gt: { notes: "E2:1" } } }
form: [a]
mix:
  gt: { pan: left }
""", diags)
    assert [str(d) for d in diags.errors] == \
        ["[error] mix > gt > pan: must be a number (-1 left, 1 right) from -1 to 1, got 'left'"]


def test_mixdown_hits_the_loudness_target_and_reports():
    from beat.compile import compile_song
    from beat.render import mixdown

    diags = Diagnostics()
    song = load_song("""
beat: 0.1
meta: { tempo: 120, time: 4/4 }
instruments:
  dr: { type: drums, model: { engine: kit } }
  bs: { type: bass, model: { engine: ks } }
  gt: { type: guitar, model: { engine: ks } }
sections:
  a:
    bars: 1
    parts:
      dr: { hits: "bd: 1 3\\nsd: 2 4\\nhh: 1 1.5 2 2.5 3 3.5 4 4.5\\ncr: 1" }
      bs: { notes: "(E1:8)*8" }
      gt: { notes: "[E2 B2 E3]:2 [G2 D3 G3]:2" }
form: [a, a, a]
mix:
  gt: { pan: -0.5, reverb: more }
  master: { loudness: -16 }
""", diags)
    assert [str(d) for d in diags.errors] == []
    audio, report = mixdown(compile_song(song, diags), sr=22050)
    assert report.loudness == pytest.approx(-16, abs=0.3)
    assert report.true_peak_db <= -0.99
    assert set(report.parts) == {"dr", "bs", "gt"}
    assert report.lines()[0].startswith("mix: -16.")
    left, right = np.sum(audio ** 2, axis=0)
    assert left > right  # the guitar is panned left
