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
    assert problems == [(0, "duration 3 beats, expected 4: 1 beat(s) missing (e.g. add r:b1)")]


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
    assert "lane 'sd' has 4 steps in this bar, expected 16; by beat it reads '----'" in messages
    assert "unknown drum lane 'zz'" in messages

    _, problems = parse_grid("bd: x---x---x---x--- | x---x---x---x----", BAR, 16, 0.6, 2)
    assert problems == [(1, "lane 'bd' has 17 steps in this bar, expected 16; "
                            "by beat it reads 'x--- x--- x--- x--- -'")]
    _, problems = parse_grid("bd: x---x---x---x---x---x---x---x----", BAR, 16, 0.6, 2)
    assert problems == [(None, "lane 'bd' has 33 steps, expected 32 (2 bar(s) x 16 steps); split into bars "
                               "it reads 'x---x---x---x--- | x---x---x---x--- | -' "
                               "(separate bars with '|' to get per-bar errors)")]
    bars, problems = parse_grid("hh: x-x- x-x- x-x- x-x-", BAR, 16, 0.6, 1)
    assert problems == [] and len(bars[0]) == 8


def test_beat_lengths():
    bars, problems = parse_notes("E2:b2.5 E2:b1/2 C4:b1 | G3:b1/3 G3 G3 G3:b3", BAR, 0.6)
    assert problems == []
    assert [it.dur for it in bars[0]] == [Fraction(5, 2), Fraction(1, 2), Fraction(1)]
    assert [it.dur for it in bars[1]] == [Fraction(1, 3)] * 3 + [Fraction(3)]
    _, problems = parse_notes("E2:b0 E2:b4", BAR, 0.6)
    assert "invalid length ':b0'" in problems[0][1]


def test_bar_length_hints():
    _, problems = parse_notes("E2:4 E2:8t E2", BAR, 0.6)
    assert problems == [(0, "duration 5/3 beats, expected 4: 7/3 beat(s) missing (e.g. add r:b7/3)")]
    _, problems = parse_notes("E2:b6", BAR, 0.6)
    assert "2 beat(s) too many; a note cannot cross the barline" in problems[0][1]


def test_hits():
    from beat.notation import parse_hits

    bars, problems = parse_hits("hh: every 0.5 | every 1/3\nsd: 2!acc 3.75!ghost 4!flam | 1+2/3", BAR, 0.6, 2)
    assert problems == []
    hh0 = [it.onset for it in bars[0] if it.lane == "hh"]
    assert hh0 == [Fraction(i, 2) for i in range(8)]
    assert [it.onset for it in bars[1] if it.lane == "hh"] == [Fraction(i, 3) for i in range(12)]
    sd0 = [(it.onset, it.arts) for it in bars[0] if it.lane == "sd"]
    assert sd0 == [(1, {"acc": True}), (Fraction(11, 4), {"ghost": True}), (3, {"flam": True})]
    assert [it.onset for it in bars[1] if it.lane == "sd"] == [Fraction(2, 3)]


def test_hits_errors():
    from beat.notation import parse_hits

    _, problems = parse_hits("sd: 2 5 2 3!accent\nbd: 1 | 1\nxx: 1", BAR, 0.6, 1)
    messages = [m for _, m in problems]
    assert "lane 'sd': beat 5 is outside the bar (beats 1 to 5, exclusive)" in messages
    assert "lane 'sd': beat 2 is listed twice" in messages
    assert "lane 'sd': unknown hit mark '!accent' (did you mean 'acc'?) (use !acc, !ghost or !flam)" in messages
    assert "lane 'bd' has 2 bar(s) separated by '|', expected 1" in messages
    assert any("unknown drum lane 'xx'" in m for m in messages)


def test_inexact_decimals_are_rejected():
    from beat.notation import parse_hits

    _, problems = parse_hits("rd: 1 1.667 | every 0.333", BAR, 0.6, 2)
    assert problems == [
        (0, "lane 'rd': beat '1.667' is not an exact subdivision; write thirds and other divisions as fractions, e.g. 1+2/3"),
        (1, "lane 'rd': every '0.333' is not an exact subdivision; write thirds and other divisions as fractions, e.g. 1/3"),
    ]
    _, problems = parse_notes("C4:b0.333 C4:b3.667", BAR, 0.6)
    assert "e.g. 1/3" in problems[0][1] and "e.g. 3+2/3" in problems[1][1]
    _, problems = parse_notes("C4:b2.5 C4:b1.5", BAR, 0.6)
    assert problems == []
