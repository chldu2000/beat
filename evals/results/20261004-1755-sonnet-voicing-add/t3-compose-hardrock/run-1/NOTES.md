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
