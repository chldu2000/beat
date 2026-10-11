"""Musical and physical plausibility checks on resolved sections."""

from itertools import groupby

from .diagnostics import Diagnostics, loc
from .notation import LANES, STRING_ARTS, Item, fmt_beats
from .pitch import pitch_name
from .song import Instrument, Section, Song

MAX_FRET_SPAN = 4  # highest fretted note minus lowest fretted note
# Natural harmonics: semitones above the open string -> (harmonic number, fret over the node).
HARMONICS = {12: (2, 12), 19: (3, 7), 24: (4, 5), 28: (5, 4), 31: (6, 3)}
MAX_BEND = {"guitar": 3.0, "bass": 2.0}  # semitones; more is rarely playable


def harmonic_strings(pitch: int, tuning: tuple[int, ...]) -> list[int]:
    """Strings on which `pitch` sounds as a natural harmonic."""
    return [s for s, o in enumerate(tuning) if pitch - o in HARMONICS]


def fingering(pitches: tuple[int, ...], tuning: tuple[int, ...], frets: int) -> list[tuple[int, int]] | None:
    """Find (string index, fret) for each pitch on distinct strings within one hand span."""
    if len(pitches) > len(tuning):
        return None
    best: list[tuple[int, int]] | None = None

    def search(i: int, used: list[tuple[int, int]]) -> bool:
        nonlocal best
        if i == len(pitches):
            fretted = [f for _, f in used if f > 0]
            if not fretted or max(fretted) - min(fretted) <= MAX_FRET_SPAN:
                best = list(used)
                return True
            return False
        for s, open_pitch in enumerate(tuning):
            fret = pitches[i] - open_pitch
            if 0 <= fret <= frets and all(s != us for us, _ in used):
                if search(i + 1, used + [(s, fret)]):
                    return True
        return False

    search(0, [])
    return best


def check_section(song: Song, section: Section, diags: Diagnostics) -> None:
    for pid, bars in section.parts.items():
        inst = song.instruments[pid]
        for bi, items in enumerate(bars):
            where = loc(section.id, pid, f"bar {bi + 1}")
            if inst.pitched:
                for item in items:
                    _check_pitched(inst, item, where, diags)
            else:
                _check_limbs(items, where, diags)
        if inst.type == "bass" and section.chords:
            _check_bass_chord_tones(section, pid, bars, diags)


def _check_pitched(inst: Instrument, item: Item, where: str, diags: Diagnostics) -> None:
    if not item.pitches:
        return
    at = f"{where}, beat {fmt_beats(item.onset + 1)}"
    strings = inst.type in ("guitar", "bass")
    if strings and item.arts.get("harm"):
        _check_harmonics(inst, item, at, diags)
        return
    lo, hi = inst.range
    for p in item.pitches:
        if not lo <= p <= hi:
            diags.error(at, f"{pitch_name(p)} is outside the {inst.type} range "
                            f"{pitch_name(lo)}-{pitch_name(hi)}")
            return

    names = " ".join(pitch_name(p) for p in item.pitches)
    if inst.type in ("guitar", "bass") and len(item.pitches) > 1:
        if inst.type == "bass" and len(item.pitches) > 2:
            diags.warn(at, f"bass plays {len(item.pitches)} notes at once ({names}); bass lines are usually 1-2 notes")
        if fingering(item.pitches, inst.tuning, inst.frets) is None:
            diags.error(at, f"[{names}] is not playable: needs one string per note and a fret span "
                            f"of at most {MAX_FRET_SPAN} (open strings excluded)")

    if strings:
        _check_bend(inst, item, at, diags)
    else:
        bad = sorted(set(item.arts) & STRING_ARTS)
        if bad:
            diags.warn(at, f"articulation {', '.join('!' + a for a in bad)} does not apply to {inst.type}")
    if inst.type == "organ" and item.arts.get("acc"):
        diags.warn(at, "!acc has no effect on organ (no touch sensitivity); for a louder passage raise the "
                       "dynamic (@f, or the part's dynamic), which also drives the organ harder")


def _check_harmonics(inst: Instrument, item: Item, at: str, diags: Diagnostics) -> None:
    """`!harm` notes are written at the pitch they sound; each needs its own string with that harmonic."""
    names = " ".join(pitch_name(p) for p in item.pitches)

    def place(i: int, used: frozenset[int]) -> bool:
        return i == len(item.pitches) or any(
            place(i + 1, used | {s}) for s in harmonic_strings(item.pitches[i], inst.tuning) if s not in used)

    if not place(0, frozenset()):
        open_names = ", ".join(pitch_name(o) for o in inst.tuning)
        diags.error(at, f"{names}!harm is not a natural harmonic on {'distinct strings' if len(item.pitches) > 1 else 'any string'}"
                        f" (write the sounding pitch: an open string ({open_names}) plus 12, 19, 24, 28 or 31 "
                        f"semitones, i.e. over fret 12, 7, 5, 4 or 3); or drop !harm")
    if any(a in item.arts for a in ("bend", "sl", "h", "p")):
        diags.warn(at, "natural harmonics cannot be bent, slid or played legato; that articulation is ignored")


def _check_bend(inst: Instrument, item: Item, at: str, diags: Diagnostics) -> None:
    bend = item.arts.get("bend")
    names = " ".join(pitch_name(p) for p in item.pitches)
    if bend is not None and bend > MAX_BEND[inst.type]:
        diags.warn(at, f"{names}!bend={bend:g}: bends over {MAX_BEND[inst.type]:g} semitones are rarely playable "
                       f"on {inst.type}; write a higher fretted note with a smaller bend")
    if bend is not None or item.arts.get("vib"):
        for p in item.pitches:
            if not any(1 <= p - o <= inst.frets for o in inst.tuning):
                what = "bent" if bend is not None else "given vibrato"
                diags.warn(at, f"{pitch_name(p)} can only be played on an open string, which cannot be {what}; "
                               f"move the note up an octave or drop the articulation")


def _check_limbs(items: list[Item], where: str, diags: Diagnostics) -> None:
    for onset, group in groupby(items, key=lambda it: it.onset):
        group = list(group)
        hands = sum(2 if it.arts.get("flam") else 1 for it in group if LANES[it.lane][1] == "hand")
        if hands > 2:
            lanes = ", ".join(it.lane + (" (flam)" if it.arts.get("flam") else "") for it in group
                              if LANES[it.lane][1] == "hand")
            diags.error(f"{where}, beat {fmt_beats(onset + 1)}",
                        f"drummer needs {hands} hands for {lanes}; at most 2 hand-played hits at once")


def _check_bass_chord_tones(section: Section, pid: str, bars: list[list[Item]], diags: Diagnostics) -> None:
    for bi, (items, chords) in enumerate(zip(bars, section.chords)):
        for chord in chords:
            if chord.pcs is None:
                continue
            note = next((it for it in items if it.onset == chord.onset and it.pitches), None)
            if note and note.pitches[0] % 12 not in chord.pcs:
                diags.warn(loc(section.id, pid, f"bar {bi + 1}, beat {fmt_beats(chord.onset + 1)}"),
                           f"bass plays {pitch_name(note.pitches[0])} under {chord.symbol}, "
                           f"which is not a chord tone")
