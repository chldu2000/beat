"""Synthesis engines: each instrument type has named engines, picked with `model: { engine: ... }`.

An engine renders all events of one part into a mono or stereo buffer of length n; engines of
instruments with section controls (the organ's Leslie speed) also get them as `controls`. Engine modules
are imported lazily so that validating a song does not load numba.
"""

from collections.abc import Callable
from importlib import import_module
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..compile import Control, Event
    from ..song import Instrument

# type -> engine name -> "module:function"; the first engine is the default.
ENGINES: dict[str, dict[str, str]] = {
    "drums": {"kit": "drums:render_part"},
    "bass": {"waveguide": "bass:render_part", "ks": "strings:render_part"},
    "guitar": {"waveguide": "guitar:render_part", "ks": "strings:render_part"},
    "organ": {"tonewheel": "organ:render_part", "drawbar": "keys:organ_part"},
    "piano": {"additive": "keys:piano_part"},
}


def engine_name(inst: "Instrument") -> str:
    name = inst.model.get("engine") if isinstance(inst.model, dict) else None
    return name if name in ENGINES[inst.type] else next(iter(ENGINES[inst.type]))


def render_part(inst: "Instrument", events: list["Event"], n: int, sr: int,
                rng: np.random.Generator, controls: list["Control"] = ()) -> np.ndarray:
    module, func = ENGINES[inst.type][engine_name(inst)].split(":")
    kwargs = {"controls": controls} if controls else {}
    return getattr(import_module(f".{module}", __package__), func)(inst, events, n, sr, rng, **kwargs)


def mix_notes(events: list["Event"], n: int, sr: int, voice: Callable[["Event"], np.ndarray]) -> np.ndarray:
    """Render each note on its own and add it at its onset (for engines without shared state)."""
    out = np.zeros(n)
    for ev in events:
        y = voice(ev)
        start = int(ev.time * sr)
        y = y[: max(0, n - start)]
        out[start:start + len(y)] += y
    return out
