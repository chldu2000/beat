# Notes

## What was hard or confusing
- SPEC.md is in Chinese, while the task and tool output are in English.
- Guitar chord playability is only checked at validation time. I had to guess which power-chord shapes would pass (they did).
- Bass register: no feedback on which octave sounds right. I kept to E1 and above.
- Melody writing without audio: I could only judge phrasing by counting beats.

## Workarounds
- The lead is written bar by bar, with ties inside a bar (`E4:2~ E4:4!vib`) to get a held, vibrato note followed by a rest.
- Verse and chorus drums use `replace` for the fill bar and `add` for crashes. The outro drums are explicit `hits` with empty bars.
- Intro lead silence is written as `r:1` bars, since a part can't start partway through a section.

## Wishes
- Auto-generate power-chord or bass-root parts from the `chords` line.
- `beat validate` checking melody notes against `chords` (flagging non-chord tones on strong beats).
- A bar-count and form summary command.
- An English version of the spec.
