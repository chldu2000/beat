# Notes

## What was hard or confusing
- SPEC.md is mostly in Chinese, while the tool messages are in English.
- It wasn't obvious that `extends` only allows one level and that `parts` merge per part. I got this from the spec, not from an error.
- Bar durations need careful counting by hand. I got one 4.5-beat bar wrong in a chorus (the validator caught it).
- The spec doesn't say whether a section used only through `extends` (chorus2) still counts as "the chorus" for a repeat. I made it a variant of chorus.

## Workarounds
- The lead only plays in the last chorus, so I made a `chorus2` section that extends `chorus` and overrides only `gt2`.
- I typed power-chord voicings by hand instead of calling `beat voicing`. They validated fine.
- I wrote the fills as a reusable drum pattern and used it with `replace` on the last bar of sections.

## Wishes
- A `repeat`/`x2` shorthand for a whole section's part, or a per-instance override in `form`, so a variant section isn't needed.
- A bar-duration hint in the validator, such as a running total per bar.
- Automatic chord-to-power-chord helpers driven by the `chords` field.
