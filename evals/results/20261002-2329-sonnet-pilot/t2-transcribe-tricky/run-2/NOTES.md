# Notes

## 1. What was hard or confusing

- Drum `grid` notation assumes one fixed subdivision (`steps`) for an entire
  multi-bar block. This song mixes triplet-eighth feel (bar 1), straight
  eighths (bar 4), and sixteenths (bars 2, 3, 5, 6) in the same part, so a
  single grid string could not express all of it without going to a very
  fine common subdivision (48 steps/bar).
- No direct note value for arbitrary beat lengths like 2.5 beats (only
  `1 2 4 8 16 32` plus dot/triplet). Had to reconstruct it from two tied
  notes of the same pitch.
- It's not obvious from the spec alone whether a tie (`~`) is only meant to
  span a barline or can also join two consecutive notes of the same pitch
  within one bar; it worked (and merged into a single sustained event in
  `beat events`), but this isn't spelled out explicitly.
- The flam-needs-2-hands rule combined with simultaneous hand-played lanes
  (e.g. ride) isn't mentioned until validation fails; the error message was
  clear, but it's a rule worth knowing before transcribing the kit part.

## 2. Workarounds

- Split the drum part into six separate 1-bar `patterns`, each with its own
  `steps:` value (12, 16, 8, 16, 16, 16) matched to the subdivision actually
  needed in that bar, then stitched them together with `use` + `replace`
  per bar instead of one multi-bar grid.
- Built the 2.5-beat bass/guitar notes (`B1`, implicit elsewhere) and the
  6-beat and 8-beat sustained chords (bass `C2`, guitar `E3`, organ chords)
  as tied sequences (`:2~ :8`, `:1~` into the next bar, etc.) since no
  single note value covers those lengths or crosses a barline directly.
- Mid-phrase dynamic changes (guitar's `p` → `f` → `mf`) were done with
  inline `@f` / `@mf` markers inside the `notes` string rather than new
  sections, since the song is really one continuous 6-bar passage.

## 3. Features or changes wished for

- Per-bar (or per-note-group) subdivision overrides within a single grid
  block, so one `grid:` entry could mix triplet and sixteenth regions
  without needing several small patterns stitched via `replace`.
- A tied/arbitrary duration shorthand (e.g. `B1:2.5` or `B1:10t16`) to avoid
  manually decomposing non-power-of-two lengths into tied notes.
- `beat events` output defaults to a human table; a quick way to filter it
  to a single bar range (like `--sections`) would have made spot-checking
  individual bars faster during authoring.
