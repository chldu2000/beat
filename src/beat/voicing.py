"""Chord voicings for `beat voicing`: playable note sets to paste into `notes`.

The DSL never voices chords itself (what the file says is what plays); this is a lookup aid.
"""

from dataclasses import dataclass
from itertools import product

from .checks import MAX_FRET_SPAN
from .pitch import chord_tones, pitch_name

STYLES = ("full", "power")
OPEN_POSITION = 3  # open strings only combine with fretted notes when the hand is this close to the nut


@dataclass(frozen=True)
class Voicing:
    pitches: tuple[int, ...]  # low to high
    frets: tuple[int | None, ...] | None = None  # per string, low to high; None = not played

    @property
    def notes(self) -> str:
        return "[" + " ".join(pitch_name(p) for p in self.pitches) + "]"

    @property
    def shape(self) -> str:
        """Tab-style shape: 'x02210', or 'x-12-14-14-13-x' when a fret has two digits."""
        if self.frets is None:
            return ""
        marks = ["x" if f is None else str(f) for f in self.frets]
        return ("-" if any(len(m) > 1 for m in marks) else "").join(marks)


def voicings(symbol: str, style: str, *, tuning: tuple[int, ...] = (), frets: int = 0,
             low: int = 48, limit: int = 6) -> list[Voicing]:
    """Voicings of a chord symbol. Fretted (tuning given) or keyboard (from `low` upward). Raises ValueError."""
    tones = chord_tones(symbol)
    if tones is None:
        raise ValueError("N.C. has no notes to voice")
    root, intervals, bass = tones
    if style == "power":
        if 7 not in intervals:
            raise ValueError(f"'{symbol}' has no perfect fifth, so it has no power chord; use the full voicing")
        found = _fretted_power(root, tuning, frets) if tuning else _keys_power(root, low)
    elif tuning:
        found = _fretted_full(root, intervals, bass, tuning, frets)
    else:
        found = _keys_full(root, intervals, bass, low)
    return found[:limit]


def _fretted_power(root: int, tuning: tuple[int, ...], frets: int) -> list[Voicing]:
    """Root, fifth and (when there is a string for it) octave on adjacent strings."""
    out = []
    for s in range(len(tuning) - 1):
        for f in range(frets + 1):
            p = tuning[s] + f
            if p % 12 != root:
                continue
            pitches = (p, p + 7, p + 12)[:min(3, len(tuning) - s)]
            fs = [pp - tuning[s + i] for i, pp in enumerate(pitches)]
            if not all(0 <= x <= frets for x in fs) or not _reachable(fs):
                continue
            shape = [None] * len(tuning)
            shape[s:s + len(fs)] = fs
            out.append(Voicing(pitches, tuple(shape)))
    return sorted(out, key=lambda v: v.pitches)


def _fretted_full(root: int, intervals: tuple[int, ...], bass: int,
                  tuning: tuple[int, ...], frets: int) -> list[Voicing]:
    """Every chord tone, the bass note lowest, adjacent strings, within one hand position."""
    pcs = {(root + i) % 12 for i in intervals}
    required = set(pcs)
    if len(intervals) >= 4:
        required.discard((root + 7) % 12)  # the fifth is usually left out of four-note chords
    allowed = pcs | {bass}
    min_strings = min(len(tuning), max(3, len(required)))

    found: set[tuple[int | None, ...]] = set()
    for base in range(0, frets - MAX_FRET_SPAN + 1):
        window = ([0] if base <= OPEN_POSITION else []) + list(range(max(base, 1), min(base + MAX_FRET_SPAN, frets) + 1))
        options = [[None] + [f for f in window if (t + f) % 12 in allowed] for t in tuning]
        for combo in product(*options):
            played = [s for s, f in enumerate(combo) if f is not None]
            if len(played) < min_strings or played != list(range(played[0], played[-1] + 1)):
                continue
            pitches = [tuning[s] + combo[s] for s in played]
            if pitches[0] % 12 != bass or len(set(pitches)) != len(pitches) or min(pitches) != pitches[0]:
                continue
            if not required <= {p % 12 for p in pitches}:
                continue
            if _reachable([combo[s] for s in played]):
                found.add(combo)

    # Drop shapes that are another shape with strings left off.
    def contained(a, b):
        return a != b and all(x is None or x == y for x, y in zip(a, b))
    kept = [c for c in found if not any(contained(c, o) for o in found)]

    def rank(c):  # easiest and fullest first: fingers cost, extra strings help, high positions cost a little
        played = [f for f in c if f is not None]
        return (_fingers(played) - 0.5 * len(played) + 0.1 * max(played), max(played))
    return [Voicing(tuple(sorted(tuning[s] + f for s, f in enumerate(c) if f is not None)), c)
            for c in sorted(kept, key=rank)]


def _reachable(fs: list[int]) -> bool:
    """One hand (frets in string order, 0 = open): within the span and at most 4 fingers."""
    fretted = [f for f in fs if f > 0]
    return not fretted or (max(fretted) - min(fretted) <= MAX_FRET_SPAN and _fingers(fs) <= 4)


def _fingers(fs: list[int]) -> int:
    """Fingers for frets in string order (0 = open). Notes at the lowest fret share one barre finger,
    unless an open string lies between them (a barre would mute it)."""
    fretted = [f for f in fs if f > 0]
    if not fretted:
        return 0
    at_min = [i for i, f in enumerate(fs) if f == min(fretted)]
    if any(f == 0 for f in fs[at_min[0]:at_min[-1]]):
        return len(fretted)
    return len(fretted) - len(at_min) + 1


def _keys_power(root: int, low: int) -> list[Voicing]:
    first = low + (root - low) % 12
    return [Voicing((p, p + 7, p + 12)) for p in (first, first + 12)]


def _keys_full(root: int, intervals: tuple[int, ...], bass: int, low: int) -> list[Voicing]:
    """Close position from `low` upward: root position, then each inversion; a slash bass goes underneath."""
    tones = [(root + i) % 12 for i in intervals]
    under = [low + (bass - low) % 12] if bass != root else []
    start = under[0] + 1 if under else low
    out = []
    for k in range(len(tones)):
        order = tones[k:] + tones[:k]
        pitches = under + [start + (order[0] - start) % 12]
        for pc in order[1:]:
            pitches.append(pitches[-1] + 1 + (pc - pitches[-1] - 1) % 12)
        out.append(Voicing(tuple(pitches)))
    return out
