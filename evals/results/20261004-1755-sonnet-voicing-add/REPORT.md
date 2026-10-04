# Eval report: 20261004-1755-sonnet-voicing-add

model `sonnet`, 3 run(s) per task

| task | final valid | first check clean | checks to green | F1 | dur acc | arts acc | dyn acc | task checks | chars/bar | cost $ | turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t3-compose-hardrock | 3/3 | 2/3 | 1.33 | — | — | — | — | 8/8, 8/8, 8/8 | 105.67 | 0.54 | 13.67 |
| t4-edit-demo | 3/3 | 3/3 | 1.00 | — | — | — | — | 12/12, 12/12, 12/12 | 99.33 | 0.21 | 14.00 |

## Error categories (distinct errors seen during the session, summed over runs)

| task | first check | whole session |
|---|---|---|
| t3-compose-hardrock | token 2, other 1, performance 1 | token 2, performance 1, other 1 |
| t4-edit-demo | — | — |
| **all** | token 2, other 1, performance 1 | token 2, performance 1, other 1 |

## Per run

### t3-compose-hardrock
- **run-1**: valid=True, error trace [4, 0, 0, 0, 0], F1=—, cost=$0.55, denied: ['Bash: beat validate song.beat.yaml --json | python3 -m json.tool 2>/dev/null || beat validate song.beat.yaml --json']
- **run-2**: valid=True, error trace [0, 0, 0, 0, 0, 0, 0], F1=—, cost=$0.53
- **run-3**: valid=True, error trace [0, 0, 0, 0, 0, 0, 0], F1=—, cost=$0.56, denied: ['Bash: beat validate song.beat.yaml --json | python3 -m json.tool 2>/dev/null || beat validate song.beat.yaml --json']

### t4-edit-demo
- **run-1**: valid=True, error trace [0, 0, 0], F1=—, cost=$0.20
- **run-2**: valid=True, error trace [0, 0, 0], F1=—, cost=$0.17
- **run-3**: valid=True, error trace [0, 0, 0, 0, 0], F1=—, cost=$0.27, denied: ['Bash: beat events song.beat.yaml --sections bridge --parts gt2; echo "---"; beat events song.beat.yaml --parts dr --sections verse --bars 1 --json | python3 -c "\nimport json,sys\nd=json.load(sys.stdin)']

## Agent notes

### t3-compose-hardrock / run-1

# Notes on composing with the Beat DSL

## 1. What was hard or confusing

- Repeating a section in `form` always plays identical content for every instance.
  It wasn't immediately obvious that giving the second chorus a different lead guitar
  part required defining a whole new section (`chorus2: extends: chorus`) rather than
  somehow varying content per-instance within one section definition.
- The outro's drum `hits` multi-bar format tripped me up at first: a trailing `|` per
  lane line is required to mark an (otherwise silent) bar, and the error message
  ("lane 'cr' has 1 bar(s) separated by '|', expected 2") only appears after the fact
  rather than from reading the spec's prose.
- `beat validate`'s "edit matches no note" error doesn't say *why* it failed to match
  (wrong beat vs. wrong pitch vs. wrong section/instance) — I had to manually recompute
  note onset times from the `notes` string to find that my target pitch started half a
  beat earlier than I assumed.

## 2. Workarounds for things the DSL couldn't express directly

- To give the final chorus a unique lead-guitar solo while keeping drums/bass/rhythm
  guitar identical to the first chorus, I duplicated the section via `extends` and
  overrode only the `gt2` part, then pointed the second `form` slot at the new section
  id instead of reusing `chorus`.
- There's no instrument-level "lead guitar accent via automation" shortcut, so the
  single extra-loud bend note in the solo was done with a `performance.edits` entry
  (`velocity: "+0.1"`) targeting one exact bar/beat/pitch rather than anything in the
  score layer itself.

## 3. Features or changes I'd want

- Per-instance overrides within a single section (e.g. `instances: { 2: { parts: { gt2: ... } } }`)
  so a repeated section can vary slightly without having to clone it with `extends`
  and juggle two section ids in `form`.
- A `beat events --at section:bar:beat --part p` lookup (or richer error context on
  failed `performance.edits`) to avoid manually re-deriving onset times from a `notes`
  string when aiming an edit.
- Clearer validator messaging for the multi-bar `hits` block, e.g. suggesting the
  missing trailing `|` directly in the error text.

### t3-compose-hardrock / run-2

# Notes on writing song.beat.yaml

## 1. What was hard or confusing

- It's not obvious up front which musical ideas are worth promoting to `patterns` vs.
  writing inline — I only realized the `use` + `transpose` combo would let one power-chord
  shape serve A5/D5/E5 after reading section 7 closely; a short worked example of
  "one pattern, three chords via transpose" in the spec would help.
