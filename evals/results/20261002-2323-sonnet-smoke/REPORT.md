# Eval report: 20261002-2323-sonnet-smoke

model `sonnet`, 1 run(s) per task

| task | final valid | first check clean | checks to green | F1 | dur acc | arts acc | dyn acc | task checks | chars/bar | cost $ | turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t5-fix-riff | 1/1 | 0/1 | 3.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 222.00 | 0.26 | 18.00 |

## Error categories (distinct errors seen during the session, summed over runs)

| task | first check | whole session |
|---|---|---|
| t5-fix-riff | yaml 1 | token 1, grid_length 1, range 1, yaml 1, structure 1, tie 1, bar_count 1 |
| **all** | yaml 1 | token 1, grid_length 1, range 1, yaml 1, structure 1, tie 1, bar_count 1 |

## Per run

### t5-fix-riff
- **run-1**: valid=True, error trace [1, 6, 0, 0], F1=1.0, cost=$0.26, denied: ['Bash: python3 -c "\ns=\'x-x-----x-x------\'\nprint(len(s), s)\ns2=\'x-x-----x-x-----\'\nprint(len(s2), s2)\n"']

## Agent notes

### t5-fix-riff / run-1

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

