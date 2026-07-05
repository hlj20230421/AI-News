"""分析服务。"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

from app.analyzers import Analyzer
from app.analyzers.embedding_client import EmbeddingClient
from app.config import settings
from app.db import SessionLocal
from app.db.models import Analysis, Article
from app.utils.logging import logger
def _persist_embedding(session, analysis_id: int, vector: list[float]) -> None:
    session.execute(
        text("UPDATE analyses SET embedding = CAST(:vec AS vector) WHERE id = :id"),
        {"vec": EmbeddingClient.to_pg_literal(vector), "id": analysis_id},
    )


def analyze_article_by_id(article_id: int) -> int | None:
    analyzer = Analyzer()
    with SessionLocal() as session:
        article = session.execute(
            select(Article).options(joinedload(Article.source), joinedload(Article.analysis)).where(Article.id == article_id)
        ).scalar_one_or_none()
        if not article:
            return None
        if article.analysis is not None:
            return article.analysis.id
        try:
            analysis = analyzer.analyze_article(article)
        except Exception:
            logger.exception("分析文章失败 article_id={}", article_id)
            return None
        session.add(analysis)
        session.commit()
        session.refresh(analysis)

        try:
            embed_text = f"{article.title}\n{analysis.summary}"
            embedding = EmbeddingClient().embed(embed_text).vector
        except Exception:
            logger.debug("文章 {} embedding 跳过（未配置或调用失败）", article_id)
            embedding = None

        if embedding:
            try:
                _persist_embedding(session, analysis.id, embedding)
                session.commit()
            except Exception:
                session.rollback()

        if analysis.score >= settings.instant_push_min_score:
            from app.scheduler.tasks import send_instant_digest

            send_instant_digest.delay(force=False)

        return analysis.id


def analyze_pending_articles(limit: int = 20) -> list[int]:
    with SessionLocal() as session:
        ids = list(
            session.execute(
                select(Article.id)
                .outerjoin(Analysis, Analysis.article_id == Article.id)
                .where(Analysis.id.is_(None))
                .order_by(Article.id.desc())
                .limit(limit)
            ).scalars()
        )
    out: list[int] = []
    for aid in ids:
        result = analyze_article_by_id(aid)
        if result is not None:
            out.append(result)
    return out
