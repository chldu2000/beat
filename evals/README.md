# DSL 评测

用来回答“Beat DSL 对 LLM 顺不顺手”。方法：让**全新的 Agent**（不带任何项目上下文）只看
`SPEC.md`、示例和作曲指南（`.claude/skills/compose/SKILL.md`）去完成任务，记录它的
校验—修改循环，并给最终结果打分。

```sh
uv run python -m evals.run --tasks t1,t2,t3,t4,t5 --runs 3 --model sonnet --label pilot
uv run python -m evals.run --grade-only evals/results/<dir>      # 只重新评分
uv run python -m evals.describe evals/refs/riff.beat.yaml        # 预览转写任务的描述
```

**每次运行都会调用 `claude -p`，消耗账号额度。** `--budget` 是单次运行的花费上限（美元）。

## 隔离

- 工作区建在系统临时目录，不在本仓库下，所以不会加载仓库的 `CLAUDE.md` 和记忆。
- `--safe-mode`：不加载用户的 CLAUDE.md、插件和 hooks。
- `--restricted`：文件工具只能访问工作区，参考答案（`evals/refs/`）读不到。
- `--permission-mode dontAsk` 加上 `Bash(beat *)`：除了 `beat` 和只读命令，其他命令一律拒绝。被拒绝的调用会记录在 `metrics.json` 的 `denied` 字段，这本身也是信号：Agent 想做但做不到的事。
- 工作区里的 `beat` 是 shim（`evals/shim.py`）：照常执行真正的 CLI，同时把每次调用时文件的错误列表和快照记录到 `beatlog/`。

## 任务（`tasks/`）

| 类型 | 测什么 | 打分 |
|---|---|---|
| transcribe | 把一段音符清单（由 `refs/` 里的参考歌曲自动生成，不是 DSL）写成 DSL | 和参考歌曲逐音比对：F1、时值、演奏法、力度准确率 |
| compose | 按创作要求自由创作 | 是否通过校验 + 任务要求（`checks`） |
| edit | 在现有歌曲上做指定修改 | `checks`，包括“其他段落没有被改动” |
| fix | 修好一个预置了错误的文件 | 是否通过校验 + 和原意（参考歌曲）比对 |

比对只看谱面（去掉 humanize、swing、edits），并且不在乎文件怎么组织（片段、段落怎么分都可以）。

## 指标（`report.py` 生成 `REPORT.md`）

- **final valid**：最终文件是否没有错误。
- **first check clean**：Agent 第一次调用 `beat` 时文件是否已经没有错误（相当于首次通过率）。
- **checks to green**：第几次检查时第一次达到零错误。
- **error categories**：错误按类型归类（`grade.py` 里的 `ERROR_CATEGORIES`），分为“第一次检查”和“整个过程”两栏。
- **F1 / dur acc / arts acc / dyn acc**：转写和修错任务的保真度。
- **chars/bar**：文件的紧凑程度。
- **Agent notes**：Agent 自己写的 NOTES.md（难点、变通写法、希望有的功能）。

## 结果

每次运行的结果保存在 `results/<时间>-<模型>-<标签>/`：`REPORT.md`，以及每个 run 的
`prompt.md`、`song.beat.yaml`、`NOTES.md`、`metrics.json`。完整对话（`transcript.jsonl`）和
`beatlog/` 也保存在那里，但不提交到 git。
