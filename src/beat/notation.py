"""Parsers for the text notations: `notes` (pitched parts), `grid` and `hits` (drums).

Each returns a list of bars, each a list of Items with onsets relative to the bar,
plus a list of (bar_index | None, message) problems for the caller to locate.
"""

import re
from dataclasses import dataclass, field
from fractions import Fraction

from .diagnostics import did_you_mean
from .pitch import parse_pitch

DYNAMICS = {
    "ppp": 0.15, "pp": 0.25, "p": 0.38, "mp": 0.50,
    "mf": 0.63, "f": 0.78, "ff": 0.90, "fff": 1.0,
}

# Articulations that only make sense on fretted string instruments.
STRING_ARTS = {"pm", "x", "h", "p", "sl", "bend", "vib", "harm"}
ARTS = STRING_ARTS | {"st", "acc"}
VALUED_ARTS = {"bend"}

# lane -> (GM drum note, limb)
LANES = {
    "bd": (36, "foot"), "sd": (38, "hand"), "ss": (37, "hand"),
    "hh": (42, "hand"), "ho": (46, "hand"), "hp": (44, "foot"),
    "t1": (48, "hand"), "t2": (45, "hand"), "t3": (41, "hand"),
    "cr": (49, "hand"), "cr2": (57, "hand"), "rd": (51, "hand"),
    "rb": (53, "hand"), "ch": (52, "hand"),
}
GRID_HITS = {"x": {}, "X": {"acc": True}, "g": {"ghost": True}, "f": {"flam": True}}

Problems = list[tuple[int | None, str]]


@dataclass
class Item:
    onset: Fraction  # beats from the start of the bar
    dur: Fraction  # beats
    pitches: tuple[int, ...]  # empty for a rest; one GM note for a drum hit
    level: float  # dynamic level 0-1 before accents
    tie: bool = False
    arts: dict = field(default_factory=dict)
    lane: str | None = None  # drum lane, None for pitched parts

    def transposed(self, semitones: int) -> "Item":
        return Item(self.onset, self.dur, tuple(p + semitones for p in self.pitches),
                    self.level, self.tie, self.arts, self.lane)


def fmt_beats(x: Fraction) -> str:
    """Exact beats: a decimal when it terminates (2.5), else a fraction (4/3) that `:b` accepts."""
    if x.denominator & (x.denominator - 1) == 0:
        return f"{float(x):g}"
    return f"{x.numerator}/{x.denominator}"


def inexact_decimal(text: str, value: Fraction) -> str | None:
    """A message if a decimal like 1.667 was meant as a third (or other non-binary division), else None.

    Decimals are exact only for halves, quarters, eighths...; thirds must be written as fractions.
    """
    if "." not in text or value.denominator & (value.denominator - 1) == 0:
        return None
    near = value.limit_denominator(12)
    whole, rest = divmod(near, 1)
    exact = f"{whole}+{rest.numerator}/{rest.denominator}" if whole and rest else str(near)
    return f"'{text}' is not an exact subdivision; write thirds and other divisions as fractions, e.g. {exact}"


_GROUP_RE = re.compile(r"\(([^()]*)\)\*(\d+)")
_TOKEN_RE = re.compile(r"\[[^\]]*\]\S*|\S+")
_NOTE_RE = re.compile(
    r"^(?P<body>\[[^\]]*\]|r|[A-G][#b]*-?\d)"
    r"(?::(?:b(?P<beats>[\d.]+(?:/\d+)?)|(?P<dur>\d+)(?P<dots>\.*)(?P<tup>t?)))?"
    r"(?P<rest>.*)$"
)
_ARTS_RE = re.compile(r"(?:![a-z]+(?:=-?[\d.]+)?)*")
_ART_RE = re.compile(r"!([a-z]+)(?:=(-?[\d.]+))?")
_DURATIONS = {1, 2, 4, 8, 16, 32}


def _expand_groups(text: str) -> str:
    prev = None
    while prev != text:
        prev = text
        text = _GROUP_RE.sub(lambda m: " ".join([m.group(1)] * int(m.group(2))), text)
    return text


