# Notes

## 1. What was hard or confusing
- SPEC.md is written in Chinese while the task and tool output are in English.
- Notes are strict about bar length. Mixing `:4.`, `:8` and `:2` in one bar needs careful hand arithmetic.
- It is unclear whether `%` in `replace` strings repeats the previous bar inside that string. I used it and it validated.
- Duration and velocity carry over between notes, but articulations don't. That makes palm-muted runs verbose.

## 2. Workarounds
- Merged the lead into the single `chorus` section so the same section name returns. It means the first chorus also has the lead melody.
- Wrote the chorus chords out as explicit notes, because `chords:` is only for validation and analysis.
- Used `!bend=1` and `!fall` for the solo phrasing, since there is no pre-bend or release-only bend.

## 3. Wishes
- Per-instance section overrides in `form`, such as `chorus+gt2`, so the lead only plays in the last chorus without a new section.
- Generating chord-strum or power-chord patterns from `chords:`.
- A way to name a rhythm and apply it to a chord list, like `strum_a` over `A D E A`.
- `beat events --by-bar` output that flags bars where a lead part is silent.
