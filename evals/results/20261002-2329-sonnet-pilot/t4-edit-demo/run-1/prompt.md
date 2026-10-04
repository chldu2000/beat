song.beat.yaml contains an existing song. Make exactly these changes:

1. Add a new 4-bar section with id `bridge`, played after the second chorus and before the
   outro. Chords: Am | C | D | B. In the bridge the drums play a half-time feel (snare only on
   beat 3 of each bar), bass plays whole notes on the chord roots, gt1 plays one sustained power
   chord per bar, the organ plays the chords, and gt2 is silent.
2. Make the snare drum lay back 10 ms more than it currently does, everywhere in the song.

Do not change anything else.

Work in the current directory and write the song to song.beat.yaml. Use `beat validate song.beat.yaml` and
`beat events song.beat.yaml` as often as you like; do not render audio.

When you are done, write NOTES.md with three short lists:
1. What was hard or confusing about the Beat DSL or its tools.
2. Workarounds you used for things the DSL could not express directly.
3. Features or changes you wish existed.
