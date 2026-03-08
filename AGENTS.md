# Idea Project 配置

## 项目概述

**Idea Project** - 面向科研前期探索的独立 Codex CLI 配置

**配置路径**:
- 主配置：`.codex/config.toml`
- Agent 配置：`.codex/agents/<name>/config.toml`
- Skills 目录：`.codex/skills/`
- 本文件：项目根目录 `AGENTS.md`

**Mission**: 把模糊研究兴趣收敛成可验证、可比较、可继续推进的研究问题。

---

## 用户背景

### 学术背景
- **学历**: 计算机科学 PhD
- **投稿目标**:
  - 顶会：NeurIPS, ICML, ICLR, KDD, ACL, AAAI
  - 高影响期刊：Nature, Science, Cell, PNAS
- **关注点**: novelty 是否真实、问题定义是否扎实、reviewer 会如何质疑、最小验证是否足够说明问题

### 协作偏好
- 用中文回答，专业术语保留英文
- 喜欢先把真实约束、真实边界、真实风险钉死，再推进分析
- 不接受“像是有 gap”这类空泛判断
- 希望看到真实论文、真实时间线、真实相邻工作，而不是只看记忆
- 因为用户是编程初学者，涉及文件路径、CLI 工作流或较复杂命令时要补一句原因解释

---

## 全局配置

### 语言设置
- 用中文回答
- 专业术语保持英文
- 不翻译特定名词或方法名

### 工作目录规范
- 计划文档优先放在 `plan/`
- 临时材料优先放在 `temp/`
- 如目录不存在，可按需创建

### 任务执行原则
- 复杂问题先收敛问题定义，再扩展本地论文与方案
- `idea` 生成阶段的研究判断优先基于用户输入 Markdown、`papers/**/*.md`、真实代码和真实结果
- 不把 Zotero、WebSearch、arXiv 或其他在线论文检索当作默认论文来源
- 若证据不足以支撑“novel”“first”“state of the art”之类表述，必须明确降级措辞
- 不捏造引用、不脑补相关工作、不把猜测包装成结论

### 工作风格
- **任务管理**: 优先把讨论沉淀成可继续推进的 Markdown 计划
- **沟通方式**: 先给结论，再给证据、假设和风险
- **问题组织**: 多方案时优先给 2-3 个清晰分支，而不是一串发散想法

---

## 核心工作流

### Idea 工作流（本地 papers-only）

```
问题空间梳理 → 本地论文方法图谱 → gap 判断 → candidate idea 收敛 → 最小验证设计
```

| 阶段 | 核心目标 | 典型输出 |
|------|----------|----------|
| 1. 问题空间梳理 | 明确主题、约束、目标场景 | 主题边界、关键词、排除项 |
| 2. 本地论文方法图谱 | 从 `papers/**/*.md` 提炼方法、假设与局限 | method map、paper shortlist |
| 3. gap 判断 | 区分真实空缺与叙事性空缺 | gap list、closest baseline 对照 |
| 4. candidate idea 收敛 | 把用户兴趣改写成一个更合理的 idea | candidate idea |
| 5. 最小验证设计 | 评估是否值得进入实现阶段 | novelty / feasibility / risk 对照表、实验草案 |

### 支撑工作流

- **本地论文源**: `papers/**/*.md` 是默认且唯一的 ideation 论文来源
- **用户 brief**: 运行时必须提供一个 Markdown 输入路径，用来说明方向、约束、非目标和偏好
- **强论文拆解**: 用 `paper-miner` 抽取 framing、method pattern 与 evaluation 设计
- **工程启发补充**: 用 `kaggle-miner` 找可迁移 baseline、数据处理技巧和工程约束

### 阶段边界

- `idea` 生成阶段：只读本地 `papers/**/*.md` 与用户 brief
- novelty / feasibility 核实：若明确进入后置核实阶段，可单独使用联网子代理；该阶段不属于默认 ideation workflow

---

## 输出标准

默认输出应尽量落成以下形式之一：
- literature landscape summary
- gap list
- candidate research questions
- novelty / feasibility / risk 对照表
- 最小验证实验草案
- 可继续推进的 Markdown 计划

输出必须满足：
- **summary-first**：先给结论，再展开依据
- **assumption 明确**：哪些是用户已给条件，哪些是暂定前提
- **uncertainty 明确**：哪些结论依赖未验证信息
- **evidence 对齐**：每个核心判断都能追溯到本地论文笔记、代码或结果
- **边界清楚**：明确说明 idea 还缺什么，不能默认已经 ready

---

## 研究判断规则

### Novelty 判断
- novelty 必须先相对本地 `papers/**/*.md` 中最近、最强、最相邻的工作来判断
- 不把“换数据集”“换表述”“堆组件”直接当成研究贡献
- 若贡献主要来自 framing、evaluation、setting 或 pipeline，必须明确指出其贡献类型
- 若需要在线补核实，必须显式声明已经离开默认 ideation 阶段

