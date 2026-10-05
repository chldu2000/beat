"""Render compiled events to stereo audio: per-part synthesis, then the mix (spec section 10).

Each part: engine -> automatic gain (the instrument type's target loudness) -> highpass -> EQ -> compressor
(make-up gain restores the RMS) -> fader -> pan -> master bus, plus a send to the shared room. Master:
glue compressor -> gain to the target loudness -> true-peak limiter. `mix=False` is the v0.1 path (gain,
pan, peak normalization), kept for A/B listening.
"""

import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import mix as mixing
from .compile import Compiled
from .synth.engine import render_part

SR = 44100
TAIL_SEC = 2.5
# Automatic gain staging: each part is normalized to this loudness (LUFS) before the user's mix gain. RMS
# targets (v0.1, still used with mix=False) let the drums sit some 7 LU over a guitar: their hits are short
# and peaky, so the same RMS sounds louder.
TARGET_LUFS = {"drums": -20.0, "bass": -20.0, "guitar": -20.0, "organ": -22.0, "piano": -20.0}
TARGET_RMS_DB = {"drums": -16.0, "bass": -18.0, "guitar": -20.0, "organ": -25.0, "piano": -21.0}
SEND_HPF_HZ = 150  # keep the lows out of the room, so the reverb doesn't muddy the bass and kick
ENVELOPE_SEC = 0.05  # resolution of the per-part levels kept for the report
LIMITER_WARN_DB = 6.0


@dataclass
class MixReport:
    loudness: float  # LUFS of the output
    true_peak_db: float
    limiter_db: float  # largest gain reduction of the limiter
    limiter_at: str  # where it happened
    limiter_part: str  # the loudest part there
    glue_db: float  # largest gain reduction of the glue compressor
    parts: dict[str, tuple[float, float]] = field(default_factory=dict)  # part -> (LUFS alone in the output, comp dB)
    warnings: list[tuple[str, str]] = field(default_factory=list)  # (where, message)

    def lines(self) -> list[str]:
        out = [f"mix: {self.loudness:.1f} LUFS, true peak {self.true_peak_db:.1f} dBTP, "
               f"glue compressor up to {self.glue_db:.1f} dB, limiter up to {self.limiter_db:.1f} dB"
               + (f" ({self.limiter_at}, loudest part {self.limiter_part})" if self.limiter_db >= 0.5 else "")]
        for pid, (lufs, comp) in self.parts.items():
            out.append(f"  {pid:<6} {lufs:6.1f} LUFS alone" + (f", compressor up to {comp:.1f} dB" if comp >= 0.05 else ""))
        return out


def render(compiled: Compiled, parts: list[str] | None = None, sr: int = SR, mix: bool = True) -> np.ndarray:
    return mixdown(compiled, parts, sr, mix)[0]


def mixdown(compiled: Compiled, parts: list[str] | None = None, sr: int = SR,
            mix: bool = True) -> tuple[np.ndarray, MixReport | None]:
    song = compiled.song
    settings: mixing.Mix = song.mix
    space = mixing.SPACES[settings.space] if mix else None
    seed = song.performance.get("seed", 0) if isinstance(song.performance, dict) else 0
    end = max((e.time + e.dur for e in compiled.events), default=compiled.duration_sec)
    tail = max(TAIL_SEC, space[0] + 0.5) if space else TAIL_SEC
    n = int((max(end, compiled.duration_sec) + tail) * sr)
    bus = np.zeros((n, 2))
    sends = np.zeros((n, 2))
    levels: dict[str, np.ndarray] = {}
    lufs: dict[str, float] = {}
    comp_db: dict[str, float] = {}

    for i, (pid, inst) in enumerate(song.instruments.items()):
        if parts and pid not in parts:
            continue
        events = [e for e in compiled.events if e.part == pid]
        if not events:
            continue
        rng = np.random.default_rng([int(seed), i])
        audio = render_part(inst, events, n, sr, rng, [c for c in compiled.controls if c.part == pid])
        strip = settings.parts[pid]
        if mix:
            audio, comp_db[pid] = _channel(_normalize_lufs(audio, TARGET_LUFS[inst.type], sr), strip, sr)
        else:
            audio = _normalize_rms(audio, TARGET_RMS_DB[inst.type])
            strip = mixing.Strip(gain_db=strip.gain_db, pan=strip.pan)
        audio = _pan(audio, strip.pan) * 10 ** (strip.gain_db / 20)
        bus += audio
        if space and mixing.REVERBS[strip.reverb] is not None:
            sends += audio * 10 ** (mixing.REVERBS[strip.reverb] / 20)
        levels[pid] = _envelope(audio, sr)
        if mix:
            from .synth.dynamics import loudness
            lufs[pid] = loudness(audio, sr)

    if not mix:
        peak = np.max(np.abs(bus))
        return (bus * 10 ** (-1 / 20) / peak if peak > 0 else bus), None
    if space:
        bus += _room(sends, space, sr)
    return _master(bus, settings, sr, compiled, levels, lufs, comp_db)


