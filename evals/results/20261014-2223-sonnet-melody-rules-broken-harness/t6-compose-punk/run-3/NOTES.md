# Notes

Caveat: the Bash tool was denied in this session (don't-ask mode), so I could not run `beat validate` or `beat events`. The song was written from SPEC.md and the demo only, and has not been validated.

## 1. What was hard or confusing
- I could not run any `beat` command, so every bar total and guitar fingering is unchecked.
- SPEC.md is in Chinese while the task and tooling are in English.
- Whether `r:4` after a `:8` note picks up the new duration (durations carry over) is easy to get wrong. I wrote a length on every token to avoid it.
- The "max 2 hands" drum rule is easy to hit when adding a crash on top of hi-hat plus snare.

## 2. Workarounds
- Power-chord shapes were copied from the demo (`[D3 A3 D4]` and similar) instead of using `beat voicing`.
- The outro's last bar is a drum `replace` with only crash and kick.
- A `!fall` on a held note is written as a tie (`D5:2~ D5:4!fall`).

## 3. Wishes
- Auto-generated rhythm patterns from the `chords:` line, e.g. "pm eighths on the root".
- A shorthand for a power chord, e.g. `D5` as a note token.
- Chord-tone checking for the lead against `chords`.
- An English version of the spec.