- `beat events --sections X` on a section whose last note ties into the *next* section
  reports a tie error ("no following note") because the following section isn't loaded.
  This had me briefly worried something was wrong until I re-ran `validate` on the whole
  file and it was clean — worth noting in the tool's `--help`/docs that `--sections` is a
  display filter only and can produce misleading tie errors at the edges.
- The exact meaning of "hands" vs. "feet" for the 2-hand drum-overlap rule isn't stated
  next to the error text itself; I had to cross-reference the lane table's 肢体 (limb)
  column to confirm `bd`/`hp` don't count against the 2-hand cap.

## 2. Workarounds

- No native "chord quality transpose" concept — I got a full D and E chorus chord by
  picking an A-shape voicing from `beat voicing` and transposing the *pattern*, relying on
  the fact that guitar-shape transposition by semitones preserves playability. Had to
  manually verify the resulting fret spans would stay within range rather than the tool
  telling me up front.
- To make the solo's final note ring through the ending, I used a cross-section tie
  (`A4:1~` at the end of chorus2, continued as `A4:1~` at the start of outro) — works, but
  the dependency between two sections' note text isn't visible unless you know to look for it.
- There's no "silence this part for one bar then come in" shorthand other than `replace`
  with an all-rest grid/hits string; I avoided needing it by just starting drums at full
  energy from bar 1 instead of fighting the DSL for a one-bar silent pickup.

## 3. Features or changes I'd want

- A `beat events` flag to include one bar of context from the adjacent section (or just
  suppress the tie-boundary error) when `--sections` is used, so spot-checking a single
  section doesn't produce a false "error".
