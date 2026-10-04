# Beat DSL Fixing Notes

## What was hard or confusing

- **YAML syntax surprises**: Notes starting with `[` (like `[F2 C3 F3]`) trigger YAML parsing errors unless quoted. The error message points to the location but not clearly to the root cause (special character interpretation).
- **Grid character counting**: The drum grid notation requires exactly 16 characters per bar per line, but mismatches produce validation errors that only mention "character count" without showing where the error is. Hard to count manually.
- **Tie semantics**: The DSL forbids ties between different notes (e.g., `F1:8~ G1:2`), but this is only caught at validation time. The constraint isn't obvious from the syntax.
- **Articulation typos**: The typo `!palm` suggested `pm` in the error, but the difference between similar-sounding articulation names isn't clear without consulting the full list.

## Workarounds used

- **Quoting notes with brackets**: Wrapped note sequences in double quotes to avoid YAML parsing errors.
- **Removing cross-note ties**: Removed the tie (`~`) from F1 to transition cleanly to G1, since the DSL doesn't allow ties between different pitches.
- **Adding missing chord**: The section had 4 bars but only 3 chords; added a 4th chord (`G`) to match the bar count.

## Features or changes wished to exist

- **Auto-quoting in YAML generation**: The tooling could auto-quote note values that start with special characters, or reject them at parse time with a clearer message.
- **Better grid error messages**: When a drum grid has the wrong character count, show the actual vs. expected length and which line has the error.
- **Tie flexibility**: Allow ties to "slide" to the next note (like a slide in music notation) rather than just forbidding cross-pitch ties entirely.
- **Pattern name validation**: Check pattern references (`use:`) at parse time and suggest corrections if a pattern is referenced but not defined (e.g., `grove` → `groove`).
