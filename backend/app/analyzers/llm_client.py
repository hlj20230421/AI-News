"""LLMClient：基于 litellm 的统一调用层。

特性：
- 跨厂商（OpenAI / Anthropic / DeepSeek / Ollama 等）统一
- 自动重试（tenacity）
- 强制返回 JSON 对象（多种容错路径）
- 调用元数据（model / token / cost）回传给上游
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import litellm
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.utils.logging import logger

JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class LLMClientError(RuntimeError):
    """LLM 调用相关的错误。"""


class LLMResponseFormatError(LLMClientError):
    """模型未返回合法 JSON。"""


@dataclass
class LLMCallResult:
    """LLM 一次调用的结构化结果。"""

    data: dict[str, Any]
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    raw_response: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


def _parse_json_loose(text: str) -> dict[str, Any]:
    """容错解析 LLM 的 JSON 输出。"""
    if not text:
        raise LLMResponseFormatError("LLM 返回空字符串")

    candidates: list[str] = [text.strip()]

    block_match = JSON_BLOCK_RE.search(text)
    if block_match:
        candidates.append(block_match.group(1))

    object_match = JSON_OBJECT_RE.search(text)
    if object_match:
        candidates.append(object_match.group(0))

    last_err: Exception | None = None
    for candidate in candidates:
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except Exception as exc:  # noqa: BLE001
            last_err = exc

    raise LLMResponseFormatError(
        f"无法从 LLM 输出解析 JSON: {last_err} | raw[:200]={text[:200]!r}"
    )


def resolve_completion_model_and_auth(
    *,
    provider: str,
    model: str,
    openai_api_key: str = "",
    openai_base_url: str = "",
    anthropic_api_key: str = "",
    deepseek_api_key: str = "",
) -> dict[str, Any]:
    """按 provider 解析 litellm 所需的 model / api_key / api_base。"""
    provider_key = provider.lower()
    extras: dict[str, Any] = {}

    if provider_key == "deepseek":
        resolved_model = model if model.startswith("deepseek/") else f"deepseek/{model}"
        if deepseek_api_key:
            extras["api_key"] = deepseek_api_key
    elif provider_key == "anthropic":
        resolved_model = model if model.startswith("anthropic/") else f"anthropic/{model}"
        if anthropic_api_key:
            extras["api_key"] = anthropic_api_key
    elif provider_key == "ollama":
        resolved_model = model if model.startswith("ollama/") else f"ollama/{model}"
        if openai_base_url:
            base = openai_base_url.rstrip("/")
            if base.endswith("/v1"):
                base = base[:-3]
            extras["api_base"] = base
    else:
        resolved_model = model
        if openai_api_key:
            extras["api_key"] = openai_api_key
        if openai_base_url:
            extras["api_base"] = openai_base_url

    return {"model": resolved_model, **extras}


class LLMClient:
    """litellm 封装。"""

    def __init__(
        self,
        *,
        model: str | None = None,
        provider: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.model = model or settings.llm_model
        self.provider = provider or settings.llm_provider
        self.timeout = timeout or settings.llm_timeout_seconds

    def _build_kwargs(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        resolved = resolve_completion_model_and_auth(
            provider=self.provider,
            model=self.model,
            openai_api_key=settings.openai_api_key,
            openai_base_url=settings.openai_base_url,
            anthropic_api_key=settings.anthropic_api_key,
            deepseek_api_key=settings.deepseek_api_key,
        )
        kwargs: dict[str, Any] = {
            **resolved,
            "messages": messages,
            "timeout": self.timeout,
            "temperature": 0.2,
        }

        provider = (self.provider or "").lower()
        if provider in {"openai", "deepseek", "ollama"}:
            kwargs["response_format"] = {"type": "json_object"}

        return kwargs

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (LLMResponseFormatError, litellm.exceptions.APIError)
        ),
        reraise=True,
    )
    def chat_json(
        self,
        *,
        system: str,
        user: str,
    ) -> LLMCallResult:
        """发起一次 chat 并返回 JSON。"""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        kwargs = self._build_kwargs(messages)

        logger.debug("LLM call model={} provider={}", self.model, self.provider)
        response = litellm.completion(**kwargs)

        try:
            content = response.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            raise LLMClientError(f"LLM 响应结构异常: {exc}") from exc

        data = _parse_json_loose(content)

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        output_tokens = getattr(usage, "completion_tokens", None) if usage else None
        cost = None
        try:
            cost = float(litellm.completion_cost(completion_response=response))
        except Exception:  # noqa: BLE001
            cost = None

        return LLMCallResult(
            data=data,
            model=kwargs["model"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            raw_response=content,
        )


__all__ = [
    "LLMClient",
    "LLMCallResult",
    "LLMClientError",
    "LLMResponseFormatError",
    "_parse_json_loose",
    "resolve_completion_model_and_auth",
]
