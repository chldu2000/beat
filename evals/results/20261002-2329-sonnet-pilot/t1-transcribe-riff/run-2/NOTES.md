# Notes on writing song.beat.yaml

## 1. What was hard or confusing

- Figuring out how `replace` interacts with a tiled pattern wasn't fully
  spelled out: it's not documented whether a replaced bar's `grid` lanes
  fully override the bar (lanes not mentioned are silent) or merge with the
  tiled pattern's lanes. I assumed full override, which turned out to be
  correct, but had to infer it from the example rather than the spec text.
- There's no notated duration for "2.5 beats" (half + eighth) as a single
  token — durations are limited to the `1 2 4 8 16 32[.][t]` set, so any
  length that isn't a sum of one dotted/plain power-of-two value has to be
  built from multiple tied notes.
- The accent placement in the English description ("beat 1: kick, crash
  (accented)") was ambiguous about which of the two simultaneous hits the
  accent applies to; had to make a judgment call (crash accented, kick not).

## 2. Workarounds

- Used a tie (`:2~` + `:8`, or `:4.~` equivalent) between two notes of the
  *same pitch* to represent a single held note of a duration that has no
  direct token (e.g. 2.5 beats), since ties merge same-pitch notes into one
  sustained event.
- Modeled a bar with a short rest in the middle (bass/guitar bar 4, beat 3
  to 3.5) with an explicit `r:8` rather than trying to express the gap
  implicitly.
- Kept the two 1-bar drum grooves (plain backbeat, ride backbeat) as
  `patterns` tiled across each 4-bar section, then used `replace` only on
  the bars that actually differ (the two fills and the crash-on-beat-1 /
  final-hit bars), instead of writing out all 8 bars of drum grid by hand.

## 3. Features or changes I'd want

- A duration token (or explicit `beats: N` syntax) for arbitrary
  beat-fraction lengths, so "2.5 beats" doesn't require a tie workaround.
- Explicit documentation (not just inferred from the example) of whether
  `replace` on a `grid` bar fully replaces all lanes or merges with the
  pattern being tiled.
- A way to mark which element of a simultaneous multi-hit grid step (e.g.
  kick + crash on the same step) is accented, rather than accenting the
  whole step or none of it.
