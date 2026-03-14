---
name: idea-prisma
description: Use when the user wants a Prisma-style dual-branch idea workflow that takes a required Markdown brief plus local paper notes, runs one Codex-native branch and one Gemini branch, then compares both outputs and selects a winner.
version: 0.1.0
---

# idea-prisma

Run a Prisma-style idea workflow with two required branches:
- a Codex-native branch driven by this skill
- a Gemini branch driven by the skill-local runner in `scripts/run_gemini_prisma.py`

Do not reduce this skill to a thin wrapper over the repo-root `idea_prisma/` package.
This skill is the primary workflow definition. The repo-root CLI is only a legacy manual path.

## When to Use

Use this skill when the user wants to:
- turn one direction brief into one full idea package with Prisma-style staging
- keep both a Codex-native result and a Gemini result for comparison
- audit intermediate planning, paper selection, expert outputs, and final winner selection

## Required Inputs

### `input_md_path` (required)

The caller must provide a workspace-relative or absolute Markdown file describing the research direction.

Minimum expected content:
- problem or topic
- target scenario or task
- hard constraints and non-goals
- optional hypotheses, baselines, datasets, or reviewer concerns

If the brief is materially ambiguous and would change expert decomposition or the evaluation focus, use `request_user_input` before running the workflow.

### `papers_dir` (optional, default `papers`)

Use local Markdown paper notes under `papers/**/*.md` as the default evidence source.

Rules:
- read the smallest relevant subset first
- do not invent missing paper details
- treat selected papers as nearest-neighbor evidence, not templates to copy; the final idea must not just restate a selected paper method with renamed terms
- if the corpus is empty or clearly irrelevant, stop instead of pretending the workflow is grounded

### `output_dir` (optional, default `runs`)

All workflow artifacts must be written under `runs/<timestamp>/`.

### `max_rounds` (optional, default `2`)

Maximum total expert rounds for each branch. Stop earlier when the review stage is satisfied.

## Output Contract

Create one timestamped run directory:

```text
runs/<timestamp>/
├── codex/
│   ├── manager_plan.json
│   ├── selected_papers.json
│   ├── experts.json
│   ├── final_idea.md
│   └── run_trace.md
├── gemini/
│   ├── manager_plan.json
│   ├── selected_papers.json
│   ├── experts.json
│   ├── final_idea.md
│   └── run_trace.jsonl
├── evaluation.md
├── final_selected.md
└── run_manifest.json
```

Keep the branch schemas aligned:
- `manager_plan.json`: `thought_process`, `selected_papers`, `experts`
- `selected_papers.json`: array of `{paper_id, title, path, content}`
- `experts.json`: array of `{role, description, prompt, temperature, round_index, output, status}`

`final_selected.md` must be a direct copy of the winning branch output. Do not merge or rewrite the winner at selection time.

`run_manifest.json` should at least record:
- `input_md_path`
- `papers_dir`
- `max_rounds`
- `codex_final_path`
- `gemini_final_path`
- `evaluation_path`
- `winner`
- `winner_source`

## Workflow

### 1. Preflight

1. Validate `input_md_path`.
2. Validate `papers_dir`.
3. If the brief is underspecified in a way that changes branch behavior, clarify with `request_user_input`.
4. Create `runs/<timestamp>/`, then create `codex/` and `gemini/`.

Do not silently downgrade to a single-branch run.

### 2. Codex Branch

The Codex branch is executed by following this skill directly.

#### 2.1 Manager

Read the brief first, then build a local paper catalog from the smallest relevant subset of `papers/**/*.md`.

Write `codex/manager_plan.json` with:
- `thought_process`: short planning rationale
- `selected_papers`: paper ids plus reasons
- `experts`: 2 to 4 supplementary experts with `role`, `description`, `prompt`, `temperature`

Always add one primary expert even if the manager proposes none.

#### 2.2 Experts

Run experts against:
- the direction brief
- the selected local paper notes
- the manager-defined task prompt

Use child agents for focused expert subtasks when they materially improve separation of concerns.
If the user explicitly asks to use child agents, the Codex branch must delegate at least one suitable expert subtask instead of keeping the whole branch local.
Do not spawn agents for the whole workflow.

Child-agent routing rules:
- prefer a preconfigured specialist agent when one is a clear fit for the current expert objective
- if no existing specialist is a good fit, create a task-specific child agent with a narrow role and prompt derived from the expert objective
- keep manager, review, synthesis, and winner selection in the parent agent so the final decision boundary stays in one place
- record each delegated subtask in `codex/run_trace.md`, including the delegated expert role, why delegation was used, and whether the child agent was preconfigured or task-specific

Write every expert result into `codex/experts.json`.

#### 2.3 Review

Run a review step after the first expert round.

Stop when either condition holds:
- the branch is already sufficient to synthesize one coherent idea
- no useful refined experts remain

Otherwise run one more expert round, then stop at `max_rounds`.

Append a concise human-readable stage log to `codex/run_trace.md`.

#### 2.4 Synthesis

Synthesize exactly one final idea in Chinese from:
- the brief
- the selected paper notes
- the expert outputs

The final answer must stay grounded in local notes. If novelty support is weak, downgrade the wording explicitly.
Write the Codex `final_idea.md` in direct, readable Chinese: prefer explicit problem, closest overlap, concrete delta, and minimal validation over dense jargon or unexplained notation.

Write the result to `codex/final_idea.md`.

### 3. Gemini Branch

Run the skill-local Gemini runner:

```bash
python .codex/skills/idea-prisma/scripts/run_gemini_prisma.py \
  --direction-md <input_md_path> \
  --papers-dir <papers_dir> \
  --run-dir <runs/timestamp> \
  --max-rounds <max_rounds>
```

Rules:
- the script must stay independent from repo-root `idea_prisma/`
- it may read `.env` or environment variables for Gemini settings
- it must write only the `gemini/` branch artifacts listed above

Required Gemini environment:
- `GEMINI_API_KEY`
- optional `GEMINI_BASE_URL`
- optional `GEMINI_MODEL_NAME`

If Gemini configuration is missing or the call fails, stop the workflow and surface the error. Do not silently continue with only the Codex branch.

### 4. Evaluation and Winner Selection

After both branches finish, compare `codex/final_idea.md` and `gemini/final_idea.md`.

Write `evaluation.md` in Chinese with these fixed dimensions:
1. brief alignment
2. grounding to local papers
3. conceptual unity
4. novelty-risk discipline
5. feasibility and minimal validation
6. clarity and reviewer defensibility

The evaluation must contain:
- one short summary paragraph
- side-by-side comparison on all six dimensions
- the chosen winner
- the main reason the losing branch was not selected

Then copy the winner verbatim into `final_selected.md`.

### 5. Failure Rules

- Missing or unreadable `input_md_path`: stop and ask for a valid Markdown file.
- Empty `papers_dir`: stop and say local grounding is unavailable.
- Gemini branch failure: stop; do not auto-degrade to Codex-only mode.
- Weak novelty evidence: avoid `first`, `novel`, or `state of the art`.

## Source Rules

- The default evidence base is the user brief plus local `papers/**/*.md`.
- Use only the relevant local subset; do not bulk-load the entire corpus unless necessary.
- If the user explicitly asks for broader adjacent work, use `research-ideation` or direct online search outside this skill, then return with clearer evidence labels.

## Notes on the Legacy CLI

The repo-root `idea_prisma/` package remains available for manual or historical use, but this skill must not depend on it internally.
