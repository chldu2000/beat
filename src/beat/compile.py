"""Compile a Song into a flat, performed event list (spec section 11)."""

from dataclasses import dataclass, field
from fractions import Fraction

import numpy as np

from .diagnostics import Diagnostics, did_you_mean, loc
from .notation import fmt_beats
from .pitch import parse_pitch, pitch_name
from .song import Section, Song

ACCENT = 0.12
GHOST = 0.35
DEFAULT_STRUM_MS = {"guitar": 8.0}
PERF_KEYS = {"seed", "humanize", "swing", "parts", "edits"}
PART_PERF_KEYS = {"humanize", "swing", "offset_ms", "velocity", "strum_ms", "lanes"}
EDIT_KEYS = {"part", "section", "instance", "bar", "beat", "pitch", "lane", "velocity", "offset_ms", "length"}


@dataclass
class Instance:
    section: Section
    index: int  # 1-based occurrence of this section in the form
    start_beat: Fraction
    start_sec: float
    global_bar: int  # 1-based bar number of the first bar

    @property
    def name(self) -> str:
        return f"{self.section.id}#{self.index}"


@dataclass
class Event:
    part: str
    beat: Fraction  # score position from the start of the song
    beats: Fraction  # score length
    pitch: int
    lane: str | None
    velocity: float
    arts: dict
    src: dict
    time: float = 0.0  # performed onset, seconds
    dur: float = 0.0  # performed length, seconds
    pos_in_bar: Fraction = Fraction(0)
    chord_rank: int = 0  # index from the lowest note of a chord, for strumming

    def to_dict(self) -> dict:
        return {
            "part": self.part, "time": round(self.time, 4), "dur": round(self.dur, 4),
            "beat": float(self.beat), "beats": float(self.beats), "pitch": self.pitch,
            "lane": self.lane, "velocity": round(self.velocity, 3), "arts": self.arts, "src": self.src,
        }


@dataclass
class Compiled:
    song: Song
    instances: list[Instance]
    events: list[Event]
    total_beats: Fraction
    duration_sec: float
    total_bars: int
    form: list[str] = field(default_factory=list)

    def beat_to_sec(self, beat: float) -> float:
        return beat_to_sec(self.instances, beat)

    def sec_to_beat(self, sec: float) -> float:
        seg = self.instances[0]
        for ins in self.instances:
            if ins.start_sec <= sec:
                seg = ins
        return float(seg.start_beat) + (sec - seg.start_sec) * seg.section.tempo / 60

    def to_dict(self) -> dict:
        return {
            "meta": {"title": self.song.meta.get("title"), "duration_sec": round(self.duration_sec, 3),
                     "bars": self.total_bars, "form": self.form},
            "parts": {pid: {"type": i.type, **({"tone": i.tone} if i.tone else {})}
                      for pid, i in self.song.instruments.items()},
            "events": [e.to_dict() for e in self.events],
        }


def beat_to_sec(instances: list[Instance], beat: float) -> float:
    seg = instances[0]
    for ins in instances:
        if float(ins.start_beat) <= beat:
            seg = ins
    return seg.start_sec + (beat - float(seg.start_beat)) * 60 / seg.section.tempo


def build_timeline(song: Song, form: list[str]) -> tuple[list[Instance], Fraction, float, int]:
    instances: list[Instance] = []
    beat, sec, bar = Fraction(0), 0.0, 1
    counts: dict[str, int] = {}
    for sid in form:
        section = song.sections[sid]
        counts[sid] = counts.get(sid, 0) + 1
        instances.append(Instance(section, counts[sid], beat, sec, bar))
        length = section.bars * song.bar_beats
        beat += length
        sec += float(length) * 60 / section.tempo
        bar += section.bars
    return instances, beat, sec, bar - 1


def compile_song(song: Song, diags: Diagnostics, form: list[str] | None = None) -> Compiled:
    """Compile the song. `form` overrides the song's form (e.g. to render only some sections)."""
    form = form if form is not None else song.form
    instances, total_beats, duration, total_bars = build_timeline(song, form)
    events: list[Event] = []
    for pid in song.instruments:
        events.extend(_part_events(song, pid, instances, diags))
    compiled = Compiled(song, instances, events, total_beats, duration, total_bars, list(form))
    _apply_performance(compiled, diags)
    compiled.events.sort(key=lambda e: (e.time, e.part, e.pitch))
    return compiled


