from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib import error, parse, request


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL_NAME = "gemini-3-pro-preview"
GEMINI_PRO_THINKING_LEVEL = "high"

MANAGER_SCHEMA = {
    "type": "object",
    "properties": {
        "thought_process": {"type": "string"},
        "selected_papers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "paper_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["paper_id", "reason"],
            },
        },
        "experts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "description": {"type": "string"},
                    "prompt": {"type": "string"},
                    "temperature": {"type": "number"},
                },
                "required": ["role", "description", "prompt", "temperature"],
            },
        },
    },
    "required": ["thought_process", "selected_papers", "experts"],
}

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "satisfied": {"type": "boolean"},
        "critique": {"type": "string"},
        "next_round_strategy": {"type": "string"},
        "refined_experts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "description": {"type": "string"},
                    "prompt": {"type": "string"},
                    "temperature": {"type": "number"},
                },
                "required": ["role", "description", "prompt", "temperature"],
            },
        },
    },
    "required": ["satisfied", "critique", "next_round_strategy", "refined_experts"],
}

MANAGER_SYSTEM_PROMPT = """
You are the Dynamic Planning Engine for a research-idea generation workflow.
Your job is to read the user's research direction and a catalog of local paper notes, then:
1. pick the smallest relevant subset of papers,
2. explain the planning logic briefly,
3. create 2 to 4 supplementary experts.

Rules:
- Use only the provided direction brief and local paper notes.
- Do not fabricate papers, claims, baselines, or novelty.
- Experts must be tightly coupled to producing one defensible oral-level research idea.
- Prefer experts that cover mechanism design, failure analysis, and evaluation defensibility.
""".strip()

REVIEW_SYSTEM_PROMPT = """
You are the Quality Assurance and Orchestration Engine.
You have the research direction, selected local paper notes, and current expert outputs.
Decide whether the expert set is sufficient to synthesize one strong and defensible idea.

Set satisfied=false when any of these holds:
- the idea is still vague or split into unrelated add-ons,
- the train-time and inference-time coupling is not concrete,
- key nearest-neighbor methods are not addressed,
- the output would be easy for reviewers to dismiss as repackaging.

If satisfied=false:
- provide a concrete critique,
- provide a short next_round_strategy,
- create refined experts whose prompts already include the critique.
""".strip()

