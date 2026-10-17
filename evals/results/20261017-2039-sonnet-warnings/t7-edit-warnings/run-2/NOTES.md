# Notes

## What was hard or confusing
- SPEC.md is in Chinese; I needed to read it to confirm that a positive `offset_ms` on a lane means later (laid-back).
- A multi-bar inline drum `hits` needs every lane to have the same number of `|`-separated bars. The error said so, but a lane used in only one bar needed a trailing `|`, which isn't obvious.
- The 3 muddy-voicing warnings (chorus, chorus_to_bridge, final guitar) were already in the song. I left them alone because the task didn't cover them.

## Workarounds
- None needed. I wrote the `break` drums inline, with no pattern, because they are used only once.
- I gave `break` a `B7 | B7` chord line so it leads into the chorus (Gmaj7).

## Wishes
- Let a lane in multi-bar `hits` omit trailing empty bars.
- Offer a "relative offset" edit (e.g. `offset_ms: +5`) so a request like "5 ms more" is explicit.
- Show the effective per-lane offsets in `beat events`.
