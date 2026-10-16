# Notes

## 1. What was hard or confusing
- SPEC.md is in Chinese while the task and tool output are in English; I had to read it carefully for details.
- It is unclear whether `extends` creates a "different section" for the "chorus must return" requirement, so I reused the same `chorus` section twice and put the lead in it both times.
- Bar totals with `%` and `*n` repeats are easy to miscount without validating.
- Guitar chord playability is only discovered at validation time.

## 2. Workarounds
- The lead can't differ between two instances of one section without a new section, so gt2 plays the melodic line in every chorus instance.
- Power chords were written by hand (standard shapes) instead of calling `beat voicing`.
- Tempo, key and chords are fixed per file, so the "A major" feel comes from the chord symbols and note choice only.

## 3. Wishes
- Per-instance overrides in `form` (e.g. `chorus: {gt2: ...}`) without defining a new section.
- Chord-symbol-driven bass/rhythm generation.
- A `beat events` warning when the lead only arpeggiates chord tones.
- English version of the spec.
