# Notes

Bash was denied in this session, so I could not run `beat validate` or `beat events`. `song.beat.yaml` has not been validated. I wrote it by hand from SPEC.md (read before the denial) and the demo file.

## 1. What was hard or confusing
- I never ran the tools, so I could not confirm that the bar durations, drum overlap rules ("at most 2 hands") or `extends` behaviour are correct.
- The "at most 2 hands" rule for drums, and how `add` interacts with it, is easy to get wrong without a validator. I put the crash only on bars where hh plays alone.
- `extends` can't be nested, and it isn't obvious whether `bars:` may be overridden in an extending section. I used `bars: 4` in `verse2`.
- The spec is in Chinese while the task prompt is in English.

## 2. Workarounds
- Used one-bar patterns plus per-bar `replace` to put the riff on different chords.
- Made the solo chorus with `extends: chorus` and an added `gt2` part, so the first chorus has no lead.

## 3. Wishes
- A pattern-with-parameters feature, such as a transpose argument for a riff by chord root.
- A way to see validation results without a shell, or a lint that is also available as a library.
- Short chord-to-power-chord helpers, for example `riff: A5` expanding to a palm-muted eighth-note pattern.
