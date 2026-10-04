# Notes on Beat DSL

## What Was Hard or Confusing

1. **Bar duration validation with `:b` notation**: The `:b` (beats) notation seemed inconsistent during validation. When using `:b0.5`, `:b1.5`, etc. for specifying durations in beats, the validator wasn't consistently counting them toward the 4-beat bar total, even though mathematically they added up correctly. Standard note durations (`:1`, `:2`, `:4`, `:8`) worked more reliably.

2. **Multi-line vs. single-line note formatting**: Notes written across multiple lines with `|` bar separators (using `|` at line breaks) behaved differently than writing all bars on a single line. The parser seemed to work more reliably with everything on one line separated by spaces and `|` characters.

3. **Dotted note durations**: Dotted notes like `:4.` (dotted quarter = 1.5 beats) appeared to have parsing issues when mixed with other duration notations in the same bar. Using simpler integer-based note lengths avoided these issues.

## Workarounds Used

1. **Avoided `:b` notation in favor of standard durations**: Instead of `G1:b1.5 G1:b0.5 G1:b0.5!acc`, I used `G1:2 G1:8 G1:8!acc` to achieve the same timing with standard note values.

2. **Wrote notes on a single line**: Instead of:
   ```yaml
   notes: |
     note1 | note2 |
     note3 | note4
   ```
   I used:
   ```yaml
   notes: "note1 | note2 | note3 | note4"
   ```

3. **Simplified rhythmic patterns**: Where the description suggested complex note combinations, I used simpler subdivisions (e.g., `F1:2 F1:8 F1:8 F1:4` instead of trying to express `F1:b1.5 F1:b2.5`).

## Features or Changes Wished For

1. **Better error messages for `:b` notation**: If the `:b` (beats) notation is supported, the validator should provide clearer error messages explaining why certain durations aren't being recognized or counted.

2. **Clarification on multi-line note formatting**: The spec should explicitly state whether notes can span multiple lines within the `|` block, or if all bars must be on a single line for reliable parsing.

3. **Support for mixed notation flexibility**: Allow seamless mixing of different duration notations (`:1 2 4 8 16 32` with dotted variants and `:b` notation) within the same bar without parsing issues.

4. **Validation suggestions for bar duration mismatches**: When a bar is short or long by a specific amount, suggest not just "add r:b0.5" but provide context about what's actually parsed in that bar.

5. **Preview or dry-run mode**: A way to see how the parser is interpreting a section before full validation, to debug notation issues more quickly.
