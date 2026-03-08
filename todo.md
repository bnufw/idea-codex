这是一个想idea的工作流，但是我现在要做如下的改变
1.抛弃掉zotero-mcp搜索论文的，使用用户提供的论文方法(papers目录),papers中的论文格式都是md格式的。
2.需要用户手动提交探究方向，根据用户的输入，可以借鉴已有的论文方法(papers目录)，去想一个更好的，合理的idea
3.想idea的提示词为 prompts/generate_idea.md
4.当idea想出来后，需要上网搜索相关的论文，根据论文的摘要，去判断idea的novelty和feasibility

评审阶段放到明天来做
5.这些都没问题后，进入到评估阶段。调用.env中给好的大模型(Gemini 2.5 pro,gemini-3.1-pro-preview和gemini-3-pro-preview)，去一个一个评审