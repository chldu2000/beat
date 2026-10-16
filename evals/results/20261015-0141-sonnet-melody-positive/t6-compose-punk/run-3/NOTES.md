# Notes

## What was hard or confusing
- SPEC.md is in Chinese, while the task and tool output are in English.
- It's unclear whether `hits` with several bars needs `|` after empty bars (I wrote `| |` in the outro and it validated).
- A bar's duration inherits from the previous note, so melody lines need care to sum to 4 beats. Validation catches mistakes, but only after the fact.
- I couldn't hear the result, so melodic choices rest on theory alone.

## Workarounds
- Rhythm guitar bars are written out in full (`([D3 A3]:8!pm)*8`), because patterns can't take a chord argument.
- The chorus ride (`rd`) plus an added `cr` stand in for open hats and a crash, which avoids the hand-count conflict with the snare.

## Wishes
- Generate rhythm guitar and bass from `chords` with a style (power-chord 8ths, root 8ths).
- Parameterised patterns, e.g. a root-note argument.
- A `beat check-melody` command that reports chord-tone and scale-tone stats against `chords`.
