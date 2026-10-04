# Beat DSL Editing Notes

## What was hard or confusing

- **Drum grid padding**: The grid notation requires exactly 16 characters per bar (one per sixteenth note), but this isn't immediately obvious from examples. I initially wrote `x-------` (8 chars) instead of `x---------------` (16 chars), which caused validation errors. The error message helped identify the issue, but the constraint would be clearer in documentation with an example.
- **Beat position mapping**: Translating "snare on beat 3" into grid position 9 required manual counting (beats 1-4 map to positions 1-4, 5-8, 9-12, 13-16). A helper tool or clearer visual representation would make this intuitive.
- **Multi-bar grid syntax**: It's not immediately clear whether bars in a grid should be separated by pipes, how spaces affect parsing, or whether trailing spaces are significant. Trial and error was needed.

## Workarounds used

- **No clear workarounds needed**: The DSL was expressive enough to encode all the requirements without tricks. I used power chord voicings for gt1 that match the existing song style, and specified gt2 as silent with `r:1` repeated rather than using a shorthand.

## Features or changes I wish existed

- **Grid visualization**: A tool that displays the drum grid visually (with beat boundaries and position numbers) would make editing drum patterns much faster and less error-prone.
- **Relative offset syntax**: For performance offsets, a way to specify "+10ms" relative to current value instead of calculating the absolute value. This would make micro-adjustments easier.
- **Chord symbol shorthand**: For quick entry, support for compact chord notation like "Am | C | D | B" to auto-generate default voicings for a given instrument type, reducing boilerplate.
- **Silence shorthand for parts**: A way to mark a part as completely silent for a section (like `gt2: { silent: true }`) instead of writing out rests for every measure.
