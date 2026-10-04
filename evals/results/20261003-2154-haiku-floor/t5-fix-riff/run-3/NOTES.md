# Beat DSL Fixing Notes

## What was hard or confusing

- **YAML syntax sensitivity**: Chord progressions and note sequences starting with special characters (like `[` for chords) need to be quoted in YAML. This isn't obvious from reading Beat DSL examples and requires understanding YAML's flow sequence syntax.
- **Typo discovery**: The error message for an unknown pattern (`use: grove` instead of `use: groove`) could have been more explicit. The error just said "unknown" without showing available pattern names.
- **Articulation validation**: The `!palm` articulation seemed like it should exist (palm mute), but the DSL uses `!pm` instead. The error message was helpful, but the naming inconsistency between "palm" and "pm" is confusing.
- **Grid step counting**: Counting characters in drum grids by hand is error-prone. A drum grid with 17 steps instead of 16 is hard to spot visually without careful alignment checking.

## Workarounds used

- **Quoted complex note sequences**: Wrapped all note sequences starting with `[` in quotes to satisfy YAML's flow sequence syntax requirements.
- **Tab/pipe alignment**: Used consistent spacing and pipe delimiters in grid notation to make step counting easier (though still manual).
- **Note range constraints**: When a bass note was out of range (G0), simply transposed it to a valid range (E1) rather than restructuring the phrase.

## Features or changes wished to exist

- **Pattern name suggestions**: When referencing an unknown pattern, show available patterns in the error message (e.g., "did you mean 'groove'? Available: groove, fill").
- **Grid validation visualization**: A tool that shows where grid step boundaries are or auto-formats grids to make the 16-step structure more obvious.
- **Partial range notes with hints**: When a note is out of range, suggest the nearest valid note that would fit (e.g., "G0 is out of range E1-E4; did you mean G1?").
- **YAML auto-quoting**: Automatically quote bare sequences in note values to avoid YAML syntax errors, or provide clearer documentation about when quoting is needed.
- **Smart tie detection**: Warn or auto-correct when a tie connects to a different note pitch, as this is almost always a mistake.
