这是一个想 idea 的工作流，当前约束如下：

1. `idea` 生成阶段不再使用 Zotero MCP，也不再通过网络搜索论文。
2. 论文来源只允许是 `papers/**/*.md` 中的本地 Markdown 笔记。
3. 用户必须手动提供探究方向 Markdown，运行时通过路径传入。
4. 生成 idea 时，可以借鉴 `papers/**/*.md` 中已有方法，但要产出一个更合理、更可辩护的候选 idea。
5. `prompts/generate_idea.md` 是当前 idea 生成的权威模板。
6. novelty / feasibility 的联网核实属于后置独立阶段，不属于默认 ideation 流程。
7. 评审阶段放到后续再做。
