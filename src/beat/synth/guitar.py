"""Electric guitar: plucked-string model with a bridge pickup, played with a pick, into a tube amp and cabinet."""

import numpy as np

from ..compile import Event
from ..song import Instrument
from . import amp
from .plucked import StringModel, strings_signal

GUITAR = StringModel(
    scale_m=0.648, pluck_m=0.12, pickup_m=0.04, pickup_hz=3800.0, pickup_q=1.4, level=0.35,
    t60_ref=6.0, f_ref=82.4, t60_range=(1.0, 8.0), damp_hz=1500.0,
    b_wound=1.5e-5, b_plain=4e-5, plain_from=55,
    width_soft=0.0010, width_hard=0.0002, noise=0.05, tension_cents=0.0,
)


def render_part(inst: Instrument, events: list[Event], n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    return amp.amp(strings_signal(GUITAR, inst, events, n, sr, rng), sr, inst.tone or "crunch")
