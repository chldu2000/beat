# Beat DSL Transcription Notes

## What was hard or confusing

1. **Timeline semantics for bar boundaries**: The 1-based beat numbering (beats 1-4 corresponding to timeline positions 1-5) took time to internalize. It's counterintuitive that beat 4 actually spans positions 4-5, so position 4.667 is valid and within the bar.

2. **Incomplete bar descriptions**: The description sometimes specified notes that summed to less than 4 beats per bar. I had to infer that missing time should be filled with rests, but the spec could be more explicit about this requirement.

3. **Drum lane alignment with `hits` notation**: Managing multiple drum lanes across bars using `|` separators while ensuring proper alignment was error-prone. It's easy to get the bar counts wrong if one lane is shorter than others.

4. **Fractional vs. decimal notation**: Both `4.5` and `4+2/3` represent valid beat positions, but mixing them in the same file feels inconsistent. The spec recommends `+1/3` notation for triplets, which is good, but the visual distinction could be clearer.

5. **Notes extending past the barline**: The spec supports this via ties (`~`), but it requires the next bar to start with the same note at position 1, which is a strict constraint. When the next bar uses a different instrument/note, you can't easily extend the previous note.

## Workarounds used

1. **Filling incomplete bars**: For bars where the specified notes didn't total 4 beats, I added explicit rests (`r:bX`) to complete them. This ensures each bar is exactly 4 beats as required.

2. **Using ties for multi-bar notes**: For notes longer than one bar (e.g., organ chords lasting 8 beats across bars 4-5), I used the `~` notation to tie notes across barlines and continued with the same note in subsequent bars.

3. **Empty lanes in drum hits**: For drum lanes that had no hits in a particular bar, I left the space between `|` characters empty (or just spaces), which is valid but visually took a moment to verify was correct.

4. **Dynamic changes via `@` directive**: Guitar dynamics needed to change mid-section (p in bar 1 → f in bar 3 → mf in bar 6), so I used `@p`, `@f`, and `@mf` directives at the appropriate bar boundaries.

## Features or changes I wish existed

1. **Auto-filling rests**: If notes in a bar sum to less than the bar length, the DSL could automatically append a rest for the remainder, reducing manual work and error risk.

2. **Shorthand for notes spanning exact bar multiples**: Allow syntax like `E3:b6` to automatically span bars rather than requiring explicit ties and continuation. The compiler could intelligently split it as `E3:b4~ | E3:b2`.

3. **Dynamic support in drum hits**: Currently `@` directives only work in pitched notes. Supporting them in `hits` notation would allow more expressive drum patterns without needing the performance layer.

4. **Visual debugging for grid alignment**: A mode that shows bar numbers above each drum lane to catch alignment errors before validation.

5. **Optional "strict timing" flag**: Some user descriptions had notes that exceeded bar length by small amounts. An optional mode that auto-clips to bar boundaries (with a warning) could simplify transcription from imprecise descriptions.

6. **Cleaner syntax for layered hits**: When many drum lanes share the same hits (e.g., kick and crash both at beat 1), a shorthand like `bd+cr: 1` instead of listing them on separate lines could reduce repetition.
