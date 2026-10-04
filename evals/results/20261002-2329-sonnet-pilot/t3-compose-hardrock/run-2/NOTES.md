# Notes on composing with Beat DSL

## 1. What was hard or confusing

- Articulation marks (`!pm`, `!acc`, etc.) do **not** carry over between notes the way
  duration/velocity do — only visible by close reading of the spec's wording and the demo
  example. Easy to assume `!pm` sticks until changed, like duration does.
- Drum grid length errors only report "expected 16" vs. actual count, not which character
  is extra/missing — for a 16/17-char string you have to recount by hand rather than get a
  diff.
- It's not obvious from the spec whether single-note (non-chord) pitches on guitar/bass are
  checked for fret-span playability the same way chords are, or just checked against overall
  instrument range.

## 2. Workarounds

- To keep chord-change bars DRY while still using `use:`-filled looping patterns, I built a
  library of 1-bar patterns per chord (`riff_a`, `stab_d`, `stab_e`, `ring_a`, `ring_d`,
  `ring_e`, `bass_a`, `bass_d`, `bass_e`) and relied on `replace` with bar numbers/ranges to
  swap in the right chord for each bar, instead of writing long multi-bar `notes` strings.
- Reused the same `chorus` section for the final chorus via `extends`, overriding only `gt2`
  to add the lead solo, so the "chorus comes back" requirement and the "solo in the last
  chorus" requirement could both be satisfied without duplicating the rhythm section.
- Verified exact grid lengths and note-duration sums by hand (counting characters/beats)
  since there's no local way to lint this without invoking the CLI.

## 3. Features or changes I'd want

- A `beat lint-grid` or similar that points out exactly which step index is extra/missing
  when a drum grid line has the wrong length, instead of just a count mismatch.
- A way to say "this articulation applies until the next pitch/articulation override" as an
  opt-in, to avoid repeating `!pm` on every single palm-muted note in a riff.
- Some indication in `beat events` (or a `--summary` flag) of total duration/beats per bar,
  to sanity-check note-value math before running full validation.
