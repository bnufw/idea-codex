from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


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
class RunArtifact:
    direction_path: str
    papers_dir: str
    selected_paper_ids: list[str]
    manager_plan: dict[str, Any]
    review_history: list[dict[str, Any]]
    experts: list[ExpertRun]
    final_output_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction_path": self.direction_path,
            "papers_dir": self.papers_dir,
            "selected_paper_ids": self.selected_paper_ids,
            "manager_plan": self.manager_plan,
            "review_history": self.review_history,
            "experts": [asdict(item) for item in self.experts],
            "final_output_path": self.final_output_path,
        }
