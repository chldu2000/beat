"""Describe a reference song as a plain note list, for transcription tasks.

The description is deliberately not in Beat DSL: the agent must translate it.

    uv run python -m evals.describe evals/refs/riff.beat.yaml
"""

import sys
from collections import defaultdict
from itertools import groupby
from pathlib import Path

from beat.pitch import pitch_name
from beat.song import Song

from .score import base_dynamic, fmt_len, fmt_pos, load, score_events

ART_NAMES = {
    "pm": "palm-muted", "x": "dead note", "st": "staccato", "acc": "accented", "h": "hammer-on",
    "p": "pull-off", "sl": "slide into this note", "vib": "vibrato", "harm": "natural harmonic",
    "ghost": "ghost note", "flam": "flam",
}
LANE_NAMES = {
    "bd": "kick", "sd": "snare", "ss": "side stick", "hh": "closed hi-hat", "ho": "open hi-hat",
    "hp": "hi-hat pedal", "t1": "high tom", "t2": "mid tom", "t3": "floor tom", "cr": "crash",
    "cr2": "crash 2", "rd": "ride", "rb": "ride bell", "ch": "china",
}


def _arts(arts: dict) -> str:
    names = [f"bend up {v:g} semitone(s)" if k == "bend" else ART_NAMES[k] for k, v in arts.items()]
    return ", ".join(names)


def describe(song: Song) -> str:
    bb = song.bar_beats
    lines = [
        f"Time signature {song.time[0]}/{song.time[1]}. Positions are 'bar N, beat B' counted from 1; "
        f"lengths are in beats (1 beat = a quarter note). A length can run past the barline: "
        f"then the note is held into the next bar(s).",
        "",
        "Parts:",
    ]
    for pid, inst in song.instruments.items():
        extra = f", tone {inst.tone}" if inst.tone else ""
        lines.append(f"- {pid}: {inst.type}{extra}")

    lines += ["", "Tempo and chords:"]
    bar = 1
    for sid in song.form:
        s = song.sections[sid]
        chords = " | ".join(" ".join(c.symbol for c in bar_chords) for bar_chords in s.chords) \
            if s.chords else "(none given)"
        lines.append(f"- bars {bar}-{bar + s.bars - 1}: {s.tempo:g} BPM, chords {chords}")
        bar += s.bars

    events = score_events(song)
    by_part = defaultdict(list)
    for e in events:
        by_part[e.part].append(e)

    for pid, inst in song.instruments.items():
        lines += ["", f"## {pid} ({inst.type})"]
        part_events = sorted(by_part.get(pid, []), key=lambda e: (e.beat, e.pitch))
        if not part_events:
            lines.append("(does not play)")
            continue
        dynamic = None
        for bar_idx, bar_events in groupby(part_events, key=lambda e: int(e.beat // bb)):
            items = []
            for onset, group in groupby(bar_events, key=lambda e: e.beat):
                group = list(group)
                dyn = base_dynamic(group[0])
                pos = fmt_pos(onset - bar_idx * bb + 1)
                prefix = f"[dynamic {dyn} from here] " if dyn != dynamic else ""
                dynamic = dyn
                if inst.pitched:
                    notes = " ".join(pitch_name(e.pitch) for e in group)
                    what = f"chord {notes}" if len(group) > 1 else notes
                    arts = _arts(group[0].arts)
                    items.append(f"{prefix}beat {pos}: {what}, {fmt_len(group[0].beats)}"
                                 + (f", {arts}" if arts else ""))
                else:
                    hits = [LANE_NAMES[e.lane] + (f" ({_arts(e.arts)})" if e.arts else "") for e in group]
                    items.append(f"{prefix}beat {pos}: {', '.join(hits)}")
            lines.append(f"bar {bar_idx + 1}: " + "; ".join(items))
    return "\n".join(lines) + "\n"


def main() -> int:
    diags, song, _ = load(Path(sys.argv[1]))
    if diags.has_errors or song is None:
        for d in diags.errors:
            print(d, file=sys.stderr)
        return 1
    print(describe(song), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
