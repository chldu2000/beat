# Notes

Changes: added a 2-bar drums-only `break` section (between `solo` and `final` in `form`). Snare lane `offset_ms` went from 5 to 10 in `performance.parts.dr.lanes.sd`, which applies everywhere.

## 1. Hard or confusing
- The spec is in Chinese, and the tool messages are in English.
- Rests in drum `hits` are not `r`. An empty bar after `|` is what works, and that is only documented by example.
- The 2-hands limit counts a crash plus a snare plus a tom on the same beat, so the first draft failed validation.
- The chorus guitar "muddy" warnings were already there and are unrelated to this task. I left them alone, since you asked me to change only the break and the snare offset.

## 2. Workarounds
- Moved the snare off beat 1 of the break bar so the crash and tom fit within two hands.
- Left bar 2 of the crash and tom lanes empty with a trailing `|`.

## 3. Wishes
- A drum `rest` token or a documented empty-bar syntax.
- A way to apply a section-wide drum fill pattern with `use` and still tweak individual lanes.
- A warning that lists every muddy-chord location, not just the first one.
