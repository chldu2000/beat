# Notes

## 1. What was hard or confusing
- SPEC.md is in Chinese while the task and tool output are in English. This slowed down reading.
- A tie at the end of a `notes` string with no following note is an error. I hit this once and had to find it by hand.
- Chords and chord shapes: I wasn't sure which power-chord voicings the guitar would accept. I only found out by validating.
- Every section repeats its part material, so the `notes` strings are long. `%` only repeats a whole bar.
- I could only check the result with `validate`. Nothing tells me how the lead and rhythm parts balance.

## 2. Workarounds
- The chorus appears twice under the same section name, so the lead (gt2) plays in both. There is no per-instance override without `extends`, so the last chorus has the same lead as the first.
- Ending a phrase on a held note and a rest was done with `:b1` lengths and a tied note, since a plain length can't carry a vibrato that starts late.
- Fills are a reusable `fill` pattern swapped into the last bar before a chorus or the final chorus.

## 3. Wishes
- A `beat validate --fix` hint, or a suggestion for the likely cause when a bar's duration is wrong.
- Per-instance section overrides (e.g. `chorus#2`) without declaring a second section.
- Auto-generated rhythm guitar from the `chords` field.
- A way to preview or inspect the mix without rendering audio.
