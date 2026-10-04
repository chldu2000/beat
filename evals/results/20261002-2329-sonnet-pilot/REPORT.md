# Eval report: 20261002-2329-sonnet-pilot

model `sonnet`, 3 run(s) per task

| task | final valid | first check clean | checks to green | F1 | dur acc | arts acc | dyn acc | task checks | chars/bar | cost $ | turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t1-transcribe-riff | 3/3 | 3/3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 259.33 | 0.42 | 11.00 |
| t2-transcribe-tricky | 3/3 | 0/3 | 2.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 351.67 | 0.63 | 14.67 |
| t3-compose-hardrock | 3/3 | 2/3 | 1.33 | — | — | — | — | 8/8, 8/8, 8/8 | 128.67 | 0.47 | 12.33 |
| t4-edit-demo | 3/3 | 3/3 | 1.00 | — | — | — | — | 12/12, 12/12, 12/12 | 101.67 | 0.26 | 14.67 |
| t5-fix-riff | 3/3 | 0/3 | 3.33 | 1.00 | 1.00 | 1.00 | 1.00 | — | 222.00 | 0.26 | 19.67 |

## Error categories (distinct errors seen during the session, summed over runs)

| task | first check | whole session |
|---|---|---|
| t1-transcribe-riff | — | — |
| t2-transcribe-tricky | playability 3, grid_length 1, bar_duration 1 | playability 3, grid_length 1, bar_duration 1 |
| t3-compose-hardrock | grid_length 5 | grid_length 5 |
| t4-edit-demo | — | — |
| t5-fix-riff | yaml 3 | bar_count 3, tie 3, grid_length 3, yaml 3, range 3, token 2, structure 2 |
| **all** | grid_length 6, playability 3, yaml 3, bar_duration 1 | grid_length 9, playability 3, bar_count 3, tie 3, yaml 3, range 3, token 2, structure 2, bar_duration 1 |

## Per run

### t1-transcribe-riff
- **run-1**: valid=True, error trace [0, 0, 0, 0, 0, 0, 0], F1=1.0, cost=$0.41, denied: ['Bash: beat events song.beat.yaml --parts bs --sections sectionA --json | python3 -m json.tool | head -100']
- **run-2**: valid=True, error trace [0, 0, 0, 0], F1=1.0, cost=$0.43, denied: ['Bash: beat events song.beat.yaml --json > events.json && python3 -c "\nimport json\nd=json.load(open(\'events.json\'))\nfor e in d[\'events\']:\n    if e[\'part\']==\'bs\':\n        print(e[\'src\'][\'global_bar\'], e']
- **run-3**: valid=True, error trace [0, 0, 0, 0, 0, 0, 0], F1=1.0, cost=$0.41

### t2-transcribe-tricky
- **run-1**: valid=True, error trace [3, 0, 0, 0, 0, 0], F1=1.0, cost=$0.66, denied: ['Bash: beat events song.beat.yaml --json --parts dr 2>&1 | python3 -c "\nimport json,sys\nd=json.load(sys.stdin)\nfor e in d[\'events\']:\n    print(e[\'src\'][\'bar\'], e[\'src\'][\'beat\'], e[\'lane\'], round(e[\'vel']
- **run-2**: valid=True, error trace [1, 0, 0, 0, 0, 0], F1=1.0, cost=$0.55, denied: ['Bash: beat events song.beat.yaml --parts dr --json | python3 -m json.tool | head -200']
- **run-3**: valid=True, error trace [1, 0, 0, 0, 0, 0], F1=1.0, cost=$0.70, denied: ['Bash: beat events song.beat.yaml --parts dr --json | python3 -c "\nimport json,sys\nd=json.load(sys.stdin)\nfor e in d[\'events\']:\n    print(e[\'src\'][\'bar\'], e[\'beat\'], e[\'lane\'], round(e[\'velocity\'],2), ']

### t3-compose-hardrock
- **run-1**: valid=True, error trace [0, 0, 0, 0, 0, 0], F1=—, cost=$0.40, denied: ['Bash: beat validate song.beat.yaml --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d)" 2>&1 | head -20']
- **run-2**: valid=True, error trace [5, 0, 0, 0, 0], F1=—, cost=$0.55, denied: ['Bash: python3 -c "\nlines = {\n\'hh\': \'x-x-x-x---------\',\n\'sd\': \'----X---xx------\',\n\'t1\': \'------------x---\',\n\'t2\': \'-------------x--\',\n\'t3\': \'--------------xX\',\n\'bd\': \'x-------x-------\',\n}\nfor k,v in li', 'Bash: beat events song.beat.yaml --sections verse --parts dr --json | python3 -m json.tool | head -80']
- **run-3**: valid=True, error trace [0, 0, 0, 0, 0], F1=—, cost=$0.46, denied: ['Bash: beat validate song.beat.yaml --json\necho "---"\nbeat events song.beat.yaml --json 2>&1 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[\'meta\'])"']

