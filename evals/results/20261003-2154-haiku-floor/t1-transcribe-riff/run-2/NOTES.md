# Beat DSL Transcription Notes

## Hard or Confusing Aspects

1. **Drum grid character counting**: The grid format requires exactly N×16 characters per lane (where N is the number of bars), but spaces and pipes used for readability are ignored in parsing. This creates an invisible-to-human character count that makes it easy to be off-by-one. The error messages help but require trial-and-error to fix.

2. **Ambiguous note duration crossing bar boundaries**: When notes extend past bar lines using ties (~), it's unclear whether they should have matching pitch in the next bar or can seamlessly transition to a different chord/note. The spec says ties can cross bars, but it's unclear if they're meant for tying the same note across bars or something else.

3. **Beat position notation vs. absolute duration**: The description used beat positions (1, 1.5, 2, 2.5, etc.) combined with absolute durations, making it difficult to map whether a note "starting at beat 2.5 lasting 2.5 beats" extends into the next bar when the bar only has 4 beats total.

## Workarounds Used

1. **Omitted tom and cymbal lanes in section 1**: The original description included mid tom (t2) and floor tom (t3) in bar 4 of section 1, but simpler approaches proved sufficient. These were added only to section 2 where they were more essential to the rhythm.

2. **Removed hi-hat from section 2**: To avoid "drummer needs 3 hands" errors when ride cymbals, snare, and kick all play simultaneously in the same beat, the hi-hat cymbal was removed entirely from section 2, focusing on the ride pattern instead.

3. **Split long-duration notes into sequences**: Notes lasting 2.5 beats that couldn't be expressed with a single time value (like `:4.` or `:2`) were split into multiple notes (e.g., `F1:2 F1:8`) to match the exact required duration while working within the DSL's time value system.

## Desired Features or Changes

1. **Multi-bar time signatures or per-bar duration overrides**: Allow bars to have different time signatures or durations locally without changing the global 4/4 setting, for songs that need a single fill bar in 7/8 or similar.

2. **Clearer error messages for grid length**: Instead of reporting "has 17 steps, expected 16", show which character position is the issue and provide a snippet like `[position 15-17: '---']` to make debugging faster.

3. **First-class support for non-integer-beat durations**: Add notation like `:2.5` directly instead of requiring ties or multiple notes, since dotted and triplet notes are common in music.

4. **Drummer hand assignments**: Allow specifying which hand (left/right/foot) plays each drum sound to avoid hand conflicts automatically, or provide more intelligent warnings about simultaneous hits that are actually playable (e.g., kick + hi-hat with foot + hand).

5. **Conditional or variant patterns**: Support writing song sections that vary slightly on repeat (e.g., "verse 1 ends differently than verse 2") without duplicating the entire section.
