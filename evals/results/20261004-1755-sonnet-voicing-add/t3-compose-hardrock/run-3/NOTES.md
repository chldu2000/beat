# Notes on composing with the Beat DSL

## 1. What was hard or confusing

- Figuring out exact note-duration arithmetic by hand (making sure every bar's
  symbols sum to exactly 4 beats) is tedious and error-prone, especially for
  the free-form solo line with mixed eighth/sixteenth/dotted values. `validate`
  gives a clear error when a bar is off, but there's no "show me the running
  beat total as I type" feedback — you only find out after writing the whole
  bar.
- It's not obvious up front whether `patterns` loop-fill by truncating or by
  wrapping (e.g. does a 4-bar pattern used in an 8-bar section repeat cleanly,
  or does a 3-bar pattern in an 8-bar section get cut mid-bar?). I ended up
  sizing patterns to divide evenly into sections to avoid the question.
- The interaction between `extends`, `replace`, and `use` is powerful but the
  "which layer wins" rules needed a careful re-read of the spec before I was
  confident that a `chorus2: { extends: chorus, parts: { gt2: ... } }` would
  pick up `chorus`'s drums/bass/gt1 untouched while fully swapping gt2.

## 2. Workarounds used

- To give the final chorus a guitar solo while keeping an earlier, calmer
  chorus, I didn't try to parametrize one "chorus" section by instance;
  instead I made `chorus2 extends chorus` and overrode only the `gt2` part.
  This is the pattern the demo already uses for `verse2 extends verse`, and
  it was the only way to get genuinely different note content per repeat
  (performance `edits` can only nudge existing notes, not add new ones).
- For the chromatic pickup lick that walks a riff back to its downbeat (e.g.
  `G2 G#2` before landing back on `A2`), I just wrote it inline inside the
  pattern bar rather than finding any dedicated "approach note" notation —
  there isn't one, so literal chromatic notes stood in fine.
- Shortened the second verse to 4 bars by giving `verse2` its own `bars:`
  and `chords:` and re-declaring `use: riff_verse` with a `replace` on the
  last bar, since `extends` inherits `bars` by default and I needed a
  shorter instance.

## 3. Features or changes wished for

- A `beat events --by-bar` style dry-run that also flags "this bar sums to
  3.5/4 beats" per-pattern as you edit a `notes` string, instead of only at
  full `validate` time, would speed up writing dense bars a lot.
- Some shorthand for "repeat the previous bar transposed" at the top level
  (not just inside `replace`) would help write a 12-bar blues-style turnaround
  without retyping the chord-tone chord three times.
- A way for `patterns` to declare "this pattern is N bars but only cleanly
  tiles into multiples of N" so `validate` could warn earlier if a section
  length doesn't divide evenly, rather than relying on the generic
  "pattern didn't divide evenly" warning showing up only when it actually
  doesn't divide evenly.
