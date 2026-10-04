# Notes on composing in Beat DSL

## 1. What was hard or confusing

- It's not obvious from the spec alone whether `replace` blocks on a `use`-based
  part accept a `transpose` key alongside `use`. I avoided the question entirely
  by writing separate transposed patterns (`riff_A`/`riff_D`/`riff_E`) instead of
  testing an undocumented combination.
- The guitar "playable power chord" rule (distinct strings, max fret span 4) is
  checked by a solver, so there's no quick way to predict by eye whether a chord
  voicing will validate — you just have to try it and read the error.
- It's easy to lose track of running duration totals in a `notes` bar by hand;
  a syntax error ("expected 4 beats, got 3.5") only shows up after writing the
  whole section, not while typing it.

## 2. Workarounds used

- To get the same riff shape over three different chords (A, D, E) without
  relying on an unverified `transpose`-inside-`replace` feature, I hand-transposed
  the riff and bass patterns into three separate named patterns and selected
  the right one per bar range with `replace: { bars: { use: ... } }`.
- For the final chorus's "big ending" (crash + sustained chord) I didn't find a
  dedicated "ending" marker, so I just made a one-bar drum pattern (`ending`)
  with a single accented crash+kick hit and let the pitched parts ring out a
  whole-note chord in that same bar.
- To make the second guitar feel like an overdub that only "arrives" for the
  choruses, I simply omitted `gt2` from sections where it should be silent
  (there's no explicit "rest for this part" keyword needed — omission is enough).

## 3. Features or changes wanted

- A way to pass `transpose` through a `replace` block (confirmed to either work
  or not work in the spec) would have let me reuse one riff pattern across
  chords instead of writing three near-identical copies.
- A dry-run "beat count" checker/formatter for `notes` strings (e.g. annotate
  each bar with its running beat total) would speed up hand-writing long chord
  rhythms.
- Named "hits"/"stabs" shorthand for common rock endings (unison hit + cymbal
  choke) would save boilerplate for song outros.
