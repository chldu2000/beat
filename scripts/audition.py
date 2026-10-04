"""Render guitar, bass, organ and drum audition clips with the new engines and the old placeholder ones.

    uv run python scripts/audition.py [out/audition] [name filter]

Each clip is written twice, `NN_name.new.wav` and `NN_name.old.wav`, plus the demo song. With a filter,
only clips whose name contains it are rendered (e.g. `tom` or `demo`).
"""

import sys
from pathlib import Path

from beat.cli import _load
from beat.compile import compile_song
from beat.diagnostics import Diagnostics
from beat.render import render, write_wav
from beat.song import load_song

# instrument type -> (new engine, old engine)
ENGINES = {"guitar": ("waveguide", "ks"), "bass": ("waveguide", "ks"), "organ": ("tonewheel", "drawbar"),
           "drums": ("modal", "kit")}

# (name, guitar tone, "bass", "organ:<registration>" or "drums", bars of notes, what to listen for). For the
# organ, `notes` may be a list of (leslie speed, notes) sections; for drums it is `hits` lines.
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
    ("organ_chords", "organ:rock", "[E3 B3 E4 G4]:1 | [C3 G3 C4 E4]:1 | [D3 A3 D4 F#4]:1 | [A2 E3 A3 C4]:1",
     "Held chords, rock registration, Leslie slow: tonewheel body, key click, the slow swirl."),
    ("organ_leslie_ramp", "organ:rock",
     [("slow", "[E3 B3 E4 G4]:1~ | [E3 B3 E4 G4]:1~"),
      ("fast", "[E3 B3 E4 G4]:1~ | [E3 B3 E4 G4]:1~ | [E3 B3 E4 G4]:1~"),
      ("slow", "[E3 B3 E4 G4]:1~ | [E3 B3 E4 G4]:1~ | [E3 B3 E4 G4]:1")],
     "One held chord: Leslie slow -> fast -> slow. The horn gets there in about a second, the drum lags."),
    ("organ_percussion", "organ:jazz",
     "C4:8 E4:8 G4:8 A4:8 r:8 G4:8 E4:4 | [D3 F3 A3 C4]:4!st r:8 [D3 F3 A3 C4]:8 r:2",
     "Jazz registration with 3rd-harmonic percussion: the 'pop' at each detached note."),
    ("organ_riff", "organ:rock",
     [("fast", "@ff [E3 B3]:8 [E3 B3]:8 [G3 D4]:8 [A3 E4]:4 [E3 B3]:8 [D4 A4]:8 [C#4 G#4]:8 | [A3 E4]:2 r:2")],
     "A ff riff, Leslie fast: overdrive grit."),
    ("organ_dynamics", "organ:rock", "@p [E3 B3 E4]:1 | @mf [E3 B3 E4]:1 | @ff [E3 B3 E4]:1 | r:1",
     "The same chord at p, mf, ff: the expression pedal makes it louder and dirtier."),
    ("organ_soft", "organ:soft", "[C4 E4 G4]:1 | [A3 C4 E4]:1 | [F3 A3 C4]:1 | [G3 B3 D4]:1",
     "Soft registration for ballads: mellow, almost clean."),
    ("tom_singles", "drums",
     ["t1: 1 2!ghost 3!acc | | |", "t2: | 1 2!ghost 3!acc | |", "t3: | | 1 2!ghost 3!acc | 1"],
     "Each tom at mf, ghost and accent, then the floor tom left to ring: pitch glide on hard hits, decay."),
    ("tom_fill", "drums",
     ["hh: 1 1.5 2 2.5 3 3.5 4 4.5 | |", "bd: 1 3 | | 1", "sd: 2 4 | 1 1.25 1.5 1.75 |",
      "t1: | 2 2.25 2.5 2.75 |", "t2: | 3 3.25 3.5 3.75 |", "t3: | 4 4.25 4.5 4.75!acc |", "cr: | | 1!acc"],
     "A groove bar, a sixteenth-note fill down the toms, a crash: toms within the kit."),
    ("tom_rolls", "drums",
     ["t2: 1!flam 2!flam 3!flam 4!flam | |",
      "t3: | 1!ghost 1.125!ghost 1.25!ghost 1.375 1.5 1.625 1.75 1.875 2 2.125 2.25 2.375 2.5 2.625 2.75 2.875"
      " 3 3.125 3.25 3.375 3.5!acc 3.625!acc 3.75!acc 3.875!acc 4!acc | 1!acc"],
     "Flams, then a 32nd-note crescendo on the floor tom: each stroke lands on the ringing head."),
    ("tom_groove", "drums",
     ["t3: 1!acc 1.5 2 2.5!acc 3 3.5 4!acc 4.5 | 1!acc 1.5 2 2.5!acc 3 3.5 4!acc 4.5",
      "bd: 1 2.5 3 | 1 2.5 3", "t2: 4.75 | 4.25 4.5 4.75", "ss: 2 4 | 2 4"],
     "A floor-tom groove with side stick: steady eighths shouldn't sound like a machine gun."),
    ("kick_singles", "drums", ["bd: 1!ghost 2 3!acc | 1 | 1!acc |"],
     "Bass drum soft, medium, accented, then left to ring: low end, beater attack, pitch drop on hard hits."),
    ("kick_rock", "drums",
     ["hh: 1 1.5 2 2.5 3 3.5 4 4.5 | 1 1.5 2 2.5 3 3.5 4 4.5", "sd: 2 4 | 2 4", "bd: 1 2.5 3 | 1 1.75 2.5 3 3.75"],
     "A rock beat with sixteenth-note doubles: punch, and whether the kick sits under the snare."),
    ("kick_doubles", "drums", ["bd: 1 1.25 1.5 1.75 2 2.25 2.5 2.75 3 3.25 3.5 3.75 4 4.25 4.5 4.75 | 1 1.25 1.5 1.75 2 2.25 2.5 2.75 3 3.25 3.5 3.75 4 4.25 4.5 4.75", "cr: 1!acc | 1!acc"],
     "Sixteenth-note double bass: each stroke lands on the moving head; it should stay defined, not smear."),
    ("snare_singles", "drums", ["sd: 1!ghost 2 3!acc | 1!ghost 1.5!ghost 2 3!acc |"],
     "Snare ghost, normal, accent, then left to ring: how much the wires buzz at each level, the tail."),
    ("snare_groove", "drums",
     ["hh: 1 1.5 2 2.5 3 3.5 4 4.5 | 1 1.5 2 2.5 3 3.5 4 4.5",
      "sd: 1.75!ghost 2!acc 2.5!ghost 3.25!ghost 4!acc 4.75!ghost | 1.75!ghost 2!acc 2.75!ghost 3.5!ghost 4!acc",
      "bd: 1 2.25 3 3.5 | 1 2.5 3.75"],
     "A funk groove with ghost notes: ghosts quiet but still with some wire, backbeats cracking."),
    ("snare_roll", "drums", ["sd: 1!flam 2!flam 3!flam 4!flam | 1!ghost 1.125!ghost 1.25!ghost 1.375!ghost 1.5!ghost 1.625!ghost 1.75!ghost 1.875!ghost 2 2.125 2.25 2.375 2.5 2.625 2.75 2.875 3 3.125 3.25 3.375 3.5 3.625 3.75 3.875 4!acc 4.125!acc 4.25!acc 4.375!acc 4.5!acc 4.625!acc 4.75!acc 4.875!acc | 1!acc", "cr: | | 1!acc", "bd: | | 1"],
     "Flams, then a 32nd-note roll from ghost to accent: the wires keep buzzing through the roll."),
    ("snare_backbeat", "drums",
     ["hh: 1 1.5 2 2.5 3 3.5 4 4.5 | 1 1.5 2 2.5 3 3.5 4 4.5", "sd: 2 4 | 2 4 4.75", "bd: 1 2.5 3 | 1 2.5 3"],
     "A plain rock beat: the snare's crack and body against the kick."),
    ("kit_sympathy", "drums",
     ["bd: 1 2.5 3 | 1 2.5 3 |", "t1: | 1 2 | 1!acc", "t2: | 3 | 2!acc", "t3: | 4 4.5 | 3!acc 4!acc"],
     "No snare is played: the snare wires should buzz along with the kick and toms, the toms ring along."),
    ("kit_room", "drums",
     ["hh: 1 1.5 2 2.5 3 3.5 4 4.5 | 1 1.5 2 2.5 3 3.5 4 4.5 | |",
      "sd: 2 4 | 2 4 | 1 1.25 1.5 1.75 |", "bd: 1 2.5 3 | 1 2.5 3 | | 1",
      "t1: | | 2 2.25 2.5 2.75 |", "t2: | | 3 3.25 |", "t3: | | 3.5 3.75 4 4.5!acc |", "cr: 1!acc | | | 1!acc"],
     "The kit in its room: overheads (the kit spread left to right) and the room tail after the last crash."),
    ("cymbals", "drums",
     ["hh: 1 1.5!acc 2 2.5!acc 3 3.5!acc 4 | 1 1.5 2 2.5 3 3.5 | |",
      "ho: 4.5 | 4 | |", "hp: | 1 2 3 4 | |", "rd: | | 1 1.5 2 3 3.5 4 | 1 2 3",
      "rb: | | 2.5 4.5 | ", "cr: 1!acc | | | 4!acc", "cr2: | | 1!acc |", "sd: 2 4 | 2 4 | 2 4 | 2", "bd: 1 3 | 1 3 | 1 3 | 1"],
     "Sampled hi-hat (accents on the shank, open and choked, pedal), ride with bell, both crashes."),
]

