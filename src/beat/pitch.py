"""Pitch names and chord symbols."""

import re

_NOTE_RE = re.compile(r"^([A-G])([#b]*)(-?\d)$")
_STEP = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def parse_pitch(name: str) -> int:
    """Scientific pitch name to MIDI number (C4 = 60). Raises ValueError."""
    m = _NOTE_RE.match(name)
    if not m:
        hint = " (note letters are uppercase)" if name[:1].islower() else ""
        raise ValueError(f"invalid pitch '{name}'{hint} (expected e.g. E2, F#3, Bb4)")
    letter, acc, octave = m.groups()
    shift = acc.count("#") - acc.count("b")
    midi = (int(octave) + 1) * 12 + _STEP[letter] + shift
    if not 0 <= midi <= 127:
        raise ValueError(f"pitch '{name}' is outside the MIDI range")
    return midi


def pitch_name(midi: int) -> str:
    return f"{_NAMES[midi % 12]}{midi // 12 - 1}"


# Longer suffixes first so the regex alternation prefers them.
_QUALITIES = {
    "maj7": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10),
    "m6": (0, 3, 7, 9),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "add9": (0, 2, 4, 7),
    "dim": (0, 3, 6),
    "aug": (0, 4, 8),
    "m": (0, 3, 7),
    "7": (0, 4, 7, 10),
    "5": (0, 7),
    "6": (0, 4, 7, 9),
    "": (0, 4, 7),
}
_CHORD_RE = re.compile(
    r"^([A-G][#b]?)(" + "|".join(q for q in _QUALITIES if q) + r")?(?:/([A-G][#b]?))?$"
)


def _pitch_class(name: str) -> int:
    return (_STEP[name[0]] + name[1:].count("#") - name[1:].count("b")) % 12


def chord_tones(symbol: str) -> tuple[int, tuple[int, ...], int] | None:
    """Chord symbol to (root pitch class, intervals above the root, bass pitch class); None for N.C.

    Raises ValueError.
    """
    if symbol == "N.C.":
        return None
    m = _CHORD_RE.match(symbol)
    if not m:
        suffixes = ", ".join(q for q in _QUALITIES if q)
        raise ValueError(f"invalid chord symbol '{symbol}' (root A-G with optional # or b, then one of: "
                         f"{suffixes}, or nothing for major; optional /bass; N.C. for no chord)")
    root, quality, bass = m.groups()
    r = _pitch_class(root)
    return r, _QUALITIES[quality or ""], _pitch_class(bass) if bass else r


def parse_chord(symbol: str) -> frozenset[int] | None:
    """Chord symbol to the set of its pitch classes; None for N.C. Raises ValueError."""
    tones = chord_tones(symbol)
    if tones is None:
        return None
    root, intervals, bass = tones
    return frozenset({(root + i) % 12 for i in intervals} | {bass})