def parse_notes(text: str, bar_beats: Fraction, level: float) -> tuple[list[list[Item]], Problems]:
    problems: Problems = []
    bars: list[list[Item]] = []
    dur = Fraction(1)
    lvl = level
    prev_bar: list[Item] | None = None

    for bi, bar_text in enumerate(text.split("|")):
        bar_text = bar_text.strip()
        if bar_text == "%":
            if prev_bar is None:
                problems.append((bi, "'%' has no previous bar to repeat"))
                prev_bar = []
            bars.append(list(prev_bar))
            continue

        bar_text = _expand_groups(bar_text)
        if "(" in bar_text or ")" in bar_text:
            problems.append((bi, "unbalanced '( ... )*n' group (groups cannot span bars)"))
            bar_text = bar_text.replace("(", " ").replace(")", " ")

        items: list[Item] = []
        t = Fraction(0)
        for tok in _TOKEN_RE.findall(bar_text):
            if tok.startswith("@"):
                if tok[1:] in DYNAMICS:
                    lvl = DYNAMICS[tok[1:]]
                else:
                    problems.append((bi, f"unknown dynamic '{tok}'{did_you_mean(tok, ['@' + d for d in DYNAMICS])} "
                                        f"(use one of {', '.join('@' + d for d in DYNAMICS)})"))
                continue

            m = _NOTE_RE.match(tok)
            if not m:
                problems.append((bi, f"cannot parse token '{tok}'"))
                continue

            if m["beats"] is not None:
                try:
                    dur = Fraction(m["beats"])
                except (ValueError, ZeroDivisionError):
                    dur = Fraction(0)
                if dur <= 0:
                    problems.append((bi, f"invalid length ':b{m['beats']}' in '{tok}' (use beats, e.g. :b2.5 or :b1/3)"))
                    continue
                if msg := inexact_decimal(m["beats"], dur):
                    problems.append((bi, f"length in '{tok}': {msg}"))
            elif m["dur"] is not None:
                d = int(m["dur"])
                if d not in _DURATIONS:
                    problems.append((bi, f"invalid duration ':{d}' in '{tok}' (use 1, 2, 4, 8, 16 or 32, "
                                         f"or a length in beats like :b2.5)"))
                    continue
                dur = Fraction(4, d) * (2 - Fraction(1, 2 ** len(m["dots"])))
                if m["tup"]:
                    dur *= Fraction(2, 3)

            rest = m["rest"]
            tie = "~" in rest
            rest = rest.replace("~", "")
            if not _ARTS_RE.fullmatch(rest):
                problems.append((bi, f"cannot parse articulations '{rest}' in '{tok}'"))
                rest = ""
            arts: dict = {}
            for name, value in _ART_RE.findall(rest):
                if name not in ARTS:
                    problems.append((bi, f"unknown articulation '!{name}' in '{tok}'{did_you_mean(name, ARTS)} "
                                        f"(use {', '.join('!' + a for a in sorted(ARTS))})"))
                elif name in VALUED_ARTS:
                    if not value:
                        problems.append((bi, f"'!{name}' needs a value, e.g. '!{name}=2'"))
                    else:
                        arts[name] = float(value)
                else:
                    arts[name] = True

            body = m["body"]
            if body == "r":
                if tie or arts:
                    problems.append((bi, f"rest '{tok}' cannot have a tie or articulations"))
                pitches: tuple[int, ...] = ()
            else:
                names = body[1:-1].split() if body.startswith("[") else [body]
                if not names:
                    problems.append((bi, f"empty chord in '{tok}'"))
                try:
                    pitches = tuple(sorted({parse_pitch(n) for n in names}))
                except ValueError as e:
                    problems.append((bi, str(e)))
                    pitches = ()

            items.append(Item(t, dur, pitches, lvl, tie, arts))
            t += dur

        if t < bar_beats:
            problems.append((bi, f"duration {fmt_beats(t)} beats, expected {fmt_beats(bar_beats)}: "
                                 f"{fmt_beats(bar_beats - t)} beat(s) missing (e.g. add r:b{fmt_beats(bar_beats - t)})"))
        elif t > bar_beats:
            problems.append((bi, f"duration {fmt_beats(t)} beats, expected {fmt_beats(bar_beats)}: "
                                 f"{fmt_beats(t - bar_beats)} beat(s) too many; a note cannot cross the barline, "
                                 f"so end it at the barline and tie it into the next bar with ~"))
        bars.append(items)
        prev_bar = items

    return bars, problems


_POS_RE = re.compile(r"^(\d+(?:\.\d+)?)(?:\+(\d+)/(\d+))?((?:![a-z]+)*)$")
HIT_ARTS = {"acc": {"acc": True}, "ghost": {"ghost": True}, "flam": {"flam": True}}
HIT_LEN = Fraction(1, 4)


def parse_hits(text: str, bar_beats: Fraction, level: float, n_bars: int) -> tuple[list[list[Item]], Problems]:
    """Drum hits by beat position: `sd: 2!acc 4 | 2 3.75!ghost 4`, or `hh: every 0.5`."""
    problems: Problems = []
    bars: list[list[Item]] = [[] for _ in range(n_bars)]
    seen: set[str] = set()

    for line in text.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            problems.append((None, f"hits line '{line.strip()}' must look like 'sd: 2 4'"))
            continue
        lane, body = (part.strip() for part in line.split(":", 1))
        if lane not in LANES:
            problems.append((None, f"unknown drum lane '{lane}'{did_you_mean(lane, LANES)} (use {', '.join(LANES)})"))
            continue
        if lane in seen:
            problems.append((None, f"drum lane '{lane}' appears twice"))
            continue
        seen.add(lane)
        segments = body.split("|")
        if len(segments) != n_bars:
            problems.append((None, f"lane '{lane}' has {len(segments)} bar(s) separated by '|', expected {n_bars}"))
            continue
        for bi, seg in enumerate(segments):
            for onset, arts in _hit_positions(seg.split(), bar_beats, lane, bi, problems):
                bars[bi].append(Item(onset=onset, dur=HIT_LEN, pitches=(LANES[lane][0],),
                                     level=level, arts=arts, lane=lane))

    for bar in bars:
        bar.sort(key=lambda it: it.onset)
    return bars, problems


