"""EmbeddingClient：基于 litellm 的统一向量生成。"""

from __future__ import annotations

from dataclasses import dataclass

import litellm

from app.config import settings


class EmbeddingClientError(RuntimeError):
    pass


@dataclass
class EmbeddingResult:
    vector: list[float]
    model: str
    input_tokens: int | None = None


def _to_pgvector_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in vec) + "]"


class EmbeddingClient:
    def __init__(self, *, model: str | None = None, provider: str | None = None) -> None:
        self.model = model or settings.embedding_model
        self.provider = provider or settings.embedding_provider

    def embed(self, text: str) -> EmbeddingResult:
        text = (text or "").strip()
        if not text:
            raise EmbeddingClientError("embedding 输入为空")

        kwargs: dict = {
            "model": self.model,
            "input": [text[:8000]],
        }
        if settings.openai_api_key:
            kwargs["api_key"] = settings.openai_api_key
        if settings.openai_base_url:
            kwargs["api_base"] = settings.openai_base_url

        resp = litellm.embedding(**kwargs)
        data = resp.data[0]
        vec = list(data["embedding"]) if isinstance(data, dict) else list(data.embedding)
        if len(vec) != settings.embedding_dim:
            raise EmbeddingClientError(f"向量维度 {len(vec)} 与配置 EMBEDDING_DIM={settings.embedding_dim} 不一致")
        usage = getattr(resp, "usage", None)
        return EmbeddingResult(
            vector=vec,
            model=self.model,
            input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
        )

    @staticmethod
    def to_pg_literal(vec: list[float]) -> str:
        return _to_pgvector_literal(vec)


__all__ = ["EmbeddingClient", "EmbeddingClientError", "EmbeddingResult"]