FINAL_SYSTEM_PROMPT = """
# Role: World-Class AI Research Scientist

You are a distinguished research scholar who has published multiple Oral papers as the first author at top-tier conferences in Computer Vision (CVPR), Machine Learning (ICML), and Representation Learning (ICLR). You possess the following core capabilities:

1. Rapid Learning and Insight: You can quickly digest core papers in a new field and accurately identify key challenges, mainstream paradigms, and research gaps that have not yet been fully explored.
2. First-Principles Thinking: You excel at starting from observed profound phenomena and returning to the essence of the problem, rather than making minor improvements within the framework of existing methods.
3. Systematic Innovation: The methodology you conceive possesses a high degree of internal unity. The contributions you propose are interconnected and mutually supportive, jointly serving a core idea, rather than being a simple stacking of modules.
4. Emphasis on Both Theory and Practice: Your ideas are not only highly innovative but also grounded in solid theory. They also have strong versatility and plug-and-play potential, allowing easy integration across scenarios.

---

# Core Task

Given the paper summaries about a specific research field provided by the user, conceive a highly innovative, simple, direct, and impressive research idea that targets solving the identified core problem(s). The idea should meet the standards of a top-tier conference Oral paper.

Important principle: Optimize for problem-solving completeness and conceptual elegance, not for a fixed number of innovation points.

---

**Highest Priority Instruction**: The following Workflow is ironclad and must be followed strictly in sequential order, step by step, without any skipping or simplification. Any deviation is considered a serious error.

# Workflow and Thinking Framework

Strictly follow the steps below:

1. Deep Analysis and Phenomenon Extraction

   * Carefully read and understand the paper summaries provided by the user.
   * Identify common problems, bottlenecks, hidden assumptions, or overlooked phenomena in existing methods.
   * Key step: Extract the most core, profound, and thought-provoking Observed Phenomenon. This phenomenon should be counter-intuitive or reveal a deep contradiction in existing paradigms. State it clearly and precisely.

2. Motivation and Core Idea Construction

   * Based on the observed phenomenon, explain why existing methods fail fundamentally (not just empirically), establishing a strong Motivation.
   * Propose a Core Idea that addresses the phenomenon directly and elegantly. This idea is the master plan for all subsequent designs.

3. Methodology Design

   * Contributions are NOT required to be a fixed count:

     * Design the minimal set of contributions necessary to fully solve the problem and make the idea defensible as an Oral-level paper.
     * **Prefer no more than 3 core methodological innovations; avoid extra, loosely-related add-ons.**
   * Coupling and synergy constraint:

     * If you propose multiple contributions, they must be strongly coupled and synergistic, not independent add-ons.
     * Explicitly state how each contribution depends on or enables the others, and why the full solution is incomplete if any is removed.
     * If you propose only one major contribution, explain its internal structure (subcomponents, principles, or mechanisms) and why it forms a complete, indivisible solution.
   * Detailed elaboration:

     * Provide an extremely detailed description for each contribution, using natural Chinese prose with clear causal logic.
     * Integrate mathematical notation, objective functions, and key constraints directly into the problem analysis and method description when helpful; do not isolate them as a detached math-only section.
     * Clearly specify what is novel, what is assumed, and what is derived.
   * Generalizability design:

     * Ensure plug-and-play compatibility. Explain precisely how the method integrates into common existing frameworks and what changes are required.
   * **Hyperparameter discipline:** keep the total number of new method-specific hyperparameters around two (and justify them); avoid introducing additional tuning knobs.

---

# Output Structure (Mandatory)

You **must** strictly follow the following format for your output. Do not add any preface, greetings, explanations, or closing remarks. Start directly with ## 1. Motivation.

<output>
## 1. Motivation

* Observed Phenomenon: [Clearly describe the core phenomenon extracted from the input materials.]
* Limitations of Existing Methods: [Analyze why current paradigms have fundamental issues under this phenomenon.]
* Our Core Idea: [State the core idea concisely and powerfully.]

## 2. Methodology

### 2.1. Overall Framework

* [Describe the full pipeline and data/gradient flow at a high level. If useful, include a compact textual flowchart.]

### 2.2. Contributions

* Provide a numbered list of contributions. The count is flexible and should match what is necessary to solve the problem.
* For each Contribution k, include:

  * Name: [Short technical name]
  * Objective: [What specific failure mode or requirement it addresses]
  * Detailed Approach: [Precise method description with equations, algorithm steps, pseudocode, and implementation details]
  * Why it is necessary: [What breaks without it]

### 2.3. Synergy and Indivisibility

* If there are multiple contributions:
  * Explain the dependency graph among them (which enables which, which introduces side effects, which resolves them).
  * Argue why the combined system achieves something none of the parts can achieve alone.
* If there is a single contribution:
  * Explain the internal coupling among its subcomponents and why it should be treated as one coherent mechanism rather than separable tricks.

### 2.4. Plug-and-Play Integration and Scope

* [Explain how to integrate the method into standard architectures/training recipes, what interfaces/modules change, and what remains unchanged.]
* [State expected computational and data requirements, and any constraints/assumptions.]
</output>

Start analyzing the paper summaries provided by the user now. Respond in Chinese.
""".strip()


class GeminiError(RuntimeError):
    pass


@dataclass(slots=True)
class Settings:
    api_key: str
    base_url: str
    model_name: str
    request_timeout: int = 180


@dataclass(slots=True)
class PaperNote:
    paper_id: str
    path: str
    title: str
    content: str
    preview: str


@dataclass(slots=True)
class ExpertSpec:
    role: str
    description: str
    prompt: str
    temperature: float


@dataclass(slots=True)
class ExpertRun:
    role: str
    description: str
    prompt: str
    temperature: float
    round_index: int
    output: str = ""
    status: str = "pending"


@dataclass(slots=True)
class ReviewDecision:
    satisfied: bool
    critique: str
    next_round_strategy: str = ""
    refined_experts: list[ExpertSpec] = field(default_factory=list)


@dataclass(slots=True)
class GenerateResult:
    text: str
    raw: dict[str, Any]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_gemini_prisma",
        description="Run the skill-local Gemini branch for idea-prisma.",
    )
    parser.add_argument("--direction-md", required=True, help="Markdown brief for the current direction.")
    parser.add_argument("--papers-dir", default="papers", help="Directory of local Markdown paper notes.")
    parser.add_argument(
        "--run-dir",
        default=None,
        help="Existing or new run root. If omitted, create runs/<timestamp>/ and write the gemini branch there.",
    )
    parser.add_argument("--max-rounds", type=int, default=2, help="Maximum total expert rounds.")
    return parser


def repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def ensure_markdown_file(path: str | Path, label: str) -> Path:
    candidate = repo_path(path)
    if not candidate.exists() or not candidate.is_file() or candidate.suffix.lower() != ".md":
        raise ValueError(f"{label} must be an existing Markdown file: {candidate}")
    return candidate


def ensure_directory(path: str | Path, label: str) -> Path:
    candidate = repo_path(path)
    if not candidate.exists() or not candidate.is_dir():
        raise ValueError(f"{label} must be an existing directory: {candidate}")
    return candidate


def extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def compact_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_preview(content: str, limit: int = 1200) -> str:
    normalized = compact_markdown(content)
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit].rstrip() + "\n..."


def scan_paper_notes(papers_dir: str | Path) -> list[PaperNote]:
    root = ensure_directory(papers_dir, "papers_dir")
    notes: list[PaperNote] = []
    for path in sorted(root.rglob("*.md")):
        content = read_text(path)
        rel_path = path.relative_to(root).as_posix()
        notes.append(
            PaperNote(
                paper_id=rel_path,
                path=str(path),
                title=extract_title(content, path.stem),
                content=compact_markdown(content),
                preview=build_preview(content),
            )
        )
    return notes


def make_branch_dir(run_dir: str | Path | None) -> Path:
    if run_dir is None:
        run_root = REPO_ROOT / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S")
    else:
        run_root = repo_path(run_dir)
    run_root.mkdir(parents=True, exist_ok=True)
    branch_dir = run_root / "gemini"
    branch_dir.mkdir(parents=True, exist_ok=False)
    return branch_dir


def _default_json(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Unsupported JSON value: {type(value)!r}")


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_default_json) + "\n",
        encoding="utf-8",
    )


def write_text(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def append_jsonl(path: str | Path, payload: dict[str, Any]) -> None:
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, default=_default_json) + "\n")


def _load_dotenv(dotenv_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not dotenv_path.exists():
        return values
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_settings(dotenv_path: str | Path = ".env") -> Settings:
    dotenv_values = _load_dotenv(repo_path(dotenv_path))

    def pick(name: str, default: str = "") -> str:
        return os.environ.get(name) or dotenv_values.get(name, default)

    api_key = pick("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY. Configure it in .env or the environment.")
    return Settings(
        api_key=api_key,
        base_url=pick("GEMINI_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        model_name=pick("GEMINI_MODEL_NAME", DEFAULT_MODEL_NAME),
    )


def build_expert_system_prompt(role: str, description: str) -> str:
    return (
        f"You are {role}. {description} "
        "Use only the provided direction and local paper notes. "
        "Answer in Chinese. Be concrete, avoid fake citations, and focus on one coherent idea."
    )


def _extract_text(payload: dict[str, Any]) -> str:
    texts: list[str] = []
    for candidate in payload.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                texts.append(text)
    return "".join(texts).strip()


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


class GeminiRestClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _build_url(self, method: str, *, stream: bool = False) -> str:
        endpoint = f"{self.settings.base_url}/models/{self.settings.model_name}:{method}"
        query = {"key": self.settings.api_key}
        if stream:
            query["alt"] = "sse"
        return f"{endpoint}?{parse.urlencode(query)}"

    def _request(self, method: str, payload: dict[str, Any], *, stream: bool = False) -> Any:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self._build_url(method, stream=stream),
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            return request.urlopen(req, timeout=self.settings.request_timeout)
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="ignore")
            raise GeminiError(f"Gemini API request failed: HTTP {exc.code} - {message}") from exc
        except error.URLError as exc:
            raise GeminiError(f"Gemini API request failed: {exc.reason}") from exc

    def _build_payload(
        self,
        user_text: str,
        system_instruction: str | None = None,
        *,
        temperature: float | None = None,
        response_schema: dict[str, Any] | None = None,
        thinking_level: str | None = None,
    ) -> dict[str, Any]:
        generation_config: dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if response_schema is not None:
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseJsonSchema"] = response_schema
        if thinking_level is not None:
            generation_config["thinkingConfig"] = {"thinkingLevel": thinking_level}
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        }
        if generation_config:
            payload["generationConfig"] = generation_config
        if system_instruction:
            payload["system_instruction"] = {"parts": [{"text": system_instruction}]}
        return payload

    def generate_text(
        self,
        user_text: str,
        system_instruction: str | None = None,
        *,
        temperature: float | None = None,
        thinking_level: str = GEMINI_PRO_THINKING_LEVEL,
    ) -> GenerateResult:
        payload = self._build_payload(
            user_text,
            system_instruction,
            temperature=temperature,
            thinking_level=thinking_level,
        )
        with self._request("generateContent", payload) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return GenerateResult(text=_extract_text(raw), raw=raw)

    def generate_json(
        self,
        user_text: str,
        system_instruction: str,
        response_schema: dict[str, Any],
        *,
        temperature: float | None = None,
        thinking_level: str = GEMINI_PRO_THINKING_LEVEL,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            user_text,
            system_instruction,
            temperature=temperature,
            response_schema=response_schema,
            thinking_level=thinking_level,
        )
        with self._request("generateContent", payload) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return json.loads(_clean_json_text(_extract_text(raw)))

    def stream_text(
        self,
        user_text: str,
        system_instruction: str | None = None,
        *,
        temperature: float | None = None,
        thinking_level: str = GEMINI_PRO_THINKING_LEVEL,
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
        payload = self._build_payload(
            user_text,
            system_instruction,
            temperature=temperature,
            thinking_level=thinking_level,
        )
        chunks: list[str] = []
        with self._request("streamGenerateContent", payload, stream=True) as response:
            event_lines: list[str] = []
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="ignore")
                stripped = line.strip()
                if not stripped:
                    if event_lines:
                        text = self._consume_event(event_lines)
                        if text:
                            chunks.append(text)
                            if on_chunk is not None:
                                on_chunk(text)
                        event_lines.clear()
                    continue
                if stripped.startswith("data:"):
                    event_lines.append(stripped[5:].strip())
            if event_lines:
                text = self._consume_event(event_lines)
                if text:
                    chunks.append(text)
                    if on_chunk is not None:
                        on_chunk(text)
        return "".join(chunks).strip()

    @staticmethod
    def _consume_event(lines: Iterable[str]) -> str:
        data = "".join(lines)
        if not data or data == "[DONE]":
            return ""
        return _extract_text(json.loads(data))


