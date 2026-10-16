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
