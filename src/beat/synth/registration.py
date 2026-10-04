"""Organ settings from `model:`: a named registration preset, overridden key by key.

Pure Python so that validating a song does not load the synthesis code.
"""

from dataclasses import dataclass, replace

# Drawbar footages as semitones above the played key: 16' 5 1/3' 8' 4' 2 2/3' 2' 1 3/5' 1 1/3' 1'.
FOOTAGES = (-12, 7, 0, 12, 19, 24, 28, 31, 36)
PERCUSSION = {"off", "2nd", "3rd", "2nd-slow", "3rd-slow"}
VIBRATO = {"off", "v1", "v2", "v3", "c1", "c2", "c3"}
LESLIE = {"slow", "fast"}
MODEL_KEYS = {"engine", "registration", "drawbars", "percussion", "vibrato", "drive", "click"}


@dataclass(frozen=True)
class Registration:
    drawbars: str  # nine digits 0-8, 16' first
    percussion: str = "off"
    vibrato: str = "c3"
    drive: float = 0.3  # 0 clean .. 1 heavy overdrive of the preamp and Leslie amp
    click: float = 0.5  # key click: 0 soft .. 1 hard


PRESETS = {
    "rock": Registration("888800000", drive=0.6),
    "full": Registration("888888888", drive=0.5),
    "jazz": Registration("888000000", percussion="3rd", drive=0.15),
    "soft": Registration("808400000", drive=0.05, click=0.3),
    "gospel": Registration("888000008", percussion="2nd", drive=0.35),
}
DEFAULT_PRESET = "rock"


def _drawbars(value) -> str | None:
    # YAML reads 888000000 as an int and drops leading zeros of 008800000.
    text = f"{value:09d}" if isinstance(value, int) and not isinstance(value, bool) else str(value)
    return text if len(text) == 9 and all(c in "012345678" for c in text) else None


def parse(model: dict) -> tuple[Registration, list[tuple[str, str]]]:
    """Resolve `model:` to a Registration plus (key, message) problems; bad values fall back to the preset."""
    problems: list[tuple[str, str]] = []
    model = model if isinstance(model, dict) else {}
    name = model.get("registration", DEFAULT_PRESET)
    if name not in PRESETS:
        problems.append(("registration", f"unknown registration {name!r}; use one of {', '.join(PRESETS)}"))
        name = DEFAULT_PRESET
    reg = PRESETS[name]
    if "drawbars" in model:
        bars = _drawbars(model["drawbars"])
        if bars is None:
            problems.append(("drawbars", f"drawbars must be nine digits 0-8, 16' first, e.g. \"888000000\"; "
                                         f"got {model['drawbars']!r}"))
        else:
            reg = replace(reg, drawbars=bars)
    for key, allowed in (("percussion", PERCUSSION), ("vibrato", VIBRATO)):
        if key in model:
            value = str(model[key]).lower()
            if value in ("false", "none"):  # YAML reads a bare `off` as False
                value = "off"
            if value in allowed:
                reg = replace(reg, **{key: value})
            else:
                problems.append((key, f"{key} must be one of {', '.join(sorted(allowed))}, got {model[key]!r}"))
    for key in ("drive", "click"):
        if key in model:
            value = model[key]
            if isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1:
                reg = replace(reg, **{key: float(value)})
            else:
                problems.append((key, f"{key} must be a number from 0 to 1, got {value!r}"))
    return reg, problems
