import pytest

from beat.checks import fingering
from beat.cli import main
from beat.pitch import chord_tones, parse_chord, parse_pitch
from beat.voicing import voicings

GUITAR = tuple(parse_pitch(n) for n in ["E2", "A2", "D3", "G3", "B3", "E4"])


@pytest.mark.parametrize("chord", ["Am", "C", "G", "F", "E7", "Bm", "D/F#", "Cmaj7", "Bdim", "Asus4", "Gadd9"])
def test_guitar_voicings_are_playable_chord_tones(chord):
    found = voicings(chord, "full", tuning=GUITAR, frets=22, limit=20)
    assert found
    pcs = parse_chord(chord)
    bass = chord_tones(chord)[2]
    for v in found:
        assert fingering(v.pitches, GUITAR, 22) is not None, v.shape
        assert {p % 12 for p in v.pitches} <= pcs
        assert v.pitches[0] % 12 == bass


def test_common_shapes_rank_high():
    def top(chord):
        return [v.shape for v in voicings(chord, "full", tuning=GUITAR, frets=22, limit=3)]
    assert "x02210" in top("Am") and "577555" in top("Am")
    assert top("C")[0] == "x32010"
    assert top("G")[0] == "320003"
    assert top("F")[0] == "133211"


def test_barre_cannot_skip_an_open_string():
    shapes = [v.shape for v in voicings("F", "full", tuning=GUITAR, frets=22, limit=50)]
    assert "103211" not in shapes


def test_power_and_keys():
    power = voicings("Am", "power", tuning=GUITAR, frets=22, limit=2)
    assert [v.shape for v in power] == ["577xxx", "x022xx"] and power[0].notes == "[A2 E3 A3]"
    drop_d = tuple(parse_pitch(n) for n in ["D2", "A2", "D3", "G3", "B3", "E4"])
    assert voicings("D5", "power", tuning=drop_d, frets=22)[0].shape == "000xxx"
    assert [v.notes for v in voicings("C", "full", low=parse_pitch("C4"))] == \
        ["[C4 E4 G4]", "[E4 G4 C5]", "[G4 C5 E5]"]
    assert voicings("G/B", "full", low=parse_pitch("C3"))[0].notes == "[B3 G4 B4 D5]"
    with pytest.raises(ValueError, match="no perfect fifth"):
        voicings("Bdim", "power", tuning=GUITAR, frets=22)


def test_voicing_cli(capsys):
    assert main(["voicing", "Am"]) == 0
    assert "x02210             [A2 E3 A3 C4 E4]" in capsys.readouterr().out
    assert main(["voicing", "Am", "power", "--for", "piano", "--low", "A2"]) == 0
    assert "[A2 E3 A3]" in capsys.readouterr().out
    assert main(["voicing", "H7"]) == 1
    assert "invalid chord symbol 'H7'" in capsys.readouterr().err
    assert main(["voicing", "C", "--for", "organ", "--tuning", "E2"]) == 1
