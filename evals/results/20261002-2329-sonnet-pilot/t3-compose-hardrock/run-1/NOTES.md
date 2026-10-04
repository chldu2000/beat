# Notes on composing with the Beat DSL

## 1. What was hard or confusing

- It's not obvious from `SPEC.md` alone which guitar chord voicings will pass the
  "playable chord" validator (distinct strings, max-min fret span <= 4, excluding
  open strings). I had to manually map notes to strings/frets by hand before
  `validate` would confirm a 5-note chord like `[A2 E3 A3 C#4 E4]` was legal; a
  6-note version of the same chord failed and I only found out by trial and error.
- `replace` on a bar replaces the *entire* bar's content, not just the lane/voice
  you want to change. For drums this means adding a crash on bar 1 of a pattern
  required re-typing the `hh`/`sd`/`bd` lanes that were already correct in the
  base pattern, instead of just adding a `cr` line.
- The relationship between `chords` (an annotation for analysis/warnings) and the
  actual `notes`/`grid` content isn't enforced, so it's easy to write a `chords`
  label that doesn't match what's actually sounding (e.g. labeling a power chord
  "D" vs "D5"). There's no validation feedback loop telling you they drifted apart.

## 2. Workarounds used

- To get a different, fully-composed lead-guitar part in the final chorus without
  touching the earlier chorus, I defined a second section (`chorus2: extends: chorus`)
  that overrides only `gt2`, rather than trying to express "same section, different
  content on repeat N" directly in `form`. The `performance.edits` per-instance
  mechanism only supports small note-level tweaks, not a full solo rewrite.
  Reusing the same section id for both choruses wasn't possible since the solo and
  rhythm part differ too much.
- For the 4-major-chord sustain at the outro, I checked playability by hand (string/
  fret assignment) and dropped to a 5-note voicing after the 6-note version I first
  wanted was rejected by the chord-fingering validator.
- The short "verse2"/"chorus2" sections are separate pattern-free `notes` blocks
  rather than reusing `riff_a`/`bass_riff` wholesale, since chord changes needed to
  land on specific bars that didn't divide evenly into the 2-bar pattern length.

## 3. Features or changes I wish existed

- A lane-scoped `replace` for drum grids (e.g. only overriding `cr` for one bar)
  instead of requiring the whole bar's grid to be retyped.
- A way to say "repeat this section but override only part X" directly in `form`
  (e.g. `chorus@2: { gt2: ... }`), instead of needing `extends` to create a whole
  new section id for a single-part variation.
- A `beat events --section chorus --diff chorus2` or similar command to quickly
  compare two sections' compiled events, useful when using `extends` to check that
  only the intended part changed.
- Validator feedback (even just a warning) when a `chords` annotation's root/quality
  doesn't match the pitches actually present in `notes`/`grid` for that bar.
