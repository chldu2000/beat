"""Dynamics for the mixer: a compressor, a true-peak lookahead limiter, and loudness (ITU-R BS.1770).

Both processors take mono (n,) or stereo (n, 2) audio, link the channels, and return the processed audio
with the gain reduction in dB per sample, so the mix report can say how hard and where they worked.
"""

import numpy as np
from numba import njit
from scipy.ndimage import minimum_filter1d
from scipy.signal import lfilter, resample_poly

RMS_MS = 5.0  # the compressor's level detector: a short RMS
TRUE_PEAK_OS = 4


@njit(cache=True)
def _compress(power, thr, ratio, knee, a_rms, a_att, a_rel, gr):
    env = 0.0
    g = 0.0
    slope = 1.0 - 1.0 / ratio
    for t in range(power.shape[0]):
        env = a_rms * env + (1.0 - a_rms) * power[t]
        over = 10.0 * np.log10(env + 1e-20) - thr
        if 2.0 * over <= -knee:
            target = 0.0
        elif 2.0 * over >= knee:
            target = slope * over
        else:
            target = slope * (over + knee / 2.0) ** 2 / (2.0 * knee)
        coef = a_att if target > g else a_rel
        g = coef * g + (1.0 - coef) * target
        gr[t] = g


def _coef(ms: float, sr: int) -> float:
    return float(np.exp(-1.0 / (ms * 1e-3 * sr)))


def _power(x: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(x ** 2 if x.ndim == 1 else np.mean(x ** 2, axis=1), dtype=np.float64)


def compress(x: np.ndarray, sr: int, threshold_db: float, ratio: float, attack_ms: float, release_ms: float,
             knee_db: float = 6.0) -> tuple[np.ndarray, np.ndarray]:
    """Feed-forward compressor with a soft knee; the level is a short RMS of the linked channels (dBFS)."""
    gr = np.zeros(len(x))
    _compress(_power(x), float(threshold_db), float(ratio), float(knee_db), _coef(RMS_MS, sr),
              _coef(attack_ms, sr), _coef(release_ms, sr), gr)
    gain = 10 ** (-gr / 20)
    return x * (gain if x.ndim == 1 else gain[:, None]), gr


@njit(cache=True)
def _release(m, a_rel, out):
    g = 1.0
    for t in range(m.shape[0]):
        g = m[t] if m[t] < g else m[t] + (g - m[t]) * a_rel
        out[t] = g


def true_peak(x: np.ndarray) -> np.ndarray:
    """Per sample, the largest |value| of the 4x oversampled signal (all channels) up to the next sample."""
    up = np.abs(resample_poly(x, TRUE_PEAK_OS, 1, axis=0))
    if up.ndim == 2:
        up = up.max(axis=1)
    return up[: len(x) * TRUE_PEAK_OS].reshape(len(x), TRUE_PEAK_OS).max(axis=1)


def limit(x: np.ndarray, sr: int, ceiling_db: float = -1.0, lookahead_ms: float = 5.0,
          release_ms: float = 80.0) -> tuple[np.ndarray, np.ndarray]:
    """Lookahead brickwall limiter on the true peak: the output's oversampled peak stays under the ceiling.

    The gain needed at each sample is the minimum over the next `lookahead` samples, released with a one-pole
    and then averaged over the lookahead, so it ramps down before a peak instead of jumping at it.
    """
    n = len(x)
    L = int(lookahead_ms * 1e-3 * sr) | 1  # odd, so the centred min filter can be shifted exactly
    h = (L - 1) // 2
    pad = np.zeros((L - 1,) + x.shape[1:])
    peak = true_peak(np.concatenate([x, pad]))
    peak = np.maximum(peak, np.concatenate([[0.0], peak[:-1]]))  # the stretch before each sample too
    ceiling = 10 ** (ceiling_db / 20) * 0.995
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-12))
    m = minimum_filter1d(np.concatenate([np.ones(L - 1), need]), L)[h:h + n + L - 1]
    smooth = np.empty_like(m)
    _release(m, _coef(release_ms, sr), smooth)
    gain = np.convolve(np.concatenate([np.ones(L - 1), smooth]), np.ones(L) / L, "valid")[L - 1:]
    return x * (gain if x.ndim == 1 else gain[:, None]), -20 * np.log10(gain)


def _k_weighting(sr: int) -> list[tuple[list[float], list[float]]]:
    """BS.1770 pre-filter (high shelf) and RLB highpass, for any sample rate."""
    G, f0, Q = 3.999843853973347, 1681.974450955533, 0.7071752369554196
    K = np.tan(np.pi * f0 / sr)
    Vh = 10 ** (G / 20)
    Vb = Vh ** 0.4996667741545416
    a0 = 1 + K / Q + K * K
    shelf = ([(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0],
             [1.0, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0])
    f0, Q = 38.13547087602444, 0.5003270373238773
    K = np.tan(np.pi * f0 / sr)
    a0 = 1 + K / Q + K * K
    hp = ([1.0, -2.0, 1.0], [1.0, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0])
    return [shelf, hp]


def loudness(x: np.ndarray, sr: int) -> float:
    """Integrated loudness in LUFS (BS.1770-4: K-weighting, 400 ms blocks, absolute and relative gates)."""
    y = x if x.ndim == 2 else x[:, None]
    for b, a in _k_weighting(sr):
        y = lfilter(b, a, y, axis=0)
    block, step = int(0.4 * sr), int(0.1 * sr)
    if len(y) < block:
        return -np.inf
    sq = np.concatenate([np.zeros((1, y.shape[1])), np.cumsum(y ** 2, axis=0)])
    starts = np.arange(0, len(y) - block + 1, step)
    z = ((sq[starts + block] - sq[starts]) / block).sum(axis=1)
    z = z[-0.691 + 10 * np.log10(z + 1e-20) > -70]
    if z.size == 0:
        return -np.inf
    rel = -0.691 + 10 * np.log10(z.mean()) - 10
    z = z[-0.691 + 10 * np.log10(z) > rel]
    return float(-0.691 + 10 * np.log10(z.mean()))