- A way to transpose a *chord-symbol* pattern by scale degree/Roman numeral (e.g. "same
  pattern, but on IV") rather than raw semitones, so the author doesn't have to work out
  the interval by hand and hope the fretting still works.
- `beat voicing` output fed directly as a `replace`/`transpose` suggestion, e.g. a flag
  that says "this transpose amount keeps the same string set" vs. one that doesn't, would
  remove the guesswork around fret-span validity when reusing shapes across chords.

### t3-compose-hardrock / run-3

# Notes on composing with the Beat DSL

## 1. What was hard or confusing

- Figuring out exact note-duration arithmetic by hand (making sure every bar's
  symbols sum to exactly 4 beats) is tedious and error-prone, especially for
  the free-form solo line with mixed eighth/sixteenth/dotted values. `validate`
  gives a clear error when a bar is off, but there's no "show me the running
  beat total as I type" feedback — you only find out after writing the whole
  bar.
- It's not obvious up front whether `patterns` loop-fill by truncating or by
  wrapping (e.g. does a 4-bar pattern used in an 8-bar section repeat cleanly,
  or does a 3-bar pattern in an 8-bar section get cut mid-bar?). I ended up
  sizing patterns to divide evenly into sections to avoid the question.
- The interaction between `extends`, `replace`, and `use` is powerful but the
  "which layer wins" rules needed a careful re-read of the spec before I was
  confident that a `chorus2: { extends: chorus, parts: { gt2: ... } }` would
  pick up `chorus`'s drums/bass/gt1 untouched while fully swapping gt2.

## 2. Workarounds used

- To give the final chorus a guitar solo while keeping an earlier, calmer
  chorus, I didn't try to parametrize one "chorus" section by instance;
  instead I made `chorus2 extends chorus` and overrode only the `gt2` part.
  This is the pattern the demo already uses for `verse2 extends verse`, and
  it was the only way to get genuinely different note content per repeat
  (performance `edits` can only nudge existing notes, not add new ones).
- For the chromatic pickup lick that walks a riff back to its downbeat (e.g.
  `G2 G#2` before landing back on `A2`), I just wrote it inline inside the
  pattern bar rather than finding any dedicated "approach note" notation —
  there isn't one, so literal chromatic notes stood in fine.
- Shortened the second verse to 4 bars by giving `verse2` its own `bars:`
  and `chords:` and re-declaring `use: riff_verse` with a `replace` on the
  last bar, since `extends` inherits `bars` by default and I needed a
  shorter instance.

## 3. Features or changes wished for

- A `beat events --by-bar` style dry-run that also flags "this bar sums to
  3.5/4 beats" per-pattern as you edit a `notes` string, instead of only at
  full `validate` time, would speed up writing dense bars a lot.
- Some shorthand for "repeat the previous bar transposed" at the top level
  (not just inside `replace`) would help write a 12-bar blues-style turnaround
  without retyping the chord-tone chord three times.
- A way for `patterns` to declare "this pattern is N bars but only cleanly
  tiles into multiples of N" so `validate` could warn earlier if a section
  length doesn't divide evenly, rather than relying on the generic
  "pattern didn't divide evenly" warning showing up only when it actually
  doesn't divide evenly.

### t4-edit-demo / run-1

# Notes

## 1. What was hard or confusing

- The spec and tool output mix Chinese and don't give an obvious way to check
  the "silence" of a part for a section other than noticing it's absent from
  `--by-bar` output.
- `beat events --by-bar` labels length as `/N` where N is beats, not note
  value (e.g. a whole note shows as `/4`, not `/1`); easy to misread at a
  glance against the `notes` string's own `:1` note-value suffix.
- Figuring out which octave/voicing to use for a brand-new section (so it
  sits in the same register as the rest of the song) required running
  `beat voicing` for every chord and eyeballing which option matched the
  existing gt1/bs/org ranges — there's no "match the register used elsewhere
  in this song" helper.

## 2. Workarounds

- No pattern reuse for the bridge drums/bass/gt1/org since each bar has a
  different chord — wrote the four bars out directly in `notes`/`hits`
  instead of defining a `pattern`.
- To get smooth voice leading for the organ chords (Am-C-D-B) I picked
  specific inversions from `beat voicing ... full --for organ` by hand rather
  than there being a "voice-lead from the previous chord" option.

## 3. Features or changes I wish existed

- A way to ask `beat voicing` to prefer voicings close to a given previous
  chord (for automatic smooth voice leading) instead of just "easiest first."
- A `beat events --by-bar` option to show note lengths in note values (e.g.
  `1`, `4.`) to match the `notes` syntax, in addition to/instead of beats.
- A quick "diff" mode for `beat events` to compare two sections/instances
  directly, useful when checking that a copied-and-modified section (like a
  bridge) matches intent relative to a neighboring section.

### t4-edit-demo / run-2

# Notes on working with the Beat DSL

## 1. What was hard or confusing

- `beat voicing` only takes a bare chord symbol, so figuring out which octave/shape
  to use for each chord in the bridge required a separate lookup per chord and then
  manually matching the style (root-as-lowest-note) already used elsewhere in the
  song. The tool doesn't know about "what the rest of the song already sounds like".
- The spec documents "half-time feel" only as a concept, not as a notation
  convention — it wasn't obvious whether "snare only on beat 3" should also imply
  silence on kick/hats, or whether a half-time feel conventionally still needs a
  kick. Had to infer the strictest reading from the literal instruction.
- Figuring out where a global change (snare laid-back timing) lives required
  scanning the whole file for every place that could set it (global `performance`,
  per-section, per-part) to be sure there was only one place to edit.

## 2. Workarounds used

- No workaround was needed for the bridge or the snare timing change — both were
  directly expressible with existing DSL features (`sections`/`parts`/`hits` and
  `performance.parts.dr.lanes.sd.offset_ms`).
- Used `beat voicing ... --for guitar/organ` purely as a lookup aid and hand-picked
  the voicing that matched the existing voicing style in the song (root note as the
  lowest pitch) rather than taking the tool's literal "easiest first" answer.

## 3. Features or changes wanted

- `beat voicing` could accept a hint like "near <pitch>" or "match style of
  section X" so suggested voicings follow the voice-leading/register already
  established in the song instead of always starting from the easiest shape.
- A way to query "what currently controls timing/velocity for part X" would help
  confirm a value lives in exactly one place before editing it (e.g. to be sure a
  `lanes.sd.offset_ms` isn't also overridden per-section).
- `beat events --by-bar` is great for drums/notes, but no equivalent compact view
  exists for confirming which parts are *silent* in a section — had to query a
  specific part with no notes and infer silence from empty output.

### t4-edit-demo / run-3

# Notes

## 1. What was hard or confusing

- The spec (`SPEC.md`) is written in Chinese, which added an extra translation step before
  I could confirm details like exact `hits` syntax or how `add`/`replace` interact.
- It's not obvious from the CLI help alone which note/octave a "root" should be voiced at for a
  given instrument; I had to lean on `beat voicing` and cross-check existing sections of the song
  to pick octaves that sound consistent with the rest of the arrangement.
- `offset_ms` is a lane-level absolute setting, not a relative delta, so "lay back 10ms more"
  required finding the current value and adding to it by hand rather than expressing the change
  as a delta directly in the DSL.

## 2. Workarounds

- To keep the new bridge section's voicings consistent with the rest of the song, I reused chord
  voicings already appearing in the `chorus` section's organ part (for C, D, and B) instead of
  picking arbitrary ones from `beat voicing`, since the tool doesn't know about the surrounding
  song context.
- "Half-time feel (snare only on beat 3)" was expressed literally as a single `sd: 3 | 3 | 3 | 3`
  hits line with no other drum lanes in the bridge, since the DSL has no dedicated "half-time"
  pattern primitive — each lane simply doesn't appear if it's silent.

## 3. Wishlist

- A relative adjustment syntax for performance-layer values (e.g. `offset_ms: "+10"`), mirroring
  what `edits[].velocity` already supports with `"+0.1"`/`"-0.1"`, so timing tweaks like "lay back
  N ms more" don't require manually reading and recomputing the absolute value.
- A way for `beat voicing` to accept the surrounding song file (or a key/register hint) so it can
  suggest voicings that stay in the same octave range as the rest of the arrangement, instead of
  always starting from its own "easiest first" default register.

