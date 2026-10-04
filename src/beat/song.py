"""Load a .beat.yaml file into a resolved Song: every section's parts expanded into bars of Items."""

import re
from dataclasses import dataclass, field
from fractions import Fraction

import yaml

from .diagnostics import Diagnostics, did_you_mean, loc
from .notation import DYNAMICS, Item, parse_grid, parse_hits, parse_notes
from .pitch import parse_chord, parse_pitch

SPEC_VERSION = "0.1"

TOP_KEYS = {"beat", "meta", "instruments", "patterns", "sections", "form", "performance", "mix"}
META_KEYS = {"title", "tempo", "time", "key", "style"}
INSTRUMENT_KEYS = {"type", "tuning", "frets", "tone", "model"}
PATTERN_KEYS = {"type", "bars", "notes", "grid", "hits", "steps"}
SECTION_KEYS = {"bars", "tempo", "dynamic", "chords", "parts", "extends"}
PART_KEYS = {"notes", "grid", "hits", "use", "steps", "transpose", "replace", "dynamic"}

INSTRUMENT_TYPES = {"drums", "bass", "guitar", "organ", "piano"}
DEFAULT_TUNING = {"guitar": ["E2", "A2", "D3", "G3", "B3", "E4"], "bass": ["E1", "A1", "D2", "G2"]}
DEFAULT_FRETS = {"guitar": 22, "bass": 21}
FIXED_RANGE = {"organ": (36, 96), "piano": (21, 108)}
TONES = {"clean", "crunch", "lead"}

_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass
class Instrument:
    id: str
    type: str
    tuning: tuple[int, ...] = ()
    frets: int = 0
    tone: str | None = None
    model: dict = field(default_factory=dict)

    @property
    def pitched(self) -> bool:
        return self.type != "drums"

    @property
    def range(self) -> tuple[int, int] | None:
        if self.type in FIXED_RANGE:
            return FIXED_RANGE[self.type]
        if self.tuning:
            return min(self.tuning), max(self.tuning) + self.frets
        return None


@dataclass
class ChordSpan:
    onset: Fraction  # beats from the start of the bar
    dur: Fraction
    symbol: str
    pcs: frozenset[int] | None  # None for N.C.


@dataclass
class Section:
    id: str
    bars: int
    tempo: float
    dynamic: str
    chords: list[list[ChordSpan]] | None
    parts: dict[str, list[list[Item]]]
    extends: str | None = None  # the section this one was derived from


@dataclass
class Song:
    meta: dict
    tempo: float
    time: tuple[int, int]
    bar_beats: Fraction
    instruments: dict[str, Instrument]
    sections: dict[str, Section]
    form: list[str]
    performance: dict
    mix: dict

    @property
    def default_steps(self) -> int:
        return int(self.bar_beats * 4)


def _yaml_error(e: yaml.YAMLError, text: str) -> str:
    """Name the line and, for the common unquoted-notation case, say exactly what to quote."""
    mark = getattr(e, "problem_mark", None) or getattr(e, "context_mark", None)
    lines = text.splitlines()
    msg = f"YAML syntax error: {getattr(e, 'problem', None) or e}"
    if mark is None:
        return msg
    msg = f"YAML syntax error at line {mark.line + 1}: {getattr(e, 'problem', None) or e}"
    # The offending value is usually on the reported line or the one before it.
    for n in (mark.line, mark.line - 1):
        if 0 <= n < len(lines):
            m = re.match(r"^\s*(notes|grid|chords)\s*:\s*([\[(%@!].*)$", lines[n])
            if m:
                return (f"{msg}. Line {n + 1}: the {m[1]} value starts with '{m[2][0]}', which YAML treats "
                        f"as syntax; wrap it in quotes: {m[1]}: \"{m[2].strip()[:40]}...\"")
    return f"{msg}. Line {mark.line + 1}: {lines[mark.line].strip()[:80] if mark.line < len(lines) else ''}\n" \
           f"Hint: quote notes/grid/chords strings that start with [ ( % @ ! or contain ': '"


def _warn_unknown(raw: dict, allowed: set[str], where: str, diags: Diagnostics) -> None:
    for k in raw:
        if k not in allowed:
            diags.warn(where, f"unknown key '{k}'{did_you_mean(k, allowed)} (allowed: {', '.join(sorted(allowed))})")


