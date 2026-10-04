Write song.beat.yaml so that it plays exactly the music described below: same parts (use the
part ids given), tempo, notes, rhythms, articulations and dynamics. Structure the file however
you like (sections, patterns, ...), but the compiled notes must match the description.

Time signature 4/4. Positions are 'bar N, beat B' counted from 1; lengths are in beats (1 beat = a quarter note). A length can run past the barline: then the note is held into the next bar(s).

Parts:
- dr: drums
- bs: bass
- gt: guitar, tone clean
- org: organ

Tempo and chords:
- bars 1-6: 92 BPM, chords Em | Am | B7 | C | C | Em

## dr (drums)
bar 1: [dynamic mf from here] beat 1: kick, ride; beat 1+2/3: ride; beat 2: side stick, ride; beat 2+2/3: ride; beat 3: kick, ride; beat 3+2/3: ride; beat 4: side stick, ride; beat 4+2/3: ride
bar 2: beat 1: kick, closed hi-hat; beat 1.5: closed hi-hat; beat 2: snare (accented), closed hi-hat; beat 2.5: kick, closed hi-hat; beat 2.75: snare (ghost note); beat 3: closed hi-hat; beat 3.25: snare (ghost note); beat 3.5: kick, closed hi-hat; beat 4: snare (accented), closed hi-hat; beat 4.5: closed hi-hat
bar 3: beat 1: kick, closed hi-hat; beat 1.5: closed hi-hat; beat 1.75: kick; beat 2: snare (accented), closed hi-hat; beat 2.5: open hi-hat; beat 3: kick, closed hi-hat; beat 3.5: closed hi-hat; beat 3.75: kick; beat 4: snare (accented), closed hi-hat; beat 4.5: open hi-hat
bar 4: beat 1: kick, hi-hat pedal, ride; beat 1.5: ride; beat 2: snare (flam), hi-hat pedal; beat 2.5: ride; beat 3: kick, hi-hat pedal, ride; beat 3.5: ride; beat 4: snare (accented), hi-hat pedal, ride; beat 4.5: ride
bar 5: beat 1: kick, snare (ghost note); beat 1.5: snare (ghost note); beat 2: snare (ghost note); beat 2.5: snare (ghost note); beat 3: kick, snare; beat 3.5: snare; beat 4: snare; beat 4.25: snare; beat 4.5: snare (accented); beat 4.75: snare (accented)
bar 6: beat 1: kick (accented), crash (accented); beat 3: snare (ghost note); beat 3.25: snare (ghost note); beat 3.75: snare (ghost note); beat 4: snare (accented)

## bs (bass)
bar 1: [dynamic mf from here] beat 1: E1, 1.5 beats (dotted quarter); beat 2.5: E1, 0.5 beats (eighth); beat 4: B1, 0.5 beats (eighth); beat 4.5: D2, 0.5 beats (eighth)
bar 2: beat 1: A1, 1/3 beats (eighth-note triplet); beat 1+1/3: A1, 1/3 beats (eighth-note triplet); beat 1+2/3: A1, 1/3 beats (eighth-note triplet); beat 2: A1, 1 beats (quarter)
bar 3: beat 1: B1, 2.5 beats; beat 3.5: A1, 0.5 beats (eighth); beat 4: G1, 1 beats (quarter)
bar 4: beat 1: C2, 6 beats
bar 6: beat 3: E1, 0.25 beats (sixteenth); beat 3.25: E1, 0.25 beats (sixteenth); beat 3.5: E1, 0.25 beats (sixteenth); beat 3.75: E1, 0.25 beats (sixteenth); beat 4: E1, 1 beats (quarter), staccato

## gt (guitar)
bar 1: [dynamic p from here] beat 1: E3, 1/3 beats (eighth-note triplet); beat 1+1/3: G3, 1/3 beats (eighth-note triplet); beat 1+2/3: B3, 1/3 beats (eighth-note triplet); beat 2: E4, 1/3 beats (eighth-note triplet); beat 2+1/3: D4, 1/3 beats (eighth-note triplet); beat 2+2/3: B3, 1/3 beats (eighth-note triplet); beat 3: G3, 1 beats (quarter)
bar 2: beat 1: A3, 0.25 beats (sixteenth); beat 1.25: B3, 0.25 beats (sixteenth); beat 1.5: C4, 0.25 beats (sixteenth); beat 1.75: D4, 0.25 beats (sixteenth); beat 2: E4, 0.75 beats (dotted eighth); beat 2.75: D4, 0.25 beats (sixteenth); beat 3: C4, 1.5 beats (dotted quarter)
bar 3: [dynamic f from here] beat 1: B3, 2 beats (half), bend up 1 semitone(s); beat 3: A3, 1 beats (quarter), slide into this note; beat 4: G3, 1 beats (quarter), vibrato
bar 4: beat 1: E3, 6 beats
bar 5: beat 3: chord E3 G3 B3, 1 beats (quarter), staccato; beat 4: chord E3 G3 B3, 1 beats (quarter), staccato
bar 6: [dynamic mf from here] beat 3: E4, 0.25 beats (sixteenth), hammer-on; beat 3.25: D4, 0.25 beats (sixteenth), pull-off; beat 3.5: E4, 0.25 beats (sixteenth), hammer-on; beat 3.75: D4, 0.25 beats (sixteenth), pull-off; beat 4: B3, 1 beats (quarter)

## org (organ)
bar 1: [dynamic pp from here] beat 1: chord E3 G3 B3, 6 beats
bar 2: beat 3: chord C3 E3 A3, 2 beats (half)
bar 3: beat 1: chord B2 D#3 F#3, 4 beats (whole)
bar 4: beat 1: chord C3 E3 G3, 8 beats

Work in the current directory and write the song to song.beat.yaml. Use `beat validate song.beat.yaml` and
`beat events song.beat.yaml` as often as you like; do not render audio.

When you are done, write NOTES.md with three short lists:
1. What was hard or confusing about the Beat DSL or its tools.
2. Workarounds you used for things the DSL could not express directly.
3. Features or changes you wish existed.
