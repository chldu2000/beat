# Notes on writing song.beat.yaml

## 1. What was hard or confusing

- Mixing subdivisions within one drum part: bar 1 needed a triplet-feel ride
  pattern (`steps: 12`) while the rest of the song uses straight 16th-note
  grids (`steps: 16`, the default). The spec doesn't show whether `steps` can
  live inline inside a `replace:` block, so it felt safer to push each bar
  into its own named pattern and reference it with `use:` — more boilerplate
  than I expected for "just one odd bar."
- Figuring out which hits count as "hands" vs "feet" for the 2-hand limit
  isn't spelled out explicitly in prose — I had to infer it from the lane
  table (`bd`/`hp` are feet, everything else is hands) and from the error
  message the validator produced (`drummer needs 3 hands`) when I mistakenly
  added a ride hit under a snare flam.
- Silent/rest stretches are easy to get subtly wrong: several bars in the
  prose description only state the notes that sound and leave the remaining
  beats implicit. Getting the arithmetic right for how much rest to insert
  (e.g. bar 2 bass ending on an implicit 2-beat rest, bar 1 guitar needing a
  trailing quarter rest) required manually summing durations beat-by-beat.
- Long tied notes spanning a barline (6- and 8-beat sustains) require
  splitting the duration across the bar boundary by hand (`:1~` then `:2`),
  and it's not obvious from the spec alone that ties only work within a
  single continuous `notes` string — i.e. they can't cross separate
  `sections`, which constrained the whole file to one 6-bar section instead
  of one section per bar.

## 2. Workarounds

- Used one single 6-bar section (instead of six 1-bar sections) purely so
  that `~` ties could bridge bar 4→5 (bass, guitar, organ) and bar 1→2
  (organ) within one continuous notes string.
- Per-bar dynamic changes on guitar (p → f → mf) were done with inline `@f`
  / `@mf` markers in the middle of the notes string rather than per-section
  `dynamic:`, since the section is shared by all parts but only guitar's
  dynamic needed to change mid-stream.
- For the drum part's one triplet bar, defined a separate 1-bar pattern with
  its own `steps: 12` and pulled it in via `use:`, then overrode the other
  five (16-step) bars individually through `replace:` referencing more 1-bar
  patterns — avoided relying on an untested "steps inside replace" feature.

## 3. Features or changes I'd want

- An explicit statement (and/or validator warning) about whether `steps:`
  is allowed directly inside a `replace:` entry, so odd bars don't require a
  whole extra named pattern.
- A lint/warning for "this bar's note durations don't fill it" that
  suggests the missing rest length automatically, rather than only erroring
  with the mismatch total — would save manual beat-by-beat addition.
- Documentation (even one line) on whether ties can span `sections`/`form`
  boundaries, since it's a natural thing to want and the answer isn't
  stated.
