# Beat DSL Implementation Notes

## What Was Hard or Confusing

1. **Grid Step Granularity for Drums**: The 16-step grid (sixteenth-note resolution in 4/4 time) can't represent fractional beat positions like 1⅔ beats (beat 1 + 2/3). The original specification used positions like "beat 1+2/3" which map to step 2.667, requiring rounding to the nearest representable step. This means drum patterns are approximations of the described rhythms.

2. **Note Duration Syntax**: The valid note durations (1, 2, 4, 8, 16, 32) correspond to specific note values in music notation. It took trial-and-error to understand that `:1` = whole note (4 beats), `:2` = half note (2 beats), `:4` = quarter note (1 beat), etc. Non-standard durations like 1.5 beats or 6 beats require combinations like `:4.` (dotted quarter) or splitting across measures.

3. **Ties Across Bar Lines**: The tie syntax (`~`) is powerful for durations spanning multiple bars, but only works for single notes, not chords. This required a different approach for organ chords lasting 6-8 beats.

4. **Rest Notation Constraints**: Rests can't use arbitrary durations (e.g., no `r:3`). Longer rests must be expressed as multiple shorter rests (e.g., `r:2 r:1`), which is verbose.

5. **Drum Lane Abbreviations**: The available drum lanes (`bd`, `sd`, `ss`, `hh`, `ho`, `hp`, `t1`, `t2`, `t3`, `cr`, `cr2`, `rd`, `rb`, `ch`) had to be looked up in the spec. Using incorrect names resulted in unhelpful error messages.

6. **Grid Formatting**: It wasn't immediately clear whether pipes and spaces in the grid are counted toward step length. The spec says they're ignored, but incorrect placement caused hard-to-debug validation errors.

## Workarounds Used

1. **Approximating Fractional Beat Positions**: When the original description used beat positions like 1⅔ (step 6.667 in a 16-step grid), I rounded to the nearest step. For example, beat 1.667 → beat 1.5 (step 6), beat 2.667 → beat 2.5 (step 10).

2. **Splitting Multi-Beat Chords Across Bars**: For organ chords lasting 6-8 beats (longer than a single bar), I:
   - Used a whole note `:1` in one bar (4 beats)
   - Continued with a half note `:2` in the next bar (2 beats)
   - This gave 4+2=6 beats or 4+4=8 beats as needed

3. **Combining Rests**: For required rest durations that aren't valid (like 3 beats), I combined smaller rests: `r:2 r:1` for 3 beats.

4. **Chord Representation in Notes**: Used bracket notation `[E3 G3 B3]` with standard note values (`:4` for quarter notes, etc.) to represent simultaneous notes.

## Features or Changes I Wish Existed

1. **Fine-Grained Drum Timing**: A way to specify fractional beat positions in drum grids, or the ability to use triplet step counts (12 steps per bar) as a default rather than only for specific bars.

2. **Chord Ties**: Support for ties on chords, not just single notes, to elegantly handle multi-beat chord durations across bar lines.

3. **Compound Rest Notation**: Shorthand for common rest patterns, like `r:3` directly instead of requiring `r:2 r:1`.

4. **Better Error Messages for Dynamics**: When a dynamic appears in an invalid context (like after a duration), the error should clarify the expected syntax instead of treating it as an articulation error.

5. **Automatic Beat Rounding**: An option to round beat positions in the original description to the nearest representable step, with a warning, rather than requiring manual adjustment.

6. **Preview Grid Visualization**: A command like `beat grid song.beat.yaml` that displays the actual drum pattern visually (like a piano roll) to verify correctness before final export.