### t4-edit-demo
- **run-1**: valid=True, error trace [0, 0, 0, 0, 0, 0, 0], F1=—, cost=$0.36, denied: ['Bash: beat events song.beat.yaml --sections bridge --json | python3 -m json.tool | head -200', 'Bash: beat events song.beat.yaml --parts dr --sections verse | head -5\necho "---"\nbeat events song.beat.yaml --json --sections intro,verse,chorus,bridge,outro --parts dr | grep -o \'"part": "dr"[^}]*\' ']
- **run-2**: valid=True, error trace [0, 0, 0, 0], F1=—, cost=$0.18, denied: ['Bash: beat events song.beat.yaml --sections bridge --json | python3 -m json.tool 2>/dev/null || beat events song.beat.yaml --sections bridge --json']
- **run-3**: valid=True, error trace [0, 0], F1=—, cost=$0.24, denied: ['Bash: find / -maxdepth 4 -iname "SPEC.md" 2>/dev/null; which beat; find / -maxdepth 6 -iname "demo.beat.yaml" 2>/dev/null', 'Bash: beat events song.beat.yaml --json | python3 -c "\nimport json,sys\nd=json.load(sys.stdin)\nsecs=[]\nfor e in d[\'events\']:\n    s=e[\'src\'][\'section\']\n    inst=e[\'src\'][\'instance\']\n    key=(s,inst)\n   ']

### t5-fix-riff
- **run-1**: valid=True, error trace [1, 6, 0, 0, 0, 0], F1=1.0, cost=$0.28
- **run-2**: valid=True, error trace [1, 4, 0, 0, 0], F1=1.0, cost=$0.22, denied: ['Bash: python3 - <<\'EOF\'\nlines = {\n"cr": "X--------------- | ---------------- | ---------------- | X---------------",\n"rd": "--x-x-x-x-x-x-x- | x-x-x-x-x-x-x-x- | x-x-x-x-x-x-x-x- | ----------------",\n']
- **run-3**: valid=True, error trace [1, 6, 6, 0, 0, 0, 0], F1=1.0, cost=$0.27, denied: ['Bash: python3 -c "\nbars = [\'x-x-----x-x-----\', \'x-x-----x-x------\', \'x-x-----x-x-----\', \'X---------------\']\nfor b in bars:\n    print(len(b), b)\n"', "Bash: s='x-x-----x-x------'; echo ${#s}"]

## Agent notes

### t1-transcribe-riff / run-1

# Notes

## 1. What was hard or confusing

