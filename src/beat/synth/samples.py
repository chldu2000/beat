"""Sampled hi-hat and cymbals from a DrumGizmo kit: DRSKit 2.1 by default.

The kit is not in git (about 3 GB). Unzip its hi-hat, crash and ride folders into `samples/DRSKit`
at the repository root (or point `BEAT_SAMPLES` at the folder that holds `DRSKit`); without it the
synthesized cymbals are used. DRSKit is CC BY 4.0: credit it where a song's credits are given.

Each hit of a DrumGizmo instrument is a multichannel WAV with every mic of the kit, listed in the
instrument's XML with its `power`. We take one mic per lane (the close mic, or the nearer overhead
for the crashes, which have no close mic) and pick the hit whose power matches the velocity.
"""

import os
import warnings
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

SAMPLES_DIR = Path(os.environ.get("BEAT_SAMPLES", Path(__file__).resolve().parents[3] / "samples"))
KIT = "DRSKit"
CREDIT = "Cymbals: DRSKit by DrumGizmo (drumgizmo.org), CC BY 4.0"

# lane -> (instrument, mic). The cymbals are heard from the overhead on their side: the ride's close mic
# brings out its pitched partials, which pile up into a whistle on eighth notes.
LANES = {
    "hh": ("Hihat_closed", "Hihat"), "ho": ("Hihat_open", "Hihat"), "hp": ("Hihat_foot", "Hihat"),
    "cr": ("Crash_left_shank", "OHL"), "cr2": ("Crash_right_shank", "OHR"),
    "rd": ("Ride_tip", "OHR"), "rb": ("Ride_tip_bell", "OHR"),
}
ACCENT = {"hh": "Hihat_closed_shank"}  # accented closed hi-hat: the shank on the edge
# lane -> (RMS, over seconds) of a full-force hit: the synthesized kit's, so the mix balance stays. The
# ride is 3 dB under it: from the overhead its stick tick is ~12 dB hotter than the ring, and would set the
# drum part's peak.
LEVEL = {"hh": (0.17, 0.1), "ho": (0.21, 0.5), "hp": (0.14, 0.1), "cr": (0.21, 1.0), "cr2": (0.21, 1.0),
         "rd": (0.16, 0.5), "rb": (0.19, 0.5)}
DYNAMICS = 2.8  # power ~ velocity^DYNAMICS (the synthesized kit's amplitude goes as velocity^1.4)
CHOICES = 3  # pick among this many hits nearest in power, avoiding the one played last
# lane -> (hold seconds, extra dB per second): the ride rings ~7 dB/s for 5-8 s, so steady eighths pile its
# partials into a drone; past the hold its tail fades faster
TAIL = {"rd": (0.25, 12.0), "rb": (0.25, 12.0)}


def kit_dir() -> Path:
    return SAMPLES_DIR / KIT


def available() -> bool:
    return all((kit_dir() / inst / f"{inst}.xml").exists() for inst, _ in LANES.values())


@lru_cache(maxsize=None)
def _hits(inst: str, mic: str) -> tuple[np.ndarray, tuple[tuple[str, int], ...]]:
    """(powers, (file, channel index) of `mic`) of an instrument's hits, softest first."""
    root = ET.parse(kit_dir() / inst / f"{inst}.xml").getroot()
    powers, files = [], []
    for s in root.find("samples").findall("sample"):
        for af in s.findall("audiofile"):
            if af.get("channel") == mic:
                powers.append(float(s.get("power")))
                files.append((af.get("file"), int(af.get("filechannel")) - 1))
    order = np.argsort(powers, kind="stable")
    return np.array(powers)[order], tuple(files[i] for i in order)


@lru_cache(maxsize=256)
def _audio(inst: str, file: str, channel: int, sr: int) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", wavfile.WavFileWarning)
        rate, data = wavfile.read(kit_dir() / inst / file, mmap=True)
    y = np.array(data[:, channel], dtype=np.float64)
    if rate != sr:
        g = np.gcd(rate, sr)
        y = resample_poly(y, sr // g, rate // g)
    return y


class Lane:
    """One lane's sampled hits, scaled so the loudest hit of its main instrument has the lane's LEVEL."""

    def __init__(self, lane: str, sr: int):
        self.inst, self.mic = LANES[lane]
        self.accent = ACCENT.get(lane)
        self.sr = sr
        powers, files = _hits(self.inst, self.mic)
        self.top = powers[-1]
        rms, sec = LEVEL[lane]
        loudest = _audio(self.inst, *files[-1], sr)[: int(sec * sr)]
        self.norm = rms / (np.sqrt(np.mean(loudest ** 2)) + 1e-12)
        self.last: dict[str, int] = {}
        self.tail = TAIL.get(lane)

    def hit(self, velocity: float, accent: bool, rng: np.random.Generator) -> np.ndarray:
        inst = self.accent if accent and self.accent else self.inst
        powers, files = _hits(inst, self.mic)
        target = self.top * max(velocity, 1e-3) ** DYNAMICS
        near = np.argsort(np.abs(np.log(powers) - np.log(target)))[:CHOICES]
        if len(near) > 1:
            near = near[near != self.last.get(inst, -1)]
        k = int(rng.choice(near))
        self.last[inst] = k
        # make up the difference between the wanted power and the hit's (within reason)
        gain = float(np.clip(np.sqrt(target / powers[k]), 0.5, 2.0))
        y = _audio(inst, *files[k], self.sr) * self.norm * gain
        return _faded(y, *self.tail, self.sr) if self.tail else y


def _faded(y: np.ndarray, hold: float, db_per_sec: float, sr: int) -> np.ndarray:
    """`y` with an extra exponential decay after `hold` seconds, cut where it is 80 dB down."""
    t = np.arange(len(y)) / sr - hold
    n = min(len(y), int((hold + 80.0 / db_per_sec) * sr))
    return (y * 10 ** (-db_per_sec * np.maximum(t, 0.0) / 20))[:n]
