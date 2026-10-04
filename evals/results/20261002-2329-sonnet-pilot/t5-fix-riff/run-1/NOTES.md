# Notes

## 1. What was hard or confusing

- The YAML "must quote notes starting with `[`" rule is easy to forget, and
  the resulting YAML parse error points at a YAML-internal line/column
  rather than the Beat-level location (section/part/bar), so it takes an
  extra mental step to map it back to the offending `notes:` line.
- `validate` reports only one error at a time when the error is a YAML
  syntax error (nothing else is checked until the file parses), but once
  parsing succeeds it reports all semantic errors at once. Good to know,
  but it means you can't predict up front how many fix/validate round
  trips a single file will take.
- Articulation typos (`!palm` instead of `!pm`) and pattern-name typos
  (`grove` instead of `groove`) are caught, but only as independent,
  unrelated-looking errors — there's no "did you mean `pm`?" suggestion,
  so diagnosing typos relies on re-reading the spec's articulation table.

## 2. Workarounds

- No real DSL workarounds were needed — every problem in the file was a
  genuine mistake (unquoted notes, a typo'd pattern name, a typo'd
  articulation, a chords list one bar short, an off-by-one grid string, a
  bass note out of range, and a tie into a different pitch). Fixes were
  all small, local edits that kept the original riff shapes.
- For the broken tie (`F1:8~ G1:2` tying into a different pitch), I
  inferred the intended target pitch by cross-checking the guitar part's
  held chord in the same bar (`[F2 C3 F3]` held across the whole bar) and
  changed the bass's final note to match (`F1:2`) rather than removing the
  tie, since the guitar clearly intended a sustained chord under the tie.

## 3. Features or changes I wish existed

- `beat validate` could point YAML syntax errors at the Beat-level
  location (section/part) when possible, instead of only the raw
  YAML line/column.
- A "did you mean?" suggestion for near-miss identifiers (pattern names,
  articulation tags) would make typo-class errors much faster to fix.
- An option to run `events` or `validate` with a dry-run "explain" mode for
  ties/chords would help confirm intent without having to mentally replay
  the grid/notes string (I used `beat events --parts ... --sections ...`
  for this, which worked well, but discovering that this is the right
  investigative tool wasn't obvious from `validate`'s error message alone).