def _hit_positions(tokens: list[str], bar_beats: Fraction, lane: str, bi: int,
                   problems: Problems) -> list[tuple[Fraction, dict]]:
    if tokens[:1] == ["every"]:
        try:
            step = Fraction(tokens[1]) if len(tokens) == 2 else Fraction(0)
        except (ValueError, ZeroDivisionError):
            step = Fraction(0)
        if step > 0 and (msg := inexact_decimal(tokens[1], step)):
            problems.append((bi, f"lane '{lane}': every {msg}"))
            return []
        if step <= 0:
            problems.append((bi, f"lane '{lane}': write 'every' with one step in beats, e.g. 'every 0.5' or 'every 1/3'"))
            return []
        count = bar_beats / step
        return [(i * step, {}) for i in range(int(count) + (0 if count.denominator == 1 else 1))]

    out: list[tuple[Fraction, dict]] = []
    for tok in tokens:
        m = _POS_RE.match(tok)
        if not m:
            problems.append((bi, f"lane '{lane}': cannot parse hit '{tok}' (use a beat like 2, 2.5, 1+1/3, "
                                 f"optionally with !acc, !ghost or !flam)"))
            continue
        pos = Fraction(m[1]) + (Fraction(int(m[2]), int(m[3])) if m[2] else 0)
        if msg := inexact_decimal(m[1], Fraction(m[1])):
            problems.append((bi, f"lane '{lane}': beat {msg}"))
            continue
        if not 1 <= pos < bar_beats + 1:
            problems.append((bi, f"lane '{lane}': beat {tok} is outside the bar (beats 1 to "
                                 f"{fmt_beats(bar_beats + 1)}, exclusive)"))
            continue
        arts: dict = {}
        for name in m[4].split("!")[1:]:
            if name in HIT_ARTS:
                arts.update(HIT_ARTS[name])
            else:
                problems.append((bi, f"lane '{lane}': unknown hit mark '!{name}'{did_you_mean(name, HIT_ARTS)} "
                                     f"(use !acc, !ghost or !flam)"))
        if any(o == pos - 1 for o, _ in out):
            problems.append((bi, f"lane '{lane}': beat {tok.split('!')[0]} is listed twice"))
            continue
        out.append((pos - 1, arts))
    return out


def _grouped(steps_text: str, size: int) -> str:
    """'x-x-x-x-x' grouped as 'x-x- x-x- x' so a missing or extra step is easy to spot."""
    return " ".join(steps_text[i:i + size] for i in range(0, len(steps_text), size))


def parse_grid(text: str, bar_beats: Fraction, steps: int, level: float,
               n_bars: int) -> tuple[list[list[Item]], Problems]:
    problems: Problems = []
    bars: list[list[Item]] = [[] for _ in range(n_bars)]
    step_len = bar_beats / steps
    per_beat = steps / bar_beats
    group = int(per_beat) if per_beat.denominator == 1 else steps
    seen: set[str] = set()

    for line in text.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            problems.append((None, f"grid line '{line.strip()}' must look like 'sd: ----x-------x---'"))
            continue
        lane, pattern = line.split(":", 1)
        lane = lane.strip()
        segments = [re.sub(r"\s", "", seg) for seg in pattern.split("|")]
        pattern = "".join(segments)
        if len(segments) == n_bars and len(pattern) != steps * n_bars:
            # Bars are marked with '|': point at the bar that has the wrong length.
            for bi, seg in enumerate(segments):
                if len(seg) != steps:
                    problems.append((bi, f"lane '{lane}' has {len(seg)} steps in this bar, expected {steps}; "
                                         f"by beat it reads '{_grouped(seg, group)}'"))
            continue
        if lane not in LANES:
            problems.append((None, f"unknown drum lane '{lane}'{did_you_mean(lane, LANES)} (use {', '.join(LANES)})"))
            continue
        if lane in seen:
            problems.append((None, f"drum lane '{lane}' appears twice"))
            continue
        seen.add(lane)
        expected = steps * n_bars
        if len(pattern) != expected:
            bars_text = " | ".join(pattern[i:i + steps] for i in range(0, len(pattern), steps))
            problems.append((None, f"lane '{lane}' has {len(pattern)} steps, expected {expected} "
                                   f"({n_bars} bar(s) x {steps} steps); split into bars it reads "
                                   f"'{bars_text}' (separate bars with '|' to get per-bar errors)"))
            continue
        for i, c in enumerate(pattern):
            if c in "-.":
                continue
            if c not in GRID_HITS:
                problems.append((i // steps, f"lane '{lane}': unknown hit '{c}' (use x X g f, or - for silence)"))
                continue
            bars[i // steps].append(Item(
                onset=(i % steps) * step_len, dur=step_len, pitches=(LANES[lane][0],),
                level=level, arts=dict(GRID_HITS[c]), lane=lane,
            ))

    for bar in bars:
        bar.sort(key=lambda it: it.onset)
    return bars, problems
