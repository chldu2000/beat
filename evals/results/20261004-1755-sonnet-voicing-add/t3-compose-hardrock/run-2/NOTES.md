# Notes on writing song.beat.yaml

## 1. What was hard or confusing

- It's not obvious up front which musical ideas are worth promoting to `patterns` vs.
  writing inline — I only realized the `use` + `transpose` combo would let one power-chord
  shape serve A5/D5/E5 after reading section 7 closely; a short worked example of
  "one pattern, three chords via transpose" in the spec would help.
- `beat events --sections X` on a section whose last note ties into the *next* section
  reports a tie error ("no following note") because the following section isn't loaded.
  This had me briefly worried something was wrong until I re-ran `validate` on the whole
  file and it was clean — worth noting in the tool's `--help`/docs that `--sections` is a
  display filter only and can produce misleading tie errors at the edges.
- The exact meaning of "hands" vs. "feet" for the 2-hand drum-overlap rule isn't stated
  next to the error text itself; I had to cross-reference the lane table's 肢体 (limb)
  column to confirm `bd`/`hp` don't count against the 2-hand cap.

## 2. Workarounds

- No native "chord quality transpose" concept — I got a full D and E chorus chord by
  picking an A-shape voicing from `beat voicing` and transposing the *pattern*, relying on
  the fact that guitar-shape transposition by semitones preserves playability. Had to
  manually verify the resulting fret spans would stay within range rather than the tool
  telling me up front.
- To make the solo's final note ring through the ending, I used a cross-section tie
  (`A4:1~` at the end of chorus2, continued as `A4:1~` at the start of outro) — works, but
  the dependency between two sections' note text isn't visible unless you know to look for it.
- There's no "silence this part for one bar then come in" shorthand other than `replace`
  with an all-rest grid/hits string; I avoided needing it by just starting drums at full
  energy from bar 1 instead of fighting the DSL for a one-bar silent pickup.

## 3. Features or changes I'd want

- A `beat events` flag to include one bar of context from the adjacent section (or just
  suppress the tie-boundary error) when `--sections` is used, so spot-checking a single
  section doesn't produce a false "error".
- A way to transpose a *chord-symbol* pattern by scale degree/Roman numeral (e.g. "same
  pattern, but on IV") rather than raw semitones, so the author doesn't have to work out
  the interval by hand and hope the fretting still works.
- `beat voicing` output fed directly as a `replace`/`transpose` suggestion, e.g. a flag
  that says "this transpose amount keeps the same string set" vs. one that doesn't, would
  remove the guesswork around fret-span validity when reusing shapes across chords.
