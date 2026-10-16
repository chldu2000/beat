# Eval report: 20261015-0130-sonnet-melody-rules

model `sonnet`, 3 run(s) per task

| task | final valid | first check clean | checks to green | F1 | dur acc | arts acc | dyn acc | task checks | chars/bar | cost $ | turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t3-compose-hardrock | 3/3 | 3/3 | 1.00 | — | — | — | — | 8/8, 8/8, 8/8 | 116.33 | 0.19 | 7.33 |
| t6-compose-punk | 3/3 | 2/3 | 1.33 | — | — | — | — | 8/8, 8/8, 8/8 | 90.00 | 0.18 | 8.00 |

## Error categories (distinct errors seen during the session, summed over runs)

| task | first check | whole session |
|---|---|---|
| t3-compose-hardrock | — | — |
| t6-compose-punk | bar_duration 2, tie 1 | bar_duration 2, tie 1 |
| **all** | bar_duration 2, tie 1 | bar_duration 2, tie 1 |

## Per run

### t3-compose-hardrock
- **run-1**: valid=True, error trace [0, 0], F1=—, cost=$0.20
- **run-2**: valid=True, error trace [0], F1=—, cost=$0.18
- **run-3**: valid=True, error trace [0], F1=—, cost=$0.19

### t6-compose-punk
- **run-1**: valid=True, error trace [3, 0], F1=—, cost=$0.21
- **run-2**: valid=True, error trace [0], F1=—, cost=$0.17
- **run-3**: valid=True, error trace [0], F1=—, cost=$0.17

## Agent notes

### t3-compose-hardrock / run-1

# Notes

## 1. What was hard or confusing
- SPEC.md is written in Chinese while the task and tool output are in English.
- It is unclear whether `extends` re-applies a drum `replace`/`add` from the parent when the child overrides `dr`. I restated them in the child to be safe.
- Empty drum lanes with `|` separators (e.g. `t1: | | |`) are easy to get wrong, so I avoided them.
- I could not hear the result, so melody and groove choices rest on the spec alone.

## 2. Workarounds
- A `chorus_last` section that `extends` `chorus` adds the lead (gt2), so the final chorus differs without duplicating the rhythm parts.
- The fill into each chorus is a `replace` on the last verse bar, because a fill belongs to the preceding section.
- The intro's drum build-up is written directly as `hits` with `|`-separated bars instead of a pattern.

## 3. Wishes
- Open-string bass chug in `A1` (e.g. `(A1:8)*8`) shown as a one-bar repeat shorthand across sections.
- A `beat events --by-bar` option to show only the drum lanes or only bars with a given articulation.
- A validator hint when a section's final bar has no fill or crash before a section change.
- Per-section mix automation, so the lead could be louder in the last chorus.

### t3-compose-hardrock / run-2

# Notes

## 1. What was hard or confusing
- `:4` means quarter note and `:1` a whole note, so `:2~ :4` takes some care. Numeric durations also carry over to the next note, so I spelled them out to avoid bar-sum errors.
- The 2-hand limit for drums made the chorus pattern awkward. A crash plus hi-hat plus snare on beat 1 is illegal, so I used ride instead of hi-hat.
- SPEC.md is written in Chinese. That is fine, but it is worth knowing.
- I could not hear the result. Only validation and the event view checked the bar math, so the musical feel is unverified.

## 2. Workarounds
- The same `chorus` section is used twice, so the lead plays in both choruses. The DSL has no way to say "only in the last instance" short of a separate section.
- Fills are one-bar patterns swapped in with `replace` on the final bar of a section.
- Power-chord shapes were written by hand (A5 = `[A2 E3 A3]`) rather than looked up.

## 3. Wishes
- A per-instance override in `form`, such as `chorus+solo`, so a section can vary without needing a new section.
- Chord-symbol shorthand in `notes`, such as `A5:4.`, that expands to the guitar voicing.
- Auto-generated bass from `chords`.
- Warnings that say the section-level beat sums are fine, plus a `--by-bar` view for drums that shows hand counts.

