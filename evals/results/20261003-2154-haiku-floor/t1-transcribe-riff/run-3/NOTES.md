# Beat DSL Experience Notes

## 1. Difficult or Confusing Aspects

- **Duration inheritance and note parsing**: The spec describes duration inheritance, but consecutive notes with the same pitch sometimes fail to parse as separate events. Using `G1:8 G1:8` was parsed as 0.5 beats instead of 1 beat, requiring the final note to use a different duration value (`G1:4`) to force recognition.

- **Drum grid step counting**: Calculating exact 16-step grids for drum patterns while using spaces for beat grouping requires careful counting. The specs state spaces are ignored, but they affect readability and potential confusion about whether a bar has exactly 16 characters.

- **Bar-spanning notes ambiguity**: When a note's specified duration would extend past a bar boundary, it's unclear whether it should use tie notation (`~`), be truncated to fit, or extend into the next bar. The spec mentions ties are for connecting across bars, but resolution is unclear when the next bar contains a different pitch.

- **Rest notation and syntax**: Initially unclear whether rests (`r:8`) should be explicitly written or if gaps between notes are implicit. The YAML multiline format (using `>-`) didn't resolve parsing issues, suggesting the problem is in the DSL parsing itself rather than YAML formatting.

## 2. Workarounds Used

- **Duration variations instead of repetition**: When consecutive identical notes of the same duration failed to parse, I used different durations (`G1:8` followed by `G1:4`) to ensure each note was recognized as a separate event.

- **Explicit grid formatting**: Used verbose 16-character strings for drum grids with explicit dashes to ensure each bar was exactly 16 steps, avoiding ambiguity about spaces and separators.

- **Multiline notes with `>-`**: Split long notes specifications across lines for readability, though this didn't resolve the parsing issues I encountered.

- **Bars calculated separately**: Verified each bar's total duration independently (1 + 0.5 + 0.5 + 0.5 = etc.) before combining into the file, catching duration mismatches early.

## 3. Desired Features or Changes

- **Better support for identical consecutive notes**: Allow `G1:8 G1:8` to unambiguously parse as two separate eighth notes without requiring syntax workarounds like `(G1:8)*2` or duration variation.

- **Clearer bar boundary semantics**: Explicit rules for notes that extend past bar boundaries—whether they require ties, automatic truncation, or error reporting.

- **More flexible rest notation**: Support implicit rests between notes (e.g., assuming silence fills gaps) or require explicit gaps to be specified without rest notation.

- **Diagnostic output during validation**: Show exactly which notes are being parsed, their parsed durations, and the computed total for each bar to help debug duration mismatches.

- **YAML-agnostic syntax**: Decouple the DSL syntax from YAML parsing to reduce confusion about when line breaks, spaces, and continuation are significant.

- **Accent/articulation on specific positions**: Currently `!acc` is attached to individual note specifications. It would be clearer to optionally specify accents separately from the note (e.g., in a metadata section) for cases where many notes of the same pitch need different articulations.
