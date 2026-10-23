"""The guitar rig as the DSL sees it: amp tones, pedals in signal order, and the pedals' knobs from `model:`.

Pure Python so that validating a song does not load the synthesis code (that is in `amp.py`).
"""

from ..diagnostics import did_you_mean

TONES = ("clean", "crunch", "lead")
# Signal order, whatever order a song lists them in: the fuzz wants the pickup straight, the boost pushes the amp.
PEDALS = ("fuzz", "od", "boost")
KNOBS = {
    "fuzz": {"drive": 0.6, "tone": 0.5, "level": 0.5},
    "od": {"drive": 0.5, "tone": 0.5, "level": 0.5},
    "boost": {"level": 0.5},
}
MODEL_KEYS = {"engine", *PEDALS}
NONE = "none"  # the `pedals` control value with every pedal off


def fmt(on) -> str:
    """A set of pedals as a control value, in signal order: "fuzz+od", or "none"."""
    return "+".join(p for p in PEDALS if p in on) or NONE


def split(value: str) -> tuple[str, ...]:
    return () if value == NONE else tuple(value.split("+"))


def parse_pedals(raw) -> tuple[tuple[str, ...], str | None]:
    """A `pedals:` list as names in signal order, plus a problem message (unknown names are dropped)."""
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return (), f"pedals must be a list such as [od] or [fuzz, boost] ([] for none), got {raw!r}"
    bad = [str(p) for p in raw if p not in PEDALS]
    on = tuple(p for p in PEDALS if p in raw)
    if bad:
        return on, f"unknown pedal {bad[0]!r}{did_you_mean(bad[0], PEDALS)}; use {', '.join(PEDALS)}"
    return on, None


def knobs(model) -> tuple[dict[str, dict[str, float]], list[tuple[str, str]]]:
    """Every pedal's knobs (0-1) from `model:` (e.g. `od: { drive: 0.7 }`), plus (key, message) problems;
    knobs not set, or set badly, keep their defaults."""
    model = model if isinstance(model, dict) else {}
    out = {p: dict(k) for p, k in KNOBS.items()}
    problems: list[tuple[str, str]] = []
    for pedal in PEDALS:
        if pedal not in model:
            continue
        spec = model[pedal]
        if not isinstance(spec, dict):
            example = ", ".join(f"{k}: {v}" for k, v in KNOBS[pedal].items())
            problems.append((pedal, f"{pedal} takes its knobs as a mapping, e.g. {pedal}: {{ {example} }}"))
            continue
        for key, value in spec.items():
            if key not in KNOBS[pedal]:
                problems.append((f"{pedal} > {key}", f"{pedal} has no knob {key!r}{did_you_mean(key, KNOBS[pedal])}; "
                                                    f"its knobs are {', '.join(KNOBS[pedal])}"))
            elif isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1:
                out[pedal][key] = float(value)
            else:
                problems.append((f"{pedal} > {key}", f"{key} must be a number from 0 to 1, got {value!r}"))
    return out, problems