def load_song(text: str, diags: Diagnostics) -> Song | None:
    """Parse and resolve a song. Returns None only when the file is too broken to continue."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        diags.error("", _yaml_error(e, text))
        return None
    if not isinstance(data, dict):
        diags.error("", "the file must be a YAML mapping")
        return None

    _warn_unknown(data, TOP_KEYS, "top level", diags)
    if str(data.get("beat")) != SPEC_VERSION:
        diags.error("beat", f"spec version must be {SPEC_VERSION}, got {data.get('beat')!r}")

    meta = data.get("meta")
    if not isinstance(meta, dict):
        diags.error("meta", "missing 'meta' mapping with at least tempo and time")
        return None
    _warn_unknown(meta, META_KEYS, "meta", diags)
    tempo = meta.get("tempo")
    if not isinstance(tempo, (int, float)) or tempo <= 0:
        diags.error("meta > tempo", f"tempo must be a positive number (BPM), got {tempo!r}")
        return None
    m = re.match(r"^(\d+)/(\d+)$", str(meta.get("time", "")))
    if not m or int(m[2]) not in (1, 2, 4, 8, 16) or int(m[1]) <= 0:
        diags.error("meta > time", f"time signature must look like 4/4, got {meta.get('time')!r}")
        return None
    time = (int(m[1]), int(m[2]))
    bar_beats = Fraction(time[0] * 4, time[1])

    instruments = _load_instruments(data.get("instruments"), diags)
    if not instruments:
        return None

    song = Song(meta=meta, tempo=float(tempo), time=time, bar_beats=bar_beats,
                instruments=instruments, sections={}, form=[],
                performance=data.get("performance") or {}, mix=data.get("mix") or {})

    patterns = data.get("patterns") or {}
    if not isinstance(patterns, dict):
        diags.error("patterns", "'patterns' must be a mapping of pattern id to pattern")
        patterns = {}
    for pid, pat in patterns.items():
        if not isinstance(pat, dict):
            diags.error(f"pattern {pid}", "pattern must be a mapping")
        else:
            _warn_unknown(pat, PATTERN_KEYS, f"pattern {pid}", diags)

    raw_sections = _resolve_extends(data.get("sections"), diags)
    for sid, raw in raw_sections.items():
        section = _load_section(sid, raw, song, patterns, diags)
        if section:
            song.sections[sid] = section
    if not song.sections:
        diags.error("sections", "the song has no usable sections")
        return None

    form = data.get("form")
    if not isinstance(form, list) or not form:
        diags.error("form", "'form' must be a non-empty list of section ids")
        return None
    for i, sid in enumerate(form):
        if sid not in raw_sections:
            diags.error(f"form[{i}]", f"unknown section '{sid}'{did_you_mean(sid, raw_sections)}")
    song.form = [sid for sid in form if sid in song.sections]
    if not song.form:
        return None

    from .checks import check_section  # local import: checks depends on Song types
    for section in song.sections.values():
        check_section(song, section, diags)
    return song


def _load_instruments(raw, diags: Diagnostics) -> dict[str, Instrument]:
    if not isinstance(raw, dict) or not raw:
        diags.error("instruments", "'instruments' must map part ids to instruments, e.g. gt1: { type: guitar }")
        return {}
    out: dict[str, Instrument] = {}
    for pid, spec in raw.items():
        where = f"instruments > {pid}"
        if not isinstance(pid, str) or not _ID_RE.match(pid):
            diags.error(where, "part id must start with a lowercase letter and use only a-z, 0-9, _")
            continue
        if not isinstance(spec, dict) or spec.get("type") not in INSTRUMENT_TYPES:
            got = spec.get("type") if isinstance(spec, dict) else None
            diags.error(where, f"instrument needs a type{did_you_mean(got, INSTRUMENT_TYPES) if got else ''}: "
                               f"{', '.join(sorted(INSTRUMENT_TYPES))}")
            continue
        _warn_unknown(spec, INSTRUMENT_KEYS, where, diags)
        itype = spec["type"]
        inst = Instrument(id=pid, type=itype, model=spec.get("model") or {})
        if itype in DEFAULT_TUNING:
            try:
                inst.tuning = tuple(parse_pitch(str(n)) for n in spec.get("tuning", DEFAULT_TUNING[itype]))
            except ValueError as e:
                diags.error(f"{where} > tuning", str(e))
                inst.tuning = tuple(parse_pitch(n) for n in DEFAULT_TUNING[itype])
            frets = spec.get("frets", DEFAULT_FRETS[itype])
            if not isinstance(frets, int) or not 12 <= frets <= 27:
                diags.error(f"{where} > frets", f"frets must be an integer between 12 and 27, got {frets!r}")
                frets = DEFAULT_FRETS[itype]
            inst.frets = frets
        if itype == "guitar":
            inst.tone = spec.get("tone", "crunch")
            if inst.tone not in TONES:
                diags.error(f"{where} > tone", f"tone must be one of {', '.join(sorted(TONES))}"
                                               f"{did_you_mean(inst.tone, TONES)}")
                inst.tone = "crunch"
        out[pid] = inst
    return out


def _resolve_extends(raw, diags: Diagnostics) -> dict[str, dict]:
    if not isinstance(raw, dict) or not raw:
        diags.error("sections", "'sections' must map section ids to sections")
        return {}
    out: dict[str, dict] = {}
    for sid, sec in raw.items():
        if not isinstance(sec, dict):
            diags.error(f"section {sid}", "section must be a mapping")
            continue
        parent_id = sec.get("extends")
        if parent_id is None:
            out[sid] = sec
            continue
        parent = raw.get(parent_id)
        if not isinstance(parent, dict):
            diags.error(f"section {sid}", f"extends unknown section '{parent_id}'{did_you_mean(parent_id, raw)}")
            continue
        if "extends" in parent:
            diags.error(f"section {sid}", f"'{parent_id}' itself uses extends; only one level is supported")
            continue
        merged = {**parent, **sec}
        merged["parts"] = {**(parent.get("parts") or {}), **(sec.get("parts") or {})}
        out[sid] = merged
    return out


def _load_section(sid: str, raw: dict, song: Song, patterns: dict, diags: Diagnostics) -> Section | None:
    where = f"section {sid}"
    _warn_unknown(raw, SECTION_KEYS, where, diags)
    bars = raw.get("bars")
    if not isinstance(bars, int) or bars <= 0:
        diags.error(where, f"'bars' must be a positive integer, got {bars!r}")
        return None
    tempo = raw.get("tempo", song.tempo)
    if not isinstance(tempo, (int, float)) or tempo <= 0:
        diags.error(f"{where} > tempo", f"tempo must be a positive number, got {tempo!r}")
        tempo = song.tempo
    dynamic = raw.get("dynamic", "mf")
    if dynamic not in DYNAMICS:
        diags.error(f"{where} > dynamic", f"unknown dynamic '{dynamic}'{did_you_mean(dynamic, DYNAMICS)} "
                                          f"(use {', '.join(DYNAMICS)})")
        dynamic = "mf"

    section = Section(id=sid, bars=bars, tempo=float(tempo), dynamic=dynamic, chords=None, parts={},
                      extends=raw.get("extends"))
    if "chords" in raw:
        section.chords = _parse_chords(raw["chords"], bars, song.bar_beats, f"{sid} > chords", diags)

    parts = raw.get("parts") or {}
    if not isinstance(parts, dict):
        diags.error(f"{sid} > parts", "'parts' must map part ids to content")
        parts = {}
    for pid, spec in parts.items():
        if pid not in song.instruments:
            diags.error(f"{sid} > {pid}", f"unknown part '{pid}'{did_you_mean(pid, song.instruments)} "
                                          f"(declare it under instruments)")
            continue
        section.parts[pid] = _load_part(spec, song.instruments[pid], section, song, patterns, diags)
    return section


def _parse_chords(raw, bars: int, bar_beats: Fraction, where: str,
                  diags: Diagnostics) -> list[list[ChordSpan]] | None:
    if not isinstance(raw, str):
        diags.error(where, "chords must be a string like 'Em | C | G D | B7'")
        return None
    bar_texts = raw.split("|")
    if len(bar_texts) != bars:
        diags.error(where, f"{len(bar_texts)} bars of chords, expected {bars}")
        return None
    out: list[list[ChordSpan]] = []
    for bi, bt in enumerate(bar_texts):
        symbols = bt.split()
        if not symbols:
            diags.error(loc(where, f"bar {bi + 1}"), "empty bar (use N.C. for no chord)")
            out.append([])
            continue
        span = bar_beats / len(symbols)
        spans = []
        for i, sym in enumerate(symbols):
            try:
                spans.append(ChordSpan(i * span, span, sym, parse_chord(sym)))
            except ValueError as e:
                diags.error(loc(where, f"bar {bi + 1}"), str(e))
        out.append(spans)
    return out


def _parse_bars(spec: dict, inst: Instrument, n_bars: int, level: float, song: Song,
                where: str, diags: Diagnostics) -> list[list[Item]]:
    """Parse one `notes`, `grid` or `hits` block that must span exactly n_bars."""
    empty: list[list[Item]] = [[] for _ in range(n_bars)]
    if inst.pitched:
        if "grid" in spec or "hits" in spec:
            diags.error(where, f"'{inst.type}' is a pitched instrument; use 'notes', not 'grid' or 'hits'")
            return empty
        text = spec.get("notes")
        if not isinstance(text, str):
            hint = " (YAML read it as a list/number; wrap the notes in quotes)" if text is not None else ""
            diags.error(where, f"'notes' must be a string{hint}")
            return empty
        bars, problems = parse_notes(text, song.bar_beats, level)
        if len(bars) != n_bars:
            diags.error(where, f"{len(bars)} bars written, expected {n_bars}")
    else:
        if "notes" in spec:
            diags.error(where, "drums use 'grid' or 'hits', not 'notes'")
            return empty
        if ("grid" in spec) == ("hits" in spec):
            diags.error(where, "drums need exactly one of 'grid' or 'hits'")
            return empty
        key = "hits" if "hits" in spec else "grid"
        text = spec[key]
        if not isinstance(text, str):
            diags.error(where, f"'{key}' must be a string")
            return empty
        if key == "hits":
            bars, problems = parse_hits(text, song.bar_beats, level, n_bars)
        else:
            steps = spec.get("steps", song.default_steps)
            if not isinstance(steps, int) or steps <= 0:
                diags.error(where, f"'steps' must be a positive integer, got {steps!r}")
                return empty
            bars, problems = parse_grid(text, song.bar_beats, steps, level, n_bars)

    for bi, msg in problems:
        diags.error(loc(where, f"bar {bi + 1}" if bi is not None else None), msg)
    return (bars + empty)[:n_bars]


def _load_part(spec, inst: Instrument, section: Section, song: Song, patterns: dict,
               diags: Diagnostics) -> list[list[Item]]:
    where = f"{section.id} > {inst.id}"
    empty: list[list[Item]] = [[] for _ in range(section.bars)]
    if not isinstance(spec, dict):
        diags.error(where, "part must be a mapping with one of notes / grid / hits / use")
        return empty
    _warn_unknown(spec, PART_KEYS, where, diags)

    dynamic = spec.get("dynamic", section.dynamic)
    if dynamic not in DYNAMICS:
        diags.error(f"{where} > dynamic", f"unknown dynamic '{dynamic}'{did_you_mean(dynamic, DYNAMICS)}")
        dynamic = section.dynamic
    level = DYNAMICS[dynamic]

    sources = [k for k in ("notes", "grid", "hits", "use") if k in spec]
    if len(sources) != 1:
        diags.error(where, f"part needs exactly one of notes / grid / hits / use, got {sources or 'none'}")
        return empty

    if "use" in spec:
        bars = _pattern_bars(spec["use"], inst, section.bars, level, song, patterns, where, diags)
    else:
        bars = _parse_bars(spec, inst, section.bars, level, song, where, diags)

    transpose = spec.get("transpose", 0)
    if transpose:
        if not inst.pitched or not isinstance(transpose, int):
            diags.error(f"{where} > transpose", "transpose must be an integer and only applies to pitched parts")
        else:
            bars = [[it.transposed(transpose) for it in bar] for bar in bars]

    replace = spec.get("replace") or {}
    if not isinstance(replace, dict):
        diags.error(f"{where} > replace", "'replace' must map bar numbers (e.g. 8 or '5-6') to notes/grid")
        replace = {}
    for key, rspec in replace.items():
        m = re.match(r"^(\d+)(?:-(\d+))?$", str(key))
        first, last = (int(m[1]), int(m[2] or m[1])) if m else (0, 0)
        if not m or not 1 <= first <= last <= section.bars:
            diags.error(f"{where} > replace", f"invalid bar range '{key}' (section has {section.bars} bars)")
            continue
        if not isinstance(rspec, dict):
            diags.error(f"{where} > replace {key}", "replacement must be a mapping with notes, grid, hits or use")
            continue
        rwhere = f"{where} > replace {key}"
        n = last - first + 1
        if "use" in rspec:
            new = _pattern_bars(rspec["use"], inst, n, level, song, patterns, rwhere, diags)
        else:
            new = _parse_bars(rspec, inst, n, level, song, rwhere, diags)
        bars[first - 1:last] = new
    return bars


def _pattern_bars(name, inst: Instrument, n_bars: int, level: float, song: Song, patterns: dict,
                  where: str, diags: Diagnostics) -> list[list[Item]]:
    """Expand a pattern to n_bars, looping it if it is shorter."""
    empty: list[list[Item]] = [[] for _ in range(n_bars)]
    pat = patterns.get(name)
    if not isinstance(pat, dict):
        diags.error(where, f"unknown pattern '{name}'{did_you_mean(name, patterns)}")
        return empty
    ptype = pat.get("type", "drums" if "grid" in pat or "hits" in pat else "pitched")
    if ptype not in ("drums", "pitched") or (ptype == "drums") != (inst.type == "drums"):
        diags.error(where, f"pattern '{name}' is type '{ptype}' but '{inst.id}' is {inst.type}")
        return empty
    pbars = pat.get("bars")
    if not isinstance(pbars, int) or pbars <= 0:
        diags.error(f"pattern {name}", f"'bars' must be a positive integer, got {pbars!r}")
        return empty
    pat_bars = _parse_bars(pat, inst, pbars, level, song, f"{where} (pattern {name})", diags)
    if n_bars % pbars:
        diags.warn(where, f"pattern '{name}' ({pbars} bars) does not divide {n_bars} bar(s); "
                          f"the last repeat is cut short")
    return [pat_bars[i % pbars] for i in range(n_bars)]
