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
