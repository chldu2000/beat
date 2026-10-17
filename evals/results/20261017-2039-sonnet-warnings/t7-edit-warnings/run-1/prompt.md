song.beat.yaml contains an existing song. Make these changes:

1. Add a new 2-bar section with id `break`, played after the solo and before `final`. Only the
   drums play in it (a groove or fill that builds into the last chorus); everyone else is silent.
2. Make the snare drum lay back 5 ms more than it currently does, everywhere in the song.

Work in the current directory and write the song to song.beat.yaml. Use `beat validate song.beat.yaml` and
`beat events song.beat.yaml` as often as you like (`beat` is on PATH; run it exactly like that); do not
render audio. Bash only runs `beat` and read-only commands, one command per call (no heredocs,
redirects or loops): write files with the Write and Edit tools. A denied command does not
mean `beat` is unavailable.

When you are done, write NOTES.md with three short lists:
1. What was hard or confusing about the Beat DSL or its tools.
2. Workarounds you used for things the DSL could not express directly.
3. Features or changes you wish existed.
