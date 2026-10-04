"""Electric bass: plucked-string model with a split-coil pickup mid-body, played with fingers, into a bass amp.

Compared with the guitar: a longer scale, stiffer strings (more inharmonicity), longer sustain,
a wider (finger) stroke, a darker pickup, and tension modulation (hard notes start a little sharp).
"""

import numpy as np

from ..compile import Event
from ..song import Instrument
from . import amp
from .plucked import StringModel, strings_signal

BASS = StringModel(
    scale_m=0.864, pluck_m=0.12, pickup_m=0.15, pickup_hz=5000.0, pickup_q=1.5, level=0.35,
    t60_ref=9.0, f_ref=41.2, t60_range=(2.0, 12.0), damp_hz=2000.0,
    b_wound=1e-4, b_plain=1e-4, plain_from=128,
    width_soft=0.0006, width_hard=0.00015, noise=0.02, tension_cents=6.0,
)


def render_part(inst: Instrument, events: list[Event], n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    return amp.bass_amp(strings_signal(BASS, inst, events, n, sr, rng), sr)
