"""Assign each note of a guitar or bass part to a string and fret, the way a player's hand would.

Notes starting at the same score position form a chord. Each chord takes the playable fingering
(distinct strings, fret span within one hand) that moves the hand least, keeps legato notes
(`!h`, `!p`, `!sl`) on the string of the previous note, and avoids cutting a note that is still held.
"""

from collections.abc import Iterator
from itertools import groupby

from ..checks import MAX_FRET_SPAN
from ..compile import Event

LEGATO_ARTS = ("h", "p", "sl")
HELD_EPS = 0.01  # seconds; a note ending within this of the next onset counts as released
BOX = 4  # frets one hand position covers without moving
OPEN_REACH = 5  # from this hand position on, open strings are a stretch


def fingerings(pitches: tuple[int, ...], tuning: tuple[int, ...], frets: int,
               span: int = MAX_FRET_SPAN) -> Iterator[tuple[tuple[int, int], ...]]:
    """Every (string, fret) assignment on distinct strings with fretted notes within `span` frets."""
    def search(i: int, used: tuple[tuple[int, int], ...]) -> Iterator[tuple[tuple[int, int], ...]]:
        if i == len(pitches):
            yield used
            return
        for s, open_pitch in enumerate(tuning):
            fret = pitches[i] - open_pitch
            if not 0 <= fret <= frets or any(s == us for us, _ in used):
                continue
            fretted = [f for _, f in used if f > 0] + ([fret] if fret > 0 else [])
            if fretted and max(fretted) - min(fretted) > span:
                continue
            yield from search(i + 1, used + ((s, fret),))

    yield from search(0, ())


def _fallback(pitches: tuple[int, ...], tuning: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    """For notes no hand can play: each note on the highest string at or below it."""
    out = []
    for p in pitches:
        s = max((i for i, o in enumerate(tuning) if o <= p), default=0, key=lambda i: tuning[i])
        out.append((s, max(0, p - tuning[s])))
    return tuple(out)


def _hand_after(hand: float | None, fretted: list[int]) -> float:
    """Index-finger fret after the smallest move that brings all fretted notes under the hand."""
    lo, hi = min(fretted), max(fretted)
    first, last = min(lo, hi - BOX + 1), lo  # hand positions that cover the notes
    if hand is None:
        return float(last)
    return float(min(max(hand, first), last))


def assign(events: list[Event], tuning: tuple[int, ...], frets: int) -> list[tuple[int, int]]:
    """(string index, fret) for each event, in the order of `events`."""
    result: list[tuple[int, int] | None] = [None] * len(events)
    order = sorted(range(len(events)), key=lambda i: (events[i].beat, events[i].pitch))
    hand: float | None = None  # fret under the index finger; the hand covers hand .. hand + BOX - 1
    sounding: dict[int, float] = {}  # string -> end time of the note on it
    last_strings: tuple[int, ...] = ()

    for _, grp in groupby(order, key=lambda i: events[i].beat):
        idx = list(grp)
        pitches = tuple(events[i].pitch for i in idx)
        onset = min(events[i].time for i in idx)
        legato = len(idx) == 1 and any(events[idx[0]].arts.get(a) for a in LEGATO_ARTS)

        def cost(fing: tuple[tuple[int, int], ...]) -> float:
            fretted = [f for _, f in fing if f > 0]
            c = 0.0
            if fretted:
                c += abs(_hand_after(hand, fretted) - hand) if hand is not None else 0.0
                c += 0.02 * min(fretted)  # mild preference for lower positions
            if hand is not None and hand >= OPEN_REACH:
                c += 0.6 * (len(fing) - len(fretted))  # open strings sound different up the neck
            for s, _ in fing:
                if sounding.get(s, -1.0) > onset + HELD_EPS:
                    c += 4.0  # would cut a note that is still held
            if legato and last_strings and fing[0][0] != last_strings[0]:
                c += 20.0
            return c

        best = min(fingerings(pitches, tuning, frets), key=cost, default=None) or _fallback(pitches, tuning)
        for i, sf in zip(idx, best):
            result[i] = sf
            sounding[sf[0]] = events[i].time + events[i].dur
        fretted = [f for _, f in best if f > 0]
        if fretted:
            hand = _hand_after(hand, fretted)
        last_strings = tuple(s for s, _ in best)
    return result  # type: ignore[return-value]
