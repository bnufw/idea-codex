from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import PaperNote


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def ensure_markdown_file(path: str | Path, label: str) -> Path:
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file() or candidate.suffix.lower() != ".md":
        raise ValueError(f"{label} 必须是存在的 Markdown 文件：{candidate}")
    return candidate


def ensure_directory(path: str | Path, label: str) -> Path:
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_dir():
        raise ValueError(f"{label} 必须是存在的目录：{candidate}")
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


def load_generate_prompt(prompt_path: str | Path = "prompts/generate_idea.md") -> str:
    content = read_text(prompt_path).strip()
    match = re.search(r"<system>\s*(.*?)\s*</system>", content, re.DOTALL)
    return match.group(1).strip() if match else content


def make_run_dir(base_dir: str | Path = "runs") -> Path:
    root = Path(base_dir)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = root / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _default_json(value: Any) -> Any:
    if is_dataclass(value):
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
