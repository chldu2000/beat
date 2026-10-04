# Beat DSL Experience Notes

## What was hard or confusing

- **Grid notation ambiguity**: The 16-character grid format is clear once you understand it represents 16th notes, but the mapping from beat positions to grid positions (e.g., beat 3 = positions 8-11) requires counting and mental arithmetic.
- **Drum lane naming**: Abbreviations like `sd` (snare), `bd` (kick), `hh` (hi-hat), `cr` (crash), `rd` (ride) are not immediately obvious without consulting examples.
- **Chord voicing choices**: Determining appropriate octaves and voicings for organ chords required examining existing patterns rather than having explicit conventions in the spec.
- **Performance offset semantics**: It's unclear whether negative offsets are possible or if the offset direction is always "lay back" (push later in time).

## Workarounds used

- **Rests for silent instruments**: Used `r:1` notation to keep gt2 silent in the bridge rather than omitting the part entirely, maintaining consistency with the song structure.
- **Power chord spelling**: Inferred power chord voicings (e.g., `[A2 E3]` for Am) by pattern-matching against similar chords in existing sections (chorus chords).
- **Half-time drum pattern**: Created the half-time feel by hand-crafting a simple beat_bridge pattern with just bd and sd lanes rather than building it from humanize parameters.

## Features or changes wished existed

- **Explicit beat-to-grid mapping**: A helper tool or clearer documentation showing beat numbers and their grid positions (e.g., "beat 3 = positions 8-11").
- **Chord voicing templates**: Built-in chord voicing suggestions for different instruments (bass roots, guitar shells, organ triads) to avoid guesswork.
- **Part inheritance with modifications**: A way to say "use this drum pattern, but keep only the snare lane" without duplicating patterns.
- **Visual preview**: A simple ASCII timeline view showing where hits occur relative to beat numbers (e.g., showing beat 1, 2, 3, 4 labels above the grid).
- **Validation hints**: When a part is omitted, an optional warning or note to confirm it's intentional (silent tracks can be easy to forget).
