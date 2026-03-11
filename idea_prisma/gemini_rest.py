from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Iterable
from urllib import error, parse, request

from .config import Settings


class GeminiError(RuntimeError):
    pass


@dataclass(slots=True)
class GenerateResult:
    text: str
    raw: dict[str, Any]


def _extract_text(payload: dict[str, Any]) -> str:
    texts: list[str] = []
    for candidate in payload.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                texts.append(text)
    return "".join(texts).strip()


class GeminiRestClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _build_url(self, method: str, stream: bool = False) -> str:
        endpoint = f"{self.settings.base_url}/models/{self.settings.model_name}:{method}"
        query = {"key": self.settings.api_key}
        if stream:
            query["alt"] = "sse"
        return f"{endpoint}?{parse.urlencode(query)}"

    def _request(self, method: str, payload: dict[str, Any], stream: bool = False) -> Any:
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
            raise GeminiError(f"Gemini API 请求失败：HTTP {exc.code} - {message}") from exc
        except error.URLError as exc:
            raise GeminiError(f"Gemini API 请求失败：{exc.reason}") from exc

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
        thinking_level: str = "high",
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
        thinking_level: str = "high",
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
        text = _extract_text(raw)
        return json.loads(_clean_json_text(text))

    def stream_text(
        self,
        user_text: str,
        system_instruction: str | None = None,
        *,
        temperature: float | None = None,
        thinking_level: str = "high",
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
        payload = json.loads(data)
        return _extract_text(payload)


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()
