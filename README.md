# beat

LLM 作曲编曲 + 代码合成乐器的摇滚乐队。

- 规格：[docs/SPEC.md](docs/SPEC.md)
- 决策记录：[docs/DECISIONS.md](docs/DECISIONS.md)
- 示例：[examples/demo.beat.yaml](examples/demo.beat.yaml)

```sh
uv sync
uv run beat validate examples/demo.beat.yaml          # 校验（--json 给 Agent 用）
uv run beat events   examples/demo.beat.yaml --parts gt1 --sections chorus
uv run beat render   examples/demo.beat.yaml -o out/demo.wav
uv run beat midi     examples/demo.beat.yaml -o out/demo.mid
uv run pytest
```
