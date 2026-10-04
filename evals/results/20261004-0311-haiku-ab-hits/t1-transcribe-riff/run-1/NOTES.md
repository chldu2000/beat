# Beat DSL Observations

## What was hard or confusing

1. **YAML structure**: The proper hierarchy took several iterations to get right. Parts must be defined directly within sections (under `sections > main > parts`), not in a separate `performance` section. The documentation hint pointing to `SPEC.md` and examples helped clarify this.

2. **Cross-barline notes**: Handling notes that extend past the barline is complex. Using `~` for ties seemed intuitive, but getting the exact duration calculations right required careful consideration of which beats map to which bars.

3. **Duration notation complexity**: The DSL uses two different duration systems:
   - Note-based durations (4 = quarter, 8 = eighth, 4. = dotted quarter)
   - Beat-based durations (`:b2.5` = 2.5 beats)
   - Mixing these correctly required understanding when each applies.

4. **Drum lane syntax**: Figuring out the available drum lanes (bd, sd, hh, rd, t1, t2, t3, cr, etc.) and their exact names required referencing error messages since they weren't initially obvious.

## Workarounds used

1. **Avoided cross-barline notes**: Rather than having bass/guitar notes extend across bars with ties, I split them at the barline when necessary. This simplified validation but meant some compound note patterns became rests within bars.

2. **Empty bars for drum lanes**: When certain drum lanes (like hh = hi-hat) didn't have hits in later bars (5-8), I represented them with empty bar slots (just `|` with no hits) rather than explicitly listing rests.

3. **Beat-based rest notation**: Used `r:bX` notation to fill gaps in bars where no instrument had notes, ensuring each bar exactly filled 4 beats.

## Features or changes that would be helpful

1. **Pattern repeat syntax**: A way to reference repeated patterns without restating all 8 bars. Currently, drum patterns that repeat across bars must be written out fully or use the `replace` mechanism, which requires understanding the replace syntax.

2. **Better cross-barline note documentation**: More examples and clearer guidance on using `~` ties would help. The behavior of tied notes extending into the next bar could be better documented.

3. **Drum lane "fill" option**: Instead of requiring every lane to be specified for every bar, a way to say "only list hits for lanes that have notes, fill the rest with rests automatically" would reduce boilerplate.

4. **Duration parsing flexibility**: Accepting duration formats like `2.5` directly instead of requiring `:b2.5` for beat-based durations would be more intuitive for beat counts.

5. **IDE hints**: Error messages sometimes required trial-and-error to understand what was expected. Better error messages or IDE autocomplete would help (e.g., "expected one of: bd, sd, hh, ..." in the error for unknown drum lanes).
