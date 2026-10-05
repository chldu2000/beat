"""A room: feedback delay network reverb (numba), mono or stereo in, stereo out.

Eight delay lines with prime lengths, a Householder feedback matrix, and a one-pole low-pass in each
line so the high end dies faster (air and soft surfaces). Delay gains are set from the RT60.
"""

import numpy as np
from numba import njit

DELAYS_MS = np.array([19.1, 23.7, 29.3, 31.9, 37.3, 41.1, 43.7, 53.9])


@njit(cache=True)
def _fdn(x, lens, gains, damp, out):
    n = x.shape[0]
    L = lens.shape[0]
    size = 1
    while size <= lens.max():
        size *= 2
    mask = size - 1
    buf = np.zeros((L, size))
    lp = np.zeros(L)
    v = np.zeros(L)
    w = 0
    for t in range(n):
        s = 0.0
        for i in range(L):
            y = buf[i, (w - lens[i]) & mask]
            lp[i] = (1.0 - damp[i]) * y + damp[i] * lp[i]
            v[i] = gains[i] * lp[i]
            s += v[i]
        s *= 2.0 / L
        for i in range(L):
            buf[i, w] = x[t, i & 1] + v[i] - s
        out[t, 0] += v[0] + v[2] + v[4] + v[6]
        out[t, 1] += v[1] + v[3] + v[5] + v[7]
        w = (w + 1) & mask


def reverb(x: np.ndarray, sr: int, rt60: float = 0.6, rt60_high: float = 0.25, predelay_ms: float = 8.0,
           size: float = 1.0) -> np.ndarray:
    """Stereo (n, 2) wet signal of `x`: decays in `rt60` s, the top end (~5 kHz) in `rt60_high`.

    A mono `x` feeds every delay line; a stereo one feeds its left channel to the lines heard on the left
    and its right channel to the others.
    """
    x = np.stack([x, x], axis=1) if x.ndim == 1 else x
    lens = np.round(DELAYS_MS * size * 1e-3 * sr).astype(np.int64)
    sec = lens / sr
    gains = 10 ** (-3 * sec / rt60)
    # the low-pass takes the extra decay at 5 kHz: |H| = g_high / g_low there
    ratio = 10 ** (-3 * sec / rt60_high) / gains
    c = np.cos(2 * np.pi * 5000 / sr)
    # one-pole (1 - a) / (1 - a z^-1): solve |H(5 kHz)| = ratio for a
    r2 = ratio ** 2
    A, B, C = r2 - 1, 2 * (1 - r2 * c), r2 - 1
    damp = np.where(r2 < 1, (-B + np.sqrt(np.maximum(B * B - 4 * A * C, 0))) / (2 * np.where(A == 0, 1, A)), 0)
    damp = np.clip(np.where(damp > 1, 1 / damp, damp), 0, 0.95)
    pre = int(predelay_ms * 1e-3 * sr)
    xin = np.concatenate([np.zeros((pre, 2)), x[: len(x) - pre]]) if pre else x
    out = np.zeros((len(x), 2))
    _fdn(np.ascontiguousarray(xin, dtype=np.float64), lens, gains, damp, out)
    return out / 2
