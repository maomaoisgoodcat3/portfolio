from __future__ import annotations

from typing import Any, Protocol

import httpx


class LLMClient(Protocol):
    def embed_query(self, text: str) -> list[float]:
        ...

    def answer(self, system: str, contents: list[dict[str, Any]]) -> str:
        ...


class GeminiError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class GeminiClient:
    _base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: str,
        chat_model: str,
        embed_model: str = "gemini-embedding-001",
        timeout: float = 20.0,
    ) -> None:
        self._api_key = api_key
        self._chat_model = chat_model
        self._embed_model = embed_model
        self._client = httpx.Client(
            timeout=timeout,
            headers={"x-goog-api-key": api_key},
        )

    def embed_query(self, text: str) -> list[float]:
        payload = {
            "content": {"parts": [{"text": text}]},
            "taskType": "RETRIEVAL_QUERY",
            "outputDimensionality": 768,
        }
        response = self._request(
            "POST",
            f"{self._base_url}/{self._embed_model}:embedContent",
            json=payload,
        )
        try:
            values = response["embedding"]["values"]
            if not isinstance(values, list) or not all(
                isinstance(value, (int, float)) for value in values
            ):
                raise ValueError
            return [float(value) for value in values]
        except (KeyError, TypeError, ValueError) as exc:
            raise GeminiError("Embedding response was invalid") from exc

    def answer(self, system: str, contents: list[dict[str, Any]]) -> str:
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024,
            },
        }
        response = self._request(
            "POST",
            f"{self._base_url}/{self._chat_model}:generateContent",
            json=payload,
        )
        candidates = response.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise GeminiError("Gemini returned no candidates")

        candidate = candidates[0]
        if not isinstance(candidate, dict):
            raise GeminiError("Gemini returned an invalid candidate")
        finish_reason = candidate.get("finishReason")
        if finish_reason in {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT"}:
            raise GeminiError("Gemini response was blocked")
        text = self._candidate_text(candidate)
        if not text:
            if finish_reason == "MAX_TOKENS":
                raise GeminiError("Gemini response reached the token limit")
            raise GeminiError("Gemini response contained no text")
        return text

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._client.request(method, url, **kwargs)
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            raise GeminiError("Gemini request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise GeminiError(f"Gemini request failed with HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise GeminiError("Gemini request failed") from exc
        if not isinstance(payload, dict):
            raise GeminiError("Gemini returned an invalid response")
        return payload

    @staticmethod
    def _candidate_text(candidate: dict[str, Any]) -> str:
        content = candidate.get("content")
        if not isinstance(content, dict):
            return ""
        parts = content.get("parts")
        if not isinstance(parts, list):
            return ""
        return "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ).strip()

    def close(self) -> None:
        self._client.close()
