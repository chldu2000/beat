# Eval report: 20261015-0135-sonnet-melody-failures

model `sonnet`, 3 run(s) per task

| task | final valid | first check clean | checks to green | F1 | dur acc | arts acc | dyn acc | task checks | chars/bar | cost $ | turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t3-compose-hardrock | 3/3 | 1/3 | 2.00 | — | — | — | — | 8/8, 8/8, 8/8 | 111.00 | 0.20 | 9.00 |
| t6-compose-punk | 3/3 | 3/3 | 1.00 | — | — | — | — | 8/8, 8/8, 8/8 | 93.00 | 0.17 | 6.00 |

## Error categories (distinct errors seen during the session, summed over runs)

| task | first check | whole session |
|---|---|---|
| t3-compose-hardrock | bar_duration 4, tie 2 | bar_duration 4, tie 2 |
| t6-compose-punk | — | — |
| **all** | bar_duration 4, tie 2 | bar_duration 4, tie 2 |

## Per run

### t3-compose-hardrock
- **run-1**: valid=True, error trace [0], F1=—, cost=$0.19
- **run-2**: valid=True, error trace [1, 1, 0, 0, 0], F1=—, cost=$0.23
- **run-3**: valid=True, error trace [5, 0], F1=—, cost=$0.18

### t6-compose-punk
- **run-1**: valid=True, error trace [0], F1=—, cost=$0.19
- **run-2**: valid=True, error trace [0], F1=—, cost=$0.16
- **run-3**: valid=True, error trace [0], F1=—, cost=$0.16

## Agent notes

### t3-compose-hardrock / run-1

# Notes

## 1. What was hard or confusing
- SPEC.md is in Chinese while the task and tool output are in English. It was readable, but it is a small barrier.
- Whether `extends` can be used for a "last chorus" variant wasn't stated outright. It was inferable: one level, parts merge per part.
- I couldn't hear anything, so I couldn't check the lead's phrasing, the mix balance, or whether the guitar voicings sound good. I could only check the notation.
- The rule "at most 2 hands" for drum overlaps is easy to break when mixing crash, hat and snare. I only knew it from the spec.

## 2. Workarounds
- The last chorus needs lead guitar but the first doesn't. I made a separate section, `chorus_last`, that extends `chorus` and adds `gt2`. The form list can't switch a part on per instance.
- `verse2` extends `verse` and adds short lead fills. Each fill needed a full 8-bar `gt2` string padded with `r:1` rests.
- Repeated riff bars are written out in full instead of using `%`, to stay safe with `!pm` (articulations don't carry over).

## 3. Wishes
- Per-instance part overrides in `form`, for example `- chorus: { gt2: ... }`, so no extra section is needed.
- Rest-padding shorthand, e.g. `r:8bars` or a `rest` pattern, so a part can stay silent for N bars.
- A `beat check`/lint that reports the voice-leading or role of each part, and a text-based melody-range summary.
- Auto-generated power-chord shorthand in `notes`, such as `A5` meaning the standard voicing.

### t3-compose-hardrock / run-2

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

### t3-compose-hardrock / run-3

# Notes

## 1. What was hard or confusing
- SPEC.md is written in Chinese while the task and tool output are in English.
- Counting eighth notes by hand in the riff (I wrote 9 in one bar). The error message was clear, though.
- A tie needs a following note in the same part, so a section can't end on a tied note unless the next section continues it. This isn't obvious for the last section.
- Hand limits for drums (crash + hat + snare) aren't visible until validation, so I used the ride for the chorus.

## 2. Workarounds
- Chorus 2 is a separate section (`chorus_last`, via `extends`) so gt2 plays only there.
- Drum fills are `replace`d into the last bar of a section instead of being separate sections.
- The outro ends on untied whole notes, because ties can't dangle.

## 3. Wishes
- A `beat events --by-bar` style check inside `validate` for the sum of beats per bar, with the offending token.
- A shorthand for "power chord" that expands per chord symbol, e.g. `@chord` taken from `chords:`.
- A warning when gt2 is silent in a whole section, or a lead is below the rhythm guitar's register.
- An English edition of the spec.

### t6-compose-punk / run-1

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

### t6-compose-punk / run-2

# Notes

## 1. What was hard or confusing
- The spec is in Chinese while the task and tool docs are in English.
- Drum `hits` multi-bar syntax (`|` with empty bars, every lane padded to the same bar count) is easy to get wrong. Nothing in the spec says whether a trailing `|` is required.
- The hand limit (2 per moment) interacts with `add`, so a crash on top of hh+sd needs care.
- `chords` is only used for analysis, so nothing checks that it matches the notes.
- Duration carry-over (the last length persists) makes melody lines hard to check by eye.

## 2. Workarounds
- Patterns (`gt_verse`, `bs_chorus`, and so on) hold the repeated 8-bar parts. Fills and crashes come from `replace` and `add`.
- I used power-chord dyads and triads that I judged playable by hand. I did not call `beat voicing`. Validation passed.
- The outro has a one-bar final hit, written with the drum `hits` per-bar syntax.

## 3. Wishes
- Generate rhythm or bass parts from `chords`, for example a `strum: eighths` shorthand.
- Let `validate` report whether a melody note is in the chord or scale.
- Let drum patterns carry named fill variants with a shorthand like `fill_every: 4`.
- A way to listen to a melody, or a pitch-contour view in `events`.

### t6-compose-punk / run-3

# Notes

## What was hard or confusing
- SPEC.md is in Chinese while the task and tooling are in English, so I had to translate as I read.
- It wasn't obvious whether `add` (a crash on beat 1) would clash with `hh` on the same beat. The "two hands" rule is only spelled out in prose.
- A tied note can't cross a bar line, so a 3-beat note plus a rest needed `:b3`.
- I couldn't hear the result, so melody quality is judged only from the note listing.

## Workarounds
- Used `D5:b3!vib r:4` for the held final chorus note instead of a tie.
- Used the 8-bar `fill` pattern with `replace` for section-end drum fills.
- Wrote power chords by hand instead of calling `beat voicing`.

## Wishes
- A way to repeat a chord or pattern across bars without writing `%` or repeating text (e.g. `(...)*8 | %` works but is wordy).
- Per-section mix or dynamics automation.
- Validation of melody notes against the section's `chords` (a warning for non-chord tones on strong beats in pitched lead parts).
- An English version of the spec.

