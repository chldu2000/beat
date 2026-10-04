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
