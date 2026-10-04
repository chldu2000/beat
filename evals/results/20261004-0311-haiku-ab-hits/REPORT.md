# Eval report: 20261004-0311-haiku-ab-hits

model `haiku`, 3 run(s) per task

| task | final valid | first check clean | checks to green | F1 | dur acc | arts acc | dyn acc | task checks | chars/bar | cost $ | turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t1-transcribe-riff | 3/3 | 0/3 | 7.33 | 0.95 | 0.98 | 1.00 | 0.83 | — | 208.00 | 0.50 | 37.67 |
| t2-transcribe-tricky | 3/3 | 0/3 | 3.33 | 0.98 | 1.00 | 0.97 | 0.93 | — | 273.33 | 0.31 | 15.33 |

## Error categories (distinct errors seen during the session, summed over runs)

| task | first check | whole session |
|---|---|---|
| t1-transcribe-riff | token 13, bar_duration 3, yaml 2 | token 70, bar_duration 22, yaml 7, structure 6, other 3, bar_count 2, playability 2, tie 2 |
| t2-transcribe-tricky | token 7, bar_duration 2, other 2, bar_count 1 | token 68, bar_duration 31, other 12, bar_count 4, playability 2 |
| **all** | token 20, bar_duration 5, yaml 2, other 2, bar_count 1 | token 138, bar_duration 53, other 15, yaml 7, bar_count 6, structure 6, playability 4, tie 2 |

## Per run

### t1-transcribe-riff
- **run-1**: valid=True, error trace [1, 2, 1, 1, 3, 1, 0, 0, 0, 11, 15, 48, 6, 4, 2, 0, 0, 0, 0], F1=0.928, cost=$0.60
  - missing: dr bar 1 beat 1 hh; dr bar 1 beat 2.5 hh; dr bar 1 beat 3 hh; dr bar 2 beat 1 hh; dr bar 2 beat 2.5 hh; dr bar 2 beat 3 hh
  - extra: dr bar 1 beat 1.5 bd; dr bar 1 beat 3.5 bd; dr bar 2 beat 1.5 bd; dr bar 2 beat 3.5 bd; dr bar 3 beat 1.5 bd; dr bar 3 beat 3.5 bd
  - wrong_length: bs bar 3 beat 2.5 F1: 1.5 beats (dotted quarter) instead of 2.5 beats; gt bar 3 beat 2.5 F2: 1.5 beats (dotted quarter) instead of 2.5 beats; gt bar 3 beat 2.5 C3: 1.5 beats (dotted quarter) instead of 2.5 beats; gt bar 3 beat 2.5 F3: 1.5 beats (dotted quarter) instead of 2.5 beats
- **run-2**: valid=True, error trace [1, 9, 2, 0, 0, 0, 0, 0], F1=0.991, cost=$0.36
  - missing: dr bar 6 beat 1 rd; dr bar 7 beat 1 rd
  - extra: dr bar 6 beat 1 cr; dr bar 7 beat 1 cr
- **run-3**: valid=True, error trace [16, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0], F1=0.923, cost=$0.54
  - missing: bs bar 3 beat 2.5 F1; gt bar 3 beat 2.5 F2; gt bar 3 beat 2.5 C3; gt bar 3 beat 2.5 F3; dr bar 4 beat 2 hh; bs bar 4 beat 2.5 G1
  - extra: bs bar 3 beat 3 F1; gt bar 3 beat 3 F2; gt bar 3 beat 3 C3; gt bar 3 beat 3 F3; bs bar 3 beat 3.5 F1; gt bar 3 beat 3.5 F2
  - wrong_length: bs bar 3 beat 1 F1: 2 beats (half) instead of 1.5 beats (dotted quarter); gt bar 3 beat 1 F2: 2 beats (half) instead of 1.5 beats (dotted quarter); gt bar 3 beat 1 C3: 2 beats (half) instead of 1.5 beats (dotted quarter); gt bar 3 beat 1 F3: 2 beats (half) instead of 1.5 beats (dotted quarter); bs bar 4 beat 1 G1: 2 beats (half) instead of 1.5 beats (dotted quarter); gt bar 4 beat 1 G2: 2 beats (half) instead of 1.5 beats (dotted quarter)

### t2-transcribe-tricky
- **run-1**: valid=True, error trace [9, 2, 0, 0, 0], F1=1.0, cost=$0.27
- **run-2**: valid=True, error trace [1, 0, 0, 0], F1=0.996, cost=$0.30
  - missing: bs bar 1 beat 4.5 D2