class GeminiPrismaRunner:
    def __init__(self, client: GeminiRestClient):
        self.client = client

    def run(
        self,
        direction_md: str,
        papers_dir: str,
        *,
        run_dir: str | Path | None,
        max_rounds: int,
    ) -> Path:
        direction_path = ensure_markdown_file(direction_md, "direction_md")
        paper_notes = scan_paper_notes(papers_dir)
        if not paper_notes:
            raise ValueError("papers_dir does not contain any Markdown paper notes.")

        branch_dir = make_branch_dir(run_dir)
        trace_path = branch_dir / "run_trace.jsonl"
        self._trace(
            trace_path,
            "run_started",
            direction_path=str(direction_path),
            papers_dir=str(ensure_directory(papers_dir, "papers_dir")),
        )

        direction_text = read_text(direction_path)
        manager_plan = self._safe_execute_manager(direction_text, paper_notes, trace_path)
        write_json(branch_dir / "manager_plan.json", manager_plan)

        selected_notes = self._select_papers(manager_plan, paper_notes)
        selected_payload = [
            {
                "paper_id": note.paper_id,
                "title": note.title,
                "path": note.path,
                "content": note.content,
            }
            for note in selected_notes
        ]
        write_json(branch_dir / "selected_papers.json", selected_payload)
        self._trace(
            trace_path,
            "manager_completed",
            selected_paper_ids=[item["paper_id"] for item in selected_payload],
            expert_count=len(manager_plan.get("experts", [])) + 1,
        )

        experts = [self._primary_expert(direction_text)] + [
            ExpertSpec(
                role=item["role"],
                description=item["description"],
                prompt=item["prompt"],
                temperature=float(item["temperature"]),
            )
            for item in manager_plan.get("experts", [])
        ]

        expert_runs = self._run_experts(experts, direction_text, selected_notes, round_index=1, trace_path=trace_path)
        round_index = 1
        while round_index < max_rounds and len(expert_runs) > 1:
            review = self._safe_execute_review(direction_text, selected_notes, expert_runs, trace_path)
            self._trace(
                trace_path,
                "review_completed",
                round_index=round_index,
                satisfied=review.satisfied,
                critique=review.critique,
                refined_expert_count=len(review.refined_experts),
            )
            if review.satisfied or not review.refined_experts:
                break
            round_index += 1
            expert_runs.extend(
                self._run_experts(
                    review.refined_experts,
                    direction_text,
                    selected_notes,
                    round_index=round_index,
                    trace_path=trace_path,
                )
            )

        final_text = self._execute_synthesis(direction_text, selected_notes, expert_runs, trace_path)
        write_text(branch_dir / "final_idea.md", final_text + "\n")
        write_json(branch_dir / "experts.json", [asdict(item) for item in expert_runs])
        self._trace(trace_path, "run_completed", output_path=str(branch_dir / "final_idea.md"))
        return branch_dir

    def _safe_execute_manager(self, direction_text: str, paper_notes: list[PaperNote], trace_path: Path) -> dict[str, Any]:
        try:
            return self._execute_manager(direction_text, paper_notes)
        except Exception as exc:
            self._trace(trace_path, "manager_failed", error=str(exc))
            return {
                "thought_process": f"Manager failed. Fallback to primary expert only. Error: {exc}",
                "selected_papers": [],
                "experts": [],
            }

    def _execute_manager(self, direction_text: str, paper_notes: list[PaperNote]) -> dict[str, Any]:
        catalog = [
            {
                "paper_id": note.paper_id,
                "title": note.title,
                "preview": note.preview,
            }
            for note in paper_notes
        ]
        user_text = (
            "Research Direction:\n"
            f"{direction_text.strip()}\n\n"
            "Local Paper Catalog:\n"
            f"{json.dumps(catalog, ensure_ascii=False, indent=2)}\n\n"
            "Return the smallest relevant paper subset and supplementary experts."
        )
        return self.client.generate_json(
            user_text=user_text,
            system_instruction=MANAGER_SYSTEM_PROMPT,
            response_schema=MANAGER_SCHEMA,
        )

    def _select_papers(self, manager_plan: dict[str, Any], paper_notes: list[PaperNote]) -> list[PaperNote]:
        by_id = {note.paper_id: note for note in paper_notes}
        selected_ids: list[str] = []
        for item in manager_plan.get("selected_papers", []):
            paper_id = item.get("paper_id", "")
            if paper_id in by_id and paper_id not in selected_ids:
                selected_ids.append(paper_id)
        if not selected_ids:
            selected_ids = [note.paper_id for note in paper_notes[: min(4, len(paper_notes))]]
        return [by_id[item] for item in selected_ids[:8]]

    @staticmethod
    def _primary_expert(direction_text: str) -> ExpertSpec:
        return ExpertSpec(
            role="Primary Idea Architect",
            description="Draft the main research idea and keep all parts tightly coupled.",
            prompt=(
                "Directly convert the research direction into one coherent oral-level idea. "
                "Make the train-time and inference-time coupling explicit, and avoid unrelated add-ons.\n\n"
                f"Direction:\n{direction_text.strip()}"
            ),
            temperature=0.9,
        )

    def _run_experts(
        self,
        experts: list[ExpertSpec],
        direction_text: str,
        selected_notes: list[PaperNote],
        *,
        round_index: int,
        trace_path: Path,
    ) -> list[ExpertRun]:
        note_bundle = self._selected_notes_text(selected_notes)
        with ThreadPoolExecutor(max_workers=min(4, len(experts))) as pool:
            futures = [
                pool.submit(self._run_one_expert, spec, direction_text, note_bundle, round_index, trace_path)
                for spec in experts
            ]
            return [future.result() for future in futures]

    def _run_one_expert(
        self,
        spec: ExpertSpec,
        direction_text: str,
        note_bundle: str,
        round_index: int,
        trace_path: Path,
    ) -> ExpertRun:
        self._trace(trace_path, "expert_started", role=spec.role, round_index=round_index)
        user_text = (
            f"Direction:\n{direction_text.strip()}\n\n"
            f"Selected Local Paper Notes:\n{note_bundle}\n\n"
            f"Your Task:\n{spec.prompt.strip()}"
        )
        try:
            result = self.client.generate_text(
                user_text=user_text,
                system_instruction=build_expert_system_prompt(spec.role, spec.description),
                temperature=spec.temperature,
            )
            self._trace(trace_path, "expert_completed", role=spec.role, round_index=round_index)
            return ExpertRun(
                role=spec.role,
                description=spec.description,
                prompt=spec.prompt,
                temperature=spec.temperature,
                round_index=round_index,
                output=result.text,
                status="completed",
            )
        except Exception as exc:
            self._trace(trace_path, "expert_failed", role=spec.role, round_index=round_index, error=str(exc))
            return ExpertRun(
                role=spec.role,
                description=spec.description,
                prompt=spec.prompt,
                temperature=spec.temperature,
                round_index=round_index,
                output=f"Expert failed: {exc}",
                status="error",
            )

    def _safe_execute_review(
        self,
        direction_text: str,
        selected_notes: list[PaperNote],
        expert_runs: list[ExpertRun],
        trace_path: Path,
    ) -> ReviewDecision:
        try:
            return self._execute_review(direction_text, selected_notes, expert_runs)
        except Exception as exc:
            self._trace(trace_path, "review_failed", error=str(exc))
            return ReviewDecision(
                satisfied=True,
                critique=f"Review failed, stop refinement and continue to synthesis. Error: {exc}",
            )

    def _execute_review(
        self,
        direction_text: str,
        selected_notes: list[PaperNote],
        expert_runs: list[ExpertRun],
    ) -> ReviewDecision:
        user_text = (
            f"Direction:\n{direction_text.strip()}\n\n"
            f"Selected Local Paper Notes:\n{self._selected_notes_text(selected_notes)}\n\n"
            "Current Expert Outputs:\n"
            f"{json.dumps([asdict(item) for item in expert_runs], ensure_ascii=False, indent=2)}"
        )
        payload = self.client.generate_json(
            user_text=user_text,
            system_instruction=REVIEW_SYSTEM_PROMPT,
            response_schema=REVIEW_SCHEMA,
        )
        return ReviewDecision(
            satisfied=bool(payload["satisfied"]),
            critique=payload.get("critique", ""),
            next_round_strategy=payload.get("next_round_strategy", ""),
            refined_experts=[
                ExpertSpec(
                    role=item["role"],
                    description=item["description"],
                    prompt=item["prompt"],
                    temperature=float(item["temperature"]),
                )
                for item in payload.get("refined_experts", [])
            ],
        )

    def _execute_synthesis(
        self,
        direction_text: str,
        selected_notes: list[PaperNote],
        expert_runs: list[ExpertRun],
        trace_path: Path,
    ) -> str:
        self._trace(trace_path, "synthesis_started")
        user_text = (
            "Direction Brief:\n"
            f"{direction_text.strip()}\n\n"
            "Relevant Local Paper Notes:\n"
            f"{self._selected_notes_text(selected_notes)}\n\n"
            "Expert Analyses:\n"
            f"{json.dumps([asdict(item) for item in expert_runs], ensure_ascii=False, indent=2)}\n\n"
            "Use only these materials. If local evidence is insufficient for strong novelty claims, downgrade the wording explicitly."
        )
        buffer: list[str] = []

        def on_chunk(text: str) -> None:
            buffer.append(text)
            sys.stdout.write(text)
            sys.stdout.flush()

        text = self.client.stream_text(
            user_text=user_text,
            system_instruction=FINAL_SYSTEM_PROMPT,
            on_chunk=on_chunk,
        )
        if not buffer:
            sys.stdout.write(text)
            sys.stdout.flush()
        if buffer and not text:
            text = "".join(buffer)
        sys.stdout.write("\n")
        self._trace(trace_path, "synthesis_completed")
        return text.strip()

    @staticmethod
    def _selected_notes_text(selected_notes: list[PaperNote]) -> str:
        return "\n\n".join(
            f"[Paper ID] {note.paper_id}\n[Title] {note.title}\n[Content]\n{note.content}"
            for note in selected_notes
        )

    @staticmethod
    def _trace(path: Path, event: str, **payload: Any) -> None:
        append_jsonl(
            path,
            {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "event": event,
                **payload,
            },
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = load_settings()
        runner = GeminiPrismaRunner(GeminiRestClient(settings))
        branch_dir = runner.run(
            direction_md=args.direction_md,
            papers_dir=args.papers_dir,
            run_dir=args.run_dir,
            max_rounds=max(1, args.max_rounds),
        )
    except (ValueError, GeminiError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    parser.exit(0, f"\nGemini branch completed: {branch_dir}\n")


if __name__ == "__main__":
    raise SystemExit(main())
