# Notes

## 1. What was hard or confusing

- The YAML-quoting rule for `notes`/`grid`/`chords` strings starting with `[`, `(`, `%`, `@`, `!`
  is easy to forget as a composer, and the resulting YAML parse error points at a generic
  "block mapping" location rather than directly saying "quote this string."
- Validation stops at the first class of error it hits category-by-category (YAML syntax, then
  structural, then musical), so early runs only reveal one problem at a time; several passes of
  validate → fix → validate were needed to surface all six errors.
- Articulation typos (`!palm` instead of `!pm`) and pattern-name typos (`grove` vs `groove`) are
  only caught at validation time, with no autocomplete/spec-list to check against while writing.

## 2. Workarounds

- No DSL mechanism was needed beyond fixing the existing constructs; all six issues were
  resolvable with small, local edits (quoting, chord count, articulation name, grid length,
  pitch range, tie target) without changing the song's structure.
- Where intent was ambiguous (the out-of-range `G0` bass note, the mistied `G1` resolution, and
  the missing 4th chord in section `a`), I inferred the most consistent fix by cross-referencing
  the matching guitar part and the surrounding chord progression rather than guessing arbitrarily.

## 3. Features or changes wished for

- `beat validate` reporting *all* errors across every category in one pass (or at least all
  structural/musical errors together) instead of apparently stopping early, to cut down on
  validate/fix iterations.
- A way to list valid articulation marks and pattern/section names inline (e.g. `beat lint
  --suggest` with "did you mean `pm`?" / "did you mean `groove`?") since these are easy typos with
  no immediate feedback while authoring.
- Clearer error messages for grid length mismatches that point out *which* bar segment
  (by index) has the wrong step count, rather than just the lane name and total deviation.
