"""Analyzer：把 LLMClient 的输出落到 Analysis ORM 实例。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.analyzers.embedding_client import EmbeddingClient, EmbeddingResult
from app.analyzers.llm_client import LLMCallResult, LLMClient
from app.analyzers.prompts import SYSTEM_PROMPT, build_user_prompt
from app.db.models import Analysis, Article
from app.utils.logging import logger

ALLOWED_CATEGORIES = {
    "research",
    "product",
    "industry",
    "tooling",
    "policy",
    "other",
}


def _coerce_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 5.0
    return max(1.0, min(10.0, score))


def _coerce_tags(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        if len(out) >= 8:
            break
    return out


def _coerce_category(value: Any) -> str:
    if isinstance(value, str) and value.strip().lower() in ALLOWED_CATEGORIES:
        return value.strip().lower()
    return "other"


@dataclass
class AnalyzerInput:
    """让 Analyzer 不强依赖 ORM 实例，便于测试。"""

    title: str
    source_name: str
    published_at: datetime | None
    content: str


class Analyzer:
    """文章分析器。"""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client or LLMClient()

    def analyze_input(self, payload: AnalyzerInput) -> tuple[dict[str, Any], LLMCallResult]:
        """对一份输入做分析，返回 (规范化字段, 原始 LLM 调用结果)。"""
        user_prompt = build_user_prompt(
            title=payload.title,
            source=payload.source_name,
            published_at=(
                payload.published_at.isoformat() if payload.published_at else "(未知)"
            ),
            content=payload.content or "",
        )

        result = self.llm.chat_json(system=SYSTEM_PROMPT, user=user_prompt)

        data = result.data
        normalized = {
            "summary": str(data.get("summary") or "").strip()[:1000],
            "tags": _coerce_tags(data.get("tags")),
            "category": _coerce_category(data.get("category")),
            "score": _coerce_score(data.get("score")),
            "score_reason": str(data.get("score_reason") or "").strip()[:200],
        }
        if not normalized["summary"]:
            normalized["summary"] = "(LLM 未返回有效摘要)"

        return normalized, result

    def analyze_article(self, article: Article) -> Analysis:
        """主入口：对一篇文章生成 Analysis（未提交，由调用方 commit）。"""
        source_name = article.source.name if article.source else "(unknown)"
        content = article.content or article.summary or ""
        if not content:
            logger.warning("Article {} 没有内容可分析，仅用标题", article.id)
            content = article.title

        normalized, result = self.analyze_input(
            AnalyzerInput(
                title=article.title,
                source_name=source_name,
                published_at=article.published_at,
                content=content,
            )
        )

        return Analysis(
            article_id=article.id,
            summary=normalized["summary"],
            tags=normalized["tags"],
            category=normalized["category"],
            score=normalized["score"],
            score_reason=normalized["score_reason"],
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=result.cost_usd,
            raw_response=result.raw_response[:8000] if result.raw_response else None,
            analyzed_at=datetime.now(tz=timezone.utc),
        )


__all__ = ["Analyzer", "AnalyzerInput", "ALLOWED_CATEGORIES"]
