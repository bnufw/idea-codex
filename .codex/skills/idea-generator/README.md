# Idea Generator

这个 skill 用来把“用户手动提供的方向说明”与 `papers/` 里的本地论文方法笔记结合起来，生成一个更合理、更完整的 research idea。

## 它做什么

- 读取用户提供的 `input_md_path`
- 读取 `papers/` 下相关的论文方法 Markdown
- 参考 `prompts/generate_idea.md` 的固定输出结构
- 基于已有方法做改进式构思，而不是脱离材料空想

## 必要输入

- `input_md_path`：用户手动提供的 Markdown 路径，写清研究方向、问题、约束、非目标等
- `papers/`：本地论文目录，默认读取 `papers/**/*.md`

## 工作流

1. 先读 `input_md_path`，锁定真实问题与约束
2. 再读 `papers/` 里相关论文方法
3. 提炼哪些方法可复用、哪里有明显不足
4. 必要时再调用 `paper-miner` 或 `literature-reviewer`
5. 最后按 `prompts/generate_idea.md` 产出一个候选 idea

## 适合的场景

- “根据 `plan/topic.md` 和 `papers/` 里的论文，帮我想一个更好的 idea”
- “我已经有探究方向，请结合本地论文方法给一个合理方案”

## 注意

- `papers/` 中的论文笔记默认都应是 `.md` 文件
- 若 `papers/` 为空，skill 会明确降级说明，不会假装有论文依据
- 若涉及 recent works、venue、citation 或 novelty 判断，仍应额外做实时核查
