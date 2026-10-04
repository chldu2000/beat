# Notes on writing song.beat.yaml

## 1. What was hard or confusing

- The `steps` setting for a drum `grid` applies to the whole block, so a bar that
  needs triplet subdivisions (bar 1's swung ride) can't live in the same grid
  string as bars that need straight 16th-note resolution (bars 2, 3, 5, 6).
  There's no per-bar `steps` override inside one multi-bar grid.
- Durations that don't correspond to a single token (e.g. 2.5 beats, or a note
  that trails off into silence for the remainder of a bar) aren't directly
  expressible — you have to reconstruct them from tied notes and explicit
  rests, and the arithmetic has to add up exactly or `validate` rejects the
  bar. A few of the English descriptions had an implicit trailing rest that
  wasn't stated explicitly (e.g. bass bar 2, guitar bar 2), which only showed
  up as a "duration ... expected 4" error.
- `beat events` plain-text output doesn't show note length in beats directly
  (only seconds), so checking "is this really a dotted quarter" means doing
  tempo math by hand or switching to `--json`.

## 2. Workarounds

- Split the 6-bar drum part into six single-bar `patterns` (one per distinct
  rhythmic grid, including one with `steps: 12` for the triplet ride feel in
  bar 1) and stitched them together with `use` + `replace` on every bar. This
  sidesteps the "one steps value per grid block" limitation.
- Represented long sustained notes/chords that cross bar lines (bass bar 4's
  6-beat C2, guitar bar 4's 6-beat E3, organ's 6-beat and 8-beat chords) as a
  whole-note (or half-note) tied `~` into the following bar(s), closed by a
  matching note/chord of identical pitches with no trailing tie.
- Added explicit rests (`r:2`, `r:8`, etc.) wherever the prose described notes
  that didn't fill out the full 4 beats of a bar, since `validate` requires
  each bar's note strings to sum exactly to the bar length.
- Used inline `@f` / `@mf` dynamic markers inside a part's `notes` string to
  express dynamic changes mid-part (e.g. guitar going p → f at bar 3 → mf at
  bar 6), since the `dynamic:` field only sets one static default per part.

## 3. Features or changes I'd want

- Per-bar `steps` (or an explicit "this bar is a triplet bar" shorthand) so a
  single grid block can mix straight and triplet subdivisions.
- A duration shorthand for "tie to end of bar" or arbitrary beat lengths
  (e.g. `:2.5` or `len=2.5`) instead of requiring manual tie decomposition.
- `beat events` text output could include the length in beats (not just
  seconds) next to each event, to make eyeballing rhythms against a spec
  faster without doing BPM arithmetic.
