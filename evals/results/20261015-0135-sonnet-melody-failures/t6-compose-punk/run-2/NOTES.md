# Notes

## 1. What was hard or confusing
- The spec is in Chinese while the task and tool docs are in English.
- Drum `hits` multi-bar syntax (`|` with empty bars, every lane padded to the same bar count) is easy to get wrong. Nothing in the spec says whether a trailing `|` is required.
- The hand limit (2 per moment) interacts with `add`, so a crash on top of hh+sd needs care.
- `chords` is only used for analysis, so nothing checks that it matches the notes.
- Duration carry-over (the last length persists) makes melody lines hard to check by eye.

## 2. Workarounds
- Patterns (`gt_verse`, `bs_chorus`, and so on) hold the repeated 8-bar parts. Fills and crashes come from `replace` and `add`.
- I used power-chord dyads and triads that I judged playable by hand. I did not call `beat voicing`. Validation passed.
- The outro has a one-bar final hit, written with the drum `hits` per-bar syntax.

## 3. Wishes
- Generate rhythm or bass parts from `chords`, for example a `strum: eighths` shorthand.
- Let `validate` report whether a melody note is in the chord or scale.
- Let drum patterns carry named fill variants with a shorthand like `fill_every: 4`.
- A way to listen to a melody, or a pitch-contour view in `events`.
