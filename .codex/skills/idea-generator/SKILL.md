---
name: idea-generator
description: Use when the user wants to generate or refine one research idea from a required Markdown brief and local Markdown paper notes stored in `papers/**/*.md`, following `prompts/generate_idea.md`.
version: 0.2.0
---

# Idea Generator

Generate exactly one stronger and more defensible research idea by combining:
- a required user-authored Markdown brief provided through `input_md_path`
- local paper notes stored as Markdown files under `papers/**/*.md`
- the authoritative generation template in `prompts/generate_idea.md`

## When to Use

Use this skill when:
- the user already has a research direction, problem statement, or constraint set written in Markdown
- the repository contains local paper notes in `papers/**/*.md`
- the goal is to propose one better idea grounded in those paper methods instead of doing open-ended brainstorming

## Required Inputs

### `input_md_path` (required)

The caller must provide a workspace-relative or absolute path to a user-authored `.md` file.

The file should contain as many of the following as possible:
- research direction or problem statement
- target scenario or task setting
- hard constraints and non-goals
- observed pain points or hypotheses
- optional target venue, dataset, metric, or implementation preference

### `papers/**/*.md` (required local paper source)

Use local Markdown paper notes as the only paper source for this skill.

Rules:
- read only the relevant subset
- do not invent missing details
- if the corpus is weak or empty, say so explicitly

### `prompts/generate_idea.md` (authoritative template)

Always read `prompts/generate_idea.md` before producing the final answer.

Treat it as the authoritative prompt for:
- reasoning order
- output structure
- idea quality bar

## Workflow

1. Validate `input_md_path`.
   - Confirm the file exists and is Markdown.
   - If it is missing or unreadable, stop and ask the user for a valid path.

2. Read the user brief first.
   - Extract the problem, scenario, constraints, assumptions, non-goals, and what “better” should mean.

3. Scan `papers/**/*.md`.
   - Find the smallest relevant subset.
   - Extract method family, mechanism, assumptions, strengths, limitations, and reusable design patterns.

4. Identify the improvement opportunity.
   - Compare the brief against the local paper map.
   - Pin down what should be reused, what should change, and what contradiction or failure mode the new idea should resolve.

5. Use `paper-miner` only when helpful.
   - Invoke it if the local notes are numerous, heterogeneous, or weakly structured.
   - Otherwise complete the task locally.

6. Load `prompts/generate_idea.md`.
   - Follow its workflow and output structure exactly.

7. Produce exactly one coherent idea.
   - Prefer conceptual unity over module stacking.
   - Prefer the minimal number of tightly coupled contributions.
   - Make clear what is reused, what is changed, and why the result is more reasonable than the source methods.

## Source Rules

- Base every core judgment on `input_md_path` and relevant `papers/**/*.md`.
- Treat local paper notes as grounded evidence for ideation.
- Do not claim a paper supports something unless that support appears in the local note.
- Do not fall back to online search inside this skill.

## Output Rules

- Respond in Chinese.
- Follow the structure required by `prompts/generate_idea.md`.
- Keep assumptions and uncertainty inside the required sections.
- State integration scope, likely compute or data cost, and key assumptions explicitly.

## Failure Handling

- Missing `input_md_path`: ask the user for a valid Markdown path.
- Empty or irrelevant `papers/**/*.md`: say that local paper grounding is unavailable, then stop or proceed with reduced confidence.
- Conflicting paper notes: surface the conflict before committing to the idea.
- Weak novelty evidence: avoid strong claims such as `first`, `novel`, or `state of the art`.
