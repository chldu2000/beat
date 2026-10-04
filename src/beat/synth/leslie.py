"""Leslie rotary speaker (122 style): an 800 Hz crossover feeds a rotating treble horn and a rotating
bass drum, picked up by two microphones on opposite sides of the cabinet (stereo).

Each rotor's speed follows its target (slow "chorale" / fast "tremolo") with its own inertia: the
light horn gets there in about a second, the heavy drum takes several. For every microphone the
rotor's sound arrives by a direct path and cabinet reflections; each path's length changes as the
rotor turns (Doppler, through a moving fractional delay), and its level (and, for the horn, its
brightness) follows which way the rotor's opening is facing.
"""

import numpy as np
from numba import njit
from scipy.signal import butter, sosfilt

from ..compile import Control

CROSSOVER_HZ = 800.0
HORN_TOP_HZ = 7000.0
SPEED_HZ = {"horn": (0.8, 6.8), "drum": (0.67, 5.9)}  # (slow, fast) revolutions per second
INERTIA_S = {"horn": (0.3, 0.6), "drum": (1.4, 1.8)}  # time constant (speeding up, slowing down)
RADIUS_M = {"horn": 0.17, "drum": 0.11}
BACK_LEVEL = {"horn": 0.35, "drum": 0.55}  # level with the mouth facing away from the microphone
MIC_DISTANCE_M = 0.5
MIC_ANGLES = (-np.pi / 2, np.pi / 2)  # left, right
# (angle offset, extra delay s, gain): the direct path and reflections off the cabinet walls
PATHS = {"horn": np.array([(0.0, 0.0, 1.0), (np.pi, 0.0012, 0.3), (np.pi / 2, 0.0025, 0.2)]),
         "drum": np.array([(0.0, 0.0, 1.0), (np.pi / 2, 0.002, 0.25)])}
SOUND_MPS = 343.0


def speed_track(controls: list[Control], n: int, sr: int) -> np.ndarray:
    """1.0 where the Leslie is switched to fast, 0.0 where slow, from the part's `leslie` controls."""
    changes = sorted((c.time, c.value) for c in controls if c.name == "leslie")
    fast = np.zeros(n)
    for k, (t, value) in enumerate(changes):
        fast[0 if k == 0 else int(t * sr):] = value == "fast"  # the first setting holds from the start
    return fast


@njit(cache=True)
def _hermite(x, pos):
    i = int(np.floor(pos))
    f = pos - i
    if i < 1 or i + 2 >= len(x):
        return 0.0
    xm, x0, x1, x2 = x[i - 1], x[i], x[i + 1], x[i + 2]
    c1 = 0.5 * (x1 - xm)
    c2 = xm - 2.5 * x0 + 2.0 * x1 - 0.5 * x2
    c3 = 0.5 * (x2 - xm) + 1.5 * (x0 - x1)
    return ((c3 * f + c2) * f + c1) * f + x0


@njit(cache=True)
def _rotor(x, fast, sr, slow_hz, fast_hz, tau_up, tau_down, radius, back, bright, theta0, mics, paths, out):
    """Add one rotor's sound at each microphone into out[:, m]."""
    d = MIC_DISTANCE_M
    speed = fast_hz if fast[0] > 0.5 else slow_hz
    theta = theta0
    n_m, n_p = len(mics), len(paths)
    lp = np.zeros((n_m, n_p))
    for i in range(len(x)):
        target = fast_hz if fast[i] > 0.5 else slow_hz
        tau = tau_up if target > speed else tau_down
        speed += (target - speed) / (tau * sr)
        theta += 2 * np.pi * speed / sr
        for m in range(n_m):
            for p in range(n_p):
                alpha = theta - mics[m] - paths[p, 0] * (1 if m == 0 else -1)
                c = np.cos(alpha)
                length = np.sqrt(d * d + radius * radius - 2 * d * radius * c)
                s = _hermite(x, i - (length / SOUND_MPS + paths[p, 1]) * sr)
                facing = 0.5 * (1 + c)
                g = back + (1 - back) * facing * facing
                if bright:
                    k = np.exp(-2 * np.pi * (1500.0 + 8000.0 * facing) / sr)  # beaming: brighter on axis
                    lp[m, p] = (1 - k) * s + k * lp[m, p]
                    s = lp[m, p]
                out[i, m] += paths[p, 2] * g * s


def rotary(x: np.ndarray, fast: np.ndarray, sr: int) -> np.ndarray:
    lo = sosfilt(butter(2, CROSSOVER_HZ, "lp", fs=sr, output="sos"), x)
    hi = sosfilt(butter(2, CROSSOVER_HZ, "hp", fs=sr, output="sos"), x)
    hi = sosfilt(butter(2, HORN_TOP_HZ, "lp", fs=sr, output="sos"), hi)
    out = np.zeros((len(x), 2))
    mics = np.array(MIC_ANGLES)
    for name, sig, theta0 in (("horn", hi, 0.3), ("drum", lo, 1.9)):
        _rotor(sig, fast, float(sr), *SPEED_HZ[name], *INERTIA_S[name], RADIUS_M[name], BACK_LEVEL[name],
               name == "horn", theta0, mics, PATHS[name], out)
    return out
