# Notes

## What was hard or confusing
- SPEC.md is written in Chinese while the task and tool output are English; that slowed the first read.
- Bar durations have to be exact. There is no helper to show how many beats a bar has left, so I summed lengths by hand.
- It was unclear how `!fall` and `!vib` behave on a final note when no tie follows. I assumed they work on a single note.
- `chords` is only used for checks and warnings. The parts still have to be spelled out by hand, so the chord list and the notes can drift apart.
- I couldn't hear the result, so I had no way to judge whether a rhythm or melody sounds good, only whether it is valid.

## Workarounds
- I wrote repeated power-chord eighths as `([D3 A3]:8!pm)*8`, once per bar, because `!pm` doesn't carry over to later notes.
- Each section repeats its own chord-root bass line, since there is no way to make bass follow `chords`.
- I used the `fill` pattern with `replace` for the last bar of a section, and `add` for the crashes, so the base groove stays in one place.
- The outro drums use `hits` with empty bars, because one bar needs a different feel from the others.

## Wishes
- Generating bass roots and power-chord strums from `chords` (for example `auto: eighths-root`) would remove most of the repetitive text.
- `beat events --by-bar` could also report each bar's total duration, and `validate` could show a clearer "N beats short" hint.
- Per-note ornament shorthand for pickup notes into the next bar.
- A text preview of melody contour, or interval analysis against the chord (`beat analyze`), to check chord-tone use without listening.
