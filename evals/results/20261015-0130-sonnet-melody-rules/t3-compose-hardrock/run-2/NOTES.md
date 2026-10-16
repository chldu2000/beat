# Notes

## 1. What was hard or confusing
- `:4` means quarter note and `:1` a whole note, so `:2~ :4` takes some care. Numeric durations also carry over to the next note, so I spelled them out to avoid bar-sum errors.
- The 2-hand limit for drums made the chorus pattern awkward. A crash plus hi-hat plus snare on beat 1 is illegal, so I used ride instead of hi-hat.
- SPEC.md is written in Chinese. That is fine, but it is worth knowing.
- I could not hear the result. Only validation and the event view checked the bar math, so the musical feel is unverified.

## 2. Workarounds
- The same `chorus` section is used twice, so the lead plays in both choruses. The DSL has no way to say "only in the last instance" short of a separate section.
- Fills are one-bar patterns swapped in with `replace` on the final bar of a section.
- Power-chord shapes were written by hand (A5 = `[A2 E3 A3]`) rather than looked up.

## 3. Wishes
- A per-instance override in `form`, such as `chorus+solo`, so a section can vary without needing a new section.
- Chord-symbol shorthand in `notes`, such as `A5:4.`, that expands to the guitar voicing.
- Auto-generated bass from `chords`.
- Warnings that say the section-level beat sums are fine, plus a `--by-bar` view for drums that shows hand counts.
