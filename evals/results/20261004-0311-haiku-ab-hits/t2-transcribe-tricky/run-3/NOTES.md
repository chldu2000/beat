# Beat DSL Transcription Notes

## 1. Hard or Confusing Things

- **Triplet notation**: Representing triplet eighth notes required using `:b1/3` for beat-duration notation rather than standard note-value notation (`:8`, `:16`, etc.). The distinction between note-value durations and beat-duration notation took experimentation to understand.

- **Bar structure and spanning notes**: Notes that extend across barlines must be explicitly split with ties (~). The validator strictly enforces that each bar contains exactly 4 beats, forcing careful management of notes that span multiple bars.

- **Beat position numbering**: The description used positions like "1+2/3" for triplet positions, which required converting to decimal (1.667) or exact fractions. The Beat DSL's handling of fractional beat positions within triplets wasn't immediately clear.

- **Articulation name mapping**: Some articulations from the description didn't directly map to Beat DSL. For example, "flam" for drums and "ghost note" for quiet snare hits don't have explicit articulation modifiers (though the notes themselves are played correctly). Finding that !h means hammer-on and !p means pull-off required trial and error.

- **Drum hit vs. pitched note syntax**: Drums use a different syntax (lane-based hits format) compared to pitched instruments (note-based format), which required understanding two different notational systems within the same file.

## 2. Workarounds Used

- **Ghost notes without modifiers**: Silent or quiet snare hits (ghost notes) are represented simply as snare hits without articulation markers, relying on the drum interpretation to understand they should be soft.

- **Flam without modifier**: Drum flams couldn't be explicitly represented with an unsupported articulation, so they're included as standard snare hits that would be interpreted as flams by the performer.

- **Triplet duration in fractions**: Used `:b1/3` for one-third beat durations to represent eighth-note triplets, since standard note durations (1, 2, 4, 8, 16, 32) don't support triplets directly.

- **Decimal approximations for complex beat positions**: Converted "1+2/3" beat positions to 1.667 decimal notation for use in drum hits, though Beat DSL's beat-event output shows these as fractions (1+2/3).

## 3. Wished Features

- **Direct triplet notation**: A syntax like `:8t` or `:triplet-8` for triplet note values would be clearer than having to use beat-duration notation for triplets.

- **Flam and ghost-note articulation markers**: Explicit !flam and !ghost modifiers would allow annotating these techniques directly in the notation rather than relying on semantic interpretation.

- **Implicit bar duration padding**: Auto-padding incomplete bars with rests instead of requiring explicit `r:2` entries would reduce boilerplate and error-prone manual bar length calculations.

- **Cross-bar note groups**: Allow grouped notes (like rapid sixteenths or rolls) to span barlines without requiring manual splitting and careful duration arithmetic.

- **Drum-lane specific modifiers**: Ability to apply articulations differently per drum voice (e.g., a snare that's both accented and on the flam) without complex parsing.
