# Notes

## What was hard or confusing
- SPEC.md is in Chinese while the task and tool output are in English, so I had to translate as I read.
- `extends` merges parts, but a part that uses `replace` still needs its own base content. It wasn't clear whether I could inherit a part and only replace bars. I wrote a separate full `chorus_end` section to be safe.
- Drum `hits` with several bars: every lane must have all the bar slots, and an empty bar is written as an empty slot between `|`. This is easy to get wrong.
- The spec doesn't say whether a note's duration carries across `|` bars inside repeat groups. I wrote `:8` explicitly every time.
- I can't hear the result, so I couldn't check the lead's audibility against the rhythm guitar. I judged it by register only.

## Workarounds
- Section variants (final chorus ending on D, bridge) are separate sections, because I couldn't override single bars of an inherited part cheaply.
- One-bar chord patterns (`dpm`, `gpm`, ...) are defined but I wrote the section notes out in full, since a `use` can't take a different chord per bar without a `replace` per bar.
- A long note over a bar line is a tie (`C#5:2~ C#5:4!vib`), with the vibrato on the tied tail.

## Wishes
- Chord-driven generation: a `strum`/`power` pattern that follows the section's `chords` line.
- A `pattern` that takes a root or chord parameter, so one riff can cover D/G/A/Bm.
- `beat events --by-bar` option to show chord names and section boundaries alongside the notes.
- Per-bar `replace` for inherited parts in `extends`, without restating the base.
- A melody check in `validate` for the range and leaps of a lead part.
