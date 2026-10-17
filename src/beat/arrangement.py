"""Arrangement checks across parts, on the compiled score: clear defects only, never matters of style.

Agents rarely look at their parts after writing them, so these reach them as `beat validate` warnings.
"""

from collections import defaultdict
from statistics import mean, median

from .diagnostics import Diagnostics, loc
from .notation import fmt_beats
from .pitch import pitch_name

# The lowest note at which a close interval still sounds clear (orchestration rule of thumb).
LOW_INTERVAL_LIMIT = {1: 52, 2: 51, 3: 48, 4: 46}  # m2 above E3, M2 Eb3, m3 C3, M3 Bb2
CLASH_SEC = 0.4  # a minor 9th over the bass shorter than this passes as a passing note
STATIC_MIN_BARS = 16


def lead_part(compiled, events=None) -> str | None:
    """The part carrying the melody: a guitar with the lead tone, else the highest mostly single-note part."""
    insts = compiled.song.instruments
    leads = [p for p, i in insts.items() if i.tone == "lead"]
    if leads:
        return leads[0]
    events = compiled.events if events is None else events
    best, best_pitch = None, -1.0
    for pid, inst in insts.items():
        if inst.type in ("drums", "bass"):
            continue
        evs = [e for e in events if e.part == pid]
        if not evs or len(evs) / len({e.beat for e in evs}) > 1.2:  # mostly chords: accompaniment
            continue
        p = mean(e.pitch for e in evs)
        if p > best_pitch:
            best, best_pitch = pid, p
    return best


def _at(ev) -> str:
    return loc(ev.src["section"], ev.part, f"bar {ev.src['bar']}, beat {fmt_beats(ev.pos_in_bar + 1)}")


def check_arrangement(compiled, diags: Diagnostics) -> None:
    events = compiled.events
    insts = compiled.song.instruments
    lead = lead_part(compiled, events)
    _muddy_voicings(events, insts, diags)
    if lead:
        _bass_clashes(compiled, events, insts, lead, diags)
        _buried_lead(events, insts, lead, diags)
    _static_parts(events, insts, diags)


def _muddy_voicings(events, insts, diags: Diagnostics) -> None:
    chords = defaultdict(list)
    for e in events:
        if insts[e.part].pitched:
            chords[(e.part, e.beat)].append(e)
    found = defaultdict(list)  # (section, part, low, high) -> the chords that have it
    for group in chords.values():
        ps = sorted({e.pitch for e in group})
        for lo, hi in zip(ps, ps[1:]):
            limit = LOW_INTERVAL_LIMIT.get(hi - lo)
            if limit and lo < limit:
                found[(group[0].src["section"], group[0].part, lo, hi)].append(group[0])
    for (_, _, lo, hi), where in found.items():
        more = len({(e.src["instance"], e.src["bar"], e.pos_in_bar) for e in where}) - 1
        diags.warn(_at(where[0]), f"{pitch_name(lo)} and {pitch_name(hi)} sound muddy together this low"
                                  f"{f' (and {more} more time(s) in this section)' if more else ''}; voice the "
                                  f"chord higher, or drop one of them (e.g. a power chord)")


def _bass_clashes(compiled, events, insts, lead, diags: Diagnostics) -> None:
    bass = [e for e in events if insts[e.part].type == "bass"]
    for e in (e for e in events if e.part == lead):
        for b in bass:
            start, end = max(e.beat, b.beat), min(e.beat + e.beats, b.beat + b.beats)
            if end <= start or (e.pitch - b.pitch) % 12 != 1 or e.pitch < b.pitch:
                continue
            sec = compiled.beat_to_sec(float(end)) - compiled.beat_to_sec(float(start))
            if sec >= CLASH_SEC:
                diags.warn(_at(e), f"{pitch_name(e.pitch)} sounds a minor 9th over the bass {pitch_name(b.pitch)} "
                                   f"for {sec:.1f} s, which grates; change one of the two notes or "
                                   f"move the lead on sooner")
                break


def _buried_lead(events, insts, lead, diags: Diagnostics) -> None:
    # Distorted rhythm guitars mask a lead in their register; keys comping above a lead are normal.
    rhythm = [e for e in events if e.part != lead and insts[e.part].type == "guitar"]
    pairs = defaultdict(list)  # section instance -> (lead pitch, top rhythm note under it)
    for e in (e for e in events if e.part == lead):
        tops = [r.pitch for r in rhythm if r.beat <= e.beat < r.beat + r.beats]
        if tops:
            pairs[(e.src["section"], e.src["instance"])].append((e.pitch, max(tops)))
    for (section, _), notes in pairs.items():
        if len(notes) < 8:
            continue
        lead_mid, top_mid = median(p for p, _ in notes), median(t for _, t in notes)
        if lead_mid < top_mid:
            diags.warn(loc(section, lead),
                       f"the lead mostly sits under the rhythm guitars (its middle note "
                       f"{pitch_name(int(lead_mid))}, their top notes around {pitch_name(int(top_mid))}), "
                       f"so they mask it; move the lead up an octave, or thin out or lower the rhythm guitars here")


def _static_parts(events, insts, diags: Diagnostics) -> None:
    for pid in insts:
        bars = defaultdict(list)
        for e in events:
            if e.part == pid:
                bars[e.src["global_bar"]].append((e.pos_in_bar, e.lane or e.pitch, e.beats))
        contents = {tuple(sorted(v)) for v in bars.values()}
        if len(bars) >= STATIC_MIN_BARS and len(contents) == 1:
            diags.warn(loc(pid), f"plays the very same bar in all {len(bars)} bars it plays; vary it "
                                 f"between sections (fills, accents, a different groove in the chorus)")
