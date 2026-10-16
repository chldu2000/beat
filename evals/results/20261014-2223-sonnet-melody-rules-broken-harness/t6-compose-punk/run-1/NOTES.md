# Notes

Caveat: the Bash tool was denied in this session, so I could not run `beat validate` or `beat events`. `song.beat.yaml` is unvalidated. I checked bar durations by hand (40 bars, 182 BPM).

## 1. What was hard or confusing
- I couldn't run the tools, so I had no check on guitar chord playability or bass downbeat warnings. SPEC.md is the only reference, and it is written in Chinese.
- The rule that a bar's durations must sum exactly to 4 beats needs careful hand counting for the melody.
- It is unclear whether `gt2` can play notes as high as G5 with `!fall` on a tied note.

## 2. Workarounds
- I used two-note power chords (root and fifth) in the verse so they are easy to finger. I did not check them with `beat voicing`.
- I built the drum fills as a shared pattern and used `add` for the crashes.

## 3. Wishes
- A `repeat bars` shorthand for notes, so `(D2:8)*8 | %` doesn't need to be written out.
- A tool that checks bar sums while I'm editing, or auto-fills the last rest.
- Chord-driven bass and rhythm generation from `chords`.
