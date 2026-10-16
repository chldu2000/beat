# Eval report: 20261014-2223-sonnet-melody-rules

model `sonnet`, 3 run(s) per task

| task | final valid | first check clean | checks to green | F1 | dur acc | arts acc | dyn acc | task checks | chars/bar | cost $ | turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t3-compose-hardrock | 2/3 | 2/2 | 1.00 | — | — | — | — | 8/8, 8/8 | 114.33 | 0.18 | 6.67 |
| t6-compose-punk | 3/3 | 1/1 | 1.00 | — | — | — | — | 8/8, 8/8, 8/8 | 84.33 | 0.20 | 7.00 |

## Error categories (distinct errors seen during the session, summed over runs)

| task | first check | whole session |
|---|---|---|
| t3-compose-hardrock | — | — |
| t6-compose-punk | — | — |
| **all** | — | — |

## Per run

### t3-compose-hardrock
- **run-1**: valid=True, error trace [0], F1=—, cost=$0.18, denied: ["Bash: cat > song.beat.yaml <<'EOF'\nbeat: 0.1\n\nmeta:\n  title: Highway Fuse\n  tempo: 128\n  time: 4/4\n  key: A major\n  style: hard rock\n\ninstruments:\n  dr:  { type: drums }\n  bs:  { type: bass }\n  gt1: {"]
- **run-2**: valid=True, error trace [0], F1=—, cost=$0.17, denied: ["Bash: cat > song.beat.yaml <<'EOF'\nbeat: 0.1\n\nmeta:\n  title: Highway Thunder\n  tempo: 126\n  time: 4/4\n  key: A major\n  style: hard rock\n\ninstruments:\n  dr:  { type: drums }\n  bs:  { type: bass }\n  gt1"]
- **run-3**: valid=False, error trace [], F1=—, cost=$0.19, final errors: ["[error] intro > dr > replace 1-2 > bar 2: lane 'hh': cannot parse hit 'hh:' (use a beat like 2, 2.5, 1+1/3, optionally with !acc, !ghost or !flam)", "[error] outro > dr > bar 2: lane 'cr': cannot parse hit 'cr:' (use a beat like 2, 2.5, 1+1/3, optionally with !acc, !ghost or !flam)", "[error] outro > dr > bar 2: lane 'bd': cannot parse hit 'bd:' (use a beat like 2, 2.5, 1+1/3, optionally with !acc, !ghost or !flam)"], denied: ["Bash: cat > song.beat.yaml <<'EOF'\nbeat: 0.1\n\nmeta:\n  title: Highway Thunder\n  tempo: 128\n  time: 4/4\n  key: A major\n  style: hard rock\n\ninstruments:\n  dr:  { type: drums }\n  bs:  { type: bass }\n  gt1"]

### t6-compose-punk
- **run-1**: valid=True, error trace [], F1=—, cost=$0.18, denied: ["Bash: cat > song.beat.yaml <<'EOF'\nbeat: 0.1\n\nmeta:\n  title: Parking Lot Summer\n  tempo: 182\n  time: 4/4\n  key: D major\n  style: melodic punk\n\ninstruments:\n  dr:  { type: drums }\n  bs:  { type: bass }"]
- **run-2**: valid=True, error trace [0], F1=—, cost=$0.22, denied: ["Bash: cat > song.beat.yaml <<'EOF'\nbeat: 0.1\n\nmeta:\n  title: Last Bus Home\n  tempo: 180\n  time: 4/4\n  key: D major\n  style: melodic punk\n\ninstruments:\n  dr:  { type: drums }\n  bs:  { type: bass }\n  gt"]
- **run-3**: valid=True, error trace [], F1=—, cost=$0.21, denied: ['Bash: for c in D G A B; do beat voicing ${c}5 power --max 2; done; beat voicing Bm power --max 2', "Bash: cat > song.beat.yaml <<'EOF'\nbeat: 0.1\n\nmeta:\n  title: Nowhere Fast\n  tempo: 182\n  time: 4/4\n  key: D major\n  style: melodic punk\n\ninstruments:\n  dr:  { type: drums }\n  bs:  { type: bass }\n  gt1"]

