# Beat DSL Observations

## What Was Hard or Confusing

1. **Grid format with fixed 16-step resolution**: Grids expect exactly 16 sixteenth-note positions per bar. This fixed resolution makes it difficult to specify rhythms that don't align perfectly with sixteenth notes. The position-to-beat mapping (0→1.0, 1→1.25, 2→1.5, etc.) had to be worked out manually and is easy to get wrong.

2. **String format for rhythms**: The DSL requires writing notes and drums as inline strings with no support for semantic markup (like `A1*2` for repetition or `A2_D3` for chords). Each rhythm pattern must be manually written out as a visual grid or sequence.

3. **Limited note specification**: The simple `notes` format treats each pitch as a quarter note with no built-in way to specify different durations, articulations, or simultaneous notes (chords). This forces users to either write many repetitions or switch to a different format.

4. **Validation error messages**: Some error messages like "cannot parse articulations '_D3'" were cryptic—it wasn't immediately clear that underscores were being interpreted as articulation syntax rather than chord separators.

## Workarounds Used

1. **Grid notation for drums**: Used the grid format (e.g., `bd: x-------x-------`) instead of the notes format because it allows precise position-based specification of hits.

2. **Single-bar sections**: Rather than trying to define multi-bar sections with complex patterns, broke the song into 8 sections (one per bar) to avoid grid length calculation errors.

3. **Simplifying the bass/guitar parts**: Due to the limitations of the `notes` format (one quarter note per pitch), I wrote 4 quarter notes per bar instead of the original 8 eighth notes. The chords specified in the task (like F2-C3-F3) were also simplified to single pitches.

4. **Grid padding**: Carefully constructed grid strings to be exactly 16 characters by padding with dashes, using the validated `sd: ----x---xxxx----` pattern as a reference template.

## Wishlist Features

1. **Duration syntax**: A way to specify note lengths directly, like `A1/0.5` for eighth notes or `A1/2` for half notes, without requiring repetition or special formatting.

2. **Chord notation in notes format**: Support for brackets or commas to group pitches, like `[A2 E3]` or `A2,E3` for simultaneous notes.

3. **Repeat/loop syntax**: Pattern repeats like `A1*4` to write 4 A1's, reducing redundancy in simple patterns.

4. **Relative grid positioning**: Instead of fixed 16-step grids, allow grids to be specified relative to beats, like `beat_1: x`, `beat_1.5: x`, `beat_2: x` which the system would expand.

5. **Better error messages**: Clearer validation errors that explicitly state what characters/formats are reserved or invalid (e.g., "underscore is reserved for articulation syntax, use [pitch pitch] for chords").

6. **Visual grid editor**: A visual tool to draw out drum patterns and see the 16-step grid positions overlaid with beat numbers, reducing manual counting errors.
