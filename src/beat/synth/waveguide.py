"""Single-delay-loop string waveguide with persistent state (numba).

One call runs one string for a whole part. The loop is
    y[n] = x[n] + Loss(Disp(Delay_d(y)))[n]
with a cubic Lagrange fractional delay, a cascade of first-order allpasses for stiffness
(inharmonicity) and a one-pole loss filter. The string is driven by a list of segments, each
holding loop parameters from its start sample on: a new note changes the delay (fret), damping
changes the loss filter, and a re-pluck first scales the existing vibration down (the pick stops
the string). Excitations are added at the loop input. The output is the bridge-pickup tap.
"""

from functools import lru_cache

import numpy as np
from numba import njit
from scipy.optimize import minimize_scalar

N_ALLPASS = 2
MAX_DC_GAIN = 0.9999
MAX_POLE = 0.9  # loss filter pole; beyond this the filter eats the fundamental's neighbours too


@njit(cache=True)
def run_string(out, buf_len_pow2, seg_start, seg_delay, seg_g, seg_a, seg_c, seg_tap, seg_stop, seg_glide,
               exc_start, exc_off, exc_len, exc_data):
    """Run one string and add its pickup signal into `out`. Segments and excitations sorted by start."""
    n_total = out.shape[0]
    size = 1 << buf_len_pow2
    mask = size - 1
    buf = np.zeros(size)
    ap_x = np.zeros(N_ALLPASS)
    ap_y = np.zeros(N_ALLPASS)
    lp = 0.0
    w = 0
    S = seg_start.shape[0]
    E = exc_start.shape[0]
    si = -1
    ei = 0
    cur = -1
    epos = 0
    d = 4.0
    d_step = 0.0
    d_target = 4.0
    glide_left = 0
    g = 0.0
    a = 0.0
    c = 0.0
    tap = 1.0
    quiet = 0
    n = n_total
    if S > 0:
        n = seg_start[0]
    if E > 0 and exc_start[0] < n:
        n = exc_start[0]

    while n < n_total:
        while si + 1 < S and seg_start[si + 1] <= n:
            si += 1
            stop = seg_stop[si]
            if stop > 0.0:
                k = 1.0 - stop
                for i in range(size):
                    buf[i] *= k
                lp *= k
                for j in range(N_ALLPASS):
                    ap_x[j] *= k
                    ap_y[j] *= k
            g = seg_g[si]
            a = seg_a[si]
            c = seg_c[si]
            tap = seg_tap[si]
            d_target = seg_delay[si]
            if seg_glide[si] > 0 and si > 0:
                glide_left = seg_glide[si]
                d_step = (d_target - d) / glide_left
            else:
                glide_left = 0
                d = d_target
            quiet = 0
        while ei < E and exc_start[ei] <= n:
            cur = ei
            epos = 0
            ei += 1
            quiet = 0

        x = 0.0
        if cur >= 0:
            x = exc_data[exc_off[cur] + epos]
            epos += 1
            if epos >= exc_len[cur]:
                cur = -1

        if glide_left > 0:
            d += d_step
            glide_left -= 1
            if glide_left == 0:
                d = d_target

        # Cubic Lagrange read of y[n - d], taps at delays m0 .. m0 + 3 with m0 = floor(d) - 1.
        m0 = int(np.floor(d)) - 1
        f = d - m0
        h0 = -(f - 1.0) * (f - 2.0) * (f - 3.0) / 6.0
        h1 = f * (f - 2.0) * (f - 3.0) / 2.0
        h2 = -f * (f - 1.0) * (f - 3.0) / 2.0
        h3 = f * (f - 1.0) * (f - 2.0) / 6.0
        v = (h0 * buf[(w - m0) & mask] + h1 * buf[(w - m0 - 1) & mask]
             + h2 * buf[(w - m0 - 2) & mask] + h3 * buf[(w - m0 - 3) & mask])
        for j in range(N_ALLPASS):
            yj = c * v + ap_x[j] - c * ap_y[j]
            ap_x[j] = v
            ap_y[j] = yj
            v = yj
        lp = g * (1.0 - a) * v + a * lp
        y = x + lp
        buf[w] = y

        # Bridge pickup: y[n] - y[n - tap], the pickup position's comb.
        ti = int(tap)
        tf = tap - ti
        yt = (1.0 - tf) * buf[(w - ti) & mask] + tf * buf[(w - ti - 1) & mask]
        out[n] += y - yt
        w = (w + 1) & mask

        # Skip ahead once the string has been silent for longer than one period.
        if cur < 0 and abs(y) < 1e-7:
            quiet += 1
        else:
            quiet = 0
        if quiet > d + 8:
            nxt = n_total
            if si + 1 < S:
                nxt = seg_start[si + 1]
            if ei < E and exc_start[ei] < nxt:
                nxt = exc_start[ei]
            if nxt > n + 1:
                buf[:] = 0.0
                ap_x[:] = 0.0
                ap_y[:] = 0.0
                lp = 0.0
                n = nxt
                continue
        n += 1


