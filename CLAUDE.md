# beat

LLM-composed rock band with code-synthesized instruments. The user communicates in Chinese.

- `docs/DECISIONS.md` — vision, architecture and the decision log. Append new decisions there.
- `docs/SPEC.md` — Beat DSL spec (song format, compiled events, CLI). Keep it in sync with the code.
- `.claude/skills/compose/` — the composer agent's workflow. Evals use the same text as its system prompt.
- `evals/` — measures how well a fresh agent writes the DSL (see `evals/README.md`).

## Commands

```sh
uv run beat validate examples/demo.beat.yaml
uv run beat render examples/demo.beat.yaml -o out/demo.wav
uv run pytest
```

## Code layout (`src/beat/`)

`notation.py` (text notations) → `song.py` (YAML → resolved sections) → `checks.py` (playability)
→ `compile.py` (timeline, ties, performance layer → events) → `render.py` + `synth/` (audio), `midi.py`.
`mix.py` resolves the `mix:` settings (presets, per-instrument defaults; no numba); `render.py` runs each
part's channel strip (`synth/eq.py`, `synth/dynamics.py`), the shared room (`room.py`) and the master
(glue compressor, BS.1770 loudness, true-peak limiter), and returns a mix report.

`synth/engine.py` maps each instrument type to named engines (`model: { engine: ... }`). Guitar and
bass share the plucked-string model: `fretboard.py` (string assignment) → `waveguide.py` (numba string
loop) → `plucked.py`; `guitar.py` / `bass.py` hold each instrument's `StringModel` and amp chain
(`amp.py`, `cab.py`). The organ: `registration.py` (presets and `model:` keys, no numba) → `organ.py`
(tonewheels, key contacts, percussion, scanner, preamp) → `leslie.py` (rotary speaker, stereo); its
Leslie speed reaches the engine as section `controls`. Drums: `drums.py` (subtractive kit; the default
`modal` engine swaps in `membrane.py` for the bass drum, snare and toms: two-head modal drum with an
implicit beater contact, an optional port and snare wires, numba; the drums hear each other's radiated
pressure, and overheads plus `room.py`, an FDN reverb, hear the whole kit). `samples.py` plays the
hi-hat and cymbals from the DRSKit samples in `samples/` (gitignored; synthesized if missing).
`scripts/audition.py` renders new-vs-old listening clips.

Diagnostics must name a location (`section > part > bar N, beat B`) and say what to change: the
composer agent fixes songs from these messages alone.
