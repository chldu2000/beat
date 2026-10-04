# Notes

## 1. What was hard or confusing

- `grid` strings are position-sensitive but there's no explicit column/beat ruler in the
  file — figuring out that "beat 3" in 4/4 (16 steps/bar) is step 9 meant counting dashes
  by hand (`steps per beat = steps/bar ÷ time signature numerator`).
- It's not obvious from the spec alone whether an instrument omitted from a section's
  `parts` is "silent" vs. an error; had to reread section 7 ("声部没有列出就不演奏") to be
  sure `gt2: silent` just means leaving it out.
- The lay-back performance knob (`offset_ms`) is a per-lane *performance* setting, separate
  from the `grid`/`notes` pitch content — easy to miss on a quick skim that "snare lay back"
  isn't something you touch in the pattern at all.

## 2. Workarounds

- There's no vocabulary for "half-time feel" as a named concept; expressed it literally as
  a one-lane grid pattern (`sd` only, hit on beat 3) with everything else omitted.
- Power chords are just written as two-note dyads (`[A2 E3]`) rather than a dedicated
  "power chord" notation — matched the voicing style already used elsewhere in the song
  (verse/chorus gt1) for consistency rather than inventing a new convention.

## 3. Wishes

- A named/reusable "rhythmic feel" concept (e.g. half-time, swing-16, etc.) that expands to
  a grid, instead of hand-counting dashes to land a hit on a specific beat.
- A shorthand chord-to-voicing helper (e.g. `chord:Am:power` or `chord:Am:triad`) so simple
  chordal parts (whole-note pads, power chords) don't require manually spelling out pitches
  that are already implied by the `chords:` line.
- `beat events --sections` output showing the section order/instance list directly (e.g. a
  `--form` flag) would make it faster to confirm placement of a new section without scanning
  full event dumps.