TEMPLATE = """beat: 0.1
meta: {{ title: {name}, tempo: 100, time: 4/4 }}
instruments:
  {pid}: {{ {spec} }}
sections:
{sections}
form: [{form}]
"""


def clip_song(name: str, kind: str, notes) -> str:
    if kind == "drums":
        lines = "\\n".join(notes)
        bars = notes[0].count("|") + 1
        return TEMPLATE.format(name=name, pid="dr", spec="type: drums", form="s0",
                               sections=f"  s0:\n    bars: {bars}\n    parts:\n      dr: {{ hits: \"{lines}\" }}")
    if kind == "bass":
        pid, spec = "bs", "type: bass"
    elif kind.startswith("organ:"):
        pid, spec = "org", f"type: organ, model: {{ registration: {kind[6:]} }}"
    else:
        pid, spec = "gt", f"type: guitar, tone: {kind}"
    parts = notes if isinstance(notes, list) else [(None, notes)]
    sections = []
    for i, (speed, text) in enumerate(parts):
        extra = f"leslie: {speed}, " if speed else ""
        sections.append(f"  s{i}:\n    bars: {text.count('|') + 1}\n    parts:\n"
                        f"      {pid}: {{ {extra}notes: \"{text}\" }}")
    return TEMPLATE.format(name=name, pid=pid, spec=spec, sections="\n".join(sections),
                           form=", ".join(f"s{i}" for i in range(len(parts))))


