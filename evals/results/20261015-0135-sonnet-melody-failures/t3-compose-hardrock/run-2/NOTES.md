# NOTES

Song: `song.beat.yaml`, "Thunder Road Rattle". A major, 126 BPM, 34 bars. Form: intro (4), verse (8), chorus (8), bridge (4), chorus2 (8, with the gt2 lead), outro (2). Fills lead into the chorus (verse bar 8) and into chorus2 (bridge bar 4). `beat validate` passes with 0 warnings. I did not render audio.

## 1. What was hard or confusing
- SPEC.md is in Chinese while the task and tool output are in English. It was readable but slower to scan.
- Counting eighths inside bars with `(x)*n` and a sticky duration is error-prone. I wrote bar 8 of the verse gt1 short by half a beat, and the error did not show how the sticky duration had carried over.
- `--bars` accepts only a single range (`5-8`). `12-13,27-34` is rejected.
- Chorus2 reuses the chorus drums, but the chorus's `add` and `replace` rules (crash on bars 1 and 5, a different last bar) are inherited implicitly through `extends`. That is easy to lose track of.
- The validator checks hand count and guitar playability, but not whether a lead line sits well on the chord. I had to check it by eye.

## 2. Workarounds
- Power-chord riffs are written as repeated per-bar strings, or as one-bar patterns (`riff_a`, `riff_d`, `riff_e`) plus `replace`. The verse gt1 is written out in full because a pattern per chord does not fit a section that changes chord per bar.
- The chorus drum pattern is a single bar that loops. Crashes go on with `add`, and the last bar is replaced with a final crash and kick. This avoids three-hand collisions with `hh` and `sd`.
- The solo is a separate `chorus2` section that `extends` the chorus, so `gt2` is added without repeating the other parts.
- For `!fall` on a held end note I used `E5:2~ E5:2!fall`.

## 3. Wishes
- `--bars` should accept comma-separated ranges.
- Validation errors for a short bar should also name the offending token or show the running beat total.
- A way to apply a pattern per chord from `chords`, for example a riff template transposed by the chord root. That would replace the repeated per-chord riff strings.
- `beat events --by-bar` could have a mode that shows only one part against the chord names, to check lead notes against chords.
- A "section instance count" or `form` repeat shorthand, e.g. `chorus x2`.
