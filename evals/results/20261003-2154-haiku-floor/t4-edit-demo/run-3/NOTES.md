# Beat DSL Notes

## Hard or Confusing

- **Multi-bar grid format**: It wasn't immediately clear that bars should be separated with `|` rather than split across multiple lines. The error message helped but would have saved time with clearer documentation.
- **Chord voicing octaves**: Determining the right octaves for chord voicings (Am as [A3 C4 E4]) required trial and error to get a balanced sound across the register.
- **Silent parts**: It took investigation to confirm that omitting a part entirely makes it silent, as opposed to providing explicit rest notes.
- **Power chord notation**: The convention for power chords using root and fifth (e.g., [A3 E4]) versus root-fifth-octave voicings could be clearer in examples.

## Workarounds

- **Multi-bar grids**: Used explicit `|` separators to define the same snare pattern across all 4 bridge bars rather than creating a separate pattern.
- **Organ voicings**: Selected specific octaves and note combinations manually to match the existing chord style rather than deriving them algorithmically.
- **Half-time drums**: Defined the snare on beat 3 directly in the bridge section's grid rather than creating a reusable pattern (simpler for a one-off).

## Wished Features

- **Grid pattern repetition syntax**: A way to repeat grid patterns concisely, like `(sd: --------X-------)*4` instead of explicit bar-by-bar duplication.
- **Relative octave notation**: Allow octaves relative to a section or part baseline (e.g., `+2` instead of absolute octave numbers).
- **Part inheritance with muting**: An explicit way to say "use this part but silent" rather than omitting it entirely.
- **Better error messages for grids**: Report errors per-bar when a grid has issues, not just the concatenated version.
- **Chord voicing helpers**: Built-in utilities or templates for common voicing patterns (triads, shells, power chords) by root and chord type.
