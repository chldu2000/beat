"""Human- and agent-readable views of compiled events."""

from collections import defaultdict
from fractions import Fraction
from itertools import groupby

from .compile import Compiled, Event
from .pitch import pitch_name

DUR_NAMES = {
    Fraction(4): "whole", Fraction(3): "dotted half", Fraction(2): "half",
    Fraction(3, 2): "dotted quarter", Fraction(1): "quarter", Fraction(3, 4): "dotted eighth",
    Fraction(1, 2): "eighth", Fraction(3, 8): "dotted sixteenth", Fraction(1, 4): "sixteenth",
    Fraction(1, 8): "32nd", Fraction(2, 3): "quarter-note triplet", Fraction(1, 3): "eighth-note triplet",
    Fraction(1, 6): "sixteenth-note triplet",
}


def fmt_pos(x: Fraction) -> str:
    """Beats as a decimal when exact (2.5), else a mixed fraction (1+1/3)."""
    if x.denominator in (1, 2, 4, 8, 16):
        return f"{float(x):g}"
    whole = x.numerator // x.denominator
    rest = x - whole
    return f"{whole}+{rest.numerator}/{rest.denominator}" if whole else f"{rest.numerator}/{rest.denominator}"


def fmt_len(x: Fraction) -> str:
    name = DUR_NAMES.get(x)
    return f"{fmt_pos(x)} beats" + (f" ({name})" if name else "")


def parse_bar_range(text: str) -> tuple[int, int]:
    """'5' or '5-8' (global bar numbers, 1-based). Raises ValueError."""
    first, _, last = text.partition("-")
    try:
        lo, hi = int(first), int(last or first)
    except ValueError:
        lo, hi = 0, 0
    if lo < 1 or hi < lo:
        raise ValueError(f"invalid bar range '{text}' (use e.g. 5 or 5-8)")
    return lo, hi


def select(events: list[Event], parts: list[str] | None = None,
           bars: tuple[int, int] | None = None) -> list[Event]:
    return [e for e in events
            if (not parts or e.part in parts)
            and (not bars or bars[0] <= e.src["global_bar"] <= bars[1])]


def _arts(arts: dict) -> str:
    return "".join(f"!{k}" if v is True else f"!{k}={v:g}" for k, v in arts.items())


def table(compiled: Compiled, events: list[Event]) -> str:
    """One line per note: score position and length in beats, then the performed time."""
    lines = [f"{'bar':>4} {'beat':>6} {'len':>6}  {'part':<6} {'note':<5} {'vel':>4}  {'time':>7}  "
             f"{'source':<22} arts"]
    for e in sorted(events, key=lambda e: (e.beat, e.part, e.pitch)):
        s = e.src
        lines.append(f"{s['global_bar']:>4} {fmt_pos(Fraction(s['beat']).limit_denominator(48)):>6} "
                     f"{fmt_pos(e.beats):>6}  {e.part:<6} {e.lane or pitch_name(e.pitch):<5} "
                     f"{e.velocity:4.2f}  {e.time:7.3f}  "
                     f"{s['section'] + '#' + str(s['instance']) + ' bar ' + str(s['bar']):<22} {_arts(e.arts)}")
    return "\n".join(lines)


def by_bar(compiled: Compiled, events: list[Event]) -> str:
    """Compact score view: one line per part per bar, `beat:note/length` items.

    Lengths are in beats, parenthesized when fractional: `1:E3/(1/3)`. Chords and drum hits
    that start together are joined with '+'.
    """
    song = compiled.song
    by_key: dict[int, dict[str, list[Event]]] = defaultdict(lambda: defaultdict(list))
    for e in events:
        by_key[e.src["global_bar"]][e.part].append(e)

    instance_of_bar = {}
    for ins in compiled.instances:
        for i in range(ins.section.bars):
            instance_of_bar[ins.global_bar + i] = (ins, i)

    lines = []
    for bar in sorted(by_key):
        ins, i = instance_of_bar[bar]
        chords = ""
        if ins.section.chords:
            chords = "  chords: " + " ".join(c.symbol for c in ins.section.chords[i])
        lines.append(f"bar {bar} = {ins.name} bar {i + 1}  ({ins.section.tempo:g} BPM){chords}")
        for pid in song.instruments:
            part_events = sorted(by_key[bar].get(pid, []), key=lambda e: (e.src["beat"], e.pitch))
            if not part_events:
                continue
            items = []
            for beat, group in groupby(part_events, key=lambda e: e.src["beat"]):
                group = list(group)
                pos = fmt_pos(Fraction(beat).limit_denominator(48))
                if group[0].lane:
                    hits = "+".join(e.lane + _arts(e.arts) for e in group)
                    items.append(f"{pos}:{hits}")
                else:
                    notes = "+".join(pitch_name(e.pitch) for e in group)
                    length = fmt_pos(group[0].beats)
                    if "/" in length:
                        length = f"({length})"
                    items.append(f"{pos}:{notes}/{length}{_arts(group[0].arts)}")
            lines.append(f"  {pid:<5} " + "  ".join(items))
    return "\n".join(lines)