### Gap 判断
- 区分 **真实能力缺口**、**评测缺口**、**工程可用性缺口**、**叙事性 gap**
- 若本地论文笔记已覆盖同类思路，要明确说明覆盖到什么程度
- 如果 gap 依赖过时基线或过时问题设定，应直接标记为高风险

### 问题定义
- research question 必须能被验证，而不是只可被讨论
- 尽量明确任务、数据、比较对象、主要指标和失败标准
- 若一个 idea 同时依赖多条高风险前提，默认先拆成更小问题

---

## Skills

### 本地 Skills 目录
本项目 skills 统一放在 `.codex/skills/`。

### 可用 Skills
- `research-ideation`: 基于用户 brief 与 `papers/**/*.md` 做问题梳理、gap 分析与问题收敛
- `idea-generator`: 基于用户提供的方向 Markdown 与 `papers/` 中的论文方法 Markdown 生成一个更合理的候选 idea
- `citation-verification`: 基于本地论文笔记核查关键引文、年份、venue 与 claim 是否一致
- `daily-paper-generator`: 从本地 `papers/**/*.md` 中筛选值得优先阅读或复核的论文笔记
- `kaggle-learner`: 提炼可迁移 baseline、工程技巧与竞赛启发
- `planning-with-files`: 把讨论结果整理成可继续推进的 Markdown 计划

### Skill 使用协议
- 每次响应前，先判断当前问题是否命中本项目某个 skill
- 优先使用最小必要 skill 集合，不机械展开全部 skills
- 若判断依赖论文证据，默认先看本地 `papers/**/*.md`
- 若需要输出持续推进文档，优先考虑 `planning-with-files`

---

## Skill Evaluation Protocol

Before responding to ANY user message:
1. Evaluate whether any project-local skill in `.codex/skills/` applies
2. Invoke the most relevant skill when it can materially reduce repeated reasoning or improve output quality
3. If no skill is useful, continue directly, but do not skip evaluation

---

## Agents

### 可用 Agents
- `literature-reviewer`: 本地论文归纳、主题对比、gap 识别与 novelty 风险判断
- `paper-miner`: 从强论文中抽取 framing、method pattern 与 evaluation 模板
- `kaggle-miner`: 从 Kaggle 解法中提炼 baseline、工程 heuristic 与数据处理经验

### Agent 调度规则
1. 本地论文图谱整理或 gap 判断优先 `literature-reviewer`
2. 需要抽取强论文写法、实验组织或 framing 模式时优先 `paper-miner`
3. 需要工程 baseline、数据技巧或竞赛启发时优先 `kaggle-miner`
4. 若任务足够聚焦，优先本地直接完成，不为“显得高级”而强行起 agent
5. 多条独立线索可并行，但必须避免重复读取同一批本地论文笔记

---

## 命名与文档规范

### 文件命名
- Markdown 文件优先使用语义清晰的 kebab-case
- 研究笔记可采用 `YYYY-MM-DD-topic.md`
- 计划文件名应能直接看出主题与用途

### 标签与描述
- 标签格式优先 Title Case，缩写保持全大写
- 描述尽量写清用途、前提、结论与未决项

### 引用记录
- 记录论文时尽量包含年份、venue、任务和比较关系
- 若仅看到了摘要或二手总结，要明确标注证据层级
- 若本地论文笔记缺少关键信息，要明确写成“本地证据不足”

---

## 目录规范

- `AGENTS.md`：项目长期行为约束，位于项目根目录
- `.codex/config.toml`：项目级 Codex 配置
- `.codex/agents/`：agent role 配置
- `.codex/skills/`：项目 skills
- `papers/`：本地论文方法 Markdown

说明：
- `AGENTS.md` 放项目根目录，便于按目录作用域生效
- agents 的 `config_file` 相对 `.codex/config.toml` 解析
- skills 统一收纳在 `.codex/skills/`

---

## Session Start Protocol

When starting a new session, ALWAYS:
1. Check git status and current workspace state
2. Identify the current topic, constraints, and target problem statement
3. List project-local skills that are likely relevant
4. Check whether the user has provided a valid Markdown brief and whether `papers/**/*.md` contains usable local evidence

---

## Session Wrap-Up Protocol

每次任务结束时，主动提供简要总结：

```
📋 本次操作回顾
1. [主要分析动作]
2. [关键证据来源]

📊 当前状态
• [当前 idea 的清晰度 / 风险 / 仍缺失的关键证据]

💡 下一步建议
1. [是否继续补本地论文笔记]
2. [是否重写 research question]
3. [是否进入最小验证设计]
```

---

## 研究诚信与安全规则

- 不伪造 citation、实验结果、时间线或文献结论
- 不把未读全文的论文说成“已经确认支持某结论”
- 不在项目文件中硬编码 API key、token、密码等敏感信息
- 若结论仅来自本地论文笔记，必须明确说明证据层级，不得包装成已完成全网核实
