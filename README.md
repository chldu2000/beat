# beat

**LLM 作曲编曲、代码合成乐器的摇滚乐队。**

beat 让大语言模型（LLM）或 AI Agent 用一种文本 DSL 写歌，再由代码把乐谱编译成演奏事件，用物理建模合成器“演奏”出来，最后混音成完整的音频。和端到端的音频生成不同，beat 的每一个音符、每一处演奏细节、每一项混音设置都写在文本文件里，可以阅读、校验、修改和复现。

> 项目处于早期阶段（规格 v0.1），DSL 和合成器仍在快速变化。

## 特性

- **为 LLM 设计的乐谱格式**：YAML 加紧凑的文本记谱（`E2:8!pm`、`hh: every 0.5`），谱面、演奏、混音三层分离。
- **可操作的诊断信息**：每条错误都指明位置（`段落 > 声部 > 第 N 小节，第 B 拍`）并说明该怎么改，Agent 只凭这些信息就能修好歌曲。
- **可演奏性检查**：音域、吉他和弦能否按出来、鼓手的手脚够不够用等，都按真实乐器校验。
- **物理建模乐器**：
  - 电吉他、电贝斯：数字波导弦模型（保留振动状态，支持击弦 / 勾弦、闷音），加放大器和箱体模型
  - Hammond 风琴：91 个音轮、键触点弹跳、打击泛音、扫描颤音和 Leslie 旋转音箱
  - 鼓：底鼓、军鼓、嗵鼓为双鼓皮模态模型（非线性鼓槌接触、响弦、共鸣面开孔），整组鼓之间相互声学耦合；踩镲和镲片使用采样（可选）
- **混音层**：每个声部的通道条（高通、EQ、压缩、声像、混响发送），共用的 FDN 混响空间，母线压缩、BS.1770 响度归一化和真峰值限幅。
- **结果可复现**：同一个文件、同一个 `seed`，渲染结果逐采样一致。
- **导出 MIDI**，并提供面向 Agent 的 `--json` 输出。

## 工作原理

```
歌曲文件 (.beat.yaml)
  │  notation.py   文本记谱解析
  │  song.py       YAML → 段落、片段、曲式展开
  │  checks.py     可演奏性检查
  ▼
compile.py         时间线、连音线、演奏层（人性化、摇摆、力度）→ 事件表
  ├─► midi.py      MIDI 导出
  └─► render.py    合成器（synth/）→ 声部通道条 → 共用空间 → 母带 → WAV
```

架构和设计取舍的完整记录见 [docs/DECISIONS.md](docs/DECISIONS.md)。

## 安装

