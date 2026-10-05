---
name: compose
description: Compose, arrange or edit a song for the rock band in Beat DSL (.beat.yaml files), then validate it and check the compiled result. Use when asked to write, extend, rearrange or fix a song.
---

# Composing in Beat DSL

You write songs as `.beat.yaml` files in the Beat DSL. `SPEC.md` (in this repo: `docs/SPEC.md`) is the
authoritative format reference — read it before writing. `examples/demo.beat.yaml` is a complete example.

## Tools

- `beat validate SONG [--json]` — errors and warnings with locations. Exit code 1 if there are errors.
- `beat events SONG --by-bar [--bars 5-8] [--parts a,b]` — compact score view, one line per part per
  bar: `beat:note/length` (lengths in beats; chords and simultaneous drum hits joined with `+`).
  Use it to confirm the file says what you meant.
- `beat events SONG [--bars 5-8] [--parts a,b] [--sections x,y]` — one line per note with bar, beat,
  length, velocity and performed time. Add `--json` for the full event data.
- `beat voicing CHORD [full|power] [--for guitar|organ|piano]` — playable voicings of a chord symbol
  (guitar: fret shape and notes, easiest first). Paste the notes into `notes` instead of working out
  chord shapes yourself.

## Workflow

1. **Plan** before writing notes: key, tempo, time signature, form (section order and lengths), chord
   progression per section, and the role of each part.
2. **Skeleton**: write `meta`, `instruments`, `sections` with `bars` and `chords`, and `form`. Validate.
3. **Parts**, one at a time: drums → bass → rhythm guitar → keys / lead. Validate after each part.
4. **Fix every error.** Read warnings too and fix the ones that are real mistakes.
5. **Check intent** with `beat events --by-bar --bars …` on bars you are unsure about (rhythms, ties,
   repeats, drum grids).
6. **Organ**: choose its sound once with `model: { registration: ... }` (SPEC section 3), shape it per
   section with `dynamic` (it has no touch sensitivity; `!acc` does nothing) and `leslie: fast` where
   the section should lift (usually choruses and solos).
7. **Mix** (`mix:`, SPEC section 10) last, and only where the defaults don't fit: every part already
   gets EQ, compression and the shared room. Usually set `pan` (spread two rhythm guitars left and
   right, keep bass and drums centered), `gain_db` for balance, `space` for the
   song's feel (`room` tight, `hall` for ballads) and `reverb: more` on a lead. `beat render` prints a
   mix report; fix its warnings (the limiter working too hard means a part or the loudness is too high).
8. Keep repeated material in `patterns` and vary it with `replace` (whole bars, optionally
   transposed) and, for drums, `add` (extra hits such as a crash), so later edits stay local.

When editing an existing song, change only what was asked and keep everything else identical.
