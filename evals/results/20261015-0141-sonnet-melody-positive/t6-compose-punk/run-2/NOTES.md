# Notes

## 1. What was hard or confusing
- SPEC.md is written in Chinese; the task and the tool docs are in English.
- Guitar chords must be fingerable, and the validator only says so after the fact. I used `beat voicing`-style power-chord shapes from memory, and they validated.
- Drum hand limits (2 hands per moment) interact with `add`, so crash-plus-hat or crash-plus-snare needs care. The `add` I used on beat 1 only collided with hits I had not written there.
- No audio render allowed, so the melody is judged only on paper.

## 2. Workarounds
- Eighth-note guitar chords are written as `(...)*8` repeats, since articulations do not carry over.
- The last chorus has no distinct ending, so the outro repeats the chorus melody on the tonic.
- The whole-note guitar ending uses a plain chord because I chose not to risk tie rules.

## 3. Wishes
- A `chords`-driven shorthand for power chords (e.g. `D5:8!pm*8`).
- Per-section tempo or mix automation, for example a lift in the final chorus.
- A `beat events` option that prints the melody as scale degrees or checks it against the declared chords.
