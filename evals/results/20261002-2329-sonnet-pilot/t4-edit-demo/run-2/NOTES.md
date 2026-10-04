# Notes

## 1. What was hard or confusing
- The spec and tool help are in Chinese; mapping terms like "lane", "grid steps", and chord
  voicing rules to the right YAML keys took a careful re-read before editing.
- It's not obvious from the spec alone what counts as a valid "power chord" voicing for the
  guitar fret-span/playability check; I had to infer the convention (root-fifth-octave) from
  existing sections rather than from an explicit rule.
- Drum grids use absolute step positions (e.g. step 9 of 16 for beat 3), so translating "snare
  on beat 3" into `-`/`X` characters requires doing the beat-to-step arithmetic by hand.

## 2. Workarounds
- No direct "chord root to MIDI note" helper exists, so bass/organ/guitar pitches for the new
  bridge chords (Am, C, D, B) were chosen manually by matching octave/voicing conventions already
  used elsewhere in the song (e.g. reusing the `[C3 G3 C4]`-style power-chord shape and the
  organ's triad voicings from the chorus).
- "Half-time feel, snare only on beat 3" has no dedicated grid shorthand, so it was written as a
  plain grid with a single `X` per bar rather than reusing a pattern.

## 3. Features I wish existed
- A way to reference "chord root" or "chord tones" symbolically in `notes`/`grid` (e.g. `root:1`)
  instead of hand-picking MIDI pitches that match a section's `chords:` line.
- A `beat diff` command to compare two versions of a song's compiled events, to make confirming
  "only X changed" type edits (like the snare offset) easier than manually re-reading timestamps.
