"""Score-level views of a song: performance stripped, so only what the score says is compared."""

from collections import defaultdict
from fractions import Fraction
from pathlib import Path

from beat.compile import ACCENT, GHOST, Compiled, Event, compile_song
from beat.diagnostics import Diagnostics
from beat.notation import DYNAMICS
from beat.pitch import pitch_name
from beat.song import Song, load_song
from beat.views import fmt_len, fmt_pos


def load(path: Path) -> tuple[Diagnostics, Song | None, Compiled | None]:
    diags = Diagnostics()
    try:
        song = load_song(path.read_text(encoding="utf-8"), diags)
        compiled = compile_song(song, diags) if song else None
    except Exception as e:  # a crash is a finding, not a reason to stop grading
        diags.error("", f"internal error: {type(e).__name__}: {e}")
        return diags, None, None
    return diags, song, compiled


def score_events(song: Song) -> list[Event]:
    """Events with score velocities and positions (no humanize, swing, edits or offsets)."""
    perf, song.performance = song.performance, {}
    try:
        return compile_song(song, Diagnostics()).events
    finally:
        song.performance = perf


def base_dynamic(ev: Event) -> str:
    level = ev.velocity
    if ev.arts.get("acc"):
        level -= ACCENT
    if ev.arts.get("ghost"):
        level /= GHOST
    return min(DYNAMICS, key=lambda d: abs(DYNAMICS[d] - level))


# --- comparison ---------------------------------------------------------------

def _key(ev: Event) -> tuple:
    return ev.part, ev.beat, ev.lane or ev.pitch


def _where(ev: Event, bar_beats: Fraction) -> str:
    bar = int(ev.beat // bar_beats) + 1
    beat = ev.beat - (bar - 1) * bar_beats + 1
    return f"{ev.part} bar {bar} beat {fmt_pos(beat)} {ev.lane or pitch_name(ev.pitch)}"


def compare(cand: Song, ref: Song) -> dict:
    """Note-level agreement of a candidate with a reference, keyed by part, onset and pitch/lane."""
    c = {_key(e): e for e in score_events(cand)}
    r = {_key(e): e for e in score_events(ref)}
    matched = c.keys() & r.keys()
    precision = len(matched) / len(c) if c else 0.0
    recall = len(matched) / len(r) if r else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    def share(pred) -> float:
        return sum(1 for k in matched if pred(c[k], r[k])) / len(matched) if matched else 0.0

    per_part = {}
    for part in sorted({k[0] for k in r} | {k[0] for k in c}):
        rc = {k for k in r if k[0] == part}
        cc = {k for k in c if k[0] == part}
        m = len(rc & cc)
        per_part[part] = round(2 * m / (len(rc) + len(cc)), 3) if rc or cc else 1.0

    bar_beats = ref.bar_beats
    wrong_len = [k for k in matched if c[k].beats != r[k].beats and not c[k].lane]
    return {
        "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
        "duration_acc": round(share(lambda a, b: a.lane is not None or a.beats == b.beats), 3),
        "arts_acc": round(share(lambda a, b: a.arts == b.arts), 3),
        "dynamic_acc": round(share(lambda a, b: abs(a.velocity - b.velocity) < 0.01), 3),
        "per_part_f1": per_part,
        "missing": [_where(r[k], bar_beats) for k in sorted(r.keys() - c.keys(), key=_sort)][:15],
        "extra": [_where(c[k], bar_beats) for k in sorted(c.keys() - r.keys(), key=_sort)][:15],
        "wrong_length": [f"{_where(c[k], bar_beats)}: {fmt_len(c[k].beats)} instead of {fmt_len(r[k].beats)}"
                         for k in sorted(wrong_len, key=_sort)][:15],
    }


def _sort(k: tuple):
    return k[1], k[0], str(k[2])


def section_events(song: Song, section_ids: list[str]) -> dict[str, list[tuple]]:
    """Score events of the given sections, relative to each instance, for unchanged-ness checks."""
    out: dict[str, list[tuple]] = defaultdict(list)
    for e in score_events(song):
        s = e.src
        if s["section"] in section_ids:
            out[s["section"]].append((s["instance"], s["bar"], s["beat"], e.part, e.lane or e.pitch,
                                      float(e.beats), round(e.velocity, 3), tuple(sorted(e.arts.items()))))
    return {k: sorted(v) for k, v in out.items()}
