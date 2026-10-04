"""Render guitar and bass audition clips with the waveguide engine and the old Karplus-Strong one.

    uv run python scripts/audition.py [out/audition]

Each clip is written twice, `NN_name.new.wav` and `NN_name.old.wav`, plus the demo song.
"""

import sys
from pathlib import Path

from beat.cli import _load
from beat.compile import compile_song
from beat.diagnostics import Diagnostics
from beat.render import render, write_wav
from beat.song import load_song

# (name, guitar tone or "bass", bars of notes, what to listen for)
CLIPS = [
    ("single_clean", "clean", "E2:1 | A3:1 | E4:1 | E5:1",
     "Single notes, clean: attack, tuning, how the sustain darkens as it decays."),
    ("single_crunch", "crunch", "E2:1 | A3:1 | E4:1 | E5:1",
     "The same notes through the crunch amp."),
    ("chug", "crunch", "(E2:8!pm)*6 G2:8 A2:8 | (E2:8!pm)*4 E2:4 r:4",
     "Palm-muted chugs, then an open note that rings and is released."),
    ("dead_notes", "crunch", "E2:8!pm E2:8!x E2:8!pm E2:8!x [E2 B2 E3]:8 [E2 B2 E3]:8!x [E2 B2 E3]:4 | r:1",
     "Dead (fully muted) notes between palm mutes and chords."),
    ("legato", "lead", "A3:8 B3:8!h A3:8!p G3:8 A3:4 C4:8 D4:8!h | D4:8!p C4:8 A3:4 A3:2",
     "Hammer-ons and pull-offs: only the first note of each slur is picked."),
    ("open_chords", "clean", "[E2 B2 E3 G#3 B3 E4]:1 | [C3 E3 G3 C4 E4]:1 | [G2 B2 D3 G3 B3 G4]:1 | [A2 E3 A3 C4 E4]:1",
     "Strummed open chords, clean: strings ring together, no note cuts another."),
    ("power_chords", "crunch", "[E2 B2 E3]:4 [E2 B2 E3]:8 [G2 D3 G3]:8 r:8 [A2 E3 A3]:8 [A2 E3 A3]:4 | [B2 F#3 B3]:1",
     "Power chords through crunch, with short releases between them."),
    ("lead_line", "lead", "E4:8 G4:8 A4:4 B4:8 A4:8 G4:8 E4:8 | D4:8 E4:8 G4:4 E4:2",
     "A lead line through the lead amp."),
    ("bass_single", "bass", "E1:1 | A1:1 | D2:1 | G2:1",
     "Bass single notes: low end, attack (hard notes start slightly sharp), sustain."),
    ("bass_line", "bass", "E1:8 E1 B1 E1 E2 E1 B1 D2 | A1:8 A1 E2 A1 G1 G1 D2 G1",
     "Eighth-note root-fifth line: evenness, how each note stops the previous one."),
    ("bass_mutes", "bass", "(E1:8!pm)*4 E1:8!x E1:8 G1:8 A1:8 | (A1:8!pm)*4 A1:8!x A1:8 E1:4",
     "Palm-muted and dead bass notes."),
    ("bass_legato", "bass", "E1:8 G1:8!h A1:4 A1:8 G1:8!p E1:4 | E1:1",
     "Bass hammer-ons and pull-offs."),
]

TEMPLATE = """beat: 0.1
meta: {{ title: {name}, tempo: 100, time: 4/4 }}
instruments:
  {pid}: {{ {spec} }}
sections:
  a:
    bars: {bars}
    parts:
      {pid}: {{ notes: "{notes}" }}
form: [a]
"""


def render_both(song, compiled, path: Path, parts=None) -> None:
    for engine, suffix in (("waveguide", "new"), ("ks", "old")):
        for inst in song.instruments.values():
            if inst.type in ("guitar", "bass"):
                inst.model = {**inst.model, "engine": engine}
        write_wav(path.with_suffix(f".{suffix}.wav"), render(compiled, parts))


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out/audition")
    out.mkdir(parents=True, exist_ok=True)
    notes_md = ["# Guitar and bass audition", "",
                "Each clip: `.new.wav` (waveguide) and `.old.wav` (Karplus-Strong).", ""]
    for i, (name, tone, notes, listen) in enumerate(CLIPS, 1):
        pid, spec = ("bs", "type: bass") if tone == "bass" else ("gt", f"type: guitar, tone: {tone}")
        text = TEMPLATE.format(name=name, pid=pid, spec=spec, bars=notes.count("|") + 1, notes=notes)
        diags = Diagnostics()
        song = load_song(text, diags)
        compiled = compile_song(song, diags) if song else None
        if diags.has_errors or compiled is None:
            print(f"{name}:", *map(str, diags.items), sep="\n  ")
            return 1
        render_both(song, compiled, out / f"{i:02d}_{name}")
        notes_md.append(f"{i:02d}. **{name}** ({tone}): {listen}")
        print(f"{i:02d}_{name}")

    _, song, compiled = _load("examples/demo.beat.yaml")
    for name, itype in (("90_demo_guitars", "guitar"), ("91_demo_bass", "bass")):
        render_both(song, compiled, out / name, [p for p, i in song.instruments.items() if i.type == itype])
    render_both(song, compiled, out / "92_demo_full")
    notes_md += ["90. **demo_guitars**: both demo guitar parts without the band.",
                 "91. **demo_bass**: the demo bass part alone.", "92. **demo_full**: the whole demo."]
    (out / "README.md").write_text("\n".join(notes_md) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
