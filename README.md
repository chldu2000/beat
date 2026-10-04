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

## 采样（可选，不在 git 里）

踩镲和镲片用 [DrumGizmo](https://drumgizmo.org/wiki/doku.php?id=kits:drskit) 的 DRSKit 2.1 采样（约 3 GB）。没有采样时自动改用合成的镲片。

```sh
# 下载 DRSKit2_1.zip（MD5 8c4d4b61ad9d354b3b845edd5da9c133），只解压踩镲和镲片
unzip DRSKit2_1.zip 'DRSKit/Hihat*' 'DRSKit/Crash*' 'DRSKit/Ride*' 'DRSKit/*.xml' -d samples
```

也可以用环境变量 `BEAT_SAMPLES` 指向放 `DRSKit` 的目录。

## 署名

DRSKit 采样以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 授权：用到它的歌曲，在列出制作人员的地方写上 “Cymbals: DRSKit by DrumGizmo (drumgizmo.org), CC BY 4.0”。
