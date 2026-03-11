---
name: research-ideation
description: Use when the user wants to brainstorm research ideas, identify gaps, define a research question, or plan an early-stage project from a user-provided Markdown brief, local paper notes in `papers/**/*.md`, and optional online paper search when local evidence is insufficient.
---

# Research Ideation

This skill supports an early ideation workflow that is local-first but can widen its evidence base when needed.

Primary inputs:
- a user-provided Markdown brief
- local paper notes in `papers/**/*.md`

Optional augmentation:
- online paper search when the local corpus is sparse, stale, clearly incomplete, or the user explicitly asks for broader adjacent work

Prefer Exa MCP paper search for online expansion. Use general web search only as fallback.

## When to Use

Use this skill when the user wants to:
- brainstorm or refine a research idea
- understand a local paper set before proposing a question
- identify gaps from existing local paper notes
- turn a vague direction into a testable research question
- produce a research plan or minimal validation sketch

## Required Inputs

### 1. User brief

The user should provide a Markdown file describing as much of the following as possible:
- topic or problem statement
- target task or scenario
- hard constraints and non-goals
- what would count as a better idea
- known pain points or hypotheses
- optional target venue, dataset, metric, or engineering preference

### 2. Local papers

Use `papers/**/*.md` as the default durable paper source for this skill.

Rules:
- read only the subset relevant to the user brief
- do not invent details missing from the notes
- if the local notes are weak, explicitly downgrade confidence

### 3. Optional online paper search

Use online paper search when one or more of the following are true:
- the user explicitly asks to search for papers online
- the local paper set is too small to bound novelty risk
- the local notes appear outdated relative to a fast-moving topic
- the local notes mention adjacent work but not the closest current neighbors

Rules:
- prefer Exa MCP for paper discovery
- use online search to widen the candidate set, not to fabricate deep reading
- label whether a claim comes from local notes, online abstracts, or fuller paper evidence

## Workflow

1. Read the user brief first.
   - Extract problem, constraints, assumptions, non-goals, and what would count as a better idea.

2. Clarify blocking gaps before reading papers when needed.
   - If the brief is missing any of these fields in a way that would change the ideation result, use `request_user_input` before continuing:
     - target task or scenario
     - hard constraints
     - non-goals
     - what would count as a better idea
   - Ask one batched clarification round only.
   - Ask only the 1 to 3 highest-leverage questions.
   - Treat the user's answers as an in-session supplement to the brief.
   - Do not require the user to rewrite the Markdown file before continuing.

3. Build a local paper map.
   - Find the relevant files in `papers/**/*.md`.
   - Extract method family, core mechanism, assumptions, strengths, limitations, and reusable patterns.

4. Expand the paper map online when needed.
   - Search for recent or adjacent papers with Exa MCP.
   - Use titles, abstracts, venues, and dates to identify the strongest nearest neighbors.
   - Keep evidence tiered: online discovery is not the same as full-paper verification.

5. Compare the brief against the grounded paper map.
   - Identify what is already covered.
   - Identify what is missing, contradictory, weakly evaluated, or overly narrow.

6. Produce a grounded gap view.
   - Distinguish real capability gaps from narrative or packaging gaps.
   - Call out where the evidence is strong and where it is incomplete.
   - Separate local-note evidence from online-search evidence.

7. Form one or more testable candidate questions.
   - Keep the question tied to a concrete task, comparison target, metric, and failure condition.

8. Draft a minimal validation plan.
   - State what evidence would justify implementation.
   - State what would falsify the idea early.

## Agent Use

- Use `paper-miner` when the local paper set is large and heterogeneous.
- Use `literature-reviewer` when the job is to synthesize and contrast many local paper notes.
- Use online paper search when the user asks for broader coverage or when the local corpus is too weak to bound the problem responsibly.

## Source Rules

- Base every core judgment on the user brief, local paper notes, and online paper search results when used.
- Treat local paper notes as the strongest reusable evidence layer inside this repo.
- Treat online paper search as a widening layer unless the paper has been read deeply enough to support stronger claims.
- If a claim cannot be supported by the local notes, say so directly.
- If a claim is supported only by online search snippets or abstracts, say so directly.
- Do not turn missing evidence into a confident novelty claim.

## Output Rules

- Respond in Chinese.
- Keep the answer summary-first.
- Make reused patterns and changed assumptions explicit.
- Make clarification-derived assumptions explicit when `request_user_input` was used.
- State uncertainty and missing evidence explicitly.
- Label the evidence source when both local notes and online paper search are used.
- Prefer outputs such as gap lists, candidate questions, risk tables, and minimal validation plans.

## Failure Handling

- Missing user brief: ask for a valid Markdown path.
- Materially underspecified brief: use one batched `request_user_input` round before paper mapping.
- Clarification still unavailable: stop and state which blocking fields are still missing.
- Empty `papers/`: say that local paper grounding is unavailable and switch to online paper search with downgraded confidence, or stop if the user wants local-only grounding.
- Irrelevant local notes: say that the current corpus does not support the requested direction well.
- Online search unavailable: continue with local notes only and clearly mark the literature boundary as incomplete.
- Weak novelty evidence: avoid claims such as `first`, `novel`, or `state of the art`.
