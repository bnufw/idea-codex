# Idea Codex

面向 **Idea stage** 的 Codex CLI 配置仓库，主流程只使用两类本地材料：
- 用户运行时提供的方向 Markdown
- `papers/**/*.md` 中的论文方法笔记

它用于把模糊研究兴趣收敛成一个更合理、可验证、可继续推进的 idea。

## 这个仓库做什么

- 从本地 `papers/**/*.md` 建立方法图谱
- 区分真实 gap 和叙事性 gap
- 基于用户 brief 生成一个更强的 candidate idea
- 输出 research question、风险判断和最小验证草案

它不是代码仓，也不是论文定稿仓，而是一个偏研究前期分析的 Codex workspace。

## 目录结构

```text
.
├── AGENTS.md
├── papers/
├── plan/
├── prompts/
└── .codex/
    ├── config.toml
    ├── agents/
    └── skills/
```

- `AGENTS.md`：研究判断规则、输出标准、workflow
- `papers/`：本地论文方法笔记，格式为 Markdown
- `prompts/`：idea 生成与后续评审提示词
- `.codex/config.toml`：模型、sandbox、features、agents 配置

## 当前配置特点

- 模型：`gpt-5.4`
- reasoning：`xhigh`
- sandbox：`workspace-write`
- features：`multi_agent`、`memories`、`skill_approval`、`fast_mode`、`child_agents_md`、`default_mode_request_user_input`
- 论文来源：`idea` 生成阶段只读取本地 `papers/**/*.md`

## Agents

当前已配置的 agent：

- `literature-reviewer`
- `paper-miner`
- `kaggle-miner`

最常见的分工是：本地论文归纳看 `literature-reviewer`，强论文模式抽取看 `paper-miner`，工程 baseline 启发看 `kaggle-miner`。

## Skills

主流程最常用的本地 skill：

- `research-ideation`
- `idea-generator`
- `planning-with-files`
- `citation-verification`
- `daily-paper-generator`
- `kaggle-learner`

## 论文来源规则

- 用户必须提供一个方向 Markdown 路径，例如 `input_md_path`
- 论文语料只来自 `papers/**/*.md`
- `idea` 生成阶段不使用 Zotero、WebSearch、arXiv 或其他在线论文检索
- 如果后续要核实 novelty 或 feasibility，应单独进入后置核实阶段，不属于默认 ideation 流程

## 推荐用法

比较稳的顺序是：

```text
用户 brief -> 筛选相关 papers/*.md -> 方法/假设/缺口整理 -> 生成一个 candidate idea -> 最小验证设计
```

开始前优先看 `AGENTS.md`；生成 idea 时优先使用 `prompts/generate_idea.md` 与 `papers/**/*.md`。

## 边界

- 适合：方向探索、本地文献归纳、gap 分析、idea 收敛、最小验证设计
- 不适合：代码实现、训练调试、论文定稿

当任务重点变成“怎么实现和验证方法”时，更适合 `code`；变成“怎么写 paper 和 rebuttal”时，更适合 `paper`。
