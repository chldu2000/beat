"""The mix layer's settings (spec section 10): presets, per-instrument defaults, and parsing `mix:`.

Every part goes through a channel strip (highpass, EQ, compressor, fader, pan, reverb send) into the master
bus (glue compressor, limiter, loudness). The DSP lives in `render.py`; this module only resolves settings,
so validating a song does not load numba.
"""

from dataclasses import dataclass, field

from .diagnostics import did_you_mean

# space -> FDN room settings (rt60 s, rt60 at ~5 kHz s, predelay ms, size)
SPACES = {
    "dry": None,
    "room": (0.5, 0.25, 8.0, 0.8),
    "studio": (0.8, 0.35, 15.0, 1.0),
    "hall": (1.8, 0.7, 30.0, 1.8),
}
DEFAULT_SPACE = "studio"
# comp -> (threshold dB above the part's RMS, ratio, attack ms, release ms)
COMPS = {
    "off": None,
    "light": (6.0, 2.0, 20.0, 150.0),
    "medium": (3.0, 3.0, 10.0, 120.0),
    "heavy": (0.0, 4.0, 5.0, 100.0),
}
# reverb -> send level, dB of reverb energy against the dry part
REVERBS = {"off": None, "less": -20.0, "normal": -14.0, "more": -9.0}
# master style -> glue compressor (threshold dB above the mix's RMS, ratio, attack ms, release ms)
STYLES = {"rock": (1.0, 2.0, 30.0, 250.0), "gentle": (4.0, 1.5, 30.0, 300.0), "none": None}
DEFAULT_STYLE = "rock"
DEFAULT_LOUDNESS = -14.0  # LUFS
CEILING_DB = -1.0  # true peak

# instrument type -> fixed frequencies (Hz) of the low shelf, mid peak and high shelf that `eq` adjusts
EQ_BANDS = {
    "drums": (80, 400, 5000),
    "bass": (80, 700, 2500),
    "guitar": (120, 800, 4000),
    "organ": (100, 1000, 4000),
    "piano": (100, 1000, 5000),
}
# instrument type -> highpass Hz, fixed EQ (kind, Hz, dB, Q) under the user's, comp, reverb, peak catch
DEFAULTS = {
    "drums": (0, [], "medium", "less", 18.0),
    "bass": (35, [("peak", 250, -1.5, 1.0)], "heavy", "off", 0.0),
    "guitar": (90, [("peak", 350, -1.5, 1.0)], "light", "normal", 0.0),
    "organ": (60, [], "light", "normal", 0.0),
    "piano": (50, [], "light", "more", 0.0),
}
# The drums' stick and cymbal transients sit some 21 dB over their RMS; left alone, the master limiter
# ducks the whole band at every crash. A fast peak limiter on the drums only (this many dB over their
# RMS) takes the top off those few hits instead.
PEAK_RELEASE_MS = 20.0

PART_KEYS = {"gain_db", "pan", "eq", "hpf", "comp", "reverb"}
EQ_KEYS = ("low", "mid", "high")
MASTER_KEYS = {"style", "loudness", "gain_db"}
EQ_RANGE = 12.0
GAIN_RANGE = (-40.0, 20.0)
HPF_RANGE = (20.0, 1000.0)
LOUDNESS_RANGE = (-30.0, -6.0)


@dataclass
class Strip:
    gain_db: float = 0.0
    pan: float = 0.0
    hpf: float = 0.0  # Hz, 0 = off
    eq: list[tuple[str, float, float, float]] = field(default_factory=list)  # (kind, Hz, dB, Q)
    comp: str = "off"
    reverb: str = "off"
    peak: float = 0.0  # peak catch: limit to this many dB over the part's RMS (0 = off); not a DSL key


@dataclass
class Mix:
    space: str = DEFAULT_SPACE
    parts: dict[str, Strip] = field(default_factory=dict)
    style: str = DEFAULT_STYLE
    loudness: float = DEFAULT_LOUDNESS  # target LUFS, master gain_db included


def default_strip(itype: str) -> Strip:
    hpf, eq, comp, reverb, peak = DEFAULTS[itype]
    return Strip(hpf=hpf, eq=list(eq), comp=comp, reverb=reverb, peak=peak)