def _part_events(song: Song, pid: str, instances: list[Instance], diags: Diagnostics) -> list[Event]:
    events: list[Event] = []
    pending: dict[int, Event] = {}  # pitch -> event a tie will extend
    pending_where = ""

    def broken_tie(why: str) -> None:
        nonlocal pending
        names = " ".join(pitch_name(p) for p in sorted(pending))
        diags.error(pending_where, f"tie from {names} {why}")
        pending = {}

    for ins in instances:
        bars = ins.section.parts.get(pid)
        if bars is None:
            if pending:
                broken_tie(f"but '{pid}' does not play in {ins.name}")
            continue
        for bi, items in enumerate(bars):
            bar_start = ins.start_beat + bi * song.bar_beats
            for item in items:
                where = loc(ins.name, pid, f"bar {bi + 1}, beat {fmt_beats(item.onset + 1)}")
                if not item.pitches:
                    if pending:
                        broken_tie("is followed by a rest")
                    continue
                if pending and not set(pending) <= set(item.pitches):
                    broken_tie(f"but the next note is {' '.join(pitch_name(p) for p in item.pitches)}")

                level = item.level
                if item.arts.get("acc"):
                    level += ACCENT
                if item.arts.get("ghost"):
                    level *= GHOST
                src = {"section": ins.section.id, "instance": ins.index, "bar": bi + 1,
                       "beat": float(item.onset + 1), "global_bar": ins.global_bar + bi}

                new_pending: dict[int, Event] = {}
                for rank, p in enumerate(item.pitches):
                    if p in pending:
                        ev = pending[p]
                        ev.beats += item.dur
                    else:
                        ev = Event(pid, bar_start + item.onset, item.dur, p, item.lane, level,
                                   dict(item.arts), src, pos_in_bar=item.onset, chord_rank=rank)
                        events.append(ev)
                    if item.tie:
                        new_pending[p] = ev
                pending = new_pending
                if item.tie:
                    pending_where = where
    if pending:
        broken_tie("has no following note")
    return events


def _num(value, default: float, where: str, diags: Diagnostics) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    diags.error(where, f"expected a number, got {value!r}")
    return default


def _apply_performance(compiled: Compiled, diags: Diagnostics) -> None:
    song = compiled.song
    perf = song.performance if isinstance(song.performance, dict) else {}
    if not isinstance(song.performance, dict):
        diags.error("performance", "'performance' must be a mapping")
    for k in perf:
        if k not in PERF_KEYS:
            diags.warn("performance", f"unknown key '{k}'{did_you_mean(k, PERF_KEYS)} "
                                      f"(allowed: {', '.join(sorted(PERF_KEYS))})")

    seed = int(_num(perf.get("seed"), 0, "performance > seed", diags))
    rng = np.random.default_rng(seed)
    global_hum = perf.get("humanize") or {}
    global_swing = perf.get("swing")
    parts_cfg = perf.get("parts") or {}
    for pid, cfg in parts_cfg.items():
        if pid not in song.instruments:
            diags.error(f"performance > parts > {pid}", f"unknown part '{pid}'{did_you_mean(pid, song.instruments)}")
        elif isinstance(cfg, dict):
            for k in cfg:
                if k not in PART_PERF_KEYS:
                    diags.warn(f"performance > parts > {pid}", f"unknown key '{k}'{did_you_mean(k, PART_PERF_KEYS)}")

    edits = _load_edits(perf.get("edits") or [], song, diags)
    edit_hits = [0] * len(edits)
    active_sections = {ins.section.id for ins in compiled.instances}
    chord_jitter: dict[int, float] = {}

    for ev in compiled.events:
        inst = song.instruments[ev.part]
        cfg = parts_cfg.get(ev.part) or {}
        where = f"performance > parts > {ev.part}"
        lane_cfg = (cfg.get("lanes") or {}).get(ev.lane) or {} if ev.lane else {}

        velocity = ev.velocity + _num(cfg.get("velocity"), 0, where, diags) \
            + _num(lane_cfg.get("velocity"), 0, where, diags)
        offset_ms = _num(cfg.get("offset_ms"), 0, where, diags) + _num(lane_cfg.get("offset_ms"), 0, where, diags)
        strum = _num(cfg.get("strum_ms"), DEFAULT_STRUM_MS.get(inst.type, 0), where, diags)
        offset_ms += strum * ev.chord_rank
        length = 0.5 if ev.arts.get("st") else 1.0

        start = ev.beat + _swing_shift(ev.pos_in_bar, cfg.get("swing", global_swing), diags)

        for i, ed in enumerate(edits):
            if _edit_matches(ed, ev):
                edit_hits[i] += 1
                v = ed.get("velocity")
                if isinstance(v, str):
                    velocity += float(v)
                elif v is not None:
                    velocity = float(v)
                offset_ms += ed.get("offset_ms", 0)
                length *= ed.get("length", 1)

        hum = {**global_hum, **(cfg.get("humanize") or {})}
        # Always draw both numbers so changing one setting never reshuffles other notes.
        jitter_t, jitter_v = rng.standard_normal(2)
        # Notes of one chord share `src`; they move together so the strum order survives.
        jitter_t = chord_jitter.setdefault(id(ev.src), jitter_t)
        offset_ms += jitter_t * _num(hum.get("timing_ms"), 0, "performance > humanize", diags)
        velocity += jitter_v * _num(hum.get("velocity"), 0, "performance > humanize", diags)

        t0 = compiled.beat_to_sec(float(start))
        t1 = compiled.beat_to_sec(float(start + ev.beats * Fraction(length).limit_denominator(1000)))
        ev.time = max(0.0, t0 + offset_ms / 1000)
        ev.dur = max(0.005, t1 - t0)
        ev.velocity = float(np.clip(velocity, 0.05, 1.0))

    for ed, hits in zip(edits, edit_hits):
        if hits == 0 and ed["section"] in active_sections:
            diags.error(ed["_where"], "edit matches no note (did the score change?)")


