# Idea Codex

面向 **Idea stage** 的 Codex CLI 配置仓库，主要用于 literature review、gap 判断、research question 收敛和最小验证设计。

## 这个仓库做什么

- 建立 literature landscape
- 区分真实 gap 和叙事性 gap
- 把兴趣改写成可验证问题
- 输出最小验证草案和风险判断

它不是代码仓，也不是论文仓，而是一个偏研究前期分析的 Codex workspace。

## 目录结构

```text
idea/
├── AGENTS.md
└── .codex/
    ├── config.toml
    ├── agents/
    └── skills/
```

- `AGENTS.md`：研究判断规则、输出标准、workflow
- `.codex/config.toml`：模型、sandbox、features、MCP、agents 配置
- `.codex/agents/`：文献、论文结构、工程启发相关 agent
- `.codex/skills/`：研究分析与计划沉淀工具

## 当前配置特点

- 模型：`gpt-5.4`
- reasoning：`xhigh`
- sandbox：`workspace-write`
- features：`multi_agent`、`memories`、`skill_approval`、`fast_mode`、`child_agents_md`
- 已声明 `zotero-mcp`

## Agents

当前已配置的 agent：

- `literature-reviewer`
- `paper-miner`
- `kaggle-miner`

最常见的分工是：文献格局看 `literature-reviewer`，强论文拆解看 `paper-miner`，工程 baseline 启发看 `kaggle-miner`。

## Skills

当前本地 skill 包括：

- `research-ideation`
- `citation-verification`
- `daily-paper-generator`
- `kaggle-learner`
- `planning-with-files`

## Zotero 说明

`idea/.codex/config.toml` 已声明 Zotero MCP，但里面的 `ZOTERO_API_KEY`、`ZOTERO_LIBRARY_ID` 等值目前是占位符。

这意味着：

- 结构已经接好了
- 真正使用前还需要替换成本地真实配置

## 推荐用法

比较稳的顺序是：

```text
问题空间梳理 -> literature landscape -> gap 判断 -> research question 收敛 -> 最小验证设计
```

开始前优先看 `idea/AGENTS.md`；需要确认 Zotero 或 agent 配置时看 `idea/.codex/config.toml`。

## 边界

- 适合：方向探索、文献格局、gap 分析、问题收敛
- 不适合：代码实现、训练调试、论文定稿

当任务重点变成“怎么实现和验证方法”时，更适合 `code`；变成“怎么写 paper 和 rebuttal”时，更适合 `paper`。
