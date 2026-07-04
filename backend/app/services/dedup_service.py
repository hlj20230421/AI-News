"""语义去重：入库前检查与近期文章的向量相似度。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.analyzers.embedding_client import EmbeddingClient
from app.config import settings
from app.utils.logging import logger


def _build_embed_text(title: str, summary: str | None, content: str | None) -> str:
    parts = [title.strip()]
    if summary and summary.strip():
        parts.append(summary.strip()[:2000])
    elif content and content.strip():
        parts.append(content.strip()[:2000])
    return "\n\n".join(parts)


def find_similar_article_id(
    session: Session,
    *,
    title: str,
    summary: str | None = None,
    content: str | None = None,
    embedder: EmbeddingClient | None = None,
) -> tuple[int | None, float | None]:
    """若存在相似文章返回 (article_id, similarity)，否则 (None, None)。"""
    embedder = embedder or EmbeddingClient()
    try:
        result = embedder.embed(_build_embed_text(title, summary, content))
    except Exception as exc:  # noqa: BLE001
        logger.warning("embedding 失败，跳过去重: {}", exc)
        return None, None

    since = datetime.now(tz=UTC) - timedelta(days=settings.embedding_dedup_days)
    vec_literal = EmbeddingClient.to_pg_literal(result.vector)
    row = session.execute(
        text(
            """
            SELECT a.article_id,
                   1 - (an.embedding <=> CAST(:vec AS vector)) AS similarity
            FROM analyses an
            JOIN articles a ON a.id = an.article_id
            WHERE an.embedding IS NOT NULL
              AND an.analyzed_at >= :since
            ORDER BY an.embedding <=> CAST(:vec AS vector)
            LIMIT 1
            """
        ),
        {"vec": vec_literal, "since": since},
    ).first()

    if not row:
        return None, None

    article_id, similarity = row[0], float(row[1])
    if similarity >= settings.embedding_similarity_threshold:
        logger.info(
            "语义去重命中 article_id={} similarity={:.4f} threshold={}",
            article_id,
            similarity,
            settings.embedding_similarity_threshold,
        )
        return article_id, similarity
    return None, None


__all__ = ["find_similar_article_id"]