def _swing_shift(pos: Fraction, swing, diags: Diagnostics) -> Fraction:
    if not swing:
        return Fraction(0)
    if not isinstance(swing, dict) or swing.get("grid") not in (8, 16):
        diags.error("performance > swing", "swing must look like { amount: 0.6, grid: 8 } (grid 8 or 16)")
        return Fraction(0)
    amount = Fraction(str(swing.get("amount", 0.5)))
    unit = Fraction(4, swing["grid"])
    steps = pos / unit
    if steps.denominator == 1 and steps.numerator % 2 == 1:
        return (2 * amount - 1) * unit
    return Fraction(0)


def _load_edits(raw, song: Song, diags: Diagnostics) -> list[dict]:
    if not isinstance(raw, list):
        diags.error("performance > edits", "'edits' must be a list")
        return []
    out = []
    for i, ed in enumerate(raw):
        where = f"performance > edits[{i}]"
        if not isinstance(ed, dict):
            diags.error(where, "edit must be a mapping")
            continue
        for k in ed:
            if k not in EDIT_KEYS:
                diags.warn(where, f"unknown key '{k}'{did_you_mean(k, EDIT_KEYS)}")
        if ed.get("part") not in song.instruments:
            diags.error(where, f"unknown part {ed.get('part')!r}{did_you_mean(ed.get('part'), song.instruments)}")
            continue
        if ed.get("section") not in song.sections:
            diags.error(where, f"unknown section {ed.get('section')!r}{did_you_mean(ed.get('section'), song.sections)}")
            continue
        if not isinstance(ed.get("bar"), int) or not isinstance(ed.get("beat"), (int, float)):
            diags.error(where, "edit needs integer 'bar' and numeric 'beat' (1 = downbeat)")
            continue
        e = {**ed, "_where": where}
        if "pitch" in ed:
            try:
                e["pitch"] = parse_pitch(str(ed["pitch"]))
            except ValueError as err:
                diags.error(where, str(err))
                continue
        v = ed.get("velocity")
        if isinstance(v, str):
            try:
                float(v)
            except ValueError:
                diags.error(where, f"velocity must be a number or a string like '+0.1', got {v!r}")
                continue
        out.append(e)
    return out


def _edit_matches(ed: dict, ev: Event) -> bool:
    s = ev.src
    return (ed["part"] == ev.part and ed["section"] == s["section"]
            and ed.get("instance", s["instance"]) == s["instance"]
            and ed["bar"] == s["bar"] and abs(ed["beat"] - s["beat"]) < 1e-6
            and ed.get("pitch", ev.pitch) == ev.pitch
            and ed.get("lane", ev.lane) == ev.lane)
