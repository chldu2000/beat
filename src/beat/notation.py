"""Parsers for the two text notations: `notes` (pitched parts) and `grid` (drums).

Both return a list of bars, each a list of Items with onsets relative to the bar,
plus a list of (bar_index | None, message) problems for the caller to locate.
"""

import re
from dataclasses import dataclass, field
from fractions import Fraction

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
    f = float(x)
    return f"{f:g}" if Fraction(f).limit_denominator(1000) == x else str(x)


_GROUP_RE = re.compile(r"\(([^()]*)\)\*(\d+)")
_TOKEN_RE = re.compile(r"\[[^\]]*\]\S*|\S+")
_NOTE_RE = re.compile(
    r"^(?P<body>\[[^\]]*\]|r|[A-G][#b]*-?\d)"
    r"(?::(?P<dur>\d+)(?P<dots>\.*)(?P<tup>t?))?"
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
                    problems.append((bi, f"unknown dynamic '{tok}' (use one of {', '.join('@' + d for d in DYNAMICS)})"))
                continue

            m = _NOTE_RE.match(tok)
            if not m:
                problems.append((bi, f"cannot parse token '{tok}'"))
                continue

            if m["dur"] is not None:
                d = int(m["dur"])
                if d not in _DURATIONS:
                    problems.append((bi, f"invalid duration ':{d}' in '{tok}' (use 1, 2, 4, 8, 16 or 32)"))
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
                    problems.append((bi, f"unknown articulation '!{name}' in '{tok}'"))
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

        if t != bar_beats:
            problems.append((bi, f"duration {fmt_beats(t)} beats, expected {fmt_beats(bar_beats)}"))
        bars.append(items)
        prev_bar = items

    return bars, problems


def parse_grid(text: str, bar_beats: Fraction, steps: int, level: float,
               n_bars: int) -> tuple[list[list[Item]], Problems]:
    problems: Problems = []
    bars: list[list[Item]] = [[] for _ in range(n_bars)]
    step_len = bar_beats / steps
    seen: set[str] = set()

    for line in text.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            problems.append((None, f"grid line '{line.strip()}' must look like 'sd: ----x-------x---'"))
            continue
        lane, pattern = line.split(":", 1)
        lane = lane.strip()
        pattern = re.sub(r"[\s|]", "", pattern)
        if lane not in LANES:
            problems.append((None, f"unknown drum lane '{lane}' (use {', '.join(LANES)})"))
            continue
        if lane in seen:
            problems.append((None, f"drum lane '{lane}' appears twice"))
            continue
        seen.add(lane)
        expected = steps * n_bars
        if len(pattern) != expected:
            problems.append((None, f"lane '{lane}' has {len(pattern)} steps, expected {expected} "
                                   f"({n_bars} bar(s) x {steps} steps)"))
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
