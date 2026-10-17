# Notes

## What was hard or confusing
- Multi-bar `hits` need every lane to have the same number of `|` bars. A lane with only one bar (`cr: 1!acc`) fails, and the error message is the only hint.
- The sign of `offset_ms` (positive = later) is only implied by the "laid-back" comment in SPEC section 9.
- The pre-existing muddy-voicing warnings in chorus, chorus_to_bridge and final are unrelated to this task. I left them alone because the task said to change only what was asked.

## Workarounds
- I wrote the crash lane as `cr: 1!acc |` so it has two bars, with an empty second bar.

## Wishes
- Let a lane in multi-bar `hits` be shorter than the rest, with the missing bars treated as empty.
- Let `beat validate` or `beat events` show the effective per-lane offset, so a performance change can be confirmed without rendering.
