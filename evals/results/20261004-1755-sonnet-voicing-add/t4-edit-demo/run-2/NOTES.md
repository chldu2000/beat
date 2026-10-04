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