- **run-3**: valid=True, error trace [2, 93, 14, 8, 0, 0, 0, 0, 0], F1=0.95, cost=$0.36
  - missing: dr bar 1 beat 1+2/3 rd; dr bar 1 beat 2+2/3 rd; dr bar 1 beat 3+2/3 rd; dr bar 1 beat 4+2/3 rd; dr bar 3 beat 1 hh; dr bar 3 beat 2 hh
  - extra: dr bar 1 beat 1+667/1000 rd; dr bar 1 beat 2+667/1000 rd; dr bar 1 beat 3+667/1000 rd; dr bar 1 beat 4+667/1000 rd

## Agent notes

### t1-transcribe-riff / run-1

# Beat DSL Observations

## What was hard or confusing

1. **YAML structure**: The proper hierarchy took several iterations to get right. Parts must be defined directly within sections (under `sections > main > parts`), not in a separate `performance` section. The documentation hint pointing to `SPEC.md` and examples helped clarify this.

2. **Cross-barline notes**: Handling notes that extend past the barline is complex. Using `~` for ties seemed intuitive, but getting the exact duration calculations right required careful consideration of which beats map to which bars.

3. **Duration notation complexity**: The DSL uses two different duration systems:
   - Note-based durations (4 = quarter, 8 = eighth, 4. = dotted quarter)
   - Beat-based durations (`:b2.5` = 2.5 beats)
   - Mixing these correctly required understanding when each applies.

4. **Drum lane syntax**: Figuring out the available drum lanes (bd, sd, hh, rd, t1, t2, t3, cr, etc.) and their exact names required referencing error messages since they weren't initially obvious.

## Workarounds used

1. **Avoided cross-barline notes**: Rather than having bass/guitar notes extend across bars with ties, I split them at the barline when necessary. This simplified validation but meant some compound note patterns became rests within bars.

2. **Empty bars for drum lanes**: When certain drum lanes (like hh = hi-hat) didn't have hits in later bars (5-8), I represented them with empty bar slots (just `|` with no hits) rather than explicitly listing rests.

3. **Beat-based rest notation**: Used `r:bX` notation to fill gaps in bars where no instrument had notes, ensuring each bar exactly filled 4 beats.

## Features or changes that would be helpful

1. **Pattern repeat syntax**: A way to reference repeated patterns without restating all 8 bars. Currently, drum patterns that repeat across bars must be written out fully or use the `replace` mechanism, which requires understanding the replace syntax.

2. **Better cross-barline note documentation**: More examples and clearer guidance on using `~` ties would help. The behavior of tied notes extending into the next bar could be better documented.

3. **Drum lane "fill" option**: Instead of requiring every lane to be specified for every bar, a way to say "only list hits for lanes that have notes, fill the rest with rests automatically" would reduce boilerplate.

4. **Duration parsing flexibility**: Accepting duration formats like `2.5` directly instead of requiring `:b2.5` for beat-based durations would be more intuitive for beat counts.

5. **IDE hints**: Error messages sometimes required trial-and-error to understand what was expected. Better error messages or IDE autocomplete would help (e.g., "expected one of: bd, sd, hh, ..." in the error for unknown drum lanes).

### t1-transcribe-riff / run-2

# Beat DSL Evaluation Notes

## What Was Hard or Confusing

1. **Gaps in drum patterns**: When drum events don't occur at consecutive beats (e.g., beats 3→3.5 with nothing at beat 3), it's unclear whether this represents a rest or just sparse notation. The validator catches it, but the spec could be clearer about whether gaps require explicit rests.

2. **Articulation syntax ordering**: Initially confused about whether articulations come before or after durations (should be `NOTE:DURATION!ART`, not `NOTE!ART:DURATION`). The spec clearly states this, but the counterintuitive ordering tripped up early attempts.

3. **Drum lanes with overlapping beats**: When using `hits` format with multiple drum lanes, figuring out which lanes should have simultaneous strikes at the same beat required careful reading of the drum specification (e.g., kick + hi-hat at beat 1 means adding to both `bd:` and `hh:` lines).

4. **Ride cymbal timing edge case**: The ride cymbal in bar 5 starts at beat 1.5, not beat 1, requiring careful distinction between when crash vs. ride occurs. The spec doesn't explicitly warn about common edge cases like this.

## Workarounds Used