def _lagrange_response(w: np.ndarray, d: float) -> np.ndarray:
    m0 = np.floor(d) - 1
    f = d - m0
    h = np.array([-(f - 1) * (f - 2) * (f - 3) / 6, f * (f - 2) * (f - 3) / 2,
                  -f * (f - 1) * (f - 3) / 2, f * (f - 1) * (f - 2) / 6])
    z = np.exp(-1j * np.outer(w, m0 + np.arange(4)))
    return z @ h


def _allpass_delay(w: np.ndarray | float, c: float) -> np.ndarray:
    """Phase delay in samples of one first-order allpass (c + z^-1) / (1 + c z^-1)."""
    z = np.exp(-1j * np.asarray(w))
    return -np.angle((c + z) / (1 + c * z)) / np.asarray(w)


def _loss_delay(w: float, a: float) -> float:
    return float(-np.angle((1 - a) / (1 - a * np.exp(-1j * w))) / w)


@lru_cache(maxsize=4096)
def dispersion_coef(f0: float, B: float, sr: int) -> float:
    """Allpass coefficient whose delay falls with frequency like a stiff string's partials."""
    if B <= 0:
        return 0.0
    k = np.arange(1, 40)
    fk = k * f0 * np.sqrt(1 + B * k * k)
    k, fk = k[fk < min(6000.0, 0.4 * sr)], fk[fk < min(6000.0, 0.4 * sr)]
    if len(k) < 3:
        return 0.0
    target = sr / (f0 * np.sqrt(1 + B * k * k))  # loop delay each partial needs
    target -= target[0]
    wk = 2 * np.pi * fk / sr

    def err(c: float) -> float:
        dly = N_ALLPASS * _allpass_delay(wk, c)
        return float(np.sum((dly - dly[0] - target) ** 2 / k))

    return float(minimize_scalar(err, bounds=(-0.9, 0.0), method="bounded").x)


def loss_coefs(f0: float, t60_low: float, t60_high: float, f_high: float, sr: int,
               interp_gain: float = 1.0) -> tuple[float, float]:
    """(g, a) of g(1-a)/(1 - a z^-1): the fundamental decays in t60_low s, partials near f_high in t60_high s.

    `interp_gain` is the fractional delay's own gain at f_high, which the filter makes up for.
    A one-pole cannot fall off faster than about f0 / f_high; steeper targets get the steepest it can do.
    """
    g0 = 10 ** (-3 / (t60_low * f0))
    gh = min(g0, 10 ** (-3 / (t60_high * f0)) / max(interp_gain, 1e-3))
    r2 = (gh / g0) ** 2
    c0, ch = np.cos(2 * np.pi * f0 / sr), np.cos(2 * np.pi * f_high / sr)
    a = 0.0
    if r2 < 1 - 1e-12:
        # |H(wh)|^2 / |H(w0)|^2 = r^2  <=>  (r^2 - 1) a^2 + 2 (c0 - r^2 ch) a + (r^2 - 1) = 0
        A, Bq = r2 - 1, 2 * (c0 - r2 * ch)
        disc = Bq * Bq - 4 * A * A
        roots = [(-Bq + s * np.sqrt(disc)) / (2 * A) for s in (1, -1)] if disc >= 0 else []
        a = min((r for r in roots if 0 <= r <= MAX_POLE), default=MAX_POLE)
    g = g0 * np.sqrt(1 - 2 * a * c0 + a * a) / (1 - a)  # gain g0 at the fundamental
    g = min(g, MAX_DC_GAIN)  # the loop's gain at DC must stay below 1
    return float(g), float(a)


def loop_params(f0: float, B: float, t60_low: float, t60_high: float, f_high: float,
                sr: int) -> tuple[float, float, float, float]:
    """(delay for the interpolator, g, a, allpass c) so the loop is tuned to f0."""
    period = sr / f0
    c = dispersion_coef(round(f0, 2), B, sr)
    w0 = 2 * np.pi * f0 / sr
    wh = 2 * np.pi * f_high / sr
    g, a = 0.0, 0.0
    d = period
    for _ in range(2):  # the loss filter's gain depends a little on the delay it is paired with
        ig = float(np.abs(_lagrange_response(np.array([wh]), max(d, 2.0))[0]))
        g, a = loss_coefs(f0, t60_low, t60_high, f_high, sr, ig)
        d = period - _loss_delay(w0, a) - N_ALLPASS * float(_allpass_delay(w0, c))
    return max(d, 2.0), g, a, c