def _channel(audio: np.ndarray, strip: mixing.Strip, sr: int) -> tuple[np.ndarray, float]:
    """Highpass, EQ, compressor and peak catch; returns the audio and the compressor's largest gain
    reduction (dB)."""
    from .synth.dynamics import compress, limit
    from .synth.eq import equalize, highpass

    audio = equalize(highpass(audio, sr, strip.hpf), sr, strip.eq)
    rms = _active_rms(audio)
    if rms == 0:
        return audio, 0.0
    comp, comp_db = mixing.COMPS[strip.comp], 0.0
    if comp is not None:
        above, ratio, attack, release = comp
        audio, gr = compress(audio, sr, 20 * np.log10(rms) + above, ratio, attack, release)
        audio, comp_db = audio * rms / _active_rms(audio), float(gr.max())
    if strip.peak:
        audio = limit(audio, sr, 20 * np.log10(rms) + strip.peak, 2.0, mixing.PEAK_RELEASE_MS)[0]
    return audio, comp_db


def _room(sends: np.ndarray, space: tuple, sr: int) -> np.ndarray:
    """The shared room, scaled so that a send level is the reverb's energy against the dry part."""
    from .synth import room
    from .synth.eq import highpass

    rt60, rt60_high, predelay, size = space
    impulse = np.zeros((int((rt60 * 1.5 + 0.1) * sr), 2))
    impulse[0] = 1
    ir = room.reverb(impulse, sr, rt60, rt60_high, predelay, size)
    scale = np.sqrt(2 / np.sum(ir ** 2))
    return scale * room.reverb(highpass(sends, sr, SEND_HPF_HZ), sr, rt60, rt60_high, predelay, size)


def _master(bus: np.ndarray, settings: mixing.Mix, sr: int, compiled: Compiled,
            levels: dict[str, np.ndarray], lufs: dict[str, float],
            comp_db: dict[str, float]) -> tuple[np.ndarray, MixReport]:
    from .synth.dynamics import compress, limit, loudness, true_peak

    glue = mixing.STYLES[settings.style]
    glue_gr = np.zeros(1)
    if glue is not None and (rms := _active_rms(bus)) > 0:
        above, ratio, attack, release = glue
        bus, glue_gr = compress(bus, sr, 20 * np.log10(rms) + above, ratio, attack, release)

    gain_db = 0.0
    out, gr = limit(bus, sr, mixing.CEILING_DB)
    for _ in range(2):  # the limiter takes a little loudness off, so aim again
        now = loudness(out, sr)
        if not np.isfinite(now):
            break
        gain_db += settings.loudness - now
        out, gr = limit(bus * 10 ** (gain_db / 20), sr, mixing.CEILING_DB)

    at = int(np.argmax(gr))
    k = min(at // int(ENVELOPE_SEC * sr), min((len(v) for v in levels.values()), default=1) - 1)
    loudest = max(levels, key=lambda p: levels[p][k]) if levels else ""
    report = MixReport(
        loudness=loudness(out, sr), true_peak_db=float(20 * np.log10(max(true_peak(out).max(), 1e-12))),
        limiter_db=float(gr.max()), limiter_at=_where(compiled, at / sr), limiter_part=loudest,
        glue_db=float(glue_gr.max()))
    for pid, part_lufs in lufs.items():  # before the glue compressor and limiter, so roughly
        report.parts[pid] = (part_lufs + gain_db, comp_db.get(pid, 0.0))
    if report.limiter_db > LIMITER_WARN_DB:
        report.warnings.append((
            report.limiter_at,
            f"the master limiter pulls the mix down by {report.limiter_db:.1f} dB here ({loudest} is loudest), "
            f"which flattens the hits; lower mix > {loudest} > gain_db, or mix > master > loudness "
            f"(now {settings.loudness:g})"))
    return out, report


def _envelope(audio: np.ndarray, sr: int) -> np.ndarray:
    """Mean energy (both channels) in ENVELOPE_SEC blocks."""
    block = int(ENVELOPE_SEC * sr)
    e = np.sum(audio ** 2, axis=1)
    m = len(e) // block
    return e[: m * block].reshape(m, block).mean(axis=1)


def _where(compiled: Compiled, sec: float) -> str:
    """A time as `section#n > bar N, beat B`."""
    ins = compiled.instances[0]
    for x in compiled.instances:
        if x.start_sec <= sec:
            ins = x
    rel = compiled.sec_to_beat(sec) - float(ins.start_beat)
    bar_beats = float(compiled.song.bar_beats)
    bar = int(rel // bar_beats) + 1
    if bar > ins.section.bars:
        return f"{ins.name} > after the last bar"
    return f"{ins.name} > bar {bar}, beat {round((rel - (bar - 1) * bar_beats) * 4) / 4 + 1:g}"


def _active_rms(audio: np.ndarray) -> float:
    mono = audio if audio.ndim == 1 else audio.mean(axis=1)
    active = mono[np.abs(mono) > 1e-4]
    return float(np.sqrt(np.mean(active ** 2))) if active.size else 0.0


def _normalize_lufs(audio: np.ndarray, target: float, sr: int) -> np.ndarray:
    from .synth.dynamics import loudness

    now = loudness(audio, sr)
    return audio * 10 ** ((target - now) / 20) if np.isfinite(now) else audio


def _normalize_rms(audio: np.ndarray, target_db: float) -> np.ndarray:
    rms = _active_rms(audio)
    return audio * (10 ** (target_db / 20) / rms) if rms else audio


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
