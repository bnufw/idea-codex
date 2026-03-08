---
name: Research Ideation
description: Use when the user wants to brainstorm research ideas, identify gaps, define a research question, or plan an early-stage project from a user-provided Markdown brief and local paper notes in `papers/**/*.md`.
version: 0.2.0
---

# Research Ideation

This skill supports the early ideation workflow using only:
- a user-provided Markdown brief
- local paper notes in `papers/**/*.md`

It does not use Zotero or online paper search during the default ideation stage.

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
- known pain points or hypotheses
- optional target venue, dataset, metric, or engineering preference

### 2. Local papers

Use `papers/**/*.md` as the only paper source for this skill.

Rules:
- read only the subset relevant to the user brief
- do not invent details missing from the notes
- if the local notes are weak, explicitly downgrade confidence

## Workflow

1. Read the user brief first.
   - Extract problem, constraints, assumptions, non-goals, and what counts as a better idea.

2. Build a local paper map.
   - Find the relevant files in `papers/**/*.md`.
   - Extract method family, core mechanism, assumptions, strengths, limitations, and reusable patterns.

3. Compare the brief against the local paper map.
   - Identify what is already covered.
   - Identify what is missing, contradictory, weakly evaluated, or overly narrow.

4. Produce a grounded gap view.
   - Distinguish real capability gaps from narrative or packaging gaps.
   - Call out where the evidence is strong and where it is incomplete.

5. Form one or more testable candidate questions.
   - Keep the question tied to a concrete task, comparison target, metric, and failure condition.

6. Draft a minimal validation plan.
   - State what evidence would justify implementation.
   - State what would falsify the idea early.

## Agent Use

- Use `paper-miner` when the local paper set is large and heterogeneous.
- Use `literature-reviewer` when the job is to synthesize and contrast many local paper notes.
- Do not switch to online search unless the parent task explicitly says the workflow has moved into a separate post-idea verification stage.

## Source Rules

- Base every core judgment on the user brief or `papers/**/*.md`.
- Treat local paper notes as the evidence layer for this skill.
- If a claim cannot be supported by the local notes, say so directly.
- Do not turn missing evidence into a confident novelty claim.

## Output Rules

- Respond in Chinese.
- Keep the answer summary-first.
- Make reused patterns and changed assumptions explicit.
- State uncertainty and missing evidence explicitly.
- Prefer outputs such as gap lists, candidate questions, risk tables, and minimal validation plans.

## Failure Handling

- Missing user brief: ask for a valid Markdown path.
- Empty `papers/`: say that local paper grounding is unavailable and stop or downgrade confidence.
- Irrelevant local notes: say that the current corpus does not support the requested direction well.
- Weak novelty evidence: avoid claims such as `first`, `novel`, or `state of the art`.
