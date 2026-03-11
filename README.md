# Idea Codex

面向 **Idea stage** 的 Codex CLI 配置仓库，主流程是 local-first，并优先使用两类本地材料：
- 用户运行时提供的方向 Markdown
- `papers/**/*.md` 中的论文方法笔记

当 brief 过于模糊、会影响 ideation 判断时，`research-ideation` 应先用一轮 `request_user_input` 补齐关键信息；当本地语料不足、过旧，或需要扩展最近邻工作时，它再补充在线论文搜索，优先使用 Exa MCP。

它用于把模糊研究兴趣收敛成一个更合理、可验证、可继续推进的 idea。

## 这个仓库做什么

- 从本地 `papers/**/*.md` 建立方法图谱，并在必要时在线扩展相邻工作
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
- `idea_prisma/`：保留的 legacy Python Prisma 编排器，供手动或历史用法继续使用

## 当前配置特点

- 模型：`gpt-5.4`
- reasoning：`xhigh`
- sandbox：`workspace-write`
- features：`multi_agent`、`memories`、`skill_approval`、`fast_mode`、`child_agents_md`、`default_mode_request_user_input`
- 论文来源：默认先读本地 `papers/**/*.md`，必要时由 `research-ideation` 补充在线论文搜索

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
- `idea-prisma`
- `planning-with-files`
- `citation-verification`
- `daily-paper-generator`
- `kaggle-learner`

## 论文来源规则

- 用户必须提供一个方向 Markdown 路径，例如 `input_md_path`
- 如果 brief 缺少 target scenario、hard constraints、non-goals 或“什么样的结果才算更好的 idea”，`research-ideation` 应先用一轮 `request_user_input` 补齐，再继续
- `papers/**/*.md` 是默认且优先的论文语料
- 当本地语料不足、主题变化快或用户明确要求扩展相邻工作时，`research-ideation` 可以补充 Exa MCP 或 WebSearch 做在线论文搜索
- 在线搜索结果应标注证据层级；摘要级证据不能包装成完整论文结论
- 若后续需要更强 novelty / feasibility 核实，可继续进入更重的后置核实阶段

## 推荐用法

比较稳的顺序是：

```text
用户 brief -> 必要时一轮 request_user_input 补齐关键槽位 -> 筛选相关 papers/*.md -> 必要时在线扩展相邻工作 -> 方法/假设/缺口整理 -> 生成一个 candidate idea -> 最小验证设计
```

开始前优先看 `AGENTS.md`；生成 idea 时优先使用 `prompts/generate_idea.md` 与 `papers/**/*.md`。

## 边界

- 适合：方向探索、本地文献归纳、gap 分析、idea 收敛、最小验证设计
- 不适合：代码实现、训练调试、论文定稿

当任务重点变成“怎么实现和验证方法”时，更适合 `code`；变成“怎么写 paper 和 rebuttal”时，更适合 `paper`。

## Prisma 风格 Dual-Branch Skill

这个仓库现在把 `idea-prisma` 作为主入口：它不是“调用根目录 `idea_prisma/` 的薄 wrapper”，而是一个独立 skill。

默认流程是：

```text
input_md_path + papers/**/*.md
-> Codex 原生 Prisma 分支
-> skill-local Gemini Prisma 分支
-> evaluation.md 对比评审
-> final_selected.md 选出单一 winner
```

如果希望让 Codex 直接执行这条流程，优先使用本地 skill `idea-prisma`。

### Skill 输入

`idea-prisma` 默认要求：

- `input_md_path`：必需，用户方向 brief 的 Markdown 路径
- `papers_dir`：可选，默认 `papers/`
- `output_dir`：可选，默认 `runs/`
- `max_rounds`：可选，默认 `2`

如果 brief 本身还模糊到会影响 expert 拆分或比较标准，skill 应先用 `request_user_input` 澄清，再继续执行。

### Gemini 分支环境变量

在 `.env` 中配置：

```env
GEMINI_API_KEY=...
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_MODEL_NAME=gemini-3-pro-preview
```

- 这些变量只给 `idea-prisma` skill 内的 Gemini 分支使用
- `GEMINI_BASE_URL` 应该是 **Google/Gemini 协议** 的根前缀，适合官方地址或 Gemini-compatible 代理
- `GEMINI_MODEL_NAME` 默认按本项目固定为 `gemini-3-pro-preview`
- Gemini 分支的阶段设定与旧 Prisma 路线保持一致：`planning / expert / synthesis` 都固定 `high`
- Gemini 3 请求参数按官方接口写成 `thinkingLevel=high`，不再暴露 `thinking_budget`
- `manager / review / synthesis` 不额外传 `temperature`；只有 expert 保留由 manager 动态分配的 `temperature`

### 标准产物

一次完整 skill 运行默认会在 `runs/<timestamp>/` 下保留：

- `codex/final_idea.md`
- `gemini/final_idea.md`
- `evaluation.md`
- `final_selected.md`
- 以及两条分支各自的 `manager_plan.json`、`selected_papers.json`、`experts.json`

### Legacy CLI

根目录 `idea_prisma/` 仍然保留，适合手动跑旧的 Gemini-only 路径：

```bash
python -m idea_prisma run -d input/1.md
```

参数含义：

- `-d` / `--direction-md`：用户当前的方向 brief，不是 prompt 模板
- `-p` / `--papers-dir`：本地 Markdown 论文笔记目录，默认就是 `papers/`
- `--output-dir`：可选，默认输出到 `runs/<timestamp>/`
- `--max-rounds`：可选，默认最多 2 轮 expert

这个 CLI 保留是为了不打断旧用法；新工作流以 skill 为主，不再把它当成 `idea-prisma` 的内部实现。