def render_both(song, compiled, path: Path, parts=None) -> None:
    for k, suffix in ((0, "new"), (1, "old")):
        for inst in song.instruments.values():
            if inst.type in ENGINES:
                inst.model = {**inst.model, "engine": ENGINES[inst.type][k]}
        write_wav(path.with_suffix(f".{suffix}.wav"), render(compiled, parts))


DEMOS = [  # (name, instrument type or None for the whole band, what it is)
    ("90_demo_guitars", "guitar", "both demo guitar parts without the band."),
    ("91_demo_bass", "bass", "the demo bass part alone."),
    ("92_demo_full", None, "the whole demo."),
    ("93_demo_organ", "organ", "the demo organ part alone."),
    ("94_demo_drums", "drums", "the demo drum part alone."),
]


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out/audition")
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    out.mkdir(parents=True, exist_ok=True)
    notes_md = ["# Guitar, bass, organ and drum audition", "",
                "Each clip: `.new.wav` (waveguide / tonewheel / modal toms) and `.old.wav` "
                "(Karplus-Strong / old drawbar / old kit).", ""]
    for i, (name, tone, notes, listen) in enumerate(CLIPS, 1):
        if only not in name:
            continue
        text = clip_song(name, tone, notes)
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
    for name, itype, what in DEMOS:
        if only not in name:
            continue
        parts = [p for p, i in song.instruments.items() if i.type == itype] if itype else None
        render_both(song, compiled, out / name, parts)
        notes_md.append(f"{name[:2]}. **{name[3:]}**: {what}")
        print(name)
    if not only:
        (out / "README.md").write_text("\n".join(notes_md) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
