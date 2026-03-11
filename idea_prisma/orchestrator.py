from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import GEMINI_PRO_THINKING_LEVEL
from .files import (
    append_jsonl,
    ensure_markdown_file,
    load_generate_prompt,
    make_run_dir,
    read_text,
    scan_paper_notes,
    write_json,
    write_text,
)
from .gemini_rest import GeminiRestClient
from .models import ExpertRun, ExpertSpec, ReviewDecision, RunArtifact
from .prompts import MANAGER_SYSTEM_PROMPT, REVIEW_SYSTEM_PROMPT, build_expert_system_prompt


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


class IdeaPrismaOrchestrator:
    def __init__(self, client: GeminiRestClient):
        self.client = client

    def run(
        self,
        direction_md: str,
        papers_dir: str,
        *,
        output_dir: str = "runs",
        max_rounds: int = 2,
    ) -> Path:
        direction_path = ensure_markdown_file(direction_md, "direction_md")
        paper_notes = scan_paper_notes(papers_dir)
        if not paper_notes:
            raise ValueError("papers_dir 下没有找到任何 Markdown 论文笔记。")

        run_dir = make_run_dir(output_dir)
        trace_path = run_dir / "run_trace.jsonl"
        self._trace(trace_path, "run_started", direction_path=str(direction_path), papers_dir=papers_dir)

        direction_text = read_text(direction_path)
        manager_plan = self._safe_execute_manager(direction_text, paper_notes, trace_path)
        write_json(run_dir / "manager_plan.json", manager_plan)

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
        write_json(run_dir / "selected_papers.json", selected_payload)
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
        review_history: list[dict[str, Any]] = []

        round_index = 1
        while round_index < max_rounds and len(expert_runs) > 1:
            review = self._safe_execute_review(direction_text, selected_notes, expert_runs, trace_path)
            review_history.append(
                {
                    "round_index": round_index,
                    "satisfied": review.satisfied,
                    "critique": review.critique,
                    "next_round_strategy": review.next_round_strategy,
                    "refined_experts": [asdict(item) for item in review.refined_experts],
                }
            )
            self._trace(
                trace_path,
                "review_completed",
                round_index=round_index,
                satisfied=review.satisfied,
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

        final_prompt = load_generate_prompt()
        final_text = self._execute_synthesis(direction_text, selected_notes, expert_runs, final_prompt, trace_path)
        final_output_path = run_dir / "final_idea.md"
        write_text(final_output_path, final_text + "\n")
        write_json(run_dir / "experts.json", [asdict(item) for item in expert_runs])

        artifact = RunArtifact(
            direction_path=str(direction_path),
            papers_dir=papers_dir,
            selected_paper_ids=[item.paper_id for item in selected_notes],
            manager_plan=manager_plan,
            review_history=review_history,
            experts=expert_runs,
            final_output_path=str(final_output_path),
        )
        write_json(run_dir / "run_artifact.json", artifact.to_dict())
        self._trace(trace_path, "run_completed", output_path=str(final_output_path))
        return run_dir

    def _safe_execute_manager(self, direction_text: str, paper_notes: list[Any], trace_path: Path) -> dict[str, Any]:
        try:
            return self._execute_manager(direction_text, paper_notes)
        except Exception as exc:
            self._trace(trace_path, "manager_failed", error=str(exc))
            return {
                "thought_process": f"Manager failed. Fallback to primary expert only. Error: {exc}",
                "selected_papers": [],
                "experts": [],
            }

    def _execute_manager(self, direction_text: str, paper_notes: list[Any]) -> dict[str, Any]:
        catalog = []
        for note in paper_notes:
            catalog.append(
                {
                    "paper_id": note.paper_id,
                    "title": note.title,
                    "preview": note.preview,
                }
            )
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
            thinking_level=GEMINI_PRO_THINKING_LEVEL,
        )

    def _select_papers(self, manager_plan: dict[str, Any], paper_notes: list[Any]) -> list[Any]:
        by_id = {note.paper_id: note for note in paper_notes}
        selected_ids = []
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
        selected_notes: list[Any],
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
                thinking_level=GEMINI_PRO_THINKING_LEVEL,
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
        selected_notes: list[Any],
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
        selected_notes: list[Any],
        expert_runs: list[ExpertRun],
    ) -> ReviewDecision:
        expert_payload = [asdict(item) for item in expert_runs]
        user_text = (
            f"Direction:\n{direction_text.strip()}\n\n"
            f"Selected Local Paper Notes:\n{self._selected_notes_text(selected_notes)}\n\n"
            "Current Expert Outputs:\n"
            f"{json.dumps(expert_payload, ensure_ascii=False, indent=2)}"
        )
        payload = self.client.generate_json(
            user_text=user_text,
            system_instruction=REVIEW_SYSTEM_PROMPT,
            response_schema=REVIEW_SCHEMA,
            thinking_level=GEMINI_PRO_THINKING_LEVEL,
        )
        refined = [
            ExpertSpec(
                role=item["role"],
                description=item["description"],
                prompt=item["prompt"],
                temperature=float(item["temperature"]),
            )
            for item in payload.get("refined_experts", [])
        ]
        return ReviewDecision(
            satisfied=bool(payload["satisfied"]),
            critique=payload.get("critique", ""),
            next_round_strategy=payload.get("next_round_strategy", ""),
            refined_experts=refined,
        )

    def _execute_synthesis(
        self,
        direction_text: str,
        selected_notes: list[Any],
        expert_runs: list[ExpertRun],
        final_system_prompt: str,
        trace_path: Path,
    ) -> str:
        self._trace(trace_path, "synthesis_started")
        expert_payload = [asdict(item) for item in expert_runs]
        user_text = (
            "Direction Brief:\n"
            f"{direction_text.strip()}\n\n"
            "Relevant Local Paper Notes:\n"
            f"{self._selected_notes_text(selected_notes)}\n\n"
            "Expert Analyses:\n"
            f"{json.dumps(expert_payload, ensure_ascii=False, indent=2)}\n\n"
            "Use only these materials. If local evidence is insufficient for strong novelty claims, downgrade the wording explicitly."
        )
        buffer: list[str] = []

        def on_chunk(text: str) -> None:
            buffer.append(text)
            sys.stdout.write(text)
            sys.stdout.flush()

        text = self.client.stream_text(
            user_text=user_text,
            system_instruction=final_system_prompt,
            thinking_level=GEMINI_PRO_THINKING_LEVEL,
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
    def _selected_notes_text(selected_notes: list[Any]) -> str:
        blocks = []
        for note in selected_notes:
            blocks.append(
                f"[Paper ID] {note.paper_id}\n[Title] {note.title}\n[Content]\n{note.content}"
            )
        return "\n\n".join(blocks)

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
