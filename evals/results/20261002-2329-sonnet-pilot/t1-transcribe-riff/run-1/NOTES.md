# Notes

## 1. What was hard or confusing

- There's no notation token for an arbitrary beat length like 2.5 beats (only
  `1 2 4 8 16 32` plus dot/triplet). Figuring out that a tie (`~`) between two
  notes of the same pitch is the intended way to build a non-standard duration
  took some thought, and isn't spelled out as an explicit technique in the spec
  (it's only shown tying across a barline).
- The spec doesn't say explicitly whether `!acc`/`!pm` etc. persist to
  following notes the way duration and velocity do. I assumed articulations
  are per-note only (not "sticky"), which matched the intended transcription,
  but it would be good to confirm this in the spec.
- Figuring out how to express a mid-bar silence (a rest between two attacks
  where the beat-grid specifies exact start times) required manually computing
  gaps rather than being able to just place notes "at" beat positions.

## 2. Workarounds

- Used `F1:2~ F1:8` (and similarly for guitar chords) to express a single
  sustained note of 2.5 beats, since no single duration token covers that
  length.
- Inserted an explicit `r:8` rest in bass/guitar bar 4 to represent the silent
  half-beat between the second and third attacks (beat 3.0–3.5), since notes
  are specified as a contiguous sequence rather than by absolute position.
- Split the song into two `sections` (bars 1-4, bars 5-8) specifically because
  the `dynamic` (mf → f) changes at bar 5 for every part; this let the section
  default velocity handle it instead of per-note `@` markers.
- Built small one-bar drum `patterns` (`beat_a`, `fill_a`, `ride_beat`,
  `crash_start`, `ending_hit`) and used `replace` for the bars that differ,
  rather than writing one long grid per section.

## 3. Wishlist

- A duration token/shorthand for arbitrary tied lengths (e.g. `:2.5`) so ties
  aren't needed just to express a plain sustained note.
- A way to place a note/rest at an explicit beat position within a bar (e.g.
  `@2.5 F1:1`) instead of having to compute rests and offsets by hand to keep
  a bar's total duration exact.
- `beat events` output showing the source `notes`/`grid` token alongside each
  event (not just bar/beat) would make cross-checking faster.
