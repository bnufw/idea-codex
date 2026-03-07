# Idea Codex

面向科研前期探索的独立 Codex CLI 配置仓库。

这个仓库不是论文代码仓，也不是实验仓。它的目标更靠前：把模糊兴趣收敛成可验证、可比较、可继续推进的 research question，并把文献、gap、risk 和最小验证思路整理清楚。

## Overview

- 定位：Idea-stage Codex workspace
- 目标：literature review、gap finding、research question design
- 工作方式：优先基于真实论文、真实时间线、实时检索和明确证据判断
- 默认输出：landscape summary、gap list、candidate research questions、novelty / feasibility / risk 表、最小验证草案

当前仓库中的真实入口主要有两类：

- `AGENTS.md`：定义长期工作规则、输出标准、workflow 和判断边界
- `.codex/`：定义 Codex 的模型、MCP、agents 和 skills

## Repository Layout

```text
idea/
├── AGENTS.md
└── .codex/
    ├── config.toml
    ├── agents/
    │   ├── kaggle-miner/
    │   ├── literature-reviewer/
    │   └── paper-miner/
    └── skills/
        ├── citation-verification/
        ├── daily-paper-generator/
        ├── kaggle-learner/
        ├── planning-with-files/
        └── research-ideation/
```

## Core Config

`idea/.codex/config.toml` 当前反映的是一个高上下文、偏研究分析的配置：

- 模型：`gpt-5.4`
- reasoning：`xhigh`
- context window：`1000000`
- sandbox：`workspace-write`
- features：`multi_agent`、`memories`、`skill_approval`、`fast_mode`、`child_agents_md`

这个配置说明该仓库更适合做：

- 多轮文献归纳
- gap 与 novelty 风险判断
- 多 agent 分工检索
- 从讨论沉淀到 Markdown 计划

## Agents

当前启用的 agent 都来自 `idea/.codex/config.toml`：

| Agent | 作用 |
| --- | --- |
| `literature-reviewer` | 系统化文献检索、主题归纳、gap 分析 |
| `paper-miner` | 从强论文中抽取 framing、method pattern、evaluation 结构 |
| `kaggle-miner` | 提炼可迁移 baseline、工程 heuristic 和数据处理经验 |

推荐分工：

- 需要建立 literature landscape 时，优先 `literature-reviewer`
- 需要看强论文怎么定义问题、怎么讲故事时，优先 `paper-miner`
- 需要找工程上可行的 baseline 或启发时，优先 `kaggle-miner`

## Skills

当前本地 skills 位于 `idea/.codex/skills/`：

| Skill | 作用 |
| --- | --- |
| `research-ideation` | 研究构思启动、gap 分析、问题收敛 |
| `citation-verification` | 核查引文、年份、venue 和引用准确性 |
| `daily-paper-generator` | 快速扫描近作，生成待深挖论文列表 |
| `kaggle-learner` | 提炼 baseline、工程技巧和竞赛启发 |
| `planning-with-files` | 把讨论结果沉淀成可继续推进的 Markdown 文档 |

如果只想记住一条规则，可以用下面这个最小映射：

- 想从“一个方向”变成“一个问题”时，用 `research-ideation`
- 想确认 citation 和时间线时，用 `citation-verification`
- 想快速补近作时，用 `daily-paper-generator`
- 想把结论落成文档时，用 `planning-with-files`

## Zotero Integration

这个仓库已经在 `idea/.codex/config.toml` 中声明了 Zotero MCP：

- command：`zotero-mcp`
- args：`serve`
- enabled：`true`

同时还声明了这些环境变量位：

- `ZOTERO_API_KEY`
- `ZOTERO_LIBRARY_ID`
- `ZOTERO_LIBRARY_TYPE`
- `UNPAYWALL_EMAIL`
- `UNSAFE_OPERATIONS`

注意两点：

1. 当前文件里的值是占位符，不是真实凭据
2. 这表示仓库默认假设你的本机已经安装并可运行 `zotero-mcp`

如果你要真正使用 Zotero：

- 先把这些占位符改成你自己的本地配置
- 再确认 `zotero-mcp` 在命令行里可执行
- 最后再让 Codex 调用相关文献工作流

这样做的原因很简单：Idea-stage 判断很依赖真实文献与真实元数据，Zotero 是这个仓库里最重要的外部连接点之一。

## Recommended Workflow

这个仓库最贴合 `AGENTS.md` 的工作流是：

```text
问题空间梳理
→ literature landscape
→ gap 判断
→ research question 收敛
→ 最小验证设计
```

一个比较稳的使用顺序可以是：

1. 先明确主题、约束、目标场景和排除项
2. 用 `literature-reviewer` 或 Zotero 建立文献格局
3. 用 `citation-verification` 检查关键近作、年份、venue 和 claim
4. 把 gap 分成能力缺口、评测缺口、工程缺口、叙事性 gap
5. 将问题重写成可验证的 research question
6. 用 `planning-with-files` 沉淀成 plan 或 research note

## How To Use

这个仓库适合被当成一个独立的 Idea workspace 使用。

最直接的理解方式是：

- `AGENTS.md` 决定你应该怎么分析问题
- `.codex/config.toml` 决定 Codex 用什么模型、agent 和 MCP
- `.codex/skills/` 提供可复用的研究分析动作

如果你要把它接到自己的 Codex 环境里，至少要检查以下几项：

- 仓库根目录下是否保留了 `AGENTS.md`
- `.codex/config.toml` 是否被当前 workspace 读取
- `zotero-mcp` 是否已安装
- Zotero 相关环境变量是否仍是占位值

## Working Principles

这个仓库的核心判断标准直接来自 `idea/AGENTS.md`：

- summary-first：先给结论，再给证据、假设和风险
- evidence-first：优先真实论文、真实代码、真实结果和实时检索
- uncertainty-explicit：未验证部分必须明确标注
- no fake novelty：不能把弱证据包装成 novelty
- question-first：研究问题必须可验证，而不是只可讨论

## Notes

- 这是 Idea-stage 仓库，不负责实现代码、训练 pipeline 或 paper 定稿
- 不要把“有意思的方向”直接当成“已成立的研究问题”
- 不要把占位的 Zotero 配置直接当成可运行配置
- 如果结论依赖近作、venue 或 citation 时序，应该优先做实时核验

## When To Use This Repo

适合：

- 研究方向还比较模糊
- 需要快速建立文献格局
- 需要判断 gap 是否真实
- 需要把 idea 收敛成可验证问题

不适合：

- 已经进入代码实现阶段
- 已经在写论文主文
- 主要任务是 rebuttal 或 camera-ready 修改

当任务从“研究问题是否成立”转向“如何把方法做出来”时，更适合切到 Code-stage 仓库；当任务变成“如何把结果写清楚”时，更适合切到 Paper-stage 仓库。
