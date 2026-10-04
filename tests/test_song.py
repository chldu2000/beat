from pathlib import Path

import numpy as np
import pytest

from beat.checks import fingering
from beat.compile import compile_song
from beat.diagnostics import Diagnostics
from beat.pitch import parse_pitch
from beat.song import load_song

DEMO = Path(__file__).parent.parent / "examples" / "demo.beat.yaml"

HEADER = """
beat: 0.1
meta: { tempo: 120, time: 4/4 }
instruments:
  dr: { type: drums }
  bs: { type: bass }
  gt: { type: guitar }
  org: { type: organ }
"""


def build(body: str, form: str = "[a]"):
    diags = Diagnostics()
    song = load_song(HEADER + body + f"\nform: {form}\n", diags)
    compiled = compile_song(song, diags) if song else None
    return diags, compiled


def messages(diags: Diagnostics, level: str = "error") -> str:
    return "\n".join(str(d) for d in diags.items if d.level == level)


def test_demo_is_clean():
    diags = Diagnostics()
    song = load_song(DEMO.read_text(), diags)
    compiled = compile_song(song, diags)
    assert diags.items == []
    assert compiled.total_bars == 38
    assert compiled.events == sorted(compiled.events, key=lambda e: (e.time, e.part, e.pitch))


def test_compile_is_deterministic():
    def run():
        diags = Diagnostics()
        return [e.to_dict() for e in compile_song(load_song(DEMO.read_text(), diags), diags).events]
    assert run() == run()


def test_timing_and_ties():
    diags, c = build("""
sections:
  a:
    bars: 2
    parts:
      bs: { notes: "E1:2~ E1:4 A1:4 | E1:1" }
""")
    assert diags.items == []
    ev = c.events
    assert [(e.pitch, float(e.beat), float(e.beats)) for e in ev] == [(28, 0, 3), (33, 3, 1), (28, 4, 4)]
    assert ev[1].time == pytest.approx(1.5)  # beat 3 at 120 BPM


def test_broken_tie():
    diags, _ = build("""
sections:
  a:
    bars: 1
    parts:
      bs: { notes: "E1:2~ A1:2" }
""")
    assert "tie from E1 but the next note is A1" in messages(diags)


def test_patterns_replace_and_extends():
    diags, c = build("""
patterns:
  groove: { type: drums, bars: 1, grid: "bd: x---x---x---x---" }
  fill: { type: drums, bars: 1, grid: "sd: xxxxxxxxxxxxxxxx" }
sections:
  a:
    bars: 4
    parts:
      dr: { use: groove, replace: { 4: { use: fill } } }
  b:
    extends: a
    tempo: 100
""", form="[a, b]")
    assert diags.items == []
    lanes = [e.lane for e in c.events]
    assert lanes.count("bd") == 2 * 3 * 4
    assert lanes.count("sd") == 2 * 16
    assert c.instances[1].section.tempo == 100


def test_range_and_bar_count_errors():
    diags, _ = build("""
sections:
  a:
    bars: 2
    parts:
      bs: { notes: "C1:1" }
      org: { notes: "C1:1 | C4:1" }
""")
    errs = messages(diags)
    assert "a > bs: 1 bars written, expected 2" in errs
    assert "C1 is outside the bass range E1-E4" in errs
    assert "C1 is outside the organ range C2-C7" in errs


def test_unplayable_guitar_chord():
    diags, _ = build("""
sections:
  a:
    bars: 1
    parts:
      gt: { notes: "[E2 F2]:2 [A2 E3 A3 C#4 E4]:2" }
""")
    errs = messages(diags)
    assert "[E2 F2] is not playable" in errs
    assert "C#4" not in errs


def test_fingering():
    tuning = tuple(parse_pitch(n) for n in ["E2", "A2", "D3", "G3", "B3", "E4"])
    em = tuple(parse_pitch(n) for n in ["E2", "B2", "E3", "G3", "B3", "E4"])
    assert fingering(em, tuning, 22) == [(0, 0), (1, 2), (2, 2), (3, 0), (4, 0), (5, 0)]
    stretch = (parse_pitch("F2"), parse_pitch("G#5"))  # fret 1 on low E + fret 16+ elsewhere
    assert fingering(stretch, tuning, 22) is None


def test_drummer_hands():
    diags, _ = build("""
sections:
  a:
    bars: 1
    parts:
      dr:
        grid: |
          hh: x---------------
          sd: x---f-----------
          cr: x---x-----------
""")
    errs = messages(diags)
    assert "a > dr > bar 1, beat 1: drummer needs 3 hands" in errs
    assert "beat 2: drummer needs 3 hands for sd (flam), cr" in errs


def test_warnings():
    diags, _ = build("""
sections:
  a:
    bars: 1
    chords: "C"
    parts:
      bs: { notes: "D2:1", colour: red }
      org: { notes: "C4:1!pm" }
""")
    warns = messages(diags, "warning")
    assert "bass plays D2 under C" in warns
    assert "unknown key 'colour'" in warns
    assert "!pm does not apply to organ" in warns


def test_performance_edits_and_swing():
    diags, c = build("""
sections:
  a:
    bars: 1
    parts:
      bs: { notes: "(E1:8)*8" }
performance:
  swing: { amount: 0.75, grid: 8 }
  edits:
    - { part: bs, section: a, bar: 1, beat: 2, velocity: 0.95 }
    - { part: bs, section: a, bar: 1, beat: 2.25, velocity: 0.1 }
""")
    assert "edits[1]: edit matches no note" in messages(diags)
    times = [e.time for e in c.events]
    assert times[1] == pytest.approx(0.375)  # off-beat eighth pushed to 3/4 of the beat
    assert c.events[2].velocity == pytest.approx(0.95)


def test_render_smoke():
    from beat.render import render

    diags, c = build("""
sections:
  a:
    bars: 1
    parts:
      dr: { grid: "bd: x---x---x---x---\\nho: --x---x---x---x-" }
      bs: { notes: "E1:4 E1!pm E1!x E1!st" }
      gt: { notes: "[E2 B2 E3]:2 [A2 E3 A3]:2" }
      org: { notes: "[E3 B3]:1" }
""")
    assert not diags.has_errors
    audio = render(c, sr=22050)
    assert audio.shape[1] == 2
    assert np.isfinite(audio).all()
    assert np.abs(audio).max() == pytest.approx(10 ** (-1 / 20), rel=1e-3)


def test_did_you_mean_suggestions():
    diags, _ = build("""
patterns:
  groove: { type: drums, bars: 1, grid: "bd: x---x---x---x---" }
sections:
  a:
    bars: 1
    parts:
      dr: { use: grove }
      bs: { notes: "E1:1!palm", dynamc: f }
      gt: { notes: "@mff E2:1" }
""")
    text = messages(diags) + messages(diags, "warning")
    assert "unknown pattern 'grove' (did you mean 'groove'?)" in text
    assert "unknown articulation '!palm' in 'E1:1!palm' (did you mean 'pm'?)" in text
    assert "unknown key 'dynamc' (did you mean 'dynamic'?)" in text
    assert "unknown dynamic '@mff' (did you mean '@mf'?)" in text


def test_yaml_error_names_the_line_to_quote():
    diags = Diagnostics()
    assert load_song(HEADER + 'sections:\n  a:\n    bars: 1\n    parts:\n      gt:\n'
                              '        notes: [E2 B2]:1 E2\nform: [a]\n', diags) is None
    (err,) = diags.errors
    assert "Line 14: the notes value starts with '['" in err.message
    assert 'wrap it in quotes: notes: "[E2 B2]:1 E2' in err.message
