# Notes

## 1. What was hard or confusing

- The YAML quoting rule (strings starting with `[` must be quoted) is easy to
  forget when writing `notes` by hand, and the resulting YAML parser error
  doesn't point at the Beat-level problem — you have to recognize it's a
  quoting issue yourself. The tool's hint text did help here, though.
- Several errors were simple typos (`grove` vs `groove`, `!palm` vs `!pm`,
  `G0` vs `G1`) that only surface one at a time per `validate` run, so fixing
  a file with multiple unrelated mistakes takes several validate/edit cycles.
- The tie-mismatch error (`tie from F1 but the next note is G1`) required
  cross-referencing the guitar part's rhythm/held-chord to figure out which
  side of the mismatch (the tied pitch vs. the destination pitch) was the
  actual typo, since the spec doesn't say which one is "wrong."

## 2. Workarounds

- No real workarounds were needed — all six validation errors were
  straightforward typos/omissions (missing chord bar, misspelled pattern
  name, misspelled articulation, out-of-range note, wrong tie target,
  one-character-too-long drum grid row). Fixed each in place without
  changing the song's structure.

## 3. Features or changes wished for

- `beat validate` reporting all errors it can find in one pass is already
  the case here, which was nice — but it would help even more if grid
  length errors could show a diff/alignment against the expected length
  instead of just "17 steps, expected 16", since counting dashes by eye is
  error-prone.
- A lint-style check that flags unknown articulation names against the
  spec's known list (with a "did you mean `!pm`?" suggestion) would have
  caught `!palm` and `grove`/`groove`-style typos faster.
