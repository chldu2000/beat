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
