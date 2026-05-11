"""
LLM provider abstraction.

The rest of the codebase calls `complete(messages, ...)` or
`stream(messages, ...)` and doesn't care which model is behind it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator, Literal

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

Role = Literal["system", "user", "assistant"]


class LLM(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1200,
        response_format_json: bool = False,
    ) -> str: ...

    @abstractmethod
    def stream(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> Iterator[str]: ...


# ------------------------------------------------------------
# OpenAI
# ------------------------------------------------------------
class OpenAILLM(LLM):
    def __init__(self, settings: Settings):
        from openai import OpenAI

        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY required for OpenAI LLM provider.")
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_chat_model
        log.info("OpenAILLM ready (model=%s)", self._model)

    def complete(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1200,
        response_format_json: bool = False,
    ) -> str:
        kwargs: dict = dict(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response_format_json:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    def stream(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> Iterator[str]:
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta


# ------------------------------------------------------------
# Anthropic
# ------------------------------------------------------------
class AnthropicLLM(LLM):
    def __init__(self, settings: Settings):
        from anthropic import Anthropic

        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY required for Anthropic provider.")
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_chat_model
        log.info("AnthropicLLM ready (model=%s)", self._model)

    @staticmethod
    def _split_system(messages: list[dict]) -> tuple[str, list[dict]]:
        sys_parts: list[str] = []
        rest: list[dict] = []
        for m in messages:
            if m["role"] == "system":
                sys_parts.append(m["content"])
            else:
                rest.append({"role": m["role"], "content": m["content"]})
        return "\n\n".join(sys_parts), rest

    def complete(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1200,
        response_format_json: bool = False,
    ) -> str:
        system, rest = self._split_system(messages)
        # JSON mode: nudge in the system prompt; Anthropic returns prose by default.
        if response_format_json:
            system += "\n\nRespond ONLY with valid JSON. No prose, no markdown fences."
        resp = self._client.messages.create(
            model=self._model,
            system=system or None,
            messages=rest,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # Concatenate text blocks.
        parts: list[str] = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "".join(parts)

    def stream(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> Iterator[str]:
        system, rest = self._split_system(messages)
        with self._client.messages.stream(
            model=self._model,
            system=system or None,
            messages=rest,
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            for delta in stream.text_stream:
                yield delta


# ------------------------------------------------------------
# Mock — for offline dev / CI. Echoes a templated answer.
# ------------------------------------------------------------
class MockLLM(LLM):
    def __init__(self) -> None:
        log.warning("Using MockLLM. Responses are templated, not generated.")

    @staticmethod
    def _last_user(messages: list[dict]) -> str:
        for m in reversed(messages):
            if m["role"] == "user":
                return m["content"]
        return ""

    def complete(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1200,
        response_format_json: bool = False,
    ) -> str:
        question = self._last_user(messages)
        if response_format_json:
            return (
                '{"summary": "Mock company summary based on retrieved filings.",'
                ' "revenue_trends": "Revenue grew modestly year-over-year in the '
                'retrieved context.", "risk_factors": [{"title": "Mock risk",'
                ' "description": "Placeholder risk description.", "severity":'
                ' "medium"}], "competitive_positioning": "Mock competitive note.",'
                ' "management_commentary": "Mock management commentary.",'
                ' "overall_risk": "medium"}'
            )
        return (
            "Based on the retrieved context, here is a placeholder answer to your "
            f"question: '{question[:200]}'. (Mock LLM is active — set "
            "LLM_PROVIDER=openai or anthropic with an API key for real answers.)"
            " [1]"
        )

    def stream(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> Iterator[str]:
        text = self.complete(messages, temperature=temperature, max_tokens=max_tokens)
        for word in text.split():
            yield word + " "


# ------------------------------------------------------------
# Factory
# ------------------------------------------------------------
def get_llm(settings: Settings | None = None) -> LLM:
    settings = settings or get_settings()
    provider = settings.llm_provider
    if provider == "anthropic" and settings.anthropic_api_key:
        return AnthropicLLM(settings)
    if provider == "openai" and settings.openai_api_key:
        return OpenAILLM(settings)
    return MockLLM()
