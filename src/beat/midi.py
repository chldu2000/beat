"""Export compiled events to a standard MIDI file (performed timing, GM programs)."""

import mido

from .compile import Compiled

TPB = 480
PROGRAMS = {"bass": 33, "organ": 16, "piano": 0}
GUITAR_PROGRAMS = {"clean": 27, "crunch": 29, "lead": 30}


def export_midi(compiled: Compiled, path: str) -> None:
    song = compiled.song
    mid = mido.MidiFile(ticks_per_beat=TPB)

    def tick(sec: float) -> int:
        return max(0, round(compiled.sec_to_beat(sec) * TPB))

    conductor = [(0, mido.MetaMessage("track_name", name=song.meta.get("title") or "beat")),
                 (0, mido.MetaMessage("time_signature", numerator=song.time[0], denominator=song.time[1]))]
    for ins in compiled.instances:
        conductor.append((round(float(ins.start_beat) * TPB),
                          mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(ins.section.tempo))))
    mid.tracks.append(_to_track(conductor))

    channels = iter(c for c in range(16) if c != 9)
    for pid, inst in song.instruments.items():
        channel = 9 if inst.type == "drums" else next(channels, 0)
        msgs = [(0, mido.MetaMessage("track_name", name=pid))]
        if inst.type != "drums":
            program = GUITAR_PROGRAMS[inst.tone] if inst.type == "guitar" else PROGRAMS[inst.type]
            msgs.append((0, mido.Message("program_change", channel=channel, program=program)))
        for ev in compiled.events:
            if ev.part != pid:
                continue
            vel = max(1, round(ev.velocity * 127))
            on, off = tick(ev.time), tick(ev.time + ev.dur)
            msgs.append((on, mido.Message("note_on", channel=channel, note=ev.pitch, velocity=vel)))
            msgs.append((max(off, on + 1), mido.Message("note_off", channel=channel, note=ev.pitch, velocity=0)))
        mid.tracks.append(_to_track(msgs))
    mid.save(path)


def _to_track(msgs: list[tuple[int, mido.Message]]) -> mido.MidiTrack:
    # note_off before note_on at the same tick so repeated notes are not cut.
    msgs.sort(key=lambda m: (m[0], 0 if m[1].type == "note_off" else 1))
    track = mido.MidiTrack()
    now = 0
    for t, msg in msgs:
        track.append(msg.copy(time=t - now))
        now = t
    return track
