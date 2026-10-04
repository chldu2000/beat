# Notes

## 1. What was hard or confusing

- The error messages are precise about *where* something is wrong (section, part,
  bar) but not always about *what the composer probably meant*. E.g. a tie
  mismatch (`F1` tied to `G1`) just says the tie is broken; figuring out which
  side was the typo required comparing against the guitar part in the same bar.
- Unquoted `notes:` strings starting with `[` fail with a raw YAML parser
  traceback rather than a Beat-specific diagnostic, even though the spec and a
  comment in the example file both warn about this. It would be easy to miss
  if you didn't already know the rule.
- Grid alignment bugs (one extra/missing `-` in a 16-step lane) are invisible
  by eye in a monospace block when bars are concatenated with `|` on one line;
  you only find them via the validator's bar/lane-specific step count.

## 2. Workarounds

- No real workarounds were needed — every error had a direct, in-spec fix
  (quote the string, correct the pattern-name typo, correct the articulation
  name, add the missing chord, fix the tied pitch, fix the grid length).
- Used `beat events` on the affected sections after each fix to visually
  confirm the repaired bass tie and drum groove matched the surrounding
  (already-correct) guitar/drum material, rather than trusting validation
  alone.

## 3. Features or changes I'd want

- A "did you mean" suggestion for unknown pattern names (`grove` vs `groove`)
  and unknown articulations (`!palm` vs `!pm`), since both are simple typos of
  valid identifiers already defined elsewhere in the file.
- A lint check that a section's `chords` bar count matches its `bars` count
  with a pointer to which bar is missing, rather than only "3 bars of chords,
  expected 4" (useful as-is, but naming the missing bar index would save a
  recount).
- A grid-diff helper (or `beat events` option) that prints step index markers
  above/below long concatenated multi-bar grid lines, making off-by-one
  alignment errors visible without needing the validator round-trip.
