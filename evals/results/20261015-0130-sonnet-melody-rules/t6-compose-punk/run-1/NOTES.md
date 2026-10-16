# Notes

## 1. What was hard or confusing
- SPEC.md is written in Chinese, while the task prompt and tool output are in English.
- A note cannot cross a barline, so a held note plus rest needs careful beat arithmetic. I miscounted twice (5-beat bars); the validator caught both.
- A tie must join identical pitches. I wrote `C#5:2~` at the end of a section by mistake, and the error only said the next note was A4.
- The bass "not a chord tone" warning depends on `chords` granularity, so a bar with a half-bar chord change needs a chord split.
- I couldn't hear the result, so groove and melody choices are untested by ear.

## 2. Workarounds
- Power chords are written as 2- or 3-note `[...]` chords by hand, since `chords:` generates nothing.
- The long chord-by-chord riffs live in `patterns` (`gt_verse`, `bs_verse`, `bs_chorus`) and are reused across both verses.
- A "held note, then breath" is written as a tie, then `r:4`, so the bar still sums to 4.

## 3. Wishes
- Auto-generate rhythm parts from `chords:` (power-chord eighths, root-note bass).
- A `beats remaining` hint in bar-duration errors showing where the bar overflows.
- Say in tie errors which note the tie came from, and mention a missing following section.
- Pattern parameters, e.g. a riff with a chord-root argument.
- A lint for the melody: held note length in seconds, and chord-tone vs tension per strong beat.
