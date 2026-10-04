"""Drums with two heads, by modal synthesis with a nonlinear stick contact (numba).

A drum is a batter head and a resonant head coupled through the air in the shell, and maybe a port
hole in the resonant head (a Helmholtz resonator on the same air). Each head is a sum
of ideal circular-membrane modes (m, n): frequencies from the Bessel zeros, a modal mass from the
mode shape, and a decay that grows with frequency. Modes with m > 0 come in pairs a fraction of a
percent apart (uneven lug tuning), which beat. Only axisymmetric (m = 0) modes change the cavity
volume, so the cavity pressure couples those of both heads.

A stick is a mass with Hertz contact F = K * max(0, y - w)^alpha against the batter head at the
strike point, integrated together with the modes: a harder hit is a shorter, brighter contact, and a
new hit lands on whatever the head is already doing. The tension of each head rises with its stretch
(the sum of squared mode amplitudes times their slopes), so hard hits start sharp and glide down. Modes above the modelled
ones are too dense to resolve; they are a decaying noise driven by the contact force.

One call runs one drum for a whole part, skipping ahead while it is silent.
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from numba import njit
from scipy.signal import butter, oaconvolve, sosfilt
from scipy.special import jn_zeros, jv

INCH = 0.0254
SIGMA_BATTER = 0.36  # kg/m², single-ply 10 mil Mylar with coating
SIGMA_RESO = 0.27  # kg/m², 7.5 mil clear
STIFF = 4e9 * 2.5e-4 / (1 - 0.4)  # N/m, Young's modulus x thickness / (1 - Poisson) of Mylar
RHO_C2 = 1.42e5  # Pa, air
AIR = 0.25  # share of the ideal cavity stiffness (air mass loading and the vent hole take the rest)
STICK_SEC = 0.04  # a stick is followed for this long after it hits
MIC_THETA = 1.3  # angle of the close mic from the strike point
MAX_OSC = 600
MAX_HZ = 4000.0
BLOCK = 8  # samples between tension updates
MAX_GLIDE = 1.5  # frequency ratio cap of the tension modulation


@dataclass(frozen=True)
class Beater:
    mass: float  # kg, effective mass at the tip
    k: float  # N/m^alpha, Hertz contact stiffness
    alpha: float  # Hertz exponent: about 1.5 for wood on Mylar, 2.5 and up for felt
    speed: float  # m/s at full velocity


STICK = Beater(mass=0.015, k=2e7, alpha=1.5, speed=5.5)  # loosely held stick
FELT = Beater(mass=0.035, k=2e9, alpha=2.5, speed=4.0)  # bass drum pedal with a felt beater


@dataclass(frozen=True)
class Wires:
    """Snare wires across the snare-side head: `count` masses on springs, pressed on by `preload`."""
    count: int = 8
    mass: float = 0.002  # kg per mass
    freq: float = 70.0  # Hz, each mass on its spring (the wire tension)
    q: float = 8.0
    spread: float = 0.25  # random spread of mass and frequency between strands
    preload: float = 1.5e-4  # m, how far the springs would pull the wires into the head
    span: float = 0.75  # the wires cover this share of the diameter
    k: float = 5e6  # N/m^alpha, steel on Mylar
    alpha: float = 1.5
    buzz_ms: float = 40.0  # decay of the unresolved wire and head modes the collisions excite
    buzz_db: float = 6.0  # their level, against the modal part of a full-force hit


@dataclass(frozen=True)
class Shell:
    pitch: float  # Hz, lowest mode of the coupled drum
    diameter: float  # inches
    depth: float  # inches
    reso: float = 1.0  # resonant-head wave speed squared relative to the batter head's
    reso_sigma: float = SIGMA_RESO
    decay: float = 3.0  # 1/s, amplitude decay rate of the lowest modes
    damping: float = 25.0  # 1/s per kHz², extra decay of higher modes
    radiation: float = 2.0  # 1/s, extra decay of the m = 0 modes, which radiate best
    strike: float = 0.3  # strike radius / head radius
    beater: Beater = STICK
    port: float = 0.0  # Hz, Helmholtz resonance of a port hole in the resonant head (0: no port)
    port_q: float = 4.0
    mic_r: float = 0.6  # close mic over the batter head, radius share
    mic_local: float = 0.5  # the head under the mic, against the whole head's volume velocity
    reso_level: float = 0.4  # the resonant head's volume velocity at the mic
    port_level: float = 0.0  # the port's volume velocity at the mic
    bottom_mic: float = 0.0  # the resonant head under the bottom mic (snare drums)
    wires: Wires | None = None
    residual_ms: float = 50.0  # decay of the unresolved modes
    residual_db: float = -14.0  # unresolved modes, against the modal part of a full-force hit
    level_rms: float = 0.5  # RMS of the first 100 ms of a full-force hit


@dataclass
class Modes:
    """Oscillators of the drum: head 0 is the batter, head 1 the resonant head, head 2 the air in the port."""
    head: np.ndarray
    m: np.ndarray
    j: np.ndarray  # Bessel zero j_mn
    psi: np.ndarray  # angular offset of the mode shape
    omega: np.ndarray  # rad/s at rest tension, without the air
    gamma: np.ndarray  # 1/s
    mass: np.ndarray  # kg
    grad: np.ndarray  # integral of |grad shape|^2 over the head
    air: np.ndarray  # integral of the shape over the head (m = 0 only)
    mic: np.ndarray  # weight of the mode velocity at the mic
    k_air: float  # N/m^5, cavity pressure per volume
    area: float
    tension: np.ndarray  # N/m at rest, per head (1 for the port)
    top_hz: float  # highest modelled batter mode


@lru_cache(maxsize=None)
def _zeros(m: int) -> np.ndarray:
    return jn_zeros(m, 30)


def _head(sigma: float, a: float, tension: float, rng: np.random.Generator, max_osc: int):
    """(m, j, psi, omega, mass) of one head's lowest modes; m > 0 modes as split pairs."""
    c = np.sqrt(tension / sigma)
    rows = []
    for m in range(40):
        for j in _zeros(m):
            if j * c / (2 * np.pi * a) <= MAX_HZ:
                rows.append((j, m))
    rows.sort()
    out = []
    for j, m in rows:
        w = j * c / a
        if m == 0:
            out.append((m, j, 0.0, w, sigma * np.pi * a * a * jv(1, j) ** 2))
            continue
        split, psi = rng.uniform(0.001, 0.005), rng.uniform(0, 2 * np.pi)
        mass = sigma * np.pi * a * a * jv(m + 1, j) ** 2 / 2
        out.append((m, j, psi, w * (1 - split / 2), mass))
        out.append((m, j, psi + np.pi / (2 * m), w * (1 + split / 2), mass))
        if len(out) >= max_osc:
            break
    return [np.array(col) for col in zip(*out[:max_osc])]


