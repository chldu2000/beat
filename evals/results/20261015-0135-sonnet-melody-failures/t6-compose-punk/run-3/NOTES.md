# Notes

## What was hard or confusing
- SPEC.md is in Chinese while the task and tooling are in English, so I had to translate as I read.
- It wasn't obvious whether `add` (a crash on beat 1) would clash with `hh` on the same beat. The "two hands" rule is only spelled out in prose.
- A tied note can't cross a bar line, so a 3-beat note plus a rest needed `:b3`.
- I couldn't hear the result, so melody quality is judged only from the note listing.

## Workarounds
- Used `D5:b3!vib r:4` for the held final chorus note instead of a tie.
- Used the 8-bar `fill` pattern with `replace` for section-end drum fills.
- Wrote power chords by hand instead of calling `beat voicing`.

## Wishes
- A way to repeat a chord or pattern across bars without writing `%` or repeating text (e.g. `(...)*8 | %` works but is wordy).
- Per-section mix or dynamics automation.
- Validation of melody notes against the section's `chords` (a warning for non-chord tones on strong beats in pitched lead parts).
- An English version of the spec.
