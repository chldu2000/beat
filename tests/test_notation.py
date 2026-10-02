from fractions import Fraction

from beat.notation import DYNAMICS, parse_grid, parse_notes
from beat.pitch import parse_chord, parse_pitch, pitch_name

BAR = Fraction(4)


def test_pitch_names():
    assert parse_pitch("C4") == 60
    assert parse_pitch("E1") == 28
    assert parse_pitch("Bb3") == 58
    assert parse_pitch("F#2") == 42
    assert pitch_name(42) == "F#2"


def test_chords():
    assert parse_chord("Em") == {4, 7, 11}
    assert parse_chord("B7") == {11, 3, 6, 9}
    assert parse_chord("C/E") == {0, 4, 7}
    assert parse_chord("E5") == {4, 11}
    assert parse_chord("N.C.") is None


def test_sticky_duration_and_groups():
    bars, problems = parse_notes("(E2:8!pm)*4 G2 E2 A2 B2", BAR, 0.6)
    assert problems == []
    items = bars[0]
    assert len(items) == 8
    assert all(it.dur == Fraction(1, 2) for it in items)
    assert items[0].arts == {"pm": True} and items[4].arts == {}
    assert items[7].onset == Fraction(7, 2)


def test_durations_dots_triplets():
    bars, problems = parse_notes("C4:4. C4:8 C4:8t C4 C4 C4:4", BAR, 0.6)
    assert problems == []
    assert [it.dur for it in bars[0]] == [Fraction(3, 2), Fraction(1, 2)] + [Fraction(1, 3)] * 3 + [Fraction(1)]


def test_chord_tie_dynamics_and_bar_repeat():
    bars, problems = parse_notes("@f [E2 B2 E3]:2~ [E2 B2 E3]:2 | % | @p r:1", BAR, 0.6)
    assert problems == []
    assert bars[0][0].pitches == (40, 47, 52) and bars[0][0].tie
    assert bars[0][0].level == DYNAMICS["f"]
    assert len(bars[1]) == 2
    assert bars[2][0].pitches == ()


def test_bar_duration_error():
    _, problems = parse_notes("E2:4 E2 E2 | E2:1", BAR, 0.6)
    assert problems == [(0, "duration 3 beats, expected 4")]


def test_bad_tokens():
    _, problems = parse_notes("H2:4 E2:3 E2!foo E2:4", BAR, 0.6)
    messages = " ".join(m for _, m in problems)
    assert "cannot parse token 'H2:4'" in messages
    assert "invalid duration" in messages
    assert "unknown articulation '!foo'" in messages


def test_bend_value():
    bars, problems = parse_notes("A3:1!bend=2", BAR, 0.6)
    assert problems == [] and bars[0][0].arts == {"bend": 2.0}


def test_grid():
    bars, problems = parse_grid("sd: ----X---|----g---\nbd: x-------|f-------", BAR, 8, 0.6, 2)
    assert problems == []
    assert [(it.lane, it.onset, it.arts) for it in bars[0]] == [("bd", 0, {}), ("sd", 2, {"acc": True})]
    assert [(it.lane, it.arts) for it in bars[1]] == [("bd", {"flam": True}), ("sd", {"ghost": True})]


def test_grid_length_and_lane_errors():
    _, problems = parse_grid("sd: ----\nzz: x---------------", BAR, 16, 0.6, 1)
    messages = " ".join(m for _, m in problems)
    assert "lane 'sd' has 4 steps, expected 16" in messages
    assert "unknown drum lane 'zz'" in messages
