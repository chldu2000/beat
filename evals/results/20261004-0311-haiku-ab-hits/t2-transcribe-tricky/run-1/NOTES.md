# Beat DSL Transcription Notes

## What was hard or confusing

1. **Drum lanes requiring complete bar coverage**: All drum lanes must explicitly list hits for every bar in the section, even if some bars are empty. Empty bars need placeholder separators (`|`), which wasn't immediately obvious from the spec.

2. **Tie notation and bar crossing**: Understanding that notes cannot cross bar lines and must be split with ties (`~`) to continue in the next bar took some trial-and-error, especially when instruments like the organ had notes spanning multiple bars (e.g., 6 or 8 beats).

3. **Beat position arithmetic**: Converting between fractional beat positions (e.g., "beat 1+2/3") and time durations required careful calculation to ensure each bar totaled exactly 4 beats. Ghost notes and articulations made visual verification harder.

4. **Hand availability for drummers**: The validation that drummers can only play 2 hand-played instruments at once was initially surprising. For example, having side stick + ride cymbal at the same beat is valid (2 hands), but adding snare would fail.

5. **Dynamics application**: Understanding that `@f` (dynamic marking) applies to subsequent notes and affects their force/velocity took clarification. The order matters: dynamics marked at the start of a bar affect all following notes until another dynamic is marked.

## Workarounds used

1. **Multi-line notes with `>-`**: Used YAML's multi-line scalar `>-` for long pitch note sequences to improve readability while keeping all notes in one notes field.

2. **Separating drum voices**: Organized each drum voice (bd, sd, hh, etc.) on separate lines in the hits block rather than trying to represent them inline, which made bar-by-bar verification easier.

3. **Explicit beat-by-beat mapping**: For bars with complex rhythms, I manually tracked each beat position (1, 1.5, 1.75, 2, 2.5, etc.) to ensure no gaps or overlaps when summing durations.

4. **Fractional beat notation (`:b`) for precision**: Used `:b` (beat-based duration) notation extensively instead of musical note values (`:8`, `:16`, `:4.`) for calculations involving triplets and sixteenths, which reduced rounding errors.

5. **Pattern-less structure**: For a 6-bar piece, I avoided creating patterns and just wrote all bars inline in the main section, which was simpler than setting up replacements.

## Features or changes I wish existed

1. **Per-bar dynamic/articulation overrides in hits**: Ability to write `2!acc!ghost` in one place rather than requiring separate lanes. The current lane-based system is verbose for complex polyrhythmic patterns.

2. **Automatic bar-spanning tie handling**: Let me write `E3:b6` across bars 4-5 without manually breaking it into `E3:b4~ | E3:b2`. The compiler could auto-split at bar boundaries.

3. **Drum grid with more granularity options**: The grid format is great for visual patterns, but for hits, being able to write `every 0.5` for eighth-note hi-hats is simpler than listing every single beat. More "every" patterns for triplets (already supported as `every 1/3`) would help.

4. **Validation warnings for incomplete bar fills**: A warning when a bar has less than 4 beats of content (or exactly 4 but with suspicious gaps) would catch mistakes earlier. Same for bars with 4.0001 beats due to rounding.

5. **Beat position aliases**: Support writing `beat 3` instead of `3` in hits for clarity, or even `beat_3_triplet_2` → `3+1/3`. The current numeric-only syntax is terse but can be error-prone.

6. **Humanization per-instrument presets**: Pre-configured humanize profiles like `humanize: jazz` or `humanize: metal` instead of manually tweaking `timing_ms` and `velocity` for each part.
