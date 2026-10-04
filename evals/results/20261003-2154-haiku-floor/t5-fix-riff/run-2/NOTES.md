# Beat DSL Notes

## Hard or Confusing

- **YAML syntax with note arrays**: Note values starting with `[` need to be quoted or YAML interprets the bracket as syntax. The error message was helpful but initially surprising.
- **Pattern name typos**: A typo like `grove` instead of `groove` passed YAML validation but failed at pattern resolution, requiring a separate validation pass to catch.
- **Drum grid step counting**: Counting steps in drum grids (particularly with pipes separating bars) requires careful attention to spacing. A single missing space throws off the count, and the error points to the bar but requires manual inspection to locate the exact issue.
- **Bass instrument range constraints**: The bass instrument has a fixed range (E1-E4) which is restrictive for some musical ideas. The error message was clear but it wasn't obvious upfront.
- **Tie semantics**: Ties (`~`) can only connect identical notes. A tie from F1 to G1 is invalid, which requires understanding that ties are specifically for extending duration, not for portamento.

## Workarounds

- **Quoted note values**: Wrapped all notes starting with `[` in quotes to comply with YAML parsing rules.
- **Removed invalid tie**: Removed the tie from F1 to G1 and let them be separate notes, preserving the rhythmic intent.
- **Explicit chords per bar**: Instead of a more compact chord syntax, specified each bar's chord explicitly (`Am | Am | F | G`).
- **Careful drum grid formatting**: Paid close attention to space alignment in drum grids to ensure exact 16-step counts per bar.

## Features or Changes Wished

- **Smarter note range defaults**: Allow bass to drop below E1 for specific parts, or at least provide an override mechanism without requiring instrument redefinition.
- **Better drum grid validation**: Auto-pad or provide a clearer error that shows the exact bar with count, possibly with a visual ruler.
- **Flexible chord syntax**: Support chord shorthand for repeated progressions (e.g., `Am(2) F G` instead of `Am | Am | F | G`).
- **Tie alternatives**: Add a portamento or glide notation distinct from ties, allowing smooth transitions between different notes.
- **Pattern validation in context**: Validate that pattern references (like `use: groove`) exist before other validations run, to catch typos earlier.