需要 Python 3.12 及以上和 [uv](https://docs.astral.sh/uv/)。

```sh
git clone git@github.com:chldu2000/beat.git
cd beat
uv sync
```

首次渲染时 numba 会编译合成器内核，需要多等一会儿。

### 镲片采样（可选）

踩镲和镲片使用 [DrumGizmo](https://drumgizmo.org/wiki/doku.php?id=kits:drskit) 的 DRSKit 2.1 采样（约 3 GB，不包含在仓库里）。没有采样时会自动改用合成的镲片。

```sh
# 下载 DRSKit2_1.zip（MD5 8c4d4b61ad9d354b3b845edd5da9c133），只解压踩镲和镲片
unzip DRSKit2_1.zip 'DRSKit/Hihat*' 'DRSKit/Crash*' 'DRSKit/Ride*' 'DRSKit/*.xml' -d samples
```

也可以用环境变量 `BEAT_SAMPLES` 指向存放 `DRSKit` 的目录。

## 快速上手

一首最小的歌：

```yaml
beat: 0.1

meta: { title: Hello Riff, tempo: 120, time: 4/4, key: E minor }

instruments:
  dr: { type: drums }
  bs: { type: bass }
  gt: { type: guitar, tone: crunch }

sections:
  verse:
    bars: 2
    parts:
      dr:
        hits: |
          hh: every 0.5 | every 0.5
          sd: 2 4 | 2 4
          bd: 1 3 3.5 | 1 3
      bs: { notes: "(E1:8)*8 | (E1:8)*6 D2:8 E2:8" }
      gt: { notes: "E2:8!pm E2!pm G2 E2!pm A2 E2!pm Bb2 A2 | (E2:8!pm)*4 [D3 A3]:4 [E3 B3]:4" }

form: [verse, verse]
```

保存为 `hello.beat.yaml`，然后：

```sh
uv run beat validate hello.beat.yaml                 # 校验
uv run beat events   hello.beat.yaml --by-bar        # 逐小节查看编译结果
uv run beat render   hello.beat.yaml -o out/hello.wav
uv run beat midi     hello.beat.yaml -o out/hello.mid
```

完整的示例见 [examples/](examples/)：

- [demo.beat.yaml](examples/demo.beat.yaml)：鼓、贝斯、两把吉他和风琴的硬摇滚演示曲
- [neon_asphalt.beat.yaml](examples/neon_asphalt.beat.yaml)：完整长度的器乐硬摇滚，小调主歌、大调副歌、16 小节吉他 solo

## 命令行

| 命令 | 作用 |
|---|---|
| `beat validate SONG [--json]` | 校验，列出错误和警告；有错误时退出码为 1 |
| `beat events SONG [--by-bar] [--parts a,b] [--sections x,y] [--bars 5-8] [--json]` | 输出编译后的音符 |
| `beat render SONG -o out.wav [--parts …] [--sections …] [--mix off]` | 渲染音频并打印混音报告 |
| `beat midi SONG -o out.mid` | 导出 MIDI |
| `beat voicing CHORD [full\|power] [--for guitar\|bass\|organ\|piano]` | 列出和弦的可演奏排列，供复制到 `notes` 中 |

各命令的完整参数见 [docs/SPEC.md §13](docs/SPEC.md#13-命令行工具)。

## 用 Agent 作曲

[`.claude/skills/compose/`](.claude/skills/compose/SKILL.md) 是作曲 Agent 的工作流程：读规格 → 写歌 → `validate` → 用 `events --by-bar` 核对 → 修改。在 [Claude Code](https://claude.com/claude-code) 中打开本仓库，让它写一首歌或修改现有的歌，就会使用这套流程。

[`evals/`](evals/README.md) 用来衡量全新的 Agent 只凭规格和作曲指南写 DSL 的能力（转写、创作、修改、修错四类任务），DSL 的改动以评测数据为依据。评测会调用 `claude -p`，消耗账号额度。

## 文档

- [docs/SPEC.md](docs/SPEC.md)：Beat DSL 规格（歌曲格式、事件表、命令行）
- [docs/DECISIONS.md](docs/DECISIONS.md)：愿景、架构和决策记录
- [evals/README.md](evals/README.md)：评测方法和指标

## 开发

```sh
uv run pytest                                 # 测试
uv run python scripts/audition.py out/audition   # 生成新旧引擎的对比试听片段（可加名称过滤，如 tom）
```

`src/beat/` 的模块分工见 [CLAUDE.md](CLAUDE.md)。修改 DSL 时请同步更新 `docs/SPEC.md`，重要的设计决定记录在 `docs/DECISIONS.md`。

## 路线图

- 用物理模型替换钢琴的占位合成器
- 乐理和音频分析（`beat analyze`）
- 多拍号、段落内变速；吉他指定弦和品；滑音、推弦、揉弦的渲染
- 混音自动化、贝斯侧链
- 五线谱 / 钢琴卷帘编辑界面
- 远期：小型交响乐团

## 许可证

本项目的代码和文档以 [MIT 许可证](LICENSE) 发布。

DRSKit 采样不属于本项目，由 DrumGizmo 以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 授权。发布使用了这些采样渲染的音频时，请在列出制作人员的地方注明：

> Cymbals: DRSKit by DrumGizmo (drumgizmo.org), CC BY 4.0
