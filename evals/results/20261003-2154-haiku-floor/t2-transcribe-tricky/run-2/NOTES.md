# Beat DSL Transcription Notes

## What Was Hard or Confusing

1. **Drum Grid Step Counts and Bar Separation**: The grid notation requires exact character counts for each lane per bar. When mixing multiple step sizes (e.g., 12 steps for triplet bar, 16 steps for standard bars), it's easy to miscalculate characters. The `|` character is ignored in counting but essential for visual separation.

2. **Multi-Bar Notes with Ties**: Notes spanning multiple bars using the `~` (tie) notation were counterintuitive. The spec example `E2:1~ | E2:2` for a 6-beat note makes sense conceptually but requires careful management of where the bar boundary goes, especially when the second bar also has other notes.

3. **YAML Multiline String Handling**: Using `>-` for multiline notes means spaces between lines get collapsed, but `|` characters within the string are preserved. This creates ambiguity about where bar boundaries actually occur. A single missing or extra `|` character silently creates or removes a bar.

4. **Duration Precision**: The original description appeared to have mathematical inconsistencies (e.g., guitar bar 2 had durations that summed to 4.25 beats for a 4-beat bar). Distinguishing between transcription errors and my misunderstanding required iterative validation and adjusting note durations.

5. **Articulation Syntax**: The `!` articulation notation within notes requires careful positioning and can't span bars. Multiple articulations stack (e.g., `C4:4!h!p` for hammer-on + pull-off), but the parser strictly validates timing, making it easy to exceed bar lengths.

## Workarounds Used

1. **Separate Drum Patterns Per Bar**: Instead of trying to manage one complex grid for all 6 bars, I defined separate `patterns` for each drum bar with appropriate `steps` (12 for triplet bar 1, 16 for standard bars). Then used `replace` to substitute each bar. This made debugging individual bars much easier.

2. **Removing Extra Spaces in Grid Notation**: I initially included spaces within grid rows for readability, but the parser counted them. Final solution was to write drum patterns without internal spaces, using only `|` for visual bar separation.

3. **Merging Bar Content Strategically**: Bar 5 originally had both the continuation of a tied note AND new chords. Rather than separate them, I merged both into one bar: `E3:2 [E3 G3 B3]:4!st [E3 G3 B3]:4!st`, reducing the total bar count to exactly 6.

4. **Adjusting Note Durations to Fit**: When bars had fractional durations that didn't add to 4 beats, I adjusted the smallest note values. For example, changing the final note of guitar bar 2 from `C4:4` (1 beat) to `C4:8` (0.5 beats) to make the bar exactly 4 beats.

5. **Using Whole Note Rests**: For the final bar with no musical content, a single `r:1` (whole note rest = 4 beats) is clearer than `r:4 r:4 r:4 r:4` (four separate quarter-note rests).

## Features or Changes Wished

1. **Better Error Messages for Character Counts**: When a grid lane has the wrong number of steps, the error message should say "expected 16 characters, got 17 at positions X-Y" rather than showing the mangled output.

2. **Bar-Level Validation for Notes**: The validator should report "bar N: duration X beats, expected 4" but also suggest which notes to adjust to fix it, rather than requiring manual calculation.

3. **Support for Steps Declaration Per Lane**: Different lanes in the same bar could support different step counts (e.g., triplet hi-hat patterns alongside regular bass drum patterns in the same bar), rather than requiring separate patterns.

4. **Explicit Tie Syntax Across Bars**: A notation like `E2:1-|E2:2` (using `-` to indicate tie direction) might be clearer than `E2:1~ | E2:2`, making the intent more obvious in the source.

5. **Repeating Group Validation**: The `(...)` repeat syntax should allow specification like `(note sequence)*2:bar=2`, meaning "repeat this 2-bar group twice" rather than requiring manual concatenation.

6. **Default Step Size Per Section**: Setting `steps: 16` once at the section level and then using `steps: 12` only for specific bars via replace might reduce boilerplate.
