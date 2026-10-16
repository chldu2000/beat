# Notes

## 1. What was hard or confusing
- SPEC.md is written in Chinese while the task and tool output are in English.
- Counting eighth notes by hand in the riff (I wrote 9 in one bar). The error message was clear, though.
- A tie needs a following note in the same part, so a section can't end on a tied note unless the next section continues it. This isn't obvious for the last section.
- Hand limits for drums (crash + hat + snare) aren't visible until validation, so I used the ride for the chorus.

## 2. Workarounds
- Chorus 2 is a separate section (`chorus_last`, via `extends`) so gt2 plays only there.
- Drum fills are `replace`d into the last bar of a section instead of being separate sections.
- The outro ends on untied whole notes, because ties can't dangle.

## 3. Wishes
- A `beat events --by-bar` style check inside `validate` for the sum of beats per bar, with the offending token.
- A shorthand for "power chord" that expands per chord symbol, e.g. `@chord` taken from `chords:`.
- A warning when gt2 is silent in a whole section, or a lead is below the rhythm guitar's register.
- An English edition of the spec.
