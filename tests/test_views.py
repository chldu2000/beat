from pathlib import Path

import pytest

from beat.cli import main
from beat.compile import compile_song
from beat.diagnostics import Diagnostics
from beat.song import load_song
from beat.views import by_bar, parse_bar_range, select

ROOT = Path(__file__).parent.parent
TRICKY = ROOT / "evals" / "refs" / "tricky.beat.yaml"


def compiled(path: Path):
    diags = Diagnostics()
    c = compile_song(load_song(path.read_text(), diags), diags)
    assert not diags.has_errors
    return c


def test_parse_bar_range():
    assert parse_bar_range("5") == (5, 5)
    assert parse_bar_range("5-8") == (5, 8)
    for bad in ("0", "8-5", "x", ""):
        with pytest.raises(ValueError):
            parse_bar_range(bad)


def test_by_bar_view():
    c = compiled(TRICKY)
    text = by_bar(c, select(c.events, ["gt", "dr"], (1, 1)))
    lines = text.splitlines()
    assert lines[0] == "bar 1 = s#1 bar 1  (92 BPM)  chords: Em"
    assert lines[1].startswith("  dr    1:bd+rd  1+2/3:rd  2:ss+rd")
    assert lines[2].startswith("  gt    1:E3/(1/3)  1+1/3:G3/(1/3)")
    assert lines[2].endswith("3:G3/1")


def test_by_bar_shows_ties_as_one_long_note_and_arts():
    c = compiled(TRICKY)
    text = by_bar(c, select(c.events, ["bs", "gt"], (4, 5)))
    assert "4:C2/6" not in text  # positions are 1-based beats within the bar
    assert "1:C2/6" in text
    assert "3:E3+G3+B3/1!st" in text


def test_events_cli_filters(capsys):
    assert main(["events", str(TRICKY), "--bars", "6", "--parts", "bs"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].split()[:4] == ["bar", "beat", "len", "part"]
    assert len(out) == 1 + 5 and all(line.split()[0] == "6" for line in out[1:])

    assert main(["events", str(TRICKY), "--parts", "gtr"]) == 1
    assert "unknown part 'gtr' (did you mean 'gt'?)" in capsys.readouterr().err
