# Beat DSL Composition Notes

## 1. Hard or Confusing Parts

- **Drum grid step counting**: The grid requires exact step counts per bar (16 for 4/4 at default), and spaces/pipes don't count. It's easy to be off by one character. The error messages help, but multi-line grids make visual alignment tricky.

- **Rhythm notation ambiguity**: When using compact notation like `(A1:8)*8`, it's easy to lose track of whether you're filling a bar or multiple bars. No visual feedback until validation.

- **Tied notes across bars**: The `~` syntax for tied notes works, but requires the next bar to start with the exact same pitch. If you edit one note, you must remember to update the tie target, or it silently breaks.

- **Performance layer velocity values**: The spec uses numeric values (0.05, -0.05) but also mentions "+0.1" syntax in the edits section, which caused confusion—strings like `"+0.1"` are not valid, only numbers.

- **Section inheritance with `extends`**: The `extends` feature merges parts, which is powerful but the merge behavior (per-part overrides) could be clearer in error messages when parts conflict.

## 2. Workarounds Used

- **Drum patterns with consistent structure**: I created reusable patterns (`beat_verse`, `beat_chorus`, `drum_fill`) to avoid manually writing grid lines multiple times. This kept the codebase DRY.

- **Avoiding tied notes for simplicity**: For the outro, I used separate whole-note values instead of tying across bars, to avoid accidental tie-target mismatches.

- **Explicit measure notation**: In drum grids, I added `|` to separate bars visually, which helps catch step-count errors during manual review.

- **Bass notes aligned to chord progression**: When bass warnings appeared (bass playing non-chord tones), I switched from automatic eighth-note patterns to chord-aligned root notes.

- **Performance edits for accent control**: The performance layer's edits were too restricted for precise control, so I relied on patterns and performance velocity/offset settings instead.

## 3. Desired Features or Changes

- **Drum grid validation hints**: Show a per-bar step count as part of error messages (e.g., "bar 1 has 15/16 steps") to make debugging faster.

- **Visual grid editor with playback**: A simple UI to draw grid patterns and hear them in real-time would beat text editing for drum parts.

- **Richer `replace` syntax**: Allow `replace` to work on patterns as well as sections, so you can create a drum pattern and override just one bar within it without redefining the whole thing.

- **Tied-note safety**: Detect when a tie target doesn't exist or has a different pitch, and report it as an error rather than silently breaking the tie.

- **Multi-bar rhythm notation**: Shorthand like `4x (E1:8)*8` to mean "repeat this for 4 bars" would reduce line clutter in notes sections.

- **Performance part-level defaults**: It would be nice to set default `humanize`, `strum_ms`, or `offset_ms` at the part level without repeating them per-section.

- **Built-in metronome or tap-along click track**: For live composition, a click track render would help verify the feel before full render.
