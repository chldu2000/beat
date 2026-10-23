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
   repeats, drum grids). Read the lead with `--parts LEAD` and revise it if it mostly arpeggiates the
   chord of each bar, repeats one bar's rhythm or one ornament without anything else changing, or sits
   under the rhythm guitars while they play full chords — unless the song means it to.
6. **Dynamics**: give sections a level with `dynamic`, and let builds grow instead of jumping:
   `dynamic: { from: mp, to: f }` ramps a whole section or part (a pre-chorus into the chorus, drums
   included); `@<` / `@>` in `notes` swell or fade toward the next dynamic. A section's `tempo` can
   change too (`{ from: 120, to: 100 }` for a closing ritardando). The beat-by-beat lean (downbeats
   firmer, off-beats lighter) and a slight push in loud sections are automatic.
7. **Organ**: choose its sound once with `model: { registration: ... }` (SPEC section 3), shape it per
   section with `dynamic` (it has no touch sensitivity; `!acc` does nothing, but ramps and hairpins
   swell even a held chord) and `leslie: fast` where the section should lift (usually choruses and
   solos); `@fast` / `@slow` in its `notes` switch the Leslie mid-section.
8. **Guitar sound**: an instrument's `tone` (`clean` / `crunch` / `lead`) and `pedals` (`fuzz`, `od`,
   `boost`; their knobs go in `model:`, SPEC section 3) are its defaults. A section's part can set its
   own (`tone: clean` for a quiet verse), and `@lead`, `@+boost` / `@-boost` in its `notes` switch
   mid-section, e.g. a boost for the solo or a fuzz on the last chord of a phrase.
9. **Mix** (`mix:`, SPEC section 10) last, and only where the defaults don't fit: every part already
   gets EQ, compression and the shared room. Usually set `pan` (spread two rhythm guitars left and
   right, keep bass and drums centered), `gain_db` for balance, `space` for the
   song's feel (`room` tight, `hall` for ballads) and `reverb: more` on a lead. `beat render` prints a
   mix report; fix its warnings (the limiter working too hard means a part or the loudness is too high).
10. Keep repeated material in `patterns` and vary it with `replace` (whole bars, optionally
   transposed) and, for drums, `add` (extra hits such as a crash), so later edits stay local.

## Writing the melody

You cannot hear the result, so write the lead with these in mind. The style of the song comes first;
each point says why, so you can tell when it does not apply.

- **Think in seconds.** One beat lasts 60/tempo seconds, and the ear hears a note as held from about a
  second (3 beats at 180 BPM, 2 at 120); at 184 BPM a dotted quarter (0.49 s) is a passing note.
- **Shape phrases like a singer would.** A phrase moves toward a goal, lands, and breathes before the
  next one; the gaps are where other parts answer.
- **Give held notes a life.** On this guitar a held note with a steady pitch sounds synthetic. Add
  `!vib` (on a tied note, `A5:2~ A5:2!vib` starts it later), bend into it from below (`G5:4!bend=2`
  sounds A5), or end it with `!fall`.
- **Let the melody have its own line.** Choose notes for where the melody is going, not only from the
  chord of the moment; use ornaments where a note needs emphasis.
- **Make the lead heard.** It cuts through above the rhythm guitars' top notes, or in their register
  when they thin out or drop away. Give the chorus a lift over the verse: register, rhythm density,
  arrangement or dynamics.

When editing an existing song, change only what was asked and keep everything else identical.
