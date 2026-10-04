# Beat DSL Transcription Notes

## 1. What Was Hard or Confusing

- **Beat-to-grid step conversion**: Converting fractional beat positions (like beat 1+2/3) to grid step positions requires careful calculation. The formula `(beat - 1) * 4 + 1` must be applied precisely, and rounding errors of ±0.08 beats are unavoidable when beat positions don't align to sixteenth-note boundaries. For example, beat 1+2/3 (1.667) rounds to step 4 (beat 1.75).

- **Grid character counts**: Each drum lane in a multi-bar grid must total exactly 16 × (number of bars) characters. Subtle issues like writing 15 dashes instead of 16 caused validation failures. The pipe (|) and space characters are ignored for counting, which is helpful for readability but easy to miscalculate.

- **Note duration syntax**: The Beat DSL uses numeric values (1, 2, 4, 8, 16, 32) where larger numbers mean shorter durations (like traditional music notation). This is counterintuitive at first. Also, dotted values (like 4.) add 50%, and triplet values (like 4t) multiply by 2/3, which requires mental arithmetic.

- **Handling gaps in the bar**: When a musical description only specifies notes for part of a bar (e.g., notes at beats 1-3, with beat 4 unspecified), I needed to explicitly fill the gap with rests to reach exactly 4 beats total per bar.

- **Drummer hand constraints**: The validator enforces realistic hand usage (max 2 hands for hand-played instruments). A flam counts as 2 hands. This constraint can require moving drum hits to different positions or times if the description conflicts with physics.

## 2. Workarounds Used

- **Using ties for split notes**: When the description listed the same note twice in sequence (e.g., "beat 1: B1, 2.5 beats" followed by a beat 3.5 note), I used the tie notation (`B1:2~ B1:8`) to represent a continuous 2.5-beat note split across the DSL's beat boundaries.

- **Mapping triplet rhythms to the grid**: Triplet subdivisions (1/3 beat) don't align perfectly with the 16-step sixteenth-note grid. I calculated the nearest step position and accepted minor timing rounding (±0.08 beats).

- **Multi-bar tied notes**: For notes spanning multiple bars (like the 6-beat organ chord in bars 1-2), I split the note into separate bars with the first using a tie (`[E3 G3 B3]:1~`) and the second continuing without the tie (`[E3 G3 B3]:2`).

- **Explicit grid strings for empty bars**: When a lane (e.g., hi-hat in bar 1) had no notes, I filled it with the full 16-dash string (`----------------`) rather than leaving it empty, to avoid length validation errors.

## 3. Features or Changes I Wish Existed

- **More flexible step sizes per bar**: Allow specifying step size on a per-bar basis without nesting in `replace`, to handle non-grid-aligned rhythms (like 1/3-beat triplets) more naturally.

- **Automatic rest-filling**: Automatically fill incomplete bars with rests rather than requiring explicit `r:4` notation, since musical bars are always complete.

- **Beat-based grid notation alternative**: Offer an optional beat-indexed notation for drums (e.g., `bd: {1, 3}` meaning hits at beats 1 and 3) as an alternative to the character-grid format, which would eliminate off-by-one counting errors.

- **Clearer error messages for grid length mismatches**: Show the actual character count and expected count per bar, not just "has 15 steps, expected 16", which doesn't help identify which bar or character is wrong.

- **Support for swing/triplet grid modes**: Allow setting `steps: 12` (triplet eighths) for the entire section without needing `replace`, to handle shuffle and swing patterns more idiomatically.

- **Articulation visualization**: Include articulations (ghost notes, flams, accents) in the `--by-bar` events output by default, to verify that articulation markings were parsed correctly.
