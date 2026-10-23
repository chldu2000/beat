"""Compile a Song into a flat, performed event list (spec section 11)."""

import zlib
from dataclasses import dataclass, field
from fractions import Fraction

import numpy as np

from .arrangement import check_arrangement
from .diagnostics import Diagnostics, did_you_mean, loc
from .notation import fmt_beats
from .pitch import parse_pitch, pitch_name
from .song import Section, Song
from .synth import rig

ACCENT = 0.12
GHOST = 0.35
DEFAULT_STRUM_MS = {"guitar": 8.0}
# Articulations that may start on a tied continuation; the event lists them in `arts.tied` as
# {"at": beats into the note, <art>: value}.
LATE_ARTS = ("vib", "bend", "release", "fall")
NO_TOUCH = {"organ"}  # keyboards whose loudness does not follow the key stroke: accents are ignored
# Markers in `notes` that switch a setting from that point: the part type they apply to, and what they switch.
SWITCH_OWNERS = {"leslie": "organ", "tone": "guitar", "pedal": "guitar"}
SWITCH_WHAT = {"leslie": "an organ's Leslie", "tone": "a guitar's amp tone", "pedal": "a guitar pedal"}
# How much louder the downbeat is played and how much softer the finest subdivisions (velocity, 0-1;
# scaled by metric_weight). Players lean on the beat and lighten the off-beats; the hi-hat's down/up
# stroke alternation is the strongest case. Crashes and the organ (no touch) skip it.
DEFAULT_ACCENTS = {"bass": 0.04, "guitar": 0.04, "piano": 0.05}
DRUM_ACCENTS = {"hh": 0.10, "ho": 0.05, "rd": 0.08, "rb": 0.06, "bd": 0.04, "sd": 0.03, "ss": 0.03,
                "t1": 0.03, "t2": 0.03, "t3": 0.03, "hp": 0.03}
# Timing drift (ms, standard deviation): slow, correlated pushing and dragging instead of per-note
# jitter. Off by default (DRIFT_BAND_MS); `humanize: { drift_ms: 8 }` turns it on. The band drifts
# together (a breathing tempo); each player also drifts against the band, by DRIFT_PART_MS scaled by
# the band's setting over DRIFT_REF_MS: least the drummer, who keeps time, and the bass, who locks to
# the kick.
DRIFT_BAND_MS = 0.0
DRIFT_REF_MS = 8.0
DRIFT_PART_MS = {"drums": 2.0, "bass": 3.0, "guitar": 4.0, "organ": 4.0, "piano": 4.0}
# Time constants of the drift's components, in beats (about 1, 4 and 16 bars of 4/4): summed, they
# approximate the 1/f fluctuation of human timing, which listeners prefer to white jitter.
DRIFT_TAUS = (4, 16, 64)
HUMANIZE_KEYS = {"timing_ms", "velocity", "drift_ms"}
# Timing with an intent (ms): drummers rush fills and land the next downbeat on time (off by default;
# `fill_rush_ms: 10` is a typical amount); in a section
# that builds (its dynamic ramps up) drums and bass lean further ahead until the next section.
# tempo_push: the louder sections are played up to this much faster than written (0.01 = 1%), as a
# band without a click does; the tempo rises over the bar before and settles over the bar after.
FEEL = {"fill_rush_ms": 0.0, "build_push_ms": 5.0, "tempo_push": 0.01}
PUSHING = {"drums", "bass"}
TOMS = {"t1", "t2", "t3"}
DRUMS = {"bd", "sd", "ss"} | TOMS  # fills are told apart on these, not on cymbals or the hi-hat
PERF_KEYS = {"seed", "humanize", "swing", "accents", "feel", "parts", "edits"}
PART_PERF_KEYS = {"humanize", "swing", "accents", "offset_ms", "velocity", "strum_ms", "lanes"}
LANE_PERF_KEYS = {"offset_ms", "velocity", "accents"}
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
    swell: tuple[Fraction, float] | None = None  # (beat, level) a swell under the note is heading for
    swell_to: tuple[float, float] | None = None  # the same, performed: (seconds, velocity)

    def to_dict(self) -> dict:
        return {
            "part": self.part, "time": round(self.time, 4), "dur": round(self.dur, 4),
            "beat": float(self.beat), "beats": float(self.beats), "pitch": self.pitch,
            "lane": self.lane, "velocity": round(self.velocity, 3), "arts": self.arts, "src": self.src,
        }


