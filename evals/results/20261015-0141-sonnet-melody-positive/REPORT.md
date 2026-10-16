# Eval report: 20261015-0141-sonnet-melody-positive

model `sonnet`, 3 run(s) per task

| task | final valid | first check clean | checks to green | F1 | dur acc | arts acc | dyn acc | task checks | chars/bar | cost $ | turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t3-compose-hardrock | 3/3 | 2/3 | 1.33 | — | — | — | — | 8/8, 8/8, 8/8 | 108.33 | 0.20 | 8.67 |
| t6-compose-punk | 3/3 | 3/3 | 1.00 | — | — | — | — | 8/8, 8/8, 8/8 | 97.67 | 0.17 | 6.00 |

## Error categories (distinct errors seen during the session, summed over runs)

| task | first check | whole session |
|---|---|---|
| t3-compose-hardrock | bar_duration 2 | bar_duration 2 |
| t6-compose-punk | — | — |
| **all** | bar_duration 2 | bar_duration 2 |

## Per run

### t3-compose-hardrock
- **run-1**: valid=True, error trace [0], F1=—, cost=$0.22
- **run-2**: valid=True, error trace [2, 0], F1=—, cost=$0.17
- **run-3**: valid=True, error trace [0], F1=—, cost=$0.20

### t6-compose-punk
- **run-1**: valid=True, error trace [0], F1=—, cost=$0.19
- **run-2**: valid=True, error trace [0], F1=—, cost=$0.16
- **run-3**: valid=True, error trace [0], F1=—, cost=$0.16

## Agent notes

### t3-compose-hardrock / run-1

# Notes

## 1. What was hard or confusing
- SPEC.md is written in Chinese while the task and tool output are in English.
- Notes are strict about bar length. Mixing `:4.`, `:8` and `:2` in one bar needs careful hand arithmetic.
- It is unclear whether `%` in `replace` strings repeats the previous bar inside that string. I used it and it validated.
- Duration and velocity carry over between notes, but articulations don't. That makes palm-muted runs verbose.

## 2. Workarounds
- Merged the lead into the single `chorus` section so the same section name returns. It means the first chorus also has the lead melody.
- Wrote the chorus chords out as explicit notes, because `chords:` is only for validation and analysis.
- Used `!bend=1` and `!fall` for the solo phrasing, since there is no pre-bend or release-only bend.

## 3. Wishes
- Per-instance section overrides in `form`, such as `chorus+gt2`, so the lead only plays in the last chorus without a new section.
- Generating chord-strum or power-chord patterns from `chords:`.
- A way to name a rhythm and apply it to a chord list, like `strum_a` over `A D E A`.
- `beat events --by-bar` output that flags bars where a lead part is silent.

### t3-compose-hardrock / run-2

# Notes

## What was hard or confusing
- SPEC.md is mostly in Chinese, while the tool messages are in English.
- It wasn't obvious that `extends` only allows one level and that `parts` merge per part. I got this from the spec, not from an error.
- Bar durations need careful counting by hand. I got one 4.5-beat bar wrong in a chorus (the validator caught it).
- The spec doesn't say whether a section used only through `extends` (chorus2) still counts as "the chorus" for a repeat. I made it a variant of chorus.

## Workarounds
- The lead only plays in the last chorus, so I made a `chorus2` section that extends `chorus` and overrides only `gt2`.
- I typed power-chord voicings by hand instead of calling `beat voicing`. They validated fine.
- I wrote the fills as a reusable drum pattern and used it with `replace` on the last bar of sections.

## Wishes
- A `repeat`/`x2` shorthand for a whole section's part, or a per-instance override in `form`, so a variant section isn't needed.
- A bar-duration hint in the validator, such as a running total per bar.
- Automatic chord-to-power-chord helpers driven by the `chords` field.

### t3-compose-hardrock / run-3

# Notes

## 1. What was hard or confusing
- SPEC.md is in Chinese while the task and tool output are in English; I had to read it carefully for details.
- It is unclear whether `extends` creates a "different section" for the "chorus must return" requirement, so I reused the same `chorus` section twice and put the lead in it both times.
- Bar totals with `%` and `*n` repeats are easy to miscount without validating.
- Guitar chord playability is only discovered at validation time.

## 2. Workarounds
- The lead can't differ between two instances of one section without a new section, so gt2 plays the melodic line in every chorus instance.
- Power chords were written by hand (standard shapes) instead of calling `beat voicing`.
- Tempo, key and chords are fixed per file, so the "A major" feel comes from the chord symbols and note choice only.

## 3. Wishes
- Per-instance overrides in `form` (e.g. `chorus: {gt2: ...}`) without defining a new section.
- Chord-symbol-driven bass/rhythm generation.
- A `beat events` warning when the lead only arpeggiates chord tones.
- English version of the spec.

### t6-compose-punk / run-1

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

### t6-compose-punk / run-2

# Notes

## 1. What was hard or confusing
- SPEC.md is written in Chinese; the task and the tool docs are in English.
- Guitar chords must be fingerable, and the validator only says so after the fact. I used `beat voicing`-style power-chord shapes from memory, and they validated.
- Drum hand limits (2 hands per moment) interact with `add`, so crash-plus-hat or crash-plus-snare needs care. The `add` I used on beat 1 only collided with hits I had not written there.
- No audio render allowed, so the melody is judged only on paper.

## 2. Workarounds
- Eighth-note guitar chords are written as `(...)*8` repeats, since articulations do not carry over.
- The last chorus has no distinct ending, so the outro repeats the chorus melody on the tonic.
- The whole-note guitar ending uses a plain chord because I chose not to risk tie rules.

## 3. Wishes
- A `chords`-driven shorthand for power chords (e.g. `D5:8!pm*8`).
- Per-section tempo or mix automation, for example a lift in the final chorus.
- A `beat events` option that prints the melody as scale degrees or checks it against the declared chords.

### t6-compose-punk / run-3

# Notes

## What was hard or confusing
- SPEC.md is in Chinese, while the task and tool output are in English.
- It's unclear whether `hits` with several bars needs `|` after empty bars (I wrote `| |` in the outro and it validated).
- A bar's duration inherits from the previous note, so melody lines need care to sum to 4 beats. Validation catches mistakes, but only after the fact.
- I couldn't hear the result, so melodic choices rest on theory alone.

## Workarounds
- Rhythm guitar bars are written out in full (`([D3 A3]:8!pm)*8`), because patterns can't take a chord argument.
- The chorus ride (`rd`) plus an added `cr` stand in for open hats and a crash, which avoids the hand-count conflict with the snare.

## Wishes
- Generate rhythm guitar and bass from `chords` with a style (power-chord 8ths, root 8ths).
- Parameterised patterns, e.g. a root-note argument.
- A `beat check-melody` command that reports chord-tone and scale-tone stats against `chords`.