- There's no notation token for an arbitrary beat length like 2.5 beats (only
  `1 2 4 8 16 32` plus dot/triplet). Figuring out that a tie (`~`) between two
  notes of the same pitch is the intended way to build a non-standard duration
  took some thought, and isn't spelled out as an explicit technique in the spec
  (it's only shown tying across a barline).
- The spec doesn't say explicitly whether `!acc`/`!pm` etc. persist to
  following notes the way duration and velocity do. I assumed articulations
  are per-note only (not "sticky"), which matched the intended transcription,
  but it would be good to confirm this in the spec.
- Figuring out how to express a mid-bar silence (a rest between two attacks
  where the beat-grid specifies exact start times) required manually computing
  gaps rather than being able to just place notes "at" beat positions.

## 2. Workarounds

- Used `F1:2~ F1:8` (and similarly for guitar chords) to express a single
  sustained note of 2.5 beats, since no single duration token covers that
  length.
- Inserted an explicit `r:8` rest in bass/guitar bar 4 to represent the silent
  half-beat between the second and third attacks (beat 3.0–3.5), since notes
  are specified as a contiguous sequence rather than by absolute position.
- Split the song into two `sections` (bars 1-4, bars 5-8) specifically because
  the `dynamic` (mf → f) changes at bar 5 for every part; this let the section
  default velocity handle it instead of per-note `@` markers.
- Built small one-bar drum `patterns` (`beat_a`, `fill_a`, `ride_beat`,
  `crash_start`, `ending_hit`) and used `replace` for the bars that differ,
  rather than writing one long grid per section.

## 3. Wishlist

- A duration token/shorthand for arbitrary tied lengths (e.g. `:2.5`) so ties
  aren't needed just to express a plain sustained note.
- A way to place a note/rest at an explicit beat position within a bar (e.g.
  `@2.5 F1:1`) instead of having to compute rests and offsets by hand to keep
  a bar's total duration exact.
- `beat events` output showing the source `notes`/`grid` token alongside each
  event (not just bar/beat) would make cross-checking faster.

### t1-transcribe-riff / run-2

# Notes on writing song.beat.yaml

## 1. What was hard or confusing

- Figuring out how `replace` interacts with a tiled pattern wasn't fully
  spelled out: it's not documented whether a replaced bar's `grid` lanes
  fully override the bar (lanes not mentioned are silent) or merge with the
  tiled pattern's lanes. I assumed full override, which turned out to be
  correct, but had to infer it from the example rather than the spec text.
- There's no notated duration for "2.5 beats" (half + eighth) as a single
  token — durations are limited to the `1 2 4 8 16 32[.][t]` set, so any
  length that isn't a sum of one dotted/plain power-of-two value has to be
  built from multiple tied notes.
- The accent placement in the English description ("beat 1: kick, crash
  (accented)") was ambiguous about which of the two simultaneous hits the
  accent applies to; had to make a judgment call (crash accented, kick not).

## 2. Workarounds

- Used a tie (`:2~` + `:8`, or `:4.~` equivalent) between two notes of the
  *same pitch* to represent a single held note of a duration that has no
  direct token (e.g. 2.5 beats), since ties merge same-pitch notes into one
  sustained event.
- Modeled a bar with a short rest in the middle (bass/guitar bar 4, beat 3
  to 3.5) with an explicit `r:8` rather than trying to express the gap
  implicitly.
- Kept the two 1-bar drum grooves (plain backbeat, ride backbeat) as
  `patterns` tiled across each 4-bar section, then used `replace` only on
  the bars that actually differ (the two fills and the crash-on-beat-1 /
  final-hit bars), instead of writing out all 8 bars of drum grid by hand.

## 3. Features or changes I'd want

- A duration token (or explicit `beats: N` syntax) for arbitrary
  beat-fraction lengths, so "2.5 beats" doesn't require a tie workaround.
- Explicit documentation (not just inferred from the example) of whether
  `replace` on a `grid` bar fully replaces all lanes or merges with the
  pattern being tiled.
- A way to mark which element of a simultaneous multi-hit grid step (e.g.
  kick + crash on the same step) is accented, rather than accenting the
  whole step or none of it.

### t1-transcribe-riff / run-3

# Notes

## 1. What was hard or confusing

- The spec and tool output are in Chinese while the task prompt is in English; no functional
  problem, but it required careful cross-referencing between `SPEC.md` and the English task
  description.
- It's not obvious from the spec alone whether per-note articulations (`!pm`, `!acc`, ...) carry
  over like duration/dynamic do, or must be repeated on every note. I assumed they don't carry
  over (each note needs its own `!` marks) and confirmed this by checking `beat events` output.
- Expressing a note with a duration that isn't a "clean" subdivision (e.g. 2.5 beats) isn't
  directly supported — you have to compose it from a tie across two notated durations
  (`:8~ :2`). This is discoverable from the demo file but not spelled out clearly in the spec
  text itself.
- Whether `replace` bar indices in a section are section-relative or song-global is only
  demonstrated by example, not stated explicitly (it's section-relative).

## 2. Workarounds

- A 2.5-beat note (bass/guitar bar 3, and similar in bar 4) was built as two tied notes
  (`:8~` followed by `:2`) rather than one literal duration.
- An "implicit" eighth-note rest in the middle of a bar (bass/guitar bar 4, between beat 3 and
  3.5) had to be written explicitly as `r:8` since the DSL has no concept of implied silence
  between two timed events.
- The one-bar drum fill in bar 4 and the one-off ending hits in bar 8 were written as their own
  one-bar `patterns` and pulled in via `replace`, rather than inlining a 4-bar grid, to keep the
  repeated 3-bar grooves short and readable.

## 3. Features/changes wished for

- A short explicit statement in the spec about whether articulation markers persist across
  notes like duration/dynamic do (currently only inferable).
- A way to express "this many beats" directly (e.g. `:2.5`) for the common case of a sustained
  note that doesn't line up with a single named subdivision, instead of requiring a tie across
  two notated values.
- A dedicated accent-only drum "hit" grid shorthand would be nice, but not essential — `drv_hit`
  with a single `X` per lane worked fine.

### t2-transcribe-tricky / run-1

# Notes on writing song.beat.yaml

## 1. What was hard or confusing

- The `steps` setting for a drum `grid` applies to the whole block, so a bar that
  needs triplet subdivisions (bar 1's swung ride) can't live in the same grid
  string as bars that need straight 16th-note resolution (bars 2, 3, 5, 6).
  There's no per-bar `steps` override inside one multi-bar grid.
- Durations that don't correspond to a single token (e.g. 2.5 beats, or a note
  that trails off into silence for the remainder of a bar) aren't directly
  expressible — you have to reconstruct them from tied notes and explicit
  rests, and the arithmetic has to add up exactly or `validate` rejects the
  bar. A few of the English descriptions had an implicit trailing rest that
  wasn't stated explicitly (e.g. bass bar 2, guitar bar 2), which only showed
  up as a "duration ... expected 4" error.
- `beat events` plain-text output doesn't show note length in beats directly
  (only seconds), so checking "is this really a dotted quarter" means doing
  tempo math by hand or switching to `--json`.

## 2. Workarounds

- Split the 6-bar drum part into six single-bar `patterns` (one per distinct
  rhythmic grid, including one with `steps: 12` for the triplet ride feel in
  bar 1) and stitched them together with `use` + `replace` on every bar. This
  sidesteps the "one steps value per grid block" limitation.
- Represented long sustained notes/chords that cross bar lines (bass bar 4's
  6-beat C2, guitar bar 4's 6-beat E3, organ's 6-beat and 8-beat chords) as a
  whole-note (or half-note) tied `~` into the following bar(s), closed by a
  matching note/chord of identical pitches with no trailing tie.
- Added explicit rests (`r:2`, `r:8`, etc.) wherever the prose described notes
  that didn't fill out the full 4 beats of a bar, since `validate` requires
  each bar's note strings to sum exactly to the bar length.
- Used inline `@f` / `@mf` dynamic markers inside a part's `notes` string to
  express dynamic changes mid-part (e.g. guitar going p → f at bar 3 → mf at
  bar 6), since the `dynamic:` field only sets one static default per part.

## 3. Features or changes I'd want

- Per-bar `steps` (or an explicit "this bar is a triplet bar" shorthand) so a
  single grid block can mix straight and triplet subdivisions.
- A duration shorthand for "tie to end of bar" or arbitrary beat lengths
  (e.g. `:2.5` or `len=2.5`) instead of requiring manual tie decomposition.
- `beat events` text output could include the length in beats (not just
  seconds) next to each event, to make eyeballing rhythms against a spec
  faster without doing BPM arithmetic.

### t2-transcribe-tricky / run-2

# Notes

## 1. What was hard or confusing

- Drum `grid` notation assumes one fixed subdivision (`steps`) for an entire
  multi-bar block. This song mixes triplet-eighth feel (bar 1), straight
  eighths (bar 4), and sixteenths (bars 2, 3, 5, 6) in the same part, so a
  single grid string could not express all of it without going to a very
  fine common subdivision (48 steps/bar).
- No direct note value for arbitrary beat lengths like 2.5 beats (only
  `1 2 4 8 16 32` plus dot/triplet). Had to reconstruct it from two tied
  notes of the same pitch.
- It's not obvious from the spec alone whether a tie (`~`) is only meant to
  span a barline or can also join two consecutive notes of the same pitch
  within one bar; it worked (and merged into a single sustained event in
  `beat events`), but this isn't spelled out explicitly.
- The flam-needs-2-hands rule combined with simultaneous hand-played lanes
  (e.g. ride) isn't mentioned until validation fails; the error message was
  clear, but it's a rule worth knowing before transcribing the kit part.

## 2. Workarounds

- Split the drum part into six separate 1-bar `patterns`, each with its own
  `steps:` value (12, 16, 8, 16, 16, 16) matched to the subdivision actually
  needed in that bar, then stitched them together with `use` + `replace`
  per bar instead of one multi-bar grid.
- Built the 2.5-beat bass/guitar notes (`B1`, implicit elsewhere) and the
  6-beat and 8-beat sustained chords (bass `C2`, guitar `E3`, organ chords)
  as tied sequences (`:2~ :8`, `:1~` into the next bar, etc.) since no
  single note value covers those lengths or crosses a barline directly.
- Mid-phrase dynamic changes (guitar's `p` → `f` → `mf`) were done with
  inline `@f` / `@mf` markers inside the `notes` string rather than new
  sections, since the song is really one continuous 6-bar passage.

## 3. Features or changes wished for

- Per-bar (or per-note-group) subdivision overrides within a single grid
  block, so one `grid:` entry could mix triplet and sixteenth regions
  without needing several small patterns stitched via `replace`.
- A tied/arbitrary duration shorthand (e.g. `B1:2.5` or `B1:10t16`) to avoid
  manually decomposing non-power-of-two lengths into tied notes.
- `beat events` output defaults to a human table; a quick way to filter it
  to a single bar range (like `--sections`) would have made spot-checking
  individual bars faster during authoring.

### t2-transcribe-tricky / run-3

# Notes on writing song.beat.yaml

## 1. What was hard or confusing

- Mixing subdivisions within one drum part: bar 1 needed a triplet-feel ride
  pattern (`steps: 12`) while the rest of the song uses straight 16th-note
  grids (`steps: 16`, the default). The spec doesn't show whether `steps` can
  live inline inside a `replace:` block, so it felt safer to push each bar
  into its own named pattern and reference it with `use:` — more boilerplate
  than I expected for "just one odd bar."
- Figuring out which hits count as "hands" vs "feet" for the 2-hand limit
  isn't spelled out explicitly in prose — I had to infer it from the lane
  table (`bd`/`hp` are feet, everything else is hands) and from the error
  message the validator produced (`drummer needs 3 hands`) when I mistakenly
  added a ride hit under a snare flam.
- Silent/rest stretches are easy to get subtly wrong: several bars in the
  prose description only state the notes that sound and leave the remaining
  beats implicit. Getting the arithmetic right for how much rest to insert
  (e.g. bar 2 bass ending on an implicit 2-beat rest, bar 1 guitar needing a
  trailing quarter rest) required manually summing durations beat-by-beat.
- Long tied notes spanning a barline (6- and 8-beat sustains) require
  splitting the duration across the bar boundary by hand (`:1~` then `:2`),
  and it's not obvious from the spec alone that ties only work within a
  single continuous `notes` string — i.e. they can't cross separate
  `sections`, which constrained the whole file to one 6-bar section instead
  of one section per bar.

## 2. Workarounds

- Used one single 6-bar section (instead of six 1-bar sections) purely so
  that `~` ties could bridge bar 4→5 (bass, guitar, organ) and bar 1→2
  (organ) within one continuous notes string.
- Per-bar dynamic changes on guitar (p → f → mf) were done with inline `@f`
  / `@mf` markers in the middle of the notes string rather than per-section
  `dynamic:`, since the section is shared by all parts but only guitar's
  dynamic needed to change mid-stream.
- For the drum part's one triplet bar, defined a separate 1-bar pattern with
  its own `steps: 12` and pulled it in via `use:`, then overrode the other
  five (16-step) bars individually through `replace:` referencing more 1-bar
  patterns — avoided relying on an untested "steps inside replace" feature.

## 3. Features or changes I'd want

- An explicit statement (and/or validator warning) about whether `steps:`
  is allowed directly inside a `replace:` entry, so odd bars don't require a
  whole extra named pattern.
- A lint/warning for "this bar's note durations don't fill it" that
  suggests the missing rest length automatically, rather than only erroring
  with the mismatch total — would save manual beat-by-beat addition.
- Documentation (even one line) on whether ties can span `sections`/`form`
  boundaries, since it's a natural thing to want and the answer isn't
  stated.

### t3-compose-hardrock / run-1

# Notes on composing with the Beat DSL

## 1. What was hard or confusing

- It's not obvious from `SPEC.md` alone which guitar chord voicings will pass the
  "playable chord" validator (distinct strings, max-min fret span <= 4, excluding
  open strings). I had to manually map notes to strings/frets by hand before
  `validate` would confirm a 5-note chord like `[A2 E3 A3 C#4 E4]` was legal; a
  6-note version of the same chord failed and I only found out by trial and error.
- `replace` on a bar replaces the *entire* bar's content, not just the lane/voice
  you want to change. For drums this means adding a crash on bar 1 of a pattern
  required re-typing the `hh`/`sd`/`bd` lanes that were already correct in the
  base pattern, instead of just adding a `cr` line.
- The relationship between `chords` (an annotation for analysis/warnings) and the
  actual `notes`/`grid` content isn't enforced, so it's easy to write a `chords`
  label that doesn't match what's actually sounding (e.g. labeling a power chord
  "D" vs "D5"). There's no validation feedback loop telling you they drifted apart.

## 2. Workarounds used

- To get a different, fully-composed lead-guitar part in the final chorus without
  touching the earlier chorus, I defined a second section (`chorus2: extends: chorus`)
  that overrides only `gt2`, rather than trying to express "same section, different
  content on repeat N" directly in `form`. The `performance.edits` per-instance
  mechanism only supports small note-level tweaks, not a full solo rewrite.
  Reusing the same section id for both choruses wasn't possible since the solo and
  rhythm part differ too much.
- For the 4-major-chord sustain at the outro, I checked playability by hand (string/
  fret assignment) and dropped to a 5-note voicing after the 6-note version I first
  wanted was rejected by the chord-fingering validator.
- The short "verse2"/"chorus2" sections are separate pattern-free `notes` blocks
  rather than reusing `riff_a`/`bass_riff` wholesale, since chord changes needed to
  land on specific bars that didn't divide evenly into the 2-bar pattern length.

## 3. Features or changes I wish existed

- A lane-scoped `replace` for drum grids (e.g. only overriding `cr` for one bar)
  instead of requiring the whole bar's grid to be retyped.
- A way to say "repeat this section but override only part X" directly in `form`
  (e.g. `chorus@2: { gt2: ... }`), instead of needing `extends` to create a whole
  new section id for a single-part variation.
- A `beat events --section chorus --diff chorus2` or similar command to quickly
  compare two sections' compiled events, useful when using `extends` to check that
  only the intended part changed.
- Validator feedback (even just a warning) when a `chords` annotation's root/quality
  doesn't match the pitches actually present in `notes`/`grid` for that bar.

### t3-compose-hardrock / run-2

# Notes on composing with Beat DSL

## 1. What was hard or confusing

- Articulation marks (`!pm`, `!acc`, etc.) do **not** carry over between notes the way
  duration/velocity do — only visible by close reading of the spec's wording and the demo
  example. Easy to assume `!pm` sticks until changed, like duration does.
- Drum grid length errors only report "expected 16" vs. actual count, not which character
  is extra/missing — for a 16/17-char string you have to recount by hand rather than get a
  diff.
- It's not obvious from the spec whether single-note (non-chord) pitches on guitar/bass are
  checked for fret-span playability the same way chords are, or just checked against overall
  instrument range.

## 2. Workarounds

- To keep chord-change bars DRY while still using `use:`-filled looping patterns, I built a
  library of 1-bar patterns per chord (`riff_a`, `stab_d`, `stab_e`, `ring_a`, `ring_d`,
  `ring_e`, `bass_a`, `bass_d`, `bass_e`) and relied on `replace` with bar numbers/ranges to
  swap in the right chord for each bar, instead of writing long multi-bar `notes` strings.
- Reused the same `chorus` section for the final chorus via `extends`, overriding only `gt2`
  to add the lead solo, so the "chorus comes back" requirement and the "solo in the last
  chorus" requirement could both be satisfied without duplicating the rhythm section.
- Verified exact grid lengths and note-duration sums by hand (counting characters/beats)
  since there's no local way to lint this without invoking the CLI.

## 3. Features or changes I'd want

- A `beat lint-grid` or similar that points out exactly which step index is extra/missing
  when a drum grid line has the wrong length, instead of just a count mismatch.
- A way to say "this articulation applies until the next pitch/articulation override" as an
  opt-in, to avoid repeating `!pm` on every single palm-muted note in a riff.
- Some indication in `beat events` (or a `--summary` flag) of total duration/beats per bar,
  to sanity-check note-value math before running full validation.

### t3-compose-hardrock / run-3

# Notes on composing in Beat DSL

## 1. What was hard or confusing

- It's not obvious from the spec alone whether `replace` blocks on a `use`-based
  part accept a `transpose` key alongside `use`. I avoided the question entirely
  by writing separate transposed patterns (`riff_A`/`riff_D`/`riff_E`) instead of
  testing an undocumented combination.
- The guitar "playable power chord" rule (distinct strings, max fret span 4) is
  checked by a solver, so there's no quick way to predict by eye whether a chord
  voicing will validate — you just have to try it and read the error.
- It's easy to lose track of running duration totals in a `notes` bar by hand;
  a syntax error ("expected 4 beats, got 3.5") only shows up after writing the
  whole section, not while typing it.

## 2. Workarounds used

- To get the same riff shape over three different chords (A, D, E) without
  relying on an unverified `transpose`-inside-`replace` feature, I hand-transposed
  the riff and bass patterns into three separate named patterns and selected
  the right one per bar range with `replace: { bars: { use: ... } }`.
- For the final chorus's "big ending" (crash + sustained chord) I didn't find a
  dedicated "ending" marker, so I just made a one-bar drum pattern (`ending`)
  with a single accented crash+kick hit and let the pitched parts ring out a
  whole-note chord in that same bar.
- To make the second guitar feel like an overdub that only "arrives" for the
  choruses, I simply omitted `gt2` from sections where it should be silent
  (there's no explicit "rest for this part" keyword needed — omission is enough).

## 3. Features or changes wanted

- A way to pass `transpose` through a `replace` block (confirmed to either work
  or not work in the spec) would have let me reuse one riff pattern across
  chords instead of writing three near-identical copies.
- A dry-run "beat count" checker/formatter for `notes` strings (e.g. annotate
  each bar with its running beat total) would speed up hand-writing long chord
  rhythms.
- Named "hits"/"stabs" shorthand for common rock endings (unison hit + cymbal
  choke) would save boilerplate for song outros.

### t4-edit-demo / run-1

# Notes

## 1. What was hard or confusing

- The spec and tool output are in Chinese while the song file and comments are in English; no
  problem once read, but it means there's no bilingual quick-reference to cross-check terminology
  against (e.g. confirming "half-time feel" has no dedicated DSL construct).
- There's no first-class concept of a "power chord" or "chord voicing" — `notes` is just raw
  pitches, so turning a chord symbol like `Am` into a sensible 2-note power-chord shape is a manual
  music-theory step done by the author, not something the DSL or tool can check against the
  declared `chords:` string.
- Drum `grid` steps are an absolute step index into the bar, so writing "snare only on beat 3"
  means counting steps by hand (`steps_per_bar / beats_per_bar * (beat-1)`) rather than addressing
  beats directly.
- It's not obvious from the spec whether an empty/omitted part (like silent `gt2`) needs an
  explicit marker or can simply be left out; `beat events --parts gt2` was needed to confirm
  "not listed" really does mean silent rather than an error.

## 2. Workarounds used

- For the bridge's "one sustained power chord per bar" and "organ plays the chords", there's no
  helper that derives a power-chord voicing or a close triad from a chord symbol, so I hand-picked
  guitar/organ pitches by matching the octave/voicing conventions already used elsewhere in the
  song (e.g. reusing the same `[C3 G3]`/`[D3 A3]`/`[B2 F#3]` shapes from the verse/chorus, and
  extending the pattern to `A` for the new `Am` chord).
- "Snare only on beat 3" was expressed as a one-lane `grid` with no `bd`/`hh` lines at all, relying
  on the rule that unwritten lanes simply don't play, rather than any explicit "mute lane" syntax.
- Confirmed the half-time snare placement and the gt2 silence by reading `beat events` output
  directly (timestamps, beat numbers, and the absence of gt2 rows) instead of trusting the grid
  math alone.

## 3. Features or changes wanted

- A way to reference "beat N" directly in grid lane strings (or a helper to place a single hit at
  a named beat) instead of counting dashes.
- A built-in way to derive power-chord / triad voicings from the section's `chords:` string for a
  given part, so parts that "play the chords" don't require manually re-deriving pitches that are
  already declared at the section level.
- A lint/warning when a part's notes diverge in quality from the declared `chords:` (e.g. flagging
  that a part plays a bare 5th against a chord symbol with a 3rd), to catch mismatches like the
  intentional power-chord simplification versus a real mistake.

### t4-edit-demo / run-2

# Notes

## 1. What was hard or confusing
- The spec and tool help are in Chinese; mapping terms like "lane", "grid steps", and chord
  voicing rules to the right YAML keys took a careful re-read before editing.
- It's not obvious from the spec alone what counts as a valid "power chord" voicing for the
  guitar fret-span/playability check; I had to infer the convention (root-fifth-octave) from
  existing sections rather than from an explicit rule.
- Drum grids use absolute step positions (e.g. step 9 of 16 for beat 3), so translating "snare
  on beat 3" into `-`/`X` characters requires doing the beat-to-step arithmetic by hand.

## 2. Workarounds
- No direct "chord root to MIDI note" helper exists, so bass/organ/guitar pitches for the new
  bridge chords (Am, C, D, B) were chosen manually by matching octave/voicing conventions already
  used elsewhere in the song (e.g. reusing the `[C3 G3 C4]`-style power-chord shape and the
  organ's triad voicings from the chorus).
- "Half-time feel, snare only on beat 3" has no dedicated grid shorthand, so it was written as a
  plain grid with a single `X` per bar rather than reusing a pattern.

## 3. Features I wish existed
- A way to reference "chord root" or "chord tones" symbolically in `notes`/`grid` (e.g. `root:1`)
  instead of hand-picking MIDI pitches that match a section's `chords:` line.
- A `beat diff` command to compare two versions of a song's compiled events, to make confirming
  "only X changed" type edits (like the snare offset) easier than manually re-reading timestamps.

### t4-edit-demo / run-3

# Notes

## 1. What was hard or confusing

- `grid` strings are position-sensitive but there's no explicit column/beat ruler in the
  file — figuring out that "beat 3" in 4/4 (16 steps/bar) is step 9 meant counting dashes
  by hand (`steps per beat = steps/bar ÷ time signature numerator`).
- It's not obvious from the spec alone whether an instrument omitted from a section's
  `parts` is "silent" vs. an error; had to reread section 7 ("声部没有列出就不演奏") to be
  sure `gt2: silent` just means leaving it out.
- The lay-back performance knob (`offset_ms`) is a per-lane *performance* setting, separate
  from the `grid`/`notes` pitch content — easy to miss on a quick skim that "snare lay back"
  isn't something you touch in the pattern at all.

## 2. Workarounds

- There's no vocabulary for "half-time feel" as a named concept; expressed it literally as
  a one-lane grid pattern (`sd` only, hit on beat 3) with everything else omitted.
- Power chords are just written as two-note dyads (`[A2 E3]`) rather than a dedicated
  "power chord" notation — matched the voicing style already used elsewhere in the song
  (verse/chorus gt1) for consistency rather than inventing a new convention.

## 3. Wishes

- A named/reusable "rhythmic feel" concept (e.g. half-time, swing-16, etc.) that expands to
  a grid, instead of hand-counting dashes to land a hit on a specific beat.
- A shorthand chord-to-voicing helper (e.g. `chord:Am:power` or `chord:Am:triad`) so simple
  chordal parts (whole-note pads, power chords) don't require manually spelling out pitches
  that are already implied by the `chords:` line.
- `beat events --sections` output showing the section order/instance list directly (e.g. a
  `--form` flag) would make it faster to confirm placement of a new section without scanning
  full event dumps.

### t5-fix-riff / run-1

# Notes

## 1. What was hard or confusing

- The YAML "must quote notes starting with `[`" rule is easy to forget, and
  the resulting YAML parse error points at a YAML-internal line/column
  rather than the Beat-level location (section/part/bar), so it takes an
  extra mental step to map it back to the offending `notes:` line.
- `validate` reports only one error at a time when the error is a YAML
  syntax error (nothing else is checked until the file parses), but once
  parsing succeeds it reports all semantic errors at once. Good to know,
  but it means you can't predict up front how many fix/validate round
  trips a single file will take.
- Articulation typos (`!palm` instead of `!pm`) and pattern-name typos
  (`grove` instead of `groove`) are caught, but only as independent,
  unrelated-looking errors — there's no "did you mean `pm`?" suggestion,
  so diagnosing typos relies on re-reading the spec's articulation table.

## 2. Workarounds

- No real DSL workarounds were needed — every problem in the file was a
  genuine mistake (unquoted notes, a typo'd pattern name, a typo'd
  articulation, a chords list one bar short, an off-by-one grid string, a
  bass note out of range, and a tie into a different pitch). Fixes were
  all small, local edits that kept the original riff shapes.
- For the broken tie (`F1:8~ G1:2` tying into a different pitch), I
  inferred the intended target pitch by cross-checking the guitar part's
  held chord in the same bar (`[F2 C3 F3]` held across the whole bar) and
  changed the bass's final note to match (`F1:2`) rather than removing the
  tie, since the guitar clearly intended a sustained chord under the tie.

## 3. Features or changes I wish existed

- `beat validate` could point YAML syntax errors at the Beat-level
  location (section/part) when possible, instead of only the raw
  YAML line/column.
- A "did you mean?" suggestion for near-miss identifiers (pattern names,
  articulation tags) would make typo-class errors much faster to fix.
- An option to run `events` or `validate` with a dry-run "explain" mode for
  ties/chords would help confirm intent without having to mentally replay
  the grid/notes string (I used `beat events --parts ... --sections ...`
  for this, which worked well, but discovering that this is the right
  investigative tool wasn't obvious from `validate`'s error message alone).

### t5-fix-riff / run-2

# Notes

## 1. What was hard or confusing

- The error messages are precise about *where* something is wrong (section, part,
  bar) but not always about *what the composer probably meant*. E.g. a tie
  mismatch (`F1` tied to `G1`) just says the tie is broken; figuring out which
  side was the typo required comparing against the guitar part in the same bar.
- Unquoted `notes:` strings starting with `[` fail with a raw YAML parser
  traceback rather than a Beat-specific diagnostic, even though the spec and a
  comment in the example file both warn about this. It would be easy to miss
  if you didn't already know the rule.
- Grid alignment bugs (one extra/missing `-` in a 16-step lane) are invisible
  by eye in a monospace block when bars are concatenated with `|` on one line;
  you only find them via the validator's bar/lane-specific step count.

## 2. Workarounds

- No real workarounds were needed — every error had a direct, in-spec fix
  (quote the string, correct the pattern-name typo, correct the articulation
  name, add the missing chord, fix the tied pitch, fix the grid length).
- Used `beat events` on the affected sections after each fix to visually
  confirm the repaired bass tie and drum groove matched the surrounding
  (already-correct) guitar/drum material, rather than trusting validation
  alone.

## 3. Features or changes I'd want

- A "did you mean" suggestion for unknown pattern names (`grove` vs `groove`)
  and unknown articulations (`!palm` vs `!pm`), since both are simple typos of
  valid identifiers already defined elsewhere in the file.
- A lint check that a section's `chords` bar count matches its `bars` count
  with a pointer to which bar is missing, rather than only "3 bars of chords,
  expected 4" (useful as-is, but naming the missing bar index would save a
  recount).
- A grid-diff helper (or `beat events` option) that prints step index markers
  above/below long concatenated multi-bar grid lines, making off-by-one
  alignment errors visible without needing the validator round-trip.

### t5-fix-riff / run-3

# Notes

## 1. What was hard or confusing

- The YAML quoting rule (strings starting with `[` must be quoted) is easy to
  forget when writing `notes` by hand, and the resulting YAML parser error
  doesn't point at the Beat-level problem — you have to recognize it's a
  quoting issue yourself. The tool's hint text did help here, though.
- Several errors were simple typos (`grove` vs `groove`, `!palm` vs `!pm`,
  `G0` vs `G1`) that only surface one at a time per `validate` run, so fixing
  a file with multiple unrelated mistakes takes several validate/edit cycles.
- The tie-mismatch error (`tie from F1 but the next note is G1`) required
  cross-referencing the guitar part's rhythm/held-chord to figure out which
  side of the mismatch (the tied pitch vs. the destination pitch) was the
  actual typo, since the spec doesn't say which one is "wrong."

## 2. Workarounds

- No real workarounds were needed — all six validation errors were
  straightforward typos/omissions (missing chord bar, misspelled pattern
  name, misspelled articulation, out-of-range note, wrong tie target,
  one-character-too-long drum grid row). Fixed each in place without
  changing the song's structure.

## 3. Features or changes wished for

- `beat validate` reporting all errors it can find in one pass is already
  the case here, which was nice — but it would help even more if grid
  length errors could show a diff/alignment against the expected length
  instead of just "17 steps, expected 16", since counting dashes by eye is
  error-prone.
- A lint-style check that flags unknown articulation names against the
  spec's known list (with a "did you mean `!pm`?" suggestion) would have
  caught `!palm` and `grove`/`groove`-style typos faster.