1. **Filling temporal gaps with explicit rests**: Since bar 4 of the intro had unintended silence between beat 3 and 3.5, explicitly added `r:b0.5` to fill the gap rather than relying on implicit rests.

2. **Explicit beat lists instead of ranges**: For drums, used explicit beat listings (e.g., `rd: 1.5 2 2.5 3 3.5 4 4.5`) instead of `every 0.5` when patterns had exceptions (like excluding beat 1).

3. **Patterns for repetitive sections**: Defined reusable patterns (`drum_main`, `drum_fill`, `drum_ride`) to avoid repeating identical bars, though patterns required careful beat-by-beat specification rather than higher-level abstractions.

## Features That Would Be Helpful

1. **Shorthand for conditional rhythms**: A way to express "every 0.5 beats except beat 1" would reduce boilerplate. Something like `rd: every 0.5 except 1` or `rd: 1.5-4.5 by 0.5`.

2. **Better error messages for duration mismatches**: When a bar's notes sum to 3.5 instead of 4 beats, showing which beats are missing would help faster iteration (e.g., "missing 0.5 beats; gap found between beats 3-3.5").

3. **YAML anchors in drum patterns**: Allow `&anchor` / `*anchor` references for common drum beat configurations to reduce pattern duplication (e.g., defining a standard hi-hat pattern once and reusing it).

4. **Implicit rests for gaps**: Auto-fill temporal gaps with rests instead of requiring manual `r:b...` notation, since rests are usually unintentional omissions rather than creative choices.

5. **Note range/repetition in drum hits**: For patterns like "snare at 3, 3.25, 3.5, 3.75", allow something like `sd: 3+0.25*4` or `sd: 3 to 3.75 step 0.25` to avoid listing every beat.

6. **Visual bar ruler in `--by-bar` output**: The compact view is helpful, but showing beat positions (e.g., `|1--|2--|3--|4--|`) would make parsing by eye easier.

### t1-transcribe-riff / run-3

# Notes on Beat DSL

## What Was Hard or Confusing

1. **Bar duration validation with `:b` notation**: The `:b` (beats) notation seemed inconsistent during validation. When using `:b0.5`, `:b1.5`, etc. for specifying durations in beats, the validator wasn't consistently counting them toward the 4-beat bar total, even though mathematically they added up correctly. Standard note durations (`:1`, `:2`, `:4`, `:8`) worked more reliably.

2. **Multi-line vs. single-line note formatting**: Notes written across multiple lines with `|` bar separators (using `|` at line breaks) behaved differently than writing all bars on a single line. The parser seemed to work more reliably with everything on one line separated by spaces and `|` characters.

3. **Dotted note durations**: Dotted notes like `:4.` (dotted quarter = 1.5 beats) appeared to have parsing issues when mixed with other duration notations in the same bar. Using simpler integer-based note lengths avoided these issues.

## Workarounds Used

1. **Avoided `:b` notation in favor of standard durations**: Instead of `G1:b1.5 G1:b0.5 G1:b0.5!acc`, I used `G1:2 G1:8 G1:8!acc` to achieve the same timing with standard note values.

2. **Wrote notes on a single line**: Instead of:
   ```yaml
   notes: |
     note1 | note2 |
     note3 | note4
   ```
   I used:
   ```yaml
   notes: "note1 | note2 | note3 | note4"
   ```

3. **Simplified rhythmic patterns**: Where the description suggested complex note combinations, I used simpler subdivisions (e.g., `F1:2 F1:8 F1:8 F1:4` instead of trying to express `F1:b1.5 F1:b2.5`).

## Features or Changes Wished For

1. **Better error messages for `:b` notation**: If the `:b` (beats) notation is supported, the validator should provide clearer error messages explaining why certain durations aren't being recognized or counted.

2. **Clarification on multi-line note formatting**: The spec should explicitly state whether notes can span multiple lines within the `|` block, or if all bars must be on a single line for reliable parsing.

3. **Support for mixed notation flexibility**: Allow seamless mixing of different duration notations (`:1 2 4 8 16 32` with dotted variants and `:b` notation) within the same bar without parsing issues.

4. **Validation suggestions for bar duration mismatches**: When a bar is short or long by a specific amount, suggest not just "add r:b0.5" but provide context about what's actually parsed in that bar.

5. **Preview or dry-run mode**: A way to see how the parser is interpreting a section before full validation, to debug notation issues more quickly.

### t2-transcribe-tricky / run-1

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

### t2-transcribe-tricky / run-2

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

### t2-transcribe-tricky / run-3

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

