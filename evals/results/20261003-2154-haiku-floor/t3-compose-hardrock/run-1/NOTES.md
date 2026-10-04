# Composing "Thunder Road" - Beat DSL Observations

## 1. What was hard or confusing

- **Time value notation**: The distinction between `:1 :2 :4 :8 :16 :32` took careful verification. It's not immediately intuitive that `:4` = 1 beat in 4/4 time. I had to count beats multiple times to ensure bars added up correctly (e.g., `:2 :2` = 4 beats, not 8).
- **Bar length validation errors**: When bar durations were wrong, the error messages pointed to the bar but not the exact problem until I manually added up the note lengths. Seeing "duration 6 beats, expected 4" required me to work backwards to identify which notes were the culprit.
- **Grid syntax for drum fills**: Multi-lane drum grids with explicit bar separators (using `|`) required careful formatting. The YAML multiline strings needed proper indentation, and I initially wrote the hi-hat pattern wrong on the first attempt.
- **Replace bar ranges**: Using `5-6: { notes: "..." }` requires providing exactly 2 bars worth of notes, not 1. I wrote `"[F#2 C#3 F#3]:8!pm..."` (which was only 1 bar) when it needed the `|` separator to define 2 bars.
- **Extends inheritance**: The `extends: verse` feature is powerful but it's not entirely clear what "only override listed parts" means. I had to verify that the parts from the parent section were actually being used when I didn't override them.

## 2. Workarounds used

- **Rhythmic filler**: For the lead guitar melody in bar 35 (bar 7 of chorus2), I used eighth notes (`E5:8 D#5:8 C#5:8 B4:8`) to create a fast run, then quarter notes for the landing. The DSL doesn't have glissando or slide notation, so I used discrete notes to suggest a descending passage.
- **Final bar truncation**: The outro bars were written out fully (4 bars total) to give a proper hard-rock ending. I avoided using complicated syncopation and stuck to clean quarter-note and half-note rhythms.
- **Drum fills as patterns**: Instead of writing tom fills inline, I created a reusable `fill` pattern that could be dropped into replace sections at the end of sections. This made it easier to iterate on the transition points without rewriting the same 16 steps multiple times.
- **Power chord simplicity**: For the rhythm guitar in the chorus, I used simple quarter-note power chords `[D3 A3 D4]:4` repeated four times per bar, even though AC/DC often uses more syncopated rhythms. The 4-on-the-floor approach was easier to verify and sounded appropriate.

## 3. Wished for features

- **Shorthand for repeated note sequences**: Something like `*(pattern, n)` or `rep(notes, count)` to avoid writing `([A2 E2 A3]:8!pm)*8` every time. A macro or template system would reduce redundancy.
- **Glissando and slide notation**: `!sl` (slide) is marked as "⏳ 忽略" (ignored in v0.1), so I couldn't notate the smooth transitions I hear in my head for lead guitar passages. Having `!slide-up`, `!slide-down`, or a gliss() notation would help.
- **Chord shorthand for multi-part sections**: Writing `[A2 E3 A3]:4` is compact, but having a way to write "A power chord in octaves" once and reuse it would reduce error-prone repetition across verses and choruses.
- **Humanize at the section level**: The `performance` layer allows global humanize and per-part tweaks, but it would be nice to apply different humanization to, say, the intro vs. the chorus without listing every part explicitly.
- **Transposition for entire sections**: `transpose: 2` works for patterns and parts, but there's no way to transpose an entire section or to re-voice chords (e.g., "play this D major, but an octave higher"). The chord definitions in `chords:` don't map to voicings.
- **Note dynamics inline without @**: Writing `@f A2:8` to set force on one note is a bit verbose. A shorthand like `A2:8f` or `A2:8@f` (without the space) would be cleaner.
- **Grid visualization in `by-bar` mode for drums**: The `beat events --by-bar` output is terse for drums (just "bd+hh" etc.). A visual grid representation (even ASCII art) would make it easier to spot rhythm mistakes at a glance.
