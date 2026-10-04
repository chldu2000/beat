"""Render compiled events to stereo audio: per-part synthesis, gain staging, pan, master."""

import wave
from pathlib import Path

import numpy as np

from .compile import Compiled
from .synth.engine import render_part

SR = 44100
TAIL_SEC = 2.5
# Automatic gain staging: each part is normalized to this RMS (dBFS) before the user's mix gain.
TARGET_RMS_DB = {"drums": -16.0, "bass": -18.0, "guitar": -20.0, "organ": -25.0, "piano": -21.0}


def render(compiled: Compiled, parts: list[str] | None = None, sr: int = SR) -> np.ndarray:
    song = compiled.song
    seed = song.performance.get("seed", 0) if isinstance(song.performance, dict) else 0
    end = max((e.time + e.dur for e in compiled.events), default=compiled.duration_sec)
    n = int((max(end, compiled.duration_sec) + TAIL_SEC) * sr)
    master = np.zeros((n, 2))
    mix = song.mix if isinstance(song.mix, dict) else {}

    for i, (pid, inst) in enumerate(song.instruments.items()):
        if parts and pid not in parts:
            continue
        events = [e for e in compiled.events if e.part == pid]
        if not events:
            continue
        rng = np.random.default_rng([int(seed), i])
        audio = render_part(inst, events, n, sr, rng, [c for c in compiled.controls if c.part == pid])
        audio = _normalize_rms(audio, TARGET_RMS_DB[inst.type])
        cfg = mix.get(pid) or {}
        gain = 10 ** (float(cfg.get("gain_db", 0)) / 20)
        master += _pan(audio, float(cfg.get("pan", 0))) * gain

    master *= 10 ** (float((mix.get("master") or {}).get("gain_db", 0)) / 20)
    peak = np.max(np.abs(master))
    if peak > 0:
        master *= 10 ** (-1 / 20) / peak
    return master


def _normalize_rms(audio: np.ndarray, target_db: float) -> np.ndarray:
    mono = audio if audio.ndim == 1 else audio.mean(axis=1)
    active = mono[np.abs(mono) > 1e-4]
    if active.size == 0:
        return audio
    rms = np.sqrt(np.mean(active ** 2))
    return audio * (10 ** (target_db / 20) / rms)


def _pan(audio: np.ndarray, pan: float) -> np.ndarray:
    """Constant-power pan for mono parts; balance for stereo parts."""
    pan = float(np.clip(pan, -1, 1))
    left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    if audio.ndim == 1:
        return np.stack([audio * left, audio * right], axis=1)
    return audio * np.array([left, right]) * np.sqrt(2)


def write_wav(path: str | Path, audio: np.ndarray, sr: int = SR) -> None:
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