### t3-compose-hardrock / run-3

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

### t6-compose-punk / run-1

# Notes

## 1. What was hard or confusing
- SPEC.md is written in Chinese, while the task prompt and tool output are in English.
- A note cannot cross a barline, so a held note plus rest needs careful beat arithmetic. I miscounted twice (5-beat bars); the validator caught both.
- A tie must join identical pitches. I wrote `C#5:2~` at the end of a section by mistake, and the error only said the next note was A4.
- The bass "not a chord tone" warning depends on `chords` granularity, so a bar with a half-bar chord change needs a chord split.
- I couldn't hear the result, so groove and melody choices are untested by ear.

## 2. Workarounds
- Power chords are written as 2- or 3-note `[...]` chords by hand, since `chords:` generates nothing.
- The long chord-by-chord riffs live in `patterns` (`gt_verse`, `bs_verse`, `bs_chorus`) and are reused across both verses.
- A "held note, then breath" is written as a tie, then `r:4`, so the bar still sums to 4.

## 3. Wishes
- Auto-generate rhythm parts from `chords:` (power-chord eighths, root-note bass).
- A `beats remaining` hint in bar-duration errors showing where the bar overflows.
- Say in tie errors which note the tie came from, and mention a missing following section.
- Pattern parameters, e.g. a riff with a chord-root argument.
- A lint for the melody: held note length in seconds, and chord-tone vs tension per strong beat.

### t6-compose-punk / run-2

# Notes

## What was hard or confusing
- SPEC.md is in Chinese, while the task and tool output are in English.
- Guitar chord playability is only checked at validation time. I had to guess which power-chord shapes would pass (they did).
- Bass register: no feedback on which octave sounds right. I kept to E1 and above.
- Melody writing without audio: I could only judge phrasing by counting beats.

## Workarounds
- The lead is written bar by bar, with ties inside a bar (`E4:2~ E4:4!vib`) to get a held, vibrato note followed by a rest.
- Verse and chorus drums use `replace` for the fill bar and `add` for crashes. The outro drums are explicit `hits` with empty bars.
- Intro lead silence is written as `r:1` bars, since a part can't start partway through a section.

## Wishes
- Auto-generate power-chord or bass-root parts from the `chords` line.
- `beat validate` checking melody notes against `chords` (flagging non-chord tones on strong beats).
- A bar-count and form summary command.
- An English version of the spec.

### t6-compose-punk / run-3

# Notes

## What was hard or confusing
- SPEC.md is written in Chinese while the task and tool output are English; that slowed the first read.
- Bar durations have to be exact. There is no helper to show how many beats a bar has left, so I summed lengths by hand.
- It was unclear how `!fall` and `!vib` behave on a final note when no tie follows. I assumed they work on a single note.
- `chords` is only used for checks and warnings. The parts still have to be spelled out by hand, so the chord list and the notes can drift apart.
- I couldn't hear the result, so I had no way to judge whether a rhythm or melody sounds good, only whether it is valid.

## Workarounds
- I wrote repeated power-chord eighths as `([D3 A3]:8!pm)*8`, once per bar, because `!pm` doesn't carry over to later notes.
- Each section repeats its own chord-root bass line, since there is no way to make bass follow `chords`.
- I used the `fill` pattern with `replace` for the last bar of a section, and `add` for the crashes, so the base groove stays in one place.
- The outro drums use `hits` with empty bars, because one bar needs a different feel from the others.

## Wishes
- Generating bass roots and power-chord strums from `chords` (for example `auto: eighths-root`) would remove most of the repetitive text.
- `beat events --by-bar` could also report each bar's total duration, and `validate` could show a clearer "N beats short" hint.
- Per-note ornament shorthand for pickup notes into the next bar.
- A text preview of melody contour, or interval analysis against the chord (`beat analyze`), to check chord-tone use without listening.