def parse(raw, parts: dict[str, str]) -> tuple[Mix, list[tuple[str, str, str]]]:
    """Resolve `mix:` for parts {id: instrument type}. Returns the Mix and (level, where, message) problems;
    bad values fall back to the defaults."""
    problems: list[tuple[str, str, str]] = []

    def error(where: str, msg: str) -> None:
        problems.append(("error", where, msg))

    mix = Mix(parts={pid: default_strip(t) for pid, t in parts.items()})
    if raw is None:
        return mix, problems
    if not isinstance(raw, dict):
        error("mix", "mix must be a mapping of part ids (and space, master) to settings, e.g. gt1: { pan: -0.5 }")
        return mix, problems

    for key, value in raw.items():
        if key == "space":
            if value not in SPACES:
                error("mix > space", f"space must be one of {', '.join(SPACES)}, got {value!r}"
                                     f"{did_you_mean(value, SPACES)}")
            else:
                mix.space = value
        elif key == "master":
            _master(value, mix, problems)
        elif key in parts:
            _strip(value, parts[key], mix.parts[key], f"mix > {key}", problems)
        else:
            error(f"mix > {key}", f"unknown part '{key}'{did_you_mean(key, list(parts) + ['space', 'master'])}; "
                                  f"mix keys are part ids from instruments, space and master")
    return mix, problems


def _number(value, lo: float, hi: float, where: str, unit: str, problems: list) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not lo <= value <= hi:
        problems.append(("error", where, f"must be a number{unit} from {lo:g} to {hi:g}, got {value!r}"))
        return None
    return float(value)


def _choice(value, choices: dict, where: str, problems: list) -> str | None:
    if value not in choices:
        problems.append(("error", where, f"must be one of {', '.join(choices)}, got {value!r}"
                                         f"{did_you_mean(value, choices)}"))
        return None
    return value


def _unknown(raw: dict, allowed, where: str, problems: list) -> None:
    for k in raw:
        if k not in allowed:
            problems.append(("warning", where, f"unknown key '{k}'{did_you_mean(k, allowed)} "
                                               f"(allowed: {', '.join(sorted(allowed))})"))


def _strip(raw, itype: str, strip: Strip, where: str, problems: list) -> None:
    if not isinstance(raw, dict):
        problems.append(("error", where, "part settings must be a mapping, e.g. { gain_db: -2, pan: -0.5 }"))
        return
    _unknown(raw, PART_KEYS, where, problems)
    if "gain_db" in raw:
        v = _number(raw["gain_db"], *GAIN_RANGE, f"{where} > gain_db", " (dB)", problems)
        strip.gain_db = strip.gain_db if v is None else v
    if "pan" in raw:
        v = _number(raw["pan"], -1, 1, f"{where} > pan", " (-1 left, 1 right)", problems)
        strip.pan = strip.pan if v is None else v
    if "hpf" in raw:
        if raw["hpf"] == "off":
            strip.hpf = 0.0
        else:
            v = _number(raw["hpf"], *HPF_RANGE, f"{where} > hpf", " (Hz) or off", problems)
            strip.hpf = strip.hpf if v is None else v
    for key, choices in (("comp", COMPS), ("reverb", REVERBS)):
        if key in raw:
            v = _choice(raw[key], choices, f"{where} > {key}", problems)
            if v is not None:
                setattr(strip, key, v)
    if "eq" in raw:
        eq = raw["eq"]
        if not isinstance(eq, dict):
            problems.append(("error", f"{where} > eq", "eq must be a mapping of band to dB, e.g. { mid: -2, high: 1 }"))
            return
        _unknown(eq, EQ_KEYS, f"{where} > eq", problems)
        for band, hz, kind in zip(EQ_KEYS, EQ_BANDS[itype], ("low", "peak", "high")):
            if band in eq:
                v = _number(eq[band], -EQ_RANGE, EQ_RANGE, f"{where} > eq > {band}", " (dB)", problems)
                if v:
                    strip.eq.append((kind, hz, v, 0.7))


def _master(raw, mix: Mix, problems: list) -> None:
    where = "mix > master"
    if not isinstance(raw, dict):
        problems.append(("error", where, "master must be a mapping, e.g. { style: rock, loudness: -14 }"))
        return
    _unknown(raw, MASTER_KEYS, where, problems)
    if "style" in raw:
        v = _choice(raw["style"], STYLES, f"{where} > style", problems)
        mix.style = mix.style if v is None else v
    if "loudness" in raw:
        v = _number(raw["loudness"], *LOUDNESS_RANGE, f"{where} > loudness", " (LUFS)", problems)
        mix.loudness = mix.loudness if v is None else v
    if "gain_db" in raw:
        v = _number(raw["gain_db"], -20, 20, f"{where} > gain_db", " (dB, added to loudness)", problems)
        if v is not None:
            mix.loudness = min(max(mix.loudness + v, LOUDNESS_RANGE[0]), LOUDNESS_RANGE[1])
