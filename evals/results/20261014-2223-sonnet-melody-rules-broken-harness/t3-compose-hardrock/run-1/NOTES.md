# Notes on writing song.beat.yaml

## 1. What was hard or confusing
- SPEC.md is in Chinese while the task and tool output are in English. This is harmless but surprising.
- The two-hands limit for drums is easy to break. A crash on beat 1 together with a continuous `hh` line fails, and the rule is only mentioned in the `add` section. I put the crash in a `replace` bar for the chorus.
- Notes cannot cross bar lines, so every held note needs `~` ties. The first-note-only rule for articulations adds to the bookkeeping.
- My first attempt to write the file with a shell heredoc was denied by the sandbox. Writing it with the file tool worked.

## 2. Workarounds
- The chorus has a crash on beat 1 and hh on the remaining eighths. I wrote it with `replace` on bar 1 instead of adding a crash to the pattern.
- The last chorus is a `chorus_last` section that `extends` chorus and only adds gt2. This avoids copying the whole chorus.
- The fill and the final-bar hits are written as one-bar patterns or `replace` bars.
- The long vibrato notes use ties (`A5:2~ A5:2!vib`).

## 3. Wishes
- A way to put a crash on beat 1 of a pattern that also carries `hh` (for example, an automatic hh choke or drop) without needing `replace`.
- An `add` that can optionally override an existing hit.
- Allow a note to run past a bar line, with the tool splitting it automatically.
- `beat validate` could report the pre-chorus fills it finds, and show a chord-vs-notes check (non-chord tones).
- An English version of SPEC.md.
