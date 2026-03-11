from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL_NAME = "gemini-3-pro-preview"
GEMINI_PRO_THINKING_LEVEL = "high"


@dataclass(slots=True)
class Settings:
    api_key: str
    base_url: str
    model_name: str
    request_timeout: int = 180


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
    dotenv_values = _load_dotenv(Path(dotenv_path))

    def pick(name: str, default: str = "") -> str:
        return os.environ.get(name) or dotenv_values.get(name, default)

    api_key = pick("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("缺少 GEMINI_API_KEY。请先在 .env 中配置。")

    base_url = pick("GEMINI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model_name = pick("GEMINI_MODEL_NAME", DEFAULT_MODEL_NAME)

    return Settings(api_key=api_key, base_url=base_url, model_name=model_name)