@dataclass
class Control:
    """A setting that a part holds from `time` on: the organ's Leslie speed, a guitar's `tone` or the
    `pedals` it has on (e.g. "od+boost", or "none")."""
    part: str
    time: float
    name: str
    value: str
    src: dict

    def to_dict(self) -> dict:
        return {"part": self.part, "time": round(self.time, 4), "name": self.name, "value": self.value,
                "src": self.src}


@dataclass
class Compiled:
    song: Song
    instances: list[Instance]
    events: list[Event]
    total_beats: Fraction
    duration_sec: float
    total_bars: int
    form: list[str] = field(default_factory=list)
    controls: list[Control] = field(default_factory=list)
    tempo: "TempoMap | None" = None

    def beat_to_sec(self, beat: float) -> float:
        return self.tempo.sec(beat)

    def sec_to_beat(self, sec: float) -> float:
        return self.tempo.beat(sec)

    def to_dict(self) -> dict:
        return {
            "meta": {"title": self.song.meta.get("title"), "duration_sec": round(self.duration_sec, 3),
                     "bars": self.total_bars, "form": self.form},
            "parts": {pid: {"type": i.type, **({"tone": i.tone} if i.tone else {})}
                      for pid, i in self.song.instruments.items()},
            "events": [e.to_dict() for e in self.events],
            **({"controls": [c.to_dict() for c in self.controls]} if self.controls else {}),
        }


