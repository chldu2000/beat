from beat.arrangement import lead_part
from beat.compile import compile_song
from beat.diagnostics import Diagnostics
from beat.song import load_song

HEADER = """
beat: 0.1
meta: { tempo: 120, time: 4/4 }
instruments:
  dr: { type: drums }
  bs: { type: bass }
  gt: { type: guitar }
  ld: { type: guitar, tone: lead }
"""


def warnings(body: str) -> str:
    diags = Diagnostics()
    song = load_song(HEADER + body + "\nform: [a]\n", diags)
    compile_song(song, diags)
    assert not diags.errors, diags.errors
    return "\n".join(str(d) for d in diags.warnings)


def test_muddy_low_third_is_reported_once_per_section():
    w = warnings("""
sections:
  a:
    bars: 2
    parts:
      gt: { notes: "[F#2 A2]:2 [F#2 A2]:2 | [E2 B2 E3]:1" }
""")
    assert w.count("muddy") == 1
    assert "a > gt > bar 1, beat 1: F#2 and A2 sound muddy" in w
    assert "1 more time" in w


def test_power_chord_and_high_third_are_clear():
    w = warnings("""
sections:
  a:
    bars: 1
    parts:
      gt: { notes: "[E2 B2 E3]:2 [C4 E4]:2" }
""")
    assert "muddy" not in w


def test_held_minor_ninth_over_the_bass():
    w = warnings("""
sections:
  a:
    bars: 1
    parts:
      bs: { notes: "E1:1" }
      ld: { notes: "F4:2 E4:8 F4:8 r:4" }
""")
    assert "a > ld > bar 1, beat 1: F4 sounds a minor 9th over the bass E1 for 1.0 s" in w
    assert "beat 3.5" not in w  # an eighth-note passing tone is fine


def test_lead_under_the_rhythm_guitar():
    body = """
sections:
  a:
    bars: 2
    parts:
      gt: { notes: "[E3 B3 E4]:1 | [E3 B3 E4]:1" }
      ld: { notes: "(%s:8)*8 | (%s:8)*8" }
"""
    assert "a > ld: the lead mostly sits under the rhythm guitars" in warnings(body % ("G3", "A3"))
    assert "under the rhythm" not in warnings(body % ("G4", "A4"))


def test_static_part():
    body = r"""
patterns:
  groove: { type: drums, bars: 1, hits: "bd: 1 3\nsd: 2 4" }
  fill: { type: drums, bars: 1, hits: "sd: 1 2 3 4" }
sections:
  a:
    bars: 16
    parts:
      dr: { use: groove%s }
"""
    assert "dr: plays the very same bar in all 16 bars" in warnings(body % "")
    assert "very same bar" not in warnings(body % ", replace: { 16: { use: fill } }")


def test_lead_part_falls_back_to_the_highest_single_note_part():
    diags = Diagnostics()
    song = load_song("""
beat: 0.1
meta: { tempo: 120, time: 4/4 }
instruments:
  gt1: { type: guitar }
  gt2: { type: guitar }
sections:
  a:
    bars: 1
    parts:
      gt1: { notes: "[E3 B3 E4]:1" }
      gt2: { notes: "E5:2 D5:2" }
form: [a]
""", diags)
    assert lead_part(compile_song(song, diags)) == "gt2"
