# Notes

## 1. Hard or confusing
- My first attempt to create the file with a Bash heredoc was denied by the permission mode, so I used the Write tool and only used Bash for `beat validate`.
- SPEC.md is written in Chinese while the task prompt is in English.
- Durations are sticky but articulations are not, so every `!pm` has to be repeated. `(X:8!pm)*8` makes that manageable.
- Chord-to-bar mapping (`Bm G` in one bar) is only used for validation and analysis. Nothing generates notes from it.
- I did not run `beat events`, so I never confirmed the rhythms against the score view. I only know the file validates (40 bars, 0 warnings).

## 2. Workarounds
- Power-chord voicings were typed by hand (e.g. `[D3 A3 D4]`) instead of running `beat voicing`.
- The final chorus bar uses `r:2` and a shortened drum fill to mark the phrase end. This avoids needing a separate "tag" section.
- The last chorus bar of the lead is a held, vibrato note followed by a rest. Silence at the end of each phrase stands in for a sung breath.

## 3. Wishes
- A way to derive power-chord or strum patterns from the `chords:` field, e.g. `strum: eighths-pm`.
- A "repeat count" for whole sections or a `%`-style bar-repeat across patterns.
- A diff view comparing `beat events --by-bar` output before and after an edit.