class TempoMap:
    """The performed tempo along the song, in steps of `step` beats: each step's tempo moves linearly
    from `start[i]` to `end[i]` (BPM), so a written jump between sections stays a jump."""

    def __init__(self, start: np.ndarray, end: np.ndarray, step: float):
        self.start, self.end, self.step = start, end, step
        self.at = np.concatenate([[0.0], np.cumsum([self._span(i, step) for i in range(len(start))])])

    def _span(self, i: int, u: float) -> float:
        """Seconds for the first u beats of step i."""
        a, b = self.start[i], self.end[i]
        if abs(b - a) < 1e-9:
            return 60 * u / a
        return 60 * self.step / (b - a) * np.log1p((b - a) * u / (self.step * a))

    def sec(self, beat: float) -> float:
        i = min(max(int(beat // self.step), 0), len(self.start) - 1)
        return float(self.at[i] + self._span(i, beat - i * self.step))

    def beat(self, sec: float) -> float:
        i = min(max(int(np.searchsorted(self.at, sec, "right")) - 1, 0), len(self.start) - 1)
        a, b, r = self.start[i], self.end[i], sec - self.at[i]
        if abs(b - a) < 1e-9:
            return i * self.step + r * a / 60
        return i * self.step + self.step * a / (b - a) * np.expm1(r * (b - a) / (60 * self.step))

    def bpm(self, beat: float) -> float:
        i = min(max(int(beat // self.step), 0), len(self.start) - 1)
        return float(self.start[i] + (self.end[i] - self.start[i]) * (beat - i * self.step) / self.step)


def build_timeline(song: Song, form: list[str]) -> tuple[list[Instance], Fraction, TempoMap, int]:
    instances: list[Instance] = []
    beat, bar = Fraction(0), 1
    counts: dict[str, int] = {}
    for sid in form:
        section = song.sections[sid]
        counts[sid] = counts.get(sid, 0) + 1
        instances.append(Instance(section, counts[sid], beat, 0.0, bar))
        beat += section.bars * song.bar_beats
        bar += section.bars
    tempo = _tempo_map(song, instances, beat)
    for ins in instances:
        ins.start_sec = tempo.sec(float(ins.start_beat))
    return instances, beat, tempo, bar - 1


def _tempo_map(song: Song, instances: list[Instance], total: Fraction) -> TempoMap:
    step = Fraction(1, max(4, song.bar_beats.denominator))
    n = max(int(total / step), 1)
    starts, ends = np.zeros(n), np.zeros(n)
    for ins in instances:
        sec, length = ins.section, ins.section.bars * song.bar_beats
        first, count = int(ins.start_beat / step), int(length / step)
        k = np.arange(count + 1) / count  # step boundaries across the section, 0..1
        written = sec.tempo + ((sec.tempo_end or sec.tempo) - sec.tempo) * k
        starts[first:first + count], ends[first:first + count] = written[:-1], written[1:]
    push = _tempo_push(song, instances, np.arange(n + 1) * float(step))
    return TempoMap(starts * push[:-1], ends * push[1:], float(step))


def _tempo_push(song: Song, instances: list[Instance], x: np.ndarray) -> np.ndarray:
    """Tempo factors at beats `x`: louder sections faster by up to `feel.tempo_push`, reached over the
    bar before them and left over the bar after them."""
    feel = song.performance.get("feel") if isinstance(song.performance, dict) else None
    push = (feel or {}).get("tempo_push", FEEL["tempo_push"]) if isinstance(feel or {}, dict) else 0
    if not isinstance(push, (int, float)) or not push:
        return np.ones(len(x))

    def level(ins: Instance) -> float:
        drums = [d for p, d in ins.section.dynamics.items() if song.instruments[p].type == "drums"]
        return float(np.mean(drums or [ins.section.dynamic]))
    levels = np.array([level(ins) for ins in instances])
    span = levels.max() - levels.min()
    factors = 1 + push * ((levels - levels.min()) / span if span > 0 else 0 * levels)
    starts = np.array([float(ins.start_beat) for ins in instances])
    out = factors[np.clip(np.searchsorted(starts, x, "right") - 1, 0, None)]
    bar = float(song.bar_beats)
    for k in range(1, len(instances)):
        prev, new, at = factors[k - 1], factors[k], starts[k]
        lo = at - bar if new > prev else at
        window = (x >= lo) & (x < lo + bar)
        out[window] = prev + (new - prev) * (x[window] - lo) / bar
    return out


def compile_song(song: Song, diags: Diagnostics, form: list[str] | None = None) -> Compiled:
    """Compile the song. `form` overrides the song's form (e.g. to render only some sections)."""
    form = form if form is not None else song.form
    instances, total_beats, tempo, total_bars = build_timeline(song, form)
    events: list[Event] = []
    controls = [Control(pid, ins.start_sec, name, value, {"section": ins.section.id, "instance": ins.index})
                for ins in instances for pid, settings in ins.section.controls.items()
                for name, value in settings.items()]
    for pid in song.instruments:
        events.extend(_part_events(song, pid, instances, diags, controls))
    for c in controls:
        if "at" in c.src:
            c.time = tempo.sec(float(c.src.pop("at")))
    controls.sort(key=lambda c: (c.time, c.part))
    compiled = Compiled(song, instances, events, total_beats, tempo.sec(float(total_beats)), total_bars,
                        list(form), controls, tempo)
    _apply_performance(compiled, diags)
    compiled.events.sort(key=lambda e: (e.time, e.part, e.pitch))
    check_arrangement(compiled, diags)
    return compiled


def _part_events(song: Song, pid: str, instances: list[Instance], diags: Diagnostics,
                 controls: list[Control]) -> list[Event]:
    events: list[Event] = []
    touch = song.instruments[pid].type not in NO_TOUCH
    pending: dict[int, Event] = {}  # pitch -> event a tie will extend
    pending_where = ""

    def broken_tie(why: str) -> None:
        nonlocal pending
        names = " ".join(pitch_name(p) for p in sorted(pending))
        diags.error(pending_where, f"tie from {names} {why}")
        pending = {}

    itype = song.instruments[pid].type
    for ins in instances:
        bars = ins.section.parts.get(pid)
        if bars is None:
            if pending:
                broken_tie(f"but '{pid}' does not play in {ins.name}")
            continue
        pedals = set(rig.split(ins.section.controls.get(pid, {}).get("pedals", rig.NONE)))
        for bi, items in enumerate(bars):
            bar_start = ins.start_beat + bi * song.bar_beats
            for item in items:
                where = loc(ins.name, pid, f"bar {bi + 1}, beat {fmt_beats(item.onset + 1)}")
                switch = next((k for k in SWITCH_OWNERS if k in item.arts), None)
                if switch:
                    value = item.arts[switch]
                    if itype != SWITCH_OWNERS[switch]:
                        diags.error(where, f"@{value} switches {SWITCH_WHAT[switch]}; '{pid}' is {itype}")
                        continue
                    name = switch
                    if switch == "pedal":
                        pedal, on = value[1:], value[0] == "+"
                        if (pedal in pedals) == on:
                            diags.warn(where, f"@{value} has no effect: {pedal} is already {'on' if on else 'off'} "
                                              f"here (each section starts with its own or the instrument's "
                                              f"pedals); drop it")
                            continue
                        pedals = pedals | {pedal} if on else pedals - {pedal}
                        name, value = "pedals", rig.fmt(pedals)
                    controls.append(Control(pid, 0.0, name, value,
                                            {"section": ins.section.id, "instance": ins.index, "bar": bi + 1,
                                             "beat": float(item.onset + 1), "at": bar_start + item.onset}))
                    continue
                if not item.pitches:
                    if pending:
                        broken_tie("is followed by a rest")
                    continue
                if pending and not set(pending) <= set(item.pitches):
                    broken_tie(f"but the next note is {' '.join(pitch_name(p) for p in item.pitches)}")

                level = item.level
                if item.arts.get("acc") and touch:
                    level += ACCENT
                if item.arts.get("ghost"):
                    level *= GHOST
                src = {"section": ins.section.id, "instance": ins.index, "bar": bi + 1,
                       "beat": float(item.onset + 1), "global_bar": ins.global_bar + bi}

                new_pending: dict[int, Event] = {}
                late = {a: v for a, v in item.arts.items() if a in LATE_ARTS}
                if pending:
                    ignored = sorted(a for a in item.arts if a not in LATE_ARTS)
                    if ignored:
                        diags.warn(where, f"{', '.join('!' + a for a in ignored)} on a tied note has no effect; "
                                          f"put it on the first note of the tie")
                    first = next(iter(pending.values()))
                    bent = "bend" in first.arts or any("bend" in t for t in first.arts.get("tied", []))
                    if "release" in late and not bent:
                        diags.warn(where, "!release has no bend to release: bend an earlier note of the tie, "
                                          "e.g. 'A4:4!bend=2~ A4:4!release'")
                elif item.arts.get("release"):
                    diags.error(where, "!release only applies to a tied note: tie it from the bent note, "
                                       "e.g. 'A4:4!bend=2~ A4:4!release'")
                for rank, p in enumerate(item.pitches):
                    if p in pending:
                        ev = pending[p]
                        if late:
                            ev.arts.setdefault("tied", []).append({"at": float(ev.beats), **late})
                        ev.beats += item.dur
                    else:
                        ev = Event(pid, bar_start + item.onset, item.dur, p, item.lane, level,
                                   dict(item.arts), src, pos_in_bar=item.onset, chord_rank=rank)
                        if item.swell:
                            # Accents and ghosts shift the whole swell, like the ramp shifts the notes.
                            ev.swell = (ev.beat + item.swell[0], item.swell[1] + level - item.level)
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
    global_hum = perf.get("humanize") or {}
    for where, hum in [("performance > humanize", global_hum)] + [
            (f"performance > parts > {pid} > humanize", (c or {}).get("humanize") or {})
            for pid, c in (perf.get("parts") or {}).items() if isinstance(c, dict)]:
        for k in hum if isinstance(hum, dict) else ():
            if k not in HUMANIZE_KEYS:
                diags.warn(where, f"unknown key '{k}'{did_you_mean(k, HUMANIZE_KEYS)} "
                                  f"(allowed: {', '.join(sorted(HUMANIZE_KEYS))})")
    global_swing = perf.get("swing")
    parts_cfg = perf.get("parts") or {}
    for pid, cfg in parts_cfg.items():
        if pid not in song.instruments:
            diags.error(f"performance > parts > {pid}", f"unknown part '{pid}'{did_you_mean(pid, song.instruments)}")
        elif isinstance(cfg, dict):
            for k in cfg:
                if k not in PART_PERF_KEYS:
                    diags.warn(f"performance > parts > {pid}", f"unknown key '{k}'{did_you_mean(k, PART_PERF_KEYS)}")
            for lane, lane_cfg in (cfg.get("lanes") or {}).items():
                for k in lane_cfg if isinstance(lane_cfg, dict) else ():
                    if k not in LANE_PERF_KEYS:
                        diags.warn(f"performance > parts > {pid} > lanes > {lane}",
                                   f"unknown key '{k}'{did_you_mean(k, LANE_PERF_KEYS)}")

    for pid, cfg in parts_cfg.items():
        if pid in song.instruments and song.instruments[pid].type in NO_TOUCH and (cfg or {}).get("accents"):
            diags.warn(f"performance > parts > {pid} > accents",
                       f"{song.instruments[pid].type} has no touch, so accents have no effect")

    feel = perf.get("feel") or {}
    if not isinstance(feel, dict):
        diags.error("performance > feel", "feel must look like { fill_rush_ms: 10, build_push_ms: 5 }")
        feel = {}
    for k in feel:
        if k not in FEEL:
            diags.warn("performance > feel", f"unknown key '{k}'{did_you_mean(k, FEEL)} (allowed: {', '.join(FEEL)})")
    _num(feel.get("tempo_push"), FEEL["tempo_push"], "performance > feel > tempo_push", diags)
    rush = _num(feel.get("fill_rush_ms"), FEEL["fill_rush_ms"], "performance > feel > fill_rush_ms", diags)
    push = _num(feel.get("build_push_ms"), FEEL["build_push_ms"], "performance > feel > build_push_ms", diags)
    intent = _intent_offsets(compiled, rush, push)

    edits = _load_edits(perf.get("edits") or [], song, diags)
    edit_hits = [0] * len(edits)
    active_sections = {ins.section.id for ins in compiled.instances}
    chord_jitter: dict[int, float] = {}
    # Each part draws from its own stream, so adding a part or a note leaves the others' jitter alone.
    rngs = {pid: _rng(seed, f"jitter:{pid}") for pid in song.instruments}
    n_beats = int(compiled.total_beats) + 2
    band_ms = _num(global_hum.get("drift_ms"), DRIFT_BAND_MS, "performance > humanize > drift_ms", diags)
    band = drift_curve(_rng(seed, "drift:band"), n_beats) * band_ms
    drifts = {}
    for pid, inst in song.instruments.items():
        own = ((parts_cfg.get(pid) or {}).get("humanize") or {}).get("drift_ms")
        # The band's setting scales every player's default too: one knob for a looser or tighter band.
        default = DRIFT_PART_MS.get(inst.type, 0) * band_ms / DRIFT_REF_MS
        own_ms = _num(own, default, f"performance > parts > {pid} > humanize", diags)
        drifts[pid] = band + drift_curve(_rng(seed, f"drift:{pid}"), n_beats) * own_ms

    for ev in compiled.events:
        inst = song.instruments[ev.part]
        cfg = parts_cfg.get(ev.part) or {}
        where = f"performance > parts > {ev.part}"
        lane_cfg = (cfg.get("lanes") or {}).get(ev.lane) or {} if ev.lane else {}

        score_velocity = ev.velocity
        velocity = ev.velocity + _num(cfg.get("velocity"), 0, where, diags) \
            + _num(lane_cfg.get("velocity"), 0, where, diags)
        if inst.type not in NO_TOUCH:
            depth = next((c["accents"] for c in (lane_cfg, cfg, perf) if c.get("accents") is not None),
                         DRUM_ACCENTS.get(ev.lane, 0) if ev.lane else DEFAULT_ACCENTS.get(inst.type, 0))
            velocity += _num(depth, 0, f"{where} > accents", diags) * metric_weight(ev.pos_in_bar, song.time)
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
        jitter_t, jitter_v = rngs[ev.part].standard_normal(2)
        # Notes of one chord share `src`; they move together so the strum order survives.
        jitter_t = chord_jitter.setdefault(id(ev.src), jitter_t)
        offset_ms += jitter_t * _num(hum.get("timing_ms"), 0, "performance > humanize", diags)
        velocity += jitter_v * _num(hum.get("velocity"), 0, "performance > humanize", diags)
        offset_ms += float(np.interp(float(ev.beat), np.arange(n_beats), drifts[ev.part]))
        offset_ms += intent.get(id(ev), 0.0)

        t0 = compiled.beat_to_sec(float(start))
        t1 = compiled.beat_to_sec(float(start + ev.beats * Fraction(length).limit_denominator(1000)))
        ev.time = max(0.0, t0 + float(offset_ms) / 1000)
        ev.dur = max(0.005, t1 - t0)
        ev.velocity = float(np.clip(velocity, 0.05, 1.0))
        if ev.swell:
            ev.swell_to = (compiled.beat_to_sec(float(ev.swell[0])) + float(offset_ms) / 1000,
                           float(np.clip(ev.swell[1] + velocity - score_velocity, 0.05, 1.0)))

    for ed, hits in zip(edits, edit_hits):
        if hits == 0 and ed["section"] in active_sections:
            diags.error(ed["_where"], "edit matches no note (did the score change?)")


def find_fills(compiled: Compiled, part: str) -> dict[tuple[str, int, int], Fraction]:
    """Drum fills of a part: (section, instance, bar) -> the beat in the bar where the fill starts.

    A fill is a phrase-ending bar (every 4th, or the section's last) that departs from the section's
    usual bar on the drums (cymbals and hi-hat aside), from its first differing beat on, into toms or
    at least 3 snare hits (ghosts aside)."""
    bars: dict[tuple[str, int, int], dict[Fraction, set]] = {}
    snares: dict[tuple[str, int, int], list[Fraction]] = {}
    for ev in compiled.events:
        if ev.part != part or ev.lane not in DRUMS:
            continue
        key = (ev.src["section"], ev.src["instance"], ev.src["bar"])
        bars.setdefault(key, {}).setdefault(ev.pos_in_bar, set()).add(ev.lane)
        if ev.lane == "sd" and not ev.arts.get("ghost"):
            snares.setdefault(key, []).append(ev.pos_in_bar)
    fills = {}
    for ins in compiled.instances:
        n = ins.section.bars
        own = [bars.get((ins.section.id, ins.index, b), {}) for b in range(1, n + 1)]
        usual = max(own, key=own.count)
        for b, hits in enumerate(own, 1):
            if hits == usual or not (b == n or b % 4 == 0):
                continue
            start = min(p for p in hits.keys() | usual.keys() if hits.get(p) != usual.get(p))
            later = {lane for p, lanes in hits.items() if p >= start for lane in lanes}
            key = (ins.section.id, ins.index, b)
            if later & TOMS or sum(p >= start for p in snares.get(key, [])) >= 3:
                fills[key] = start
    return fills


def _intent_offsets(compiled: Compiled, rush_ms: float, push_ms: float) -> dict[int, float]:
    """Offsets (ms, negative is early) by id(event): fills rushed toward the barline, builds pushed."""
    song = compiled.song
    out: dict[int, float] = {}
    instances = {(ins.section.id, ins.index): ins for ins in compiled.instances}
    fills = {pid: find_fills(compiled, pid) for pid, inst in song.instruments.items()
             if inst.type == "drums" and rush_ms}
    for ev in compiled.events:
        inst_type = song.instruments[ev.part].type
        ins = instances[(ev.src["section"], ev.src["instance"])]
        ms = 0.0
        start = fills.get(ev.part, {}).get((ins.section.id, ins.index, ev.src["bar"]))
        if start is not None and ev.pos_in_bar >= start:
            ms -= rush_ms * float((ev.pos_in_bar - start) / (song.bar_beats - start))
        lo, hi = ins.section.dynamics.get(ev.part, (0, 0))
        if push_ms and inst_type in PUSHING and hi > lo:
            ms -= push_ms * float((ev.beat - ins.start_beat) / (ins.section.bars * song.bar_beats))
        if ms:
            out[id(ev)] = ms
    return out


def _rng(seed: int, name: str) -> np.random.Generator:
    return np.random.default_rng([seed, zlib.crc32(name.encode())])


def drift_curve(rng: np.random.Generator, n_beats: int) -> np.ndarray:
    """Unit-variance drift sampled once per beat: a sum of slow random walks that pull back to zero
    (one per time constant in DRIFT_TAUS), so it wanders like human timing but never runs away."""
    out = np.zeros(n_beats)
    for tau in DRIFT_TAUS:
        a = np.exp(-1 / tau)
        noise = rng.standard_normal(n_beats) * np.sqrt(1 - a * a)
        x = np.empty(n_beats)
        x[0] = rng.standard_normal()  # start anywhere in the walk's usual range
        for i in range(1, n_beats):
            x[i] = a * x[i - 1] + noise[i]
        out += x
    return out / np.sqrt(len(DRIFT_TAUS))


def metric_weight(pos: Fraction, time: tuple[int, int]) -> float:
    """How strong a position in the bar is: 1 on the downbeat, 0.6 on the middle beat of a four-beat
    bar, 0.4 on other beats, -0.4 on halves or thirds of a beat, -1 on anything finer."""
    if pos == 0:
        return 1.0
    num, den = time
    compound = den == 8 and num % 3 == 0 and num > 3  # 6/8, 9/8, 12/8: the beat is a dotted quarter
    beat = Fraction(12, den) if compound else Fraction(4, den)
    in_beats = pos / beat
    if in_beats.denominator == 1:
        beats_in_bar = num // 3 if compound else num
        return 0.6 if beats_in_bar == 4 and in_beats == 2 else 0.4
    if (in_beats * 2).denominator == 1 or (in_beats * 3).denominator == 1:
        return -0.4
    return -1.0


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
