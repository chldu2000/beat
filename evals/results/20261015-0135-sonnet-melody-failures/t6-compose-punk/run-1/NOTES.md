# Notes

## What was hard or confusing
- Remembering that articulations don't carry over, so palm-muted runs need `(X:8!pm)*8` everywhere.
- Ties can't cross bars, and each bar must sum exactly; I used `:b3` for dotted-half lengths to avoid this.
- Only validation was possible (no audio), so melody feel is judged from the note list alone.
- SPEC.md is in Chinese while the task and tool output are in English.

## Workarounds
- Power chords written as two-note `[D3 A3]` shapes by hand (no auto-voicing from `chords`).
- Chord changes repeated bar by bar in `notes` strings; I defined some patterns (pm_*, op_*, b_*) but ended up writing the bars inline, so they are unused.
- Intro drums use `replace` on bars 1-2 for a half-time hi-hat feel.

## Wishes
- Generate rhythm-guitar and bass parts from `chords` plus a named style (e.g. `punk_eighths`).
- A warning for unused patterns.
- Per-section mix automation and a way to apply `!pm` to a whole bar or pattern.
