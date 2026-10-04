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

Diagnostics must name a location (`section > part > bar N, beat B`) and say what to change: the
composer agent fixes songs from these messages alone.