def _lowest_mode(sh: Shell, scale: float) -> float:
    """Lowest frequency (Hz) of the coupled m = 0 modes with both tensions scaled by `scale`."""
    md = build(sh, np.random.default_rng(0), scale)
    sel = (md.m == 0) & (md.head < 2)
    mass, omega, air = md.mass[sel], md.omega[sel], md.air[sel]
    stiff = np.diag(mass * omega ** 2) + md.k_air * np.outer(air, air)
    inv = 1 / np.sqrt(mass)
    w2 = np.linalg.eigvalsh(inv[:, None] * stiff * inv[None, :])
    return float(np.sqrt(w2.min()) / (2 * np.pi))


def build(sh: Shell, rng: np.random.Generator, scale: float = 1.0, max_osc: int = MAX_OSC) -> Modes:
    """Modes of a drum; `scale` multiplies the nominal tensions (see `tune`)."""
    a = sh.diameter * INCH / 2
    area = np.pi * a * a
    t_batter = SIGMA_BATTER * (2 * np.pi * a * sh.pitch / jn_zeros(0, 1)[0]) ** 2 * scale
    t_reso = t_batter * sh.reso * sh.reso_sigma / SIGMA_BATTER
    cols = []
    for h, (sigma, tension) in enumerate([(SIGMA_BATTER, t_batter), (sh.reso_sigma, t_reso)]):
        m, j, psi, w, mass = _head(sigma, a, tension, rng, max_osc if h == 0 or sh.wires is None else max_osc // 3)
        if h == 1 and sh.wires is None:
            # driven only through the air, so only its m = 0 modes move
            keep = m == 0
            m, j, psi, w, mass = m[keep], j[keep], psi[keep], w[keep], mass[keep]
        cols.append((np.full(len(m), h), m, j, psi, w, mass, tension))
    head, m, j, psi, omega, mass = (np.concatenate([c[i] for c in cols]) for i in range(6))
    f_khz = omega / (2 * np.pi * 1000)
    gamma = sh.decay + sh.damping * f_khz ** 2 + np.where(m == 0, sh.radiation, 0.0)
    sigma = np.where(head == 0, SIGMA_BATTER, sh.reso_sigma)
    grad = (j / a) ** 2 * mass / sigma
    air = np.where(m == 0, 2 * np.pi * a * a * jv(1, j) / j, 0.0)
    local = jv(m, j * sh.mic_r) * np.cos(m * (MIC_THETA - psi))
    mic = np.where(head == 0, sh.mic_local * local + air / area,
                   sh.reso_level * air / area + sh.bottom_mic * local)
    k_air = AIR * RHO_C2 / (area * sh.depth * INCH)
    top = omega[head == 0].max() / (2 * np.pi)
    if sh.port > 0:
        # The air plug in the port: a mass on the cavity's stiffness, no restoring force of its own.
        # Its mass is set so that it resonates at `port` with the cavity alone.
        port_area = 0.1 * area
        w = 2 * np.pi * sh.port
        extra = dict(head=2, m=0, j=0.0, psi=0.0, omega=0.0, gamma=w / (2 * sh.port_q),
                     mass=k_air * port_area ** 2 / w ** 2, grad=0.0, air=port_area,
                     mic=sh.port_level * port_area / area)
        head, m, j, psi, omega, gamma, mass, grad, air, mic = (
            np.append(arr, extra[name]) for arr, name in zip(
                (head, m, j, psi, omega, gamma, mass, grad, air, mic),
                ("head", "m", "j", "psi", "omega", "gamma", "mass", "grad", "air", "mic")))
    return Modes(head, m, j, psi, omega, gamma, mass, grad, air, mic, k_air, area,
                 np.array([cols[0][6], cols[1][6], 1.0]), top)


@lru_cache(maxsize=None)
def tune(sh: Shell) -> float:
    """Tension scale that puts the coupled drum's lowest mode on `sh.pitch` (the air stiffens it)."""
    lo, hi = 0.1, 1.0
    for _ in range(20):
        mid = (lo + hi) / 2
        if _lowest_mode(sh, mid) > sh.pitch:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def strike_shape(md: Modes, r: float, theta: float) -> np.ndarray:
    """Batter mode shapes at the strike point (zero for the resonant head)."""
    return np.where(md.head == 0, jv(md.m, md.j * r) * np.cos(md.m * (theta - md.psi)), 0.0)


@njit(cache=True)
def _contact(d, comp, k, alpha):
    """Force F = k * (d - comp * F)^alpha of a one-sided contact, solved for F (0 if d <= 0)."""
    if d <= 0.0:
        return 0.0
    hi_f = d / comp
    F = min(k * d ** alpha, hi_f)
    for _ in range(30):
        r = max(d - comp * F, 0.0)
        g = F - k * r ** alpha
        dg = 1.0 + k * alpha * comp * r ** (alpha - 1.0)
        F_new = F - g / dg
        if F_new <= 0.0:
            F_new = 0.5 * F
        if F_new >= hi_f:
            F_new = 0.5 * (F + hi_f)
        if abs(F_new - F) < 1e-9 * (1.0 + F):
            return F_new
        F = F_new
    return F


@njit(cache=True)
def run_drum(out, force_out, wire_out, vol_out, ext_p, ext_thr, dt, head, omega, gamma, mass, grad, air, mic, k_air, area, tension,
             stick_mass, stick_k, alpha, hit_start, hit_speed, hit_shape, hit_comp,
             wire_shape, wire_mass, wire_k, wire_c, wire_rest, wire_z0, wire_fs, wire_comp,
             contact_k, contact_alpha, n_batter):
    """Run one drum and add its mic signal (velocity units) into `out`, the stick force into `force_out`
    and the snare wires' force on the head (less their preload) into `wire_out`. The first `n_batter`
    oscillators are the batter head's: the sticks touch only those, the wires only the others.

    `ext_p` is the sound pressure of the other drums at this one (Pa), pushing on both heads and the
    port; the drum wakes up for it where it exceeds `ext_thr`. `vol_out` gets the volume velocity the
    drum pushes into the room (m^3/s), which sets the pressure it radiates."""
    n_total = out.shape[0]
    N = omega.shape[0]
    H = hit_start.shape[0]
    q = np.zeros(N)
    q1 = np.zeros(N)
    c1 = np.zeros(N)
    c2 = np.exp(-2.0 * gamma * dt)
    b = dt * dt / mass
    qp = np.zeros(N)
    n_air = 0
    air_idx = np.zeros(N, np.int64)
    for i in range(N):
        if air[i] != 0.0:
            air_idx[n_air] = i
            n_air += 1
    slots = 4
    s_hit = -np.ones(slots, np.int64)
    s_y = np.zeros(slots)
    s_u = np.zeros(slots)
    s_end = np.zeros(slots, np.int64)
    stretch = np.zeros(3)
    W = wire_mass.shape[0]
    wz = wire_z0.copy()
    wv = np.zeros(W)
    peak_energy = 0.0
    hi = 0
    n = n_total
    if H > 0:
        n = hit_start[0]
    m = 0
    while m < n and abs(ext_p[m]) <= ext_thr:
        m += 1
    n = min(n, m)
    blk = 0

    while n < n_total:
        while hi < H and hit_start[hi] <= n:
            k = 0  # the slot of the oldest stick
            for s in range(slots):
                if s_hit[s] < 0:
                    k = s
                    break
                if s_end[s] < s_end[k]:
                    k = s
            w = 0.0
            for i in range(N):
                w += hit_shape[hi, i] * q[i]
            s_hit[k] = hi
            s_y[k] = w
            s_u[k] = hit_speed[hi]
            s_end[k] = n + int(STICK_SEC / dt)
            hi += 1
            blk = 0

        if blk == 0:
            # Tension follows the stretch; recompute the resonator coefficients.
            stretch[:] = 0.0
            energy = 0.0
            for i in range(N):
                v = (q[i] - q1[i]) / dt
                energy += mass[i] * (v * v + omega[i] * omega[i] * q[i] * q[i])
                if grad[i] > 0.0:
                    # Mean square over a cycle from the amplitude: following q^2 itself would modulate
                    # the tension at twice each mode's frequency and pump energy into it.
                    stretch[head[i]] += grad[i] * (q[i] * q[i] + v * v / (omega[i] * omega[i])) / 2.0
            for i in range(N):
                ratio = np.sqrt(1.0 + STIFF * stretch[head[i]] / (2.0 * area * tension[head[i]]))
                if ratio > MAX_GLIDE:
                    ratio = MAX_GLIDE
                w = omega[i] * ratio
                wd2 = w * w - gamma[i] * gamma[i]
                if wd2 >= 0.0:
                    c1[i] = 2.0 * np.exp(-gamma[i] * dt) * np.cos(np.sqrt(wd2) * dt)
                else:  # overdamped (the port has no stiffness of its own)
                    c1[i] = 2.0 * np.exp(-gamma[i] * dt) * np.cosh(np.sqrt(-wd2) * dt)
            if energy > peak_energy:
                peak_energy = energy
            active = False
            for s in range(slots):
                if s_hit[s] >= 0:
                    active = True
            if not active and energy < 1e-11 * peak_energy:
                q[:] = 0.0
                q1[:] = 0.0
                wz[:] = wire_z0
                wv[:] = 0.0
                nxt = n_total
                if hi < H:
                    nxt = hit_start[hi]
                m = n + 1
                while m < nxt and abs(ext_p[m]) <= ext_thr:
                    m += 1
                if m >= n_total:
                    break
                if m > n + 1:
                    n = m
                    continue
        blk = (blk + 1) % BLOCK

        # Free step of the modes, with the cavity pressure as an explicit force.
        vol = 0.0
        for k in range(n_air):
            vol += air[air_idx[k]] * q[air_idx[k]]
        p = k_air * vol
        for i in range(N):
            qp[i] = c1[i] * q[i] - c2[i] * q1[i]
        p -= ext_p[n]
        for k in range(n_air):
            i = air_idx[k]
            qp[i] -= b[i] * p * air[i]

        # Each stick in contact: solve its force implicitly, F = K (y' - w')^alpha with the stick
        # position y' and head position w' after the step both depending on F. An explicit force
        # is unstable against the light, stiff high modes.
        total = 0.0
        for s in range(slots):
            h = s_hit[s]
            if h < 0:
                continue
            w = 0.0
            for i in range(n_batter):
                w += hit_shape[h, i] * qp[i]
            d = s_y[s] + s_u[s] * dt - w
            F = 0.0
            if d > 0.0:
                F = _contact(d, dt * dt / stick_mass + hit_comp[h], stick_k, alpha)
                for i in range(n_batter):
                    qp[i] += b[i] * hit_shape[h, i] * F
                total += F
            elif s_u[s] <= 0.0:
                s_hit[s] = -1  # it bounced off; the player takes it away
            s_u[s] -= F / stick_mass * dt
            s_y[s] += s_u[s] * dt
            if n >= s_end[s]:
                s_hit[s] = -1
        force_out[n] += total

        # Snare wires: masses on springs, pressed against the snare-side head (outward coordinates,
        # head at rest = 0). The head's rest state already includes the preload, so it feels the
        # contact force less the static one: when the wires lift off, it loses their push.
        buzz = 0.0
        for k in range(W):
            v = wv[k] + dt * (-wire_k[k] * (wz[k] - wire_rest[k]) - wire_c[k] * wv[k]) / wire_mass[k]
            z = wz[k] + dt * v
            u = 0.0
            for i in range(n_batter, N):
                u -= wire_shape[k, i] * qp[i]
            # penetration after the step: d - comp * F, with the head relieved of the static force
            d = u - z + (wire_comp[k] - dt * dt / wire_mass[k]) * wire_fs[k]
            F = _contact(d, wire_comp[k], contact_k, contact_alpha)
            for i in range(n_batter, N):
                qp[i] += b[i] * wire_shape[k, i] * (F - wire_fs[k])
            wv[k] = v + dt * F / wire_mass[k]
            wz[k] = z + dt * dt * F / wire_mass[k]
            buzz += F - wire_fs[k]
        wire_out[n] += buzz

        y = 0.0
        for i in range(N):
            y += mic[i] * (qp[i] - q[i])
        vol = 0.0
        for k in range(n_air):
            i = air_idx[k]
            vol -= air[i] * (qp[i] - q[i])  # into the cavity is out of the room
        for i in range(N):
            q1[i] = q[i]
            q[i] = qp[i]
        out[n] += y / dt
        vol_out[n] += vol / dt
        n += 1


def stick_speed(beater: Beater, velocity: float) -> float:
    """m/s at the tip for a velocity 0..1."""
    return beater.speed * (0.055 + 0.945 * max(velocity, 0.0) ** 1.4)


class Drum:
    """One tuned drum, ready to render hits; the first 100 ms of a full-force hit have an RMS of `level_rms`."""

    def __init__(self, sh: Shell, sr: int, rng: np.random.Generator):
        self.sh, self.sr = sh, sr
        self.md = build(sh, rng, tune(sh))
        t = np.arange(int(sh.residual_ms * 6e-3 * sr)) / sr
        lo = min(self.md.top_hz, 0.4 * sr)
        hp = butter(2, [lo, min(10000.0, 0.45 * sr)], "bp", fs=sr, output="sos")
        self.ir = sosfilt(hp, rng.standard_normal(len(t))) * np.exp(-t / (sh.residual_ms * 1e-3))
        self._wires(rng)
        modal, force, wire, vol = self._run([0.0], [1.0], [(sh.strike, 0.0)], int(0.1 * sr))
        peak = np.max(np.abs(modal))
        # far mics hear the radiated (volume) part; at the level the close mic has
        self.far = np.sqrt(np.mean(modal ** 2)) / (np.sqrt(np.mean((np.gradient(vol) * sr) ** 2)) + 1e-12)
        resid = oaconvolve(force, self.ir)[: len(force)]
        self.residual = 10 ** (sh.residual_db / 20) * peak / (np.max(np.abs(resid)) + 1e-12)
        y = modal + self.residual * resid
        self.buzz = 0.0
        if sh.wires:
            buzz = oaconvolve(wire, self.buzz_ir)[: len(wire)]
            self.buzz = 10 ** (sh.wires.buzz_db / 20) * peak / (np.max(np.abs(buzz)) + 1e-12)
            y = y + self.buzz * buzz
        self.level = sh.level_rms / (np.sqrt(np.mean(y ** 2)) + 1e-12)

    def _wires(self, rng: np.random.Generator) -> None:
        """Wire arrays for `run_drum` (empty without wires) and the buzz impulse response."""
        md, wr, sr = self.md, self.sh.wires, self.sr
        N = len(md.omega)
        if wr is None:
            self.wire = (np.zeros((0, N)),) + tuple(np.zeros(0) for _ in range(7))
            self.buzz_ir = np.zeros(1)
            return
        x = np.linspace(-wr.span, wr.span, wr.count)
        theta = np.where(x >= 0, np.pi / 2, -np.pi / 2)
        shape = np.array([np.where(md.head == 1, jv(md.m, md.j * abs(xi)) * np.cos(md.m * (th - md.psi)), 0.0)
                          for xi, th in zip(x, theta)])
        mass = wr.mass * (1 + wr.spread * rng.uniform(-1, 1, wr.count))
        w = 2 * np.pi * wr.freq * (1 + wr.spread * rng.uniform(-1, 1, wr.count))
        k = mass * w ** 2
        rest = np.full(wr.count, -wr.preload)
        z0 = -(k * wr.preload / wr.k) ** (1 / wr.alpha)  # sitting in the head under the preload
        fs = k * (z0 - rest)
        comp = 1 / (mass * sr ** 2) + (shape ** 2 / md.mass).sum(axis=1) / sr ** 2
        self.wire = (shape, mass, k, mass * w / wr.q, rest, z0, fs, comp)
        t = np.arange(int(wr.buzz_ms * 6e-3 * sr)) / sr
        bp = butter(2, [2000.0, min(12000.0, 0.45 * sr)], "bp", fs=sr, output="sos")
        self.buzz_ir = sosfilt(bp, rng.standard_normal(len(t))) * np.exp(-t / (wr.buzz_ms * 1e-3))

    def _run(self, times, velocities, points, n, ext=None):
        md, b = self.md, self.sh.beater
        start = np.array([int(max(0.0, t) * self.sr) for t in times], np.int64)
        order = np.argsort(start, kind="stable")
        shape = np.array([strike_shape(md, r, th) for r, th in points]).reshape(len(points), len(md.omega))
        out, force, wire, vol = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
        wr = self.sh.wires or Wires()
        ext = np.zeros(n) if ext is None else ext
        thr = 1e-4 * np.max(np.abs(ext)) if np.any(ext) else np.inf
        run_drum(out, force, wire, vol, ext, thr, 1.0 / self.sr, md.head.astype(np.int64), md.omega, md.gamma, md.mass, md.grad,
                 md.air, md.mic, md.k_air, md.area, md.tension, b.mass, b.k, b.alpha, start[order],
                 np.array([stick_speed(b, v) for v in velocities])[order], shape[order],
                 (shape[order] ** 2 / md.mass).sum(axis=1) / self.sr ** 2, *self.wire, wr.k, wr.alpha,
                 int(np.sum(md.head == 0)))
        return out, force, wire, vol

    def render(self, times, velocities, n: int, rng: np.random.Generator,
               ext: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Hits at `times` (s) with `velocities`, each near the usual spot, with the other drums' sound
        pressure `ext` (Pa) on the heads: (close mic, far mic, rate of change of the volume velocity
        in m^3/s^2, which the radiated pressure is proportional to)."""
        points = [(float(np.clip(rng.normal(self.sh.strike, 0.05), 0.05, 0.85)), float(rng.normal(0, 0.25)))
                  for _ in times]
        modal, force, wire, vol = self._run(times, velocities, points, n, ext)
        noise = oaconvolve(force, self.ir)[:n] * self.residual
        if self.sh.wires:
            noise += oaconvolve(wire, self.buzz_ir)[:n] * self.buzz
        dvol = np.gradient(vol) * self.sr
        return (modal + noise) * self.level, (self.far * dvol + noise) * self.level, dvol


# lane -> drum. 10", 12" rack toms and a 16" floor tom, at the old kit's pitches
TOMS = {
    "t1": Shell(pitch=196.0, diameter=10, depth=8, reso=1.1, decay=4.0),
    "t2": Shell(pitch=147.0, diameter=12, depth=9, reso=1.1, decay=3.5),
    "t3": Shell(pitch=98.0, diameter=16, depth=16, reso=1.1, decay=3.0),
}

# 22" x 18" bass drum, ported front head, a pillow against the batter head
KICK = Shell(pitch=55.0, diameter=22, depth=18, reso=1.15, decay=5.0, damping=150.0, radiation=3.0,
             strike=0.15, beater=FELT, port=48.0, mic_r=0.25, mic_local=0.35, reso_level=0.5, port_level=1.0,
             residual_ms=12.0, residual_db=-14.0)
# 14" x 5.5" snare: coated batter, thin snare-side head tuned higher, wires across it, top and bottom mics
SNARE = Shell(pitch=200.0, diameter=14, depth=5.5, reso=1.5, reso_sigma=0.105, decay=6.0, damping=40.0,
              strike=0.2, bottom_mic=0.3, wires=Wires(), residual_ms=30.0, level_rms=0.25)
DRUMS = {"bd": KICK, "sd": SNARE, **TOMS}