## Agent notes

### t3-compose-hardrock / run-1

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

### t3-compose-hardrock / run-2

# Notes

## 1. Hard or confusing
- SPEC.md is written in Chinese, and it is long (33 KB). My first read of it was truncated by tool output limits.
- It is unclear whether `chords:` has to match the `notes`. It seems to be used only for analysis.
- Rules such as "no more than 2 hands at once" and "a note can't cross a bar line" only show up when you validate.
- A `hits` bar needs every lane to have the same number of bars, and the `|` syntax for that is easy to forget.
- A Bash call was denied partway through the session, so I couldn't chain the write, validate and events commands in one call.
- I did not run `beat events`, so the bar-by-bar check of rhythms was skipped. `beat validate` passed: 38 bars, 0 warnings.

## 2. Workarounds
- I used `extends` to make `chorus_last` (the lead-guitar chorus) and `verse2`. This avoids copying the rhythm parts.
- The 8-bar rhythm-guitar verse is one pattern (`verse_gt`), because `replace` can't change a pattern's pitch for only some bars.
- The bass chorus line is a pattern so that both choruses share it.
- Only the last chorus has a `!fall` ending, so the last chorus has a different shape from the first.

## 3. Wishes
- A `chords:`-to-bass auto-fill, such as a root-eighths shortcut like `bass: roots 8`.
- A power-chord shorthand, e.g. `A5` expanding to a playable voicing in the guitar's range.
- A warning when a lead part is written but sits below the rhythm guitar's top note.
- An English version of the spec.

### t3-compose-hardrock / run-3

# Notes

Bash was denied in this session, so I could not run `beat validate` or `beat events`. `song.beat.yaml` has not been validated. I wrote it by hand from SPEC.md (read before the denial) and the demo file.

## 1. What was hard or confusing
- I never ran the tools, so I could not confirm that the bar durations, drum overlap rules ("at most 2 hands") or `extends` behaviour are correct.
- The "at most 2 hands" rule for drums, and how `add` interacts with it, is easy to get wrong without a validator. I put the crash only on bars where hh plays alone.
- `extends` can't be nested, and it isn't obvious whether `bars:` may be overridden in an extending section. I used `bars: 4` in `verse2`.
- The spec is in Chinese while the task prompt is in English.

## 2. Workarounds
- Used one-bar patterns plus per-bar `replace` to put the riff on different chords.
- Made the solo chorus with `extends: chorus` and an added `gt2` part, so the first chorus has no lead.

## 3. Wishes
- A pattern-with-parameters feature, such as a transpose argument for a riff by chord root.
- A way to see validation results without a shell, or a lint that is also available as a library.
- Short chord-to-power-chord helpers, for example `riff: A5` expanding to a palm-muted eighth-note pattern.

### t6-compose-punk / run-1

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

### t6-compose-punk / run-2

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

### t6-compose-punk / run-3

# Notes

Caveat: the Bash tool was denied in this session (don't-ask mode), so I could not run `beat validate` or `beat events`. The song was written from SPEC.md and the demo only, and has not been validated.

## 1. What was hard or confusing
- I could not run any `beat` command, so every bar total and guitar fingering is unchecked.
- SPEC.md is in Chinese while the task and tooling are in English.
- Whether `r:4` after a `:8` note picks up the new duration (durations carry over) is easy to get wrong. I wrote a length on every token to avoid it.
- The "max 2 hands" drum rule is easy to hit when adding a crash on top of hi-hat plus snare.

## 2. Workarounds
- Power-chord shapes were copied from the demo (`[D3 A3 D4]` and similar) instead of using `beat voicing`.
- The outro's last bar is a drum `replace` with only crash and kick.
- A `!fall` on a held note is written as a tie (`D5:2~ D5:4!fall`).

## 3. Wishes
- Auto-generated rhythm patterns from the `chords:` line, e.g. "pm eighths on the root".
- A shorthand for a power chord, e.g. `D5` as a note token.
- Chord-tone checking for the lead against `chords`.
- An English version of the spec.

