# Notes

## 1. What was hard or confusing

- The spec and tool output are in Chinese while the task prompt is in English; no functional
  problem, but it required careful cross-referencing between `SPEC.md` and the English task
  description.
- It's not obvious from the spec alone whether per-note articulations (`!pm`, `!acc`, ...) carry
  over like duration/dynamic do, or must be repeated on every note. I assumed they don't carry
  over (each note needs its own `!` marks) and confirmed this by checking `beat events` output.
- Expressing a note with a duration that isn't a "clean" subdivision (e.g. 2.5 beats) isn't
  directly supported — you have to compose it from a tie across two notated durations
  (`:8~ :2`). This is discoverable from the demo file but not spelled out clearly in the spec
  text itself.
- Whether `replace` bar indices in a section are section-relative or song-global is only
  demonstrated by example, not stated explicitly (it's section-relative).

## 2. Workarounds

- A 2.5-beat note (bass/guitar bar 3, and similar in bar 4) was built as two tied notes
  (`:8~` followed by `:2`) rather than one literal duration.
- An "implicit" eighth-note rest in the middle of a bar (bass/guitar bar 4, between beat 3 and
  3.5) had to be written explicitly as `r:8` since the DSL has no concept of implied silence
  between two timed events.
- The one-bar drum fill in bar 4 and the one-off ending hits in bar 8 were written as their own
  one-bar `patterns` and pulled in via `replace`, rather than inlining a 4-bar grid, to keep the
  repeated 3-bar grooves short and readable.

## 3. Features/changes wished for

- A short explicit statement in the spec about whether articulation markers persist across
  notes like duration/dynamic do (currently only inferable).
- A way to express "this many beats" directly (e.g. `:2.5`) for the common case of a sustained
  note that doesn't line up with a single named subdivision, instead of requiring a tie across
  two notated values.
- A dedicated accent-only drum "hit" grid shorthand would be nice, but not essential — `drv_hit`
  with a single `X` per lane worked fine.
