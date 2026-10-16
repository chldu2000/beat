# Notes

## 1. Hard or confusing
- SPEC.md is written in Chinese, and it is long (33 KB). My first read of it was truncated by tool output limits.
- It is unclear whether `chords:` has to match the `notes`. It seems to be used only for analysis.
- Rules such as "no more than 2 hands at once" and "a note can't cross a bar line" only show up when you validate.
- A `hits` bar needs every lane to have the same number of bars, and the `|` syntax for that is easy to forget.
- A Bash call was denied partway through the session, so I couldn't chain the write, validate and events commands in one call.
- I did not run `beat events`, so the bar-by-bar check of rhythms was skipped. `beat validate` passed: 38 bars, 0 warnings.

## 2. Workarounds
- I used `extends` to make `chorus_last` (the lead-guitar chorus) and `verse2`. This avoids copying the rhythm parts.
- The 8-bar rhythm-guitar verse is one pattern (`verse_gt`), because `replace` can't change a pattern's pitch for only some bars.
- The bass chorus line is a pattern so that both choruses share it.
- Only the last chorus has a `!fall` ending, so the last chorus has a different shape from the first.

## 3. Wishes
- A `chords:`-to-bass auto-fill, such as a root-eighths shortcut like `bass: roots 8`.
- A power-chord shorthand, e.g. `A5` expanding to a playable voicing in the guitar's range.
- A warning when a lead part is written but sits below the rhythm guitar's top note.
- An English version of the spec.
