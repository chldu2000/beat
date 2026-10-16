# Notes

## 1. What was hard or confusing
- SPEC.md is in Chinese while the task and tool output are in English. It was readable, but it is a small barrier.
- Whether `extends` can be used for a "last chorus" variant wasn't stated outright. It was inferable: one level, parts merge per part.
- I couldn't hear anything, so I couldn't check the lead's phrasing, the mix balance, or whether the guitar voicings sound good. I could only check the notation.
- The rule "at most 2 hands" for drum overlaps is easy to break when mixing crash, hat and snare. I only knew it from the spec.

## 2. Workarounds
- The last chorus needs lead guitar but the first doesn't. I made a separate section, `chorus_last`, that extends `chorus` and adds `gt2`. The form list can't switch a part on per instance.
- `verse2` extends `verse` and adds short lead fills. Each fill needed a full 8-bar `gt2` string padded with `r:1` rests.
- Repeated riff bars are written out in full instead of using `%`, to stay safe with `!pm` (articulations don't carry over).

## 3. Wishes
- Per-instance part overrides in `form`, for example `- chorus: { gt2: ... }`, so no extra section is needed.
- Rest-padding shorthand, e.g. `r:8bars` or a `rest` pattern, so a part can stay silent for N bars.
- A `beat check`/lint that reports the voice-leading or role of each part, and a text-based melody-range summary.
- Auto-generated power-chord shorthand in `notes`, such as `A5` meaning the standard voicing.
