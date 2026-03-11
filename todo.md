这是一个想 idea 的工作流，当前约束如下：

1. `idea` 生成阶段默认 local-first，但 `research-ideation` 可以在本地语料不足时补充在线论文搜索。
2. `papers/**/*.md` 仍是默认且优先的本地 Markdown 论文笔记来源。
3. 用户必须手动提供探究方向 Markdown，运行时通过路径传入。
4. 生成 idea 时，可以借鉴 `papers/**/*.md` 中已有方法，但要产出一个更合理、更可辩护的候选 idea。
5. `prompts/generate_idea.md` 是当前 idea 生成的权威模板。
6. 在线论文搜索可以用于扩展相邻工作；更强 novelty / feasibility 核实仍属于更重的后置阶段。
7. 评审阶段放到后续再做。

direction(research-ideation)->具体做法(Prisma)->

Prisma项目解决问题的能力很强，当我讨论完direction后，我需要把此direction交给Prisma，去得到一个完整的idea内容(用于发表oral级别的论文)。你需要借鉴Prisma项目的核心流程，把它写成python。我会在.env中配置Gemini的key，base_url和model_name。
写成脚本，传两个参数，一个是direction一个是papers目录下的参考文章，传入时要简短说明这两个参数一个是direction，一个是现有相关论文的方法

# 3.9
-[] 测试一下Prisma流程，输出在runs目录下了
-[] 把idea_prisma做成一个skill

research-ideation的输出为