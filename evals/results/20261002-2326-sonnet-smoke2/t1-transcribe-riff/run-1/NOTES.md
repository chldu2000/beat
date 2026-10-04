# Notes

## 1. What was hard or confusing

- Figuring out exactly how a tied note (`~`) compiles was not obvious from
  the spec text alone — it wasn't clear whether a tie produces one merged
  event or two separate note-ons. Had to check with `beat events` to confirm
  it merges into a single sustained event with combined duration.
- A rhythm with a silent gap in the middle (e.g. notes landing on beat 1,
  2.5, 3.5, 4 with nothing at beat 3) is easy to get wrong by just
  concatenating the written note durations — you have to notice the implicit
  rest yourself and insert an explicit `r:8`, since the DSL has no "skip to
  this beat" notation.
- The grid step size being tied to `beats * 4` (sixteenth notes) means any
  rhythm finer than a sixteenth, or any beat subdivision that doesn't land on
  a sixteenth boundary, has no obvious representation; luckily everything
  here lined up on sixteenths.

## 2. Workarounds

- Used `r:8` (an explicit rest) to represent the silent half-beat gaps in the
  bass/guitar bar-4 rhythms, since there is no shorthand for "this beat
  simply isn't played."
- Represented "a note that's 2.5 beats long" as a tie between a half note and
  an eighth note (`F1:2~ F1:8`), since there's no single duration token for
  2.5 beats.
- For drum bars that are identical across several bars, split them into
  one-bar `patterns` (`groove_a`, `groove_b`) and used `replace` only for the
  bars that differ (fill, crash-in, final hit), instead of writing the full
  4-bar grid inline.

## 3. Wishlist

- A duration syntax for arbitrary beat lengths (e.g. `:2.5`) instead of
  requiring a tie across two notes for non-power-of-two lengths.
- An explicit "rest/gap" shorthand that's clearer than remembering to insert
  `r:` tokens by hand when reading a "beat X: note" style description.
- `beat events` text output accepting a `--bars` filter (in addition to
  `--sections`) would have made it faster to double check a single bar
  without scrolling through a whole section.
