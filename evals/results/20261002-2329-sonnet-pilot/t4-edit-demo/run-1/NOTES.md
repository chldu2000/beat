# Notes

## 1. What was hard or confusing

- The spec and tool output are in Chinese while the song file and comments are in English; no
  problem once read, but it means there's no bilingual quick-reference to cross-check terminology
  against (e.g. confirming "half-time feel" has no dedicated DSL construct).
- There's no first-class concept of a "power chord" or "chord voicing" — `notes` is just raw
  pitches, so turning a chord symbol like `Am` into a sensible 2-note power-chord shape is a manual
  music-theory step done by the author, not something the DSL or tool can check against the
  declared `chords:` string.
- Drum `grid` steps are an absolute step index into the bar, so writing "snare only on beat 3"
  means counting steps by hand (`steps_per_bar / beats_per_bar * (beat-1)`) rather than addressing
  beats directly.
- It's not obvious from the spec whether an empty/omitted part (like silent `gt2`) needs an
  explicit marker or can simply be left out; `beat events --parts gt2` was needed to confirm
  "not listed" really does mean silent rather than an error.

## 2. Workarounds used

- For the bridge's "one sustained power chord per bar" and "organ plays the chords", there's no
  helper that derives a power-chord voicing or a close triad from a chord symbol, so I hand-picked
  guitar/organ pitches by matching the octave/voicing conventions already used elsewhere in the
  song (e.g. reusing the same `[C3 G3]`/`[D3 A3]`/`[B2 F#3]` shapes from the verse/chorus, and
  extending the pattern to `A` for the new `Am` chord).
- "Snare only on beat 3" was expressed as a one-lane `grid` with no `bd`/`hh` lines at all, relying
  on the rule that unwritten lanes simply don't play, rather than any explicit "mute lane" syntax.
- Confirmed the half-time snare placement and the gt2 silence by reading `beat events` output
  directly (timestamps, beat numbers, and the absence of gt2 rows) instead of trusting the grid
  math alone.

## 3. Features or changes wanted

- A way to reference "beat N" directly in grid lane strings (or a helper to place a single hit at
  a named beat) instead of counting dashes.
- A built-in way to derive power-chord / triad voicings from the section's `chords:` string for a
  given part, so parts that "play the chords" don't require manually re-deriving pitches that are
  already declared at the section level.
- A lint/warning when a part's notes diverge in quality from the declared `chords:` (e.g. flagging
  that a part plays a bare 5th against a chord symbol with a 3rd), to catch mismatches like the
  intentional power-chord simplification versus a real mistake.
